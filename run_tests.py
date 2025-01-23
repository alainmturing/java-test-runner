import os
import re
import shutil
import subprocess
from pathlib import Path
from datetime import datetime
import csv
import sys

# Color codes for terminal output
class Colors:
    GREEN = '\033[0;32m'
    RED = '\033[0;31m'
    BLUE = '\033[0;34m'
    YELLOW = '\033[0;33m'  # Added yellow for FAILED_TO_RUN status
    NC = '\033[0m'  # No color

# Directory structure constants
BASE_DIR = "calibrated_tasks/java_tasks"
CODE_DIR = "code"
TEST_DIR = "test"
RESULTS_DIR = "test_results"
SRC_MAIN = "src/main/java"
SRC_TEST = "src/test/java"
BUILD_GRADLE_FILE = "build.gradle"
COVERAGE_FILE = os.path.join(RESULTS_DIR, "coverage.txt")

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
    "solution.java": "solution.java",
    "incorrect_solution.java": "incorrect.java",
}

class TestResult:
    def __init__(self, file_name):
        self.file_name = file_name
        self.status = "NOT_RUN"
        self.output = ""
        self.error = None
        self.timestamp = datetime.now()
        self.coverage = None

class CoverageMetrics:
    def __init__(self):
        self.instruction_coverage = 0
        self.branch_coverage = 0
        self.line_coverage = 0
        self.complexity_coverage = 0
        self.method_coverage = 0
        self.class_coverage = 0
        
        # Track raw numbers for calculating overall coverage
        self.total_lines = 0
        self.covered_lines = 0
        self.total_instructions = 0
        self.covered_instructions = 0
        self.total_branches = 0
        self.covered_branches = 0

def setup_task_directory(task_id):
    """
    Set up the code and test directories for the given task ID
    """
    # Get absolute path of the script's directory
    script_dir = os.path.dirname(os.path.abspath(__file__))
    
    # Construct absolute path to task directory
    task_dir = os.path.join(script_dir, BASE_DIR, task_id)
    
    # Debug information
    print(f"Current working directory: {os.getcwd()}")
    print(f"Looking for task directory at: {task_dir}")
    
    if not os.path.exists(task_dir):
        print(f"{Colors.RED}Task directory '{task_dir}' not found{Colors.NC}")
        return False

    # Create directories under the task directory
    task_code_dir = os.path.join(task_dir, CODE_DIR)
    task_test_dir = os.path.join(task_dir, TEST_DIR)
    task_results_dir = os.path.join(task_dir, RESULTS_DIR)
    
    os.makedirs(task_code_dir, exist_ok=True)
    os.makedirs(task_test_dir, exist_ok=True)
    os.makedirs(task_results_dir, exist_ok=True)

    # First handle the test file specifically
    test_file_path = os.path.join(task_dir, "test.java")
    if os.path.exists(test_file_path):
        dest_test_path = os.path.join(task_test_dir, "MainTest.java")
        shutil.copy2(test_file_path, dest_test_path)
        print(f"{Colors.BLUE}Copied test.java to {dest_test_path}{Colors.NC}")

    # Then handle all other .java files
    for file_name in os.listdir(task_dir):
        if file_name.endswith('.java') and file_name != 'test.java':
            orig_path = os.path.join(task_dir, file_name)
            new_name = FILE_MAPPING.get(file_name, file_name)  # Use mapping if exists, otherwise keep original name
            dest_path = os.path.join(task_code_dir, new_name)
            shutil.copy2(orig_path, dest_path)
            print(f"{Colors.BLUE}Copied {file_name} to {dest_path}{Colors.NC}")

    return True

def parse_jacoco_csv():
    coverage_file = "build/reports/jacoco/test/jacocoTestReport.csv"
    if not os.path.exists(coverage_file):
        return None

    metrics = CoverageMetrics()
    
    with open(coverage_file, 'r') as f:
        reader = csv.DictReader(f)
        for row in reader:
            # Look for either Main or Solution class
            if row['CLASS'].endswith('Main') or row['CLASS'].endswith('Solution'):  # Modified this line
                # Calculate raw numbers
                covered_instructions = int(row['INSTRUCTION_COVERED'])
                missed_instructions = int(row['INSTRUCTION_MISSED'])
                metrics.total_instructions = covered_instructions + missed_instructions
                metrics.covered_instructions = covered_instructions
                
                covered_branches = int(row['BRANCH_COVERED'])
                missed_branches = int(row['BRANCH_MISSED'])
                metrics.total_branches = covered_branches + missed_branches
                metrics.covered_branches = covered_branches
                
                covered_lines = int(row['LINE_COVERED'])
                missed_lines = int(row['LINE_MISSED'])
                metrics.total_lines = covered_lines + missed_lines
                metrics.covered_lines = covered_lines

                # Calculate percentages
                if metrics.total_instructions > 0:
                    metrics.instruction_coverage = (covered_instructions / metrics.total_instructions) * 100
                if metrics.total_branches > 0:
                    metrics.branch_coverage = (covered_branches / metrics.total_branches) * 100
                if metrics.total_lines > 0:
                    metrics.line_coverage = (covered_lines / metrics.total_lines) * 100
                break  # Added break since we found our class

    return metrics

def calculate_overall_coverage(test_results):
    total_lines = 0
    covered_lines = 0
    total_instructions = 0
    covered_instructions = 0
    total_branches = 0
    covered_branches = 0
    
    for result in test_results:
        if result.coverage and result.status == "PASSED":
            total_lines += result.coverage.total_lines
            covered_lines += result.coverage.covered_lines
            total_instructions += result.coverage.total_instructions
            covered_instructions += result.coverage.covered_instructions
            total_branches += result.coverage.total_branches
            covered_branches += result.coverage.covered_branches
    
    metrics = {
        'overall_coverage': (covered_lines / total_lines * 100) if total_lines > 0 else 0,
        'instruction_coverage': (covered_instructions / total_instructions * 100) if total_instructions > 0 else 0,
        'branch_coverage': (covered_branches / total_branches * 100) if total_branches > 0 else 0,
        'line_coverage': (covered_lines / total_lines * 100) if total_lines > 0 else 0
    }
    
    return metrics

def cleanup():
    print(f"{Colors.BLUE}Cleaning up build and src directories...{Colors.NC}")
    for directory in ["build", "src", ".gradle", "gradle", ".ropeproject"]:
        shutil.rmtree(directory, ignore_errors=True)
    for file in ["gradlew", "gradlew.bat", BUILD_GRADLE_FILE]:
        if os.path.exists(file):
            os.remove(file)

def delete_work_dir():
    """Delete work_dir in the same directory as run_tests.py"""
    script_dir = os.path.dirname(os.path.abspath(__file__))
    work_dir = os.path.join(script_dir, "work_dir")
    if os.path.exists(work_dir):
        shutil.rmtree(work_dir)

def find_java_files(directory):
    java_files = []
    for file_path in Path(directory).rglob("*.java"):
        if "build" not in str(file_path) and ".gradle" not in str(file_path):
            java_files.append(str(file_path))
    return java_files

def find_test_files(task_id):
    task_test_dir = os.path.join(BASE_DIR, task_id, TEST_DIR)
    return find_java_files(task_test_dir)

def find_code_files(task_id):
    task_code_dir = os.path.join(BASE_DIR, task_id, CODE_DIR)
    return find_java_files(task_code_dir)

def check_test_convention(test_file):
    """Check if test file references Solution or Main"""
    with open(test_file, 'r') as f:
        content = f.read()
    return 'Solution' in content

def get_class_name(content):
    """Extract the original class name from the file content"""
    match = re.search(r'public class (\w+)', content)
    return match.group(1) if match else None

def process_java_file(file_path, use_solution):
    with open(file_path, 'r') as f:
        content = f.read()
    
    target_class = "Solution" if use_solution else "Main"
    
    # Find all unique class names in the file
    class_pattern = r'(?:class|new|throws|extends|implements|\w+\s+)[\s\n]*(\w+)(?=[\s\n]*[{(\s])'
    class_names = set(re.findall(class_pattern, content))
    keywords = {'String', 'Integer', 'Boolean', 'Double', 'Float', 'List', 'Map', 'Set', 'Exception'}
    class_names = {name for name in class_names if name not in keywords}
    
    # Get the main class name
    main_class = re.search(r'public class (\w+)', content).group(1)
    
    # Replace all occurrences of the main class name
    content = re.sub(f'(?<!new )\\b{main_class}\\b', target_class, content)
    content = re.sub(f'new {main_class}\\(', f'new {target_class}(', content)
    
    return content


def setup_test_environment(code_file, test_files):
    # Create necessary directories
    os.makedirs(SRC_MAIN, exist_ok=True)
    os.makedirs(SRC_TEST, exist_ok=True)

    # Check test file convention
    uses_solution = check_test_convention(test_files[0])
    
    # Process main code file
    main_content = process_java_file(code_file, uses_solution)
    filename = "Solution.java" if uses_solution else "Main.java"
    main_file_path = os.path.join(SRC_MAIN, filename)
    with open(main_file_path, 'w') as f:
        f.write(main_content)

    # Copy test file
    for test_file in test_files:
        test_filename = "SolutionTest.java" if uses_solution else "MainTest.java"
        test_file_path = os.path.join(SRC_TEST, test_filename)
        shutil.copy2(test_file, test_file_path)

def save_coverage_report(test_results, task_id):
    """Save coverage report to a file"""
    # Get absolute path for results directory
    script_dir = os.path.dirname(os.path.abspath(__file__))
    task_results_dir = os.path.join(script_dir, BASE_DIR, task_id, RESULTS_DIR)
    os.makedirs(task_results_dir, exist_ok=True)
    coverage_file = os.path.join(task_results_dir, "coverage.txt")

    with open(coverage_file, 'w') as f:
        f.write("Code Coverage Report\n")
        f.write("===================\n\n")
        f.write(f"Generated: {datetime.now()}\n\n")
        
        # Add overall coverage section
        overall_metrics = calculate_overall_coverage(test_results)
        f.write("Overall Coverage Metrics:\n")
        f.write("------------------------\n")
        f.write(f"Overall Coverage: {overall_metrics['overall_coverage']:.2f}%\n")
        f.write(f"Total Instruction Coverage: {overall_metrics['instruction_coverage']:.2f}%\n")
        f.write(f"Total Branch Coverage: {overall_metrics['branch_coverage']:.2f}%\n")
        f.write(f"Total Line Coverage: {overall_metrics['line_coverage']:.2f}%\n\n")

        # Add individual file coverage
        f.write("Individual File Coverage:\n")
        f.write("------------------------\n")
        for result in test_results:
            f.write(f"\n{os.path.basename(result.file_name)}:\n")
            if result.status == "PASSED" and result.coverage:
                f.write(f"  Line Coverage: {result.coverage.line_coverage:.2f}%\n")
                f.write(f"  Branch Coverage: {result.coverage.branch_coverage:.2f}%\n")
                f.write(f"  Instruction Coverage: {result.coverage.instruction_coverage:.2f}%\n")
            else:
                f.write(f"  No coverage data (Status: {result.status})\n")
        
def run_tests(task_id):
    """
    Run tests for all code files against test files
    """
    # Get absolute paths for task directories
    script_dir = os.path.dirname(os.path.abspath(__file__))
    task_dir = os.path.join(script_dir, BASE_DIR, task_id)
    task_code_dir = os.path.join(task_dir, CODE_DIR)
    task_test_dir = os.path.join(task_dir, TEST_DIR)
    task_results_dir = os.path.join(task_dir, RESULTS_DIR)
    
    test_results = []

    # Find all code files in the code directory
    code_files = [f for f in os.listdir(task_code_dir) if f.endswith('.java')]
    test_files = [f for f in os.listdir(task_test_dir) if f.endswith('.java')]

    if not code_files:
        print(f"{Colors.RED}No Java files found in {task_code_dir} directory{Colors.NC}")
        return test_results

    if not test_files:
        print(f"{Colors.RED}No test files found in {task_test_dir} directory{Colors.NC}")
        return test_results

    print(f"{Colors.GREEN}Found {len(code_files)} code files and {len(test_files)} test files{Colors.NC}")

    # Create and move to work directory for testing
    work_dir = os.path.join(script_dir, "work_dir")
    if os.path.exists(work_dir):
        shutil.rmtree(work_dir)
    os.makedirs(work_dir)
    original_dir = os.getcwd()
    os.chdir(work_dir)

    for code_file in code_files:
        code_file_path = os.path.join(task_code_dir, code_file)
        print(f"\n{Colors.BLUE}Testing {code_file}{Colors.NC}")
        
        test_result = TestResult(code_file)
        
        try:
            # Clean working directory for each test
            cleanup()
            
            # Use the new setup_test_environment function that handles the naming convention
            test_file_paths = [os.path.join(task_test_dir, test_file) for test_file in test_files]
            setup_test_environment(code_file_path, test_file_paths)
            
            create_build_gradle()
            
            gradle_result = run_gradle(capture_output=True)
            test_result.output = gradle_result.stdout + gradle_result.stderr
            
            if 'compileJava FAILED' in test_result.output or 'error:' in test_result.output:
                test_result.status = "FAILED_TO_RUN"
                test_result.error = "Compilation failed"
            elif gradle_result.returncode == 0:
                test_result.status = "PASSED"
                test_result.coverage = parse_jacoco_csv()
                print(f"{Colors.GREEN}Successfully tested {code_file}{Colors.NC}")
            else:
                test_result.status = "FAILED"
                test_result.error = f"Tests failed with return code: {gradle_result.returncode}"
                print(f"{Colors.RED}Tests failed for {code_file}{Colors.NC}")
                
        except Exception as e:
            test_result.status = "FAILED_TO_RUN"
            test_result.error = str(e)
            print(f"{Colors.YELLOW}Failed to run tests for {code_file}: {e}{Colors.NC}")
        
        # Save individual test result in task-specific results directory
        save_test_result(test_result, task_id)
        test_results.append(test_result)
        cleanup()
    
    # Change back to original directory and clean up work directory
    os.chdir(original_dir)
    if os.path.exists(work_dir):
        shutil.rmtree(work_dir)
    
    return test_results

def save_test_result(test_result, task_id):
    """Save individual test result to a file"""
    # Get absolute path for results directory
    script_dir = os.path.dirname(os.path.abspath(__file__))
    task_results_dir = os.path.join(script_dir, BASE_DIR, task_id, RESULTS_DIR)
    os.makedirs(task_results_dir, exist_ok=True)
    
    # Save individual test result
    file_name = os.path.basename(test_result.file_name)
    result_file = os.path.join(task_results_dir, f"{file_name.split('.java')[0]}.txt")
    
    with open(result_file, 'w') as f:
        f.write(f"Test Results for {file_name}\n")
        f.write("=" * (16 + len(file_name)) + "\n\n")
        f.write(f"Timestamp: {test_result.timestamp}\n")
        f.write(f"Status: {test_result.status}\n")
        if test_result.coverage:
            f.write("\nCoverage Metrics:\n")
            f.write("-----------------\n")
            f.write(f"Line Coverage: {test_result.coverage.line_coverage:.2f}%\n")
            f.write(f"Branch Coverage: {test_result.coverage.branch_coverage:.2f}%\n")
            f.write(f"Instruction Coverage: {test_result.coverage.instruction_coverage:.2f}%\n")
        f.write("\nTest Output:\n")
        f.write("-----------\n")
        f.write(test_result.output)
        if test_result.error:
            f.write("\nErrors:\n")
            f.write("-------\n")
            f.write(str(test_result.error))

def save_summary(test_results, task_id):
    """Save summary of all test results"""
    script_dir = os.path.dirname(os.path.abspath(__file__))
    task_results_dir = os.path.join(script_dir, BASE_DIR, task_id, RESULTS_DIR)
    os.makedirs(task_results_dir, exist_ok=True)
    summary_file = os.path.join(task_results_dir, "summary.txt")
    
    def is_letter_file(filename):
        return bool(re.match(r'^[A-Za-z]\.java$', filename))
    
    def categorize_results(results):
        claude_tests = []
        llama_tests = []
        other_tests = []
        
        for result in results:
            file_name = os.path.basename(result.file_name)
            if is_letter_file(file_name):
                first_letter = file_name[0].upper()
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
            status_icon = "✅" if result.status == "PASSED" else "❌"
            f.write(f"{status_icon} {os.path.basename(result.file_name)}: {result.status}\n")

def create_build_gradle():
    gradle_content = """plugins {
    id 'java'
    id 'jacoco'
}

repositories {
    mavenCentral()
}

dependencies {
    implementation 'org.springframework:spring-core:5.3.20'
    testImplementation 'org.junit.jupiter:junit-jupiter:5.10.0'
}

test {
    useJUnitPlatform()
    finalizedBy jacocoTestReport

    testLogging {
        events 'passed', 'skipped', 'failed'
        showExceptions true
        showCauses true
        showStackTraces true
        exceptionFormat = 'full'
    }
}

jacocoTestReport {
    reports {
        csv.required = true
        html.required = true
    }
}                                                                                                                                                                                         
"""
    with open(BUILD_GRADLE_FILE, "w") as f:
        f.write(gradle_content)

def run_gradle(capture_output=True):
    subprocess.run(["gradle", "wrapper"], check=True, capture_output=capture_output)
    result = subprocess.run(["./gradlew", "test", "jacocoTestReport"], 
                          capture_output=capture_output, text=True)
    return result

def main():
    # Declare global at the start of the function
    global RESULTS_DIR
    
    if len(sys.argv) != 2:
        print(f"{Colors.RED}Usage: python {sys.argv[0]} <task_id>{Colors.NC}")
        print("Example: python run_tests.py 304027")
        return

    task_id = sys.argv[1]
    if not re.match(r'^\d{6}$', task_id):
        print(f"{Colors.RED}Invalid task ID format. Must be a 6-digit number.{Colors.NC}")
        return

    print(f"{Colors.GREEN}Starting Java code testing for task {task_id}...{Colors.NC}")

    # Set task-specific results directory - MODIFIED THIS LINE
    RESULTS_DIR = "test_results"  # Instead of os.path.join(BASE_DIR, task_id, RESULTS_DIR)

    # Set up the task directory structure
    if not setup_task_directory(task_id):
        return

    # Run tests and get results
    test_results = run_tests(task_id)
    
    # Save summary and coverage report
    save_summary(test_results, task_id)
    save_coverage_report(test_results, task_id)

    print(f"{Colors.GREEN}All tests completed. Results and coverage report saved in {RESULTS_DIR} directory.{Colors.NC}")
     # Delete work_dir at the end
    delete_work_dir()
if __name__ == "__main__":
    main()