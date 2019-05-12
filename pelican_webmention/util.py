import yaml
import time
import requests


def load_yaml(filename):
    try:
        with open(filename) as f:
            return yaml.safe_load(f)
    except Exception as exc:
        print("Trouble opening YAML file " + filename + ', error = ' + str(exc))
        return None


def wait_for_url(url):
    timeout_secs = 15
    wait_secs = 1
    started = time.time()

    done = False
    found = False
    while not done:
        print('requesting head from ' + url)
        r = requests.head(url)
        if r.ok:
            print('found head from ' + url)
            done = True
            found = True
        elif (time.time() - started) >= timeout_secs:
            print('timeout for ' + url)
            done = True
            found = False
        else:
            print('sleeping...', flush=True)
            time.sleep(wait_secs)
    return found
