import itertools
import json
import os
import shutil
import subprocess

import pandas as pd

import generate
import runner
import server


DIMENSIONS = {
    # 'size': [10, 100, 1000, 10000, 100000, 1000000, 10000000, 100000000],
    'size': [10000000],
    'type': ['array', 'table'],
    'format': ['csv', 'json', 'arrow'],
    'compression': ['none', 'gzip'],
    'browser': ['chrome']
}


RESULT_COLUMNS = [
    'runtime',
    'mem',
    'nbytes',
    'niter'
]


def call_for_product(func, args, dimensions):
    dimensions = sorted(dimensions.items())

    for prod in itertools.product(*(x[1] for x in dimensions)):
        attrs = dict((dim[0], p) for dim, p in zip(dimensions, prod))
        if attrs['format'] == 'arrow' and attrs['type'] == 'array':
            continue
        if attrs['size'] > 1000000 and attrs['format'] != 'arrow':
            continue
        func(attrs, *args)


def main():
    # Create a cache directory here where resources will be served from
    cache_dir = './.cache'
    if not os.path.isdir(cache_dir):
        os.makedirs(cache_dir)

    # Build and install the Javascript side of things 
    webapp_dir = os.path.join(os.path.dirname(__file__), '..', 'webapp')
    # subprocess.run(['npm', 'install'], cwd=webapp_dir)
    subprocess.run(['npm', 'run', 'build'], cwd=webapp_dir)
    bundle_dir = os.path.join(webapp_dir, 'dist')
    for filename in os.listdir(bundle_dir):
        shutil.copy(os.path.join(bundle_dir, filename), cache_dir)

    # Generate the source data files
    call_for_product(generate.generate_file, (cache_dir,), DIMENSIONS)

    # Start serving files in another process
    port = server.spawn_web_server(cache_dir)

    # Run the benchmarks and collect the results
    if os.path.isfile('results.json'):
        with open('results.json', 'r') as fd:
            results = json.load(fd)
    else:
        results = []
    call_for_product(
        runner.run_benchmark, (cache_dir, results, port), DIMENSIONS)
    with open('results.json', 'w') as fd:
        json.dump(results, fd)
