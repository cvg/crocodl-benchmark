import os
import matplotlib.pyplot as plt
from scantools import logger


def visualize_trajectories(
        trajectories: dict = None,
        save_path: str = None
        ):
    """
    Visualizes the trajectories of all files. 
    Args:   
        trajectories: dict -> Dictionary containing the session name, rotation (quaternions) and translation (xyz) of the device
        save_path: str -> Path to save the figure (optional). If None, the figure will be displayed but not saved.
    Output:
        None
    """ 
    fig = plt.figure()
    ax = fig.add_subplot(111, projection='3d')

    for trajectory in trajectories:
        translations = trajectory["translation"]
        ax.plot(translations[:, 0], translations[:, 1], translations[:, 2], label=trajectory["session"])

    ax.set_xlabel('X')
    ax.set_ylabel('Y')
    ax.set_zlabel('Z')

    ax.view_init(elev=60, azim=-60)

    if save_path is not None:
        # Save without legend
        filename = os.path.splitext(os.path.basename(save_path))[0]
        ax.set_title(filename)
        directory = os.path.dirname(save_path)
        if directory and not os.path.exists(directory):
            os.makedirs(directory, exist_ok=True)
        plt.savefig(save_path, bbox_inches='tight', dpi=300)
        logger.info(f"Figure saved to {save_path} (without legend)")
    else:
        logger.info("No save path provided, displaying the figure instead.")

    return 0
