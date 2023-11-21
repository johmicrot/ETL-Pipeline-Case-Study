import os


class Config:
    # AWS S3
    RAW_S3_BUCKET = os.environ.get('RAW_S3_BUCKET', 'default_raw_bucket_name')
    PROCESSED_S3_BUCKET = os.environ.get('PROCESSED_S3_BUCKET', 'default_processed_bucket_name')
    MODEL_S3_BUCKET = os.environ.get('MODEL_S3_BUCKET', 'default_model_bucket_name')
    INFERENCE_S3_BUCKET = os.environ.get('MODEL_S3_BUCKET', 'default_model_bucket_name')

    # Kafka configurations
    KAFKA_ENDPOINT = os.environ.get('KAFKA_ENDPOINT', 'localhost:9092')
    KAFKA_TOPIC = os.environ.get('KAFKA_TOPIC', 'default_topic_name')
    KAFKA_GROUP_ID = 'group_id'

    # Database configurations
    DB_HOST = os.environ.get('DB_HOST', 'localhost')
    DB_PORT = os.environ.get('DB_PORT', 5432)  # Default port for PostgreSQL
    DB_NAME = os.environ.get('DB_NAME', 'default_db_name')
    DB_USER = os.environ.get('DB_USER', 'default_user')
    DB_PASSWORD = os.environ.get('DB_PASSWORD', 'default_password')

    # Kubeflow settings
    PIPELINE_MANIFEST_NAME = 'kubeflow_etl_pipeline.yaml'
    KUBEFLOW_EXP_NAME = 'Experiment1'
    KUBEFLOW_ADDRESS = 'http://10.64.140.43.nip.io'
    KUBE_REOCURRING_JOB_FREQ_SECONDS = 60 * 60 * 24  # One day
    KUBE_REOCURRING_JOB_ENDTIME = '12'
    PIPELINE_NAME = 'ETL_model_pipeline'

    # Other settings
    RESAMPLE_FREQUENCY = '1S'  # Default resampling to 1 second
    MODEL_TRAINING_THRESHOLD_DAYS = 14  # 2 weeks of data in days
    MODEL_TRAINING_THRESHOLD_SECONDS = MODEL_TRAINING_THRESHOLD_DAYS * 24 * 60 * 60  # 2 weeks of data in seconds

    STATEVECTOR_NAME = 'StateVectors'
    INFERENCE_NUMBER_OF_FILES = 1000
    ##################################################

    # Model parameters
    MODEL_NAME = 'casestudy1'
    MODEL_PARAMETERS = {
        "learning_rate": 0.001,
        "batch_size": 32,
        "num_layers": 4,
        # ... any other model-specific parameters
    }

    WRITE_TO_DB_QUERY = """
        INSERT INTO raw_data_batches (asset_id, s3_location, first_timestamp, status, received_time)
        VALUES (%s, %s, %s, %s, %s, %s)
        ON CONFLICT (s3_location) DO NOTHING;
        """

    RETRIEVE_UNPROCESSED_QUERY = """
        SELECT batch_id, s3_location FROM raw_data_batches WHERE was_processed = FALSE;
        """
    MARK_RECORD_AS_PROCESSED = """
        UPDATE raw_data_batches SET has_state_vector = TRUE WHERE batch_id = %s;
        """
    ASSET_IDS_QUERY = """
        SELECT asset_id FROM assets;
        """
    DAYS_COUNT_QUERY = """
        SELECT COUNT(DISTINCT DATE(processed_time))
        FROM state_vectors
        WHERE asset_id = %s AND processed_time > current_date - INTERVAL '%s days';
        """
    VECTOR_S3_LOCATIONS_QUERY = """
        SELECT vector_id, s3_location FROM state_vectors;
        """

    INSERT_MODEL_QUERY = """
        INSERT INTO models (version, model_name, full_model_name, s3_location, trained_date) 
        VALUES (%s, %s, %s, %s, %s);
        """

    SELECT_MAX_MODEL_QUERY = "SELECT MAX(version) FROM models WHERE model_name = %s;"

    FETCH_STATEVECTORS_LIMIT = "SELECT vector_id, s3_location FROM state_vectors LIMIT %s;" % INFERENCE_NUMBER_OF_FILES