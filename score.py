
# imports up here can be used to
import pandas as pd
import json
import datetime
import os
import joblib
import argparse
from azureml.core import Workspace, Datastore, Run, Dataset, Model

from azureml.core.authentication import ServicePrincipalAuthentication
from utils import get_run_config, set_run_config

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

def score():

    config = get_run_config(ws, args.exp_name)
    print(config)

    if not config:
        print("config does not exist. Return")
        return

    experiment_name = config['name']
    model_name = str(experiment_name) + "_model"
    model_ws = Model(ws, model_name)
    print("loaded model", model_ws)

    dataset_name = config['dataset_name']
    label = config['label']
    dataset = Dataset.get_by_name(ws, name=dataset_name)
    dataframe1 = dataset.to_pandas_dataframe()
    dataframe1 = dataframe1.drop(columns=label)
    print(dataframe1)


    pickled_model_name = model_ws.download(exist_ok = True)

    # ..and deserialize
    model = joblib.load(pickled_model_name)
    print(model)

    pred = model.predict(dataframe1)
    print(pred)
    dataframe1[label] = pred

    datastore = Datastore(ws, 'adls_raw_storage')
    os.mkdir('./out')
    dataframe1.to_csv('./out/predictions.csv', index=False)

    datastore.upload('./out', target_path='ML_results', overwrite=True)

    set_run_config(ws, config['name'], last_scored_ts=str(datetime.datetime.now()))

score()
