#!/usr/bin/env python3
import time
import re
import os
import argparse
import math

import rerun as rr
import trimesh
import numpy as np


def setdiff2d_set(src, dst):
    src_set = set(map(tuple, src))
    dst_set = set(map(tuple, dst))
    deleted_set = src_set - dst_set
    added_set = dst_set - src_set
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


class RerunPlySender:

    def __init__(self):
        self.pre_positions = np.array([])
        self.pre_colors = np.array([])
        self.pre_max_index = 0

    def log(self, point_cloud, point_size=0.001,
            ply_division_number=100, ply_block_number=1000, ply_stride=1, splitting_method='overall', enable_diff_by_index=False, enable_diff_by_position=False):
        positions = np.array(point_cloud.vertices)
        print('the number of point clouds:', len(positions))

        if False:
            start = time.perf_counter()
            if True:
                if len(self.pre_positions) == 0:
                    self.pre_positions = np.array([[np.nan, np.nan, np.nan]])
                nrows, ncols = self.pre_positions.shape
                dtype = {'names': ['f{}'.format(i) for i in range(ncols)],
                         'formats': ncols * [self.pre_positions.dtype]}

                deleted_points = len(
                    np.setdiff1d(
                        self.pre_positions.view(dtype),
                        positions.view(dtype)))
                added_points = len(
                    np.setdiff1d(
                        positions.view(dtype),
                        self.pre_positions.view(dtype)))
            else:
                deleted_points, added_points = count_setdiff2d_set(
                    self.pre_positions, positions)

            diff_points = deleted_points + added_points
            print(
                f"({added_points}(added) + {deleted_points}(deleted) = {diff_points}(diff)) / {len(positions)}(current) ({diff_points/len(positions)*100.0:.3f}%)")
            end = time.perf_counter()
            print('{:.2f}s'.format(end - start))

        if hasattr(point_cloud, 'visual') and hasattr(
                point_cloud.visual, 'vertex_colors'):
            colors = np.array(point_cloud.visual.vertex_colors[:, :3])
        else:
            # white
            # colors = np.ones((positions.shape[0], 3)) * 1.0

            # gradation
            num_points = len(positions)
            colors = np.column_stack((
                np.linspace(0, 255, num_points, dtype='int'),  # r
                np.linspace(0, 255, num_points, dtype='int'),  # g
                np.linspace(0, 255, num_points, dtype='int'),  # b
            ))

        if enable_diff_by_index and enable_diff_by_position:
            print(
                '[ERR] both enable_diff_by_index and enable_diff_by_position are enabled')

        if enable_diff_by_index:
            # NOTE: compare with same index
            min_length = min(len(self.pre_positions), len(positions))
            no_change_cnt = 0
            changed_cnt = 0
            added_cnt = 0
            deleted_cnt = 0
            for i in range(min_length):
                if np.array_equal(self.pre_positions[i], positions[i]):
                    no_change_cnt += 1  # no change
                else:
                    colors[i] = [255, 255, 0]  # changed
                    changed_cnt += 1
            for i in range(min_length, len(positions)):
                colors[i] = [0, 255, 0]  # added
                added_cnt += 1
            deleted_cnt = max(0, len(self.pre_positions) - len(positions))
            diff_cnt = changed_cnt + added_cnt + deleted_cnt
            print(f"{no_change_cnt}(no_change), ({changed_cnt}(changed) + {added_cnt}(added) + {deleted_cnt}(deleted) = {diff_cnt}(diff)) / {len(positions)}(current) ({diff_cnt/len(positions)*100.0:.3f}%)")

        if enable_diff_by_position:
            deleted_set, added_set = setdiff2d_set(
                self.pre_positions, positions)
            for i in range(0, len(positions)):
                if tuple(positions[i]) in added_set:
                    colors[i, :3] = [0, 255, 0]  # diff(changed or added)
            changed_or_added_cnt = len(added_set)
            changed_or_deleted_cnt = len(deleted_set)
            diff_cnt = changed_or_added_cnt + changed_or_deleted_cnt
            print(
                f"({changed_or_added_cnt}(changed or added) + {changed_or_deleted_cnt}(changed or deleted) = {diff_cnt}(diff)) / {len(positions)}(current) ({diff_cnt/len(positions)*100.0:.3f}%)")

        radii = np.full(positions.shape[0], point_size)

        # ply_stride # 1 to ply_division_number
        if splitting_method == 'overall':
            for offset in range(0, ply_division_number, ply_stride):
                rr.log(
                    "PLY\\ Point\\ Cloud/data/({}\\ at\\ {})".format(offset +
                                                                     1, ply_division_number),
                    rr.Points3D(
                        positions=positions[offset::ply_division_number],
                        colors=colors[offset::ply_division_number],
                        radii=radii[offset::ply_division_number]))
        elif splitting_method == 'order':
            n_positions = len(positions)
            n_block_points = ply_block_number
            n_blocks = math.ceil(n_positions / n_block_points)
            skip_cnt = 0
            for i in range(0, n_blocks):
                offset = n_block_points * i
                label = "PLY\\ Point\\ Cloud/data/({})".format(i)
                pre_positions_block = np.array(
                    self.pre_positions[offset:offset + n_block_points:ply_stride])
                positions_block = np.array(
                    positions[offset:offset + n_block_points:ply_stride])
                pre_colors_block = np.array(
                    self.pre_colors[offset:offset + n_block_points:ply_stride])
                colors_block = np.array(
                    colors[offset:offset + n_block_points:ply_stride])
                if np.array_equal(pre_positions_block, positions_block) and (
                        (not enable_diff_by_index and not enable_diff_by_position) or np.array_equal(pre_colors_block, colors_block)):
                    skip_cnt += 1
                    # print('skipped', label, '/', n_blocks)
                else:
                    rr.log(label,
                           rr.Points3D(
                               positions=positions_block,
                               colors=colors_block,
                               radii=radii[offset:offset + n_block_points:ply_stride]))
            print(f'skipped {skip_cnt} / {n_blocks}')
            self.pre_max_index = max(self.pre_max_index, n_blocks)
            for i in range(n_blocks, self.pre_max_index):
                label = "PLY\\ Point\\ Cloud/data/({})".format(i)
                rr.log(label, rr.Clear.recursive())
        else:
            print(f"[ERR] Invalid splitting_method '{splitting_method}'")
        label = "PLY\\ Point\\ Cloud/info"
        rr.log(label, rr.AnyValues(length=len(positions)))

        self.pre_positions = positions
        self.pre_colors = colors


def main():
    parser = argparse.ArgumentParser(
        formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument('-s', '--spawn', action='store_true')
    parser.add_argument('--addr', default='127.0.0.1:9876')
    parser.add_argument('-a', '--app-title', default='no_app_name')
    parser.add_argument('--recording_id', default=None)
    parser.add_argument(
        '--block-number',
        default=1000,
        type=int,
        help='block number for --splitting-method=order')
    parser.add_argument(
        '--division-number',
        default=100,
        type=int,
        help='division number for --splitting-method=overall')
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
    parser.add_argument('--enable-diff-by-index', action='store_true')
    parser.add_argument('--enable-diff-by-position', action='store_true')
    parser.add_argument('--off-auto-index', action='store_true')
    parser.add_argument('-v', '--verbose', action='store_true')
    parser.add_argument('files', nargs='*')

    args, extra_args = parser.parse_known_args()
    if len(extra_args):
        print(f"[ERR] There is extra args {extra_args}")
        return

    files = args.files
    if len(files) == 0:
        print("[WARN] Please set ply files.")
        return

    rr.init(
        "{}".format(args.app_title),
        recording_id=args.recording_id,
        spawn=args.spawn)
    if not args.spawn and args.addr:
        rr.connect(addr=args.addr)

        print('[raw input]', files)
        files = files[args.offset:]
        files = files[::args.interval]
        print('[filtered input]:', files)

        # cnt = 0
        ply_sender = RerunPlySender()
        for i, file in enumerate(files):
            id = i
            if not args.off_auto_index:
                match = re.search('([0-9]+)\\.ply', file)
                if match:
                    id = int(match.group(1))
            print('id:', id)
            rr.set_time_sequence("id", id)
            if file == 'example':
                num_points = 10000 + i * 1000
                pcd = load_example_point_clouds(num_points)
                pcd.vertices[i * 1000:(i + 1) * 1000, :] += [0.1, 0.1, 0.1]
                # if cnt == 2:
                # pcd.vertices = pcd.vertices[:1000]
                # if cnt == 4:
                # pcd.vertices = np.delete(pcd.vertices, 1, 0)
            else:
                pcd = load_plyfile(file)
            # if cnt == 3:
                # pcd.vertices = np.delete(pcd.vertices, 1, 0)
            # cnt += 1
            ply_sender.log(
                pcd,
                args.point_size,
                args.division_number,
                args.block_number,
                args.stride,
                args.splitting_method,
                args.enable_diff_by_index,
                args.enable_diff_by_position,
            )


if __name__ == "__main__":
    main()
