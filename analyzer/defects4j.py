import logging
import sys

from utils import _equal_lists

logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s %(levelname)-8s %(message)s',
                    datefmt='%Y-%m-%d %H:%M:%S')

class defects4jAnalyzer(object):
    def __init__(self):
        pass

    @staticmethod
    def analyze_original_log(log_path):
        with open(log_path, 'r') as f:
            lines = f.readlines()
        
        test_failures = []
        analyze_success = False
    
        for line in lines:
            if line[:4] == '--- ':
                test_failures.append(line[4:].strip())
                analyze_success = True
        
        if not analyze_success:
            logging.error('Failed to analyze original log: no test failures found')
            sys.exit(1)
        
        return (len(test_failures), test_failures)

    @staticmethod    
    def analyze_reproduced_log(log_path):
        with open(log_path, 'r') as f:
            lines = f.readlines()
        
        test_failures_buggy_version = []
        test_failures_fixed_version = []
        analyze_buggy_success = False
        analyze_fixed_success = False
    
        analyze_buggy = False
        analyze_fixed = False
        
        for line in lines:
            # the first 'failing tests:' is for buggy version
            # then grab the following test failures on buggy version
            if (not analyze_buggy_success) and (line[:14] == 'Failing tests:'):
                analyze_buggy = True
                analyze_buggy_success = True
                continue
            # the second 'failing tests:' if for fixed version
            # then grab the following test failures on fixed version
            # ideally, there should be 0 test failures on fixed version
            if analyze_buggy_success and line[:14] == 'Failing tests:':
                analyze_buggy = False
                analyze_fixed = True
                analyze_fixed_success = True
            if analyze_buggy and line[:4] == '  - ':
                test_failures_buggy_version.append(line[4:].strip())
            if analyze_fixed and line[:4] == '  - ':
                test_failures_fixed_version.append(line[4:].strip())
            
        if not (analyze_buggy_success or analyze_fixed_success):
            logging.warning('Reproduced log is not well-formatted. Broken.')
    
        # return ( (num, [list_of_test_failures_buggy]), (num, [list_of_test_failures_fixed]) )
        return ((len(test_failures_buggy_version), test_failures_buggy_version), 
        (len(test_failures_fixed_version), test_failures_fixed_version))
        
    @staticmethod
    def analyze(project, id):
        original_log_path = 'outputs/defects4j/original/{}-{}.log'.format(project, id)
        reproduced_log_path = 'outputs/defects4j/reproduced/{}-{}.log'.format(project, id)
    
        # three metrics to analyze: existence of bug, number match, name match 
        reproducible_existence = False
        reproducible_num_match = False
        reproducible_name_match = False
    
        (original_num_test_failures, original_test_failures) = defects4jAnalyzer.analyze_original_log(original_log_path)
        (reproduced_num_test_failures_buggy_version, reproduced_test_failures_buggy_version),\
        (reproduced_num_test_failures_fixed_version, reproduced_test_failures_fixed_version) = defects4jAnalyzer.analyze_reproduced_log(reproduced_log_path)
    
        # print(original_num_test_failures, original_test_failures)
        # print(reproduced_num_test_failures_buggy_version, reproduced_test_failures_buggy_version)
        # print(reproduced_num_test_failures_fixed_version, reproduced_test_failures_fixed_version)
    
        # existence: at least one test failure in reproduced buggy version, and no test failure on reproduced fixed version
        if reproduced_num_test_failures_buggy_version > 0 and reproduced_num_test_failures_fixed_version == 0:
            reproducible_existence = True
        
        # number match: number of test failures in reproduced buggy version is equal to number of test failures in original buggy version
        # and no test failure in reproduced fixed version
        if reproduced_num_test_failures_buggy_version == original_num_test_failures and reproduced_num_test_failures_fixed_version == 0:
            reproducible_num_match = True
    
        # name match: name of test failures in reproduced buggy version is equal to name of test failures in original buggy version
        # and no test failure in reproduced fixed version
        if _equal_lists(reproduced_test_failures_buggy_version, original_test_failures) and reproduced_num_test_failures_fixed_version == 0:
            reproducible_name_match = True
        
        return (reproducible_existence, reproducible_num_match, reproducible_name_match)
    

