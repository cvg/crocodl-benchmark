import numpy as np
from . import logger
import matplotlib.pyplot as plt
from pathlib import Path
from typing import List, Dict

def set_axes_equal(ax):
    """
    Set 3D plot axes to have equal scale.
    This function adjusts the limits of the x, y, and z axes of a 3D plot so that they have the same scale.
    Args:
        ax: The 3D plot axes to adjust.
    Returns:
        Set 3D plot axes to have equal scale.
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
    Visualize the original, transformed, and restored trajectories in 3D space.
    This function creates 3D scatter plots to visualize the original trajectory, the transformed trajectory,
    and the restored trajectory after applying an inverse transformation. It saves the visualizations to the specified path.
    Args:
        translation_orig: List of original trajectory translations.
        translation_new: List of transformed trajectory translations.
        translation_restored: List of restored trajectory translations after inverse transformation.
        visualization_path: Path to save the visualizations.
        map_id: Identifier for the map being visualized.
    Returns:
        None
    """

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

def visualize_all(
        query_data: List[Dict], 
        filename: Path
        ) -> None:
    """
    Visualize all query data in a 3D scatter plot.
    Args:
        query_data: List of dictionaries containing session data with keys 'session_id', 'session', and 'keys'.
        filename: Path to save the visualization image.
    Returns:
        None
    """
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

def visualize_comparison(
        poses: np.array, 
        poses_pruned: np.array, 
        filename: Path
        ) -> None:
    """
    Visualize the original and pruned trajectories in a 3D scatter plot.
    Args:
        poses: Original trajectory poses as a numpy array of shape (N, 3).
        poses_pruned: Pruned trajectory poses as a numpy array of shape (M, 3).
        filename: Path to save the visualization image.
    Returns:
        None
    """
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