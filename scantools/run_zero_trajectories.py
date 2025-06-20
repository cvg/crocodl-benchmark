from pathlib import Path
import argparse
import shutil
import logging
import numpy as np
from scantools.utils.utils import read_csv, write_csv


"""
Set average pose of trajectories to [0, 0, 0]
"""


def run(file_path):
    logging.info('Zeroing trajectories')
    if not file_path.is_file():
        raise IOError(f'File not found: {file_path}')

    shutil.copyfile(file_path, Path(str(file_path) + '.unzeroed'))

    trajectories, columns = read_csv(file_path)

    xyz_sum = np.array([0.0, 0.0, 0.0])
    for line in trajectories:
        xyz_sum += [float(i) for i in line[6:9]]
    xyz_average = xyz_sum / len(trajectories)

    for line in trajectories:
        xyz = [float(i) for i in line[6:9]]
        line[6:9] = [str(i) for i in (xyz - xyz_average)]

    write_csv(file_path, trajectories, columns)
    logging.info(f'Shifted all trajectories by {xyz_average}')

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('--file', type=Path, required=True,
                        help="Relative or global path of Capture-formatted trajectories file. Ex: ~/lamar/data/CAB/01/trajectories.txt")
    logging.getLogger().setLevel(logging.INFO)

    args = parser.parse_args()
    file_path = args.file
    run(file_path)
