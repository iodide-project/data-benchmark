import json
import os


import numpy as np
from selenium.webdriver.support.wait import WebDriverWait
from selenium.common.exceptions import TimeoutException


import generate


class Ready:
    def __call__(self, driver):
        inited = driver.execute_script(
            "return window.ready")
        return inited is not None


class Done:
    def __call__(self, driver):
        done = driver.execute_script(
            "return window.benchmark_result")
        return done is not None


class SeleniumWrapper:
    def __init__(self, port, size):
        driver = self.get_driver()
        wait = WebDriverWait(driver, timeout=size)
        driver.get(f'http://127.0.0.1:{port}/index.html')
        wait.until(Ready())
        self.wait = wait
        self.driver = driver

    def execute(self, code):
        return self.driver.execute_script(code)


class FirefoxWrapper(SeleniumWrapper):
    def get_driver(self):
        from selenium.webdriver import Firefox
        from selenium.webdriver.firefox.options import Options
        from selenium.common.exceptions import JavascriptException

        options = Options()
        options.add_argument('-headless')

        self.JavascriptException = JavascriptException

        return Firefox(
            executable_path='geckodriver', firefox_options=options)

    def print_log(self):
        # TODO: Firefox doesn't have built-in support for this
        pass


class ChromeWrapper(SeleniumWrapper):
    def get_driver(self):
        from selenium.webdriver import Chrome
        from selenium.webdriver.chrome.options import Options
        from selenium.common.exceptions import WebDriverException
        from selenium.webdriver.common.desired_capabilities import DesiredCapabilities

        options = Options()
        options.binary_location = '/usr/bin/google-chrome-stable'
        options.add_argument('--headless')
        options.add_argument('--enable-precise-memory-info')

        d = DesiredCapabilities.CHROME
        d['loggingPrefs'] = { 'browser': 'ALL' }

        self.JavascriptException = WebDriverException

        return Chrome(chrome_options=options, desired_capabilities=d)

    def print_log(self):
        for entry in self.driver.get_log('browser'):
            print(entry)


def update_result(results, attrs, result):
    for row in results:
        for key, val in attrs.items():
            if row[key] != val:
                break
        else:
            row.update(result)
            break
    else:
        row = dict(attrs)
        row.update(result)
        results.append(row)

    with open('results.json', 'w') as fd:
        json.dump(results, fd)

    return results


def run_benchmark(attrs, cache_dir, results, port):
    print("Running benchmark", attrs)

    filename = generate.get_filename(attrs)
    attrs_json = json.dumps(attrs)

    if attrs['browser'] == 'firefox':
        sel = FirefoxWrapper(port, attrs['size'])
    elif attrs['browser'] == 'chrome':
        sel = ChromeWrapper(port, attrs['size'])
    else:
        raise NotImplementedError()

    # TODO: Fix this -- Firefox doesn't like Infinity in JSON
    result = {
        'runtime': np.inf,
        'mem': np.inf,
    }

    try:
        sel.driver.execute_script(
            f'window.run_benchmark("{filename}", {attrs_json});')
        try:
            sel.wait.until(Done())
        except TimeoutException:
            pass
        else:
            result = sel.driver.execute_script(
                'return window.benchmark_result;')
        print("Timing result: ", result)
    except sel.JavascriptException:
        pass
    else:
        sel.print_log()
    finally:
        sel.driver.quit()

        result['nbytes'] = os.stat(os.path.join(cache_dir, filename)).st_size

        update_result(results, attrs, result)
