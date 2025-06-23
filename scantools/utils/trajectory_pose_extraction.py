import numpy as np
from pathlib import Path
from scantools.capture import Capture
from scantools import logger
from scantools.utils.utils import read_csv
from scantools.utils.io import read_sequence_list

def read_pose_data(
        capture: Capture,
        session_id: str = "",
        ) -> tuple:
    """
    Reads pose data from a given capture session and session_id.

    Args:
        capture: Capture -> Capture object containing the session path
        session_id: str -> Session ID to read pose data from
    Output:
        tuple -> A tuple containing two lists:
            - quaternions: List of quaternions representing the rotation of the device
            - translations: List of translations (x, y, z) representing the position of the device
    """
    trajectories, col_trajectories = read_csv(capture.session_path(session_id) / "proc" / "alignment_trajectories.txt")

    quaternions = []
    translations = []
    
    for row in trajectories:
        try:
            # Extract quaternion (qw, qx, qy, qz) and translation (tx, ty, tz)
            qw = float(row[2])
            qx = float(row[3])
            qy = float(row[4])
            qz = float(row[5])
            
            tx = float(row[6])
            ty = float(row[7])
            tz = float(row[8])
            
            # Append to lists
            quaternions.append([qw, qx, qy, qz])
            translations.append([tx, ty, tz])

        except ValueError:
            logger.warning(f"Skipping invalid row: {row}")

    return quaternions, translations

def extract_pose_data(
        capture: Capture,
        session_id: str = "",
        ) -> dict:
    """
    Extracts pose data from a given capture session and session_id.

    Args:
        capture: Capture -> Capture object containing the session path
        session_id: str -> Session ID to extract pose data from
    Output:
        dict -> Dictionary containing the session name, rotation (quaternions) and translation (xyz) of the device
    """

    quaternions, translations = read_pose_data(capture, session_id)

    quaternions = np.array(quaternions)
    translations = np.array(translations)

    return {
        "session": session_id,
        "rotation": quaternions,
        "translation": translations
    }


def extract_pose_data_map_query(
        capture: Capture,
        map_query_id: str = "",
        session_ids: str = "",
        ) -> dict:
    """
    Extracts pose data from a given capture session and session_id.

    Args:
        capture: Capture -> Capture object containing the session path
        session_id: str -> Session ID to extract pose data from
    Output:
        dict -> Dictionary containing the session name, rotation (quaternions) and translation (xyz) of the device
    """
    quaternions = []
    translations = []

    for session_id in session_ids:
        logger.info(f"  Extracting pose data for session: {session_id}")
        
        quaternions_new, translations_new = read_pose_data(capture, session_id)

        quaternions.extend(quaternions_new)
        translations.extend(translations_new)

        logger.info(f"  Extracted pose data for session: {session_id}")

    # Convert lists to NumPy arrays
    quaternions = np.array(quaternions)
    translations = np.array(translations)

    return {
        "session": map_query_id,
        "rotation": quaternions,
        "translation": translations
    }

def read_map_query_trajectories(
        capture: Capture,
        device: str = "",
        ) -> dict:
    """
    Reads map and query trajectories for a given device.

    Args:
        capture: Capture -> Capture object containing the session path
        device: str -> Device prefix to read trajectories for (e.g., "ios", "hl", "spot")
    Output:
        dict -> Dictionary containing the map and query trajectories
    """
    session_ids_map = capture.path / Path(device + "_map.txt")
    session_ids_query = capture.path / Path(device + "_query.txt")

    session_ids = read_sequence_list(session_ids_map)
    map_trajectory = extract_pose_data_map_query(capture, device + "_map", session_ids)

    session_ids = read_sequence_list(session_ids_query)
    query_trajectory = extract_pose_data_map_query(capture, device + "_query", session_ids)

    return {
        "map": map_trajectory,
        "query": query_trajectory
    }