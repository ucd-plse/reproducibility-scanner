import os, sys
import logging
from utils import _run_command

logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s %(levelname)-8s %(message)s',
                    datefmt='%Y-%m-%d %H:%M:%S')

def defects4j_init():
    logging.info('Initializing Defects4J')
    defects4j_path = os.path.join(os.getcwd(), 'benchmarks/defects4j')
    defects4j_bin = os.path.join(os.getcwd(), 'benchmarks/defects4j/framework/bin/defects4j')
  
    _, stdout, stderr, ok = _run_command('cpanm --installdeps .', cwd=defects4j_path)
    if not ok:
        logging.error('Failed to install dependencies for Defects4J')
        logging.error(stdout)
        logging.error(stderr)
        sys.exit(1)
  
    _, stdout, stderr, ok = _run_command('./init.sh', cwd=defects4j_path)
    if not ok:
        logging.error('Failed to initialize Defects4J')
        logging.error(stdout)
        logging.error(stderr)
        sys.exit(1)
  
    # this is to reproduce all bugs, not only active ones
    _, stdout, stderr, ok = _run_command('sed -i \'97,100 s/^/#/\' {}/framework/test/test_verify_bugs.sh'.format(defects4j_path))
    if not ok:
        logging.error('Failed to modify test_verify_bugs.sh')
        logging.error(stdout)
        logging.error(stderr)
        sys.exit(1)  

    # merge deprecated bug into active bugs because we want to reproduce all bugs
    project_list = os.listdir('benchmarks/defects4j/framework/projects')
    for project in project_list:
        if not os.path.isdir(os.path.join('benchmarks/defects4j/framework/projects', project)):
            continue
        if project == 'lib':
            continue
        with open('benchmarks/defects4j/framework/projects/{}/deprecated-bugs.csv'.format(project), 'r') as f:
            deprecated_bugs = f.readlines()
        if len(deprecated_bugs) > 1:
            # deprecated_bugs exists
            # append deprecated bugs to active bugs
            with open('benchmarks/defects4j/framework/projects/{}/active-bugs.csv'.format(project), 'a') as f:
                for bug in deprecated_bugs[1:]:
                    f.write(bug)
            # erase deprecated-bugs.csv
            with open('benchmarks/defects4j/framework/projects/{}/deprecated-bugs.csv'.format(project), 'w') as f:
                f.write(deprecated_bugs[0])
        else:
            # no deprecated bugs, do nothing
            pass

    _, stdout, stderr, ok = _run_command('yes | cpan DBI', cwd=defects4j_path)
    if not ok:
        logging.error('Failed to install DBI')
        logging.error(stdout)
        logging.error(stderr)
        sys.exit(1)

    _, stdout, stderr, ok = _run_command('{} info -p Lang'.format(defects4j_bin))
    print(stdout)
    if not ok:
        logging.error('Failed to run Defects4J')
        logging.error(stdout)
        logging.error(stderr)
        sys.exit(1)
  
    logging.info('Defects4J initialized\n')


def bugswarm_init():
    logging.info('Initializing BugSwarm')
    # set up credentials.py
    _, stdout, stderr, ok = _run_command('cp credentials.sample.py credentials.py', cwd=os.path.join(os.getcwd(), 'benchmarks/bugswarm/bugswarm/common'))
    if not ok:
        logging.error('Failed to copy credentials.sample.py to credentials.py')
        logging.error(stdout)
        logging.error(stderr)
    
    _, stdout, stderr, ok = _run_command('sed -i \"s/\'\'/\'#\'/g\" credentials.py', cwd=os.path.join(os.getcwd(), 'benchmarks/bugswarm/bugswarm/common'))
    _, stdout, stderr, ok = _run_command('sed -i \"s/\[\]/\[\'#\'\]/g\" credentials.py', cwd=os.path.join(os.getcwd(), 'benchmarks/bugswarm/bugswarm/common'))
    _, stdout, stderr, ok = _run_command('sed -i \"s/COMMON_HOSTNAME = \'#\'/COMMON_HOSTNAME = \'www.api.bugswarm.org\'/g\" credentials.py', cwd=os.path.join(os.getcwd(), 'benchmarks/bugswarm/bugswarm/common'))
    if not ok:
        logging.error('Failed to modify credentials.py')
        logging.error(stdout)
        logging.error(stderr)

    # rename bugswarm reproducer to avoid name conflict
    if os.path.isdir('benchmarks/bugswarm/reproducer'):
        _, stdout, stderr, ok = _run_command('mv reproducer bugswarm_reproducer', cwd=os.path.join(os.getcwd(), 'benchmarks/bugswarm/'))
        if not ok:
            logging.error('Failed to rename bugswarm reproducer')
            logging.error(stdout)
            logging.error(stderr)
            sys.exit(1)

    # install bugswarm
    _, stdout, stderr, ok = _run_command('pip install -e .', cwd=os.path.join(os.getcwd(), 'benchmarks/bugswarm'))
    print(stdout)
    if not ok:
        logging.error('Failed to install bugswarm')
        logging.error(stdout)
        logging.error(stderr)
        sys.exit(1)
    
    logging.info('BugSwarm initialized\n')

def growingbugs_init():
    logging.info('Initializing GrowingBugs')
    growingbugs_path = os.path.join(os.getcwd(), 'benchmarks/growingbugs')
    growingbugs_bin = os.path.join(os.getcwd(), 'benchmarks/growingbugs/framework/bin/defects4j')


    _, stdout, stderr, ok = _run_command('cpanm --installdeps .', cwd=growingbugs_path)
    if not ok:
        logging.error('Failed to install dependencies for GrowingBugs')
        logging.error(stdout)
        logging.error(stderr)
        sys.exit(1)
  
    _, stdout, stderr, ok = _run_command('./init.sh', cwd=growingbugs_path)
    if not ok:
        logging.error('Failed to initialize GrowingBugs')
        logging.error(stdout)
        logging.error(stderr)
        sys.exit(1)

    # This step clones all projects in growingbugs and it costs a lot of time.
    logging.info('Cloning all projects in GrowingBugs into {}/project_repos'.format(growingbugs_path))
    logging.info('This step may take a while...')
    _, stdout, stderr, ok = _run_command('./repos.sh', cwd=growingbugs_path)
    if not ok:
        logging.error('Failed to clone GrowingBugs Repositories')
        logging.error(stdout)
        logging.error(stderr)
        sys.exit(1)

    # merge deprecated bug into active bugs because we want to reproduce all bugs
    project_list = os.listdir('benchmarks/growingbugs/framework/projects')
    for project in project_list:
        if not os.path.isdir(os.path.join('benchmarks/growingbugs/framework/projects', project)):
            continue
        if project == 'lib':
            continue
        if len(os.listdir('benchmarks/growingbugs/framework/projects/{}/'.format(project))) == 0:
            # clean up empty project that included by GrowingBUgs maintainers
            logging.info('Skip empty project {}'.format(project))
            continue
        with open('benchmarks/growingbugs/framework/projects/{}/deprecated-bugs.csv'.format(project), 'r') as f:
            deprecated_bugs = f.readlines()
        if len(deprecated_bugs) > 1:
            # deprecated_bugs exists
            # append deprecated bugs to active bugs
            with open('benchmarks/growingbugs/framework/projects/{}/active-bugs.csv'.format(project), 'a') as f:
                for bug in deprecated_bugs[1:]:
                    f.write(bug)
            # erase deprecated-bugs.csv
            with open('benchmarks/growingbugs/framework/projects/{}/deprecated-bugs.csv'.format(project), 'w') as f:
                f.write(deprecated_bugs[0])
        else:
            # no deprecated bugs, do nothing
            pass

    _, stdout, stderr, ok = _run_command('{} info -p Mrunit'.format(growingbugs_bin))
    print(stdout)
    if not ok:
        logging.error('Failed to run GrowingBugs')
        logging.error(stdout)
        logging.error(stderr)
        sys.exit(1)
  
    logging.info('GrowingBugs initialized\n')



def main():
    defects4j_init()
    bugswarm_init()
    growingbugs_init()

if __name__ == '__main__':
    sys.exit(main())