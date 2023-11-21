import boto3
from kafka import KafkaConsumer
from datetime import datetime
import pickle
import config
import pandas as pd
import psycopg2
from io import BytesIO


class ModelTrainingJob:
    """
    This class represents a job for training models.
    It sequentially performs the following actions
    1) Checks to make sure that all assets have suffent data to start training
    2) Interacts with S3, and Postgres database to retrieve the
    latest model name/number and Statevectors, train the model, and save the data used to train the model along
     with the model to the S3 bucket.  Register the model to the Postgres DB.
    """

    def __init__(self):
        self.config = config
        self.consumer = KafkaConsumer(topics=self.config['KAFKA_TOPIC'],
                                      bootstrap_servers='your_kafka_servers',
                                      group_id='your_group_id',
                                      auto_offset_reset='earliest')
        self.s3 = boto3.client('s3', aws_access_key_id='YOUR_ACCESS_KEY', aws_secret_access_key='YOUR_SECRET_KEY')
        self.pipeline_name = config.PIPELINE_NAME
        self.pp_bucket_name = config.PROCESSED_S3_BUCKET
        self.db_conn = psycopg2.connect(
            dbname=self.config.DB_NAME,
            user=self.config.DB_USER,
            password=self.config.DB_PASSWORD,
            host=self.config.DB_HOST,
            port=self.config.DB_PORT
        )

    def check_sufficient_data_in_db(self):
        """
        Checks the database to ensure there is sufficient data from the last two weeks to train the model. If there is
        sufficient data, it returns True and a list of vectors with their locations. Otherwise, it returns False and None.

        Returns:
        bool: Whether there is sufficient data to train the model.
        list: List of vectors with their locations if there is sufficient data, otherwise None.
        """

        cursor = self.db_conn.cursor()

        cursor.execute(config.ASSET_IDS_QUERY)
        asset_ids = [record[0] for record in cursor.fetchall()]

        for asset_id in asset_ids:
            cursor.execute(config.DAYS_COUNT_QUERY, (asset_id, config.MODEL_TRAINING_THRESHOLD_DAYS))
            days_count = cursor.fetchone()[0]

            if days_count < config.MODEL_TRAINING_THRESHOLD:
                cursor.close()
                return False, None

        # If here is reached, all assets have enough data

        # Fetch all vector_ids and their corresponding s3_locations
        cursor.execute(config.VECTOR_S3_LOCATIONS_QUERY)
        results = cursor.fetchall()
        # vectors_s3_locations = [{"vector_id": record[0], "s3_location": record[1]} for record in results]
        s3_locations = [record[0] for record in results]
        cursor.close()
        return True, s3_locations

    def train_model(self, data):
        """
        Trains the model with the provided data. This is a placeholder and should be replaced with actual
        model training code.

        Args:
        data (pd.DataFrame): The data to train the model on.

        Returns:
        object: The trained model object.
        """
        return None

    def fetch_preprocessed_data(self, s3_object_filename):
        """
        Fetches preprocessed data from S3 and loads it into a DataFrame.

        Args:
        s3_object_filename (str): S3 object filename where the preprocessed data is stored.

        Returns:
        pd.DataFrame: The preprocessed data loaded into a DataFrame.
        """
        data_obj = self.s3.get_object(Bucket=self.pp_bucket_name, Key=s3_object_filename)
        pd_parquet_data = pd.read_parquet(BytesIO(data_obj['Body'].read()))
        return pd_parquet_data

    def save_model_and_data_to_s3(self, model, data, file_model_name, version, timestamp):
        """
        Saves the trained model and data to S3 with a given version and timestamp.

        Args:
        model (object): The trained model object to save.
        data (pd.DataFrame): The data used for training the model.
        version (int): The version of the model.
        timestamp (str): The timestamp when the model was trained.
        """
        data_name = f"{self.config.MODEL_NAME}_{version}_{timestamp}_data.parquet"

        # Save and upload model to S3.  This can also be done as a stream.
        with open(file_model_name, 'wb') as model_file:
            pickle.dump(model, model_file)
        self.s3.upload_file(file_model_name, self.config.MODEL_S3_BUCKET, file_model_name)

        # Save and upload data to S3
        data.to_parquet('data.parquet')
        self.s3.upload_file('data.parquet', self.config.MODEL_S3_BUCKET, data_name)

    def register_model_in_db(self, current_datetime):
        """
        Registers the trained model in the database with the given timestamp.

        Args:
        current_datetime (str): The timestamp when the model was trained.

        Returns:
        int: The version of the registered model and the model file name stored on the s3 bucket
        """
        with self.db_conn.cursor() as cursor:
            # Fetch the latest version for the given pipeline_name
            cursor.execute(config.SELECT_MAX_MODEL_QUERY, (self.config.MODEL_NAME))
            current_version = cursor.fetchone()[0]

            # If a version exists, increment it. Otherwise, start with 1.
            new_version = current_version + 1 if current_version else 1

            full_model_name = '%s_%s_%s.pkl' % (self.config.MODEL_NAME,
                                                new_version,
                                                current_datetime)

            # Insert the new model record with the incremented version number
            cursor.execute(config.INSERT_MODEL_QUERY,
                           (new_version,
                            self.config.MODEL_NAME,
                            full_model_name,
                            self.config.MODEL_S3_BUCKET,
                            current_datetime))

            self.db_conn.commit()
        return new_version, full_model_name

    def train(self):
        """
        Orchestrates the model training process by checking for sufficient data, fetching preprocessed data,
        training the model, registering the model in the database, and saving the model and data to S3.

        We are converting the data to pandas, for very large datasets this wouldn't scale well, possibly
        numpy arrays would need to be used.
        """
        sufficient_data, vector_locations = self.check_sufficient_data_in_db()
        if sufficient_data:
            data_list = []
            for location in vector_locations:
                data = self.fetch_preprocessed_data(location)
                data_list.append(data)
            all_data_df = pd.concat(data_list, ignore_index=True)
            model = self.train_model(all_data_df)

            current_datetime = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')

            model_version, file_model_name = self.register_model_in_db(current_datetime)

            self.save_model_and_data_to_s3(model, data, file_model_name, model_version, current_datetime)

        else:
            print('Not Enough data to train')

    def close(self):
        self.db_conn.close()


if __name__ == "__main__":
    trainer = ModelTrainingJob()
    try:
        trainer.train()
    finally:
        trainer.close()
