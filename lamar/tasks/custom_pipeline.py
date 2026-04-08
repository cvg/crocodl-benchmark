from pathlib import Path
from abc import ABC, abstractmethod 

from lamar import logger
from scantools.capture import Capture

class CustomPipelinePaths:

    def __init__(self, root, config, query_id, ref_id):
        self.root = root
        self.workdir = root / 'poses' / query_id / ref_id / config['name']
        self.poses = self.workdir / 'poses.txt'
        self.config = self.workdir / 'configuration.json'

    def save_poses(self, config, paths):
        """
        Method that saves poses.
        """
        logger.info('Default saver: Poses saved to %s.', self.poses) 
        logger.info('Default saver: Configuration saved to %s.', self.config)

class CustomPipeline(ABC):

    pipelines = {}
    config = {}
    paths = None

    def __init__(self, *args, **kwargs):
        return

    def run(self, capture, ref_id, query_id, query_filename, outputs):
        """
        Do NOT override or change this in method.
        Added such that poses are always validated and saved.
        """
        ref = capture.sessions[ref_id]
        query = capture.sessions[query_id]
        self._create_paths(outputs, self.config, query_id, ref_id)
        poses = self._run(capture, ref, query, query_filename, outputs)
        self.validate_poses(poses)
        self.paths.save_poses(self.config, poses)
        return poses

    def _create_paths(self, outputs, config, query_id, ref_id):
        self.paths = CustomPipelinePaths(outputs, self.config, query_id, ref_id)
        return self.paths

    @abstractmethod
    def _run(self, *args, **kwargs):
        """
        Subclasses implement this.
        Must return poses in correct format.
        """
        raise NotImplementedError

    @staticmethod
    def validate_poses(poses):
        """
        Pose output validation.
        """
        if poses is None:
            raise ValueError("Pipeline returned poses=None")
        if not isinstance(poses, (list, dict)):
            raise ValueError(f"Pipeline must return a list or dict of poses, got: {type(poses)}")

    @classmethod
    def register(cls, name: str):
        """
        Class decorator to register a pipeline class by name.
        """
        def decorator(pipeline_cls):
            if name in cls.pipelines:
                raise ValueError(
                    f"Pipeline '{name}' already registered "
                    f"by {cls.pipelines[name]}"
                )
            cls.pipelines[name] = pipeline_cls
            return pipeline_cls

        return decorator

    @classmethod
    def create(cls, name):
        """
        Creates an empty instance of a registered pipeline by name.
        """
        if name not in cls.pipelines:
            available = ", ".join(sorted(cls.pipelines.keys()))
            raise ValueError(f"Unknown pipeline '{name}'. Available: {available}")

        return cls.pipelines[name]()