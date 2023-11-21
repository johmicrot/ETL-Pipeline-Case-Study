from kafka import KafkaConsumer
import json
import config
import psycopg2
from datetime import datetime

class NewFileTrigger:
    """
    This class is responsible for triggering the processing of new files by consuming messages from a Kafka topic.
    It performs the following sequentially:
    1) Retrieves the kafka messeges indicating one or more new data batch files
    2) Uses the message to load the new files.
    3) Extracts relevant information from the file name
    4) Writes the information to a Postgres database.

    Assumption:
    - The new file reported by kafka will contain a raw batch file name.  The file name will contain the
    asset_id and first_timestamp separated by a  "_".
    The structure would look like <asset_id>_<first_timestamp>.parquet


    """

    def __init__(self):
        self.config = config
        self.consumer = KafkaConsumer(
            topic=config.KAFKA_TOPIC,
            bootstrap_servers=config.KAFKA_ENDPOINT,
            value_deserializer=lambda v: json.loads(v.decode('utf-8')),
            auto_offset_reset='latest',
            group_id=config.KAFKA_GROUP_ID
        )

    def db_connection(self):
        return psycopg2.connect(
            dbname=config.DB_NAME,
            user=config.DB_USER,
            password=config.DB_PASSWORD,
            host=config.DB_HOST,
            port=config.DB_PORT
        )

    def extract_data_from_filename(self, filename):
        """
        Extracts asset_id and first_timestamp from the provided filename.

        Args:
        - filename (str): The filename string from which the data is to be extracted.

        Returns:
        - tuple: A tuple containing the asset_id, first_timestamp, and last_timestamp extracted from the filename.
        """

        parts = filename.split('_')
        asset_id = int(parts[0])
        first_timestamp = datetime.fromtimestamp(float(parts[1]))
        return asset_id, first_timestamp

    def write_to_db(self, filename, s3_key):
        """
        Writes a new record to the Postgres database containing
        information extracted from the filename and the provided s3_key.
        Each row entry will have a "was_preprocessed" set to false.  This helps
        with selecting samples which have never been preprocessed.

        Args:
        - filename (str): The filename string containing asset_id and first_timestamp.
        - s3_key (str): The s3_key associated with the file, which is also written to the database.
        """
        with self.db_connection() as conn:
            with conn.cursor() as cursor:
                asset_id, first_timestamp = self.extract_data_from_filename(filename)
                received_time = datetime.now()

                query = config.WRITE_TO_DB_QUERY
                cursor.execute(query, (asset_id, s3_key, first_timestamp, 'RECEIVED', received_time))
                conn.commit()

    def generate_filename(self, s3_key):
        """
        The s3 object key will contain the literal location so splitting the file location is performed
        to obtain the filename.
        """

        return s3_key.split('/')[-1]

    def process_new_batches(self):
        """
        Initiates the consumer to retrieve new data batches from the Kafka topic,
        and for each batch received, extracts relevant information and writes
        it to the PostgreSQL database.
        """
        print("Scanning for new raw data batches...")

        try:
            for message in self.consumer:
                data = message.value

                if 'Records' in data:
                    for record in data['Records']:
                        s3_key = record['s3']['object']['key']

                        filename = self.generate_filename(s3_key)

                        try:
                            self.write_to_db(filename, s3_key)
                        except Exception as e:
                            # Notify or log the error
                            print(f"Error while inserting into the database: {e}")

        except Exception as e:
            print(f"Error with KafkaConsumer: {e}")

    def close(self):
        self.consumer.close()

if __name__ == "__main__":
    consumer = NewFileTrigger()
    try:
        consumer.process_new_batches()
    finally:
        consumer.close()
