# Java Test Runner Setup Guide

## Directory Structure
The test runner requires a specific directory structure:
```
.
├── code/           # Directory containing Java files to test
│   ├── A.java     # Single-letter solution files (A-J)
│   ├── base.java  # Other solution files
│   └── ...
├── test/          # Directory containing test files
│   └── MainTest.java
└── test_results/  # Generated automatically
```

## Test File Requirements
1. The test file must be named exactly `MainTest.java`
2. The test class must be declared as `public class MainTest`
3. Place the test file in the `test/` directory
4. Use JUnit Jupiter (JUnit 5) annotations for tests

## Code File Requirements
1. Place all Java files to be tested in the `code/` directory
2. Each file should contain exactly one public class
3. The script will automatically rename the public class to `Main` during testing

## Prerequisites
- Python 3.6 or higher
- Java Development Kit (JDK) 11 or higher
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
    // Add additional repositories if needed, e.g.:
    // maven { url 'https://jitpack.io' }
}

dependencies {
    // Existing dependencies
    implementation 'com.fasterxml.jackson.core:jackson-databind:2.15.2'
    implementation 'org.json:json:20230227'
    implementation 'org.jsoup:jsoup:1.18.3'

    // Add your custom dependencies here, for example:
    implementation 'org.apache.commons:commons-lang3:3.12.0'
    implementation 'com.google.guava:guava:31.1-jre'
    
    // For test dependencies, use testImplementation:
    testImplementation 'org.junit.jupiter:junit-jupiter-api:5.9.2'
    testImplementation 'org.mockito:mockito-junit-jupiter:5.15.2'
    testRuntimeOnly 'org.junit.jupiter:junit-jupiter-engine:5.9.2'
}
"""
```

Dependency formats:
- For regular dependencies: `implementation 'group:artifact:version'`
- For test dependencies: `testImplementation 'group:artifact:version'`
- For compile-only dependencies: `compileOnly 'group:artifact:version'`
- For annotation processors: `annotationProcessor 'group:artifact:version'`

You can find the correct dependency notation for most libraries on [Maven Central](https://mvnrepository.com/).

## Usage
1. Place your code files in the `code/` directory
2. Place `MainTest.java` in the `test/` directory
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

## Common Issues
- Ensure your code files contain only one public class
- Verify `MainTest.java` is properly named and contains `public class MainTest`
- Check that Java and Python are properly installed and accessible from the command line
- Make sure you have write permissions in the directory
- If adding new dependencies, verify they are compatible with your JDK version

## Default Dependencies
The script automatically sets up:
- JUnit Jupiter
- Mockito
- JaCoCo for code coverage
- Jackson Databind
- JSON library
- JSoup

Additional dependencies can be added as described in the "Managing Dependencies" section.