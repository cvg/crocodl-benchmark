from pathlib import Path
from typing import Dict
import argparse
import logging
from scantools.utils.utils import read_csv, write_csv
import numpy as np
import pickle
from pytransform3d.transformations import pq_from_transform, transform_from_pq, invert_transform
from tqdm import tqdm

"""
Assumptions:
- kinect's IMU was chosen as the system rig
- This script is run before post-processing the session at all
- sensor_device_id in rigs.txt are exactly the same as those in the pickled transform dictionnary

WARNING: this script MUST be run BEFORE creating virtual rigs or rotating images; it essentially overwrites the transformations in rigs.txt; since image rotation and virtual rigs modify these transformations, this must be run first
"""


def fix_rigs(rigs_path : Path, sensor_to_rig : Dict[str, np.array]):
    rigs, columns = read_csv(rigs_path)
    logging.info("Correcting extrinsics in rigs.txt")
    for rig in rigs:
        sensor_device_id = rig[1]
        if sensor_device_id in sensor_to_rig:
            logging.debug(f'Found sensor {sensor_device_id} in transforms, fixing extrinsics')
            pq = pq_from_transform(sensor_to_rig[sensor_device_id])
            rig[2:] = [str(i) for i in (np.append(pq[3:], pq[:3]))]
        else:
            logging.warning(f'Didn\'t find sensor {sensor_device_id} in transforms, not changing its extrinsics')
    write_csv(rigs_path, rigs, columns)


def fix_trajectories(trajectories_path : Path, rig_to_body : Dict[str, np.array]):
    trajectories, columns = read_csv(trajectories_path)
    T_body_rig_old = rig_to_body['old']
    T_body_rig_new = rig_to_body['new']
    logging.info("Correcting extrinsics in trajectories.txt")
    for trajectory in tqdm(trajectories):
        # qw, qx, qy, qz, x, y, z
        qp = [float(i) for i in trajectory[2:9]]
        T_odom_rig_old = transform_from_pq(np.append(qp[4:], qp[:4]))
        T_odom_rig_new = (T_odom_rig_old @ invert_transform(T_body_rig_old)) @ T_body_rig_new
        pq_new = pq_from_transform(T_odom_rig_new)
        trajectory[2:9] = [str(i) for i in np.append(pq_new[3:], pq_new[:3])]
    write_csv(trajectories_path, trajectories, columns)


def run(session_path : Path, pickle_sensor : Path, pickle_rig : Path):
    """
    Transformations are taken from calibration_heaven notebook output
    """
    logging.info('Correcting sensor extrinsics. This script MUST be run BEFORE any other post-processing such as image rotation, virtual rig creation, etc.')
    if not pickle_sensor.is_file():
        raise IOError(f'File not found: {pickle_sensor}')
    with open(pickle_sensor, 'rb') as f:
        sensor_to_rig = pickle.load(f)
    if not (session_path / 'rigs.txt').is_file():
        logging.info('rigs.txt not found in session_path folder, skipping')
    else:
        fix_rigs(session_path / 'rigs.txt', sensor_to_rig)

    if pickle_rig != None:
        if not pickle_rig.is_file():
            raise IOError(f'File not found: {pickle_rig}')
        with open(pickle_rig, 'rb') as f:
            rig_to_body = pickle.load(f)
        if not (session_path / 'trajectories.txt').is_file():
            logging.info('trajectories.txt not found in session_path folder, skipping')
        else:
            fix_trajectories(session_path / 'trajectories.txt', rig_to_body)
    else:
        logging.info("Path to pickled rig_to_body transformations not provided, skipping trajectories correction")


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--session_path', type=Path, required=True,
                        help="Relative or global path of folder containing trajectories.txt and rigs.txt. Ex: ~/lamar/data/CAB/01")
    parser.add_argument('--pickle_sensor', type=Path, required=True,
                        help="Relative or global path of pickled transforms between ZED, Kinect, and Spot sensors, and rig frame after calibration")
    parser.add_argument('--pickle_rig', type=Path, required=False,
                        help="Relative or global path of pickled transforms between the rig frame and spot body frame, before and after calibration; if the body frame is the rig frame, this flag can be ignored")
    parser.add_argument('--debug', action='store_true', required=False,
                        help="Extra terminal output for debugging")
    args = parser.parse_args()
    session_path = args.session_path
    pickle_sensor = args.pickle_sensor
    pickle_rig = args.pickle_rig
    if args.debug:
        logging.getLogger().setLevel(logging.DEBUG)
    else:
        logging.getLogger().setLevel(logging.INFO)
    run(session_path, pickle_sensor, pickle_rig)
