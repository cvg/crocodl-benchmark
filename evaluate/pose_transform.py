import numpy as np
from scipy.spatial.transform import Rotation as R


def estimate_rigid_transform(pred_xyz, gt_xyz):
    # Nx3: N x [tx, ty, tz]
    assert pred_xyz.shape == gt_xyz.shape and pred_xyz.shape[1] == 3
    X = gt_xyz.astype(np.float64)   # target
    Y = pred_xyz.astype(np.float64) # source

    mu_X, mu_Y = X.mean(0), Y.mean(0)
    Xc, Yc = X - mu_X, Y - mu_Y
    U, S, Vt = np.linalg.svd(Yc.T @ Xc)
    R_opt = Vt.T @ U.T
    if np.linalg.det(R_opt) < 0:
        Vt[-1, :] *= -1
        R_opt = Vt.T @ U.T
    t_opt = mu_X - R_opt @ mu_Y
    return R_opt, t_opt

def _quat_wxyz_to_matrix(q_wxyz):
    q_xyzw = np.stack([q_wxyz[...,1], q_wxyz[...,2], q_wxyz[...,3], q_wxyz[...,0]], axis=-1)
    return R.from_quat(q_xyzw).as_matrix()

def _matrix_to_quat_wxyz(R_mats):
    q_xyzw = R.from_matrix(R_mats).as_quat()
    return np.stack([q_xyzw[...,3], q_xyzw[...,0], q_xyzw[...,1], q_xyzw[...,2]], axis=-1)

def apply_transform(R_opt, t_opt, poses_pred_arr):
    # poses_pred_arr: (N, 7) = [qw, qx, qy, qz, tx, ty, tz]
    q = poses_pred_arr[:, 0:4]
    t = poses_pred_arr[:, 4:7]

    t_aligned = (R_opt @ t.T).T + t_opt
    R_old = _quat_wxyz_to_matrix(q)
    R_new = R_opt[None, :, :] @ R_old
    q_aligned = _matrix_to_quat_wxyz(R_new)
    q_aligned = q_aligned / np.linalg.norm(q_aligned, axis=1, keepdims=True)
    return q_aligned, t_aligned

def align_pred_to_gt(pred_poses, gt_poses):
    common_ts = sorted(set(pred_poses.keys()) & set(gt_poses.keys()))
    if len(common_ts) < 3:
        raise ValueError("At least 3 point to align.")

    pred_xyz = np.stack([pred_poses[t]['position'] for t in common_ts], axis=0)  # source
    gt_xyz   = np.stack([gt_poses[t]['position']   for t in common_ts], axis=0)  # target

    # 1. Estimate R, t
    R_opt, t_opt = estimate_rigid_transform(pred_xyz, gt_xyz)

    # 2. Transform
    all_ts = sorted(pred_poses.keys())
    poses_pred_arr = np.stack(
        [np.concatenate([pred_poses[t]['quaternion'], pred_poses[t]['position']]) for t in all_ts],
        axis=0
    )  # (N,7)
    q_aligned, t_aligned = apply_transform(R_opt, t_opt, poses_pred_arr)

    # 3. Format
    aligned_poses = {}
    for i, t in enumerate(all_ts):
        aligned_poses[t] = {
            'device_id': pred_poses[t]['device_id'],
            'position': t_aligned[i],
            'quaternion': q_aligned[i],
            'timestamp': t
        }

    return aligned_poses, (R_opt, t_opt)