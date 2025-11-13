import os
import shutil
# from .extract_map import extract_map
from .extract_query import extract_query


def copy_map(session_dir, map_endpoint_dir, symlinks=True):
    os.makedirs(map_endpoint_dir, exist_ok=True)
    shutil.copytree(session_dir, map_endpoint_dir,
                    dirs_exist_ok=True,
                    symlinks=symlinks)

def extract_location(location_dir, endpoint_dir, map_ep, query_ep):
    location_dir = os.path.join(location_dir, "sessions")
    endpoint_dir = os.path.join(endpoint_dir, "sessions")
    
    sessions = sorted(os.listdir(location_dir))
    for session in sessions:
        if session.endswith('_query'): continue
        
        session_dir = os.path.join(location_dir, session)
        map_endpoint_dir = os.path.join(endpoint_dir, session)
        query_endpoint_dir = os.path.join(endpoint_dir, f"{session.split('_')[0]}_query")
        
        # extract_map(session_dir, map_endpoint_dir, ext_percent=map_ep)
        copy_map(session_dir, map_endpoint_dir, symlinks=True)
        
        extract_query(map_endpoint_dir, query_endpoint_dir, ext_percent=query_ep)