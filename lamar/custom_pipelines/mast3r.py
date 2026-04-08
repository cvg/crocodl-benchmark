from lamar import logger
from lamar.tasks import CustomPipeline, CustomPipelinePaths

from scantools.capture import Capture

class Mast3rPaths(CustomPipelinePaths):
    def __init__(self, root, config, query_id, ref_id):
        self.root = root
        self.retrival = root / 'poses' / query_id / ref_id / config['retrival']
        self.matching = root / 'poses' / query_id / ref_id / config['name']
        self.workdir = root / 'poses' / query_id / ref_id / config['name']
        self.poses = self.workdir / 'poses.txt'
        self.config = self.workdir / 'configuration.json'
        self.matches = self.matching / 'matches.h5'
        self.matches_config = self.matching / 'configuration.json'

    def save_matches(self, matches):
        """
        Method that saves matches.
        """
        logger.info('Mast3r custom saver: Matches saved to %s.', self.matching) 

@CustomPipeline.register("Mast3r")
class Mast3r(CustomPipeline):

    config = {
        'name': 'Mast3r',
        'retrival': 'netvlad'
    }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        return

    def _run(self, capture, ref, query, query_filename, outputs):
        """
        Custom run method for Mast3r.
        """

        #TODO: implement master pose calculation


        logger.info('Running %s custom pipeline with config: %s', self.config['name'], self.config)
        self.paths.save_matches([])
        poses = []

        return poses

    def _create_paths(self, outputs, config, query_id, ref_id):
        self.paths = Mast3rPaths(outputs, config, query_id, ref_id)
        return self.paths