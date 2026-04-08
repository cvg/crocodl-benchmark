import os
import shutil
import argparse
from tqdm import tqdm
from pathlib import Path

from . import logger
from .capture import Capture, Session


def copy_rel_file(rel_path, src_raw: Path, dst_raw: Path):
    """
    Copy one relative file from src_raw to dst_raw.
    """
    if rel_path is None:
        return

    rel_path = Path(str(rel_path))
    src = src_raw / rel_path

    if not src.exists():
        logger.warning(f"Missing raw file (skipping): {src}")
        return

    dst = dst_raw / rel_path
    dst.parent.mkdir(parents=True, exist_ok=True)

    if not dst.exists():
        shutil.copy2(src, dst)


def copy_raw_images_depths(session,
                           ts_chunk,
                           src_session_dir: Path,
                           dst_session_dir: Path):
    """
    Copy raw_data files referenced by images and depths
    for timestamps in ts_chunk.
    """
    src_raw = src_session_dir / Session.data_dirname
    dst_raw = dst_session_dir / Session.data_dirname

    # Collect relative paths (deduplicate)
    rel_paths = set()

    # ---- Images ----
    if session.images is not None:
        for ts in ts_chunk:
            if ts not in session.images:
                continue
            items = session.images[ts]
            if isinstance(items, dict):
                rel_paths.update(items.values())
            else:
                rel_paths.add(items)

    # ---- Depths ----
    if session.depths is not None:
        for ts in ts_chunk:
            if ts not in session.depths:
                continue
            items = session.depths[ts]
            if isinstance(items, dict):
                rel_paths.update(items.values())
            else:
                rel_paths.add(items)

    rel_paths = [p for p in rel_paths if p is not None]

    for rel in tqdm(rel_paths, desc=f"Copying raw_data (images+depths) for {session.id}", unit="file", leave=False):
        copy_rel_file(rel, src_raw, dst_raw)

def subset_like(obj, ts_keys):
    """
    Keep only timestamp keys in ts_keys (works for trajectories/images/depths).
    """
    if obj is None:
        return None

    sub = {ts: obj[ts] for ts in ts_keys if ts in obj}

    cls = obj.__class__
    if hasattr(cls, "from_dict") and callable(getattr(cls, "from_dict")):
        try:
            return cls.from_dict(sub)
        except Exception:
            pass

    try:
        return cls(sub)
    except Exception:
        return sub


def subset_rigs_by_timestamps(rigs_obj, ts_keys):
    """
    rigs keys look like: "<timestamp>-body" (string), not integer timestamps.
    Keep rigs where the prefix timestamp matches any ts in ts_keys.
    Based on rigs.txt format. 
    """
    if rigs_obj is None:
        return None

    ts_set = set(int(t) for t in ts_keys)

    sub = {}
    for rig_id in rigs_obj.keys():
        # rig_id example: "1686029631383703-body"
        try:
            ts_prefix = int(str(rig_id).split("-", 1)[0])
        except Exception:
            continue
        if ts_prefix in ts_set:
            sub[rig_id] = rigs_obj[rig_id]

    cls = rigs_obj.__class__
    if hasattr(cls, "from_dict") and callable(getattr(cls, "from_dict")):
        try:
            return cls.from_dict(sub)
        except Exception:
            pass

    try:
        return cls(sub)
    except Exception:
        return sub


def split_ts_by_duration_us(timestamps, max_session_duration_s):
    """
    timestamps are in MICROSECONDS (as in your trajectories.txt). :contentReference[oaicite:3]{index=3}
    """
    if not timestamps:
        return []

    timestamps = sorted(int(t) for t in timestamps)

    chunks = []
    start_idx = 0
    start_ts = timestamps[0]

    for i, ts in enumerate(timestamps):
        elapsed_s = (ts - start_ts) * 1e-6  # us -> seconds

        if elapsed_s >= max_session_duration_s and i > start_idx:
            chunks.append(timestamps[start_idx:i])
            start_idx = i
            start_ts = timestamps[i]

    chunks.append(timestamps[start_idx:])
    return chunks


def split_session(capture: Capture,
                  session_id: str = None,
                  max_session_duration: int = 120):

    logger.info(f"Processing session {session_id} with maximum duration of {max_session_duration}s.")
    session = capture.sessions[session_id]

    if session.trajectories is None:
        logger.warning(f"Session {session_id} has no trajectories. Skipping.")
        return []

    all_ts = sorted(session.trajectories.keys())
    if not all_ts:
        logger.warning(f"Session {session_id} has empty trajectories. Skipping.")
        return []

    chunks = split_ts_by_duration_us(all_ts, max_session_duration)
    logger.info(f"Session {session_id}: {len(all_ts)} timestamps split into {len(chunks)} sessions.")

    new_session_ids = []

    for idx, ts_chunk in enumerate(chunks):
        new_id = f"{session_id}_{idx:03d}"
        logger.info(f"Creating split session {new_id} with {len(ts_chunk)} timestamps.")

        new_session = Session(
            sensors=session.sensors,  # copy

            # split ONLY these four, but rigs needs special handling:
            rigs=subset_rigs_by_timestamps(session.rigs, ts_chunk),
            trajectories=subset_like(session.trajectories, ts_chunk),
            images=subset_like(session.images, ts_chunk),
            depths=subset_like(session.depths, ts_chunk),

            # copy the rest:
            pointclouds=session.pointclouds,
            wifi=session.wifi,
            bt=session.bt,
            proc=session.proc,
            origins=session.origins,

            id=new_id
        )

        # Save next to original session directory
        out_dir = capture.path / "sessions" / new_id
        src_dir = capture.path / "sessions" / session_id
        new_session.save(out_dir)
        copy_raw_images_depths(session, ts_chunk, src_dir, out_dir)

        new_session_ids.append(new_id)

    return new_session_ids


def run(capture_path: Path, 
        session_id: str = None,
        max_session_duration: int = 120):
    
    if session_id == None:
        spot_sessions = []
        logger.info("No session_id provided, processing all spot sessions in the capture.")
        sessions_path = capture_path / 'sessions'
        sessions = [f for f in os.listdir(sessions_path) if os.path.isdir(os.path.join(sessions_path, f))]
        for session_id in sessions:
            if "spot" in session_id:
                spot_sessions.append(session_id)
    else:
        if "spot" not in session_id:
            logger.error(f"Session {session_id} is not spot session.")
        spot_sessions = [session_id]

    capture = Capture.load(capture_path, session_ids=spot_sessions)

    output = []

    for session_id in spot_sessions:
        
        path = capture_path / 'sessions' / session_id
                
        if "map" in session_id or "query" in session_id:
            logger.info(f"Skipping session {session_id} as it is a map or query session.")
            continue

        new_sessions = split_session(capture, session_id, max_session_duration)

        output.append({
            'session_id': new_sessions
        })

    return output
            

if __name__ == '__main__':
    parser = argparse.ArgumentParser(formatter_class=argparse.ArgumentDefaultsHelpFormatter,
                                     argument_default=argparse.SUPPRESS)
    
    parser.add_argument('--capture_path', type=Path, required=True, help='Path to the Capture directory.')
    parser.add_argument('--session_id', type=str, help='ID of the session to transform timestamps. If not provided, all sessions will be processed.')
    parser.add_argument('--max_session_duration', type=int, help='Maximum length of split sessions.')

    args = parser.parse_args().__dict__
    run(**args)
