import os, sys
import logging
import subprocess

from benchmarks import benchmarks
from utils import _run_command

logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s %(levelname)-8s %(message)s',
                    datefmt='%Y-%m-%d %H:%M:%S')

class growingbugsReproducer(object):
    def __init__(self):
        pass

    @staticmethod
    def reproduce_artifact(project, id):
        if not os.path.isdir('outputs/growingbugs/reproduced'):
            _, stdout, stderr, ok = _run_command('mkdir -p outputs/growingbugs/reproduced')
            if not ok:
                logging.error('Failed to create directory outputs/growingbugs/reproduced')
                logging.error(stdout)
                logging.error(stderr)
                sys.exit(1)
        with open('outputs/growingbugs/reproduced/{}-{}.log'.format(project, id), 'w+') as f:
            growingbugs_path = os.path.join(os.getcwd(), 'benchmarks/growingbugs')
            subprocess.call(['./test_verify_bugs.sh', '-p{}'.format(project), '-b{}'.format(id)], stdout=f, stderr=subprocess.STDOUT, cwd='{}/framework/test'.format(growingbugs_path))

    @staticmethod
    def copy_over_original_log(project, id):
        if not os.path.isdir('outputs/growingbugs/original'):
            _, stdout, stderr, ok = _run_command('mkdir -p outputs/growingbugs/original')
            if not ok:
                logging.error('Failed to create directory outputs/growingbugs/original')
                logging.error(stdout)
                logging.error(stderr)
                sys.exit(1)
        original_log_path = 'benchmarks/growingbugs/framework/projects/{}/trigger_tests/{}'.format(project, id)
        _, stdout, stderr, ok = _run_command('cp {} outputs/growingbugs/original/{}-{}.log'.format(original_log_path, project, id))
        if not ok:
            logging.error('Failed to copy original log')
            logging.error(stdout)
            logging.error(stderr)
            sys.exit(1)


