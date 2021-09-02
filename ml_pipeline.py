import azureml.core
from azureml.core import Workspace, Datastore, Run, Dataset
from azureml.pipeline.steps import PythonScriptStep
from azureml.core import Experiment
from azureml.pipeline.core import PipelineData, Pipeline, PipelineParameter, StepSequence, PipelineEndpoint
import os
from azureml.core.runconfig import RunConfiguration
from azureml.core.conda_dependencies import CondaDependencies

from azureml.train.automl import AutoMLConfig
from azureml.core import Dataset, Workspace, Experiment, Datastore

import pandas as pd
from sklearn.model_selection import train_test_split

from pprint import pprint
import argparse
import json
import sys
from utils import get_run_config, set_run_config

parser = argparse.ArgumentParser()
parser.add_argument('--experiment_name', type=str, required=True,
                   help="Name of the experiment")
args = parser.parse_args()

tenant_id = os.environ['TENANT_ID']
sp_id = os.environ['SP_ID']
sp_key = os.environ['SP_KEY']

subscription_id = os.environ['SUB_ID']
resource_group = os.environ['RSG_GRP']
workspace_name = os.environ['WS_NAME']

ws = Workspace(subscription_id, resource_group, workspace_name)

config = get_run_config(ws, args.experiment_name)
print(config)

if not config:
    print("config not found.")
    sys.exit(0)

compute_target = config['compute_target']
exp_name = config['name']

run_config = RunConfiguration()
conda = CondaDependencies()
conda.add_pip_package('azureml-core')
conda.add_pip_package('azureml-train-automl')
conda.add_pip_package('xgboost==0.90')
conda.add_pip_package('joblib')
run_config.environment.python.conda_dependencies = conda

source_directory = "."
train_file = "train.py"
score_file = "score.py"

param_exp_name = PipelineParameter(name="exp_name", default_value="default_value")
param_sub_id = PipelineParameter(name="sub_id", default_value="default_value")
param_res_gp = PipelineParameter(name="res_gp", default_value="default_value")
param_ws_name = PipelineParameter(name="ws_name", default_value="default_value")
param_tenant_id = PipelineParameter(name="tenant_id", default_value="default_value")
param_sp_id = PipelineParameter(name="sp_id", default_value="default_value")
param_sp_key = PipelineParameter(name="sp_key", default_value="default_value")


training_step = PythonScriptStep(script_name=train_file,
                                source_directory=source_directory,
                                compute_target=compute_target, 
                                arguments=["--exp_name", param_exp_name,\
                                    "--sub_id", param_sub_id, "--res_gp", param_res_gp,\
                                    "--ws_name", param_ws_name, "--tenant_id", param_tenant_id,\
                                    "--sp_id", param_sp_id, "--sp_key", param_sp_key],
                                runconfig = run_config,
                                allow_reuse=False)

scoring_step = PythonScriptStep(script_name=score_file,
                                source_directory=source_directory,
                                compute_target=compute_target, 
                                arguments=["--exp_name", param_exp_name,\
                                    "--sub_id", param_sub_id, "--res_gp", param_res_gp,\
                                    "--ws_name", param_ws_name, "--tenant_id", param_tenant_id,\
                                    "--sp_id", param_sp_id, "--sp_key", param_sp_key],
                                runconfig = run_config,
                                allow_reuse=False)

run_steps = [training_step, scoring_step]
# run_steps = [training_step]
step_sequence = StepSequence(steps=run_steps)

pipeline1 = Pipeline(workspace=ws, steps=step_sequence)

pipeline_run1 = Experiment(ws, exp_name).submit(pipeline1, regenerate_outputs=True, \
    pipeline_parameters={"exp_name": exp_name,"sub_id": subscription_id,\
        "res_gp": resource_group, "ws_name": workspace_name,\
            "tenant_id": tenant_id, "sp_id": sp_id, "sp_key": sp_key})

pipeline_run1.wait_for_completion()

published_pipeline1  = pipeline_run1.publish_pipeline(name=exp_name, 
                               description="Internal EP of "+ exp_name, version="1.0")
pl_name = exp_name + '_pl'

try:
    ep_get = PipelineEndpoint.get(ws, name=pl_name)
except:
    print("PL not found.")
    ep_get = None

if ep_get == None:
    print("publish")
    ep_get = PipelineEndpoint.publish(ws, name=pl_name, pipeline=published_pipeline1,\
         description=config['description'])
else:
    print("found existing PL. ")
    ep_get.add_default(published_pipeline1)

print(ep_get.get_pipeline(ep_get.get_default_version()).endpoint)
endpoint = str(ep_get.get_pipeline(ep_get.get_default_version()).endpoint).split('/')[-1]

set_run_config(ws, exp_name, endpoint_id=endpoint)
