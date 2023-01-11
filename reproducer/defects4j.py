import os, sys
import logging
import subprocess

from benchmarks import benchmarks
from utils import _run_command

logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s %(levelname)-8s %(message)s',
                    datefmt='%Y-%m-%d %H:%M:%S')

class defects4jReproducer(object):
    def __init__(self):
        pass

    @staticmethod
    def reproduce_artifact(project, id):
        if not os.path.isdir('outputs/defects4j/reproduced'):
            _, stdout, stderr, ok = _run_command('mkdir -p outputs/defects4j/reproduced')
            if not ok:
                logging.error('Failed to create directory outputs/defects4j/reproduced')
                logging.error(stdout)
                logging.error(stderr)
                sys.exit(1)
        with open('outputs/defects4j/reproduced/{}-{}.log'.format(project, id), 'w+') as f:
            defects4j_path = os.path.join(os.getcwd(), 'benchmarks/defects4j')
            subprocess.call(['./test_verify_bugs.sh', '-p{}'.format(project), '-b{}'.format(id)], stdout=f, stderr=subprocess.STDOUT, cwd='{}/framework/test'.format(defects4j_path))

    @staticmethod
    def copy_over_original_log(project, id):
        if not os.path.isdir('outputs/defects4j/original'):
            _, stdout, stderr, ok = _run_command('mkdir -p outputs/defects4j/original')
            if not ok:
                logging.error('Failed to create directory outputs/defects4j/original')
                logging.error(stdout)
                logging.error(stderr)
                sys.exit(1)
        original_log_path = 'benchmarks/defects4j/framework/projects/{}/trigger_tests/{}'.format(project, id)
        _, stdout, stderr, ok = _run_command('cp {} outputs/defects4j/original/{}-{}.log'.format(original_log_path, project, id))
        if not ok:
            logging.error('Failed to copy original log')
            logging.error(stdout)
            logging.error(stderr)
            sys.exit(1)
        


def main(argv=None):
    argv = argv or sys.argv[1:]

    if len(argv) > 0:
    # specify bug id
        bug_id = argv[0]
        project, id = bug_id.split('-')
        defects4jReproducer.reproduce_artifact(project, id)
        defects4jReproducer.copy_over_original_log(project, id)
    else:
        # reproduce all bugs in the project
        for bug_id in benchmarks['defects4j']:
            project, id = bug_id.split('-')
            defects4jReproducer.reproduce_artifact(project, id)
            defects4jReproducer.copy_over_original_log(project, id)



if __name__ == '__main__':
    sys.exit(main())