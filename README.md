# Reproducibility Scanner 

## Usage 

### Requirements

- Ubuntu 18.04 or 20.04
- JDK 8 and JDK 11
- Maven 3.0.5 or later
- Python 3.8
- Python3-virtualenv
- Git >= 1.9
- [SVN](https://subversion.apache.org/packages.html) >= 1.8
- [Perl](https://learn.perl.org/installing/unix_linux.html) >= 5.0.12

### Installation
1. Clone the repository with submodules. This may take a while since there are large projects in benchmarks. 

    ``` sh
    git clone --recurse-submodules -j5 git@github.com:ucd-plse/Reproducibility-Scanner.git
    cd Reproducibility-Scanner
    ```

2. Create and activate a Python virtual environment.

    ``` sh
    virtualenv -p python3.8 venv
    . venv/bin/activate
    ```

3. Install Docker SDK for Python
   
    ``` sh
    pip install docker==2.5.1
    ```

4. Run initialize script. This may take 40 mins or so depending on the network condition.
   
    ``` sh
    python init.py
    ```

5. Check default Java version. Defects4J requires Java 8 as the default.

    ``` sh
    java -version
    ```
    
    The output should be version `1.8.0` for OpenJDK or Oracle JDK. If not, please refer to [How to set default Java version?](https://askubuntu.com/questions/121654/how-to-set-default-java-version)

6. Run the Reproducibility Scanner

    ``` sh
    python scan4r.py -b <benchmark> -i <bug_id> -l <file> -a
    ```

    `-b` | `--benchmark`: the name of the benchmark. Must be one of `defects4j, bears, bugswarm, growingbugs, bugs.jar`  
    `-i` | `--id`: the id of bug to reproduce. When there is no id inputted, it will reproduce all bugs in the benchmark.  
    `-l` | `--list`: the path to a text file containing a list of bug ids with one ID in one line.   
    `-a` | `--analyze-only`: do not reproduce and run the test, just analyze the existing log.

# Examples

1. Reproduce bug `Cli-1` in `defects4j` benchmark:
    ``` sh
    python scan4r.py -b defects4j -i Cli-1
    ```

2. Reproduce bugs in `bears` benchmark with bug ids in `bears_sample.txt`:
    ``` sh
    python scan4r.py -b bears -l bears_sample.txt
    ```

3. Reproduce all bugs in `growingbugs` benchmark:
    ``` sh
    python scan4r.py -b growingbugs
    ```

4. Analyze reproduced log for one bug in `bugs.jar` benchmark:
    ``` sh
    python scan4r.py -b bugs.jar -i bugs-dot-jar_WICKET-5565_204849bc -a
    ```

5. Analyze reproduced log for all bugs in `bugswarm` benchmark:
    ``` sh
    python scan4r.py -b bugswarm -a
    ```
