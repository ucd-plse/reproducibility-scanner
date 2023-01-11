import logging
import re
import json

from utils import _equal_lists

logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s %(levelname)-8s %(message)s',
                    datefmt='%Y-%m-%d %H:%M:%S')

class bearsAnalyzer(object):
    def __init__(self):
        pass

    @staticmethod
    def analyze_original_log(log_path):
        with open(log_path, 'r') as f:
            log = json.load(f)

        # we pick all test failures and errors
        # please refer to the paper for more details
        test_failures = []

        for failures in log['tests']['failureDetails']:
            test_failures.append(failures['testClass'])

        return (len(test_failures), test_failures)

    @staticmethod
    def analyze_reproduced_log(log_path):
        with open(log_path, 'r') as f:
            log_lines = f.readlines()
        
        if not bearsAnalyzer.check_test_run(log_lines):
            return (None, None)

        test_lines = bearsAnalyzer.extract_test_lines(log_lines)
        
        num_tests_run, num_tests_failed, num_tests_skipped = bearsAnalyzer.get_num_test_failures(test_lines)
        test_failures = bearsAnalyzer.get_test_failures(test_lines)

        # if len(test_failures) != num_tests_failed:
        #     logging.warning('Number of test failures does not match between reactor result and parsed failures')

        return (len(test_failures), test_failures)

    @staticmethod
    def analyze(bug_id):
        original_log_path = 'outputs/bears/original/{}.json'.format(bug_id)
        reproduced_log_path_buggy = 'outputs/bears/reproduced/buggy/{}.log'.format(bug_id)
        reproduced_log_path_fixed = 'outputs/bears/reproduced/fixed/{}.log'.format(bug_id)

        # three metrics to analysis: existence of bug, number match, name match
        reproducible_existence = False
        reproducible_num_match = False
        reproducible_name_match = False

        (original_num_test_failures, original_test_failures) = bearsAnalyzer.analyze_original_log(original_log_path)
        (reproduced_num_test_failures_buggy_version, reproduced_test_failures_buggy_version) = bearsAnalyzer.analyze_reproduced_log(reproduced_log_path_buggy)
        (reproduced_num_test_failures_fixed_version, reproduced_test_failures_fixed_version) = bearsAnalyzer.analyze_reproduced_log(reproduced_log_path_fixed)

        
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
    def check_test_run(log_lines):
        # return false if there are no test run at all
        for line in log_lines:
            if re.search('Tests run:', line):
                return True
        return False
    
    @staticmethod
    def extract_test_lines(log_lines):
        # extract test lines from log lines
    
        test_section_started = False
        reactor_started = False
        line_marker = 0
    
        err_lines = []
        err_msg = []
        test_lines = []
        reactor_lines = []
    
        # Strip ANSI color codes from lines, since they mess up the regex.
        # Taken from https://stackoverflow.com/a/14693789
        ansi_escape = re.compile(r'\x1B[@-_][0-?]*[ -/]*[@-~]', re.M)
    
        # Possible future improvement: We could even get all executed tests (also the ones which succeed)
        for line in log_lines:
            line = ansi_escape.sub('', line)
            if line[:7] == '[ERROR]':
                err_lines.append(line[8:])
            if 'usr/local/bin/run.sh:' in line and 'Killed' in line:
                err_msg.append(line)
            if '-------------------------------------------------------' in line and line_marker == 0:
                line_marker = 1
            elif re.search(r'\[INFO\] Reactor Summary:', line, re.M):
                reactor_started = True
                test_section_started = False
            elif reactor_started and not re.search(r'\[.*\]', line, re.M):
                reactor_started = False
            elif re.search(r' T E S T S', line, re.M) and line_marker == 1:
                line_marker = 2
            elif line_marker == 1:
                match = re.search(r'Building ([^ ]*)', line, re.M)
                if match:
                    if match.group(1) and len(match.group(1).strip()) > 0:
                        pass
                line_marker = 0
            elif '-------------------------------------------------------' in line and line_marker == 2:
                line_marker = 3
                test_section_started = True
            elif '-------------------------------------------------------' in line and line_marker == 3:
                line_marker = 0
                test_section_started = False
            else:
                line_marker = 0
    
            if test_section_started:
                test_lines.append(line)
            elif reactor_started:
                reactor_lines.append(line)
    
        return test_lines
    
    @staticmethod
    def get_num_test_failures(test_lines):
    
        failed_tests_started = False
        running_test = False
        curr_test = ""
    
        tests_failed_lines = []
        tests_failed = []
        tests_run = False
    
        num_tests_run = None
        num_tests_failed = None
        num_tests_skipped = None
    
        for line in test_lines:
            if re.search(r'(Failed tests:)|(Tests in error:)', line, re.M):
                failed_tests_started = True
            if failed_tests_started:
                tests_failed_lines.append(line)
                if len(line.strip()) < 1:
                    failed_tests_started = False
    
            match = re.search(r'Tests run: .*? Time elapsed: (.* s(ec)?)', line, re.M)
            if match:
                num_tests_run, num_tests_failed, num_tests_skipped = 0, 0, 0
                tests_run = True
                continue
            
            # To calculate num_tests_run, num_tests_failed, num_tests_skipped,
            # We ignore lines like Tests run: %d, Failures: %d, Errors: %d, Skipped: %d, Time elapsed: %f s - in ...
            # We only match lines like
            # Results :
            # ...
            # Tests run: %d, Failures: %d, Errors: %d, Skipped: %d
            match = re.search(r'Tests run: (\d*), Failures: (\d*), Errors: (\d*)(, Skipped: (\d*))?', line, re.M)
            if match:
                running_test = False
                num_tests_run, num_tests_failed, num_tests_skipped = 0, 0, 0
                tests_run = True
                num_tests_run += int(match.group(1))
                num_tests_failed += (int(match.group(2)) + int(match.group(3)))
                if match.group(4):
                    num_tests_skipped += int(match.group(5))
                continue
            
            # Added a space after Total tests run:, this differs from
            # TravisTorrent's original implementation. The observed output
            # of testng has a space. Consider updating the regex if we observe
            # a testng version that outputs whitespace differently.
            match = re.search(r'^Total tests run: (\d+), Failures: (\d+), Skips: (\d+)', line, re.M)
            if match:
                num_tests_run, num_tests_failed, num_tests_skipped = 0, 0, 0
                tests_run = True
                num_tests_run += int(match.group(1))
                num_tests_failed += int(match.group(2))
                num_tests_skipped += int(match.group(3))
                continue
            
            if line[:8] == 'Running ':
                running_test = True
                curr_test = line[8:]
    
            if running_test and '(See full trace by running task with --trace)' in line:
                tests_failed.append(curr_test)
    
        return (num_tests_run, num_tests_failed, num_tests_skipped)
    
    @staticmethod 
    def extract_test_method_name(line):
        match = re.search(r'(\w+(\[.+\])?\([\w.$\[\]]+\))', line)
        if match:
            return match.group(1)
        return None
    
    @staticmethod
    def get_test_failures(test_lines):
        cur_test_class = ''
        test_failures = []
    
        for line in test_lines:
            # Matches the lines of:
            # Tests run: 11, Failures: 2, Errors: 0, Skipped: 0, Time elapsed: 0.1 sec <<< FAILURE! - in path.to.TestCls
            match = re.search(r'<<< FAILURE! - in ([\w\.]+)', line, re.M)
            if match:
                cur_test_class = match.group(1)
            elif re.search(r'(<<< FAILURE!|<<< ERROR!)\s*$', line, re.M):
                failed_test = bearsAnalyzer.extract_test_method_name(line)
                if failed_test is None:
                    # Matches the likes of [ERROR] testMethod  Time elapsed: 0.011 sec  <<< FAILURE!
                    # Assuming that cur_test_class == 'path.to.TestCls', sets failed_test to 'testMethod(path.to.TestCls)
                    # '
                    match = re.search(r'^(\[ERROR\] )?(\w+)  Time elapsed:', line, re.M)
                    if match:
                        failed_test = cur_test_class
                if failed_test is None and cur_test_class != '':
                    # Matches the likes of [ERROR] path.to.TestClass.testMethod  Time elapsed: 0.011 sec  <<< FAILURE!
                    # This sets failed_test to 'testMethod(path.to.TestClass)'
                    test_class = re.escape(cur_test_class)
                    match = re.search(r'^(\[ERROR\] )?{}\.(\w+)  Time elapsed:'.format(test_class), line, re.M)
                    if match:
                        failed_test = cur_test_class
                if failed_test is None:
                    # Matches the likes of [ERROR] path.to.TestClass  Time elapsed: 0.011 sec  <<< FAILURE!
                    # This condition is only reached if the name of the test method is not present in the log.
                    # This sets failed_test to '(path.to.TestClass)'
                    match = re.search(r'^(\[ERROR\] )?([\w.]+)  Time elapsed:', line, re.M)
                    if match:
                        failed_test =  match.group(2) 
                if failed_test is not None:
                    match = re.search(r'\((.*?)\)', failed_test)
                    if match:
                        failed_test_class = match.group(1)
                        test_failures.append(failed_test_class)
                    else:
                        test_failures.append(failed_test)

        return test_failures