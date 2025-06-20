from pathlib import Path
from typing import List, Iterator, Tuple
from more_itertools import unique_everseen

def sort_and_prune(file_path : Path, overwrite : bool):
    data, columns = read_csv(file_path)
    data_no_redundant = list(unique_everseen(data, key=tuple))
    data_sorted = sorted(data_no_redundant, key=lambda x: int(x[0]))
    if overwrite:
        write_csv(file_path, data_sorted, columns)
    else:
        write_csv(Path(str(file_path) + '.sorted'), data_sorted, columns)


def read_csv(path: Path) -> Tuple[List[List[str]], List[str]]:
    # adapted from scantools.utils.io read_csv
    if not path.exists():
        raise IOError(f'CSV file does not exist: {path}')

    data = []
    with open(str(path), 'r') as fid:
        first_line = fid.readline().strip()
        if first_line[0] == '#':
            columns = [w.strip() for w in first_line[1:].split(',')]
        else:
            columns = None
            words = [w.strip() for w in first_line.split(',')]
            data.append(words)
        for line in fid:
            line = line.strip()
            if len(line) == 0:
                continue
            words = [w.strip() for w in line.split(',')]
            data.append(words)
    return data, columns


def write_csv(path: Path, table: Iterator[List[str]], columns: List[str]):
    # adapted from scantools.utils.io write_csv
    if not path.parent.exists():
        raise IOError(f'Parent directory does not exist: {path}')

    with open(str(path), 'w') as fid:
        if columns is not None:
            header = '#' + ' ' + ', '.join(columns) + '\n'
            fid.write(header)
        for row in table:
            data = ', '.join(row) + '\n'
            fid.write(data)
