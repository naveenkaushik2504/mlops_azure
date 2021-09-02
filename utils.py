from azureml.core import Dataset, Workspace, Datastore
import json

config_file = "run_config.json"

def test():
    print("in utils. Lets see if it works.")

def download_config(ws):
    config_data = Dataset.get_by_name(ws, name='ml_run_config')
    config_data.download(target_path='.', overwrite=True)
    configs = json.load(open(config_file, "r"))
    return configs

def upload_config(ws, configs):
    with open(config_file, "w") as json_file:
        json.dump(configs, json_file, indent=4)
    datastore_raw = Datastore(ws, 'adls_raw_storage')
    datastore_raw.upload_files([config_file], target_path='ML_results', overwrite=True)

def get_run_config(ws, run_name):
    configs = download_config(ws)
    print(configs)
    for item in configs:
        if item['name'] == run_name:
            return item
    print("no config found.")
    return None

def set_run_config(ws, run_name, **kwargs):
    configs = download_config(ws)
    for item in configs:
        if item['name'] == run_name:
            for key, val in kwargs.items():
                item[key] = val
            break
    print("in set config function", configs)
    upload_config(ws, configs)
