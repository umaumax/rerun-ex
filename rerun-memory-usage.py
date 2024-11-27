#!/usr/bin/env python3

import time
import psutil
import rerun as rr


def track_memory_usage():
    addr = '127.0.0.1:9876'
    recording_id = "test_recording_id"
    application_id = "{}".format("memory_usage")
    rr.init(application_id,
            recording_id=recording_id,
            spawn=False,
            )
    rr.connect(addr=addr)

    rr.log(
        'memory\\ usage',
        rr.SeriesLine(
            # color=color,
            name="all",
        ),
        # timeless=True,
    )
    rr.log(
        'memory\\ usage',
        rr.SeriesPoint(
            # color=color,
            name="all",
            marker="circle",
            marker_size=2.0,
        ),
        # timeless=True,
    )

    t = 0
    while True:
        memory_info = psutil.virtual_memory()
        memory_used = memory_info.used / (1024 ** 2)  # MB

        value = memory_used
        rr.set_time_sequence("step", int(t))
        t += 1
        rr.log('memory\\ usage', rr.Scalar(value))
        print(t, value)
        time.sleep(0.1)


if __name__ == "__main__":
    track_memory_usage()
