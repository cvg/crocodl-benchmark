from pathlib import Path
import argparse
import logging
from scantools.utils.utils import read_csv, write_csv


def run(session_path : Path, overwrite : bool):
    logging.info('Creating queries.txt')
    if (session_path / 'queries.txt').exists() and not overwrite:
        user_input = input("queries.txt exists, overwrite? (y/N): ")
        if user_input != 'y':
            exit(0)
    queries = []
    trajectories, _ = read_csv(session_path / 'trajectories.txt')
    for line in trajectories:
        queries.append([line[0], line[1]])
    write_csv(session_path / 'queries.txt', queries, None)

if __name__ == '__main__':
    logging.getLogger().setLevel(logging.INFO)
    parser = argparse.ArgumentParser()
    parser.add_argument('--session_path', type=Path, required=True,
                        help="Relative or global path of folder containing trajectories.txt and rigs.txt. Ex: ~/lamar/data/CAB/01")
    parser.add_argument('--overwrite', action='store_true', required=False,
                        help="Overwrite existing queries.txt without asking")
    args = parser.parse_args()
    session_path = args.session_path
    overwrite = args.overwrite
    run(session_path, overwrite)
