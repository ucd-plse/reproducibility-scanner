import os,sys
import logging
import getopt

from benchmarks.benchmarks import benchmarks

from reproducer.defects4j import defects4jReproducer
from reproducer.bears import bearsReproducer
from reproducer.bugswarm import bugswarmReproducer
from reproducer.growingbugs import growingbugsReproducer
from reproducer.bugsjar import bugsjarReproducer

from analyzer.defects4j import defects4jAnalyzer
from analyzer.bears import bearsAnalyzer
from analyzer.bugswarm import bugswarmAnalyzer
from analyzer.growingbugs import growingbugsAnalyzer
from analyzer.bugsjar import bugsjarAnalyzer

from utils import _get_artifact_list

logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s %(levelname)-8s %(message)s',
                    datefmt='%Y-%m-%d %H:%M:%S')


def _print_usage(msg=None):
    if msg:
        logging.error(msg)

    print('Usage: python scan4r.py OPTIONS')
    print('Options:')
    print('  -b, --benchmark <benchmark>')
    print('  -i, --id <bug_id>')
    print('  -l, --list <file>')
    print('  -a, --analyze-only')


def _validate_input(argv):
    # parse command line arguments
    short_opts = 'b:i:l:a'
    long_opts = ['benchmark=', 'id=', 'list=', 'analyze-only']

    try:
        opts, args = getopt.getopt(argv, short_opts, long_opts)
    except getopt.GetoptError:
        _print_usage()
        sys.exit(2)

    benchmark = None
    bug_id = None
    analyze_only = False
    artifact_list_file = None
    artifact_list = None

    for opt, arg in opts:
        if opt in ('-b', '--benchmark'):
            benchmark = arg
        elif opt in ('-i', '--id'):
            bug_id = arg 
        elif opt in ('-a', '--analyze-only'):
            analyze_only = True
        elif opt in ('-l', '--list'):
            artifact_list_file = arg
    
    if not benchmark:
        _print_usage('Missing benchmark name')
        sys.exit(2)

    if benchmark not in benchmarks.keys():
        _print_usage('Invalid benchmark name. Please use [{}]'.format(', '.join(benchmarks.keys())))
        sys.exit(2)
    elif bug_id and bug_id not in benchmarks[benchmark]:
        _print_usage('Invalid Bug ID: {}.'.format(bug_id))
        sys.exit(2) 

    if not bug_id and not artifact_list_file:
        # reproduce all bugs in the benchmark
        logging.info('Reproducing all bugs in {}'.format(benchmark))

    if artifact_list_file:
        logging.info('Reading artifact list from {}'.format(artifact_list_file))
        artifact_list = _get_artifact_list(artifact_list_file)
        if len(artifact_list) == 0:
            _print_usage('Invalid artifact list file: {}'.format(artifact_list_file))
            sys.exit(2)
        for artifact in artifact_list:
            if artifact not in benchmarks[benchmark]:
                _print_usage('Invalid artifact ID: {}'.format(artifact))
                sys.exit(2)

    return benchmark, bug_id, analyze_only, artifact_list
    
def defects4j(bug_id, analyze_only, artifact_list):
    if bug_id:
        project, id = bug_id.split('-')
        logging.info('Reproducing Defects4J {}-{}'.format(project, id))
        if not analyze_only:
            defects4jReproducer.reproduce_artifact(project, id)
            defects4jReproducer.copy_over_original_log(project, id)
        (reproducible_existence, reproducible_num_match, reproducible_name_match) = defects4jAnalyzer.analyze(project, id)
        logging.info('Reproducibility (Existence, NumMatch, NameMatch): {} {} {}'.format(reproducible_existence, reproducible_num_match, reproducible_name_match))
    else:
        reproducibility_result = {'Existence': 0, 'NumMatch': 0, 'NameMatch': 0}
        if artifact_list is None:
            artifact_list = benchmarks['defects4j']
        logging.info('Reproducing {} Defects4J bugs'.format(len(artifact_list)))
        for bug_id in artifact_list:
            project, id = bug_id.split('-')
            logging.info('Reproducing Defects4J {}-{}'.format(project, id))
            if not analyze_only:
                defects4jReproducer.reproduce_artifact(project, id)
                defects4jReproducer.copy_over_original_log(project, id)
            (reproducible_existence, reproducible_num_match, reproducible_name_match) = defects4jAnalyzer.analyze(project, id)
            logging.info('Reproducibility (Existence, NumMatch, NameMatch): {} {} {}'.format(reproducible_existence, reproducible_num_match, reproducible_name_match))
            reproducibility_result['Existence'] = reproducibility_result['Existence'] + reproducible_existence
            reproducibility_result['NumMatch'] = reproducibility_result['NumMatch'] + reproducible_num_match
            reproducibility_result['NameMatch'] = reproducibility_result['NameMatch'] + reproducible_name_match
        logging.info('Overall reproducibility for {} Defects4J artifacts'.format(len(artifact_list)))
        logging.info(reproducibility_result)

def bears(bug_id, analyze_only, artifact_list):
    if bug_id:
        logging.info('Reproducing Bears {}'.format(bug_id))
        if not analyze_only:
            bearsReproducer.reproduce(bug_id)
        (reproducible_existence, reproducible_num_match, reproducible_name_match) = bearsAnalyzer.analyze(bug_id)
        logging.info('Reproducibility (Existence, NumMatch, NameMatch): {} {} {}'.format(reproducible_existence, reproducible_num_match, reproducible_name_match))

    else:
        reproducibility_result = {'Existence': 0, 'NumMatch': 0, 'NameMatch': 0}
        if artifact_list is None:
            artifact_list = benchmarks['bears']
        logging.info('Reproducing {} Bears bugs'.format(len(artifact_list)))
        for bug_id in artifact_list:
            logging.info('Reproducing Bears {}'.format(bug_id))
            if not analyze_only:
                bearsReproducer.reproduce(bug_id)
            (reproducible_existence, reproducible_num_match, reproducible_name_match) = bearsAnalyzer.analyze(bug_id)
            logging.info('Reproducibility (Existence, NumMatch, NameMatch): {} {} {}'.format(reproducible_existence, reproducible_num_match, reproducible_name_match))
            reproducibility_result['Existence'] = reproducibility_result['Existence'] + reproducible_existence
            reproducibility_result['NumMatch'] = reproducibility_result['NumMatch'] + reproducible_num_match
            reproducibility_result['NameMatch'] = reproducibility_result['NameMatch'] + reproducible_name_match
        logging.info('Overall reproducibility for {} Bears artifacts'.format(len(artifact_list)))
        logging.info(reproducibility_result)


def bugswarm(bug_id, analyze_only, artifact_list):
    if bug_id:
        logging.info('Reproducing BugSwarm {}'.format(bug_id))
        if not analyze_only:
            bugswarmReproducer.reproduce(bug_id)
        (reproducible_existence, reproducible_num_match, reproducible_name_match) = bugswarmAnalyzer.analyze(bug_id)
        logging.info('Reproducibility (Existence, NumMatch, NameMatch): {} {} {}'.format(reproducible_existence, reproducible_num_match, reproducible_name_match))
        
    else:
        reproducibility_result = {'Existence': 0, 'NumMatch': 0, 'NameMatch': 0}
        if artifact_list is None:
            artifact_list = benchmarks['bugswarm']
        logging.info('Reproducing {} BugSwarm bugs'.format(len(artifact_list)))
        for bug_id in artifact_list:
            logging.info('Reproducing BugSwarm {}'.format(bug_id))
            if not analyze_only:
                bugswarmReproducer.reproduce(bug_id)
            (reproducible_existence, reproducible_num_match, reproducible_name_match) = bugswarmAnalyzer.analyze(bug_id)
            logging.info('Reproducibility (Existence, NumMatch, NameMatch): {} {} {}'.format(reproducible_existence, reproducible_num_match, reproducible_name_match))
            reproducibility_result['Existence'] = reproducibility_result['Existence'] + reproducible_existence
            reproducibility_result['NumMatch'] = reproducibility_result['NumMatch'] + reproducible_num_match
            reproducibility_result['NameMatch'] = reproducibility_result['NameMatch'] + reproducible_name_match 
        logging.info('Overall reproducibility for {} BugSwarm artifacts'.format(len(artifact_list)))
        logging.info(reproducibility_result)


def growingbugs(bug_id, analyze_only, artifact_list):
    if bug_id:
        project, id = bug_id.split('-')
        logging.info('Reproducing GrowingBugs {}-{}'.format(project, id))
        if not analyze_only:
            growingbugsReproducer.reproduce_artifact(project, id)
            growingbugsReproducer.copy_over_original_log(project, id)
        (reproducible_existence, reproducible_num_match, reproducible_name_match) = growingbugsAnalyzer.analyze(project, id)
        logging.info('Reproducibility (Existence, NumMatch, NameMatch): {} {} {}'.format(reproducible_existence, reproducible_num_match, reproducible_name_match))
    
    else:
        reproducibility_result = {'Existence': 0, 'NumMatch': 0, 'NameMatch': 0}
        if artifact_list is None:
            artifact_list = benchmarks['growingbugs']
        logging.info('Reproducing {} GrowingBugs bugs'.format(len(artifact_list)))
        for bug_id in artifact_list:
            project, id = bug_id.split('-')
            logging.info('Reproducing GrowingBugs {}-{}'.format(project, id))
            if not analyze_only:
                growingbugsReproducer.reproduce_artifact(project, id)
                growingbugsReproducer.copy_over_original_log(project, id)
            (reproducible_existence, reproducible_num_match, reproducible_name_match) = growingbugsAnalyzer.analyze(project, id)
            logging.info('Reproducibility (Existence, NumMatch, NameMatch): {} {} {}'.format(reproducible_existence, reproducible_num_match, reproducible_name_match))
            reproducibility_result['Existence'] = reproducibility_result['Existence'] + reproducible_existence
            reproducibility_result['NumMatch'] = reproducibility_result['NumMatch'] + reproducible_num_match
            reproducibility_result['NameMatch'] = reproducibility_result['NameMatch'] + reproducible_name_match
        logging.info('Overall reproducibility for {} GrowingBugs artifacts'.format(len(artifact_list)))
        logging.info(reproducibility_result)


def bugsjar(bug_id, analyze_only, artifact_list):
    if bug_id:
        logging.info('Reproducing Bugs.jar {}'.format(bug_id))
        if not analyze_only:
            bugsjarReproducer.reproduce(bug_id)
        (reproducible_existence, reproducible_num_match, reproducible_name_match) = bugsjarAnalyzer.analyze(bug_id)
        logging.info('Reproducibility (Existence, NumMatch, NameMatch): {} {} {}'.format(reproducible_existence, reproducible_num_match, reproducible_name_match))

    else:
        reproducibility_result = {'Existence': 0, 'NumMatch': 0, 'NameMatch': 0}
        if artifact_list is None:
            artifact_list = benchmarks['bugs.jar']
        logging.info('Reproducing {} Bugs.jar bugs'.format(len(artifact_list)))
        for bug_id in artifact_list:
            logging.info('Reproducing Bugs.jar {}'.format(bug_id))
            if not analyze_only:
                bugsjarReproducer.reproduce(bug_id)
            (reproducible_existence, reproducible_num_match, reproducible_name_match) = bugsjarAnalyzer.analyze(bug_id)
            logging.info('Reproducibility (Existence, NumMatch, NameMatch): {} {} {}'.format(reproducible_existence, reproducible_num_match, reproducible_name_match))
            reproducibility_result['Existence'] = reproducibility_result['Existence'] + reproducible_existence
            reproducibility_result['NumMatch'] = reproducibility_result['NumMatch'] + reproducible_num_match
            reproducibility_result['NameMatch'] = reproducibility_result['NameMatch'] + reproducible_name_match
        logging.info('Overall reproducibility for {} Bugs.jar artifacts'.format(len(artifact_list)))
        logging.info(reproducibility_result)
            

def main(argv=None):
    argv = argv or sys.argv[1:]

    logging.basicConfig(level=logging.INFO)
    
    benchmark, bug_id, analyze_only, artifact_list = _validate_input(argv)

    benchmark = benchmark.lower()

    if benchmark == 'defects4j':
        defects4j(bug_id, analyze_only, artifact_list)

    if benchmark == 'bears':
        bears(bug_id, analyze_only, artifact_list)

    if benchmark == 'bugswarm':
        bugswarm(bug_id, analyze_only, artifact_list)

    if benchmark == 'growingbugs':
        growingbugs(bug_id, analyze_only, artifact_list)

    if benchmark == 'bugs.jar':
        bugsjar(bug_id, analyze_only, artifact_list)


if __name__ == '__main__':
    sys.exit(main())