from collections import Counter

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