var Papa = require('papaparse');


window.start_time = undefined;
window.end_time = undefined;


function run_csv(filename) {
    function finish_csv(results, file) {
        window.end_time = performance.now();
    }

    window.start_time = performance.now();
    Papa.parse(filename, { download: true, complete: finish_csv })
}


function run_json(filename) {
    window.start_time = performance.now();
    fetch(filename).then((response) => {
        response.json();
    }).then((json) => {
        window.end_time = performance.now();
    });
}

// TODO: Find some way to measure browser memory consumption

function run_benchmark(filename, attrs) {
    let func;

    if (attrs['format'] == 'csv') {
        func = run_csv;
    } else if (attrs['format'] == 'json') {
        func = run_json;
    }

    func(filename);
}

window.run_benchmark = run_benchmark
