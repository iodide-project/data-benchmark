import itertools
import os
import shutil
import subprocess

import pandas as pd

import generate
import runner
import server


DIMENSIONS = {
    'size': [10, 100, 1000],
    'type': ['array', 'table'],
    'format': ['csv', 'json'],
    'compression': ['none', 'gzip'],
    'browser': ['firefox', 'chrome']
}


def call_for_product(func, args, dimensions):
    dimensions = sorted(dimensions.items())

    for prod in itertools.product(*(x[1] for x in dimensions)):
        attrs = dict((dim[0], p) for dim, p in zip(dimensions, prod))
        func(attrs, *args)


def main():
    cache_dir = './.cache'
    if not os.path.isdir(cache_dir):
        os.makedirs(cache_dir)

    webapp_dir = os.path.join(os.path.dirname(__file__), '..', 'webapp')
    subprocess.run(['npm', 'install'], cwd=webapp_dir)
    subprocess.run(['npm', 'run', 'build'], cwd=webapp_dir)
    bundle_dir = os.path.join(webapp_dir, 'dist')
    for filename in os.listdir(bundle_dir):
        shutil.copy(os.path.join(bundle_dir, filename), cache_dir)

    call_for_product(generate.generate_file, (cache_dir,), DIMENSIONS)

    port = server.spawn_web_server(cache_dir)

    columns = list(DIMENSIONS.keys()) + ['nbytes', 'runtime', 'mem']
    if os.path.isfile('results.json'):
        results = pd.read_json('results.json')
    else:
        results = pd.DataFrame(columns=columns)
    try:
        call_for_product(runner.run_benchmark, (cache_dir, results, port,), DIMENSIONS)
    finally:
        results.to_json('results.json')
