import os
import argparse
import rosbag
from pathlib import Path
from tqdm import tqdm

from . import logger

from scantools.utils.utils import (
    read_csv
)

def merge_bagfiles(output_bagfile: Path, 
                   input_bagfile1: Path, 
                   input_bagfile2: Path):
    
    if not(os.path.isfile(input_bagfile1) and os.path.isfile(input_bagfile2)):
        raise Exception('One or more of the input files does not exist')
    
    with rosbag.Bag(output_bagfile, 'w') as outbag, rosbag.Bag(input_bagfile1) as input_1, rosbag.Bag(input_bagfile2) as input_2:

        bag_1_done = False
        bag_2_done = False

        bag_1 = input_1.read_messages()
        bag_2 = input_2.read_messages()

        topic_1, msg_1, t_1 = next(bag_1)
        topic_2, msg_2, t_2 = next(bag_2)

        num_messages = input_1.get_message_count() + input_2.get_message_count()
        pbar = tqdm(total=num_messages)
        while (bag_1_done == False or bag_2_done == False):
            if (not bag_1_done) and ((t_1 <= t_2) or bag_2_done):
                outbag.write(topic_1, msg_1, t_1)
                try:
                    topic_1, msg_1, t_1 = next(bag_1)
                except:
                    bag_1_done = True
            elif (not bag_2_done) and ((t_1 > t_2) or bag_1_done):
                outbag.write(topic_2, msg_2, t_2)
                try:
                    topic_2, msg_2, t_2 = next(bag_2)
                except:
                    bag_2_done = True
            else:
                raise Exception('Error: something went wrong, both bagfiles are done, but `done` flags aren\nt set')
            pbar.update(1)
        pbar.close()


def run(input_file: Path,
        output_path: Path,
        nuc_path: Path,
        orin_path: Path,
        scene: str):
    
    """
    Given the input file, code takes give pairs of nuc and orin paths and combines them into merged file saved in Ouput_path.
    Bagfiles are saved as a name of the nuc_file + scene_name + ".bag".
    """
    
    bags, col_bags = read_csv(input_file)

    for nuc, orin in bags:
        
        out = nuc + '-' + scene + '.bag'
        nuc = nuc + '.bag'
        orin = orin + '.bag'

        nuc_bag_path = nuc_path / Path(nuc)
        orin_bag_path = orin_path / Path(orin)
        output_bag_path = output_path / Path(out)

        logger.info(f"Working on Nuc: {nuc_bag_path}")
        logger.info(f"Working on Orin: {orin_bag_path}")

        if os.path.exists(output_bag_path):
            logger.info(f"Output bagfile {output_bag_path} already exists. Skipping.")
            continue
        
        try:
            merge_bagfiles(
                output_bagfile=output_bag_path,
                input_bagfile1=nuc_bag_path,
                input_bagfile2=orin_bag_path
            )
        except Exception as e:
            error = f"[ERROR] Failed to process session {output_bag_path}: {e}"
            logger.warning(error)

        logger.info(f"Output bagfile saved to: {output_bag_path}")

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Merge two bagfiles')
    parser.add_argument('--input_file', type=Path, required=True, help="Path to the input .txt with sessions to merge.")
    parser.add_argument('--output_path', type=Path, required=True, help="Path to the directory where to put merged files.")
    parser.add_argument('--nuc_path', type=Path, required=True, help="Path to the directory of the nuc bagfiles.")
    parser.add_argument('--orin_path', type=Path, required=True, help="Path to the directory of the orin bagfiles.")
    parser.add_argument('--scene', type=str, required=True, default=None, help="Scene name, such as HYDRO.")
    args = parser.parse_args().__dict__
    run(**args)