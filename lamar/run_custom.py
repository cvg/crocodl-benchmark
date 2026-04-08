import argparse

from pprint import pformat
from pathlib import Path

from lamar import logger
from lamar.tasks import CustomPipeline

from scantools.capture import Capture

def run(outputs: Path,
        capture: Capture,
        ref_id: str,
        query_id: str,
        pipeline: str,
        query_filename: str = 'keyframes_original.txt'):

    pipeline = CustomPipeline.create(name=pipeline)
    results = pipeline.run(capture, ref_id, query_id, query_filename, outputs)

    #TODO: implement calculating results

    return results

if __name__ == '__main__':
    parser = argparse.ArgumentParser(formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument(
        '--ref_id', type=str, required=True)
    parser.add_argument(
        '--query_id', type=str, required=True)
    parser.add_argument(
        '--captures', type=Path, default=Path("./data/"), help="Path to captures directory")
    parser.add_argument(
        '--outputs', type=Path, default=Path("./outputs/"), help="Path to outputs directory")
    parser.add_argument(
        '--pipeline', type=str, required=True, choices=list(CustomPipeline.pipelines))
    parser.add_argument(
        '--query_filename', type=str, 
        choices=['keyframes_original.txt', 'keyframes_pruned.txt', 'keyframes_pruned_subsampled.txt'],
        default='keyframes_original.txt')

    args = parser.parse_args().__dict__
    args['capture'] = Capture.load(args.pop('captures'))
    results_ = run(**args)

    if isinstance(results_, str):
        logger.info('%s is a test sequence. Submit %s to the benchmark to obtain the results.',
                    args['query_id'], results_)
    else:
        logger.info('Results:\n%s', pformat(results_))


