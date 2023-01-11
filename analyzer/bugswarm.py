import logging
import os, sys
import json

from utils import _equal_lists

from bugswarm.analyzer.analyzer import Analyzer
from bugswarm.common.rest_api.database_api import DatabaseAPI

logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s %(levelname)-8s %(message)s',
                    datefmt='%Y-%m-%d %H:%M:%S')

bugswarm_log_dir = 'outputs/bugswarm/'

class bugswarmAnalyzer(object):
    def __init__(self):
        pass

    @staticmethod
    def analyze_travis_build_log(log_path):
        # analyze travis build log
        # return the number of test failures and list of test failures
        image_tag = log_path.split('/')[-1].split('.')[0]
        job_id = image_tag.split('-')[-1]
        failed_or_passed = None
        buggy_for_fixed = log_path.split('/')[-2]
        if buggy_for_fixed == 'buggy':
            failed_or_passed = 'failed'
        elif buggy_for_fixed == 'fixed':
            failed_or_passed = 'passed'

        # the bugswarm token was requested from http://www.bugswarm.org/contact/
        # we reveal the token here for replication purposes
        # please do not abuse this token
        bugswarm_token = 'pMWUOry6eJyj_OycTOXEDOW0MFmBSjFIIRjwWFBmzAc'
        bugswarm_api = DatabaseAPI(token=bugswarm_token)

        artifact_info = json.loads(bugswarm_api.find_artifact(image_tag).content)

        build_system = artifact_info['build_system'].lower()
        trigger_sha = artifact_info['{}_job'.format(failed_or_passed)]['trigger_sha']
        repo = artifact_info['repo']
        api_test_failures = artifact_info['{}_job'.format(failed_or_passed)]['num_tests_failed']

        log_path = os.path.join(os.getcwd(), log_path)

        try:
            analyze_result = Analyzer().analyze_single_log(log_path = log_path, job_id = job_id, build_system = build_system, trigger_sha = trigger_sha, repo = repo)
            num_test_failures = analyze_result['tr_log_num_tests_failed']
            
            test_failures = analyze_result['tr_log_tests_failed'].split('#')
            test_failures = list(set(test_failures))
            if test_failures[0] == '':
                test_failures = test_failures[1:]

            has_tests_ran = analyze_result['tr_log_bool_tests_ran']
            # num_test_failures should be equal to len(test_failures)
            if num_test_failures != len(test_failures):
                pass
                # return None, None
                # logging.warning('Number of test failures extracted does not match the analysis result')
            # has_tests_ran should be True when len(test_failures) > 0
            if has_tests_ran and len(test_failures) == 0 and buggy_for_fixed == 'buggy':
                # The test failures on buggy version have vanished
                return None, None
            return len(test_failures), test_failures
        except Exception as e:
            logging.error('Failed to analyze log: {}'.format(log_path))
            logging.error(e)
            return None, None

    def analyze(bug_id):
        original_buggy_log_path = os.path.join(os.getcwd(), bugswarm_log_dir, 'original', 'buggy', '{}.log'.format(bug_id))
        original_fixed_log_path = os.path.join(os.getcwd(), bugswarm_log_dir, 'original', 'fixed', '{}.log'.format(bug_id))
        reproduced_buggy_log_path = os.path.join(os.getcwd(), bugswarm_log_dir, 'reproduced', 'buggy', '{}.log'.format(bug_id)) 
        reproduced_fixed_log_path = os.path.join(os.getcwd(), bugswarm_log_dir, 'reproduced', 'fixed', '{}.log'.format(bug_id))
    
        original_buggy_num_test_failures, original_buggy_test_failures = bugswarmAnalyzer.analyze_travis_build_log(original_buggy_log_path)
        original_fixed_num_test_failures, original_fixed_test_failures = bugswarmAnalyzer.analyze_travis_build_log(original_fixed_log_path)
        reproduced_buggy_num_test_failures, reproduced_buggy_test_failures = bugswarmAnalyzer.analyze_travis_build_log(reproduced_buggy_log_path)
        reproduced_fixed_num_test_failures, reproduced_fixed_test_failures = bugswarmAnalyzer.analyze_travis_build_log(reproduced_fixed_log_path)
    
        # three metrics to analyze: existence of bug, number match, name match
        reproducible_existence = False
        reproducible_num_match = False
        reproducible_name_match = False
    
        # it is not reproducible if there is analyze error. But we don't observe this in experiments
        if None in [original_buggy_num_test_failures, original_buggy_test_failures, original_fixed_num_test_failures, original_fixed_test_failures, reproduced_buggy_num_test_failures, reproduced_buggy_test_failures, reproduced_fixed_num_test_failures, reproduced_fixed_test_failures]:
            return (reproducible_existence, reproducible_num_match, reproducible_name_match)
    
        if reproduced_fixed_num_test_failures > 0 and original_fixed_num_test_failures == 0:
            # there are test failures on fixed version
            # which means the patch is not working anymore
            # so the artifact is not reproducible
            reproducible_existence = False
            reproducible_num_match = False
            reproducible_name_match = False
            return (reproducible_existence, reproducible_num_match, reproducible_name_match)
        else:
            if reproduced_buggy_num_test_failures > 0:
                reproducible_existence = True
            if reproduced_buggy_num_test_failures == 0 and original_buggy_num_test_failures == 0:
                # we define existence still holds when original buggy log has no test failures
                # and reproduced buggy log has no test failures
                # This means the reproducibility of 'existence' holds
                reproducible_existence = True
            if reproduced_buggy_num_test_failures == original_buggy_num_test_failures:
                # this case contains 0 == 0
                # which means there are no test failures on original buggy version
                # and no test failures on reproduced buggy version
                # in this case, the build failures are not caused by test failures
                reproducible_num_match = True
            if _equal_lists(original_buggy_test_failures, reproduced_buggy_test_failures):
                # this case contains [] == []
                # use Counter to compare two lists because it is possible that the same test class fails multiple times
                # https://stackoverflow.com/questions/8106227/difference-between-two-lists-with-duplicates-in-python
                reproducible_name_match = True
            return (reproducible_existence, reproducible_num_match, reproducible_name_match)