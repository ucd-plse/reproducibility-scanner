import subprocess
from collections import Counter

def _run_command(command, cwd=None):
    if cwd:
        process = subprocess.Popen(command, cwd=cwd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)
    else:
        process = subprocess.Popen(
            command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)
    stdout, stderr = process.communicate()
    stdout = stdout.decode('utf-8').strip()
    stderr = stderr.decode('utf-8').strip()
    ok = process.returncode == 0
    return process, stdout, stderr, ok

def _equal_lists(list_a, list_b):
    # this is to compare if list_a and list_b are equal
    # and there could be duplicates in list_a and list_b
    # https://stackoverflow.com/questions/8106227/difference-between-two-lists-with-duplicates-in-python

    counter_a = Counter(list_a)
    counter_b = Counter(list_b)

    diff_a_b = counter_a - counter_b
    diff_b_a = counter_b - counter_a

    if len(diff_a_b) == 0 and len(diff_b_a) == 0:
        return True
    else:
        return False

def _get_artifact_list(file_path):
    with open(file_path, 'r') as f:
        artifact_list = f.read().splitlines()
    return artifact_list