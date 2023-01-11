import os, sys
import logging
import git
import xml.etree.ElementTree as ET

from utils import _run_command

bugsjar_path = '{}/benchmarks/bugs-dot-jar'.format(os.getcwd())
output_dir = '{}/outputs/bugs-dot-jar'.format(os.getcwd())


logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s %(levelname)-8s %(message)s',
                    datefmt='%Y-%m-%d %H:%M:%S')

class bugsjarReproducer(object):

    projects = ['maven', 'jackrabbit-oak', 'logging-log4j2', 'camel', 'accumulo', 'commons-math', 'wicket', 'flink']    
    project_dirs = {'ACCUMULO': 'accumulo', 'CAMEL': 'camel', 'FLINK': 'flink', 'LOG4J2': 'logging-log4j2', 'MATH': 'commons-math', 'OAK': 'jackrabbit-oak', 'WICKET': 'wicket', 'MNG': 'maven'}

    def __init__(self):
        pass

    @staticmethod
    def reproduce_buggy(bug_id):
        project_identifier = bug_id.split('_')[1].split('-')[0]
        project_dir = bugsjarReproducer.project_dirs[project_identifier]
        # check out to the bug branch and make sure it's clean

        repo = git.Repo('{}/{}'.format(bugsjar_path, project_dir))
        repo.git.checkout(bug_id)
        repo.git.clean('-fdx')
        repo.git.reset('--hard', 'HEAD')
        repo.git.checkout(['--', '.'])

        # install all dependencies
        # note we use -fn here to install as much dependencies as possible
        # it will continue to install dependencies regardless of the result of last goal
        _, stdout, stderr, ok = _run_command('mvn install -DskipTests -fn', cwd='{}/{}'.format(bugsjar_path, project_dir))
        build_log = stdout + stderr

        # run the test goal
        # note that in original bugs-dot-jar bugs, there was only one test goal run per bug
        # we identified the test goal run by bugs-dot-jar authors
        # and reproduce by running test of the same goal
        test_module = bugsjarReproducer.extract_tested_module(project_dir)

        if test_module != [None]:
            # multiple (in most cases only one) submodules were tested in the original test
            # so we reproduce the same
            _, stdout, stderr, ok =  _run_command('mvn test -pl {}'.format(' '.join(test_module)), cwd='{}/{}'.format(bugsjar_path, project_dir))
        else:
            # the whole project was tested in the original test
            _, stdout, stderr, ok =  _run_command('mvn test', cwd='{}/{}'.format(bugsjar_path, project_dir))
        test_log = stdout +stderr

        # write test log to file
        if not os.path.isdir('{}/reproduced/buggy'.format(output_dir)):
            _, stdout, stderr, ok = _run_command('mkdir -p {}/reproduced/buggy'.format(output_dir))
            if not ok:
                logging.error('Failed to create directory {}/reproduced/buggy'.format(output_dir))
                sys.exit(1)

        with open('{}/reproduced/buggy/{}.log'.format(output_dir, bug_id), 'w') as f:
            f.write(build_log)
            f.write('\n')
            f.write(test_log)

        # clean up
        repo.git.clean('-fdx')
        repo.git.reset('--hard', 'HEAD')
        repo.git.checkout(['--', '.'])



    @staticmethod
    def reproduce_fixed(bug_id):
        project_identifier = bug_id.split('_')[1].split('-')[0]
        project_dir = bugsjarReproducer.project_dirs[project_identifier]

        # check out to the bug branch and make sure it's clean
        repo = git.Repo('{}/{}'.format(bugsjar_path, project_dir))
        repo.git.checkout(bug_id)
        repo.git.clean('-fdx')
        repo.git.reset('--hard', 'HEAD')
        repo.git.checkout(['--', '.'])

        patch_file = '{}/{}/.bugs-dot-jar/developer-patch.diff'.format(bugsjar_path, project_dir)
        repo.git.apply(['-3', patch_file])

        # install all dependencies
        # note we use -fn here to install as much dependencies as possible
        # it will continue to install dependencies regardless of the result of last goal
        _, stdout, stderr, ok = _run_command('mvn install -DskipTests -fn', cwd='{}/{}'.format(bugsjar_path, project_dir))
        build_log = stdout + stderr

        # run the test goal
        # note that in original bugs-dot-jar bugs, there was only one test goal run per bug
        # we identified the test goal run by bugs-dot-jar authors
        # and reproduce by running test of the same goal
        test_module = bugsjarReproducer.extract_tested_module(project_dir)

        if test_module != [None]:
            # multiple (in the most case, only one) sub modules were tested in original test
            # so we reproduce the same
            _, stdout, stderr, ok =  _run_command('mvn test -pl {}'.format(' '.join(test_module)), cwd='{}/{}'.format(bugsjar_path, project_dir))
        else:
            # the whole project was tested in the original test
            _, stdout, stderr, ok =  _run_command('mvn test', cwd='{}/{}'.format(bugsjar_path, project_dir))
        test_log = stdout + stderr

        # write test log to file
        if not os.path.isdir('{}/reproduced/fixed'.format(output_dir)):
            _, stdout, stderr, ok = _run_command('mkdir -p {}/reproduced/fixed'.format(output_dir))
            if not ok:
                logging.error('Failed to create directory {}/reproduced/fixed'.format(output_dir))
                sys.exit(1)

        with open('{}/reproduced/fixed/{}.log'.format(output_dir, bug_id), 'w') as f:
            f.write(build_log)
            f.write('\n')
            f.write(test_log)

        # clean up
        repo.git.clean('-fdx')
        repo.git.reset('--hard', 'HEAD')
        repo.git.checkout(['--', '.'])


    @staticmethod
    def copy_over_original(bug_id):
        project_identifier = bug_id.split('_')[1].split('-')[0]
        project_dir = bugsjarReproducer.project_dirs[project_identifier]

        # check out to the bug branch and make sure it's clean
        repo = git.Repo('{}/{}'.format(bugsjar_path, project_dir))
        repo.git.checkout(bug_id)
        repo.git.clean('-fdx')
        repo.git.reset('--hard', 'HEAD')
        repo.git.checkout(['--', '.'])

        if not os.path.isdir('{}/original'.format(output_dir)):
            _, stdout, stderr, ok = _run_command('mkdir -p {}/original'.format(output_dir))
            if not ok:
                logging.error('Failed to create directory {}/original'.format(output_dir))
                sys.exit(1)

        _, stdout, stderr, ok = _run_command('cp {}/{}/.bugs-dot-jar/test-results.txt {}/original/{}.log'.format(bugsjar_path, project_dir, output_dir, bug_id))
        if not ok:
            logging.warning('Failed to copy over original log for {}.'.format(bug_id))


    @staticmethod
    def extract_tested_artifact_name(original_log_path):
        artifacts_tested = []
        with open (original_log_path, 'r') as f:
            log_lines = f.readlines()
            for line in log_lines:
                if line.startswith('[INFO] Building') and line.endswith('SNAPSHOT\n'):
                        artifacts_tested.append(' '.join(line.strip().split()[2:-1]))
            # There are 25 bugs.jar artifacts have tested not on exactly one module
            # 1 with zero module tested, 24 with multiple modules tests
            # for those cases, we perform a test on the whole project
            return artifacts_tested

    @staticmethod
    def extract_tested_module(project_dir):
        # step 1: extract the tested artifact name from original test log
        original_log_path = '{}/{}/.bugs-dot-jar/test-results.txt'.format(bugsjar_path, project_dir)
        tested_artifact_name = bugsjarReproducer.extract_tested_artifact_name(original_log_path)
        tested_module = []

        # step 2: check if the original tests were performed on the whole project
        if 'pom.xml' in os.listdir('{}/{}'.format(bugsjar_path, project_dir)):
            pom_path = '{}/{}/pom.xml'.format(bugsjar_path, project_dir)
            artifact_name = bugsjarReproducer.extract_artifact_name_from_pom(pom_path)
            if artifact_name in tested_artifact_name:
                # in this case, return none so do not test on sub modules, but on the whole project
                tested_module.append(None)
                return tested_module

        # step 3: check all sub modules, grab the modules tested in the original test log
        _, stdout, stderr, ok = _run_command('find {} -name pom.xml'.format(project_dir), cwd=bugsjar_path)
        if not ok:
            logging.error('Failed to execute find command in {}'.format(project_dir))
            logging.error(stdout)
            logging.error(stderr)
        
        potential_sub_modules = stdout.split('\n')
        for module_pom_path in potential_sub_modules:
            pom_path = '{}/{}'.format(bugsjar_path, module_pom_path)
            module_path = '/'.join(module_pom_path.split('/')[1:-1])
            artifact_name = bugsjarReproducer.extract_artifact_name_from_pom(pom_path)
            if artifact_name in tested_artifact_name:
                tested_module.append(module_path)
        
        return tested_module
        
    @staticmethod
    def extract_artifact_name_from_pom(pom_path):
        # https://stackoverflow.com/questions/48324475/access-xml-element-values-with-python
        try:
            tree = ET.parse(pom_path)
            root = tree.getroot()
            namespace = root.tag.replace('project', '')
            artifact_name = root.find(namespace + 'name')
            if artifact_name is not None:
                return artifact_name.text
            else:
                # None
                return artifact_name
        except Exception as e:
            if len(pom_path.split('/')) < 10:
                logging.error('Failed to parse pom file {}'.format(pom_path))
                logging.error(e)
            return None

    @staticmethod
    def reproduce(bug_id):
        bugsjarReproducer.reproduce_buggy(bug_id)
        bugsjarReproducer.reproduce_fixed(bug_id)
        bugsjarReproducer.copy_over_original(bug_id)