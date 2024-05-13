#!/usr/bin/env python3

import argparse
import csv
import numpy as np
import sys
import time

import rerun as rr


def main():
    parser = argparse.ArgumentParser(
        formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument('-s', '--spawn', action='store_true')
    parser.add_argument('--addr', default='127.0.0.1:9876')
    parser.add_argument('-a', '--app-title', default='no_app_name')
    parser.add_argument('-t', '--title', default='no_graph_name')
    parser.add_argument('-c', '--color-seed', default=0)
    parser.add_argument('--recording_id', default=None)
    parser.add_argument('--marker_size', default=2)
    parser.add_argument('--interval', type=float, default=0.0)
    parser.add_argument(
        '-i',
        '--input-filepath',
        type=argparse.FileType(),
        default=sys.stdin)
    parser.add_argument('-v', '--verbose', action='store_true')
    parser.add_argument('args', nargs='*')

    args, extra_args = parser.parse_known_args()
    spawn = args.spawn
    addr = args.addr
    app_title = args.app_title
    title = args.title
    seed = args.color_seed
    marker_size = args.marker_size
    recording_id = args.recording_id
    interval = args.interval
    input_filepath = args.input_filepath

    np.random.seed(seed=seed)
    with input_filepath as f:
        reader = csv.reader(f)
        header = next(reader)
        print('header:', header)

        rr.init(
            "{}".format(app_title),
            recording_id=recording_id,
            spawn=spawn)
        if not spawn:
            rr.connect(addr=addr)

        for column_name in header[1:]:
            color = list(np.random.choice(range(256), size=3))
            print('{} color is: {}'.format(column_name, color))
            rr.log(
                "{}/{}".format(title, column_name),
                rr.SeriesLine(
                    color=color,
                    name="{}".format(column_name),
                ),
                timeless=True,
            )
            rr.log(
                "{}/{}".format(title, column_name),
                rr.SeriesPoint(
                    color=color,
                    name="{}".format(column_name),
                    marker="circle",
                    marker_size=marker_size,
                ),
                timeless=True,
            )

        for t, row in enumerate(reader):
            rr.set_time_sequence("step", int(row[0]))
            for i, column_name in enumerate(header[1:], 1):
                print('{}[{}]={}'.format(column_name, t, row[i]))
                rr.log("{}/{}".format(title, column_name), rr.Scalar(row[i]))
            time.sleep(interval)


if __name__ == "__main__":
    main()
