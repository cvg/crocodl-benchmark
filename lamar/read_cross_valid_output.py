import re
import os
import ast
import argparse
from pathlib import Path
from collections import defaultdict

def show_matrix(results, matrix="recall"):
    # Get all labels
    labels = list(results.keys())

    # Print header
    print(f"{'':>10}", end=' ')
    for col in list(results[labels[0]].keys()):
        print(f"{col:>10}", end=' ')
    print()

    # Print rows
    for row in labels:
        print(f"{row:>10}", end=' ')
        for col in list(results[labels[0]].keys()):
            value = results[row][col][matrix]
            print(f"{value:10.4f}", end=' ')
        print()

def find_rotation_lines(
        file_path: Path,
        conf_matrix: str = "recall"  
    ):
    """
    Reads input file, finds rotation lines, and if conf_matrix flag is set, prints out confusion matrices.
    """
    if not os.path.isfile(file_path):
        print(f"Error: File '{file_path}' not found.")
        return

    with open(file_path, 'r') as file:
        lines = file.readlines()

    results = defaultdict(lambda: defaultdict(lambda: defaultdict(float)))
    for i, line in enumerate(lines):
        parts = line.strip().split(" ")
        if parts[0] in ["Rotation", "Translation", "Recall"]:
            R_type = parts[1]
            query_id, map_id = parts[2].split("-")
            value = float(parts[-1])
            results[query_id][map_id][R_type] = value

    if conf_matrix:
        show_matrix(results, conf_matrix)

    return results

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Find and analyze recall lines in a log file.")
    parser.add_argument("--file_path", type=Path, help="Path to the input text file")
    parser.add_argument('--conf_matrix', type=str, help="Set this flag to print confusion matrix", default=False)

    args = parser.parse_args().__dict__

    find_rotation_lines(**args)

