## Problem Statement

This company provides insights for the heavy industry, especially for mining machines. 
To enable scalable analytics for overground mining assets, we develop a software product that predicts activities and cycles using machine learning models. 
The main requirement for this product is scalability, i.e. enabling valuable insights for hundreds of mining machines with minimum effort in scaling-up and maintenance.

Your task is to design  a suitable ML system and provide a scaffold project in python that fulfills the defined requirements.

## Big Data Pipeline
Our big data infrastructure is supplied by our on-board-unit loggers that are mounted on the individual mining machines (like surface dumpers, excavators, wheel loaders, etc.). 
These loggers send compressed batch files approximately every 10 minutes, depending on WiFi or LTE coverage and power status. 
Along with CAN-bus, J1939-bus or other OEM-dependent data sources, the on-board units have integrated sensors for GPS (position) and forces (inertial measurement unit IMU), that have the same format for all assets that are integrated into our infrastructure.

The per 10-minutes batch file recorded GPS positions at 1 Hz and IMU forces at 10 Hz are the data source for our activity predictions.
Each row of a data batch file contains a unix timestamp.

Incoming batch files are collected, converted and dumped as raw-parquet files to an AWS S3 bucket using a unique machine UUID and the first timestamp of the batch file. 
For each new batch file a kafka message is generated and communicated via a kafka topic. 
The kafka service can be used to request all existing batch files for a specific machine using its UUID.

## The ETL pipeline

* A pipeline configuration should contain a list of asset UUIDs to generate analysis for and include all other required settings like start date of the analysis, model parameters, etc.
* A database (or another sufficient technology) should be used to track the state of the ETL pipeline, e.g. which raw data files have been processed, which models have been trained, which batch files have been used for inference and so on.
* A recurring job should scan for availability of new raw data batches for the configured assets (UUIDs).
* New files should be picked up and preprocessed. The preprocessed files should be placed in another S3 bucket using a suitable prefix for this pipeline.
The preprocessed files should be called *StateVectors*. Examples for the preprocessing are
  * resampling to _exactly_ 1Hz temporal resolution by interpolation
  * de-noising of GPS and IMU data
  * filling of gaps
  * quality validation of the raw data batch file
  * A training job should train a model if a sufficient amount of input data is available. (E.g. 2 weeks of raw data for all assets). The trained model should be placed in the S3 bucket of the service using the name of the pipeline and a proper versioning schema. The successfully trained model should be registered inside the database. The model training (input) data and the saved model should be stored in S3. --JMR (the model should determine how much data is availalbe by reading the historical kafka messages)


* An inference job should generate inferences on successfully preprocessed batch files and dump the inference output into the S3 bucket (for debugging and purposes to ensure reproducibility of the results).
* A postprocessor should take the inference result and dump it to an external postgres database. Adaptors for schema conversion and data quality assurance should be present.

## Your Task
Design a scaffold python project from scratch that covers the described ETL pipeline.
Required credentials for database and S3 access are provided via environment variables and are out of scope for this case study.
The scaffold should act as a mock-up for a scalable machine learning prototype that can be executed on big data architectures (i.e. in our current implementation kubeflow, AWS S3 buckets and an AWS RDS postgres database).
You should be able to explain your approach and in theory it should be possible to take your prepared scaffold project and start filling the classes with all the functionalities that are required.

* Generate a graphical representation of the design approach (e.g. using drawio) and place it within the *docs* folder of your project. The design should be implementation independent and cover the best practices for good software design.
* Create a python-module called *etl* that holds all the modules and classes that are required for the scaffold project.
* Use docstrings to explain the purpose of a class and the most important function definitions inside.
* Follow the basic software design principles with respect to:
  * testability
  * modularity
  * separation of concerns
  * extendibility
* Explain the steps that would be necessary to deploy this project to production.
