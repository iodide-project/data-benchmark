import csv
import gzip
import json
import os
import hashlib
import shutil
import string
import tempfile


import numpy as np
import pandas as pd


REVERSE_LOOKUP = {}


def get_attrs_for_file(hash):
    return REVERSE_LOOKUP[hash]


def get_filename(attrs):
    digest = '{type}_{compression}_{size}.{format}'.format(**attrs)
    REVERSE_LOOKUP[digest] = attrs
    return digest


def generate_file(attrs, cache_dir):
    filename = get_filename(attrs)
    filepath = os.path.join(cache_dir, filename)
    if os.path.isfile(filepath):
        return

    print(f"Generating file for {attrs}")

    np.random.seed(0)

    data = np.random.random((attrs['size'], 26))
    data[:, 25] = np.sum(data[:, :25], axis=1)

    if attrs['type'] == 'array':
        data = data.tolist()
        with open(filepath, 'w') as fd:
            if attrs['format'] == 'csv':
                writer = csv.writer(fd)
                for row in data:
                    writer.writerow(row)
            elif attrs['format'] == 'json':
                json.dump(data, fd)

    elif attrs['type'] == 'table':
        columns = string.ascii_uppercase
        data = [
            dict((col, x) for (col, x) in zip(columns, row))
            for row in data]
        df = pd.DataFrame(data)

        with open(filepath, 'w') as fd:
            if attrs['format'] == 'csv':
                df.to_csv(fd, index=False)
            elif attrs['format'] == 'json':
                df.to_json(fd, orient='records')

    else:
        raise NotImplementedError()

    if attrs['compression'] == 'none':
        pass
    elif attrs['compression'] == 'gzip':
        with tempfile.NamedTemporaryFile(delete=False) as tmp:
            with gzip.open(tmp, 'wb') as gz:
                with open(filepath, 'rb') as fd:
                    shutil.copyfileobj(fd, gz)
        os.unlink(filepath)
        shutil.copy(tmp.name, filepath)
        os.unlink(tmp.name)
    else:
        raise NotImplementedError()


