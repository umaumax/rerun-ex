#!/usr/bin/env python3
import time
import re
import os
import argparse

import rerun as rr
import trimesh
import numpy as np

pre_positions = [[]]
# pre_positions = [[np.nan,np.nan,np.nan]]


def setdiff2d_set(src, dst):
    src_set = set(map(tuple, src))
    dst_set = set(map(tuple, dst))
    deleted_set = np.array(list(src_set - dst_set))
    added_set = np.array(list(dst_set - src_set))
    return (deleted_set, added_set)


def count_setdiff2d_set(src, dst):
    src_set = set(map(tuple, src))
    dst_set = set(map(tuple, dst))
    deleted_set = np.array(list(src_set - dst_set))
    added_set = np.array(list(dst_set - src_set))
    return (len(deleted_set), len(added_set))


def load_and_log_ply(filepath, point_size=0.001,
                     ply_division_number=100, ply_stride=1):
    point_cloud = trimesh.load(filepath)

    positions = point_cloud.vertices

    start = time.perf_counter()
    global pre_positions

    # A = np.array(pre_positions)
    # B = np.array(positions)
    # # print(A,B)
    # nrows, ncols = A.shape
    # dtype = {'names': ['f{}'.format(i) for i in range(ncols)],
    # 'formats': ncols * [A.dtype]}
#
    # deleted_points = len(np.setdiff1d(A.view(dtype), B.view(dtype)))
    # added_points = len(np.setdiff1d(B.view(dtype), A.view(dtype)))

    deleted_points, added_points = count_setdiff2d_set(
        pre_positions, positions)
    diff_points = deleted_points + added_points
    print(
        f"deleted + added points = diff points / total points (ratio): {deleted_points} + {added_points} = {diff_points} / {len(positions)} ({diff_points/len(positions)*100.0:.3f}%)")
    pre_positions = positions
    end = time.perf_counter()
    print('{:.2f}s {}'.format(end - start, filepath))

    if hasattr(point_cloud, 'visual') and hasattr(
            point_cloud.visual, 'vertex_colors'):
        colors = point_cloud.visual.vertex_colors[:, :3]
    else:
        colors = np.ones((positions.shape[0], 3)) * 255

    radii = np.full(positions.shape[0], point_size)

    print(
        'load ply:',
        filepath,
        'the number of point clouds:',
        len(positions))
    print(positions[0:5])

    # ply_stride # 1 to ply_division_number
    for offset in range(0, ply_division_number, ply_stride):
        rr.log(
            "PLY Point Cloud/({} at {})".format(offset +
                                                1, ply_division_number),
            rr.Points3D(
                positions=positions[offset::ply_division_number] * 1,
                colors=colors[offset::ply_division_number],
                radii=radii[offset::ply_division_number] * 1))


def main():
    parser = argparse.ArgumentParser(
        formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument('-s', '--spawn', action='store_true')
    parser.add_argument('--addr', default='127.0.0.1:9876')
    parser.add_argument('-a', '--app-title', default='no_app_name')
    parser.add_argument('--recording_id', default=None)
    parser.add_argument('--division-number', default=100, type=int)
    parser.add_argument(
        '--stride',
        default=1,
        type=int,
        help='set between 1 to --division-number')
    parser.add_argument('--offset', default=0, type=int)
    parser.add_argument('--interval', default=1, type=int)
    parser.add_argument('--point-size', default=0.001, type=float)
    parser.add_argument('-v', '--verbose', action='store_true')
    parser.add_argument('files', nargs='*')

    args, extra_args = parser.parse_known_args()
    spawn = args.spawn
    addr = args.addr
    app_title = args.app_title
    recording_id = args.recording_id

    point_size = args.point_size
    division_number = args.division_number
    stride = args.stride
    offset = args.offset
    interval = args.interval
    files = args.files

    if len(files) == 0:
        print("[WARN] Please set ply files.")
        return

    rr.init(
        "{}".format(app_title),
        recording_id=recording_id,
        spawn=spawn)
    if not spawn and addr:
        rr.connect(addr=addr)

        print('[all]', files)
        files = files[offset:]
        files = files[::interval]
        print('[filtered]:', files)

        for i, file in enumerate(files):
            id = i
            match = re.search('([0-9]+)\\.ply', file)
            if match:
                id = int(match.group(1))
            rr.set_time_sequence("id", id)
            load_and_log_ply(
                file,
                point_size,
                division_number,
                stride)


if __name__ == "__main__":
    main()
