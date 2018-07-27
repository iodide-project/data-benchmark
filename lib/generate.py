import gzip
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
    m = hashlib.sha256()
    m.update(str(attrs['size']).encode('ascii'))
    m.update(attrs['type'].encode('ascii'))
    m.update(attrs['format'].encode('ascii'))
    m.update(attrs['compression'].encode('ascii'))
    digest = m.hexdigest()[:16]
    REVERSE_LOOKUP[digest] = attrs
    return digest


def generate_file(attrs, cache_dir):
    filename = get_filename(attrs)
    filepath = os.path.join(cache_dir, filename)
    if os.path.isfile(filepath):
        return

    print(f"Generating file for {attrs}")

    np.random.seed(0)

    if attrs['type'] == 'array':
        data = np.random.random((attrs['size'], 100))
    elif attrs['type'] == 'table':
        columns = string.ascii_uppercase
        data = [
            dict((col, np.random.random()) for col in columns)
            for i in range(attrs['size'])]
    else:
        raise NotImplementedError()

    df = pd.DataFrame(data)

    with open(filepath, 'w') as fd:
        if attrs['format'] == 'csv':
            df.to_csv(fd, header=False)
        elif attrs['format'] == 'json':
            df.to_json(fd)

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


