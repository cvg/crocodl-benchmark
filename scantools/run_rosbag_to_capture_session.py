from typing import List
import shutil
from pathlib import Path
from datetime import datetime
import argparse
import logging
import shutil
from tqdm import tqdm
import numpy as np
import matplotlib.pyplot as plt
import cv2
from pytransform3d.transformations import transform_from_pq, pq_from_transform, invert_transform, concat
from pytransform3d.transform_manager import TransformManager
from pytransform3d.plot_utils import make_3d_axis
from cv_bridge import CvBridge
import rosbag
from scantools.utils.utils import read_csv


"""
Example command to run:
python rosbag_to_capture_session.py --bag ~/bagfiles/spot_and_kinect.bag --scene CAB --captures ~/repo/lamar-benchmark/data --rig body
"""

"""
TODO:
- Allow multiple odometry/imu sources in Capture output? Check if Capture supports
- Put proper imu data in sensors.txt instead of placeholder (once LaMAR supports them)
- Add flag to check if depth images are 32FC1 and warn user in case passthrough isn't working like they wanted
- Turn if statements into if-else, since some don't need to be checked if others are true
- Allow renaming rostopics to more descriptive/less generic ones: https://stackoverflow.com/questions/29986185/python-argparse-dict-arg
- Handle rigs.txt
    - Allow more than a single rig
- Handle pointclouds.txt
- Handle depths.txt
- Handle wifi.txt
- Handle bt.txt
"""

"""
STRONG ASSUMPTIONs:

Cameras:
- A single image topic is attached to each CameraInfo topic instead
of the typical max of 5.
(see: https://docs.ros.org/en/noetic/api/sensor_msgs/html/msg/CameraInfo.html)
- CameraInfo and Image pairs have the same topic names minus the ending
 (so /spot/left/image_rect and /spot/left/camera_info, not /spot/blabla/camera_info)
- CameraInfo topics contain the string 'info' in their name
- Depth camera topics contains the string 'depth' in their name
- 32FC1 or 64FC1 depth images are represented in meters, while XUC1 are represented
 in millimeters

Odometry:
- nav_msgs/Odometry poses are specified with odometry frame as parent frame, and
 child frame is part of the "robot" (and so the transform between the child frame
 and the rig is constant/static)

Rigs:
- All sensor_msgs/* messages have a std_msgs/Header message which contains a frame_id
- Single rig is used
"""

SENSORS = 'sensors.txt'
IMAGES = 'images.txt'
DEPTHS = 'depths.txt'
TRAJECTORIES = 'trajectories.txt'
WIFI = 'wifi.txt'
RIGS = 'rigs.txt'
IMU = 'imu.txt'
DEBUG_TRANSFORMS = 'debug_transforms.txt'
DEBUG_RIGS = 'debug_rig.txt'
DEBUG_FOLDER = 'debug'
SPOT_VISION_FROM_TF = 'spot_vision.txt'

class FrameTransform:
    """
    Contains the transformation of the child frame into the parent frame
    pos_quat is concatenation of position and quaternion
    quaternion must be of form [w, x, y, z]
    """
    def __init__(self, parent='parent', child='child', pos_quat=np.array([0, 0, 0, 0, 0, 0, 0])):
        self.parent = parent
        self.child = child
        self.pos_quat = pos_quat


def visualize_transforms(session_path : Path, rig : str, frame_transforms : List[FrameTransform]):
    """
    Visualize a set of transforms relative to the rig

    :param Path session_path: absolute or relative path to session folder
    :param str rig: ROS frame_id of the rig
    :param List frame_transforms: list of static transforms between frame_ids
    """
    tm = TransformManager(strict_check=True)
    for tf in frame_transforms:
        transformation_matrix = transform_from_pq(tf.pos_quat)
        tm.add_transform(tf.child,
                         tf.parent,
                         transformation_matrix)
    ax = make_3d_axis(0.5, 111)
    ax = tm.plot_frames_in(rig, ax=ax, show_name=True, s=0.1)
    ax.view_init(45, 45)
    plt.savefig(session_path / DEBUG_FOLDER / 'sensor_frames.png', dpi=600)


def transform_to_rig(rig : str, frame_transforms : List[FrameTransform]):
    """
    TransformManager finds transformations between all frames and the
    rig frame.
    TransformManager gives the transform of the first frame with respect
    to the second (this is the opposite order as tf_echo).

    :param str rig: ROS frame_id of the rig
    :param List frame_transforms: list of static transforms between frame_ids
    :return: list containing only transforms from sensors' frame_id to rig
    """
    tm = TransformManager(strict_check=True)
    for ft in frame_transforms:
        transformation_matrix = transform_from_pq(ft.pos_quat)
        tm.add_transform(ft.child,
                         ft.parent,
                         transformation_matrix)
    # add transformed frames back
    transforms_relative_to_rig = []
    transformed_frames = []
    for ft in frame_transforms:
        if ft.child not in transformed_frames:
            transformed_frames.append(ft.child)
            try:
                pos_quat = pq_from_transform(tm.get_transform(ft.child, rig))
                transforms_relative_to_rig.append(FrameTransform(parent=rig, child=ft.child, pos_quat=pos_quat))
            except Exception as e:
                logging.debug(f'Frame {ft.child} could not be transformed to rig: {e}')
                pass
        if ft.parent not in transformed_frames:
            transformed_frames.append(ft.parent)
            try:
                pos_quat = pq_from_transform(tm.get_transform(ft.parent, rig))
                transforms_relative_to_rig.append(FrameTransform(parent=rig, child=ft.parent, pos_quat=pos_quat))
            except Exception as e:
                logging.debug(f'Frame {ft.parent} could not be transformed to rig: {e}')
                pass
    return transforms_relative_to_rig


def format_topic_title(rostopic : str):
    """
    Formats rostopic names into a more friendly format

    :param str rostopic: unformatted rostopic name
    :return: formatted rostopic name
    """
    rostopic = rostopic.replace('/', '-')
    if rostopic[0] == '-':
        return rostopic[1:]
    else:
        return rostopic


def rosbag_to_capture(session_path : Path,
                      bag : rosbag,
                      rig_frame : str,
                      all_rectified : bool,
                      additional_transforms_path : Path,
                      rostopic_info : dict,
                      imu_rostopic : str,
                      odom_rostopic : str,
                      spot_vision_from_tf : bool):

    # An image can only be added to images.txt once its distortion model/intrinsic parameters have
    # been found. Since these are stored in a sensor_msgs/CameraInfo message, and the order of
    # arrival for these messages is non-deterministic, there are early frames which can't be
    # processed; these are thrown away.
    # In practice, this amounts to a single frame or two.
    lost_frames = 0
    total_frames = 0

    # Odometry messages are a special case. On one hand, they don't belong
    # in rigs.txt, since their transformation relative to the rig changes
    # as the robot moves.
    # On the other hand, we want to express the rig in the world /odometry frame,
    # and so need the transform between the odometry message child frame and the
    # rig.
    # We therefore need to save odometry messages until after tranformations
    # between frames are found, then transform to express the rig relative to
    # the odometry frame.
    # By default, nav_msgs/Odometry expresses odometry transforms in the odometry
    # frame (so the child frame is on the robot somewhere, and the odometry frame
    # is static in the world frame).
    odom_child = None
    odom_child_to_rig = None
    odom_buffer = []

    # Store messages that arrive too soon but can't be thrown out to be played at the end of the rosbag.
    # For example, static transforms defined in tf2_msgs/TFMessage messages can't be associated with sensors
    # if no sensor_msgs/CameraInfo or equivalent message for that sensor has been read yet.
    msg_buffer = []

    # Spot-specific, designed for extracting vision-based odometry from
    # /tf rostopic
    # vision frame can either be the parent or the child, depending
    # on whether KO or VKO was selected in Spot ROS wrapper
    vision_parent = None
    vision_child = None
    vision_parent_to_rig = None
    vision_child_to_rig = None
    vision_buffer = []

    # contains key:value pairs between frame_id and corresponding sensor(s)
    frame_to_rostopic = {}

    sensors = open(session_path / SENSORS, 'a')
    images = open(session_path / IMAGES, 'a')
    depths = open(session_path / DEPTHS, 'a')
    trajectories = open(session_path / TRAJECTORIES, 'a')
    rigs = open(session_path / RIGS, 'a')
    debug_transforms = open(session_path / DEBUG_FOLDER / DEBUG_TRANSFORMS, 'a')
    debug_rig = open(session_path / DEBUG_FOLDER / DEBUG_RIGS, 'a')
    wifi = open(session_path / WIFI, 'a')
    imu = open(session_path / IMU, 'a')
    if spot_vision_from_tf:
        vision = open(session_path / SPOT_VISION_FROM_TF, 'a')
    bridge = CvBridge()

    logging.info('Reading rosbag')
    for rostopic, msg, t in tqdm(bag.read_messages(), total=bag.get_message_count()):

        # Use timestamp given by node processing the sensor, not the timestamp given by rosbag
        if "/tf" in rostopic and msg.transforms:
            # /tf and /tf_static
            timestamp = str(int(msg.transforms[0].header.stamp.to_nsec() // 1000))
        elif msg._has_header:
            timestamp = str(int(msg.header.stamp.to_nsec() // 1000))
        else:
            # catch-all for messages that don't have a header
            logging.debug(f"Rostopic {rostopic} doesn't have a header, using rosbag timestamp")
            print(t)
            timestamp = str(int(str(t)) // 1000)

        if rostopic not in rostopic_info:
            # skip this topic
            logging.debug(f"Skipping msg for rostopic {rostopic} ")
            continue

        if rostopic_info[rostopic]['msg_type'] == 'sensor_msgs/Image':
            total_frames += 1
            # String will be empty if corresponding sensor_msgs/CameraInfo not yet read
            if rostopic_info[rostopic]['model_params'] != '':
                sensor_id = rostopic_info[rostopic]['formatted_name']
                timestamped_id = timestamp + '-' + sensor_id
                if 'depth' in sensor_id:
                    sensor_type = 'depth'
                else:
                    sensor_type = 'camera'
                sensor_params = rostopic_info[rostopic]['model'] + ', '+ rostopic_info[rostopic]['model_params']
                # path relative to raw_data folder
                image_path = rostopic_info[rostopic]['formatted_name'] + '/' + timestamped_id + '.png'
                # One entry in sensors.txt per sensor
                if rostopic_info[rostopic]['sensor_initialized'] == False:
                    sensors.write(f"{sensor_id}, {sensor_id}, {sensor_type}, {sensor_params}\n")
                    rostopic_info[rostopic]['sensor_initialized'] = True
                absolute_image_path = session_path / 'raw_data' / rostopic_info[rostopic]['formatted_name'] / (timestamped_id + '.png')
                if 'depth' in sensor_id:
                    depths.write(f"{timestamp}, {sensor_id}, {image_path}\n")
                    # Saving images like they do in LaMAR:
                    # # https://github.com/microsoft/lamar-benchmark/blob/cb5042cb14f640493b1f9331ea80f2b939d20cad/scantools/utils/io.py#L61
                    # imwrite() works with 16-bit uint png files
                    # https://docs.opencv.org/3.4/d4/da8/group__imgcodecs.html#gabbc7ef1aa2edfaa87772f1202d67e0ce
                    dtype = np.uint16
                    cv_image = bridge.imgmsg_to_cv2(msg, desired_encoding='passthrough')
                    if cv_image.dtype == np.float32:
                        # 32FC1 is meters, uint16 is millimeters
                        cv_image = cv_image * 1000.0
                        mask = (cv_image > np.iinfo(dtype).max) | (cv_image < 0)
                        cv_image[mask] = 0
                        # Not using PIL because it's almost 10x as slow to save
                        #PIL.Image.fromarray(cv_image.round().astype(dtype)).save(str(absolute_image_path))
                        # dtype conversion must be explicit, otherwise output image will be wrong
                        cv2.imwrite(str(absolute_image_path), cv_image.round().astype(dtype))
                    else:
                        cv2.imwrite(str(absolute_image_path), cv_image.astype(dtype))
                else:
                    images.write(f"{timestamp}, {sensor_id}, {image_path}\n")
                    cv_image = bridge.imgmsg_to_cv2(msg, desired_encoding='passthrough')
                    # PIL uses RGB, OpenCV uses BGR:
                    # https://stackoverflow.com/questions/43232813/convert-opencv-image-format-to-pil-image-format
                    #PIL.Image.fromarray(cv2.cvtColor(cv_image, cv2.COLOR_RGB2BGR)).save(str(absolute_image_path))
                    cv2.imwrite(str(absolute_image_path), cv_image)
            else:
                # Throw out image
                lost_frames += 1

        if rostopic_info[rostopic]['msg_type'] == 'sensor_msgs/CameraInfo':
            # ROS uses three distortion models; plumb_bob (5 elements), rational_polynomial (8 elements), and equidistant/fisheyes
            # http://wiki.ros.org/camera_calibration
            # COLMAP indicates that OpenCV's full distortion model takes 8
            # https://github.com/colmap/colmap/blob/78c12b4ccd6751099e93a914cbd0611370e2acff/src/base/camera_models.h#L278
            # Must add empty parameters fill model_params
            model_params = [msg.width, msg.height, msg.K[0], msg.K[4], msg.K[2], msg.K[5]]
            if all_rectified:
                model = 'PINHOLE'
            else:
                model = 'FULL_OPENCV'
                model_params.extend(list(msg.D))
                if msg.distortion_model == 'plumb_bob':
                    model_params.extend([0.0, 0.0, 0.0])
                elif msg.distortion_model != 'rational_polynomial':
                    # equidistant doesn't seem to be supported by Capture
                    logging.error('Unsupported distortion model')
                    exit(1)
            # Set model and model parameters in Image topic
            rostopic_info[rostopic_info[rostopic]['camera_topic']]['model'] = model
            rostopic_info[rostopic_info[rostopic]['camera_topic']]['model_params'] = str(model_params)[1:-1] # [a, b, c] -> a, b, c

        if (rostopic_info[rostopic]['msg_type'] == 'nav_msgs/Odometry' and
            rostopic == odom_rostopic):
            # odom message express the position/orientation of the child frame
            # in the odometry frame
            odom_child = msg.child_frame_id
            odom_buffer.append(msg)

        if spot_vision_from_tf and rostopic == '/tf':
            for transform in msg.transforms:
                if transform.child_frame_id == 'vision':
                    vision_parent = transform.header.frame_id
                    vision_buffer.append(transform)
                elif transform.header.frame_id == 'vision':
                    vision_child = transform.child_frame_id
                    vision_buffer.append(transform)

        # Associate frame_ids to sensor rostopics
        if 'sensor_msgs' in rostopic_info[rostopic]['msg_type'] and 'info' not in rostopic:
            if msg.header.frame_id not in frame_to_rostopic:
                frame_to_rostopic[msg.header.frame_id] = []
            if rostopic not in frame_to_rostopic[msg.header.frame_id]:
                frame_to_rostopic[msg.header.frame_id].append(rostopic)

        if rostopic == '/tf_static':
                # save until rosbag finished and all sensors are paired with a frame_id
                for transform in msg.transforms:
                    msg_buffer.append((rostopic, transform, t))

        if (rostopic_info[rostopic]['msg_type'] == 'sensor_msgs/Imu' and
            rostopic == imu_rostopic):
            sensor_id = rostopic_info[rostopic]['formatted_name']
            orientation = msg.orientation
            orientation_covariance = str(msg.orientation_covariance)[1:-1] # [a, b, c] -> a, b, c
            angular_velocity = msg.angular_velocity
            angular_velocity_covariance = str(msg.angular_velocity_covariance)[1:-1]
            linear_acceleration = msg.linear_acceleration
            linear_acceleration_covariance = str(msg.linear_acceleration_covariance)[1:-1]
            imu.write(f'{timestamp}, {sensor_id}'
                      f', {orientation.x}, {orientation.y}, {orientation.z}, {orientation.w}'
                      f', {orientation_covariance}'
                      f', {angular_velocity.x}, {angular_velocity.y}, {angular_velocity.z}'
                      f', {angular_velocity_covariance}'
                      f', {linear_acceleration.x}, {linear_acceleration.y}, {linear_acceleration.z}'
                      f', {linear_acceleration_covariance}\n')
            # One entry in sensors.txt per sensor
            # TODO: update imu sensors.txt IMU content once LaMAR updated to support them
            if rostopic_info[rostopic]['sensor_initialized'] == False:
                sensors.write(f"{sensor_id}, {sensor_id}, IMU, 0\n")
                rostopic_info[rostopic]['sensor_initialized'] = True

    # Load additional transformations from file if specified
    additional_transforms = None
    if additional_transforms_path != None:
        if additional_transforms_path.exists():
            logging.info('Loading additional transforms')
            additional_transforms, _ = read_csv(additional_transforms_path)
            logging.info('Loaded additional transforms')
        else:
            raise IOError(f'File containing additional transforms doesn\'t exist: {additional_transforms_path}')
    # Iterate through static transforms (published to /tf_static topic)
    # and add to rig.txt
    # Transforms express the child frame in the parent frame
    logging.info('Parsing static transforms')
    frame_transforms = []
    if additional_transforms != None:
        for transform in additional_transforms:
            pos = [float(i) for i in transform[6:]]
            quat = [float(i) for i in transform[2:6]]
            frame_transforms.append(FrameTransform(parent=transform[0],
                                                   child=transform[1],
                                                   pos_quat=np.array([pos[0], pos[1], pos[2], quat[0], quat[1], quat[2], quat[3]])))
    for _, msg, _ in msg_buffer:
        rig_device_id = msg.header.frame_id
        pos = msg.transform.translation # [x, y, z] format position
        quat = msg.transform.rotation # [x, y, z, w] format quaternion
        # Transform containing a frame_id paired with a sensor
        if msg.child_frame_id in frame_to_rostopic:
            for rostopic in frame_to_rostopic[msg.child_frame_id]:
                sensor_id = rostopic_info[rostopic]['formatted_name']
                frame_transforms.append(FrameTransform(parent=msg.header.frame_id,
                                            child=msg.child_frame_id,
                                            pos_quat=np.array([pos.x, pos.y, pos.z, quat.w, quat.x, quat.y, quat.z])))
                debug_transforms.write(f'{rig_device_id}, {sensor_id}, {quat.w}, {quat.x}, {quat.y}, {quat.z}, {pos.x}, {pos.y}, {pos.z}\n')
        # Transform between frame_ids, neither of which is paired with a sensor
        else:
            # TODO: it's not a sensor, but the field in the rigs file is called sensor_id; compromise?
            sensor_id = msg.child_frame_id
            frame_transforms.append(FrameTransform(parent=msg.header.frame_id,
                                            child=msg.child_frame_id,
                                            pos_quat=np.array([pos.x, pos.y, pos.z, quat.w, quat.x, quat.y, quat.z])))
            debug_transforms.write(f'{rig_device_id}, {sensor_id}, {quat.w}, {quat.x}, {quat.y}, {quat.z}, {pos.x}, {pos.y}, {pos.z}\n')

    # Filter out only transforms which correspond to sensors, with the rig as their parent
    logging.info('Writing out static transforms to rigs.txt')
    transforms_relative_to_rig = transform_to_rig(rig_frame, frame_transforms)
    sensor_transforms = []
    for tf in transforms_relative_to_rig:
        # write out all transforms relative to rig for debugging
        debug_rig.write(f'{tf.parent}, {tf.child}, {tf.pos_quat[3]}, {tf.pos_quat[4]}, {tf.pos_quat[5]}, {tf.pos_quat[6]}, {tf.pos_quat[0]}, {tf.pos_quat[1]}, {tf.pos_quat[2]}\n')
        for rostopic in rostopic_info:
            if tf.child in frame_to_rostopic and rostopic in frame_to_rostopic[tf.child]:
                sensor_transforms.append(tf)
                sensor_id = rostopic_info[rostopic]['formatted_name']
                rigs.write(f'{tf.parent}, {sensor_id}, {tf.pos_quat[3]}, {tf.pos_quat[4]}, {tf.pos_quat[5]}, {tf.pos_quat[6]}, {tf.pos_quat[0]}, {tf.pos_quat[1]}, {tf.pos_quat[2]}\n')
        if odom_child != None and tf.child == odom_child:
            # found odometry child frame relative to the rig frame
            odom_child_to_rig = tf
        if vision_parent != None and tf.child == vision_parent:
            # found vision parent frame relative to the rig frame
            vision_parent_to_rig = tf
        elif vision_child != None and tf.child == vision_child:
            vision_child_to_rig = tf

    # Transform all odometry messages to express the position of the rig in the
    # odometry frame, instead of the odometry child in the odometry frame.
    # (translation of [1, 0, 0] means rig frame is 1m in away from odometry frame
    # in direction of positive x axis of odometry frame). This can be verified by
    # playing the rosbag and running `rosrun tf tf_echo odom_frame rig_frame` where
    # odom_frame is the name of the frame of odometry and rig_frame is the name
    # of the frame of the rig.
    logging.info('Writing odometry messages to trajectories.txt')
    if odom_rostopic != None and odom_child_to_rig != None and odom_child != None and len(odom_buffer) != 0:
        for msg in odom_buffer:
            timestamp = str(int(msg.header.stamp.to_nsec() // 1000))
            # Kapture examples puts the actual device id (ie. spot_odometry) as
            # the device_id, while Capture examples put the rig frame as the
            # device_id; we'll follow the Kapture example, since it makes it more
            # clear, if there are multiple odometry sources, which lines belong
            # to which (despite this script not supporting multiple odometry
            # sources).
            # Handle rig
            device_id = odom_child_to_rig.parent
            pos = msg.pose.pose.position # [x, y, z] format position
            quat = msg.pose.pose.orientation # [x, y, z, w] format quaternion
            covariance = str(msg.pose.covariance)[1:-1] # [a, b, c] -> a, b, c
            pos_quat=np.array([pos.x, pos.y, pos.z, quat.w, quat.x, quat.y, quat.z])
            odom_child_to_odom = transform_from_pq(pos_quat)
            rig_to_odom = concat(invert_transform(transform_from_pq(odom_child_to_rig.pos_quat)), odom_child_to_odom)
            pos_quat = pq_from_transform(rig_to_odom) # [x, y, z, qw, qx, qy, qz]
            if sum(msg.pose.covariance) == 0.0:
                trajectories.write(f'{timestamp}, {device_id}, {pos_quat[3]}, {pos_quat[4]}, {pos_quat[5]}, {pos_quat[6]}, {pos_quat[0]}, {pos_quat[1]}, {pos_quat[2]}\n')
            else:
                trajectories.write(f'{timestamp}, {device_id}, {pos_quat[3]}, {pos_quat[4]}, {pos_quat[5]}, {pos_quat[6]}, {pos_quat[0]}, {pos_quat[1]}, {pos_quat[2]}, {covariance}\n')
    else:
        logging.info("Either no odometry data, or insufficient info to include (such as there being no transformation between odometry frames and the rig frame, which can be fixed with the use of --transform and manually specifying the missing transformation)")

    if spot_vision_from_tf and len(vision_buffer) != 0 and (
        (vision_child != None and vision_child_to_rig != None) or
        (vision_parent != None and vision_parent_to_rig != None)
    ):
        logging.info('Writing Spot vision odometry to spot_vision.txt')
        for msg in vision_buffer:
            timestamp = str(int(msg.header.stamp.to_nsec() // 1000))
            pos = msg.transform.translation # [x, y, z] format position
            quat = msg.transform.rotation # [x, y, z, w] format quaternion
            pos_quat=np.array([pos.x, pos.y, pos.z, quat.w, quat.x, quat.y, quat.z])
            if vision_child != None:
                device_id = vision_child_to_rig.parent
                vision_child_to_vision = transform_from_pq(pos_quat)
                rig_to_vision = concat(invert_transform(transform_from_pq(vision_child_to_rig.pos_quat)), vision_child_to_vision)
                pos_quat = pq_from_transform(rig_to_vision) # [x, y, z, qw, qx, qy, qz]
            else:
                device_id = vision_parent_to_rig.parent
                vision_to_vision_parent = transform_from_pq(pos_quat)
                rig_to_vision = concat(invert_transform(transform_from_pq(vision_parent_to_rig.pos_quat)), invert_transform(vision_to_vision_parent))
                pos_quat = pq_from_transform(rig_to_vision) # [x, y, z, qw, qx, qy, qz]
            vision.write(f'{timestamp}, {device_id}, {pos_quat[3]}, {pos_quat[4]}, {pos_quat[5]}, {pos_quat[6]}, {pos_quat[0]}, {pos_quat[1]}, {pos_quat[2]}\n')


    # Can be used to verify the validity of the transformations
    # alongside comparing the transformations in rigs.txt with the output
    # of `rosrun tf tf_echo rig_frame_id sensor_frame_id`
    visualize_transforms(session_path, rig_frame, sensor_transforms)

    logging.info(f'Total frames in session: {total_frames}')
    logging.info(f'Lost frames due to sensor_msgs/CameraInfo arriving after sensor_msgs/Image: {lost_frames}')

    sensors.close()
    images.close()
    depths.close()
    trajectories.close()
    rigs.close()
    debug_transforms.close()
    wifi.close()
    imu.close()
    if spot_vision_from_tf:
        vision.close()
        logging.info("Backing up trajectories.txt to spot_odom.txt")
        shutil.copy(session_path / TRAJECTORIES,
                    session_path / "spot_odom.txt")
        logging.info("Putting spot vision odometry in trajectories.txt")
        shutil.copy(session_path / SPOT_VISION_FROM_TF,
                    session_path / TRAJECTORIES)


def run(bag_path : Path,
        capture_path : Path,
        scene : str,
        rig_frame : str,
        all_rectified : bool,
        additional_transforms_path : Path,
        odometry : str,
        imu : str,
        overwrite : bool = False,
        skip_topics = [],
        spot_vision_from_tf = False
        ):
    
    if not Path(capture_path).is_dir():
        logging.error(f"Capture path {capture_path} does not exist")
        exit(code=1)

    logging.info("Loading rosbag, this may take some time")
    bag = rosbag.Bag(bag_path)
    logging.info("Loaded rosbag")

    sessions_path = capture_path
    if not Path(sessions_path).is_dir():
        logging.info(f'No sessions for scene {scene} detected, created sessions folder')
        Path(sessions_path).mkdir(parents=True, exist_ok=True)

    bag_name = bag_path.parts[-1].rstrip('.bag')
    bag_date = bag_name[:16] # "%Y-%m-%d-%H-%M" 2023-01-22-17-55, etc.
    sessions_path = sessions_path / "sessions"
    session_path = sessions_path / Path('spot_' + bag_date)
    if Path(session_path).is_dir():
        if overwrite:
            shutil.rmtree(session_path)
            logging.info('Identically named session found, overwrite is True, erased old session')
        else:
            logging.info('Identically named session found, overwrite is False, shutting down')
            exit(0)
    Path(session_path).mkdir(parents=True, exist_ok=True)
    logging.info(f'Creating session for scene {scene} called {bag_date}')

    # Folder for debugging information
    debug_path = session_path / 'debug'
    Path(debug_path).mkdir(parents=True, exist_ok=True)

    # Set up .txt files
    f = open(session_path / SENSORS, 'w')
    f.write("# sensor_id, name, sensor_type, [sensor_params]+\n")
    f.close()
    f = open(session_path / IMAGES, 'w')
    f.write("# timestamp, sensor_id, image_path\n")
    f.close()
    f = open(session_path / DEPTHS, 'w')
    f.write("# timestamp, sensor_id, depth_map_path\n")
    f.close()
    f = open(session_path / TRAJECTORIES, 'w')
    f.write("# timestamp, device_id, qw, qx, qy, qz, tx, ty, tz, *covar\n")
    f.close()
    f = open(session_path / RIGS, 'w')
    f.write("# rig_device_id, sensor_device_id, qw, qx, qy, qz, tx, ty, tz\n")
    f.close()
    f = open(session_path / DEBUG_FOLDER / DEBUG_TRANSFORMS, 'w')
    f.write("# parent frame, child frame, qw, qx, qy, qz, tx, ty, tz\n")
    f.close()
    f = open(session_path / DEBUG_FOLDER / DEBUG_RIGS, 'w')
    f.write("# parent frame, child frame, qw, qx, qy, qz, tx, ty, tz\n")
    f.close()
    f = open(session_path / WIFI, 'w')
    f.write("# timestamp, sensor_id, mac_addr, frequency_khz, rssi_dbm, name, scan_time_start_us, scan_time_end_us\n")
    f.close()
    f = open(session_path / IMU, 'w')
    f.write("# timestamp, sensor_id, orientation (x y z w), orientation_covariance (9 floats), angular_velocity (x y z), angular_velocity_covariance (9 floats), linear_acceleration (x y z), linear_acceleration_covariance (9 floats)\n")
    f.close()
    if spot_vision_from_tf:
        f = open(session_path / SPOT_VISION_FROM_TF, 'w')
        f.write("# timestamp, device_id, qw, qx, qy, qz, tx, ty, tz, *covar\n")
        f.close()

    # rostopic_info contains info pertaining to each rostopic.
    # Necessary for images, since the image and model are stored in sensor_msgs/Image
    # but the distortion model and camera instrinsics are stored in sensor_msgs/CameraInfo
    rostopic_info = {}
    for rostopic, rostopic_data in bag.get_type_and_topic_info()[1].items():
        if rostopic in skip_topics:
            logging.warning(f'Skipping rostopic {rostopic} from extraction')
            continue
        rostopic_formatted = format_topic_title(rostopic)
        rosmsg_type = rostopic_data[0]
        rostopic_info[rostopic] = {}
        rostopic_info[rostopic]['formatted_name'] = rostopic_formatted
        rostopic_info[rostopic]['msg_type'] = rosmsg_type
        rostopic_info[rostopic]['sensor_initialized'] = False

    # Find sensor_msgs/Image and sensor_msgs/CameraInfo pairs.
    # Assumes Image-CameraInfo pairs share topic names, minus content after the final '/'
    # For example, /spot/camera/frontleft/image and /spot/camera/frontleft/camera_info
    for rostopic in rostopic_info:
        if rostopic_info[rostopic]['msg_type'] == 'sensor_msgs/Image':
            pair_found = False
            formatted_name = rostopic_info[rostopic]['formatted_name']
            # remove trailing '-image', '-camera_info', etc.
            formatted_name_root = formatted_name[:formatted_name.rindex('-')]
            for rostopic2 in rostopic_info:
                if rostopic_info[rostopic2]['msg_type'] == 'sensor_msgs/CameraInfo':
                    formatted_name2 = rostopic_info[rostopic2]['formatted_name']
                    formatted_name_root2 = formatted_name2[:formatted_name2.rindex('-')]
                    if formatted_name_root == formatted_name_root2:
                        pair_found = True
                        # sensor_msgs/CameraInfo paired with sensor_msgs/Image
                        rostopic_info[rostopic2]['camera_topic'] = rostopic
                        # set default camera model and parameters, to be updated once CameraInfo message is read
                        rostopic_info[rostopic]['model'] = 'FULL_OPENCV'
                        rostopic_info[rostopic]['model_params'] = ''
            if not pair_found:
                logging.error(f'No rostopic of type sensor_msgs/CameraInfo found for rostopic {rostopic} of type sensor_msgs/Image')
                exit(1)

    # Create folders for individual sensors
    Path(session_path / 'raw_data').mkdir(parents=True, exist_ok=True)
    for rostopic, topic_info in rostopic_info.items():
        if rostopic_info[rostopic]['msg_type'] == 'sensor_msgs/Image':
            Path(session_path / 'raw_data' / rostopic_info[rostopic]['formatted_name']).mkdir(parents=True, exist_ok=True)

    # In case of multiple IMU/Odometry sources, must specify one for the Capture session
    odom_rostopic = odometry
    if odom_rostopic != None:
        odom_specified = True
    else:
        odom_specified = False

    imu_rostopic = imu
    if imu_rostopic != None:
        imu_specified = True
    else:
        imu_specified = False

    for rostopic in rostopic_info:
        if rostopic_info[rostopic]['msg_type'] == 'nav_msgs/Odometry':
            if odom_rostopic == None:
                odom_rostopic = rostopic
            if rostopic != odom_rostopic and odom_specified == False:
                logging.error(f'Multiple odometry topics ({rostopic}, {odom_rostopic}), but none specified, please specify one using --odometry')
                exit(1)
        if rostopic_info[rostopic]['msg_type'] == 'sensor_msgs/Imu':
            if imu_rostopic == None:
                imu_rostopic = rostopic
            if rostopic != imu_rostopic and imu_specified == False:
                logging.error(f'Multiple imu topics ({rostopic}, {imu_rostopic}), but none specified, please specify one using --imu')
                exit(1)

    rosbag_to_capture(session_path=session_path,
                      bag=bag,
                      rig_frame=rig_frame,
                      all_rectified=all_rectified,
                      rostopic_info=rostopic_info,
                      imu_rostopic=imu_rostopic,
                      odom_rostopic=odom_rostopic,
                      additional_transforms_path=additional_transforms_path,
                      spot_vision_from_tf=spot_vision_from_tf)

    return session_path


if __name__ == '__main__':
    logging.getLogger().setLevel(logging.INFO)
    parser = argparse.ArgumentParser()
    parser.add_argument('--bag', type=Path, required=True,
                        help="Relative or global path of location and name of bagfile. Ex: ~/bagfiles/nameofbag.bag")
    parser.add_argument('--scene', type=str, required=True,
                        help="Name of scene. Ex: CAB, main_building, etc.")
    parser.add_argument('--captures', type=Path, default='data', required=True,
                        help="Relative or global path to captures directory. Ex: ~/lamar/data for scene folder ~/lamar/data/CAB")
    parser.add_argument('--rig', type=str, required=True,
                        help="frame_id of rig. Ex: body, head, etc.")
    parser.add_argument('--all_rectified', action='store_true', required=False,
                        help="If all cameras are rectified; will set distortion parameters to 0")
    parser.add_argument('--transforms', type=Path, required=False,
                        help='File containing additional transformations in the form parent frame, child frame, qw, qx, qy, qz, tx, ty, tz')
    parser.add_argument('--odometry', type=str, required=False,
                        help='Select odometry topic of multiple are present')
    parser.add_argument('--imu', type=str, required=False,
                        help='Select imu topic of multiple are present')
    parser.add_argument('--overwrite', action='store_true', default=False,
                        help="Overwrite existing session with same scene and starting timestamp")
    parser.add_argument('--spot_vision_from_tf', action='store_true', default=False,
                        help="Extract transformation between body and vision frames from /tf (Spot specific flag)")
    
    args = parser.parse_args()

    run(bag_path=args.bag,
        capture_path=args.captures,
        scene=args.scene,
        rig_frame=args.rig,
        all_rectified=args.all_rectified,
        additional_transforms_path=args.transforms,
        odometry=args.odometry,
        imu=args.imu,
        overwrite=args.overwrite,
        spot_vision_from_tf=args.spot_vision_from_tf)
