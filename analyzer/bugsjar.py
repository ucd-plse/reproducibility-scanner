import logging
import re
import json

from utils import _equal_lists

from analyzer.bears import bearsAnalyzer

logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s %(levelname)-8s %(message)s',
                    datefmt='%Y-%m-%d %H:%M:%S')

class bugsjarAnalyzer(object):
    def __init__(self):
        pass

    @staticmethod
    def analyze_log(log_path):
        with open(log_path, 'r') as f:
            log_lines = f.readlines()
        
        if not bearsAnalyzer.check_test_run(log_lines):
            return (None, None)

        test_lines = bearsAnalyzer.extract_test_lines(log_lines)
        
        num_tests_run, num_tests_failed, num_tests_skipped = bearsAnalyzer.get_num_test_failures(test_lines)
        test_failures = bugsjarAnalyzer.get_offending_test_failures(test_lines)

        # if len(test_failures) != num_tests_failed:
        #     logging.warning('{}: Number of test failures does not match between reactor result and parsed failures'.format(log_path))

        return (len(test_failures), test_failures)

    @staticmethod
    def analyze(bug_id):
        original_log_path = 'outputs/bugs-dot-jar/original/{}.log'.format(bug_id)
        reproduced_log_path_buggy = 'outputs/bugs-dot-jar/reproduced/buggy/{}.log'.format(bug_id)
        reproduced_log_path_fixed = 'outputs/bugs-dot-jar/reproduced/fixed/{}.log'.format(bug_id)

        # three metrics to analysis: existence of bug, number match, name match
        reproducible_existence = False
        reproducible_num_match = False
        reproducible_name_match = False

        (original_num_test_failures, original_test_failures) = bugsjarAnalyzer.analyze_log(original_log_path)
        (reproduced_num_test_failures_buggy_version, reproduced_test_failures_buggy_version) = bugsjarAnalyzer.analyze_log(reproduced_log_path_buggy)
        (reproduced_num_test_failures_fixed_version, reproduced_test_failures_fixed_version) = bugsjarAnalyzer.analyze_log(reproduced_log_path_fixed)

        
        if (reproduced_num_test_failures_buggy_version is None) or (reproduced_num_test_failures_fixed_version is None):
            # got None when there is no test run caused by compile error
            reproducible_existence = False
            reproducible_num_match = False
            reproducible_name_match = False
            return (reproducible_existence, reproducible_num_match, reproducible_name_match)
        
        if reproduced_num_test_failures_fixed_version > 0:
            # there are test failures on fixed version
            # which means the patch is not working anymore
            # so the artifact is not reproducible
            reproducible_existence = False
            reproducible_num_match = False
            reproducible_name_match = False
            return (reproducible_existence, reproducible_num_match, reproducible_name_match)
        else:
            if reproduced_num_test_failures_buggy_version > 0:
                reproducible_existence = True
            if reproduced_num_test_failures_buggy_version == original_num_test_failures:
                reproducible_num_match = True
            if _equal_lists(reproduced_test_failures_buggy_version, original_test_failures):
                # use Counter to compare two lists because it is possible that the same test class fails multiple times
                # https://stackoverflow.com/questions/8106227/difference-between-two-lists-with-duplicates-in-python
                reproducible_name_match = True
            return (reproducible_existence, reproducible_num_match, reproducible_name_match)
        

    @staticmethod 
    def extract_test_method_name(line):
        exclusions = ['Expected', 'but', 'Flake', 'Run ', 'Expect', 'in file', 'Wanted', 'But']
        for exclusion in exclusions:
            if line.strip().startswith(exclusion):
                return None
        match = re.search(r'(\w+(\[.+\])?\([\w.$\[\]]+\))', line)
        if match:
            return match.group(1)
        elif 'Flake' in line:
            return None
        elif ':' in line and not line.startswith('  Run'):
            return line.split(':')[0]
        elif '»' in line:
            return line.split('»')[0]
        elif '#' in line:
            return line.split('#')[0]
        return None


    @staticmethod
    def get_offending_test_failures(test_lines):
        test_failures = []
        has_indent = False

        # only parse when results_started == True and results_ended == False
        results_started = False
        results_ended = False

        if test_lines[0].startswith('  ') or test_lines[1].startswith('  '):
            has_indent = True

        for line in test_lines:
            if has_indent and line[:2] != '  ':
                continue
            # Skip the 'Tests run: ..., Failures: ..., Errors: ..., Skipped: ...' summary line to prevent matching
            # 'run:', 'Failures:', 'Errors:', and 'Skipped:' as test names.
            if 'Tests run:' in line or 'Flaked tests:' in line:
                if results_started:
                    results_ended = True
                    results_started = False
                continue
            if 'Results :' in line:
                results_started = True
                results_ended = False
                continue
            if not (results_started and not results_ended):
                continue
            if 'Failed tests:' in line or 'Tests in error:' in line:
                tests = line.split(':')[1].strip()
                if len(tests) > 1:
                    offending_test = bugsjarAnalyzer.extract_test_method_name(tests)
                    if offending_test is not None:
                        match = re.search(r'\((.*?)\)', offending_test)
                        if match:
                            failed_test_class = match.group(1)
                            test_failures.append(failed_test_class)
                        else:
                            test_failures.append(offending_test)
            else:
                offending_test = bugsjarAnalyzer.extract_test_method_name(line)
                if offending_test is not None:
                    match = re.search(r'\((.*?)\)', offending_test)
                    if match:
                        failed_test_class = match.group(1)
                        test_failures.append(failed_test_class)
                    else:
                        test_failures.append(offending_test)

        test_failures = [test_failure.strip() for test_failure in test_failures if not bugsjarAnalyzer.exclude(test_failure)]
        return test_failures
        
    @staticmethod
    def exclude(test_failure):
        exclusions = ['but was', '<any>', '"', '.ep', '.item', 'attrs.ep', '[java' , '-> at', 'Wicket.TimerHandles']
        for exclusion in exclusions:
            if exclusion in test_failure:
                return True
        if not '.' in test_failure:
            return True
        
        return False