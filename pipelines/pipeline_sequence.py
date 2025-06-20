from typing import List, Optional
from pathlib import Path
import argparse
import shutil

from scantools.utils.io import read_sequence_list

from scantools import logger, run_map_query_split
from scantools.capture import Capture, Session
from scantools import (
    run_sequence_aligner,
    run_combine_sequences,
    run_radio_transfer,
    run_joint_refinement,
)
from scantools.run_joint_refinement import MatchingConf, RefinementConf


conf_matcher = {'output': 'matches-superglue',
                'model': {'name': 'superglue', 'weights': 'outdoor', 'sinkhorn_iterations': 5}}
conf_matching = MatchingConf('netvlad', 'superpoint_aachen', conf_matcher)

conf_align = {
    'ios': run_sequence_aligner.Conf.from_dict(dict(
        **run_sequence_aligner.conf_ios, matching=conf_matching.to_dict())),
    'hl': run_sequence_aligner.Conf.from_dict(dict(
        **run_sequence_aligner.conf_hololens, matching=conf_matching.to_dict())),
    'spot': run_sequence_aligner.Conf.from_dict(dict(
        **run_sequence_aligner.conf_spot, matching=conf_matching.to_dict())),
}
conf_align['ios'].matching.local_features['model']['max_keypoints'] = 2048
conf_align['hl'].matching.local_features['model']['max_keypoints'] = 1024
# TODO: choose max_keypoints
conf_align['spot'].matching.local_features['model']['max_keypoints'] = 1024

conf_refine = RefinementConf(
    conf_matching,
    keyframings={
        Session.Device.PHONE: conf_align['ios'].localizer.keyframing,
        Session.Device.HOLOLENS: conf_align['hl'].localizer.keyframing,
        Session.Device.SPOT: conf_align['spot'].localizer.keyframing,
    },
)

eval_keyframing = run_combine_sequences.KeyFramingConf()
map_keyframing = run_combine_sequences.KeyFramingConf(max_distance=0.5, max_elapsed=0.4)


def process_sequence(capture, ref_id, input_path, conf, kind):
    sequence_id = f'{kind}_{input_path.name}'
    logger.info('Working on %s.', sequence_id)

    chunk_ids = sorted(filter(lambda i: i.startswith(sequence_id), capture.sessions))
    if len(chunk_ids) == 0:
        if kind == 'ios':
            shutil.copytree(input_path, capture.session_path(sequence_id))
            capture.sessions[sequence_id] = Session.load(capture.sessions_path() / sequence_id)
            chunk_ids = [sequence_id]
        elif kind.startswith('hl'):
            shutil.copytree(input_path, capture.session_path(sequence_id))
            capture.sessions[sequence_id] = Session.load(capture.sessions_path() / sequence_id)
            chunk_ids = [sequence_id]
        elif kind.startswith('spot'):
            shutil.copytree(input_path, capture.session_path(sequence_id))
            capture.sessions[sequence_id] = Session.load(capture.sessions_path() / sequence_id)
            chunk_ids = [sequence_id]
        else:
            raise ValueError(kind)

    logger.info('Found %d chunks for sequence %s', len(chunk_ids), sequence_id)
    chunk_ids_aligned = []
    num_failed = 0
    for session_id in chunk_ids:
        path_trajectory = capture.registration_path() / session_id / ref_id / 'trajectory_ba.txt'
        if not path_trajectory.exists():
            logger.info('Aligning session %s.', session_id)
            success = run_sequence_aligner.run(
                capture, ref_id, session_id, conf,
                overwrite=False,
                visualize_diff=False,
                vis_mesh_id='mesh_simplified')
            if not success:
                num_failed += 1
                continue
        chunk_ids_aligned.append(session_id)
    if num_failed > 0:
        logger.warning('Could not align %d/%d chunks for session %s.',
                       num_failed, len(chunk_ids), sequence_id)

    return chunk_ids_aligned


def run(capture_path: Path,
        ref_id: str,
        phone_dir: Optional[Path] = None,
        hololens_dir: Optional[Path] = None,
        spot_dir: Optional[Path] = None,
        phone_sequences: List[str] = ('*',),
        hololens_sequences: List[str] = ('*',),
        spot_sequences: List[str] = ('*',),
        run_lamar_splitting: bool = False
        ):

    capture = Capture.load(capture_path, wireless=False)

    select_path = capture.path / 'sequences_select.txt'
    if select_path.exists():
        sequence_ids = read_sequence_list(select_path)
        for i in sequence_ids:
            if i not in capture.sessions:
                raise ValueError(i, list(capture.sessions.keys()))
        logger.info('Read %d sequences from %s', len(sequence_ids), select_path)
    else:
        sequence_ids = []
        if phone_dir is not None:
            phone_paths = [phone_dir / g for g in phone_sequences]
            for path in phone_paths:
                sequence_ids += process_sequence(capture, ref_id, path, conf_align['ios'], 'ios')
        if hololens_dir is not None:
            hololens_paths = [hololens_dir / g for g in hololens_sequences]
            for path in hololens_paths:
                sequence_ids += process_sequence(capture, ref_id, path, conf_align['hl'], 'hl')
        if spot_dir is not None:
            spot_paths = [spot_dir / g for g in spot_sequences]
            for path in spot_paths:
                sequence_ids += process_sequence(capture, ref_id, path, conf_align['spot'], 'spot')
        assert len(sequence_ids) > 0
        logger.info('Found %d sequences', len(sequence_ids))
        with open(capture.path / 'sequences.txt', 'w') as fid:
            fid.write("\n".join(sequence_ids))

    if not all((capture.registration_path()/i/'trajectory_refined.txt').exists()
               for i in sequence_ids):
        logger.info('Running the joint refinement.')
        run_joint_refinement.run(capture, ref_id, sequence_ids, conf_refine)
    
    if run_lamar_splitting:
        logger.info('Splitting sequences into maps and queries.')
        map_ids, query_ids = run_map_query_split.run(capture, sequence_ids, ref_id=ref_id)
        query_ids_phone = list(filter(lambda i: i.startswith('ios'), query_ids))
        query_ids_hololens = list(filter(lambda i: i.startswith('hl'), query_ids))
        query_ids_spot = list(filter(lambda i: i.startswith('spot'), query_ids))

        map_id = 'map'
        query_id_phone = 'query_phone'
        query_id_hololens = 'query_hololens'
        query_id_spot = 'query_spot'
        logger.info('Writing map and query sessions')
        run_combine_sequences.run(
            capture, map_ids, map_id, overwrite_poses=True,
            keyframing=map_keyframing, reference_id=ref_id)
        for i, ids in [[query_id_phone, query_ids_phone], [query_id_hololens, query_ids_hololens], [query_id_spot, query_ids_spot]]:
            run_combine_sequences.run(
                capture, ids, i, overwrite_poses=False, keyframing=eval_keyframing)

        run_radio_transfer.run(capture, [map_id, query_id_phone, query_id_hololens])

def get_data_CAB(sequence_list_dir):
    ref_id = '2022-06-21_09.28.22+2022-06-25_11.14.36'
    phone_sequences = read_sequence_list(sequence_list_dir / 'CAB_phone.txt')
    hololens_sequences = read_sequence_list(sequence_list_dir / 'CAB_hololens.txt')
    spot_sequences = read_sequence_list(sequence_list_dir / 'CAB_spot.txt')
    return ref_id, phone_sequences, hololens_sequences, spot_sequences

def get_data_HGE(sequence_list_dir):
    ref_id = '2022-02-06_12.55.11+2022-02-26_16.21.10'
    phone_sequences = read_sequence_list(sequence_list_dir / 'HGE_phone.txt')
    hololens_sequences = read_sequence_list(sequence_list_dir / 'HGE_hololens.txt')
    spot_sequences = read_sequence_list(sequence_list_dir / 'HGE_spot.txt')
    return ref_id, phone_sequences, hololens_sequences, spot_sequences

def get_data_LIN(sequence_list_dir):
    ref_id = '2022-07-03_08.30.21'
    phone_sequences = read_sequence_list(sequence_list_dir / 'LIN_phone.txt')
    hololens_sequences = read_sequence_list(sequence_list_dir / 'LIN_hololens.txt')
    spot_sequences = read_sequence_list(sequence_list_dir / 'LIN_spot.txt')
    return ref_id, phone_sequences, hololens_sequences, spot_sequences

def get_data_ARCHE_D2(sequence_list_dir):
    ref_id = '2023-07-13_16.10.09'
    phone_sequences = read_sequence_list(sequence_list_dir / 'ARCHE_D2_phone.txt')
    hololens_sequences = read_sequence_list(sequence_list_dir / 'ARCHE_D2_hololens.txt')
    spot_sequences = read_sequence_list(sequence_list_dir / 'ARCHE_D2_spot.txt')
    return ref_id, phone_sequences, hololens_sequences, spot_sequences

def get_data_ARCHE_B3(sequence_list_dir):
    ref_id = '2023-07-12_11.28.35+2023-07-12_13.36.16'
    phone_sequences = read_sequence_list(sequence_list_dir / 'ARCHE_B3_phone.txt')
    hololens_sequences = read_sequence_list(sequence_list_dir / 'ARCHE_B3_hololens.txt')
    spot_sequences = read_sequence_list(sequence_list_dir / 'ARCHE_B3_spot.txt')
    return ref_id, phone_sequences, hololens_sequences, spot_sequences

def get_data_ARCHE_B4(sequence_list_dir):
    ref_id = '2023-07-11_09.23.13'
    phone_sequences = read_sequence_list(sequence_list_dir / 'ARCHE_B4_phone.txt')
    hololens_sequences = read_sequence_list(sequence_list_dir / 'ARCHE_B4_hololens.txt')
    spot_sequences = read_sequence_list(sequence_list_dir / 'ARCHE_B4_spot.txt')
    return ref_id, phone_sequences, hololens_sequences, spot_sequences

def get_data_ARCHE_B5(sequence_list_dir):
    ref_id = '2023-07-11_13.29.03'
    phone_sequences = read_sequence_list(sequence_list_dir / 'ARCHE_B5_phone.txt')
    hololens_sequences = read_sequence_list(sequence_list_dir / 'ARCHE_B5_hololens.txt')
    spot_sequences = read_sequence_list(sequence_list_dir / 'ARCHE_B5_spot.txt')
    return ref_id, phone_sequences, hololens_sequences, spot_sequences

def get_data_ARCHE_GRANDE(sequence_list_dir):
    ref_id = '2023-07-12_20.16.03'
    phone_sequences = read_sequence_list(sequence_list_dir / 'ARCHE_GRANDE_phone.txt')
    hololens_sequences = read_sequence_list(sequence_list_dir / 'ARCHE_GRANDE_hololens.txt')
    spot_sequences = read_sequence_list(sequence_list_dir / 'ARCHE_GRANDE_spot.txt')
    return ref_id, phone_sequences, hololens_sequences, spot_sequences

def get_data_ARCHE_STPA(sequence_list_dir):
    ref_id = '2023-07-14_09.38.48'
    phone_sequences = read_sequence_list(sequence_list_dir / 'ARCHE_GRANDE_phone.txt')
    hololens_sequences = read_sequence_list(sequence_list_dir / 'ARCHE_GRANDE_hololens.txt')
    spot_sequences = read_sequence_list(sequence_list_dir / 'ARCHE_GRANDE_spot.txt')
    return ref_id, phone_sequences, hololens_sequences, spot_sequences

def get_data_HYDRO(sequence_list_dir):
    ref_id = '2023-11-03_10.31.58+2023-11-03_13.51.06'
    phone_sequences = read_sequence_list(sequence_list_dir / 'HYDRO_phone.txt')
    hololens_sequences = read_sequence_list(sequence_list_dir / 'HYDRO_hololens.txt')
    spot_sequences = read_sequence_list(sequence_list_dir / 'HYDRO_spot.txt')
    return ref_id, phone_sequences, hololens_sequences, spot_sequences

def get_data_SUCCULENT(sequence_list_dir):
    ref_id = '2023-12-15_12.20.33+2023-12-15_13.47.02+2023-12-15_14.52.57'
    phone_sequences = read_sequence_list(sequence_list_dir / 'SUCCULENT_phone.txt')
    hololens_sequences = read_sequence_list(sequence_list_dir / 'SUCCULENT_hololens.txt')
    spot_sequences = read_sequence_list(sequence_list_dir / 'SUCCULENT_spot.txt')
    return ref_id, phone_sequences, hololens_sequences, spot_sequences

def get_data_DESIGN(sequence_list_dir):
    ref_id = '2023-12-08_10.51.38+2023-12-08_14.01.04+2023-12-08_14.54.05'
    phone_sequences = read_sequence_list(sequence_list_dir / 'DESIGN_phone.txt')
    hololens_sequences = read_sequence_list(sequence_list_dir / 'DESIGN_hololens.txt')
    spot_sequences = read_sequence_list(sequence_list_dir / 'DESIGN_spot.txt')
    return ref_id, phone_sequences, hololens_sequences, spot_sequences

def main(args):
    scene = args.scene
    ref_id, phone_sequences, hololens_sequences, spot_sequences = eval('get_data_'+scene)(args.capture_root)
    if args.skip_phone:
        phone_sequences = []
    if args.skip_hololens:
        hololens_sequences = []
    if args.skip_spot:
        spot_sequences = []
    logger.info('Found %d phone, %d HoloLens, and %d Spot sequences in lists.',
                len(phone_sequences), len(hololens_sequences), len(spot_sequences))
    run(args.capture_root/scene, ref_id, args.phone_dir/scene, args.hololens_dir/scene, args.spot_dir/scene,
        phone_sequences, hololens_sequences, spot_sequences, args.run_lamar_splitting)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--capture_root', type=Path, default=Path('data/captures/'))
    parser.add_argument('--scene', type=str, required=True, choices=[
        'CAB', 
        'HGE', 
        'LIN', 
        'ARCHE_D2', 
        'ARCHE_B3',
        'ARCHE_B4',
        'ARCHE_B5',
        'ARCHE_GRANDE',
        'ARCHE_STPA',
        'HYDRO',
        'SUCCULENT',
        'DESIGN'])

    parser.add_argument('--phone_dir', type=Path, default=Path('BOOGLEWOOGLE'))
    parser.add_argument('--hololens_dir', type=Path, default=Path('BOOGLEWOOGLE'))
    parser.add_argument('--spot_dir', type=Path, default=Path('/BOOGLEWOOGLE'))
    parser.add_argument('--skip_phone', action='store_true')
    parser.add_argument('--skip_hololens', action='store_true')
    parser.add_argument('--skip_spot', action='store_true')
    parser.add_argument('--run_lamar_splitting', action='store_true')
    main(parser.parse_args())
