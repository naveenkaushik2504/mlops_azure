import datetime
from azureml.train.automl import AutoMLConfig
# import azureml.contrib.dataset
from azureml.core import Dataset, Workspace, Experiment, Datastore
from azureml.core.authentication import ServicePrincipalAuthentication

import pandas as pd
from sklearn.model_selection import train_test_split

from pprint import pprint
import argparse
import json
import os
from utils import get_run_config, set_run_config, test

parser = argparse.ArgumentParser()
parser.add_argument('--exp_name', type=str, required=True,
                   help="Experiment Name")
parser.add_argument('--sub_id', type=str, required=True,
                   help="Sub ID")
parser.add_argument('--res_gp', type=str, required=True,
                   help="Resource Group")
parser.add_argument('--ws_name', type=str, required=True,
                   help="WS name")
parser.add_argument('--tenant_id', type=str, required=True,
                   help="Tenant ID")
parser.add_argument('--sp_id', type=str, required=True,
                   help="SP ID")                                                         
parser.add_argument('--sp_key', type=str, required=True,
                   help="SP Key")
args = parser.parse_args()

sp = ServicePrincipalAuthentication(tenant_id=args.tenant_id, # tenantID
                                    service_principal_id=args.sp_id, # clientId
                                    service_principal_password=args.sp_key) # clientSecret


ws = Workspace.get(name=args.ws_name, auth=sp, resource_group=args.res_gp, subscription_id=args.sub_id)

test()

def train():

    config = get_run_config(ws, args.exp_name)
    print(config)
    if not config:
        print("config does not exist. Return")
        return

    retrain = True
    valid_date = False
    time_now = datetime.datetime.now()
    try:
        dt_obj = datetime.datetime.strptime(config['last_trained_ts'], '%Y-%m-%d %H:%M:%S.%f')
        print(dt_obj)
        valid_date = True
    except:
        print("not a valid last trained timestamp")
        dt_obj = datetime.datetime.now()

    diff = time_now - dt_obj
    if diff.days < int(config['train_freq']) and valid_date:
        retrain = False

    if not retrain:
        print("Not yet time to retrain. Returning.")
        return

    compute_target = config['compute_target']

    dataset_name = config['dataset_name']
    dataset = Dataset.get_by_name(ws, name=dataset_name)

    label = config['label']
    automl_settings = config['automl']

    automl_regressor = AutoMLConfig(compute_target = compute_target,
                                    training_data=dataset,
                                    label_column_name=label,
                                    **automl_settings)

    experiment_name = config['name']
    experiment = Experiment(ws, experiment_name)

    run = experiment.submit(automl_regressor, show_output=True)
    run.wait_for_completion()

    best_run, fitted_model = run.get_output()
    # print(fitted_model.steps)

    prev_score = config['last_trained_score']
    new_score = best_run.properties['score']

    if new_score < prev_score:
        print("Score not improved. Return")
        return

    set_run_config(ws, config['name'], last_trained_ts=str(datetime.datetime.now()), last_trained_score=new_score)

    model_name = str(experiment_name) + "_model"
    description = 'AutoML forecast example'
    tags = None

    model = run.register_model(model_name = model_name, 
                                    description = description, 
                                    tags = tags)

train()
