import os
import argparse
from pathlib import Path
from scantools.capture import Capture
from scantools import logger
from scantools.viz.trajectories import (
    visualize_trajectories
)

from scantools.utils.io import (
    read_sequence_list
)
from scantools.utils.trajectory_pose_extraction import (
    extract_pose_data
)

def run(
        capture: Capture,
        device: str,
    ):
    """
    Main function. Visualizes all trajectories of a given device and location.

    Args:
        capture: Capture -> Capture object containing the session path
        device: str -> Device prefix to visualize (choose: ios, hl, spot)
    Output:
        None
    """

    capture_path = capture.path
    clean_path = capture_path.rstrip('/')
    location = os.path.basename(clean_path)
    base_bath = os.path.dirname(clean_path)
    session_ids = read_sequence_list(base_bath / Path(location + "_" + device + ".txt"))

    logger.info("Processing all files ...")
    trajectories = []
    for session_id in session_ids:
        logger.info(f"  Reading: {session_id}")
        trajectory = extract_pose_data(capture, session_id)
        trajectories.append(trajectory)
        logger.info(f"    Done reading: {session_id}")
    logger.info("Done processing.")

    save_path = capture.viz_path() / f"{device}_trajectories.png"
    visualize_trajectories(trajectories=trajectories, save_path=save_path)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Given prefix plots individual sessions together.")
    parser.add_argument("--capture_path", type=Path, help="Capture path of the location to visualize trajectories.")
    parser.add_argument("--device", choices=["ios", "hl", "spot"], type=str, 
                        help="Prefix of the device which is visualized (choose: ios, hl, spot).")

    args = parser.parse_args()
    args['capture'] = Capture.load(args.pop('capture_path'))

    run(**args)
