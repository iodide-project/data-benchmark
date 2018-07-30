var Papa = require('papaparse');
var Arrow = require('@apache-arrow/es5-cjs');


window.benchmark_result = undefined;


function run_csv(filename, attrs, done_callback) {
    function finish_csv(results, file) {
        done_callback(results.data);
    }

    let options = {
        download: true,
        complete: finish_csv,
        skipEmptyLines: true,
        dynamicTyping: true
    };

    if (attrs['type'] == 'table') {
        options['header'] = true;
    }

    window.start_time = performance.now();
    Papa.parse(filename, options);
}

function run_json(filename, attrs, done_callback) {
    fetch(filename)
        .then((response) => response.json())
        .then((json) => done_callback(json));
}

function run_arrow(filename, attrs, done_callback) {
    fetch(filename)
        .then((response) => response.arrayBuffer())
        .then((buffer) => {
            let table = Arrow.Table.from(new Uint8Array(buffer));
            done_callback(table);
        });
}

function get_benchmark_function(attrs) {
    if (attrs['format'] == 'csv') {
        return run_csv;
    } else if (attrs['format'] == 'json') {
        return run_json;
    } else if (attrs['format'] == 'arrow') {
        return run_arrow;
    } else {
        throw new Error(`Unknown format ${attrs['format']}`);
    }
}

let TARGET_TIME = 1000;

function validate_content(content, attrs) {
    if (content.length != attrs['size']) {
        throw new Error("Content is wrong size");
    }

    if (attrs['format'] == 'arrow') {
        function index_row(row, i) { return row.get(i); }
    } else if (attrs['type'] == 'array') {
        function index_row(row, i) { return row[i]; };
    } else if (attrs['type'] == 'table') {
        function index_row(row, i) { return row[String.fromCharCode(i + 65)]; };
    }

    let count = 0;
    for (let i = 0; i < content.length; ++i) {
        let row;
        if (attrs['format'] == 'arrow') {
            row = content.get(i);
            if (row.length != 26) {
                throw new Error("row is wrong size " + row.length);
            }
        } else {
            row = content[i];
            if (attrs['type'] == 'array') {
                if (row.length != 26) {
                    throw new Error("row is wrong size " + row.length);
                }
            } else if (attrs['type'] == 'table') {
                if (Object.keys(row).length != 26) {
                    throw new Error("row is wrong size " + Object.keys(row).length);
                }
            }
        }

        let sum = 0;
        for (let i = 0; i < 25; ++i) {
            sum += index_row(row, i);
        }

        let expected_sum = index_row(row, 25);
        if (!(sum - 1e-6 < expected_sum && sum + 1e-6 > expected_sum)) {
            throw new Error("invalid sum " + sum);
        }

        // If we haven't found an error yet, this is probably good enough...
        count += 1;
        if (count > 5) {
            break;
        }
    }
}

function run_benchmark(filename, attrs) {
    let func = get_benchmark_function(attrs);

    // First, estimate the approximate time
    let start_time = performance.now();
    func(filename, attrs, (content) => {
        let end_time = performance.now();

        validate_content(content, attrs);

        // Calculate the number of iterations we should run to take approx
        // TARGET_TIME
        let iter_time = end_time - start_time;
        let niters = Math.round(TARGET_TIME / iter_time);
        if (niters < 2) {
            niters = 2;
        }
        let i = 0;
        let maxHeap = 0;

        function run_iter(content) {
            if (performance.memory !== undefined) {
                maxHeap = Math.max(performance.memory.usedJSHeapSize, maxHeap);
            }
            if (i++ >= niters) {
                end_time = performance.now();
                window.benchmark_result = {
                    'runtime': (end_time - start_time) / niters,
                    'niter': niters,
                    'mem': maxHeap
                };
            } else {
                func(filename, attrs, run_iter);
            }
        }

        start_time = performance.now();
        func(filename, attrs, run_iter);
    });
}

window.run_benchmark = run_benchmark
