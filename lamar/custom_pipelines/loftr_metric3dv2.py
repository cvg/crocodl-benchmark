from lamar import logger
from lamar.tasks import CustomPipeline, CustomPipelinePaths

@CustomPipeline.register("LoFTRMetric3Dv2")
class LoFTRMetric3Dv2(CustomPipeline):

    config = {
        'name': 'LoFTRMetric3Dv2',
    }

    def __init__(self, *args, **kwargs):
        super().__init__()
        return

    def _run(self, capture, ref_id, query_id, query_filename, outputs):
        """
        Custom run method for LoFTRMetric3Dv2.
        """

        #TODO: implement LoFTR + Metric3Dv2 pose calculation

        logger.info('Running %s custom pipeline with config: %s', self.config['name'], self.config)
        poses = []

        return poses

