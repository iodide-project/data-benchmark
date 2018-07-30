import csv
import gzip
import json
import os
import shutil
import string
import tempfile


import numpy as np
import pandas as pd
import pyarrow as pa


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

    open_mode = 'w'
    if attrs['format'] == 'arrow':
        open_mode = 'wb'

    if attrs['type'] == 'array':
        with open(filepath, open_mode) as fd:
            if attrs['format'] == 'csv':
                writer = csv.writer(fd)
                for row in data.tolist():
                    writer.writerow(row)
            elif attrs['format'] == 'json':
                json.dump(data.tolist(), fd)
            elif attrs['format'] == 'arrow':
                raise NotImplementedError()

    elif attrs['type'] == 'table':
        columns = string.ascii_uppercase
        data = [
            dict((col, x) for (col, x) in zip(columns, row))
            for row in data]
        df = pd.DataFrame(data)

        with open(filepath, open_mode) as fd:
            if attrs['format'] == 'csv':
                df.to_csv(fd, index=False)
            elif attrs['format'] == 'json':
                df.to_json(fd, orient='records')
            elif attrs['format'] == 'arrow':
                batch = pa.RecordBatch.from_pandas(df, preserve_index=False)
                writer = pa.RecordBatchStreamWriter(fd, batch.schema)
                writer.write_batch(batch)
                writer.close()

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


