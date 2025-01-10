import os
import re
import shutil
import subprocess
from pathlib import Path
from datetime import datetime

# Color codes for terminal output
class Colors:
    GREEN = '\033[0;32m'
    RED = '\033[0;31m'
    BLUE = '\033[0;34m'
    YELLOW = '\033[0;33m'  # Added yellow for FAILED_TO_RUN status
    NC = '\033[0m'  # No color

# Directory structure constants
CODE_DIR = "code"
TEST_DIR = "test"
RESULTS_DIR = "test_results"
SRC_MAIN = "src/main/java"
SRC_TEST = "src/test/java"
BUILD_GRADLE_FILE = "build.gradle"

class TestResult:
    def __init__(self, file_name):
        self.file_name = file_name
        self.status = "NOT_RUN"  # NOT_RUN, PASSED, FAILED, FAILED_TO_RUN
        self.output = ""
        self.error = None
        self.timestamp = datetime.now()

def cleanup():
    print(f"{Colors.BLUE}Cleaning up build and src directories...{Colors.NC}")
    for directory in ["build", "src", ".gradle", "gradle", ".ropeproject"]:
        shutil.rmtree(directory, ignore_errors=True)
    for file in ["gradlew", "gradlew.bat", BUILD_GRADLE_FILE]:
        if os.path.exists(file):
            os.remove(file)

def find_java_files(directory):
    java_files = []
    for file_path in Path(directory).rglob("*.java"):
        if "build" not in str(file_path) and ".gradle" not in str(file_path):
            java_files.append(str(file_path))
    return java_files

def find_test_files():
    return find_java_files(TEST_DIR)

def find_code_files():
    return find_java_files(CODE_DIR)

def process_java_file(file_path):
    with open(file_path, 'r') as f:
        content = f.read()
    
    # Match the public class name
    match = re.search(r'public class ([A-Za-z0-9_]+)', content)
    if not match:
        print(f"Could not find public class in {file_path}")
        return content

    original_class_name = match.group(1)
    print(f"Renaming class {original_class_name} to Main")

    # Replace all occurrences of the original class name with "Main"
    updated_content = re.sub(rf'\b{original_class_name}\b', "Main", content)
    
    return updated_content

def setup_test_environment(code_file, test_files):
    # Create necessary directories
    os.makedirs(SRC_MAIN, exist_ok=True)
    os.makedirs(SRC_TEST, exist_ok=True)

    # Process and copy the main code file
    print(f"\nProcessing main code file: {code_file}")
    main_content = process_java_file(code_file)
    main_file_path = os.path.join(SRC_MAIN, "Main.java")
    with open(main_file_path, 'w') as f:
        f.write(main_content)

    # Copy test files without modification
    for test_file in test_files:
        print(f"\nCopying test file: {test_file}")
        test_file_name = os.path.basename(test_file)
        test_file_path = os.path.join(SRC_TEST, test_file_name)
        shutil.copy2(test_file, test_file_path)

def run_tests():
    code_files = find_java_files(CODE_DIR)
    test_files = find_java_files(TEST_DIR)
    test_results = []

    if not code_files:
        print(f"{Colors.RED}No Java files found in {CODE_DIR} directory{Colors.NC}")
        return test_results

    if not test_files:
        print(f"{Colors.RED}No test files found in {TEST_DIR} directory{Colors.NC}")
        return test_results

    print(f"{Colors.GREEN}Found {len(code_files)} code files and {len(test_files)} test files{Colors.NC}")

    for code_file in code_files:
        print(f"\n{Colors.BLUE}Testing {code_file}{Colors.NC}")
        
        test_result = TestResult(code_file)
        
        # Clean previous build
        cleanup()
        
        try:
            # Set up the test environment
            setup_test_environment(code_file, test_files)
            
            # Create Gradle build script
            create_build_gradle()
            
            # Run Gradle commands and capture output
            gradle_result = run_gradle(capture_output=True)
            test_result.output = gradle_result.stdout + gradle_result.stderr
            
            # Check if there were compilation errors
            if 'compileJava FAILED' in test_result.output or 'error:' in test_result.output:
                test_result.status = "FAILED_TO_RUN"
                test_result.error = "Compilation failed"
            elif gradle_result.returncode == 0:
                test_result.status = "PASSED"
                print(f"{Colors.GREEN}Successfully tested {code_file}{Colors.NC}")
            else:
                test_result.status = "FAILED"
                test_result.error = f"Tests failed with return code: {gradle_result.returncode}"
                print(f"{Colors.RED}Tests failed for {code_file}{Colors.NC}")
                
        except Exception as e:
            test_result.status = "FAILED_TO_RUN"
            test_result.error = str(e)
            print(f"{Colors.YELLOW}Failed to run tests for {code_file}: {e}{Colors.NC}")
        
        # Save test result
        save_test_result(test_result)
        test_results.append(test_result)
        
        # Cleanup after each test
        cleanup()
    
    return test_results

def save_test_result(test_result):
    # Create results directory if it doesn't exist
    os.makedirs(RESULTS_DIR, exist_ok=True)
    
    # Save individual test result
    file_name = os.path.basename(test_result.file_name)
    result_file = os.path.join(RESULTS_DIR, f"{file_name.split('.java')[0]}.txt")
    
    with open(result_file, 'w') as f:
        f.write(f"Test Results for {file_name}\n")
        f.write(f"Timestamp: {test_result.timestamp}\n")
        f.write(f"Status: {test_result.status}\n")
        f.write("\nTest Output:\n")
        f.write(test_result.output)
        if test_result.error:
            f.write("\nErrors:\n")
            f.write(str(test_result.error))

def save_summary(test_results):
    summary_file = os.path.join(RESULTS_DIR, "summary.txt")
    
    def is_letter_file(filename):
        # Check if the filename is a single letter (case insensitive) followed by .java
        return bool(re.match(r'^[A-Za-z]\.java$', filename))
    
    def categorize_results(results):
        claude_tests = []
        llama_tests = []
        
        for result in results:
            file_name = os.path.basename(result.file_name)
            if is_letter_file(file_name):
                first_letter = file_name[0].upper()
                if 'A' <= first_letter <= 'E':
                    claude_tests.append(result)
                elif 'F' <= first_letter <= 'J':
                    llama_tests.append(result)
        
        return claude_tests, llama_tests
    
    def calculate_stats(tests):
        if not tests:
            return 0, 0, 0, 0, 0  # total, passed, failed, pass_percent, fail_percent
        
        total = len(tests)
        passed = sum(1 for r in tests if r.status == "PASSED")
        failed = sum(1 for r in tests if r.status == "FAILED")
        failed_to_run = sum(1 for r in tests if r.status == "FAILED_TO_RUN")
        
        pass_percent = (passed / total) * 100 if total > 0 else 0
        fail_percent = ((failed + failed_to_run) / total) * 100 if total > 0 else 0
        
        return total, passed, failed + failed_to_run, pass_percent, fail_percent
    
    claude_tests, llama_tests = categorize_results(test_results)
    
    with open(summary_file, 'w') as f:
        f.write("Test Execution Summary\n")
        f.write("=====================\n\n")
        f.write(f"Timestamp: {datetime.now()}\n\n")
        
        # Overall statistics (including all files)
        total = len(test_results)
        passed = sum(1 for r in test_results if r.status == "PASSED")
        failed = sum(1 for r in test_results if r.status == "FAILED")
        failed_to_run = sum(1 for r in test_results if r.status == "FAILED_TO_RUN")
        
        f.write("Overall Results (All Files):\n")
        f.write("---------------------------\n")
        f.write(f"Total files tested: {total}\n")
        f.write(f"Passed: {passed}\n")
        f.write(f"Failed: {failed}\n")
        f.write(f"Failed to Run: {failed_to_run}\n\n")
        
        # Model Comparison Statistics (letter files only)
        f.write("Model Comparison Statistics (Letter Files Only):\n")
        f.write("--------------------------------------------\n\n")
        
        # Claude model statistics (A-E)
        c_total, c_passed, c_failed, c_pass_pct, c_fail_pct = calculate_stats(claude_tests)
        f.write("Claude Model Tests (A-E):\n")
        f.write("------------------------\n")
        f.write(f"Total tests: {c_total}\n")
        f.write(f"Passed: {c_passed}\n")
        f.write(f"Failed/Failed to Run: {c_failed}\n")
        f.write(f"Pass percentage: {c_pass_pct:.2f}%\n")
        f.write(f"Fail percentage: {c_fail_pct:.2f}%\n\n")
        
        # Llama model statistics (F-J)
        l_total, l_passed, l_failed, l_pass_pct, l_fail_pct = calculate_stats(llama_tests)
        f.write("Llama Model Tests (F-J):\n")
        f.write("------------------------\n")
        f.write(f"Total tests: {l_total}\n")
        f.write(f"Passed: {l_passed}\n")
        f.write(f"Failed/Failed to Run: {l_failed}\n")
        f.write(f"Pass percentage: {l_pass_pct:.2f}%\n")
        f.write(f"Fail percentage: {l_fail_pct:.2f}%\n\n")
        
        f.write("Detailed Results:\n")
        f.write("----------------\n")
        for result in test_results:
            if result.status == "PASSED":
                status_icon = "✅"
            elif result.status == "FAILED":
                status_icon = "❌"
            else:  # FAILED_TO_RUN
                status_icon = "⚠️"
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
    implementation 'com.fasterxml.jackson.core:jackson-databind:2.15.2'
    implementation 'org.json:json:20230227'
    implementation 'org.jsoup:jsoup:1.18.3'

    testImplementation 'org.junit.jupiter:junit-jupiter-api:5.9.2'
    testImplementation 'org.mockito:mockito-junit-jupiter:5.15.2'
    testRuntimeOnly 'org.junit.jupiter:junit-jupiter-engine:5.9.2'
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
    print(f"{Colors.GREEN}Starting Java code testing...{Colors.NC}")
    
    # Ensure the required directories exist
    if not os.path.exists(CODE_DIR):
        print(f"{Colors.RED}Code directory '{CODE_DIR}' not found{Colors.NC}")
        return
    
    if not os.path.exists(TEST_DIR):
        print(f"{Colors.RED}Test directory '{TEST_DIR}' not found{Colors.NC}")
        return

    # Create results directory if it doesn't exist
    os.makedirs(RESULTS_DIR, exist_ok=True)

    # Run the tests and get results
    test_results = run_tests()

    # Generate summary
    save_summary(test_results)

    # Final cleanup
    print(f"{Colors.GREEN}All tests completed. Results saved in {RESULTS_DIR} directory.{Colors.NC}")
    cleanup()

if __name__ == "__main__":
    main()