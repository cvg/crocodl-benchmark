import os
import shutil
import argparse
import numpy as np
from pathlib import Path
from scipy.spatial.transform import Rotation as R
from scantools.capture import Capture
from .capture.session import Device
from scantools.viz.map_query import (
    visualize_map_query_rotation,
)
from scantools import (
    run_combine_sequences, 
    )

from . import logger
from scantools.utils.utils import (
    read_csv, 
    write_csv
)
from scantools.utils.io import (
    read_sequence_list
)

from scantools.run_query_pruning import (
    save_keyframes,
    extract_keyframes,
    conf_align
)

from pipelines.pipeline_sequence import *

eval_keyframing = run_combine_sequences.KeyFramingConf()
map_keyframing = run_combine_sequences.KeyFramingConf(max_distance=0.5, max_elapsed=0.4)

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

def read_random_transform_csv(transform_path):
    """
    Reads a transform from a transform_path file.
    """
    transform, col_transform = read_csv(transform_path)
    q = [float(i) for i in transform[0][1:5]]
    t = [float(i) for i in transform[0][5:]]
    T = quaternion_and_translation_to_matrix(q, t)
    return q.extend(t), T

def rotate_trajectories(
        capture: Capture, 
        map_id: str,
        just_vis: bool = False
    ) -> None:
    """
    Rotate trajectories for a given map_id by applying a random transformation.
    Args:
        capture: Capture object containing the session data.
        map_id: Identifier for the map to process.
        just_vis: Only get visuals.
    Output:
        None
    """

    map_path = capture.session_path(map_id)
    
    trajectories, col_trajectories = read_csv(map_path / 'trajectories.txt')
    col_transform = ['map_id', 'qw', 'qx', 'qy', 'qz', 'tx', 'ty', 'tz']

    trajectories_out = []
    translation_new = []
    translation_orig = []
    translation_restored = []

    if just_vis:
        transform_path = map_path / 'transforms.txt'
        logger.info(f"Reading transform from {transform_path}.")
        transform, translation_matrix = read_random_transform_csv(map_path / 'transforms.txt')
    else:
        logger.info(f"Generating new 4DOF transform.")
        transform, translation_matrix = generate_random_transform_4DOF()
        write_csv(map_path / 'transforms.txt', [[map_id] + [str(x) for x in transform]], col_transform)
    
    translation_matrix_inv = np.linalg.inv(translation_matrix)

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
    
    visualize_map_query_rotation(translation_orig, translation_new, translation_restored, capture.viz_path(), map_id)

    if not just_vis:
        write_csv(map_path / 'trajectories_augumented.txt', trajectories_out, col_trajectories)

    logger.info(f"Augumented trajectories for {map_id} and saved to {map_path / 'trajectories_augumented.txt'}.")

def process_map_or_query(
        device: str = "",
        capture: Capture = None,
        map_or_query: str = "",
        transform: bool = False,
        just_vis: bool = False
    ) -> None:
    """
    Process map or query for file_path given.
    """

    sessions_id = []
    capture_path = capture.path
    file_path = capture_path / f"{device}_{map_or_query}.txt"
    sessions_id = read_sequence_list(file_path)

    output_id = device + "_" + map_or_query
    logger.info(f"Merging {map_or_query} for {device} from file {file_path} into folder {output_id}.")
    logger.info("Sessions to merge: \n    " + "\n    ".join(sessions_id))

    if not just_vis:
        if map_or_query == "map":
            overwrite_poses = True
            keyframing_conf = map_keyframing
            capture_path = capture.path
            clean_path = str(capture_path).rstrip('/')
            base_path = Path(os.path.dirname(clean_path))
            location = os.path.basename(clean_path)
            ref_id, _, _, _ = eval('get_data_' + location)(base_path)

        elif map_or_query == "query":                    
            overwrite_poses = False
            keyframing_conf = eval_keyframing
            ref_id = None

        combined_session_path = capture.sessions_path() / output_id

        if os.path.exists(combined_session_path) and os.path.isdir(combined_session_path):
            shutil.rmtree(combined_session_path)
            logger.info(f"Combined session {combined_session_path} already exists, Deleting.")
        
        run_combine_sequences.run(
                capture, 
                sessions_id, 
                output_id, 
                overwrite_poses=overwrite_poses, 
                reference_id=ref_id,
                keyframing=keyframing_conf)
        
        if map_or_query == "query":

            session = capture.sessions[output_id]
            device = session.device

            if device == Device.PHONE:
                conf = conf_align['ios']
            elif device == Device.HOLOLENS:
                conf = conf_align['hl']
            elif device == Device.SPOT:
                conf = conf_align['spot']

            keys = extract_keyframes(session=session, conf=conf.matching)

            query_session = {
                'session': session,
                'device': device,
                'session_id': output_id,
                'keys': keys
                }
            
            filename_keys = capture.session_path(output_id) / 'proc' / 'keyframes_original.txt'
            save_keyframes(session=query_session, filename=filename_keys)
            logger.info(f'Saved keyframes to: {filename_keys}')

            
    if transform and map_or_query == "map":
        rotate_trajectories(capture, output_id, just_vis)


    logger.info(f"Done merging {map_or_query} for {device}.\n")

    return sessions_id

def run(capture: Capture,
        iosq: bool = False,
        hlq: bool = False,
        spotq: bool = False,
        iosm: bool = False,
        hlm: bool = False,
        spotm: bool = False,
        transform: bool = False,
        just_vis: bool = False):
    """
    Run function. Merges sessions into query or map for devices given.
    """

    if iosq:
        map_or_query = "query"
        device = "ios"
        sessions_ios_q = process_map_or_query(device, capture, map_or_query, transform, just_vis)
    if hlq:
        map_or_query = "query"
        device = "hl"
        sessions_hl_q = process_map_or_query(device, capture, map_or_query, transform, just_vis)
    if spotq:
        map_or_query = "query"
        device = "spot"
        sessions_spot_q = process_map_or_query(device, capture, map_or_query, transform, just_vis)
    if iosm:
        map_or_query = "map"
        device = "ios"
        sessions_ios_m = process_map_or_query(device, capture, map_or_query, transform, just_vis)
    if hlm:
        map_or_query = "map"
        device = "hl"
        sessions_hl_m = process_map_or_query(device, capture, map_or_query, transform, just_vis)
    if spotm:
        map_or_query = "map"
        device = "spot"
        sessions_spot_m = process_map_or_query(device, capture, map_or_query, transform, just_vis)

if __name__ == "__main__":

    parser = argparse.ArgumentParser(description="Merges sesions into query and map of at least one of ios, hl, or spot. Or any combination of them.")
    parser.add_argument('--capture_path', type=Path, required=True, help="Where the capture is located with the merged txt files")
    parser.add_argument("--iosq", action="store_true", help="Enable iOS query map merge")
    parser.add_argument("--hlq", action="store_true", help="Enable HL query map merge")
    parser.add_argument("--spotq", action="store_true", help="Enable Spot query map merge")
    parser.add_argument("--iosm", action="store_true", help="Enable iOS map map merge")
    parser.add_argument("--hlm", action="store_true", help="Enable HL map map merge")
    parser.add_argument("--spotm", action="store_true", help="Enable Spot map map merge")
    parser.add_argument("--transform", action="store_true", help="Enable transformation of trajectories for map", default=False)
    parser.add_argument("--just_vis", action="store_true", help="Do not overwrite anything, just display visuals.", default=False)
    
    args = parser.parse_args()
    
    # Ensure at least one argument is provided
    if not (args.iosq or args.hlq or args.spotq or args.iosm or args.hlm or args.spotm):
        parser.error("At least one of --iosq, --hlq, --spotq, --iosm, --hlm, --spotm must be specified.")

    args = parser.parse_args().__dict__
    args['capture'] = Capture.load(args.pop('capture_path'))
    run(**args)
    