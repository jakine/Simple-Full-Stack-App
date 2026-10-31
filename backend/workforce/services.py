from datetime import date


def ranges_overlap(start_a, end_a, start_b, end_b):
    end_a = end_a or date.max
    end_b = end_b or date.max
    return start_a <= end_b and start_b <= end_a
