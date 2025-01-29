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
    YELLOW = '\033[0;33m'
    NC = '\033[0m'

# Directory structure constants
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

def backup_solution_java(src_main_dir):
    """Backup the original Solution.java file"""
    solution_path = os.path.join(src_main_dir, "Solution.java")
    if os.path.exists(solution_path):
        backup_path = os.path.join(src_main_dir, "Solution.java.backup")
        shutil.copy2(solution_path, backup_path)
        return True
    return False

def restore_solution_java(src_main_dir):
    """Restore the original Solution.java file from backup"""
    backup_path = os.path.join(src_main_dir, "Solution.java.backup")
    solution_path = os.path.join(src_main_dir, "Solution.java")
    if os.path.exists(backup_path):
        shutil.copy2(backup_path, solution_path)
        os.remove(backup_path)
        return True
    return False

def get_task_directories(base_path):
    """Get all task directories that match the 6-digit pattern"""
    task_dirs = []
    for item in os.listdir(base_path):
        if re.match(r'^\d{6}$', item):
            full_path = os.path.join(base_path, item)
            if os.path.isdir(full_path):
                task_dirs.append(item)
    return sorted(task_dirs)

def cleanup():
    """Clean up build directories and files"""
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

def check_test_convention(test_file):
    """Check if test file references Solution or Main"""
    with open(test_file, 'r') as f:
        content = f.read()
    return 'Solution' in content

def process_java_file(file_path, src_main_dir):
    """Process a Java file and copy it to src/main/java as Solution.java"""
    with open(file_path, 'r') as f:
        content = f.read()
    
    # Change protected/private to public
    content = re.sub(r'\b(private|protected)\s+static', 'public static', content)
    content = re.sub(r'\b(private|protected)\s+final\s+static', 'public static final', content)
    content = re.sub(r'\b(private|protected)\s+', 'public ', content)
    
    # Get the main class name and replace it with Solution
    main_class = re.search(r'public class (\w+)', content)
    if main_class:
        content = re.sub(f'(?<!new )\\b{main_class.group(1)}\\b', 'Solution', content)
        content = re.sub(f'new {main_class.group(1)}\\(', 'new Solution(', content)
    
    # Write the processed content to Solution.java
    os.makedirs(src_main_dir, exist_ok=True)
    solution_path = os.path.join(src_main_dir, "Solution.java")
    with open(solution_path, 'w') as f:
        f.write(content)

def create_build_gradle(task_dir):
    """Create build.gradle file using template if it exists, otherwise use default config"""
    # Check for task-specific build.gradle template
    template_path = os.path.join(task_dir, "build.gradle.template")
    
    if os.path.exists(template_path):
        # If template exists, copy it directly
        with open(template_path, 'r') as src, open(BUILD_GRADLE_FILE, 'w') as dest:
            dest.write(src.read())
    else:
        # Fall back to default configuration
        default_gradle_content = """plugins {
    id 'java'
    id 'jacoco'
}

repositories {
    mavenCentral()
}

dependencies {
    testImplementation 'org.junit.jupiter:junit-jupiter-api:5.9.2'
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
            f.write(default_gradle_content)

def run_gradle(capture_output=True):
    """Run Gradle tests with coverage reporting"""
    subprocess.run(["gradle", "wrapper"], check=True, capture_output=capture_output)
    try:
        result = subprocess.run(["./gradlew", "test", "jacocoTestReport"], 
                              capture_output=capture_output, 
                              text=True,
                              timeout=30)  # 30 second timeout
        return result
    except subprocess.TimeoutExpired:
        print(f"{Colors.YELLOW}Test execution timed out after 30 seconds{Colors.NC}")
        return subprocess.CompletedProcess(args=[], returncode=1, stdout="", stderr="Test timed out")

def parse_jacoco_csv():
    """Parse JaCoCo coverage report"""
    coverage_file = "build/reports/jacoco/test/jacocoTestReport.csv"
    if not os.path.exists(coverage_file):
        return None

    metrics = CoverageMetrics()
    
    with open(coverage_file, 'r') as f:
        reader = csv.DictReader(f)
        for row in reader:
            if row['CLASS'].endswith('Solution'):
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
                break

    return metrics

def run_single_test(task_dir, source_name):
    """Run a single test for a given source file"""
    test_result = TestResult(source_name)
    
    try:
        cleanup()
        create_build_gradle()
        
        # Copy test file to src/test/java
        src_test_dir = os.path.join(task_dir, SRC_TEST)
        test_files = [f for f in os.listdir(src_test_dir) if f.endswith('Test.java')]
        if test_files:
            os.makedirs("src/test/java", exist_ok=True)
            for test_file in test_files:
                shutil.copy2(
                    os.path.join(src_test_dir, test_file),
                    os.path.join("src/test/java", test_file)
                )
        
        gradle_result = run_gradle(capture_output=True)
        test_result.output = gradle_result.stdout + gradle_result.stderr
        
        if 'compileJava FAILED' in test_result.output or 'error:' in test_result.output:
            test_result.status = "FAILED_TO_RUN"
            test_result.error = "Compilation failed"
        elif gradle_result.returncode == 0:
            test_result.status = "PASSED"
            test_result.coverage = parse_jacoco_csv()
            print(f"{Colors.GREEN}Successfully tested {source_name}{Colors.NC}")
        else:
            test_result.status = "FAILED"
            test_result.error = f"Tests failed with return code: {gradle_result.returncode}"
            print(f"{Colors.RED}Tests failed for {source_name}{Colors.NC}")
            
    except Exception as e:
        test_result.status = "FAILED_TO_RUN"
        test_result.error = str(e)
        print(f"{Colors.YELLOW}Failed to run tests for {source_name}: {e}{Colors.NC}")
    
    return test_result

def process_task(task_id, base_path):
    """Process a single task directory"""
    task_dir = os.path.join(base_path, task_id)
    src_main_dir = os.path.join(task_dir, SRC_MAIN)
    test_results = []

    # First test the ideal solution
    if os.path.exists(os.path.join(src_main_dir, "Solution.java")):
        # Backup original Solution.java
        backup_solution_java(src_main_dir)
        
        # Test the original solution
        test_result = run_single_test(task_dir, "ideal_solution")
        test_results.append(test_result)

        # Process base_code.java
        base_code_path = os.path.join(task_dir, "base_code.java")
        if os.path.exists(base_code_path):
            process_java_file(base_code_path, src_main_dir)
            test_result = run_single_test(task_dir, "base_code")
            test_results.append(test_result)

        # Process alternate responses
        alt_responses_dir = os.path.join(task_dir, "alternate_responses")
        if os.path.exists(alt_responses_dir):
            for file_name in os.listdir(alt_responses_dir):
                if file_name.endswith('.java'):
                    file_path = os.path.join(alt_responses_dir, file_name)
                    process_java_file(file_path, src_main_dir)
                    new_name = FILE_MAPPING.get(file_name, file_name)
                    test_result = run_single_test(task_dir, new_name)
                    test_results.append(test_result)
                    
                    # Restore original Solution.java after each test
                    restore_solution_java(src_main_dir)

    return test_results

def save_coverage_report(test_results, task_id, base_path):
    """Save coverage report to a file"""
    task_results_dir = os.path.join(base_path, task_id, RESULTS_DIR)
    os.makedirs(task_results_dir, exist_ok=True)
    coverage_file = os.path.join(task_results_dir, "coverage.txt")

    with open(coverage_file, 'w') as f:
        f.write("Code Coverage Report\n")
        f.write("===================\n\n")
        f.write(f"Generated: {datetime.now()}\n\n")
        
        # Add individual file coverage
        f.write("Individual File Coverage:\n")
        f.write("------------------------\n")
        for result in test_results:
            f.write(f"\n{result.file_name}:\n")
            if result.status == "PASSED" and result.coverage:
                f.write(f"  Line Coverage: {result.coverage.line_coverage:.2f}%\n")
                f.write(f"  Branch Coverage: {result.coverage.branch_coverage:.2f}%\n")
                f.write(f"  Instruction Coverage: {result.coverage.instruction_coverage:.2f}%\n")
            else:
                f.write(f"  No coverage data (Status: {result.status})\n")

def save_task_summary(test_results, task_id, base_path):
    """Save summary for a single task"""
    task_results_dir = os.path.join(base_path, task_id, RESULTS_DIR)
    os.makedirs(task_results_dir, exist_ok=True)
    summary_file = os.path.join(task_results_dir, "summary.txt")
    
    with open(summary_file, 'w') as f:
        f.write(f"Test Results Summary for Task {task_id}\n")
        f.write("=" * (30 + len(task_id)) + "\n\n")
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
        f.write(f"Pass Rate: {(passed/total*100):.2f}%\n\n" if total > 0 else "Pass Rate: N/A\n\n")
        
        # Detailed results
        f.write("Detailed Results:\n")
        f.write("----------------\n")
        if total == 0:
            f.write("No tests were run for this task.\n")
        else:
            for result in test_results:
                status_icon = "✅" if result.status == "PASSED" else "❌"
                f.write(f"{status_icon} {result.file_name}: {result.status}\n")
                if result.error:
                    f.write(f"   Error: {result.error}\n")

def save_global_summary(base_path, all_results):
    """Save a global summary of all tasks"""
    summary_file = os.path.join(base_path, "summary.txt")
    
    with open(summary_file, 'w') as f:
        f.write("Global Test Execution Summary\n")
        f.write("===========================\n\n")
        f.write(f"Generated: {datetime.now()}\n\n")
        
        # Overall statistics across all tasks
        total_tasks = len(all_results)
        total_tests = sum(len(results) for results in all_results.values())
        total_passed = sum(sum(1 for r in results if r.status == "PASSED") 
                         for results in all_results.values())
        
        f.write("Overall Statistics:\n")
        f.write("-----------------\n")
        f.write(f"Total tasks processed: {total_tasks}\n")
        f.write(f"Total tests run: {total_tests}\n")
        f.write(f"Total tests passed: {total_passed}\n")
        f.write(f"Overall pass rate: {(total_passed/total_tests*100):.2f}%\n\n" if total_tests > 0 else "Overall pass rate: N/A\n\n")
        
        # Model comparison statistics
        claude_passed = 0
        claude_total = 0
        llama_passed = 0
        llama_total = 0
        
        for results in all_results.values():
            for result in results:
                if result.file_name.upper() in ['A.JAVA', 'B.JAVA', 'C.JAVA', 'D.JAVA', 'E.JAVA']:
                    claude_total += 1
                    if result.status == "PASSED":
                        claude_passed += 1
                elif result.file_name.upper() in ['F.JAVA', 'G.JAVA', 'H.JAVA', 'I.JAVA', 'J.JAVA']:
                    llama_total += 1
                    if result.status == "PASSED":
                        llama_passed += 1
        
        f.write("Model Performance:\n")
        f.write("-----------------\n")
        if claude_total > 0:
            f.write(f"Claude (A-E):\n")
            f.write(f"  Tests run: {claude_total}\n")
            f.write(f"  Tests passed: {claude_passed}\n")
            f.write(f"  Pass rate: {(claude_passed/claude_total*100):.2f}%\n\n")
        else:
            f.write("Claude (A-E): No tests run\n\n")
        
        if llama_total > 0:
            f.write(f"Llama (F-J):\n")
            f.write(f"  Tests run: {llama_total}\n")
            f.write(f"  Tests passed: {llama_passed}\n")
            f.write(f"  Pass rate: {(llama_passed/llama_total*100):.2f}%\n\n")
        else:
            f.write("Llama (F-J): No tests run\n\n")
        
        # Per-task breakdown
        f.write("Task-by-Task Breakdown:\n")
        f.write("---------------------\n")
        for task_id, results in sorted(all_results.items()):
            passed = sum(1 for r in results if r.status == "PASSED")
            total = len(results)
            f.write(f"\nTask {task_id}:\n")
            f.write(f"  Tests run: {total}\n")
            f.write(f"  Tests passed: {passed}\n")
            f.write(f"  Pass rate: {(passed/total*100):.2f}%\n" if total > 0 else "  Pass rate: N/A\n")
            
            # Detailed results for this task
            if total == 0:
                f.write("  No tests were run for this task.\n")
            else:
                f.write("  Detailed results:\n")
                for result in results:
                    status_icon = "✅" if result.status == "PASSED" else "❌"
                    f.write(f"    {status_icon} {result.file_name}: {result.status}\n")
                    if result.error:
                        f.write(f"      Error: {result.error}\n")

def main():
    if len(sys.argv) != 2:
        print(f"{Colors.RED}Usage: python {sys.argv[0]} <base_path>{Colors.NC}")
        print("Example: python run_tests.py tasks/java_tasks")
        return

    base_path = sys.argv[1]
    if not os.path.exists(base_path):
        print(f"{Colors.RED}Base path '{base_path}' not found{Colors.NC}")
        return

    print(f"{Colors.GREEN}Starting Java code testing for all tasks in {base_path}...{Colors.NC}")

    # Get all task directories
    task_dirs = get_task_directories(base_path)
    all_results = {}

    # Create work directory
    work_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "work_dir")
    if os.path.exists(work_dir):
        shutil.rmtree(work_dir)
    os.makedirs(work_dir)
    original_dir = os.getcwd()
    os.chdir(work_dir)

    try:
        for task_id in task_dirs:
            print(f"\n{Colors.BLUE}Processing task {task_id}...{Colors.NC}")
            test_results = process_task(task_id, base_path)
            all_results[task_id] = test_results
            
            # Save individual task summary and coverage
            save_task_summary(test_results, task_id, base_path)
            save_coverage_report(test_results, task_id, base_path)

        # Save global summary
        save_global_summary(base_path, all_results)

        print(f"{Colors.GREEN}All tasks completed. Global summary saved in {base_path}/summary.txt{Colors.NC}")
    
    finally:
        # Change back to original directory and clean up
        os.chdir(original_dir)
        delete_work_dir()

if __name__ == "__main__":
    main()