from typing import Dict, Optional, Tuple
import numpy as np
from scipy.spatial.transform import Rotation as R


def pose_to_matrix(pose):
    q = np.asarray(pose['quaternion'], dtype=float)
    t = np.asarray(pose['position'], dtype=float)
    # Convert [qw, qx, qy, qz] to [qx, qy, qz, qw] for scipy
    quat_xyzw = np.array([q[1], q[2], q[3], q[0]], dtype=float)
    R_mat = R.from_quat(quat_xyzw).as_matrix()
    T = np.eye(4, dtype=float)
    T[:3, :3] = R_mat
    T[:3, 3] = t
    return T

def matrix_to_pose(T: np.ndarray):
    if T.shape != (4, 4):
        raise ValueError("Transformation matrix must be 4x4")
    R_mat = T[:3, :3]
    t = T[:3, 3]
    quat_xyzw = R.from_matrix(R_mat).as_quat()
    # Convert back to [qw, qx, qy, qz]
    quat_wxyz = np.array([quat_xyzw[3], quat_xyzw[0], quat_xyzw[1], quat_xyzw[2]])
    return quat_wxyz, t

def invert_pose(pose):
    T = pose_to_matrix(pose)
    T_inv = np.linalg.inv(T)
    qwxyz, t = matrix_to_pose(T_inv)
    return {
        'device_id': pose.get('device_id', None),
        'position': t,
        'quaternion': qwxyz,
        'timestamp': pose.get('timestamp', None)
    }

def transform_pose(pose, transform):
    T_cam_world = pose_to_matrix(pose)
    T_new_cam = transform @ T_cam_world
    qwxyz, t = matrix_to_pose(T_new_cam)
    return {
        'device_id': pose.get('device_id', None),
        'position': t,
        'quaternion': qwxyz,
        'timestamp': pose.get('timestamp', None)
    }

def convert_gt_to_anchor_frame(gt_poses, anchor_pose):
    if not gt_poses:
        return {}
    # Precompute the inverse of the anchor's transformation matrix: T_anchor<=world
    T_anchor = pose_to_matrix(anchor_pose)
    T_anchor_inv = np.linalg.inv(T_anchor)
    rel_poses = {}
    for ts, pose in gt_poses.items():
        rel_poses[ts] = transform_pose(pose, T_anchor_inv)
    return rel_poses

def convert_pred_to_anchor_frame(pred_poses, anchor_pred_pose=None):
    if not pred_poses:
        return {}
    # If no anchor predicted pose is given, assume poses are already relative
    if anchor_pred_pose is None:
        return {ts: pose.copy() for ts, pose in pred_poses.items()}
    # Compute inverse of anchor predicted pose
    T_anchor_pred = pose_to_matrix(anchor_pred_pose)
    T_anchor_pred_inv = np.linalg.inv(T_anchor_pred)
    rel_pred = {}
    for ts, pose in pred_poses.items():
        rel_pred[ts] = transform_pose(pose, T_anchor_pred_inv)
    return rel_pred

def select_anchor(map_poses, anchor_timestamp=None):
    if not map_poses:
        raise ValueError("map_poses must not be empty")
    if anchor_timestamp is None:
        anchor_timestamp = min(map_poses.keys())
    if anchor_timestamp not in map_poses:
        raise ValueError(f"Anchor timestamp {anchor_timestamp} not found in map poses")
    return map_poses[anchor_timestamp].copy()
