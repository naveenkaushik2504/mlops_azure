# MLOps Template

This template can be used to configure and submit ML training runs via Azure ML Pipelines. The pipeline in the end would be submitted to an Endpoint in the ML workspace.


Following files form the basis of the template:

* `ml_pipeline.py`: code to define the pipeline steps and submit the endpoint.
* `train.py`: code to defining the training step. As of now, it triggers an [AutoML](https://docs.microsoft.com/en-us/azure/machine-learning/concept-automated-ml) run. 
* `score.py`: code to define the scoring step and upload the results
* `utils.py`: code for util functions needed by the template
* `run_config.json`: This file needs to be changed to define the properties of a new run. Details are given below

## Configuring a Run

To configure a new run, make an entry into the `run_config.json`. It might be easier to copy-paste one of the older entries and editing it.

```
{
        "name": "my_test_exp_2",
        "description": "Test versioned pipeline 2",
        "compute_target": "test-compute-ml",
        "automl": {
            "task": "regression",
            "experiment_timeout_minutes": 15,
            "primary_metric": "r2_score",
            "n_cross_validations": 3
        },
        "train_freq": 10,
        "dataset_name": "uio_test",
        "label": "reading_value_daily_avg",
        "last_trained_ts": "2021-06-06 11:42:57.579436",
        "last_trained_score": "0.9791213203864134",        
        "endpoint_id": "0c824a77-2c3f-4f92-9d42-ab5468769c98",
        "last_scored_ts": "2021-06-06 11:44:14.986474"
    }
```

Following is the exaustive list of all the parameters supported as of now:

- `name`: Name of the experiment. This is the key identifier of the experiment.
- `description`: Description about the experiment
- `compute_target`: AML compute machine to run the experiment on.
- `automl`: Parameters for AutoML experiment. More info can be found [here](https://docs.microsoft.com/en-us/python/api/azureml-train-automl-client/azureml.train.automl.automlconfig.automlconfig?view=azure-ml-py).
- `train_freq`: Number of days before the retraining to be triggered.
- `dataset_name`: Azure ML dataset to use for the experiment. An example is provided in the `data_prep.py` file and more ways to create from a variety of resources can be found [here](https://docs.microsoft.com/en-us/azure/machine-learning/how-to-create-register-datasets)
- `label`: Target column in the dataset


The below parameters are a part of config file, but do not need to be populated by the user, but are rather for the frameworks purpose.
- `last_trained_ts`: Timestamp when the model was last trained.
- `last_trained_score`: Training score acheived based on the metric defined in the AutoML settings. 
- `endpoint_id`: Endpoint where the model is deployed. 
- `last_scored_ts`: Timestamp when the model had last scored.

The output of the framework would be a registered model, pipeline and a deployed endpoint in the ML Workspace.

The user needs to make an entry in the `run_config.json` for the experiment, before it is submitted.

Following code shows a way to submit a Pipeline.

```
python ml_pipeline.py --experiment_name "my_test_exp_2"
```

Before submitting this run, the user needs to ensure that the following environment variables are set:
- `SUB_ID`: Subscription ID
- `RSG_GRP`: Resource Group
- `WS_NAME`: Workspace Name
- `TENANT_ID`: Tenant ID
- `SP_ID`: Service Principal ID
- `SP_KEY`: Service Principal Key

