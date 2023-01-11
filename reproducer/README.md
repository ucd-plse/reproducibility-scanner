# Reproducer
This component reproduces a given bug from a dataset.

## Defects4J and GrowingBugs

Defects4J and GrowingBugs provide a script to reproduce a bug and verify the reproducibility. The script is located [here](https://github.com/rjust/defects4j/blob/master/framework/test/test_verify_bugs.sh). Our reproducer executes this script to get the result produced from running the fixed and buggy versions of each artifact.

## Bugs.jar

To the best of our knowledge, Bugs.jar is the only dataset that does *not* provide instructions or scripts to reproduce a bug in their benchmark. We reached out to the authors of the dataset for information on how to run their artifacts by emailing them, but they haven't responded after several weeks. We tried our best to reproduce all bugs in Bugs.jar, and we are able to confirm with high confidence that we are running the correct commands.

**Steps we followed to reproduce a bug in the Bugs.jar benchmark:**

1. Run `mvn install -DskipTests -fn` to install as many modules as possible.  
   - `-DskipTests`: do not run tests for now, just build and install the project.  
   - `-fn`: if current module fails to build, do not abort process, just skip to the next module.  

2. Extract from Bugs.jar's reference logs the list of modules to be tested.

3. Based on the list of modules to be tested, and whether the whole project is tested or only a few modules, run:
    - `mvn test`, or
    - `mvn test -pl <module 1> <module 2> …`

To validate that we are running the correct commands, we examine the number and names of executed tests, which we confirm that match Bugs.jar's reference log for each artifact.

## BugSwarm

Since BugSwarm packs each artifact into a Docker image, a given bug is reproduced by simply running the image as a container and executing `run_passed.sh` or `run_failed.sh` to run the fixed and buggy versions, respectively. 


## Bears

Bears provides [scripts](https://github.com/bears-bugs/bears-benchmark/tree/master/scripts) to build and run tests for each bug in the benchmark. The reproducer executes these scripts to get the results.
