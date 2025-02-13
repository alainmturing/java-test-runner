# Java Test Runner Setup Guide

## Directory Structure
The test runner requires a specific directory structure:
```
.
├── code/ # Directory containing Java files to test
│ ├── A.java # Single-letter solution files (A-J)
│ ├── base.java
│ ├── solution.java
│ ├── incorrect.java
│ └── ...
├── test/ # Directory containing test files
│ └── SolutionTest.java
└── test_results/ # Generated automatically
    ├── summary.txt # Overall test results
    ├── coverage.txt # Code coverage report
    └── ... # Individual test results
```

## Test File Requirements
1. The test file must be named exactly `SolutionTest.java`
2. The test class must be declared as `public class SolutionTest`
3. Place the test file in the `test/` directory
4. Use JUnit Jupiter (JUnit 5) annotations for tests

## Code File Requirements
1. Place all Java files to be tested in the `code/` directory
2. Each file should contain exactly one public class. If your code has multiple classes, there should be one top level public class, at most 1.
3. The script will automatically rename the public class to `Solution` during testing

## Prerequisites
- Python 3.6 or higher
- Java Development Kit (JDK) 21
- Gradle (will be automatically downloaded by the wrapper)

## Installation
1. Save the test runner script as `run_tests.py`
2. Create the required directories:
```bash
mkdir code
mkdir test
```

## Managing Dependencies
To add custom dependencies for your Java code:
1. Locate the `create_build_gradle()` function in the script (around line 250)
2. Add new dependencies in the `dependencies` block. For example:
```python
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
```

Dependency formats:
- For regular dependencies: `implementation 'group:artifact:version'`
- For test dependencies: `testImplementation 'group:artifact:version'`
- For compile-only dependencies: `compileOnly 'group:artifact:version'`
- For annotation processors: `annotationProcessor 'group:artifact:version'`

You can find the correct dependency notation for most libraries on [Maven Central](https://mvnrepository.com/).

## Installed Packages Field

For the installed packages field on a task form, you are to fill it in with the gradle content you used for your task and include only the dependencies needed for that task. For example, if a task doesn't have any dependencies then it would just need junit, so it would look as follows:

```
plugins {
    id 'java'
    id 'jacoco'
}

repositories {
    mavenCentral()
    // Add additional repositories if needed, e.g.:
    // maven { url 'https://jitpack.io' }
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
```

## Usage
1. Place your code files in the `code/` directory
2. Place `SolutionTest.java` in the `test/` directory
3. Run the script:
```bash
python run_tests.py
```

## Output
The script will:
1. Generate a `test_results/` directory
2. Create individual test result files for each code file
3. Generate a `summary.txt` containing:
   - Overall test statistics
   - Specific statistics for letter-based files (A-E for Claude, F-J for Llama)
   - Detailed results for each file
4. Generate a `coverage.txt` containing:
   - Code coverage metrics for each tested file
   - Instruction coverage percentage
   - Branch coverage percentage
   - Line coverage percentage

## Coverage Report
The coverage report (`coverage.txt`) provides detailed metrics about test coverage:
- **Instruction Coverage**: Percentage of Java bytecode instructions that were executed
- **Branch Coverage**: Percentage of code branches (if/else statements, switches) that were executed
- **Line Coverage**: Percentage of code lines that were executed

Coverage data is collected using JaCoCo and is generated automatically for each successfully tested file.

## Common Issues
- Ensure your code files contain only one public class
- Verify `SolutionTest.java` is properly named and contains `public class SolutionTest`
- Check that Java and Python are properly installed and accessible from the command line
- Make sure you have write permissions in the directory
- If adding new dependencies, verify they are compatible with your JDK version
- If coverage report is missing, ensure tests ran successfully and JaCoCo plugin is properly configured

## Default Dependencies
The script automatically sets up:
- JUnit Jupiter
- Mockito
- JaCoCo for code coverage
- Jackson Databind
- JSON library
- JSoup

Additional dependencies can be added as described in the "Managing Dependencies" section.