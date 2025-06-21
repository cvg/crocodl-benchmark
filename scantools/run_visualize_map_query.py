import argparse
from pathlib import Path
from scantools.capture import Capture
from scantools.viz.map_query import (
    visualize_map_query
)

from scantools.utils.trajectory_pose_extraction import (
    read_map_query_trajectories
)

def run(
        capture: Capture,
        device: str
    ) -> None:
    """
    Main function. Visualizes query of map for devices given.

    Args:
        capture: Capture -> Capture object containing the session path
        device: str -> Prefix of the device which is visualized (choose: ios, hl, spot).
    Output:
        None
    """
    
    map_query_trajectories = read_map_query_trajectories(capture, device)
    trajectories = []
    trajectories.append(map_query_trajectories['map'])
    trajectories.append(map_query_trajectories['query'])

    save_path = capture.viz_path() / f"{device}_map_query.png"
    visualize_map_query(trajectories=trajectories, save_path=save_path)
    
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Given prefix plots individual sessions together.")
    parser.add_argument("--capture_path", type=Path, help="Capture path of the location to visualize map query.")
    parser.add_argument("--device", choices=["ios", "hl", "spot"], type=str, 
                        help="Prefix of the device which is visualized (choose: ios, hl, spot).")

    args = parser.parse_args()
    args['capture'] = Capture.load(args.pop('capture_path'))

    run(**args)