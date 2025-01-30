# Java Test Execution Scripts

This repository contains two Python scripts for executing Java unit tests across multiple solution files. The scripts are designed to handle batch processing of multiple tasks and provide detailed test results and summaries.

## Setup

### Repository Structure
Your repository should look like this:
```
your_repository/
├── tasks/
│   └── java_tasks/
│       ├── 000001/
│       │   ├── src/
│       │   │   ├── main/java/Solution.java
│       │   │   └── test/java/SolutionTest.java
│       │   ├── base_code.java
│       │   ├── installed_packages.txt
│       │   └── alternate_responses/
│       │       ├── model1.java
│       │       ├── model2.java
│       │       └── ...
│       ├── 000002/
│       └── ...
├── gradle-8.10.2/
├── run_solutions.py
└── run_specific_task.py
```

## Prerequisites

- Python 3.7+
- Java JDK 8 or higher
- Gradle 8.10.2 (must be in the same directory as the scripts)
- Required Python packages:
  - tqdm
  - logging
  - concurrent.futures

## Usage Examples

### Running All Solutions

To run tests for all solution files in the tasks/java_tasks directory:

```bash
# From the repository root
python run_solutions.py tasks/java_tasks
```

This will:
- Process all task directories under tasks/java_tasks
- Run tests in batches of 5 tasks
- Create test results in each task's directory
- Generate summary reports

### Running a Specific Task

To run tests for a specific task (e.g., task 000001):

```bash
# From the repository root
python run_specific_task.py tasks/java_tasks 000001
```

This will:
- Process only task 000001
- Test all code variations (base, solution, model responses)
- Create test results in tasks/java_tasks/000001/test_results/

## Directory Structure Details

### Task Directory Structure
Each task directory (e.g., 000001) should contain:

```
000001/
├── src/
│   ├── main/java/
│   │   └── Solution.java          # Ideal solution
│   └── test/java/
│       └── SolutionTest.java      # Unit tests
├── base_code.java                 # Initial/base code
├── installed_packages.txt         # Gradle dependencies
├── alternate_responses/           # Model-generated solutions
│   ├── A.java                    # Claude response 1
│   ├── B.java                    # Claude response 2
│   ├── C.java                    # Claude response 3
│   ├── D.java                    # Claude response 4
│   ├── E.java                    # Claude response 5
│   ├── F.java                    # Llama response 1
│   ├── G.java                    # Llama response 2
│   ├── H.java                    # Llama response 3
│   ├── I.java                    # Llama response 4
│   └── J.java                    # Llama response 5
└── test_results/                 # Generated test results
    ├── summary.txt               # Test summary report
    ├── base.txt                  # Base code test results
    ├── solution.txt              # Solution test results
    └── ...                       # Model response results
```


## Test Results

Both scripts generate test results in the following structure:

```
task_directory/
└── test_results/
    ├── summary.txt
    ├── base.txt
    ├── solution.txt
    ├── A.txt
    ├── B.txt
    └── ...
```

### Summary Report Format

The summary report includes:
- Overall test statistics
- Pass/fail rates
- Model comparison (Claude vs Llama)
- Detailed results for each tested file

## Common Features

Both scripts share the following features:

- **Logging**: Detailed logs are written to `run_tests.log`
- **Error Handling**: Comprehensive error catching and reporting
- **Resource Cleanup**: Automatic cleanup of temporary work directories
- **Gradle Integration**: Local Gradle execution with proper isolation
- **Dependency Management**: Automatic handling of project dependencies
- **Test Environment Setup**: Automated setup of test environments

## Error Handling

The scripts handle various error conditions:
- Missing directories/files
- Gradle execution failures
- Test timeouts (60-second limit)
- Build failures
- Invalid task IDs

## Performance Considerations

- Uses thread pools for parallel execution
- Optimized Gradle configuration
- Efficient resource cleanup
- Memory-conscious batch processing
- Task-specific Gradle user home directories

## Logging

Logs are written to `run_tests.log` with different verbosity levels:
- DEBUG: Detailed execution information
- INFO: General progress updates
- WARNING: Non-critical issues
- ERROR: Critical issues that affect execution

## Known Limitations

- Requires specific directory structure
- Depends on local Gradle installation
- Fixed timeout of 60 seconds per test
- Memory usage increases with parallel execution
- Limited to JUnit tests

## Troubleshooting

1. **Gradle Not Found**:
   - Ensure gradle-8.10.2 directory is present
   - Check gradle binary permissions

2. **Test Failures**:
   - Check test_results directory for detailed output
   - Review run_tests.log for error messages
   - Verify Java version compatibility

3. **Performance Issues**:
   - Reduce batch size if memory usage is high
   - Check system resources