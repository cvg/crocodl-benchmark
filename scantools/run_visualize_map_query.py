import argparse
from pathlib import Path
from scantools import logger
from scantools.capture import Capture
from scantools.viz.map_query import (
    visualize_map_query
)

from scantools.utils.trajectory_pose_extraction import (
    read_map_query_trajectories
)

def run(
        capture: Capture,
        ios: bool = False,
        hl: bool = False,
        spot: bool = False
    ) -> None:
    """
    Main function. Visualizes query of map for devices given.

    Args:
        capture: Capture -> Capture object containing the session path
        ios: bool -> Enable ios trajectory visual
        hl: bool -> Enable hl trajectory visual
        spot: bool -> Enable spot trajectory visual
    Output:
        None
    """
    devices = []

    if ios:
        devices.append("ios")
    if hl:
        devices.append("hl")
    if spot:
        devices.append("spot")

    for device in devices:
        logger.info(f"Visualizing map query for device: {device}")

        map_query_trajectories = read_map_query_trajectories(capture, device)
        trajectories = []
        trajectories.append(map_query_trajectories['map'])
        trajectories.append(map_query_trajectories['query'])

        save_path = capture.viz_path() / Path('map_query') / Path(f"map_query_{device}.png")
        visualize_map_query(trajectories=trajectories, save_path=save_path)

        logger.info(f"Map query visualization for {device} done.")
    
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Given prefix plots individual sessions together.")
    parser.add_argument("--capture_path", type=Path, help="Capture path of the location to visualize map query.")
    parser.add_argument("--ios", action="store_true", help="Enable ios trajectory visual")
    parser.add_argument("--hl", action="store_true", help="Enable hl trajectory visual")
    parser.add_argument("--spot", action="store_true", help="Enable spot trajectory visual")

    args = parser.parse_args().__dict__
    
    if args['ios'] is False and args['spot'] is False and args['hl'] is False:
        parser.error("At least one of --ios, --hl, or --spot is required.")

    args['capture'] = Capture.load(args.pop('capture_path'))

    run(**args)
