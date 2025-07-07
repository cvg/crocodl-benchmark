import sys
import os

def find_recall_lines(file_path):
    if not os.path.isfile(file_path):
        print(f"Error: File '{file_path}' not found.")
        return

    with open(file_path, 'r') as file:
        lines = file.readlines()

    for i, line in enumerate(lines):
        if 'recall' in line.lower():
            print(line.strip())
            if i + 1 < len(lines):
                print(lines[i + 1].strip())
            print('-' * 40)

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python find_recall_lines.py <path_to_text_file>")
    else:
        file_path = sys.argv[1]
        find_recall_lines(file_path)
