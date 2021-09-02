from azureml.core import Run, Dataset, Datastore, Workspace
from azureml.data.datapath import DataPath
import argparse
import argparse
import json

subscription_id = '8da70fa0-967f-413d-9b2f-c2d0a78b475a'
resource_group = 'AEA-RSG-APP-DEV-HELIX'
workspace_name = 'helixmldev'

def read_config(exp_name, **values):
    config_file = "../config.json"
    configs = json.load(open(config_file, "r"))
    print(configs)
    
    flag = 0
    for item in configs:
        if item['name'] == exp_name:
            flag = 1
            for key, val in values.items():
                item[key] = val
            break
    if flag == 0:
        values['name'] = exp_name
        configs.append(values)
        
    print(configs)
    json_file = open(config_file, "w")
    json.dump(configs, json_file, sort_keys=True)


parser = argparse.ArgumentParser()
parser.add_argument('--experiment_name', type=str, required=True,
                   help="Name of the experiment")
args = parser.parse_args()

# workspace = Workspace.from_config()
workspace = Workspace(subscription_id, resource_group, workspace_name)

data_store_name = "ml_synapse_datastore"
datastore = Datastore.get(workspace, data_store_name)

dataset_name = "ml_exp_data_1"

query_string = "select * from edw.dim_iot_datastream ds;"

query = DataPath(datastore, query_string)
tabular = Dataset.Tabular.from_sql_query(query, query_timeout=10)
tabular_ds = tabular.register(workspace, dataset_name, "Registered ds from ML data prep")

read_config(args.experiment_name, dataset="ml_exp_data_1")
