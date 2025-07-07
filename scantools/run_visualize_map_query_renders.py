import argparse
import copy
import cv2
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

from concurrent.futures import ThreadPoolExecutor

from scantools.run_map_query_split_manual import (
    quaternion_and_translation_to_matrix
)

def get_ref(capture: Capture, simplified_mesh: bool):
    """
    Reads reference NavVis scan mesh and global transformation given the scene.
    Use simplified mesh to avoid OEM issues.
    """

    clean_path = str(capture.path).rstrip('/')
    base_path = Path(os.path.dirname(clean_path))
    location = os.path.basename(clean_path)
    # from pipeline_sequence where ref_ids are hardcoded
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
    """
    Reads raw image of the session specified in data_path.
    """
    if cam_id not in images:
        # It's a rig. Pick first camera.
        cam_id = list(sorted(images.keys()))[0]
    return read_image(data_path / images[cam_id])


def render_image(cam_id, T, images, cameras, renderer, rig=None):
    """
    Renders and image using the GT mesh and the pose of the camera wanted.
    """
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

def save_render_video(images_path, video_path, skip):
    """
    Saves rendered images into a video.
    """
    os.makedirs(os.path.dirname(video_path), exist_ok=True)

    images = [img for img in os.listdir(images_path) if img.endswith(".png")]
    images.sort() 

    frame = cv2.imread(os.path.join(images_path, images[0]))
    height, width, layers = frame.shape

    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    video = cv2.VideoWriter(video_path, fourcc, int(30 / skip), (width, height))

    for image in images:
        frame = cv2.imread(os.path.join(images_path, image))
        video.write(frame)

    video.release()
    logger.info(f"Video saved to {video_path}")

def create_mask(width, height):
    """
    Creates RGB mask for raw_image/rendered_image comparison. This mask is triangular.
    """
    mask = np.fromfunction(lambda i, j: j < (width - 1) - i * (width / height), (height, width), dtype=int)
    return np.stack([mask] * 3, axis=-1)

def visualize_render_overlap(image_raw, image_render, save_path):
    """
    Uses mask calculated using create_mask to plot a comparison between image_raw and image_render.
    """
    mask = create_mask(image_raw.shape[1], image_raw.shape[0])
    combined = np.where(mask, image_raw, image_render)
    plt.imsave(save_path, combined)

def process_camera(capture, renderer, query, trajectory, session_q, ts, cam_id):
    """
    Do processing of a single camera. Render image, read raw and visualize overlap.
    """
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
    save_path = capture.viz_path() / Path('renders') / Path(query + '_renders') / Path(f"{image_name}.png")
    save_path.parent.mkdir(parents=True, exist_ok=True)
    visualize_render_overlap(image_raw, image_render, save_path)

def process_camera_wrapper(args):
    """
    Wrapper of process_camera(*args) to use with multithreading execution.
    """
    capture, renderer, query, trajectory, session_q, ts, cam_id = args
    return process_camera(capture, renderer, query, trajectory, session_q, ts, cam_id)

def run(capture: Capture, skip: int, simplified_mesh: bool, save_video: bool, num_workers: int):
    """
    Plots alignment comparison between rendered image and raw images for each image in the map/query sessions for all devices.
    Use skip argument to subsample number of images. Generally, map/query sessions have 1000-1500k images.
    """

    logger.info(f"Working on rendering with {num_workers} workers.")

    renderer, T_mesh2global = get_ref(capture, simplified_mesh)

    for query in ['spot_map', 'ios_map', 'hl_map', 'spot_query', 'ios_query', 'hl_query']:
        
        if not os.path.isdir(capture.sessions_path() / query):
            logger.info(f"Query {query} does not exist. Skipping.")

        logger.info(f"Working on rendering keyframes of {query}.")

        session_q = capture.sessions[query]

        if "map" in query:
            trajectory = session_q.trajectories

        if "query" in query:
            trajectory = session_q.proc.alignment_trajectories

        keys = list(sorted(trajectory.key_pairs()))
        keys = keys[::skip]

        if T_mesh2global is not None:
            trajectory = T_mesh2global.inv * trajectory

        arg_list = [
            (capture, renderer, query, trajectory, session_q, ts, cam_id)
            for ts, cam_id in keys
        ]

        with ThreadPoolExecutor(max_workers=num_workers) as executor:
            list(tqdm(executor.map(process_camera_wrapper, arg_list), total=len(arg_list), desc=f"Rendering cameras for {query}"))

        if save_video:
            images_path = capture.viz_path() / Path('renders') / Path(query + '_renders')
            video_path = capture.viz_path() / Path('render_videos') / Path(query + '.mp4')
            save_render_video(images_path, video_path, skip)

        logger.info(f"Done rendering keyframes of {query}.")

if __name__ == '__main__':
    parser = argparse.ArgumentParser(formatter_class=argparse.ArgumentDefaultsHelpFormatter,
                                     argument_default=argparse.SUPPRESS)
    
    parser.add_argument('--capture_path', type=Path, required=True, help="Capture path of the location to process.")
    parser.add_argument('--skip', type=int, default=10, help="Subsampling factor for images.")
    parser.add_argument('--num_workers', type=int, default=4, help="How many parallel threads to use.")
    parser.add_argument('--simplified_mesh', action="store_true", help="Use simplified mesh.", default=False)
    parser.add_argument('--save_video', action="store_true", help="Set this flag to save a video.", default=False)

    
    args = parser.parse_args().__dict__
    args['capture'] = Capture.load(args.pop('capture_path'))

    run(**args)
