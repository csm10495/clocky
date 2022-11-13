from .__main__ import seconds_to_time_str


def test_seconds_to_time_str():
    assert seconds_to_time_str(5.2344, gnu_elapsed_real_time=False) == "0m5.234s"
    assert seconds_to_time_str(65.2344, gnu_elapsed_real_time=False) == "1m5.234s"
    assert seconds_to_time_str(65.2344, gnu_elapsed_real_time=False) == "1m5.234s"
    assert seconds_to_time_str(3605.2344, gnu_elapsed_real_time=False) == "1h0m5.234s"

    assert seconds_to_time_str(5, gnu_elapsed_real_time=True) == "0:05.00"
    assert seconds_to_time_str(5.2344, gnu_elapsed_real_time=True) == "0:05.23"
    assert seconds_to_time_str(65.2344, gnu_elapsed_real_time=True) == "1:05.23"
    assert seconds_to_time_str(3605.2344, gnu_elapsed_real_time=True) == "1:00:05.23"
