import re
import os
import ast
import argparse
from pathlib import Path

def parse_id(line):
    """
    Extract ref_id and query_id from a line.
    """
    parts = line.strip().split()
    ref_id, query_id = None, None
    for part in parts:
        if part.startswith('ref_id='):
            ref_id = part.split('=')[1]
        elif part.startswith('query_id='):
            query_id = part.split('=')[1]
    return ref_id, query_id

def parse_config_and_recall(recall_line, config_line):
    """
    Extract config and recall values form a recall and config lines.
    """
    actual_line = None
    if 'Rt_thresholds' in recall_line:
        actual_line = recall_line
    if 'Rt_thresholds' in config_line:
        actual_line = config_line + ' ' + recall_line

    try:
        data = ast.literal_eval(actual_line)
        return data['Rt_thresholds'], data['recall']
    except Exception as e:
        print(f"Failed to parse: {e}")
        return None
    
def group_by_config(results):
    """
    Groups list of results dictionaries into dictionaries that share the same configs.
    """

    grouped_results = {}

    for result in results:
        r = result['r']
        t = result['t']
        config = (r, t)

        entry = {
            'recall': result['recall'],
            'ref_id': result['ref_id'],
            'query_id': result['query_id']
        }

        if config not in grouped_results:
            grouped_results[config] = []

        grouped_results[config].append(entry)

    return grouped_results

def build_confusion_mat(results_dict):
    """
    Using grouped results_dict creates confusion matrices list.
    """
    
    results = results_dict['results']
    queries = results_dict['queries']

    confusion_matrices = []

    grouped_results = group_by_config(results)
    
    for config in grouped_results.keys():

        new_matrix = []

        for element in grouped_results[config]:
            new_matrix.append(element)

        confusion_matrices.append({
            'config': config,
            'queries': queries,
            'confusion_matrix': new_matrix
        })

    return confusion_matrices

def print_confusion_mat(confusion_mat):
    """
    Using confusion matrix list, prints out recall values or None for non existing ones.
    """
    queries = ['spot_query', 'ios_query', 'hl_query']
    refs = ['spot_map', 'ios_map', 'hl_map']
    recall_lookup = {(d['ref_id'], d['query_id']): d['recall'] for d in confusion_mat}

    print(f"{'':<12}", end='')
    for ref in refs:
        print(f"{ref:<12}", end='')
    print()

    for query in queries:
        print(f"{query:<12}", end='')
        for ref in refs:
            recall = recall_lookup.get((ref, query), 'None')
            print(f"{recall:<12}", end='')
        print()

def find_recall_lines(
        file_path: Path,
        conf_matrix: bool = True    
    ):
    """
    Reads input file, finds recall lines, and if conf_matrix flag is set, prints out confusion matrices.
    """
    if not os.path.isfile(file_path):
        print(f"Error: File '{file_path}' not found.")
        return

    with open(file_path, 'r') as file:
        lines = file.readlines()

    results = []
    new_results = []

    for i, line in enumerate(lines):
        queries = ''
        if 'queries file' in line.lower():
            match = re.search(r'queries file:\s*(\S+)', line)
            if match:
                queries = match.group(1)
            if new_results != []:
                results.append({
                    'results': new_results,
                    'queries': queries,
                })
                new_results = []

        if 'recall' in line.lower():
            config_line = lines[i - 1].strip() if i > 0 else "unknown_config"
            recall_line = line.strip()
            info_line = lines[i + 1].strip() if i + 1 < len(lines) else ""

            ref_id, query_id = parse_id(info_line)
            configs, recalls = parse_config_and_recall(recall_line, config_line)

            for config, recall in zip(configs, recalls):
                new_result = {
                    'ref_id': ref_id,
                    'query_id': query_id,
                    'recall': round(recall, 3),
                    'r': config[0],
                    't': config[1]
                }
                print(new_result)
                new_results.append(new_result)

    results.append({
                    'results': new_results,
                    'queries': queries,
                })

    if conf_matrix:
        confusion_matrices = []
        for result in results:
            if result == [] or result == None:
                continue
            else:
                confusion_matrices.extend(build_confusion_mat(result))

        print()
        for conf_mat in confusion_matrices:
            print(f'----------------- {conf_mat["config"]} | {conf_mat["queries"]} -----------------')
            print_confusion_mat(conf_mat['confusion_matrix'])
            print()

    return results

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Find and analyze recall lines in a log file.")
    parser.add_argument("--file_path", type=Path, help="Path to the input text file")
    parser.add_argument('--conf_matrix', action="store_true", help="Set this flag to print confusion matrix", default=False)

    args = parser.parse_args().__dict__

    find_recall_lines(**args)

