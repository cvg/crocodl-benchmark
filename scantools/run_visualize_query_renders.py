import argparse
import copy
from tqdm import tqdm
import numpy as np
import os
import matplotlib.pyplot as plt
from pathlib import Path

from . import logger
from .capture import Capture

from .proc.rendering import Renderer
from .utils.io import read_mesh, read_image
from pipelines.pipeline_sequence import *


def get_ref(capture: Capture, simplified_mesh: bool):

    clean_path = str(capture.path).rstrip('/')
    base_path = Path(os.path.dirname(clean_path))
    location = os.path.basename(clean_path)
    ref_id, _, _, _ = eval('get_data_' + location)(base_path)

    session_ref = capture.sessions[ref_id]
    T_mesh2global = session_ref.proc.alignment_global.get_abs_pose('pose_graph_optimized')
    if simplified_mesh:
        mesh = read_mesh(capture.proc_path(ref_id) / session_ref.proc.meshes['mesh_simplified'])
    else:
        mesh = read_mesh(capture.proc_path(ref_id) / session_ref.proc.meshes['mesh'])

    renderer = Renderer(mesh)

    return renderer, T_mesh2global


def read_raw_image(cam_id, data_path, images):
    if cam_id not in images:
        # It's a rig. Pick first camera.
        cam_id = list(sorted(images.keys()))[0]
    return read_image(data_path / images[cam_id])


def render_image(cam_id, T, images, cameras, renderer, rig=None):
    T = copy.deepcopy(T)
    if cam_id not in images:
        # It's a rig. Pick first camera.
        cam_id = list(sorted(images.keys()))[0]
        T_cam2rig = rig[cam_id]
        T = T * T_cam2rig
    camera = cameras[cam_id]
    render, _ = renderer.render_from_capture(T, camera)
    render = (np.clip(render, 0, 1) * 255).astype(np.uint8)
    return render

def create_mask(width, height):
    mask = np.fromfunction(lambda i, j: j < (width - 1) - i * (width / height), (height, width), dtype=int)
    return np.stack([mask] * 3, axis=-1)

def visualize_render_overlap(image_raw, image_render, save_path):
    mask = create_mask(image_raw.shape[1], image_raw.shape[0])
    combined = np.where(mask, image_raw, image_render)
    plt.imshow(combined)
    plt.axis('off')
    plt.savefig(save_path, bbox_inches='tight', pad_inches=0)

def run(capture: Capture, skip: int, simplified_mesh: bool):

    renderer, T_mesh2global = get_ref(capture, simplified_mesh)

    for query in ['spot_query', 'ios_query', 'hl_query']:
        
        if not os.path.isdir(capture.sessions_path() / query):
            logger.info(f"Query {query} does not exist. Skipping.")

        logger.info(f"Working on rendering keyframes of {query}.")

        session_q = capture.sessions[query]
        trajectory = session_q.proc.alignment_trajectories
        keys = list(sorted(trajectory.key_pairs()))
        keys = keys[::skip]
        if T_mesh2global is not None:
            trajectory = T_mesh2global.inv() * trajectory

        for ts, cam_id in tqdm(keys, desc=f"Rendering cameras for {query}"):

            if session_q.rigs is not None:
                rig = (session_q.rigs[cam_id] if cam_id in session_q.rigs else None)
            else:
                rig = None

            image_render = render_image(
                cam_id, trajectory[ts, cam_id], session_q.images[ts], session_q.sensors,
                renderer, rig
            )

            image_raw = read_raw_image(cam_id, capture.data_path(query), session_q.images[ts])

            image_name = cam_id.replace('/', '_').replace('\\', '_')
            save_path = capture.viz_path() / Path(query + '_renders') / Path(f"{image_name}.png")
            save_path.parent.mkdir(parents=True, exist_ok=True)
            visualize_render_overlap(image_raw, image_render, save_path)

        logger.info(f"Done rendering keyframes of {query}.")

if __name__ == '__main__':
    parser = argparse.ArgumentParser(formatter_class=argparse.ArgumentDefaultsHelpFormatter,
                                     argument_default=argparse.SUPPRESS)
    
    parser.add_argument('--capture_path', type=Path, required=True)
    parser.add_argument('--skip', type=int, default=10)
    parser.add_argument("--simplified_mesh", action="store_true", help="Use simplified mesh")
    
    args = parser.parse_args().__dict__
    args['capture'] = Capture.load(args.pop('capture_path'))

    run(**args)
