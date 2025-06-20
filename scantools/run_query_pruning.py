from pathlib import Path
import open3d as o3d

from typing import List, Dict

from . import logger
import numpy as np
import matplotlib.pyplot as plt
from itertools import compress

from .capture import Session, Capture
from .capture.session import Device

from .proc.alignment.image_matching import (get_pairwise_distances,
                                            MatchingConf, 
    )

from scantools import (
    run_sequence_aligner
)

conf_matcher = {'output': 'matches-superglue',
                'model': {'name': 'superglue', 'weights': 'outdoor', 'sinkhorn_iterations': 5}}

conf_matching = MatchingConf('netvlad', 'superpoint_aachen', conf_matcher)

conf_align = {
    'ios': run_sequence_aligner.Conf.from_dict(dict(
        **run_sequence_aligner.conf_ios, matching=conf_matching.to_dict())),
    'hl': run_sequence_aligner.Conf.from_dict(dict(
        **run_sequence_aligner.conf_hololens, matching=conf_matching.to_dict())),
    'spot': run_sequence_aligner.Conf.from_dict(dict(
        **run_sequence_aligner.conf_spot, matching=conf_matching.to_dict())),
}

conf_pruning = {
    'distance': 2.5,  # meters
    'voxel_size': 1.0,  # meters
    'keep_per_voxel': 5,  # number of keyframes to keep per voxel
}

def save_configs(filename: Path):
    with open(filename, 'w') as f:
        f.write("# Configuration for query pruning\n")
        f.write(f"Distance threshold: {conf_pruning['distance']} m\n")
        f.write(f"Voxel size: {conf_pruning['voxel_size']} m\n")
        f.write(f"Keyframes to keep per voxel: {conf_pruning['keep_per_voxel']}\n")
        f.write("\n# Device configurations:\n")
        for device, conf in conf_align.items():
            f.write(f"{device}:\n{conf.to_dict()}\n")

    logger.info(f'Configuration saved to: {filename}')

def save_keyframes(session: Dict, filename: Path):

    with open(filename, 'w') as f:
        f.write("# timestamp sensor_id\n")
        for ts, sensor_id in session['keys']:
            f.write(f'{ts} {sensor_id}\n')

    return

def check_distance_between_sesions(query: Dict, ref: Dict):
    T_q2w = [query['session'].proc.alignment_trajectories[ts, sensor_id] for ts, sensor_id in query['keys']]
    T_r2w = [ref['session'].proc.alignment_trajectories[ts, sensor_id] for ts, sensor_id in ref['keys']]
    dR, dt = get_pairwise_distances(T_q2w, T_r2w)
    distance_mask = np.any(~(dt > conf_pruning['distance']), axis=0)
    return distance_mask

def visualize_all(query_data: List[Dict], filename: Path):
    fig = plt.figure(figsize=(12, 8))
    ax = fig.add_subplot(111, projection='3d')

    if not query_data:
        logger.warning("No query data available for visualization.")
        return

    for session_dict in query_data:
        session_id = session_dict['session_id']
        aligned_trajectory = [
            session_dict['session'].proc.alignment_trajectories[ts, sensor_id]
            for ts, sensor_id in session_dict['keys']
        ]
        aligned_poses = np.stack([T.t for T in aligned_trajectory]).astype(np.float32)

        ax.scatter(aligned_poses[:, 0], aligned_poses[:, 1], aligned_poses[:, 2], label=session_id, s=10, alpha=0.6)

    ax.set_title('Aligned 3D Trajectories (Top View)')
    ax.set_xlabel('X')
    ax.set_ylabel('Y')
    ax.set_zlabel('Z')

    ax.view_init(elev=90, azim=-90)

    ax.legend()
    plt.tight_layout()
    plt.savefig(filename, dpi=300)
    plt.close()

    logger.info(f'Visualization for all queries saved to: {filename}')

def visualize_comparison(poses: np.array, poses_pruned: np.array, filename: Path):
    fig = plt.figure(figsize=(12, 8))

    # Original trajectory subplot
    ax1 = fig.add_subplot(1, 2, 1, projection='3d')
    ax1.scatter(poses[:, 0], poses[:, 1], poses[:, 2], c='blue', alpha=0.5, s=10)
    ax1.view_init(elev=90, azim=-90)
    ax1.set_title('Original Trajectory')
    ax1.set_xlabel('X')
    ax1.set_ylabel('Y')
    ax1.set_zlabel('Z')
    ax1.grid(True)

    # Pruned trajectory subplot
    ax2 = fig.add_subplot(1, 2, 2, projection='3d')
    ax2.scatter(poses_pruned[:, 0], poses_pruned[:, 1], poses_pruned[:, 2], c='red', s=10)
    ax2.view_init(elev=90, azim=-90)
    ax2.set_title('Pruned Trajectory')
    ax2.set_ylabel('Y')
    ax2.set_zlabel('Z')
    ax2.grid(True)

    plt.tight_layout()
    plt.savefig(filename, dpi=300)
    plt.close()

def extract_keyframes(session: Session,
                      conf: MatchingConf):

    skip_cameras = set(conf.skip_cameras)
    skip_cameras = {i for i in session.sensors
                    if any(i.endswith(skip_camera) for skip_camera in skip_cameras)}

    keys = [
        (ts, sensor_id) for ts, sensor_id in session.trajectories.key_pairs()
        if sensor_id not in skip_cameras]
    
    return keys

def sample_query_trajectory(poses: np.ndarray):

    subsample_mask = np.ones(len(poses), dtype=bool)
    pose_pcd = o3d.geometry.PointCloud()
    pose_pcd.points = o3d.utility.Vector3dVector(poses)

    voxel_size = conf_pruning['voxel_size']
    min_bound = np.min(np.asarray(pose_pcd.points), axis=0).reshape(3, 1)
    max_bound = np.max(np.asarray(pose_pcd.points), axis=0).reshape(3, 1)

    _, indices_matrix, _ = pose_pcd.voxel_down_sample_and_trace(
        voxel_size, min_bound, max_bound, approximate_class=False
    )

    keep_per_voxel = conf_pruning['keep_per_voxel']
    subsample_mask[:] = False
    for indices in indices_matrix:
        indices = indices[indices != -1]
        if len(indices) <= keep_per_voxel:
            selected_indices = indices
        else:
            selected_positions = np.linspace(0, len(indices) - 1, keep_per_voxel, dtype=int)
            selected_indices = [indices[i] for i in selected_positions]

        for idx in selected_indices:
            subsample_mask[idx] = True

    return subsample_mask

def prune_cross_query(capture: Capture, sessions_data: List[Dict]):
    
    session_data_pruned = []
    logger.info(f"Working on pruning keyframes cross queries. Distance: {conf_pruning['distance']}m. Found {len(sessions_data)} sessions in total.")

    for session_dict_r in sessions_data:

        session_id = session_dict_r['session_id']
        aligned_trajectory = [session_dict_r['session'].proc.alignment_trajectories[ts, sensor_id] for ts, sensor_id in session_dict_r['keys']]
        aligned_poses = np.stack([T.t for T in aligned_trajectory]).astype(np.float32)

        logger.info(f'  Pruning cross queries for session: {session_id}.')

        #mask_within_threshold = np.zeros(len(session_dict_r['keys']), dtype=bool)
        mask_within_threshold = np.ones(len(session_dict_r['keys']), dtype=bool)
        
        for session_dict_q in sessions_data:

            if session_dict_r['device'] == session_dict_q['device']:
                continue

            if session_dict_r['session_id'] == session_dict_q['session_id']:
                continue

            mask_within_threshold_new = check_distance_between_sesions(
                query=session_dict_q, 
                ref=session_dict_r) 

            #mask_within_threshold = mask_within_threshold | mask_within_threshold_new
            mask_within_threshold = mask_within_threshold & mask_within_threshold_new   

        keys_pruned = [k for k, keep in zip(session_dict_r['keys'], mask_within_threshold) if keep]

        poses_pruned = aligned_poses[mask_within_threshold]

        query_session_pruned = {
            'session': session_dict_r['session'],
            'device': session_dict_r['device'],
            'session_id': session_dict_r['session_id'],
            'keys': keys_pruned 
            }
        
        session_data_pruned.append(query_session_pruned)
        
        logger.info(f'      Saved {len(poses_pruned)} out of {len(aligned_poses)} keyframes for: {session_id}.')
        
        filename_vis = capture.session_path(session_id) / 'proc' / 'visualisation_query_pruning.png'
        visualize_comparison(poses=aligned_poses, poses_pruned=poses_pruned, filename=filename_vis)
        logger.info(f'      Visualization saved to: {filename_vis}')

        filename_keys = capture.session_path(session_id) / 'proc' / 'keyframed_pruned.txt'
        save_keyframes(session=query_session_pruned, filename=filename_keys)
        logger.info(f'      Saved keyframes to: {filename_keys}')

    return session_data_pruned

def subsample_queries(capture: Capture, sessions_data: List[Dict]):

    session_data_subsampled = []
    logger.info(f"Working on subsampling pruned keyframes. Using voxel filter with voxel size: {conf_pruning['voxel_size']} and keeping: {conf_pruning['keep_per_voxel']} points.")

    for session_dict in sessions_data:

        session_id = session_dict['session_id']
        
        aligned_trajectory = [session_dict['session'].proc.alignment_trajectories[ts, sensor_id] for ts, sensor_id in session_dict['keys']]
        aligned_poses = np.stack([T.t for T in aligned_trajectory]).astype(np.float32)
        
        logger.info(f'  Subsampling pruned poses for session: {session_id}.')
        subsample_mask = sample_query_trajectory(poses=aligned_poses)

        keys_subsampled = [k for k, keep in zip(session_dict['keys'], subsample_mask) if keep]

        poses_subsampled = aligned_poses[subsample_mask]

        query_session_subsampled = {
            'session': session_dict['session'],
            'device': session_dict['device'],
            'session_id': session_dict['session_id'],
            'keys': keys_subsampled
            }

        session_data_subsampled.append(query_session_subsampled)
        
        logger.info(f'      Saved {len(keys_subsampled)} out of {len(aligned_poses)} keyframes for: {session_id}.')

        filename = capture.session_path(session_id) / 'proc' / 'visualisation_query_subsampling.png'
        visualize_comparison(poses=aligned_poses, poses_pruned=poses_subsampled, filename=filename)
        logger.info(f'      Visualization saved to: {filename}')

        filename_keys = capture.session_path(session_id) / 'proc' / 'keyframes_pruned_subsampled.txt'
        save_keyframes(session=query_session_subsampled, filename=filename_keys)
        logger.info(f'      Saved keyframes to: {filename_keys}')
    
    return session_data_subsampled

def process_queries(capture: Capture):

    query_data = []

    logger.info("Working on loading all device queries.")

    for session_id in capture.sessions.keys():

        if 'query' not in session_id:
            continue

        logger.info(f'  Loading keyframes for: {session_id}.')

        session = capture.sessions[session_id]
        device = session.device

        if device == Device.PHONE:
            conf = conf_align['ios']
        elif device == Device.HOLOLENS:
            conf = conf_align['hl']
        elif device == Device.SPOT:
            conf = conf_align['spot']
        elif device == Device.NAVVIS:
            logger.warning(f'Device is NAVVVIS for session: {session_id}. Skipping.')
            continue
        elif device == Device.UNDEFINED:
            logger.warning(f'Device is UNDEFINED for session: {session_id}. Skipping.')
            continue

        keys = extract_keyframes(session=session, conf=conf.matching)

        query_session = {
            'session': capture.sessions[session_id],
            'device': device,
            'session_id': session_id,
            'keys': keys
            }

        query_data.append(query_session)
        
        filename_keys = capture.session_path(session_id) / 'proc' / 'keyframes_original.txt'
        save_keyframes(session=query_session, filename=filename_keys)
        logger.info(f'      Saved keyframes to: {filename_keys}')
        logger.info(f'      Loaded {len(keys)} keyframes for: {session_id}.')

    return query_data

def run(capture: Capture):
    
    save_configs(filename=capture.path / 'sessions' / 'query_pruning_config.txt')
    query_data = process_queries(capture=capture)
    visualize_all(query_data=query_data, filename=capture.path / 'sessions' / 'visualisation_query_original_all.png')
    query_data_pruned = prune_cross_query(capture=capture, sessions_data=query_data)
    visualize_all(query_data=query_data_pruned, filename=capture.path / 'sessions' / 'visualisation_query_pruning_all.png')
    query_data_subsampled = subsample_queries(capture=capture, sessions_data=query_data_pruned)
    visualize_all(query_data=query_data_subsampled, filename=capture.path / 'sessions' / 'visualisation_query_subsampling_all.png')

    return query_data_subsampled

if __name__ == '__main__':
    print("TODO")