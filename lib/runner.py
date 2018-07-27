import json
import os


import numpy as np
import pandas as pd
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
            "return window.end_time")
        return done is not None


class SeleniumWrapper:
    def __init__(self, port):
        driver = self.get_driver()
        wait = WebDriverWait(driver, timeout=20)
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


class ChromeWrapper(SeleniumWrapper):
    def get_driver(self):
        from selenium.webdriver import Chrome
        from selenium.webdriver.chrome.options import Options
        from selenium.common.exceptions import WebDriverException

        options = Options()
        options.add_argument('--headless')

        self.JavascriptException = WebDriverException

        return Chrome(chrome_options=options)


def update_result(results, attrs, runtime, nbytes, mem):
    # if len(results) > 0:
    #     fields = np.ones((len(results),), np.bool)
    #     for key, val in attrs.items():
    #         fields &= results[key] == val
    #     if fields.sum() == 1:
    #         subset = results.iloc[fields]
    #     elif fields.sum() == 0:
    #         subset = results.append(attrs, ignore_index=True)
    #     else:
    #         raise ValueError("Duplicate results in table")
    # else:
    #     subset = results.append(attrs, ignore_index=True)

    row = dict(attrs)
    row['runtime'] = runtime
    row['nbytes'] = nbytes
    row['mem'] = mem

    if len(results) != 0:
        fields = np.ones((len(results),), np.bool)
        for key, val in attrs.items():
            fields &= results[key] == val
        count = np.sum(fields)
        if count == 1:
            idx = fields.nonzero()[0][0]
        elif count == 0:
            idx = len(results)
        else:
            raise ValueError("Duplicate results")
    else:
        idx = 0
    results.loc[idx] = row
    print(results)

    results.to_json('results.json')

    return results


def run_benchmark(attrs, cache_dir, results, port):
    print("Running benchmark", attrs)

    filename = generate.get_filename(attrs)

    if attrs['browser'] == 'firefox':
        sel = FirefoxWrapper(port)
    elif attrs['browser'] == 'chrome':
        sel = ChromeWrapper(port)
    else:
        raise NotImplementedError()

    runtime = None

    try:
        attrs_json = json.dumps(attrs)

        sel.driver.execute_script(f'window.run_benchmark("{filename}", {attrs_json})')
        try:
            sel.wait.until(Done())
        except TimeoutException:
            pass
        else:
            runtime = sel.driver.execute_script(
                'return window.end_time - window.start_time')
        print("Timing result: ", runtime)
    finally:
        sel.driver.quit()

        nbytes = os.stat(os.path.join(cache_dir, filename))[6]
        mem = 0

        update_result(results, attrs, runtime, nbytes, mem)

    
        
