from pathlib import Path
import argparse
import shutil
import logging
import cv2
import numpy as np
from tqdm import tqdm
from pytransform3d.transformations import transform_from_pq, pq_from_transform, concat
from scantools.utils.utils import sort_and_prune, read_csv, write_csv
from joblib import Parallel, delayed


"""
Assumes image z axis points into image

TODO: make more generic (what if depth cameras need to be rotated eventually?)

See reference implementation here:
https://github.com/microsoft/lamar-benchmark/blob/e7f575638b4b07077d6ff8dabfed2624fd0159bf/scantools/run_phone_to_capture.py#L65
"""

def run(session_path : Path, sensors_angles : list):
    """
    Rotate images to be upright, update transformations to reflect rotation
    """
    if (not session_path.is_dir() or
        not (session_path / 'images.txt').is_file() or
        not (session_path / 'sensors.txt').is_file() or
        not (session_path / 'trajectories.txt').is_file() or
        not (session_path / 'rigs.txt').is_file()):
        logging.error(f"Could not find images.txt, sensors.txt, trajectories.txt, or rigs.txt")
        exit(1)

    if ((session_path / 'sensors.txt.unrotated').is_file() or
        (session_path / 'trajectories.txt.unrotated').is_file() or
        (session_path / 'rigs.txt.unrotated').is_file()):
        logging.warning(" *.unrotated versions of sensors.txt, trajectories.txt, or rigs.txt has been found, which means that *.txt may already contain the rotated images; continuing to run this script may result in the good backup being replaced with the previous output of this script. To continue, enter 'Y'. Enter anything else to stop this script.")
        user_input = input("Y/n: ")
        if user_input != "Y":
            logging.info("Shutting down...")
            exit(0)

    logging.info('Sorting and pruning duplicate rows in images.txt, depths.txt, imu.txt, and trajectories.txt')
    sort_and_prune(session_path / 'images.txt', overwrite=True)
    sort_and_prune(session_path / 'depths.txt', overwrite=True)
    sort_and_prune(session_path / 'imu.txt', overwrite=True)
    sort_and_prune(session_path / 'trajectories.txt', overwrite=True)
    logging.info('Sorted and pruned')

    shutil.copyfile(session_path / 'sensors.txt', session_path / 'sensors.txt.unrotated')
    shutil.copyfile(session_path / 'trajectories.txt', session_path / 'trajectories.txt.unrotated')
    shutil.copyfile(session_path / 'rigs.txt', session_path / 'rigs.txt.unrotated')

    images, _ = read_csv(session_path / 'images.txt')
    sensors, col_sensors = read_csv(session_path / 'sensors.txt')
    trajectories, col_trajectories = read_csv(session_path / 'trajectories.txt')
    rigs, col_rigs = read_csv(session_path / 'rigs.txt')

    sensors_out = []
    trajectories_out = []
    rigs_out = []

    sensors_transformations = {}
    for s in sensors_angles:
        num_rot90 = sensors_angles[s] // 90
        # Negative, since the rotation is of the new frame around the old
        # camera frame, and therefore the transformation expressing the new
        # new camera frame with respect to the old one is the opposite
        angle = -num_rot90 * (np.pi / 2)
        sensors_transformations[s] = np.array([[np.cos(angle), -np.sin(angle), 0, 0],
            [np.sin(angle), np.cos(angle), 0, 0],
            [0, 0, 1, 0],
            [0, 0, 0, 1]])
        #print(f'{s}:\n{np.round(sensors_transformations[s], 3)}')

    # Handle all images
    # https://stackoverflow.com/a/76726101/11784188
    logging.info('Rotating images')
    list(tqdm(
        Parallel(return_as="generator", n_jobs=-1)(delayed(rotate_image)(session_path, sensors_angles, line) for line in images),
        total=len(images)
    ))

    # Handle sensors.txt
    logging.info('Rotating camera intrinsics')
    for line in sensors:
        sensor_id = line[0]

        current_sensor, found = dict_key_in_string(sensors_angles, sensor_id)
        if not found:
            sensors_out.append(line)
            continue

        camera_model = line[3]
        assert camera_model == 'PINHOLE'

        # width, height, focal length in x and y, optical center in x and y
        w = int(line[4])
        h = int(line[5])
        fx = float(line[6])
        fy = float(line[7])
        cx = float(line[8])
        cy = float(line[9])

        num_rot90 = sensors_angles[current_sensor] // 90
        if num_rot90 == 0:
            pass
        elif num_rot90 == 1:
            cx, cy = h - cy, cx
            fx, fy = fy, fx
            w, h = h, w
        elif num_rot90 == 2:
            cx, cy = w - cx, h - cy
        elif num_rot90 == 3:
            cx, cy = cy, w - cx
            fx, fy = fy, fx
            w, h = h, w
        else:
            raise ValueError
        
        sensors_out.append([str(i) for i in [line[0], line[1], line[2], line[3], w, h, fx, fy, cx, cy]])

    # Handle all rigs
    logging.info('Rotating transformations with respect to rig')
    for line in rigs:
        sensor_id = line[1]

        current_sensor, found = dict_key_in_string(sensors_angles, sensor_id)
        if not found:
            rigs_out.append(line)
            continue

        # qw, qx, qy, qz, tx, ty, tz
        qp = [float(i) for i in line[2:9]]
        # Camera frame expressed in rig frame
        B_to_A = transform_from_pq(qp[4:] + qp[:4])

        # Rotated camera frame expressed in original camera frame
        C_to_B = sensors_transformations[current_sensor]
        transform_rotated = concat(C_to_B, B_to_A)
        pq = pq_from_transform(transform_rotated)

        rigs_out.append([str(i) for i in [line[0], line[1], pq[3], pq[4], pq[5], pq[6], pq[0], pq[1], pq[2]]])

    # Handle all trajectories
    logging.info('Rotating trajectories')
    for line in trajectories:
        sensor_id = line[1]

        current_sensor, found = dict_key_in_string(sensors_angles, sensor_id)
        if not found:
            trajectories_out.append(line)
            continue

        # qw, qx, qy, qz, tx, ty, tz
        qp = [float(i) for i in line[2:9]]
        B_to_A = transform_from_pq(qp[4:] + qp[:4])

        # Rotated camera frame expressed in original camera frame
        C_to_B = sensors_transformations[current_sensor]
        transform_rotated = concat(C_to_B, B_to_A)
        pq = pq_from_transform(transform_rotated)

        trajectories_out.append([str(i) for i in [line[0], line[1], pq[3], pq[4], pq[5], pq[6], pq[0], pq[1], pq[2]]])

        if len(line) > 9:
            # Add covariance terms back
            trajectories_out[-1] += [str(i) for i in line[9:]]

    write_csv(session_path / 'sensors.txt', sensors_out, col_sensors)
    write_csv(session_path / 'trajectories.txt', trajectories_out, col_trajectories)
    write_csv(session_path / 'rigs.txt', rigs_out, col_rigs)


def rotate_image(session_path, sensors_angles, line):
    sensor_id = line[1]

    current_sensor, found = dict_key_in_string(sensors_angles, sensor_id)
    if found:
        image_path_relative = line[2]

        image_path_absolute = session_path / 'raw_data' / image_path_relative
        image = cv2.imread(str(image_path_absolute))

        num_rot90 = sensors_angles[current_sensor] // 90
        image_rotated = np.rot90(m=image, k=num_rot90, axes=(1,0))

        cv2.imwrite(str(image_path_absolute), image_rotated)


def dict_key_in_string(dictionnary : dict, string : str):
    """
    Return true if any key from a dictionnary is found in the target string

    :param dict dictionnary: dict whose keys will be looked for in string
    :param str string: string to look for keys of dict in
    :return: dictionnary key which was found in string (if any), and bool
    """
    current_s = None
    found = False
    for s in dictionnary:
        if s in string:
            current_s = s
            found = True
            break
    return current_s, found


def derotate_images(session_path : Path, sensor_angles : dict):
    if not ((session_path / 'sensors.txt.unrotated').is_file() or
            (session_path / 'trajectories.txt.unrotated').is_file() or
            (session_path / 'rigs.txt.unrotated').is_file()):
        logging.error("Couldn't find *.unrotated files in capture path, nothing to derotate?")

    for f in {'sensors.txt.unrotated', 'trajectories.txt.unrotated', 'rigs.txt.unrotated'}:
        if (session_path / f).is_file():
            shutil.move(session_path / f, session_path / f.rstrip('.unrotated'))

    # inverse rotation angles
    for sensor_id, angle in sensor_angles.items():
        sensor_angles[sensor_id] = -angle

    images, _ = read_csv(session_path / 'images.txt')

    # Handle all images
    logging.info('De-rotating images')
    for line in tqdm(images):
        sensor_id = line[1]

        current_sensor, found = dict_key_in_string(sensors_angles, sensor_id)
        if not found:
            continue

        image_path_relative = line[2]

        image_path_absolute = session_path / 'raw_data' / image_path_relative
        image = cv2.imread(str(image_path_absolute))

        num_rot90 = sensors_angles[current_sensor] // 90
        image_rotated = np.rot90(m=image, k=num_rot90, axes=(1,0))

        cv2.imwrite(str(image_path_absolute), image_rotated)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--session_path', type=Path, required=True,
                        help="Relative or global path of folder containing sensors.txt and rigs.txt. Ex: ~/lamar/data/CAB/01")
    parser.add_argument('--derotate', action='store_true', required=False,
                        help="Rotate images back the other way, restore backups")
    logging.getLogger().setLevel(logging.INFO)

    sensors_angles = {'spot-camera-frontleft-image' : 90,
               'spot-camera-frontright-image' : 90,
               'spot-camera-right-image' : 180}

    for s in sensors_angles:
        if sensors_angles[s] % 90 != 0:
            raise ValueError('Angle must be increment of 90 degrees')

    args = parser.parse_args()
    session_path = args.session_path

    if args.derotate:
        derotate_images(session_path, sensors_angles)
    else:
        run(session_path, sensors_angles)
