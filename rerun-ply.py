#!/usr/bin/env python3
import time
import re
import os
import argparse
import math

import rerun as rr
import trimesh
import numpy as np

pre_positions = []


def setdiff2d_set(src, dst):
    src_set = set(map(tuple, src))
    dst_set = set(map(tuple, dst))
    deleted_set = np.array(list(src_set - dst_set))
    added_set = np.array(list(dst_set - src_set))
    return (deleted_set, added_set)


def count_setdiff2d_set(src, dst):
    deleted_set, added_set = setdiff2d_set(src, dst)
    return (len(deleted_set), len(added_set))


def load_plyfile(filepath):
    point_cloud = trimesh.load(filepath)
    return point_cloud


def load_example_point_clouds(num_points=10000):
    class ExamplePcd:

        def __init__(self, vertices):
            self.vertices = vertices

    # positions = np.random.rand(num_points, 3)

    indices = np.arange(num_points)
    np.random.seed(42)
    positions = np.random.rand(num_points, 3) + \
        indices[:, None] / 10000 * 0.5
    return ExamplePcd(positions)


def load_and_log_ply(point_cloud, point_size=0.001,
                     ply_division_number=100, ply_stride=1, splitting_method='overall'):
    positions = point_cloud.vertices

    start = time.perf_counter()
    global pre_positions

    # if len(pre_positions) == 0:
    # pre_positions = [[np.nan, np.nan, np.nan]]
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
        f"deleted + added points = diff points / current total points (ratio): {deleted_points} + {added_points} = {diff_points} / {len(positions)} ({diff_points/len(positions)*100.0:.3f}%)")
    end = time.perf_counter()
    print('{:.2f}s'.format(end - start))

    if hasattr(point_cloud, 'visual') and hasattr(
            point_cloud.visual, 'vertex_colors'):
        colors = point_cloud.visual.vertex_colors[:, :3]
    else:
        # white
        # colors = np.ones((positions.shape[0], 3)) * 1.0

        # gradation
        num_points = len(positions)
        colors = np.column_stack((
            np.linspace(0, 1, num_points),  # r
            np.linspace(0, 1, num_points),  # g
            np.linspace(0, 1, num_points),  # b
        ))
        # NOTE: compare with same index
        min_length = min(len(pre_positions), len(positions))
        max_length = max(len(pre_positions), len(positions))
        # print(min_length, max_length)
        for i in range(min_length):
            if pre_positions[i, 1] == positions[i, 1]:
                pass  # no change
            else:
                colors[i] = [1, 0, 0]  # changed
        for i in range(min_length, max_length):
            colors[i] = [0, 1, 0]  # new

    radii = np.full(positions.shape[0], point_size)

    print('load ply: the number of point clouds:', len(positions))

    # ply_stride # 1 to ply_division_number
    if splitting_method == 'overall':
        for offset in range(0, ply_division_number, ply_stride):
            rr.log(
                "PLY\\ Point\\ Cloud/({}\\ at\\ {})".format(offset +
                                                            1, ply_division_number),
                rr.Points3D(
                    positions=positions[offset::ply_division_number],
                    colors=colors[offset::ply_division_number],
                    radii=radii[offset::ply_division_number]))
    elif splitting_method == 'order':
        n_positions = len(positions)
        n_block_points = math.ceil(n_positions / ply_division_number)
        for offset in range(0, n_positions, n_block_points):
            rr.log(
                "PLY\\ Point\\ Cloud/({}\\ at\\ {})".format(int(offset / n_block_points) +
                                                            1, ply_division_number),
                rr.Points3D(
                    positions=positions[offset:offset +
                                        n_block_points:ply_stride],
                    colors=colors[offset:offset + n_block_points:ply_stride],
                    radii=radii[offset:offset + n_block_points:ply_stride]))
    else:
        print(f"[ERR] Invalid splitting_method '{splitting_method}'")

    pre_positions = positions


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
    parser.add_argument(
        '--splitting-method',
        default='overall',
        choices=[
            'overall',
            'order'])
    parser.add_argument('-v', '--verbose', action='store_true')
    parser.add_argument('files', nargs='*')

    args, extra_args = parser.parse_known_args()
    spawn = args.spawn
    addr = args.addr
    app_title = args.app_title
    recording_id = args.recording_id

    point_size = args.point_size
    splitting_method = args.splitting_method
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
            if file == 'example':
                num_points = 10000 + i * 1000
                pcd = load_example_point_clouds(num_points)
                pcd.vertices[i * 1000:(i + 1) * 1000, :] += [0.1, 0.1, 0.1]
            else:
                pcd = load_plyfile(file)
            load_and_log_ply(
                pcd,
                point_size,
                division_number,
                stride,
                splitting_method)


if __name__ == "__main__":
    main()
