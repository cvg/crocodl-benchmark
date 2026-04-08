from lamar import logger
from lamar.tasks import CustomPipeline, CustomPipelinePaths

from scantools.capture import Capture

"""
INSTRUCTION: 

This is a template for a custom pipeline class. A custom saver class is also included.

It is highly encouraged to use this template without modifying the custom_pipeline script. 
This helps avoid repeatedly changing default classes when working with multiple pipeline methods.

To make your pipeline functional, you only need to implement the _run method. This method must 
return poses in a specific format, which is validated automatically. Pose saving is also handled 
automatically for you, you do not have to call that method yourself (have a look into 
CustomPipeline.run method).

By default, you do not need to inherit the default saver. However, the default saver only supports 
saving poses and configuration files. If you want to add additional saving functionalities or custom 
output paths, you should inherit from the default saver and implement your own version, as shown in 
this template. In that case, make sure to also override the _create_paths method.

If you prefer to use the default saver, simply remove the entire template saver class and delete the 
_create_paths method. The rest of the pipeline will work as intended.

"""

class TemplatePaths(CustomPipelinePaths):
    def __init__(self, root, config, query_id, ref_id):
        self.root = root
        self.workdir = root / 'poses' / query_id / ref_id / config['name']
        self.poses = self.workdir / 'poses.txt'
        self.config = self.workdir / 'configuration.json'
        self.matching = root / 'matching' / query_id / ref_id / config['name'] / config['matching']

    def save_poses(self, config, paths):
        """
        Method that saves poses.
        """
        logger.info('Template custom saver: Poses saved to %s.', self.poses) 
        logger.info('Template custom saver: Configuration saved to %s.', self.config)

    def save_matches(self, matches):
        """
        Method that saves matches.
        """
        logger.info('Template custom saver: Matches saved to %s.', self.matching) 

@CustomPipeline.register("Template")
class Template(CustomPipeline):

    config = {
        'name': 'Template',
        'matching': 'dummy_matcher'
    }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        return

    def _run(self, capture, ref_id, query_id, query_filename, outputs):
        """
        Custom run method for Template.
        """

        #TODO: implement template pose calculation

        logger.info('Running %s custom pipeline with config: %s', self.config['name'], self.config)
        self.paths.save_matches([])
        poses = []

        return poses

    def _create_paths(self, outputs, config, query_id, ref_id):
        self.paths = TemplatePaths(outputs, config, query_id, ref_id)
        return self.paths