# Case Study 1

This repository contains a scaffold for a scalable ETL (Extract, Transform, Load) 
pipeline designed to facilitate machine learning analytics on log data from mining 
machines. The pipeline processes batch files, stored as raw-parquet files in an 
AWS S3 bucket, handling tasks from preprocessing to inference. It is constructed 
adhering to best software design practices, ensuring modularity, testability, and 
extendibility, with the aim of seamless integration with advanced big data 
architectures such as Kubeflow and various AWS services. This scaffold acts as a 
structured prototype, ready to be enriched with functionalities for comprehensive 
implementations in predictive analytics projects.

## Database Table Assumptions

Refer to [Table Assumptions](./docs/TableAssumptions) for the assumptions made for the Postgres database tables.

## Getting Started

### 1. Automatic Docker Image Build and Push

A GitHub Action is configured to automatically build and push Docker images required for the pipeline. 
The workflow file is located at [`.github/workflows/docker-build-push.yml`](.github/workflows/docker-build-push.yml).

#### Images Built
- new_file_trigger
- preprocessor
- train_model
- inference

#### Triggering the Action
- The action is triggered each time you commit and push to the GitHub repository.

#### Configuration
- Currently, image tags are configured as `your-registry-url/<imagename>`.
- **Note:** Replace `your-registry-url` with the URL of your private registry.

### 2. Generate Kubeflow ETL Manifest

To generate the ETL manifest, execute the Python file as follows:
```sh
python etl_generator.py
```
Executing this command will create a `kubeflow_etl_pipeline.yaml` file.

### 3. Deploy the Kubeflow Pipeline

#### Option A: Kubeflow Dashboard UI
You can deploy the pipeline by uploading the generated `kubeflow_etl_pipeline.yaml` file to the Kubeflow Dashboard UI.  
Once The pipeline is successfully ran, go to the left tab and select "Recurring Runs" -> "Create run".  
Select your uploaded pipeline, choose the Experiment you want to run it under, and make sure the "Run Type" is 
Recurring and specify "Run every" as "1 Hours". 
Concurrent runs can be adjusted. Perhaps remove the "Catchup" option. Finish by clicking "Start"


#### Option B: Command Line Interface
Alternatively, deploy the pipeline using the kfp python library.  First define a client from `kfp.Client`,  
and then use the method "create_recurring_run"


