import argparse
import numpy as np
from . import logger
from scantools.utils.utils import read_csv, write_csv
from scantools.utils.io import read_sequence_list
from pathlib import Path
from scantools import (
    run_combine_sequences, 
    run_sequence_aligner, 
    run_radio_transfer,
    )
from scantools.proc.alignment.image_matching import KeyFramingConf
from scipy.spatial.transform import Rotation as R
import matplotlib.pyplot as plt
from scantools.capture import Capture

def generate_random_transform_6DOF():
    """
    Generates a random transformation consisting of a quaternion and a translation vector.
    Returns:
        transform: A list containing the quaternion [qw, qx, qy, qz] and translation [tx, ty, tz].
        T: The corresponding 4x4 transformation matrix in Euclidean form.
    """

    r = R.random()
    q = r.as_quat()
    q = [q[3], q[0], q[1], q[2]]

    t = np.random.uniform(-10.0, 10.0, size=3)
    
    T = quaternion_and_translation_to_matrix(q, t)

    r_euler = R.from_quat([q[1], q[2], q[3], q[0]])
    euler_angles_rad = r_euler.as_euler('xyz', degrees=False)
    euler_angles_deg = np.degrees(euler_angles_rad)

    logger.info(f"Generated random transform:")
    logger.info(f"Quaternion (wxyz): {q}")
    logger.info(f"Euler angles (degrees) [roll (X), pitch (Y), yaw (Z)]: {euler_angles_deg}")
    logger.info(f"Translation (meters) [X, Y, Z]: {t}")
    logger.info("Transformation matrix (Euclidean form):\n" + "\n".join(["  " + str(row) for row in T]))

    return [float(x) for x in q + list(t)], T

def generate_random_transform_4DOF():
    """
    Generates a random 4DOF transformation: rotation around Z-axis + 3D translation.
    Returns:
        transform: A list containing the quaternion [qw, qx, qy, qz] and translation [tx, ty, tz].
        T: The corresponding 4x4 transformation matrix in Euclidean form.
    """
    # Random yaw (rotation about Z-axis)
    yaw = np.random.uniform(-np.pi, np.pi)
    r = R.from_euler('z', yaw)
    q = r.as_quat()
    q = [q[3], q[0], q[1], q[2]]

    # Random translation
    t = np.random.uniform(-10.0, 10.0, size=3)

    # Create transformation matrix
    T = quaternion_and_translation_to_matrix(q, t)

    r_euler = R.from_quat([q[1], q[2], q[3], q[0]])
    euler_angles_rad = r_euler.as_euler('xyz', degrees=False)
    euler_angles_deg = np.degrees(euler_angles_rad)

    logger.info(f"Generated random transform:")
    logger.info(f"Quaternion (wxyz): {q}")
    logger.info(f"Euler angles (degrees) [roll (X), pitch (Y), yaw (Z)]: {euler_angles_deg}")
    logger.info(f"Translation (meters) [X, Y, Z]: {t}")
    logger.info("Transformation matrix (Euclidean form):\n" + "\n".join(["  " + str(row) for row in T]))

    return [float(x) for x in q + list(t)], T

def quaternion_and_translation_to_matrix(q, t):
    """
    Converts a quaternion and translation vector into a 4x4 transformation matrix.
    Args:
        q: Quaternion in the format [w, x, y, z].
        t: Translation vector as a list [tx, ty, tz].
    Returns:
        T: 4x4 transformation matrix.
    """
    r = R.from_quat([q[1], q[2], q[3], q[0]])
    T = np.eye(4)
    T[:3, :3] = r.as_matrix()
    T[:3, 3] = t
    return T

def decompose_matrix(T):
    """
    Decomposes a transformation matrix into quaternion and translation vector.
    Args:
        T: 4x4 transformation matrix.
    Returns:
        q: Quaternion in the format [w, x, y, z].
        t: Translation vector as a list [tx, ty, tz].
    """
    r = R.from_matrix(T[:3, :3])
    q = r.as_quat()
    q = [q[3], q[0], q[1], q[2]]
    t = T[:3, 3]
    return q, t

def set_axes_equal(ax):
    """

    Args:
        
    Returns:

    """
    x_limits = ax.get_xlim3d()
    y_limits = ax.get_ylim3d()
    z_limits = ax.get_zlim3d()

    x_range = abs(x_limits[1] - x_limits[0])
    x_middle = np.mean(x_limits)
    y_range = abs(y_limits[1] - y_limits[0])
    y_middle = np.mean(y_limits)
    z_range = abs(z_limits[1] - z_limits[0])
    z_middle = np.mean(z_limits)

    plot_radius = 0.5 * max([x_range, y_range, z_range])

    ax.set_xlim3d([x_middle - plot_radius, x_middle + plot_radius])
    ax.set_ylim3d([y_middle - plot_radius, y_middle + plot_radius])
    ax.set_zlim3d([z_middle - plot_radius, z_middle + plot_radius])

def map_query_visualization(
        translation_orig: list = [],
        translation_new: list = [],
        translation_restored: list = [],
        visualization_path: str = '',
        map_id: str = ''
    ):
    """

    Args:
        
    Returns:

    """

    # TODO: SAVE INTO VISUALIZATION FOLDER

    # ---------- Visualization ----------
    translation_orig = np.array(translation_orig)
    translation_new = np.array(translation_new)
    translation_restored = np.array(translation_restored)

    # ---------- Visualization: Original vs Restored ----------
    elev, azim = 90, 0
    fig = plt.figure(figsize=(10, 8))
    ax = fig.add_subplot(111, projection='3d')
    ax.scatter(*translation_orig.T, c='blue', label='Original', alpha=0.6)
    ax.set_title(f"Original Trajectory: {map_id}")
    ax.set_xlabel("X")
    ax.set_ylabel("Y")
    ax.set_zlabel("Z")
    ax.view_init(elev=elev, azim=azim)
    ax.legend()
    set_axes_equal(ax)
    ax.grid(True)

    img_path_orig = visualization_path / Path(map_id + 'trajectory_original_topdown.png')
    plt.savefig(img_path_orig)
    plt.close()
    logger.info(f"Saved original trajectory to {img_path_orig}")

    fig = plt.figure(figsize=(10, 8))
    ax = fig.add_subplot(111, projection='3d')
    ax.scatter(*translation_new.T, c='red', label='Transformed', alpha=0.6)
    ax.set_title(f"Transformed Trajectory: {map_id}")
    ax.set_xlabel("X")
    ax.set_ylabel("Y")
    ax.set_zlabel("Z")
    ax.view_init(elev=elev, azim=azim)
    ax.legend()
    set_axes_equal(ax)
    ax.grid(True)

    img_path_new = visualization_path / Path(map_id + 'trajectory_transformed_topdown.png')
    plt.savefig(img_path_new)
    plt.close()
    logger.info(f"Saved transformed trajectory to {img_path_new}")

    # ---------- Visualization: Original and Tranformed ----------
    fig = plt.figure(figsize=(10, 8))
    ax = fig.add_subplot(111, projection='3d')
    ax.scatter(*translation_orig.T, c='blue', label='Original', alpha=0.6)
    ax.scatter(*translation_new.T, c='red', label='Transformed', alpha=0.6)

    ax.set_title(f"Trajectory Transform Visualization: {map_id}")
    ax.set_xlabel("X")
    ax.set_ylabel("Y")
    ax.set_zlabel("Z")
    #ax.view_init(elev=elev, azim=azim)
    ax.view_init(elev=0, azim=0)
    ax.legend()
    set_axes_equal(ax)
    ax.grid(True)

    img_path = visualization_path / Path(map_id + 'trajectory_transform.png')
    plt.savefig(img_path)
    plt.close()
    logger.info(f"Saved trajectory visualization to {img_path}")

    # ---------- Visualization: Original vs Restored ----------
    fig = plt.figure(figsize=(10, 8))
    ax = fig.add_subplot(111, projection='3d')
    ax.scatter(*translation_orig.T, c='blue', label='Original', alpha=0.6)
    ax.scatter(*translation_restored.T, c='green', label='Restored', alpha=0.6)

    for o, r in zip(translation_orig, translation_restored):
        ax.plot([o[0], r[0]], [o[1], r[1]], [o[2], r[2]], c='gray', alpha=0.3)

    ax.set_title(f"Inverse Transform Check: {map_id}")
    ax.set_xlabel("X")
    ax.set_ylabel("Y")
    ax.set_zlabel("Z")
    ax.view_init(elev=70, azim=30)
    ax.legend()
    set_axes_equal(ax)
    ax.grid(True)

    img_path_restored = visualization_path / Path(map_id + 'trajectory_inverse_transform.png')
    plt.savefig(img_path_restored)
    plt.close()
    logger.info(f"Saved inverse transform check visualization to {img_path_restored}")


def rotate_trajectories(
        capture: Capture, 
        map_id: str
    ) -> None:
    """
    Rotate trajectories for a given map_id by applying a random transformation.
    Args:
        capture: Capture object containing the session data.
        map_id: Identifier for the map to process.
    Output:
        None
    """

    map_path = capture.session_path(map_id)
    
    trajectories, col_trajectories = read_csv(map_path / 'trajectories.txt')

    trajectories_out = []

    translation_new = []
    translation_orig = []
    translation_restored = []

    #transform, translation_matrix = generate_random_transform_6DOF()
    transform, translation_matrix = generate_random_transform_4DOF()
    translation_matrix_inv = np.linalg.inv(translation_matrix)
    col_transform = ['map_id', 'qw', 'qx', 'qy', 'qz', 'tx', 'ty', 'tz']

    for line in trajectories:
            
        q_orig = [float(i) for i in line[2:6]]
        t_orig = [float(i) for i in line[6:9]]

        T_orig = quaternion_and_translation_to_matrix(q_orig, t_orig)
        T_aug = translation_matrix @ T_orig

        q_aug, t_aug = decompose_matrix(T_aug)

        translation_new.append(t_aug)
        translation_orig.append(t_orig)

        T_restored = translation_matrix_inv @ T_aug
        _, t_restored = decompose_matrix(T_restored)
        translation_restored.append(t_restored)


        new_line = [line[0], line[1]] + [str(v) for v in q_aug + list(t_aug)]

        if len(line) > 9:
            new_line += line[9:]

        trajectories_out.append(new_line)
    
    map_query_visualization(translation_orig, translation_new, translation_restored, capture.viz_path(), map_id)

    write_csv(map_path / 'trajectories_augumented.txt', trajectories_out, col_trajectories)
    write_csv(map_path / 'transforms.txt', [[map_id] + [str(x) for x in transform]], col_transform)

    logger.info(f"Augumented trajectories for {map_id} and saved to {map_path / 'trajectories_augumented.txt'}.")

def process_map_or_query(
        device: str = "",
        capture: Capture = None,
        map_or_query: str = ""
    ) -> None:
    """
    Process map or query for file_path given.

    Args:
        device: "ios", "hl", or "spot
        merge_file_path: Path to merge file
        map_or_query: "map" or "query"
    Output:
        None    
    """

    sessions_id = []
    capture_path = capture.path
    file_path = capture_path / f"{device}_{map_or_query}.txt"
    #sessions_id = read_sequence_list(file_path)

    #with open(file_path, "r") as f:
    #    for line in f.readlines():
    #        if not line.startswith("#"):
    #            sessions_id.append(line.strip())

    output_id = device + "_" + map_or_query
    logger.info(f"Merging {map_or_query} for {device} from file {file_path} into folder {output_id}.")
    logger.info("Sessions to merge: \n    " + "\n    ".join(sessions_id))

    if map_or_query == "map":
        overwrite_poses = True
    elif map_or_query == "query":                    
        overwrite_poses = False

    if device == "ios":
        keyframing_conf = KeyFramingConf()
    elif device == "hl":
        keyframing_conf = KeyFramingConf(**run_sequence_aligner.conf_hololens["localizer"]["keyframing"])
    elif device == "spot":          
        keyframing_conf = KeyFramingConf()

    run_combine_sequences.run(
            capture, sessions_id, output_id, overwrite_poses=overwrite_poses,
            keyframing=keyframing_conf)
    
    if map_or_query == "map":
        rotate_trajectories(capture, output_id)

    logger.info(f"Done merging {map_or_query} for {device}.\n")

    return sessions_id

def run(capture: Capture,
        iosq: bool = False,
        hlq: bool = False,
        spotq: bool = False,
        iosm: bool = False,
        hlm: bool = False,
        spotm: bool = False):
    """
    Run function. Merges sessions into query or map for devices given.

    Args:
        None
    Output:
        None
    """

    if iosq:
        map_or_query = "query"
        device = "ios"
        sessions_ios_q = process_map_or_query(device, capture, map_or_query)
    if hlq:
        map_or_query = "query"
        device = "hl"
        sessions_hl_q = process_map_or_query(device, capture, map_or_query)
    if spotq:
        map_or_query = "query"
        device = "spot"
        sessions_spot_q = process_map_or_query(device, capture, map_or_query)
    if iosm:
        map_or_query = "map"
        device = "ios"
        sessions_ios_m = process_map_or_query(device, capture, map_or_query)
    if hlm:
        map_or_query = "map"
        device = "hl"
        sessions_hl_m = process_map_or_query(device, capture, map_or_query)
    if spotm:
        map_or_query = "map"
        device = "spot"
        sessions_spot_m = process_map_or_query(device, capture, map_or_query)

    if spotm and spotq and iosm and iosq and hlm and hlq:
        print("TODO: radio transfer, maybe")
        #run_radio_transfer.run(capture, [map_id, query_id_phone, query_id_hololens])
    
if __name__ == "__main__":

    parser = argparse.ArgumentParser(description="Merges sesions into query and map of at least one of ios, hl, or spot. Or any combination of them.")
    parser.add_argument('--capture_path', type=Path, required=True, help="Where the capture is located with the merged txt files")
    parser.add_argument("--iosq", action="store_true", help="Enable iOS query map merge")
    parser.add_argument("--hlq", action="store_true", help="Enable HL query map merge")
    parser.add_argument("--spotq", action="store_true", help="Enable Spot query map merge")
    parser.add_argument("--iosm", action="store_true", help="Enable iOS map map merge")
    parser.add_argument("--hlm", action="store_true", help="Enable HL map map merge")
    parser.add_argument("--spotm", action="store_true", help="Enable Spot map map merge")
    
    args = parser.parse_args()
    
    # Ensure at least one argument is provided
    if not (args.iosq or args.hlq or args.spotq or args.iosm or args.hlm or args.spotm):
        parser.error("At least one of --iosq, --hlq, --spotq, --iosm, --hlm, --spotm must be specified.")

    capture = Capture.load(args.capture_path)

    run(**args)
    