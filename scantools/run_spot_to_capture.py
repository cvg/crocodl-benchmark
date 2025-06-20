import argparse
import logging
from pathlib import Path
from datetime import datetime
from scantools import (
    run_rosbag_to_capture_session,
    run_correct_extrinsics,
    run_rotate_images,
    run_interpolate_rigs,
    run_create_queries,
    run_zero_trajectories,
)

"""
Do-it-all script; extracts bagfiles, corrects extrinsics (when necessary),
rotates images, interpolates rigs, and create queries file
"""

def run(input_path : Path, 
        output_path : Path, 
        overwrite : bool, 
        all_cameras : bool):
    
    if not input_path.is_dir():
        raise IOError(f"Input folder {input_path} does not exist")
    elif not output_path.is_dir():
        raise IOError(f"Output folder {output_path} does not exist")

    additional_transforms = """# parent frame, child frame, qw , qx, qy, qz, tx, ty, tz
                            body, temp_base_link, 1, 0, 0, 0, 0, 0, 0
                            body, base_link, 1, 0, 0, 0, 0, 0, 0
                            spot/body, body, 1, 0, 0, 0, 0, 0, 0"""
    
    additional_transforms_path = output_path / "transforms.txt"
    if additional_transforms_path.is_file():
        Path.unlink(additional_transforms_path)
    with open(additional_transforms_path, "w") as additional_transforms_file:
        additional_transforms_file.writelines(additional_transforms)
    
    if not all_cameras:
        skip_topics = [
        "/rgb/image_rect_color",
        "/rgb/camera_info",
        "/spot/camera/back/camera_info",
        "/spot/camera/back/image",
        "/zed2i/zed_node/left/camera_info", 
        "/zed2i/zed_node/left/image_rect_color", 
        "/zed2i/zed_node/right/camera_info", 
        "/zed2i/zed_node/right/image_rect_color", 
        #"/zed2i/zed_node/depth/depth_registered", 
        #"/zed2i/zed_node/depth/camera_info", 
        ]

    bag_paths = list(input_path.glob("*.bag"))

    for bag_path in bag_paths:
        # GLOBAL ARGUMENTS

        # rosbag_to_capture_converter
        all_rectified = True
        rig_frame = "body" # Hydrology is missing Kinect, so using Spot body frame
        spot_vision_from_tf = True
        imu = "/imu"
        odometry = "/spot/odometry"
        additional_transforms_path = output_path / "transforms.txt"

        # correct_extrinsics
        extrinsics=False
        pickle_sensor = None
        pickle_rig = None

        # rotate_images
        sensors_angles = {'spot-camera-frontleft-image' : 90,
                          'spot-camera-frontright-image' : 90,
                          'spot-camera-right-image' : 180}
        
        # interpolate_rigs
        delete_unused=False
        keep_unused_odometry=False
        fast_selecting=True
        skip_sanitation=True

        logging.info("=========================================")
        logging.info(f"Processing bag {bag_path}")
        bag_name = bag_path.parts[-1].rstrip('.bag')
        scene = bag_name[17:]
        bag_date = datetime.strptime(bag_name[:16], "%Y-%m-%d-%H-%M")
        # Not strictly necessary; the additional transforms will not hurt,
        # since older bags do not have the ZED installed, and therefore no
        # namespace collisions.
        # Mainly here as "documentation in the code"
        if bag_date < datetime.strptime("2023-06-06-08-11", "%Y-%m-%d-%H-%M"):
            additional_transforms_path = None
        if scene in {"DLAB", "CAB"}:
            scene = "CAB"
            if bag_date > datetime.strptime("2023-07-01-00-00", "%Y-%m-%d-%H-%M"):
                if bag_date < datetime.strptime("2023-07-25-12-00", "%Y-%m-%d-%H-%M"):
                    logging.info(f"Session has desync between Orin and NUC, skipping")
                    continue
                extrinsics=True
                pickle_sensor=Path(__file__).parent / "correct_extrinsics_sensor_to_rig_arche.pickle"
        elif scene in {"HG", "HGE"}:
            scene = "HGE"
            if bag_date > datetime.strptime("2023-07-01-00-00", "%Y-%m-%d-%H-%M"):
                extrinsics=True
                pickle_sensor=Path(__file__).parent / "correct_extrinsics_sensor_to_rig_arche.pickle"
        elif scene == "LIN":
            logging.info(f"Session has desync between Orin and NUC, skipping")
            continue
        elif "ARCHE" in scene:
            extrinsics=True
            pickle_sensor=Path(__file__).parent / "correct_extrinsics_sensor_to_rig_arche.pickle"
        elif scene == "HYDRO":
            # Kinect didn't record, must use ZED imu instead
            imu = "/zed2i/zed_node/imu/data"
        elif scene == "DESIGN":
            extrinsics=True
            pickle_sensor=Path(__file__).parent / "correct_extrinsics_sensor_to_rig_succulent.pickle"
        elif scene == "SUCCULENT":
            extrinsics=True
            pickle_sensor=Path(__file__).parent / "correct_extrinsics_sensor_to_rig_succulent.pickle"
        else:
            raise ValueError(f"Unhandled scene {scene}")
        if (output_path / bag_name[:16]).is_dir() and overwrite == False:
            logging.info("Capture folder for bag exists and overwrite is False, skipping")
            continue

        session_path = run_rosbag_to_capture_session.run(bag_path=bag_path,
                                      capture_path=output_path,
                                      scene=scene,
                                      rig_frame=rig_frame,
                                      all_rectified=all_rectified,
                                      additional_transforms_path=additional_transforms_path,
                                      odometry=odometry,
                                      imu=imu,
                                      overwrite=overwrite,
                                      skip_topics=skip_topics,
                                      spot_vision_from_tf=spot_vision_from_tf)
        
        logging.info("Rosbag to capture: done!")

        if extrinsics:
            run_correct_extrinsics.run(session_path=session_path,
                                   pickle_sensor=pickle_sensor,
                                   pickle_rig=pickle_rig)
            
        run_rotate_images.run(session_path=session_path,
                          sensors_angles=sensors_angles)
        
        run_interpolate_rigs.run(session_path=session_path,
                             delete_unused=delete_unused,
                             keep_unused_odometry=keep_unused_odometry,
                             fast_selecting=fast_selecting,
                             skip_sanitation=skip_sanitation)
        
        run_create_queries.run(session_path=session_path,
                               overwrite=overwrite)
        
        run_zero_trajectories.run(session_path / "trajectories.txt")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--input_path", type=Path, required=True, help="Path of folder containing bagfiles.")
    parser.add_argument("--output_path", type=Path, required=True, help="Path of folder to place Capture sessions.")
    parser.add_argument("--overwrite", action="store_true", default=False, help="Overwrite existing processed bagfiles.")
    parser.add_argument("--all_cameras", action="store_true", default=False, help="Use all 8 Spot cameras for rigs.")
    #logging.getLogger().setLevel(logging.INFO)

    args = parser.parse_args().__dict__
    run(**args)
