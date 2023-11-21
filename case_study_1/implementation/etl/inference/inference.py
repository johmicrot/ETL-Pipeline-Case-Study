import boto3
import pandas as pd
from io import BytesIO
import psycopg2
import config
import logging

logging.basicConfig(level=logging.INFO)

class InferenceJob:
    """
    This class represents an inference job. Performing inference using a machine learning model,
    and postprocessing by saving the results to S3 and Postgres.

    It sequentially performs:
    1) Fetch StateVectors
    2) Combines them into one DataFrame
    3) Converts the schema
    4) Performs Data quality assurance
    5) Saves results to Postgres Database

    """
    def __init__(self):
        # Database connection
        self.db_conn = psycopg2.connect(
            dbname=config.DB_NAME,
            user=config.DB_USER,
            password=config.DB_PASSWORD,
            host=config.DB_HOST,
            port=config.DB_PORT
        )

        # S3 client
        self.s3 = boto3.client('s3', aws_access_key_id=config.AWS_ACCESS_KEY, aws_secret_access_key=config.AWS_SECRET_KEY)
        self.inference_bucket = config.INFERENCE_RESULTS_BUCKET
        self.config = config

    def fetch_processed_vectors(self):
        """
        Fetches a specified number of Statevectors from the database.  Uses the maximum number of
        FETCH_STATEVECTORS_LIMIT to retrieve a specific maximum number of StateVectors.  Usually in training you
        would want to include all data by setting the limit to inf, but If there are too many StateVectors to load
        into memery then limit would need to be set to a reasonable number

        Returns:
        - list: A list of tuples where each tuple contains a vector_id and its corresponding s3_location.
        """
        try:
            with self.db_conn.cursor() as cursor:
                cursor.execute(config.FETCH_STATEVECTORS_LIMIT)
                return cursor.fetchall()
        except Exception as e:
            logging.error(f"Failed to fetch Statevectors. Error: {e}")
            return []

    def perform_inference(self, data):
        """
        It will query the Postgres for the
        latest model by querying the latest version from the congif.MODEL_NAME.
        Load the model from the S3 bucket provided by Postgres, and perform inference on the data.

        This is currently a placeholder and should be replaced with actual inference logic.
        """
        return None

    def save_inference_to_s3(self, result, vector_id):
        """
        Saves the inference result to an S3 bucket.

        Args:
        - result (pd.DataFrame): The inference result to save.
        - vector_id (int): The ID of the vector associated with the inference result.

        Returns:
        - str: The name under which the inference result is saved in S3.
        """
        result_name = f"inference_result_for_vector_{vector_id}.parquet"
        byte_stream = BytesIO()
        try:
            result.to_parquet(byte_stream)
            byte_stream.seek(0)
            self.s3.put_object(Bucket=self.inference_bucket, Key=result_name, Body=byte_stream.getvalue())
        except Exception as e:
            logging.error(f"Failed to save inference to S3. Error: {e}")
        return result_name

    def schema_conversion(self, data):
        """
        Converts the schema of the provided data as required. This is currently a placeholder.
        """
        return data

    def data_quality_assurance(self, data):
        """
        Performs data quality checks and possibly removes/fixes bad data. This is currently a placeholder.
        """
        return data

    def save_to_postgres(self, data):
        """
        Saves the provided data to PostgreSQL. This is currently a placeholder.
        """
        pass

    def postprocessor(self, data):
        """
        The post-processing of the provided data.  Performes schema conversion,
        ensuring data quality, performing inference, and saving the inference result to Postgres.
        """
        # Convert the schema of the data
        data = self.schema_conversion(data)

        # Ensure the quality of the data
        data = self.data_quality_assurance(data)

        # Perform the inference
        inference_result = self.perform_inference(data)

        # Save the inference to Postgres
        self.save_to_postgres(inference_result)

    def run(self,):
        """
        Orchestrates the overall inference job by fetching Statevectors from the database,
        combining the associated data, and post-processing.
        Including the data quality assurance and schema conversion
        """
        vectors = self.fetch_processed_vectors()

        combined_data_list = []
        for vector_id, s3_location in vectors:
            try:
                data_obj = self.s3.get_object(Bucket=config.PROCESSED_S3_BUCKET, Key=s3_location)
                data = pd.read_parquet(BytesIO(data_obj['Body'].read()))
                combined_data_list.append(data)
            except Exception as e:
                logging.error(f"Failed to process vector {vector_id}. Error: {e}")

        if combined_data_list:
            combined_data = pd.concat(combined_data_list, ignore_index=True)
            self.postprocessor(combined_data)

if __name__ == "__main__":
    inference = InferenceJob()
    inference.run()
