import os, sys
import logging

from utils import _run_command

bears_workspace = '{}/reproducer/workspace'.format(os.getcwd())
bears_scripts = '{}/reproducer/bears_scripts'.format(os.getcwd())
output_dir = '{}/outputs/bears'.format(os.getcwd())


logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s %(levelname)-8s %(message)s',
                    datefmt='%Y-%m-%d %H:%M:%S')

class bearsReproducer(object):
    def __init__(self):
        pass

    @staticmethod
    def reproduce_buggy(bug_id):

        # clean up workspace
        if os.path.isdir('{}/{}'.format(bears_workspace, bug_id)):
            _, stdout, stderr, ok = _run_command('rm -r {}/{}'.format(bears_workspace, bug_id))
            if not ok:
                logging.error('Failed to clean up workspace')
                logging.error(stderr)
                logging.error(stdout)
        
        # checkout buggy version of the bug
        _, stdout, stderr, ok = _run_command('python2 checkout_buggy.py --bugId {} --workspace {}'.format(bug_id, bears_workspace), cwd=bears_scripts)
        if not ok:
            logging.error('Failed to checkout buggy version')
            logging.error(stderr)
            logging.error(stdout)

        # compile buggy version of the bug
        _, stdout, stderr, ok = _run_command('python2 compile.py --bugId {} --workspace {}'.format(bug_id, bears_workspace), cwd=bears_scripts)
        if not ok:
            logging.error('Failed to compile')
            logging.error(stderr)
            logging.error(stdout)

        # run test on buggy version of the bug
        _, stdout, stderr, ok = _run_command('python2 run_tests.py --bugId {} --workspace {}'.format(bug_id, bears_workspace), cwd=bears_scripts)
        if not ok:
            logging.error('Failed to run tests')
            logging.error(stderr)
            logging.error(stdout)
        test_log = stdout

        # write test log to file
        if not os.path.isdir('{}/reproduced/buggy'.format(output_dir)):
            _, stdout, stderr, ok = _run_command('mkdir -p {}/reproduced/buggy'.format(output_dir))
            if not ok:
                logging.error('Failed to create directory {}/reproduced/buggy'.format(output_dir))
                sys.exit(1)

        with open('{}/reproduced/buggy/{}.log'.format(output_dir, bug_id), 'w+') as f:
            f.write(test_log)

        # clean up workspace
        if os.path.isdir('{}/{}'.format(bears_workspace, bug_id)):
            _, stdout, stderr, ok = _run_command('rm -r {}/{}'.format(bears_workspace, bug_id))
            if not ok:
                logging.error('Failed to clean up workspace')
                logging.error(stderr)
                logging.error(stdout)
        

    @staticmethod
    def reproduce_fixed(bug_id):

        # clean up workspace
        if os.path.isdir('{}/{}'.format(bears_workspace, bug_id)):
            _, stdout, stderr, ok = _run_command('rm -r {}/{}'.format(bears_workspace, bug_id))
            if not ok:
                logging.error('Failed to clean up workspace')
                logging.error(stderr)
                logging.error(stdout)
        
        # checkout buggy version of the bug
        _, stdout, stderr, ok = _run_command('python2 checkout_fixed.py --bugId {} --workspace {}'.format(bug_id, bears_workspace), cwd=bears_scripts)
        if not ok:
            logging.error('Failed to checkout buggy version')
            logging.error(stderr)
            logging.error(stdout)

        # compile buggy version of the bug
        _, stdout, stderr, ok = _run_command('python2 compile.py --bugId {} --workspace {}'.format(bug_id, bears_workspace), cwd=bears_scripts)
        if not ok:
            logging.error('Failed to compile')
            logging.error(stderr)
            logging.error(stdout)

        # run test on buggy version of the bug
        _, stdout, stderr, ok = _run_command('python2 run_tests.py --bugId {} --workspace {}'.format(bug_id, bears_workspace), cwd=bears_scripts)
        if not ok:
            logging.error('Failed to run tests')
            logging.error(stderr)
            logging.error(stdout)
        test_log = stdout

        # write test log to file
        if not os.path.isdir('{}/reproduced/fixed'.format(output_dir)):
            _, stdout, stderr, ok = _run_command('mkdir -p {}/reproduced/fixed'.format(output_dir))

        with open('{}/reproduced/fixed/{}.log'.format(output_dir, bug_id), 'w+') as f:
            f.write(test_log)

        # clean up workspace
        if os.path.isdir('{}/{}'.format(bears_workspace, bug_id)):
            _, stdout, stderr, ok = _run_command('rm -r {}/{}'.format(bears_workspace, bug_id))
            if not ok:
                logging.error('Failed to clean up workspace')
                logging.error(stderr)
                logging.error(stdout)

    @staticmethod
    def copy_over_original(bug_id):
        if os.path.isdir('{}/{}'.format(bears_workspace, bug_id)):
            _, stdout, stderr, ok = _run_command('rm -r {}/{}'.format(bears_workspace, bug_id))
            if not ok:
                logging.error('Failed to clean up workspace')
                logging.error(stderr)
                logging.error(stdout)
        
        # checkout buggy version of the bug
        _, stdout, stderr, ok = _run_command('python2 checkout_buggy.py --bugId {} --workspace {}'.format(bug_id, bears_workspace), cwd=bears_scripts)
        if not ok:
            logging.error('Failed to checkout buggy version')
            logging.error(stderr)
            logging.error(stdout)

        # create directory for original logs
        if not os.path.isdir('{}/original'.format(output_dir)):
            _, stdout, stderr, ok = _run_command('mkdir -p {}/original'.format(output_dir))
            if not ok:
                logging.error('Failed to create directory {}/original'.format(output_dir))
                sys.exit(1)
        
        # copy over original logs
        _, stdout, stderr, ok = _run_command('cp {}/{}/bears.json {}/original/{}.json'.format(bears_workspace, bug_id, output_dir, bug_id))

        # clean up workspace
        if os.path.isdir('{}/{}'.format(bears_workspace, bug_id)):
            _, stdout, stderr, ok = _run_command('rm -r {}/{}'.format(bears_workspace, bug_id))
            if not ok:
                logging.error('Failed to clean up workspace')
                logging.error(stderr)
                logging.error(stdout)

    @staticmethod
    def reproduce(bug_id):
        bearsReproducer.reproduce_buggy(bug_id)
        bearsReproducer.reproduce_fixed(bug_id)
        bearsReproducer.copy_over_original(bug_id)
