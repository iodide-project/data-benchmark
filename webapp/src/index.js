var Papa = require('papaparse');


window.benchmark_result = undefined;


function run_csv(filename, attrs, done_callback) {
    function finish_csv(results, file) {
        done_callback();
    }

    window.start_time = performance.now();
    Papa.parse(filename, { download: true, complete: finish_csv })
}

function run_json(filename, attrs, done_callback) {
    fetch(filename).then((response) => {
        response.json();
    }).then((json) => {
        done_callback();
    });
}

function get_benchmark_function(attrs) {
    if (attrs['format'] == 'csv') {
        return run_csv;
    } else if (attrs['format'] == 'json') {
        return run_json;
    } else {
        throw new Error(`Unknown format ${attrs['format']}`);
    }
}

let TARGET_TIME = 1000;

function run_benchmark(filename, attrs) { 
    let func = get_benchmark_function(attrs);

    // First, estimate the approximate time
    let start_time = performance.now();
    func(filename, attrs, () => {
        let end_time = performance.now();

        // Calculate the number of iterations we should run to take approx
        // TARGET_TIME
        let iter_time = end_time - start_time;
        let niters = Math.round(TARGET_TIME / iter_time);
        if (niters < 2) {
            niters = 2;
        }
        let i = 0;
        let maxHeap = 0;

        function run_iter() {
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
