import open3d as o3d
import numpy as np
from scipy.spatial.transform import Rotation as R
from collections import defaultdict

def read_poses(file_path):
    poses = []
    with open(file_path, 'r', encoding='utf-8') as f:
        for line in f:
            if line.startswith("#"): continue
            line = line.strip().split(", ")
            
            q = {
                'w': float(line[2]),
                'x': float(line[3]),
                'y': float(line[4]),
                'z': float(line[5]),
            }
            t = {
                'x': float(line[6]),
                'y': float(line[7]),
                'z': float(line[8]),
            }
            covar = np.array(line[9:], dtype=float)
            
            poses.append({
                'timestamp': line[0],
                'device_id': line[1],
                'q': q,
                't': t,
                'covar': covar
            })
    return poses

def read_rigs(file_path=None):
    if file_path is None:
        q = {'x': 0.0, 'y': 0.0, 'z': 0.0, 'w': 1.0}
        t = {'x': 0.0, 'y': 0.0, 'z': 0.0}
        return {
            'rig_sensors': {
                'q': q,
                't': t,
            }
        }
    rigs = defaultdict(dict)
    with open(file_path, 'r', encoding='utf-8') as f:
        for line in f:
            if line.startswith("#"): continue
            line = line.strip().split(", ")
            
            rig_id = line[0]
            sensor_id = line[1]
            q = {
                'w': float(line[2]),
                'x': float(line[3]),
                'y': float(line[4]),
                'z': float(line[5]),
            }
            t = {
                'x': float(line[6]),
                'y': float(line[7]),
                'z': float(line[8]),
            }
            
            rigs[rig_id][sensor_id] = {
                'q': q,
                't': t,
            }
    return rigs

def read_sensors(file_path):
    sensors = defaultdict(dict)
    with open(file_path, 'r', encoding='utf-8') as f:
        for line in f:
            if line.startswith("#"): continue
            line = line.strip().split(", ")
            if len(line) < 6: continue
            
            sensor_id = line[0]
            width, height = line[4:6]
            fx, fy, cx, cy = line[6:]
            K = np.array([
                [fx, 0, cx],
                [0, fy, cy],
                [0, 0, 1],
            ], dtype=float)
            
            sensors[sensor_id] = {
                'K': K,
                'width': int(width),
                'height': int(height),
            }
    return sensors

def load_poses(poses_path, sensors_path, rigs_path=None, len=None, color=[255, 255, 255]):
    poses = read_poses(poses_path)
    sensors = read_sensors(sensors_path)
    rigs = read_rigs(rigs_path)
    
    if len is not None:
        poses = poses[:len]
    
    for pose in poses:
        pose['color'] = color
        
        if "rig_sensors" in rigs: # ios
            pose['rig_sensors'] = rigs
            pose['rig_sensors']['rig_sensors'] = {
                    **pose['rig_sensors']['rig_sensors'],
                    **sensors[pose['device_id']]
                }
        else:
            pose['rig_sensors'] = rigs[pose['device_id']]
            for sensor_id in pose['rig_sensors']:
                pose['rig_sensors'][sensor_id] = {
                    **pose['rig_sensors'][sensor_id],
                    **sensors[sensor_id]
                }
    
    return poses
    

class CamPoseVisualizer():
    def __init__(self, scale = 0.01):
        self.scale = scale
        self.vis = o3d.visualization.Visualizer()
    
    def get_pose_matrix(self, q, t):
        q_xyzw = np.array([q['x'], q['y'], q['z'], q['w']])
        pose = np.eye(4)
        pose[:3, :3] = R.from_quat(q_xyzw).as_matrix()
        pose[:3, 3] = np.array([t['x'], t['y'], t['z']])
        return pose
    
    def get_T_from_pose_matrix(self, pose_matrix):
        return pose_matrix[:3, 3]

    def get_Q_from_pose_matrix(self, pose_matrix):
        return pose_matrix[:3, :3]
    
    def plot_cam_frustum(self, K, width, height, color=[255, 255, 255]):
        # 1. Image corner pixel coordinates (in homogeneous form)
        corners_px = np.array([
            [0,     0,      1],  # top-left
            [width, 0,      1],  # top-right
            [width, height, 1],  # bottom-right
            [0,     height, 1]   # bottom-left
        ]).T  # shape (3, 4)

        # 2. Backproject to normalized 3D rays
        K_inv = np.linalg.inv(K)
        rays = K_inv @ corners_px
        rays /= rays[2, :]  # normalize so z=1
        rays *= self.scale       # scale to desired depth

        # 3. Camera center
        cam_center = np.zeros((3, 1))  # (3, 1)

        # 4. All points: cam center + 4 corners
        points = np.hstack((cam_center, rays))  # shape (3, 5)
        points = points.T  # shape (5, 3)

        # 5. Define lines: from center to corners, and corners to each other
        lines = [
            [0, 1], [0, 2], [0, 3], [0, 4],  # camera center to corners
            [1, 2], [2, 3], [3, 4], [4, 1]   # image plane rectangle
        ]

        # 6. Colors for each line
        colors = [color for _ in lines]

        # 7. Create Open3D LineSet
        line_set = o3d.geometry.LineSet(
            points=o3d.utility.Vector3dVector(points),
            lines=o3d.utility.Vector2iVector(lines)
        )
        line_set.colors = o3d.utility.Vector3dVector(colors)

        return line_set
    
    def visualize_rig(self, rig_pose, cam_poses, color=[1, 0, 0]):
        rig_origin = self.get_T_from_pose_matrix(rig_pose) # T
        cam_origins = [
            self.get_T_from_pose_matrix(cam_pose) 
            for cam_pose in cam_poses
        ]
        
        points = [rig_origin] + cam_origins
        colors = [color] + [color] * len(cam_origins)

        pc = o3d.geometry.PointCloud()
        pc.points = o3d.utility.Vector3dVector(points)
        pc.colors = o3d.utility.Vector3dVector(colors)

        lines = [[0, i] for i in range(1, len(points))]
        line_set = o3d.geometry.LineSet()
        line_set.points = o3d.utility.Vector3dVector(points)
        line_set.lines = o3d.utility.Vector2iVector(lines)
        line_set.colors = o3d.utility.Vector3dVector([color] * len(lines))
        self.vis.add_geometry(line_set)
        self.vis.add_geometry(pc)
    
    def visualize(self, poses):
        """
        poses = [
            {   
                'color': [r, g, b]
                'timestamp': "...",
                'device_id': "..."
                'q': {'x', 'y', 'z', 'w'},
                't': {'x', 'y', 'z'},
                'covar': [...]
                'rig_sensors': {
                    "<sensor_id>": {
                        'q': {'x', 'y', 'z', 'w'},  => in 'rigs.txt', depend on '<sensor_id>' & 'device_id'
                        't': {'x', 'y', 'z'},       => in 'rigs.txt', depend on '<sensor_id>' & 'device_id'
                        'K': [],        => in 'sensors.txt'
                        'width': ...,   => in 'sensors.txt'
                        'height': ...,  => in 'sensors.txt'
                    },
                    ...
                }
            }
            ...
        ]
        """
        
        self.vis.create_window()
        for pose in poses:
            rig_pose = self.get_pose_matrix(pose['q'], pose['t'])
            
            cam_poses = []
            for sensor_id, sensor_info in pose["rig_sensors"].items():
                cam_pose_rig = self.get_pose_matrix(sensor_info['q'], sensor_info['t'])
                cam_pose_world = rig_pose @ cam_pose_rig
                
                cam_poses.append(cam_pose_world)
                
                frustum = self.plot_cam_frustum(
                    K=sensor_info['K'],
                    width=sensor_info['width'],
                    height=sensor_info['height'],
                    color=pose['color']
                )
                frustum.transform(cam_pose_world)
                self.vis.add_geometry(frustum)
                
            self.visualize_rig(rig_pose, cam_poses, pose['color'])
        
        opt = self.vis.get_render_option()
        opt.line_width = 10
        opt.background_color = np.array([0, 0, 0])
        axis = o3d.geometry.TriangleMesh.create_coordinate_frame(size=1)
        self.vis.add_geometry(axis)
        self.vis.run()
        self.vis.clear_geometries()
        self.vis.destroy_window()
    
def load_gt_and_est_poses(est_poses_path, gt_poses_path, sensors_path, rigs_path=None, est_color=[255, 0, 0], gt_color=[0, 255, 0]):
    est_poses = load_poses(est_poses_path, sensors_path, rigs_path=rigs_path, color=est_color)
    est_timestamps = set([item['timestamp'] for item in est_poses])
    
    gt_poses = load_poses(gt_poses_path, sensors_path, rigs_path=rigs_path, color=gt_color)   
    gt_timestamps = set([item['timestamp'] for item in gt_poses])
    
    matched_timestamps = est_timestamps & gt_timestamps
    
    est_poses = [pose for pose in est_poses if pose['timestamp'] in matched_timestamps]
    gt_poses = [pose for pose in gt_poses if pose['timestamp'] in matched_timestamps]
    
    return est_poses, gt_poses
        
if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='Visualize multiple query-map pairs with color differentiation')
    parser.add_argument('--pair', action='append', nargs='+',
                        help='Query Map GT_poses EST_poses Sensors [Rigs]')
    parser.add_argument('--scale', type=float, default=0.1)
    parser.add_argument('--max_poses', type=int, default=None)
    
    args = parser.parse_args()
    
    if not args.pair:
        print("Error: No device pairs specified")
        exit(1)
    
    # Color palette: device colors (GT lighter, EST darker)
    device_colors = {
        'ios': ([100, 255, 100], [0, 180, 0]),      # Green shades
        'hl':  ([100, 100, 255], [0, 0, 180]),      # Blue shades
        'spot': ([255, 100, 100], [180, 0, 0]),     # Red shades
    }
    
    all_poses = []
    
    for pair_args in args.pair:
        query, map_dev = pair_args[0], pair_args[1]
        gt_file, est_file, sensors_file = pair_args[2], pair_args[3], pair_args[4]
        rigs_file = pair_args[5] if len(pair_args) > 5 and pair_args[5] else None
        
        gt_color, est_color = device_colors.get(query, ([150, 150, 150], [100, 100, 100]))
        
        print(f"Loading {query}->{map_dev}: GT{gt_color} EST{est_color}")
        
        est_poses, gt_poses = load_gt_and_est_poses(
            est_poses_path=est_file,
            gt_poses_path=gt_file,
            sensors_path=sensors_file,
            rigs_path=rigs_file,
            est_color=est_color,
            gt_color=gt_color
        )
        
        if args.max_poses:
            est_poses = est_poses[:args.max_poses]
            gt_poses = gt_poses[:args.max_poses]
        
        print(f"  Loaded {len(est_poses)} est, {len(gt_poses)} gt poses")
        all_poses.extend(est_poses + gt_poses)
    
    print(f"\nTotal poses: {len(all_poses)}")
    print("Controls: Mouse=Rotate, Scroll=Zoom, Shift+Mouse=Pan, Q=Quit\n")
    
    visualizer = CamPoseVisualizer(scale=args.scale)
    visualizer.visualize(all_poses)