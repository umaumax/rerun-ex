#!/usr/bin/env python3

import numpy as np
import quaternion
import math
import time
import rerun as rr
import trimesh
import numpy as np


def generate_dummy_data():
    sequential_id = 0
    angular_velocity = np.array([0.1, 0.2, 0.3])
    dt = 0.1
    q = quaternion.from_euler_angles([0, 0, 0])
    while True:
        sequential_id += 1
        # quaternion_vec = np.quaternion(0.707, 0, 0.707, 0)

        x = (sequential_id - 30) * 0.1
        y = math.sin(x)
        z = math.cos(3 * x)
        rotation_increment = quaternion.from_euler_angles(
            angular_velocity * dt)
        q *= rotation_increment

        original_position = np.array([x, y, z])
        direction = np.array([0.0, 0.0, 1.0])
        rotated_direction = quaternion.rotate_vectors(q, direction)
        distance = 1.0
        rotated_vector = rotated_direction * distance
        yield (original_position, rotated_vector)


rr.init("PLY Point Cloud Viewer", spawn=True)


def create_viewcone(label, origin, quat, color):
    lines = [
        [
            [-0.5, -0.5, 0],
            [0.5, -0.5, 0],
            [0.5, 0.5, 0],
            [-0.5, 0.5, 0],
            [-0.5, -0.5, 0],
        ],
        [
            [-0.5, -0.5, 0],
            [0.0, 0.0, 1.44 / 2],
        ],
        [
            [0.5, -0.5, 0],
            [0.0, 0.0, 1.44 / 2],
        ],
        [
            [-0.5, 0.5, 0],
            [0.0, 0.0, 1.44 / 2],
        ],
        [
            [0.5, 0.5, 0],
            [0.0, 0.0, 1.44 / 2],
        ],
    ]
    rr.log(
        label,
        rr.LineStrips3D(
            lines,
            colors=[color] * len(lines),
            radii=[[0.025]] * len(lines),
            # labels=["one strip here", "and one strip there"],
        )
    )
    rr.log(
        label,
        rr.Transform3D(
            translation=origin,
            mat3x3=quaternion.as_rotation_matrix(quat)
        )
    )


def load_and_log_ply(file_path):
    point_cloud = trimesh.load(file_path)

    positions = point_cloud.vertices

    if hasattr(point_cloud, 'visual') and hasattr(
            point_cloud.visual, 'vertex_colors'):
        colors = point_cloud.visual.vertex_colors[:, :3]
    else:
        colors = np.ones((positions.shape[0], 3)) * 255

    radii = np.full(positions.shape[0], 0.01)

    for i in range(0, 10):
        origin = [i * 0.1, i * 0.2, 1]
        angle = math.radians(i * 20)
        q = quaternion.from_euler_angles([0, -angle, 0])
        label = 'viewcone/{}'.format(i)
        color = [255, 0, 0]
        create_viewcone(label, origin, q, color)

    rr.log(
        "PLY Point Cloud",
        rr.Points3D(
            positions=positions,
            colors=colors,
            radii=radii))


ply_files = [
    'ply-data/fragment.ply',
    'ply-data/fragment_000.ply',
    'ply-data/fragment_001.ply',
    'ply-data/fragment_002.ply',
]

dummy_data_generator = generate_dummy_data()
for ply_index, ply_file in enumerate(ply_files):
    rr.set_time_sequence("step", ply_index)

    load_and_log_ply(ply_file)
    n = 10
    for i in range(0, n):
        (o, v) = next(dummy_data_generator)
        # print(o, v)
        rr.log(
            "arrows-from-data/{}-{}".format(ply_index, i),
            rr.Arrows3D(
                origins=[o],
                vectors=[v],
                colors=[[1.0 * (i + ply_index * n) / (len(ply_files) * n), 0, 0.5, 0.5]]))

    time.sleep(1)
