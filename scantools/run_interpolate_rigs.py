from pathlib import Path
from typing import List, Dict
import os
import shutil
import argparse
import logging
from pyquaternion import Quaternion
from tqdm import tqdm
from bisect import bisect_left
from scantools.utils.utils import sort_and_prune, read_csv


"""
Assumes *.txt files have already been sorted by timestamp
Assumes sensors.txt, images.txt, depths, imu.txt, trajectories.txt, and rigs.txt exist
Interpolation scheme inspired by:
https://wiki.ros.org/message_filters/ApproximateTime

TODO:
- Only add sensors which exist (pointclouds, rigs, depths, etc.), not a hard-coded list
- Add flag for overwriting without user-interaction
- Use read_csv and write_csv instead of reading line by line
- Use best_timestamps instead of best_indices for storing selected messages
(dicts are technically guaranteed to preserve their order, but it's better to index them by
key, not by integer)
- Smooth interpolation using splines and multiple odometry messages
- Proper typing
- Improve documentation
- Verify correctness of interpolation, virtual rigs
- Check if there are images/imus at all, not parse them if they don't exist
"""


FAKE_SENSOR_NAME='fake-sensor'


def run(session_path : Path,
                     delete_unused : bool,
                     keep_unused_odometry : bool,
                     fast_selecting : bool,
                     skip_sanitation : bool):
    if (not session_path.is_dir() or
        not (session_path / 'sensors.txt').is_file() or
        not (session_path / 'images.txt').is_file() or
        not (session_path / 'depths.txt').is_file() or
        not (session_path / 'imu.txt').is_file() or
        not (session_path / 'trajectories.txt').is_file() or
        not (session_path / 'rigs.txt').is_file()):
        logging.error(f"sensors.txt, images.txt, depths, imu.txt, trajectories.txt, or rigs.txt don't exist in folder {session_path} (or folder doesn't exist)")
        exit(1)

    if ((session_path / 'images.txt.bak').is_file() or
        (session_path / 'depths.txt.bak').is_file() or
        (session_path / 'imu.txt.bak').is_file() or
        (session_path / 'trajectories.txt.bak').is_file() or
        (session_path / 'rigs.txt.bak').is_file()):
        logging.warning(" *.bak versions of images.txt, imu.txt, trajectories.txt, sensors.txt, or rigs.txt has been found, which means that *.txt may already contain the interpolated rigs. To continue and re-interpolate, enter 'Y'. Enter anything else to stop this script.")
        user_input = input("Y/n: ")
        if user_input != "Y":
            logging.info("Shutting down...")
            exit(0)
    else:
        shutil.copyfile(session_path / 'images.txt', session_path / 'images.txt.bak')
        shutil.copyfile(session_path / 'depths.txt', session_path / 'depths.txt.bak')
        shutil.copyfile(session_path / 'imu.txt', session_path / 'imu.txt.bak')
        shutil.copyfile(session_path / 'trajectories.txt', session_path / 'trajectories.txt.bak')
        shutil.copyfile(session_path / 'rigs.txt', session_path / 'rigs.txt.bak')

    if skip_sanitation:
        logging.info('Skipping sanitation step')
    else:
        logging.info('Sorting and pruning duplicate rows in images.txt, depths.txt, imu.txt, and trajectories.txt')
        sort_and_prune(session_path / 'images.txt.bak', overwrite=True)
        sort_and_prune(session_path / 'depths.txt.bak', overwrite=True)
        sort_and_prune(session_path / 'imu.txt.bak', overwrite=True)
        sort_and_prune(session_path / 'trajectories.txt.bak', overwrite=True)
        logging.info('Sorted and pruned')

    if keep_unused_odometry:
        logging.info("Keeping odometry messages which don't make it into virtual rigs")
        shutil.copyfile(session_path / 'sensors.txt', session_path / 'sensors.txt.bak')
        with open(session_path / 'sensors.txt', 'a') as f_sensors:
            f_sensors.write(f'{FAKE_SENSOR_NAME}, {FAKE_SENSOR_NAME}, {FAKE_SENSOR_NAME}-type, 0')

    rigs = get_sensor_transformations(session_path / 'rigs.txt.bak')

    sensors = {}            # store sensor type per sensor
    timestamps = {}         # store list of timestamps per sensor
    lines = {}              # store list of lines per sensor
    best_timestamps = {}    # store best timestamp found per sensor
    f_sensors = open(session_path / 'sensors.txt', 'r')
    # dump header row
    _ = f_sensors.readline()
    for line in f_sensors:
        sensor = line.replace(' ', '').split(',')
        # only keep sensors that also have a corresponding rig transformation
        if sensor[0] in rigs:
            sensors[sensor[0]] = {'sensor_type' : sensor[2], 'sensor_line' : line.rstrip()}
            timestamps[sensor[0]] = []
            lines[sensor[0]] = []
    f_sensors.close()

    # we require two odometry messages for interpolation; a lower bound and an
    # upper bound
    sensors['trajectory_lower'] = {'sensor_type' : 'trajectory'}
    sensors['trajectory_upper'] = {'sensor_type' : 'trajectory'}
    timestamps['trajectory_lower'] = []
    timestamps['trajectory_upper'] = []
    lines['trajectory_lower'] = []
    lines['trajectory_upper'] = []
    best_timestamps['trajectory_lower'] = None
    best_timestamps['trajectory_upper'] = None

    f_images = open(session_path / 'images.txt.bak', 'r')
    f_depths = open(session_path / 'depths.txt.bak', 'r')
    f_imus = open(session_path / 'imu.txt.bak', 'r')
    f_trajectories = open(session_path / 'trajectories.txt.bak', 'r')
    f_rigs = open(session_path / 'rigs.txt.bak', 'r')

    f_images_out = open(session_path / 'images.txt', 'w')
    f_depths_out = open(session_path / 'depths.txt', 'w')
    f_imus_out = open(session_path / 'imu.txt', 'w')
    f_trajectories_out = open(session_path / 'trajectories.txt', 'w')
    f_rigs_out = open(session_path / 'rigs.txt', 'w')

    # transfer column names
    f_images_out.write(f_images.readline())
    f_depths_out.write(f_depths.readline())
    f_imus_out.write(f_imus.readline())
    f_trajectories_out.write(f_trajectories.readline())
    f_rigs_out.write(f_rigs.readline())

    # get first line of each
    image_line = f_images.readline().rstrip()
    depth_line = f_depths.readline().rstrip()
    imu_line = f_imus.readline().rstrip()
    trajectory_line = f_trajectories.readline().rstrip()

    image_arr = image_line.replace(' ', '').split(',')
    depth_arr = depth_line.replace(' ', '').split(',')
    imu_arr = imu_line.replace(' ', '').split(',')
    trajectory_arr = trajectory_line.replace(' ', '').split(',')

    image_t = int(image_arr[0])
    depth_t = int(depth_arr[0])
    imu_t = int(imu_arr[0])
    trajectory_t = int(trajectory_arr[0])

    images_parsed = False
    depths_parsed = False
    trajectories_parsed = False
    imus_parsed = False

    if fast_selecting:
        logging.info('Creating virtual rigs with fast selection')
        select_instances = eval('select_next_instances')
    else:
        logging.info('Creating virtual rigs. If this process is too slow, try running with --fast')
        select_instances = eval('select_best_instances')
    if delete_unused:
        logging.info('Will delete unused images/depths to save space')
    num_image = len(read_csv(session_path / 'images.txt.bak')[0])
    num_depth = len(read_csv(session_path / 'depths.txt.bak')[0])
    num_imu = len(read_csv(session_path / 'imu.txt.bak')[0])
    num_trajectory = len(read_csv(session_path / 'trajectories.txt.bak')[0])
    total = num_image + num_depth + num_imu + num_trajectory
    pbar = tqdm(total=total)
    while not ((images_parsed and depths_parsed and imus_parsed and trajectories_parsed) or trajectories_parsed):
        if (((image_t <= imu_t and image_t <= depth_t and image_t < trajectory_t) or
             (depths_parsed and imus_parsed)) and
             not images_parsed):
            if image_arr[1] in sensors:
                timestamps[image_arr[1]].append(image_t)
                lines[image_arr[1]].append(image_line)
            image_line = f_images.readline().rstrip()
            if image_line != '':
                image_arr = image_line.replace(' ', '').split(',')
                image_t = int(image_arr[0])
            else:
                images_parsed = True
        elif (((depth_t <= imu_t and depth_t <= image_t and depth_t < trajectory_t) or
             (images_parsed and imus_parsed)) and
             not depths_parsed):
            if depth_arr[1] in sensors:
                timestamps[depth_arr[1]].append(depth_t)
                lines[depth_arr[1]].append(depth_line)
            depth_line = f_depths.readline().rstrip()
            if depth_line != '':
                depth_arr = depth_line.replace(' ', '').split(',')
                depth_t = int(depth_arr[0])
            else:
                depths_parsed = True
        elif (((imu_t <= image_t and imu_t <= depth_t and imu_t < trajectory_t) or
               (images_parsed and depths_parsed)) and
               not imus_parsed):
            if imu_arr[1] in sensors:
                timestamps[imu_arr[1]].append(imu_t)
                lines[imu_arr[1]].append(imu_line)
            imu_line = f_imus.readline().rstrip()
            if imu_line != '':
                imu_arr = imu_line.replace(' ', '').split(',')
                imu_t = int(imu_arr[0])
            else:
                imus_parsed = True
        elif not trajectories_parsed:
            timestamps['trajectory_lower'].append(trajectory_t)
            timestamps['trajectory_upper'].append(trajectory_t)
            lines['trajectory_lower'].append(trajectory_line)
            lines['trajectory_upper'].append(trajectory_line)
            trajectory_line = f_trajectories.readline().rstrip()
            if trajectory_line != '':
                trajectory_arr = trajectory_line.replace(' ', '').split(',')
                trajectory_t = int(trajectory_arr[0])
            else:
                trajectories_parsed = True

        at_least_one = True
        for sensor_id in sensors:
            if len(timestamps[sensor_id]) == 0:
                at_least_one = False

        if at_least_one:
            best_indices, valid_odom_found = select_instances(timestamps, best_timestamps)
            if valid_odom_found:
                logging.debug('')
                logging.debug(f'Found valid set of messages, best indices: {best_indices}')
                logging.debug('Printing first and last timestep of each sensor\'s queue')

                for idx, sensor_id in enumerate(timestamps):
                    # Just first and last timestamp, otherwise too much
                    logging.debug(f"{sensor_id}: {[timestamps[sensor_id][0], timestamps[sensor_id][-1]]}")

                if keep_unused_odometry:
                    write_unused_odometry(f_trajectories_out,
                                          f_rigs_out,
                                          lines,
                                          best_indices)

                if delete_unused:
                    delete_unused_images(session_path,
                                        sensors,
                                        lines,
                                        best_indices)

                rigs_new, time_for_all, odometry_new = interpolate(rigs, sensors, timestamps, lines, best_indices)
                write_virtual_rigs(f_images_out=f_images_out,
                                   f_depths_out=f_depths_out,
                                   f_imus_out=f_imus_out,
                                   f_trajectories_out=f_trajectories_out, f_rigs_out=f_rigs_out,
                                   sensors=sensors,
                                   lines=lines,
                                   rigs=rigs,
                                   best_indices=best_indices,
                                   rigs_new=rigs_new,
                                   time_for_all=time_for_all,
                                   odometry_new = odometry_new)

                # Remove used messages from queues
                for idx, sensor_id in enumerate(sensors):
                    if sensor_id in {'trajectory_lower', 'trajectory_upper'}:
                        # Allow trajectory reuse
                        timestamps[sensor_id] = timestamps[sensor_id][best_indices[idx]:]
                        lines[sensor_id] = lines[sensor_id][best_indices[idx]:]
                    else:
                        if (best_indices[idx]+1) < len(timestamps[sensor_id]):
                            timestamps[sensor_id] = timestamps[sensor_id][best_indices[idx]+1:]
                            lines[sensor_id] = lines[sensor_id][best_indices[idx]+1:]
                        else:
                            timestamps[sensor_id] = []
                            lines[sensor_id] = []
            else:
                logging.debug(f'Suitable set of odometry messages not found.')
        pbar.update(1)
    pbar.close()

    f_images.close()
    f_depths.close()
    f_imus.close()
    f_trajectories.close()
    f_rigs.close()
    f_images_out.close()
    f_depths_out.close()
    f_imus_out.close()
    f_trajectories_out.close()
    f_rigs_out.close()

    # TODO: figure out why, if keeping unused odometry, messages are not written to file in chronological order, and this is therefore necessary
    if keep_unused_odometry:
        sort_and_prune(session_path / 'trajectories.txt', overwrite=True)


def get_sensor_transformations(rig_file):
    """
    Parse input file (must follow rigs.txt convention) and extract transformations
    from sensor frame to rig frame.

    :param Path rig_file: location of file following rigs.txt convention
    :return: dictionnary containing sensor_id:transformation pairs and rig name
    """
    transformations = {}
    f_rigs = open(rig_file, 'r')
    # dump header row
    _ = f_rigs.readline()
    for transformation in f_rigs:
        transformation_arr = transformation.replace(' ', '').split(',')
        # x, y, z, qw, qx, qy, qz
        pos_quat = [float(i) for i in transformation_arr[6:9]+transformation_arr[2:6]]
        sensor_id = transformation_arr[1]
        transformations[sensor_id] = {'rig' : transformation_arr[0],
                                      'line' : transformation.rstrip(),
                                      'pos_quat' : pos_quat}
    f_rigs.close()
    return transformations


def select_next_instances(timestamps : Dict[str, List[int]], best_timestamps : Dict[str, int]):
    """
    Uses only the most recent of each image, and the most recent trajectory
    before all selected images as the lower bound, and oldest trajectory after 
    all images as the upper bound.
    Loosely based on: https://wiki.ros.org/message_filters/ApproximateTime
    """
    best_indices = [None] * len(timestamps)
    for index_sensor, sensor_id in enumerate(timestamps):
        if sensor_id == 'trajectory_lower':
            assert (index_sensor == len(timestamps) - 2)
            for index_trajectory, timestamp_trajectory in reversed(list(enumerate(timestamps[sensor_id]))):
                lesser_than = True
                for sensor_id_other in timestamps:
                    if (sensor_id_other not in {'trajectory_lower', 'trajectory_upper'}
                        and not (timestamp_trajectory <=
                            timestamps[sensor_id_other][-1])):
                        lesser_than = False
                if lesser_than:
                    best_indices[index_sensor] = index_trajectory
                    break
        elif sensor_id == 'trajectory_upper':
            assert (index_sensor == len(timestamps) - 1)
            for index_trajectory, timestamp_trajectory in enumerate(timestamps[sensor_id]):
                greater_than = True
                for sensor_id_other in timestamps:
                    if (sensor_id_other not in {'trajectory_lower', 'trajectory_upper'}
                        and not (timestamp_trajectory >=
                            timestamps[sensor_id_other][-1])):
                        greater_than = False
                if greater_than:
                    best_indices[index_sensor] = index_trajectory
                    break
        else:
            best_indices[index_sensor] = len(timestamps[sensor_id]) - 1 # last element
    valid_odom_found = (best_indices[-1] != None and best_indices[-2] != None)
    if valid_odom_found:
        return best_indices, valid_odom_found
    else:
        return None, valid_odom_found 


def select_best_instances(timestamps : Dict[str, List[int]], best_timestamps : Dict[str, int]):
    """
    Find set of sensor messages which are the closest to each-other across all
    sensors.
    Iterate over messages in the queue of the first sensor and find the message
    with the most similar timestamp for each other sensor.
    Choose the set of messages with the lowest variation.
    Additional condition: there must be a trajectory message lesser or equal
    to the smallest selected message in all other queues, and a trajectory message
    greater or equal to the largest select message in all other queues.

    :param dict sensors: dict containing sensor_id:{timestamp, line} pairs
    :return: set of best indices, and boolean indicating whether valid odometry messages found
    """
    sensor_ids = list(timestamps)
    best_indices = [[None]*len(timestamps) for _ in range(len(timestamps[sensor_ids[0]]))]

    # create a set of arrays containing the best match for each message in the
    # first sensor's (with prefix '0') queue
    # TODO: rename msg_0 and msg to timestamp_0 and timestamp
    for index_msg_0, msg_0 in enumerate(timestamps[sensor_ids[0]]):
        best_indices[index_msg_0][0] = index_msg_0
        for index_sensor, sensor_id in enumerate(sensor_ids[1:]):
            if sensor_id in {'trajectory_lower', 'trajectory_upper'}:
                best_delta = float("inf")
                for index_msg, msg in enumerate(timestamps[sensor_id]):
                    delta = abs(msg_0 - msg)
                    if delta < best_delta:
                        if sensor_id == 'trajectory_lower':
                            lesser_than = True
                            # [:-2] since [-1] and [-2] are trajectory_lower and _upper
                            for idx, i in enumerate(best_indices[index_msg_0][:-2]):
                                if not (msg <=
                                        timestamps[sensor_ids[idx]][i]):
                                    lesser_than = False
                            if lesser_than:
                                best_delta = delta
                                # +1 since we're looping over sensors[1:], not sensors[:]
                                best_indices[index_msg_0][index_sensor+1] = index_msg
                        elif sensor_id == 'trajectory_upper':
                            greater_than = True
                            # [:-2] since [-1] and [-2] are trajectory_lower and _upper
                            for idx, i in enumerate(best_indices[index_msg_0][:-2]):
                                if not (msg >=
                                        timestamps[sensor_ids[idx]][i]):
                                    greater_than = False
                            if greater_than:
                                best_delta = delta
                                # +1 since we're looping over sensors[1:], not sensors[:]
                                best_indices[index_msg_0][index_sensor+1] = index_msg
                        else:
                            raise ValueError(f'Something has gone terribly wrong, what should be trajectory_lower or trajectory_upper, not {sensor_id}')
            else:
                # +1 since we're looping over sensors[1:], not sensors[:]
                best_indices[index_msg_0][index_sensor+1] = take_closest(timestamps[sensor_id], msg_0)

    valid_odom_found = False
    best_array_index = None
    best_delta = float("inf")
    for index_array, array_of_indices in enumerate(best_indices):
        if array_of_indices[-1] != None and array_of_indices[-2] != None:
            valid_odom_found = True
            delta = 0
            for idx, x in enumerate(array_of_indices):
                for idy, y in enumerate(array_of_indices):
                    delta += abs(timestamps[sensor_ids[idx]][x]
                                - timestamps[sensor_ids[idy]][y])
            if delta < best_delta:
                best_delta = delta
                best_array_index = index_array

    if valid_odom_found:
        return best_indices[best_array_index], valid_odom_found
    else:
        return None, valid_odom_found


def take_closest(timestamps_sensor, timestamp):
    """
    https://stackoverflow.com/questions/12141150/from-list-of-integers-get-number-closest-to-a-given-value/12141511#12141511
    Assumes sorted list
    If not the left-most time, it will be placed to the right of the desired timestamp
    (have an index one higher than desired if closer to the smaller neighbor.
    Ex:
    bisect_left([1,4,7], 0) = 0
    bisect_left([1,4,7], 10) = 3, but we want 2
    bisect_left([1,4,7], 2) = 1, but we want 0
    bisect_left([1,4,7], 3) = 1, and we want 1
    bisect_left([1,4,7], 5) = 2, but we want 1
    bisect_left([1,4,7], 6) = 2, and we want 2
    Logic: if extremity, give the extremity. If not extremity:
    - If closer to left-hand, subtract 1
    - If closer to right-hand, keep position
    """
    position = bisect_left(timestamps_sensor, timestamp)
    if position == 0:
        return 0
    elif position == len(timestamps_sensor):
        return position - 1
    before = timestamps_sensor[position - 1]
    after = timestamps_sensor[position]
    if after - timestamp < timestamp - before:
        return position
    else:
        return position - 1


def delete_unused_images(session_path : Path,
                         sensors : dict,
                         lines : Dict[str, List[str]],
                         best_indices : list):
    for idx, sensor_id in enumerate(sensors):
        if (sensors[sensor_id]['sensor_type'] == 'camera' or 
            sensors[sensor_id]['sensor_type'] == 'depth'):
            for i in range(best_indices[idx]):
                arr = lines[sensor_id][i].replace(' ', '').split(',')
                image_path_relative = arr[2]
                image_path_absolute = session_path / 'raw_data' / image_path_relative
                if image_path_absolute.exists():
                    os.remove(image_path_absolute)


def interpolate(rigs : dict,
                sensors : dict,
                timestamps : Dict[str, List[int]],
                lines : Dict[str, List[str]],
                best_indices : list):
    """
    Interpolate transformation and rotation of each rig, create virtual rig,
    write new rigs and sensor messages to files.
    Misc sources of info on quaternion math:
    Inversion: https://en.wikipedia.org/wiki/Quaternion
    Multiplication: https://en.wikipedia.org/wiki/Quaternions_and_spatial_rotation
    Multiplication: https://mathworld.wolfram.com/Quaternion.html

    :param dict rigs: contains sensor_id, rig_id, and position/quaternion pair
    :param dict sensors: sensor_id:(sensor_type:type, queue: [{timestamp:123, line: 'aaa'}])
    :param list best_indices: array containing one index per sensor
    :return: interpolated rigs
    :return: midpoint time between start and end odometry message
    :return: interpolated odometry in order qw,qx,qy,qz,x,y,z
    """
    # shallow-ish copy of rigs that only contains the new position and quaternion
    rigs_new = {}
    time_start = timestamps['trajectory_lower'][best_indices[-2]]
    time_end = timestamps['trajectory_upper'][best_indices[-1]]

    arr_start = lines['trajectory_lower'][best_indices[-2]].replace(' ', '').split(',')
    arr_end = lines['trajectory_upper'][best_indices[-1]].replace(' ', '').split(',')

    pos_start = [float(i) for i in arr_start[6:9]]
    pos_end = [float(i) for i in arr_end[6:9]]
    quat_start = Quaternion([float(i) for i in arr_start[2:6]]).normalised
    quat_end = Quaternion([float(i) for i in arr_end[2:6]]).normalised

    # Get new timestamp
    times = [0]*len(sensors)
    for idx, sensor_id in enumerate(sensors):
        times[idx] = timestamps[sensor_id][best_indices[idx]]
    time_average = int(sum(times) / len(times))
    # fraction between 0 and 1 (t in [0, 1])
    time_interpolated = (time_average - time_start) / (time_end - time_start)

    # Get new odometry pose by interpolating start and end poses with average timestamp
    # p_inter = (1-t) * p0 + t * p1 = ... = p0 + (p1 - p0) * t
    pos_odometry = [(pos_end[0] - pos_start[0]) * time_interpolated + pos_start[0],
                    (pos_end[1] - pos_start[1]) * time_interpolated + pos_start[1],
                    (pos_end[2] - pos_start[2]) * time_interpolated + pos_start[2]]
    quat_odometry = Quaternion.slerp(quat_start,
                                     quat_end,
                                     time_interpolated)

    logging.debug(f'Odometry start time: {time_start}')
    logging.debug(f'Odometry end time: {time_end}')
    logging.debug(f'Odometry new time: {time_average}')
    logging.debug(f'Odometry start position and quaternion: {pos_start} {quat_start}')
    logging.debug(f'Odometry end position and quaternion: {pos_end} {quat_end}')
    logging.debug(f'Odometry new position and quaternion: {pos_odometry}, {quat_odometry}')

    for idx, sensor_id in enumerate(sensors):
        if sensor_id == 'trajectory_lower' or sensor_id == 'trajectory_upper':
            continue

        time_current = timestamps[sensor_id][best_indices[idx]]
        # fraction between 0 and 1 (t in [0, 1])
        time_interpolated = (time_current - time_start) / (time_end - time_start)
        # p_inter = (1-t) * p0 + t * p1 = ... = p0 + (p1 - p0) * t
        pos_interpolated = [(pos_end[0] - pos_start[0]) * time_interpolated + pos_start[0],
                            (pos_end[1] - pos_start[1]) * time_interpolated + pos_start[1],
                            (pos_end[2] - pos_start[2]) * time_interpolated + pos_start[2]]
        quat_interpolated = Quaternion.slerp(quat_start,
                                             quat_end,
                                             time_interpolated)

        pos_current = rigs[sensor_id]['pos_quat'][:3]
        quat_current = Quaternion(rigs[sensor_id]['pos_quat'][3:]).normalised

        if time_current < time_average:
            pos_delta = [pos_odometry[0] - pos_interpolated[0],
                         pos_odometry[1] - pos_interpolated[1],
                         pos_odometry[2] - pos_interpolated[2]]
            # subtracting rotations in quaternion notation done by dividing
            quat_delta = (quat_odometry / quat_interpolated).normalised
        else:
            pos_delta = [pos_interpolated[0] - pos_odometry[0],
                         pos_interpolated[1] - pos_odometry[1],
                         pos_interpolated[2] - pos_odometry[2]]
            # subtracting rotations in quaternion notation done by dividing
            quat_delta = (quat_interpolated / quat_odometry).normalised

        # position and quaternion relative to rig, used to create the virtual rigs
        pos_new = [pos_current[0] + pos_delta[0],
                   pos_current[1] + pos_delta[1],
                   pos_current[2] + pos_delta[2]]
        # https://en.wikipedia.org/wiki/Quaternions_and_spatial_rotation
        quat_new = (quat_current * quat_delta).normalised

        rigs_new[sensor_id] = {'rig': rigs[sensor_id]['rig'],
                               'pos_quat': [pos_new[0], pos_new[1], pos_new[2],
                                            quat_new[0], quat_new[1], quat_new[2], quat_new[3]]}

        logging.debug(f'')
        logging.debug(f'Sensor ID: {sensor_id}')
        logging.debug(f'Sensor time: {time_current}')
        logging.debug(f'Change in position relative to new odometry position: {pos_delta}')
        logging.debug(f'Change in rotation relative to new odometry rotation: {quat_delta}')
        logging.debug(f'Sensor original position and quaternion: {pos_current} {quat_current}')
        logging.debug(f'Sensor updated position and quaternion: {pos_new} {quat_new}')

    odometry_new = [quat_odometry[0], quat_odometry[1], quat_odometry[2], quat_odometry[3],
                    pos_odometry[0], pos_odometry[1], pos_odometry[2]]

    return rigs_new, time_average, odometry_new


def write_virtual_rigs(f_images_out, f_depths_out, f_imus_out, f_trajectories_out, f_rigs_out,
                       sensors, lines, rigs, best_indices, rigs_new, time_for_all, odometry_new):
    """
    Write out new virtual rigs, as well as updated sensor names with timestamps
    to respective files
    """
    time_for_all = str(time_for_all)
    for idx, sensor_id in enumerate(sensors):
        # TODO: all this code assumes constant order to dict, which is true,
        # but combining indexing in best_indices and key accessing in sensors
        # is really messy; it would be better if they were both by key
        if sensor_id == 'trajectory_lower':
            assert(idx == len(sensors)-2)
            arr = lines['trajectory_lower'][best_indices[idx]].replace(' ', '').split(',')
            arr[0] = time_for_all
            arr[1] = time_for_all + '-' + arr[1]
            arr[2:9] = [str(i) for i in odometry_new]
            f_trajectories_out.write(', '.join(arr) + '\n')
        elif sensors[sensor_id]['sensor_type'] == 'camera':
            arr = lines[sensor_id][best_indices[idx]].replace(' ', '').split(',')
            arr[0] = time_for_all
            f_images_out.write(', '.join(arr) + '\n')
        elif sensors[sensor_id]['sensor_type'] == 'depth':
            arr = lines[sensor_id][best_indices[idx]].replace(' ', '').split(',')
            arr[0] = time_for_all
            f_depths_out.write(', '.join(arr) + '\n')
        elif sensors[sensor_id]['sensor_type'] == 'IMU':
            arr = lines[sensor_id][best_indices[idx]].replace(' ', '').split(',')
            arr[0] = time_for_all
            f_imus_out.write(', '.join(arr) + '\n')

        if sensor_id != 'trajectory_upper' and sensor_id != 'trajectory_lower':
            arr = rigs[sensor_id]['line'].replace(' ', '').split(',')
            arr[0] = time_for_all + '-' + arr[0]
            pos_quat_new = rigs_new[sensor_id]['pos_quat']
            arr[2:9] = [str(i) for i in pos_quat_new[3:]+pos_quat_new[:3]]
            f_rigs_out.write(', '.join(arr) + '\n')


def write_unused_odometry(f_trajectories_out,
                          f_rigs_out,
                          lines : Dict[str, List[str]],
                          best_indices : list):
    """
    Maplab can use extra odometry measures, so keep the ones that didn't make it
    into a virtual rig. A fake virtual rig is necessary to comply with Capture spec (there must be a corresponding rig_device_id in rigs.txt for each device_id in
    trajectories.txt), as is a fake sensor in sensors.txt
    """
    for i in range(best_indices[-2]):
        arr = lines['trajectory_lower'][i].replace(' ', '').split(',')
        arr[1] = arr[0] + '-' + arr[1]
        f_trajectories_out.write(', '.join(arr) + '\n')
        f_rigs_out.write(f"{arr[1]}, {FAKE_SENSOR_NAME}, 1, 0, 0, 0, 0, 0, 0\n")


def revert(session_path : Path):
    logging.info('Moving *.bak files back')
    if not ((session_path / 'images.txt.bak').is_file() or
            (session_path / 'depths.txt.bak').is_file() or
            (session_path / 'imu.txt.bak').is_file() or
            (session_path / 'trajectories.txt.bak').is_file() or
            (session_path / 'rigs.txt.bak').is_file() or
            (session_path / 'sensors.txt.bak').is_file()):
        logging.error("Couldn't find *.bak files in capture path, nothing to derotate?")    


    for f in {'images.txt.bak', 'depths.txt.bak', 'imu.txt.bak', 'trajectories.txt.bak', 'rigs.txt.bak', 'sensors.txt.bak'}:
        if (session_path / f).is_file():
            shutil.move(session_path / f, session_path / f.rstrip('.bak'))


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--session_path', type=Path, required=True,
                        help="Relative or global path of folder containing sensors.txt, images.txt, imu.txt, trajectories.txt, and rigs.txt. Ex: ~/lamar/data/CAB/01")
    parser.add_argument('--delete_unused', action='store_true', required=False,
                        help="Delete images which aren't kept in images.txt or depths.txt")
    parser.add_argument('--keep_unused_odometry', action='store_true', required=False,
                        help="Write odometry messages which weren't part of virtual rigs to trajectories.txt")
    parser.add_argument('--debug', action='store_true', required=False,
                        help="Extra terminal output for debugging")
    parser.add_argument('--fast', action='store_true', required=False,
                        help='Use most recent messages instead of closest ones')
    parser.add_argument('--revert', action='store_true', required=False,
                        help='Reverse interpolation process. Should only be used if the interpolator has been run over the given session')
    parser.add_argument('--skip_sanitation', action='store_true', required=False,
                        help="Don\'t sort and prune .txt files to remove duplicate/out of order entries")
    args = parser.parse_args()
    session_path = args.session_path
    delete_unused = args.delete_unused
    keep_unused_odometry = args.keep_unused_odometry
    fast_selecting = args.fast
    skip_sanitation = args.skip_sanitation
    if args.debug:
        logging.getLogger().setLevel(logging.DEBUG)
    else:
        logging.getLogger().setLevel(logging.INFO)
    if args.revert:
        revert(session_path)
    else:
        run(session_path, delete_unused, keep_unused_odometry, fast_selecting, skip_sanitation)
