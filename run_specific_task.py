import os
import re
import shutil
import subprocess
from pathlib import Path
from datetime import datetime
import csv
import sys
import concurrent.futures
from typing import List, Optional
import logging
import traceback
import tempfile
import time
from tqdm import tqdm

# Configure logging
file_handler = logging.FileHandler("run_tests.log")
file_handler.setLevel(logging.DEBUG)
file_formatter = logging.Formatter('%(asctime)s [%(levelname)s] %(message)s')
file_handler.setFormatter(file_formatter)

# Create console handler that only logs INFO and above
console_handler = logging.StreamHandler(sys.stdout)
console_handler.setLevel(logging.INFO)
console_formatter = logging.Formatter('[%(levelname)s] %(message)s')
console_handler.setFormatter(console_formatter)

# Get the root logger and set its level to DEBUG
root_logger = logging.getLogger()
root_logger.setLevel(logging.DEBUG)

# Remove any existing handlers and add our custom handlers
for handler in root_logger.handlers[:]:
    root_logger.removeHandler(handler)
root_logger.addHandler(file_handler)
root_logger.addHandler(console_handler)

# Define script_dir globally
script_dir = os.path.dirname(os.path.abspath(__file__))

# Color codes for terminal output
class Colors:
    GREEN = '\033[0;32m'
    RED = '\033[0;31m'
    BLUE = '\033[0;34m'
    YELLOW = '\033[0;33m'  # Added yellow for FAILED_TO_RUN status
    NC = '\033[0m'  # No color

# Directory structure constants
BASE_DIR = "calibrated_tasks/java_tasks"  # This will be overridden by command line argument
CODE_DIR = "code"
TEST_DIR = "test"
RESULTS_DIR = "test_results"
SRC_MAIN = "src/main/java"
SRC_TEST = "src/test/java"
BUILD_GRADLE_FILE = "build.gradle"

GRADLE_DIR = "gradle-8.10.2"  # The name of your local Gradle directory


# Filename mapping
FILE_MAPPING = {
    "base_code.java": "base.java",
    "model1.java": "A.java",
    "model2.java": "B.java",
    "model3.java": "C.java",
    "model4.java": "D.java",
    "model5.java": "E.java",
    "model6.java": "F.java",
    "model7.java": "G.java",
    "model8.java": "H.java",
    "model9.java": "I.java",
    "model10.java": "J.java",
    "Solution.java": "Solution.java",
    "incorrect_solution.java": "incorrect.java",
}

class TestResult:
    def __init__(self, file_name):
        self.file_name = file_name
        self.status = "NOT_RUN"
        self.output = ""
        self.error = None
        self.timestamp = datetime.now()

def setup_task_directory(task_id):
    """
    Set up the code and test directories for the given task ID
    """
    try:
        # Construct absolute path to task directory
        task_dir = os.path.join(script_dir, BASE_DIR, task_id)

        # Debug information
        logging.debug(f"Current working directory: {os.getcwd()}")
        logging.debug(f"Looking for task directory at: {task_dir}")

        if not os.path.exists(task_dir):
            logging.error(f"Task directory '{task_dir}' not found")
            return False

        # Create work directory under the task directory
        task_work_dir = os.path.join(task_dir, "work_dir")
        os.makedirs(task_work_dir, exist_ok=True)
        logging.debug(f"Ensured work directory exists at: {task_work_dir}")

        # Create results directory
        task_results_dir = os.path.join(task_dir, RESULTS_DIR)
        os.makedirs(task_results_dir, exist_ok=True)
        logging.debug(f"Ensured results directory exists at: {task_results_dir}")

        return True
    except Exception as e:
        logging.exception(f"Exception in setup_task_directory for task {task_id}: {e}")
        return False

def cleanup():
    logging.info("Cleaning up build and src directories...")
    for directory in ["build", "src", ".gradle", "gradle", ".ropeproject"]:
        try:
            shutil.rmtree(directory, ignore_errors=True)
            logging.debug(f"Removed directory: {directory}")
        except Exception as e:
            logging.error(f"Error removing directory {directory}: {e}")
    for file in ["gradlew", "gradlew.bat", BUILD_GRADLE_FILE]:
        try:
            if os.path.exists(file):
                os.remove(file)
                logging.debug(f"Removed file: {file}")
        except Exception as e:
            logging.error(f"Error removing file {file}: {e}")

def delete_work_dir():
    """Delete work directories in all task folders"""
    logging.info("Deleting work directories in all task folders...")
    try:
        for task_dir in os.listdir(BASE_DIR):
            if re.match(r'^\d{6}$', task_dir):
                work_dir = os.path.join(BASE_DIR, task_dir, "work_dir")
                if os.path.exists(work_dir):
                    shutil.rmtree(work_dir)
                    logging.debug(f"Deleted work directory: {work_dir}")
    except Exception as e:
        logging.exception(f"Exception while deleting work directories: {e}")

def find_java_files(directory):
    java_files = []
    try:
        for file_path in Path(directory).rglob("*.java"):
            if "build" not in str(file_path) and ".gradle" not in str(file_path):
                java_files.append(str(file_path))
        logging.debug(f"Found {len(java_files)} Java files in {directory}")
    except Exception as e:
        logging.exception(f"Exception while finding Java files in {directory}: {e}")
    return java_files

def find_test_files(task_id):
    task_test_dir = os.path.join(BASE_DIR, task_id, TEST_DIR)
    return find_java_files(task_test_dir)

def find_code_files(task_id):
    task_code_dir = os.path.join(BASE_DIR, task_id, CODE_DIR)
    return find_java_files(task_code_dir)

def check_test_convention(test_file):
    """Check if test file references Solution or Main"""
    try:
        with open(test_file, 'r') as f:
            content = f.read()
        result = 'Solution' in content
        logging.debug(f"Test convention check for {test_file}: {'Solution found' if result else 'Main found'}")
        return result
    except Exception as e:
        logging.exception(f"Exception while checking test convention for {test_file}: {e}")
        return False

def get_class_name(content):
    """Extract the original class name from the file content"""
    match = re.search(r'public class (\w+)', content)
    class_name = match.group(1) if match else None
    logging.debug(f"Extracted class name: {class_name}")
    return class_name

def process_java_file(file_path, target_class):
    try:
        with open(file_path, 'r') as f:
            content = f.read()

        # Change protected/private to public
        content = re.sub(r'\b(private|protected)\s+static', 'public static', content)
        content = re.sub(r'\b(private|protected)\s+final\s+static', 'public static final', content)
        content = re.sub(r'\b(private|protected)\s+', 'public ', content)

        # Get the main class name and replace it
        main_class_match = re.search(r'public class (\w+)', content)
        if not main_class_match:
            logging.warning(f"No public class found in {file_path}")
            return content  # Return unmodified content

        main_class = main_class_match.group(1)
        content = re.sub(f'(?<!new )\\b{main_class}\\b', target_class, content)
        content = re.sub(f'new {main_class}\\(', f'new {target_class}(', content)

        logging.debug(f"Processed Java file {file_path}: Replaced class {main_class} with {target_class}")
        return content
    except Exception as e:
        logging.exception(f"Exception while processing Java file {file_path}: {e}")
        return ""

def setup_test_environment(code_file, test_files, work_dir):
    try:
        # Create necessary directories
        src_main = os.path.join(work_dir, SRC_MAIN)
        src_test = os.path.join(work_dir, SRC_TEST)
        os.makedirs(src_main, exist_ok=True)
        os.makedirs(src_test, exist_ok=True)
        logging.debug(f"Ensured SRC_MAIN and SRC_TEST directories exist in {work_dir}")

        # Check test file convention
        uses_solution = check_test_convention(test_files[0])

        # Process main code file
        target_class = "Solution" if uses_solution else "Main"
        main_content = process_java_file(code_file, target_class)
        filename = f"{target_class}.java"
        main_file_path = os.path.join(src_main, filename)
        with open(main_file_path, 'w') as f:
            f.write(main_content)
        logging.debug(f"Wrote processed main file to {main_file_path}")

        # Copy test file
        for test_file in test_files:
            test_filename = f"{target_class}Test.java"
            test_file_path = os.path.join(src_test, test_filename)
            shutil.copy2(test_file, test_file_path)
            logging.debug(f"Copied test file to {test_file_path}")
    except Exception as e:
        logging.exception(f"Exception in setup_test_environment: {e}")

def save_test_result(test_result, task_id):
    """Save individual test result to a file"""
    try:
        # Get absolute path for results directory
        task_results_dir = os.path.join(script_dir, BASE_DIR, task_id, RESULTS_DIR)
        os.makedirs(task_results_dir, exist_ok=True)

        # Save individual test result
        file_name = os.path.basename(test_result.file_name)
        result_file = os.path.join(task_results_dir, f"{FILE_MAPPING[file_name].split('.java')[0]}.txt")

        with open(result_file, 'w') as f:
            f.write(f"Test Results for {file_name}\n")
            f.write("=" * (16 + len(file_name)) + "\n\n")
            f.write(f"Timestamp: {test_result.timestamp}\n")
            f.write(f"Status: {test_result.status}\n")
            f.write("\nTest Output:\n")
            f.write("-----------\n")
            f.write(test_result.output)
            if test_result.error:
                f.write("\nErrors:\n")
                f.write("-------\n")
                f.write(str(test_result.error))
        logging.debug(f"Saved test result to {result_file}")
    except Exception as e:
        logging.exception(f"Exception while saving test result for {test_result.file_name}: {e}")

def save_summary(test_results, task_id):
    """Save summary of all test results"""
    try:
        task_results_dir = os.path.join(script_dir, BASE_DIR, task_id, RESULTS_DIR)
        os.makedirs(task_results_dir, exist_ok=True)
        summary_file = os.path.join(task_results_dir, "summary.txt")

        def is_letter_file(filename):
            # Update regex to match modelX.java files and map them to their letter
            if re.match(r'^model(\d+)\.java$', filename):
                model_num = int(re.match(r'^model(\d+)\.java$', filename).group(1))
                return chr(64 + model_num) + '.java'  # Convert 1->A, 2->B, etc.
            return filename

        def categorize_results(results):
            claude_tests = []
            llama_tests = []
            other_tests = []

            for result in results:
                file_name = os.path.basename(result.file_name)
                letter_file = is_letter_file(file_name)
                
                if re.match(r'^[A-J]\.java$', letter_file):
                    first_letter = letter_file[0].upper()
                    if 'A' <= first_letter <= 'E':
                        claude_tests.append(result)
                    elif 'F' <= first_letter <= 'J':
                        llama_tests.append(result)
                else:
                    other_tests.append(result)

            return claude_tests, llama_tests, other_tests

        def calculate_stats(tests):
            if not tests:
                return 0, 0, 0, 0, 0

            total = len(tests)
            passed = sum(1 for r in tests if r.status == "PASSED")
            failed = sum(1 for r in tests if r.status == "FAILED")
            failed_to_run = sum(1 for r in tests if r.status == "FAILED_TO_RUN")

            pass_percent = (passed / total) * 100 if total > 0 else 0
            fail_percent = ((failed + failed_to_run) / total) * 100 if total > 0 else 0

            return total, passed, failed + failed_to_run, pass_percent, fail_percent

        claude_tests, llama_tests, other_tests = categorize_results(test_results)

        with open(summary_file, 'w') as f:
            f.write("Test Execution Summary\n")
            f.write("=====================\n\n")
            f.write(f"Generated: {datetime.now()}\n\n")

            # Overall statistics
            total = len(test_results)
            passed = sum(1 for r in test_results if r.status == "PASSED")
            failed = sum(1 for r in test_results if r.status == "FAILED")
            failed_to_run = sum(1 for r in test_results if r.status == "FAILED_TO_RUN")

            f.write("Overall Results:\n")
            f.write("----------------\n")
            f.write(f"Total files tested: {total}\n")
            f.write(f"Passed: {passed}\n")
            f.write(f"Failed: {failed}\n")
            f.write(f"Failed to Run: {failed_to_run}\n")
            f.write(f"Pass Rate: {(passed/total*100):.2f}%\n\n")

            # Model comparison
            f.write("Model Comparison:\n")
            f.write("----------------\n")

            # Claude results
            c_total, c_passed, c_failed, c_pass_pct, c_fail_pct = calculate_stats(claude_tests)
            f.write("\nClaude Model (A-E):\n")
            f.write(f"Total tests: {c_total}\n")
            f.write(f"Passed: {c_passed}\n")
            f.write(f"Failed/Failed to Run: {c_failed}\n")
            f.write(f"Pass Rate: {c_pass_pct:.2f}%\n")

            # Llama results
            l_total, l_passed, l_failed, l_pass_pct, l_fail_pct = calculate_stats(llama_tests)
            f.write("\nLlama Model (F-J):\n")
            f.write(f"Total tests: {l_total}\n")
            f.write(f"Passed: {l_passed}\n")
            f.write(f"Failed/Failed to Run: {l_failed}\n")
            f.write(f"Pass Rate: {l_pass_pct:.2f}%\n")

            # Other results (base, solution, incorrect)
            o_total, o_passed, o_failed, o_pass_pct, o_fail_pct = calculate_stats(other_tests)
            if other_tests:
                f.write("\nOther Files:\n")
                f.write(f"Total tests: {o_total}\n")
                f.write(f"Passed: {o_passed}\n")
                f.write(f"Failed/Failed to Run: {o_failed}\n")
                f.write(f"Pass Rate: {o_pass_pct:.2f}%\n")

            # Detailed results
            f.write("\nDetailed Results:\n")
            f.write("----------------\n")
            for result in test_results:
                status_icon = "PASSED" if result.status == "PASSED" else "FAILED"
                f.write(f"{status_icon} {os.path.basename(result.file_name)}: {result.status}\n")

        logging.info(f"Saved summary report to {summary_file}")
    except Exception as e:
        logging.exception(f"Exception while saving summary: {e}")

def run_gradle(work_dir, capture_output=True):
    """Modified run_gradle function to use local Gradle directly without wrapper"""
    try:
        # Get path to local Gradle binary
        gradle_bin = os.path.join(script_dir, GRADLE_DIR, "bin", "gradle")
        if os.name == 'nt':  # Windows
            gradle_bin += '.bat'

        if not os.path.exists(gradle_bin):
            logging.error(f"Gradle binary not found at {gradle_bin}")
            raise FileNotFoundError(f"Gradle binary not found at {gradle_bin}")

        # Run gradle test directly without using wrapper
        env = os.environ.copy()
        env['GRADLE_HOME'] = os.path.join(script_dir, GRADLE_DIR)
        
        result = subprocess.run([
            gradle_bin,
            "test",
            "--no-daemon",
            "--project-cache-dir", os.path.join(work_dir, ".gradle"),
            "--gradle-user-home", os.path.join(work_dir, ".gradle")
        ], capture_output=capture_output, text=True, cwd=work_dir, env=env, timeout=240)
        
        return result
    except Exception as e:
        logging.exception(f"Exception while running gradle: {e}")
        return None

def create_build_gradle(task_id, work_dir):
    """Create build.gradle file using content from installed_packages.txt in task directory,
    preserving default JUnit/Jupiter dependencies while replacing others and removing M2.1 dependency"""
    try:
        # Base build.gradle content with optimized configuration
        base_content = """plugins {
    id 'java'
}
repositories {
    mavenLocal()
    mavenCentral()
}
%s
test {
    useJUnitPlatform()
    testLogging {
        events 'passed', 'skipped', 'failed'
        exceptionFormat 'full'
        showExceptions true
        showCauses true
        showStackTraces true
        showStandardStreams = true
        // Add this to show detailed test progress
        afterSuite { desc, result ->
            if (!desc.parent) {
                println '\\nTest result: ' + result.resultType
                println 'Test summary: ' + result.testCount + ' tests, ' +
                        result.successfulTestCount + ' succeeded, ' +
                        result.failedTestCount + ' failed, ' +
                        result.skippedTestCount + ' skipped'
            }
        }
    }
}
"""

        # Default dependencies block with JUnit dependencies
        default_junit_deps = [
            "testImplementation 'org.junit.jupiter:junit-jupiter-engine:5.9.2'",
            "testImplementation 'org.junit.jupiter:junit-jupiter-api:5.9.2'",
            "testImplementation 'org.junit.jupiter:junit-jupiter-params:5.10.1'"
        ]

        # Construct path to installed_packages.txt
        task_dir = os.path.join(script_dir, BASE_DIR, task_id)
        packages_file = os.path.join(task_dir, "installed_packages.txt")
        gradle_file = os.path.join(work_dir, BUILD_GRADLE_FILE)

        # Debug output
        logging.debug(f"Looking for installed_packages.txt at: {packages_file}")
        logging.debug(f"Creating build.gradle at: {gradle_file}")

        # Start with default dependencies
        final_deps = default_junit_deps.copy()

        if os.path.exists(packages_file):
            with open(packages_file, 'r') as f:
                content = f.read().strip()
                
            # Extract dependencies block using regex
            deps_match = re.search(r'dependencies\s*{([^}]*)}', content)
            if deps_match:
                # Get all individual dependency lines
                custom_deps = [
                    dep.strip() for dep in deps_match.group(1).split('\n')
                    if dep.strip() and any(conf in dep for conf in [
                        'implementation', 'testImplementation', 
                        'runtime', 'testRuntime',
                        'compile', 'testCompile',
                        'api', 'testApi',
                        'compileOnly', 'testCompileOnly',
                        'runtimeOnly', 'testRuntimeOnly'
                    ])
                ]
                
                # Add non-JUnit dependencies to final deps, excluding M2.1
                for dep in custom_deps:
                    # Skip nd4j M2.1 dependency
                    if "nd4j-native-platform:1.0.0-M2.1" not in dep:
                        # Keep mockito and other test dependencies even if they contain 'junit'
                        if 'mockito' in dep.lower() or not any(junit_str in dep.lower() for junit_str in ['junit', 'jupiter']):
                            final_deps.append(dep)
                
        # Create final dependencies block
        dependencies_block = "dependencies {\n    " + "\n    ".join(final_deps) + "\n}"
        
        # Insert dependencies into base content
        gradle_content = base_content % dependencies_block
        
        # Create init script content
        init_script_content = """initscript {
    repositories {
        mavenLocal()
        mavenCentral()
    }
}

allprojects {
    buildscript {
        repositories {
            mavenLocal()
            mavenCentral()
        }
    }
    repositories {
        mavenLocal()
        mavenCentral()
    }
}"""
        
        # Save init script
        init_script_path = os.path.join(work_dir, "init.gradle")
        with open(init_script_path, "w") as f:
            f.write(init_script_content)
        
        # Save build.gradle
        with open(gradle_file, "w") as f:
            f.write(gradle_content)
            
        logging.debug(f"Created build.gradle at {gradle_file}")
        logging.debug(f"Created init.gradle at {init_script_path}")
        
    except Exception as e:
        logging.exception(f"Error creating build.gradle: {e}")

def get_files_to_test(task_id):
    """Get all files that need to be tested for a task"""
    try:
        # Construct absolute path to task directory
        task_dir = os.path.join(BASE_DIR, task_id)
        files_to_test = []

        solution_code_path = os.path.join(task_dir, "src/main/java/Solution.java")
        if os.path.exists(solution_code_path):
            files_to_test.append(("Solution.java", solution_code_path))

        # Add base_code.java from task root directory
        base_code_path = os.path.join(task_dir, "base_code.java")
        if os.path.exists(base_code_path):
            files_to_test.append(("base_code.java", base_code_path))

        # Add all Java files from the code directory
        code_files = find_code_files(task_id)
        for file_path in code_files:
            file_name = os.path.basename(file_path)
            if file_name != "base_code.java":  # Avoid duplication
                files_to_test.append((file_name, file_path))

        # Add all alternate response files if any
        alt_responses_dir = os.path.join(task_dir, "alternate_responses")
        if os.path.exists(alt_responses_dir):
            for file_name in os.listdir(alt_responses_dir):
                if file_name.endswith('.java'):
                    file_path = os.path.join(alt_responses_dir, file_name)
                    files_to_test.append((file_name, file_path))

        # Debug output
        logging.debug(f"Task directory: {task_dir}")
        for name, path in files_to_test:
            logging.debug(f"Found file: {name} at {path}")

        logging.info(f"Found {len(files_to_test)} files to test for task {task_id}")
        return files_to_test
    except Exception as e:
        logging.exception(f"Exception while getting files to test for task {task_id}: {e}")
        return []


def run_test_for_file(file_name, test_work_dir, task_id):
    test_result = TestResult(file_name)
    logging.info(f"Starting test for task {task_id}, file {file_name}")
    try:
        gradle_result = run_gradle(test_work_dir, capture_output=True)
        if gradle_result:
            test_result.output = gradle_result.stdout + gradle_result.stderr
            if gradle_result.returncode == 0:
                test_result.status = "PASSED"
                logging.info(f"Test PASSED for task {task_id}, file {file_name}")
            else:
                test_result.status = "FAILED"
                test_result.error = f"Tests failed with return code: {gradle_result.returncode}\nOutput:\n{gradle_result.stdout}\nErrors:\n{gradle_result.stderr}"
                logging.info(f"Test FAILED for task {task_id}, file {file_name}. Return code: {gradle_result.returncode}")
        else:
            test_result.status = "FAILED_TO_RUN"
            test_result.error = "Gradle run returned None."
            logging.info(f"Test FAILED_TO_RUN for task {task_id}, file {file_name}. Gradle returned None.")
            
    except subprocess.TimeoutExpired as e:
        test_result.status = "FAILED_TO_RUN"
        test_result.error = f"Test timed out after {e.timeout} seconds"
        logging.info(f"Test TIMEOUT for task {task_id}, file {file_name} after {e.timeout} seconds")
    except Exception as e:
        test_result.status = "FAILED_TO_RUN"
        test_result.error = f"Error type: {type(e).__name__}\nError message: {str(e)}\nTraceback:\n{traceback.format_exc()}"
        logging.info(f"Test FAILED_TO_RUN for task {task_id}, file {file_name}. Error: {type(e).__name__}: {str(e)}")
        logging.debug(f"Full traceback for {task_id}, {file_name}:\n{traceback.format_exc()}")
        
    logging.info(f"Completed test for task {task_id}, file {file_name} with status: {test_result.status}")
    save_test_result(test_result, task_id)
    return test_result

def process_task(task_id):
    try:
        # Ensure the task directory exists
        task_dir = os.path.join(BASE_DIR, task_id)
        if not os.path.exists(task_dir):
            logging.error(f"Task directory '{task_dir}' does not exist.")
            return None

        # Create work directory under the task directory
        work_dir = os.path.join(task_dir, "work_dir")
        os.makedirs(work_dir, exist_ok=True)
        
        # Set GRADLE_USER_HOME environment variable to task-specific directory
        task_gradle_home = os.path.join(work_dir, ".gradle")
        os.makedirs(task_gradle_home, exist_ok=True)
        os.environ['GRADLE_USER_HOME'] = task_gradle_home

        # Get test file path
        test_file = os.path.join(task_dir, "src", "test", "java", "SolutionTest.java")
        if not os.path.exists(test_file):
            logging.error(f"Task {task_id}: No test file found at {test_file}")
            return None
        
        # Get all files to test
        files_to_test = get_files_to_test(task_id)
        if not files_to_test:
            logging.error(f"Task {task_id}: No Java files found to test")
            return None
            
        test_results = []
        
        # Setup all test environments first using a thread pool
        with concurrent.futures.ThreadPoolExecutor(max_workers=min(32, os.cpu_count() * 4)) as executor:
            setup_futures = []
            for file_name, file_path in files_to_test:
                test_work_dir = os.path.join(work_dir, file_name.replace('.java', ''))
                if os.path.exists(test_work_dir):
                    shutil.rmtree(test_work_dir)
                os.makedirs(test_work_dir)
                
                # Submit setup tasks to thread pool
                future = executor.submit(setup_test_environment, file_path, [test_file], test_work_dir)
                setup_futures.append((future, file_name, test_work_dir))
                
                # Create build.gradle in parallel
                executor.submit(create_build_gradle, task_id, test_work_dir)
            
            # Wait for all setup tasks to complete
            for future, file_name, test_work_dir in setup_futures:
                try:
                    future.result()
                except Exception as e:
                    logging.error(f"Task {task_id}, file {file_name}: Failed to setup test environment: {str(e)}")

        # Now run all tests in parallel with optimized thread count
        with concurrent.futures.ThreadPoolExecutor(max_workers=min(8, os.cpu_count())) as executor:
            future_to_file = {
                executor.submit(run_test_for_file, 
                              file_name, 
                              os.path.join(work_dir, file_name.replace('.java', '')),
                              task_id): (file_name, file_path) 
                for file_name, file_path in files_to_test
            }
            
            for future in concurrent.futures.as_completed(future_to_file):
                file_name, file_path = future_to_file[future]
                try:
                    result = future.result()
                    test_results.append(result)
                except Exception as e:
                    logging.error(f"Task {task_id}, file {file_name}: Failed to execute test: {str(e)}")
        
        # Generate reports
        save_summary(test_results, task_id)
        
        # Clean up work directory after tests complete
        try:
            shutil.rmtree(work_dir)
        except Exception as e:
            logging.warning(f"Failed to clean up work directory for task {task_id}: {e}")
        
        return test_results
        
    except Exception as e:
        logging.error(f"Task {task_id}: Failed to process task: {str(e)}")
        return None

def main():
    try:
        gradle_bin = os.path.join(script_dir, GRADLE_DIR, "bin", "gradle")
        if os.name == 'nt':
            gradle_bin += '.bat'
            
        if not os.path.exists(gradle_bin):
            logging.error(f"Local Gradle installation not found at {gradle_bin}")
            logging.error("Please ensure the Gradle folder is in the same directory as this script")
            return

        # Updated argument parsing
        if len(sys.argv) != 3:
            logging.error(f"Usage: python {sys.argv[0]} <root_directory> <task_id>")
            logging.error("Example: python run_tests.py /path/to/tasks 123456")
            return

        global BASE_DIR
        # Convert to absolute path
        BASE_DIR = os.path.abspath(sys.argv[1])
        task_id = sys.argv[2]

        logging.info(f"Using base directory: {BASE_DIR}")
        logging.info(f"Processing task ID: {task_id}")

        # Validate task_id format (assuming it's a number)
        if not re.match(r'^\d+$', task_id):
            logging.error("Invalid task_id format. It should be a number.")
            return

        # Process the specified task
        with tqdm(total=1, desc="Overall Progress", unit="task") as pbar:
            results = process_task(task_id)
            if results:
                logging.info(f"Successfully processed task {task_id}")
            else:
                logging.warning(f"No results for task {task_id}")
            pbar.update(1)  # Update progress bar for the completed task

        # Optionally, clean up all work directories if needed
        # delete_work_dir()
        logging.info("Task processing completed!")
    except Exception as e:
        logging.critical(f"Unhandled exception in main: {e}", exc_info=True)

if __name__ == "__main__":
    main()
