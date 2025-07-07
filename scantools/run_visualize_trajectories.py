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
        ios: bool = False,
        hl: bool = False,
        spot: bool = False
    ):
    """
    Main function. Visualizes all trajectories of a given device and location.
    """
    devices = []
    if ios:
        devices.append("ios")
    if hl:
        devices.append("hl")
    if spot:
        devices.append("spot")

    capture_path = capture.path
    clean_path = str(capture_path).rstrip('/')
    location = os.path.basename(clean_path)
    base_path = os.path.dirname(clean_path)

    for device in devices:
        logger.info(f"Visualizing trajectories for device: {device}")

        if device == "hl":
            suffix = "hololens"
        elif device == "spot":
            suffix = "spot"
        elif device == "ios":
            suffix = "phone"
            
        # read all trajectories
        session_ids = read_sequence_list(base_path / Path(location + "_" + suffix + ".txt"))

        logger.info("Processing all files ...")
        trajectories = []
        for session_id in session_ids:
            session_id = device + "_" + session_id
            logger.info(f"  Reading: {session_id}")
            # get trajectory poses
            trajectory = extract_pose_data(capture, session_id)
            trajectories.append(trajectory)
            logger.info(f"  Done reading: {session_id}")
        logger.info("Done processing.")
        
        # visualize poses
        save_path = capture.viz_path() / Path('trajectories') / Path(f"trajectories_{device}.png")
        visualize_trajectories(trajectories=trajectories, save_path=save_path)

        logger.info(f"Visualized trajectories for device {device}.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Given prefix plots individual sessions together.")
    parser.add_argument("--capture_path", type=Path, help="Capture path of the location to visualize trajectories.")
    parser.add_argument("--ios", action="store_true", help="Enable ios trajectory visual")
    parser.add_argument("--hl", action="store_true", help="Enable hl trajectory visual")
    parser.add_argument("--spot", action="store_true", help="Enable spot trajectory visual")

    args = parser.parse_args().__dict__
    
    if args['ios'] is False and args['spot'] is False and args['hl'] is False:
        parser.error("At least one of --ios, --hl, or --spot is required.")

    args['capture'] = Capture.load(args.pop('capture_path'))

    run(**args)
