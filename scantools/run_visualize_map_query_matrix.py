import argparse
from pathlib import Path
from scantools.capture import Capture

from scantools.run_visualize_map_query import (
    read_map_query_trajectories
)

from scantools.viz.map_query import (
    visualize_map_query_matrix
)

def run(
        capture: Capture,
        ios: bool = False,
        hl: bool = False,
        spot: bool = False,
    ):
    """
    Main function. Visualizes query and map of at least two of ios, hl, or spot. Or any combination of them.
    This function reads the trajectories for the specified devices and visualizes them in a matrix format.
    It requires at least two devices to be specified (ios, hl, spot).
    """

    devices = []
    filename = "matrix"
    if ios:
        devices.append("ios")
        filename += "_ios"
    if hl:
        devices.append("hl")
        filename += "_hl"
    if spot:
        devices.append("spot")
        filename += "_spot"

    filename += ".png"
    trajectories = []

    for device in devices:
        # read and combine all trajectories into map/query trajectory
        map_query_trajectories = read_map_query_trajectories(capture, device)
        trajectories.append(map_query_trajectories['map'])
        trajectories.append(map_query_trajectories['query'])

    print("Visualizing split ...")
    visualize_map_query_matrix(trajectories, capture.viz_path() / Path('map_query') / Path(filename))
    print("Visualizing ended.")
    
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Visualizes query and map of at least one of ios, hl, or spot. Or any combination of them.")
    parser.add_argument("--capture_path", type=Path, help="Capture path of the location to visualize matrix.")
    parser.add_argument("--ios", action="store_true", help="Enable iOS visual")
    parser.add_argument("--hl", action="store_true", help="Enable HL visual")
    parser.add_argument("--spot", action="store_true", help="Enable Spot visual")
    
    args = parser.parse_args()
    
    enabled = sum([args.ios, args.hl, args.spot])

    if enabled < 2:
        parser.error("At least two of --ios, --hl, or --spot must be specified.")

    if args.ios is False and args.hl is False and args.spot is False:
        parser.error("At least one of --ios, --hl, or --spot is required.")

    args = parser.parse_args().__dict__
    args['capture'] = Capture.load(args.pop('capture_path'))

    run(**args)
