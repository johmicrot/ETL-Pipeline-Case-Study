import boto3
import psycopg2
import pandas as pd
from io import BytesIO
import config




class Preprocessor:
    """
    This class represents a job for preprocessing raw data. It performs the following sequentially
    1) Interacts with S3 and Postgres database to retrieve new raw data batches,
    2) Generates StateVectors from the raw data batch files,
    3) Stores StateVectors to a different S3 bucket.
    4) Finally updating the raw_data_batches table to indicate that the StateVectors have been processed.
    """

    def __init__(self):
        self.s3 = boto3.client('s3')
        self.raw_bucket_name = config.RAW_S3_BUCKET
        self.pp_bucket_name = config.PROCESSED_S3_BUCKET
        # Establish connection to PostgreSQL
        self.db_conn = psycopg2.connect(
            dbname=config.DB_NAME,
            user=config.DB_USER,
            password=config.DB_PASSWORD,
            host=config.DB_HOST,
            port=config.DB_PORT
        )
        self.config = config


    def get_unprocessed_records(self):
        """
        Fetches unprocessed records from the database based on the "was_processed" attribute.

        Returns:
        - list: A list of dictionaries, where each dictionary contains the batch_id and the file
                location (s3_location) of unprocessed record.
        """

        with self.db_conn.cursor() as cursor:
            cursor.execute(config.RETRIEVE_UNPROCESSED_QUERY)
            records = cursor.fetchall()
            return [{"batch_id": record[0], "s3_location": record[1]} for record in records]

    def store_processed_data(self, processed_data, s3_location):
        """
        Stores preprocessed data onto the preprocessed S3 bucket.

        Args:
        - processed_data (pd.DataFrame): DataFrame containing the preprocessed data.
        - s3_location (str): The S3 location where to store the processed data.

        Returns:
        - str: The S3 object name where the preprocessed data is stored.
        """
        try:
            processed_data_io = BytesIO()
            processed_data.to_parquet(processed_data_io)
            processed_data_io.seek(0)
            self.s3.put_object(Bucket=self.pp_bucket_name, Key=s3_location, Body=processed_data_io.getvalue())

            return s3_location

        except Exception as e:
            print(f"Error in storing processed data to {s3_location}: {e}")
            return None

    def preprocess(self, raw_data):
        """
        Performs preprocessing tasks on the provided raw data.

        Args:
        - raw_data (pd.DataFrame): DataFrame containing the raw data.

        Returns:
        - pd.DataFrame: DataFrame containing the preprocessed data.
        """
        preprocessed_data = raw_data
        return preprocessed_data

    def preprocess_and_store(self, record):
        """
        Fetches raw data from S3, preprocesses it using the `preprocess` method,
        and stores the processed data back to S3 using the `store_processed_data` method.

        Args:
        - record (dict): Dictionary containing the batch_id and s3_location of the record to process.

        Returns:
        - str: The S3 object name where the preprocessed data is stored.
        """
        try:
            s3_object = self.s3.get_object(Bucket=self.raw_bucket_name, Key=record['s3_location'])
            raw_data = pd.read_parquet(BytesIO(s3_object['Body'].read()))

            processed_data = self.preprocess(raw_data)

            if processed_data is None:
                raise ValueError('Preprocessing failed.')
            raw_filename = record['s3_location'].split('/')[-1]
            processed_s3_location = f"StateVector_{record['batch_id']}.parquet"
            self.store_processed_data(processed_data, processed_s3_location)
            return processed_data

        except Exception as e:
            print(f"Error in preprocessing and storing data for record {record['batch_id']}: {e}")
            return None

    def mark_record_as_processed(self, batch_id):
        """
        Marks a record in the database as processed. Allows for effecient checking of entries which have not been
        processed.

        Args:
        - batch_id (int): The batch_id of the record to mark as processed.
        """
        with self.db_conn.cursor() as cursor:
            cursor.execute(config.MARK_RECORD_AS_PROCESSED, (batch_id,))
            self.db_conn.commit()


    def validate_data_quality(self, data):
        """
        Validates the quality of the data.
        """
        return None

    def process_batch_data(self):
        """
        For each unprocessed record in the database, it fetches the data, preprocesses it, stores it back to S3,
        and updates the database to mark the record as processed.
        """
        unprocessed_records = self.get_unprocessed_records()
        for record in unprocessed_records:
            processed_data = self.preprocess_and_store(record)
            self.mark_record_as_processed(record["batch_id"])
            self.validate_data_quality(processed_data)

    def close(self):
        self.db_conn.close()

if __name__ == "__main__":
    preprocessor = Preprocessor()
    try:
        preprocessor.process_batch_data()
    finally:
        preprocessor.close()
