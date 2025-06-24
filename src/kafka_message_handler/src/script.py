"""
Script consumes kafka messages from given KAFKA_TOPIC.

It assumes that the kafka messages are in JSON format and contain
fields like 'SensorName', 'SensorValue', 'StateName', and 'StateValue' and 'Timestamp'.

It assumes that kafka topic has three partitions (0, 1, 2).
It then stores the data in a MongoDB database named 'iiot_timeseries'
in collections 'sensors' and 'states'
"""

import json
import logging
import os
import time
import sys
import datetime
from kafka import KafkaConsumer, TopicPartition
from pymongo import MongoClient



# Set loging system
logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger("__name__")


def get_env_var(
    env_var: str, 
    req_type=None, 
    default: str | int | float = None
) -> str | int | float:
    """Read env variable and return its required value with log information

    Args:
        env_var (str): Name of environment variable
        req_type (str, int, float): required data type of env variable.
        default (str, int, float): will be returned if it's set and env variable does not exist

    Raises:
        SystemExit: Stop program if set type_var has not passed validate
        SystemExit: Stop program if env var does not exist and default is not set
        SystemExit: Stop program if cannot convert env var variable to req_type
    """
    # set type and value of env variable
    env_type = type(env_var)
    env_val = os.getenv(env_var, None)

    # check if input convert type is correct or not (if not, return error and stop program)
    allow_convert = [str, int, float]
    if req_type not in allow_convert and req_type is not None:
        logger.error(
            "Cannot convert value of env_var %s to %s. \
                Allowed convert type: str, int, float",
                env_var, req_type
        )
        raise SystemExit

    # Return value of env variable
    if env_val is None and default is None:
        # env_var doesn't exist and default value not set
        logger.error("Env variable %s doesn't exist", env_var)
        raise SystemExit
    elif env_val is None:
        # env_var doesn't exist but return default (default is different than none)
        logger.warning(
            "Env variable %s does not exist, return default value: %s",
            env_var, default
        )
        return default
    elif env_type is not req_type and req_type is not None:
        # env var exists and it's type is diffrent as configured
        try:
            converted_env = req_type(env_val)
            logger.info(
                "Env variable %s value: %s. \
                    Converted from %s to %s.",
                    env_var, env_val, env_type, req_type
            )
            return converted_env
        except Exception as e:
            logger.error(
                "Convert env_var variable %s from %s to %s failed: %s",
                env_var, env_type, req_type, e
            )
            raise SystemExit
    else:
        # env_var exists, and has the same type (or we not set type)
        logger.info("Env variable %s value: %s, type: %s",
                    env_var, env_val, env_type)
        return env_val


# Assignment const variable from env or created using env
logger.info("Setting const global variables")

KAFKA_TOPIC = get_env_var("KAFKA_TOPIC", str)
KAFKA_HOST = get_env_var("KAFKA_HOST", str)
KAFKA_PORT = get_env_var("KAFKA_PORT", int)
logger.info("KAFKA_TOPIC value is: %s ", KAFKA_TOPIC)
logger.info("KAFKA_HOST: %s  KAFKA_PORT: %s", KAFKA_HOST, KAFKA_PORT)


MONGO_HOST = get_env_var("MONGO_HOST", str)
MONGO_PORT = get_env_var("MONGO_PORT", int)

MONGO_URI = "mongodb://" + MONGO_HOST + ":" + str(MONGO_PORT)
logger.info("MONGO_URI value is:  %s", MONGO_URI)


if __name__ == "__main__":


    try:
        # Create a Kafka Consumer
        consumer = KafkaConsumer(
            #Kafka server to connect
            bootstrap_servers=[KAFKA_HOST + ":" + str(KAFKA_PORT)],
            auto_offset_reset="earliest",
            enable_auto_commit=True
        )
    except Exception as e:
        logger.error("Failed to create Kafka Consumer: %s", e)
        sys.exit(1)
    else:
        # assign the consumer to specific partitions of the topic
        consumer.assign(
                        [TopicPartition(KAFKA_TOPIC, 0),
                        TopicPartition(KAFKA_TOPIC, 1),
                        TopicPartition(KAFKA_TOPIC, 2)])

        # Create a MongoDB connection
        mongo_client = MongoClient(MONGO_URI)

        # Select the database and collection
        db = mongo_client.iiot_timeseries
        col_sensors = db.sensors
        col_states = db.states

        for msg in consumer:
            try:
                # Decode the message from Kafka and convert it to a Python dictionary
                msg_dict = json.loads(msg.value.decode('utf-8').replace('+0', '0'))
            except Exception as e:
                logger.error("Failed to decode message: %s", e)
            else:
                logger.info("kafka msg topic: %s | partition: %s | offset %s",
                            msg.topic, msg.partition, msg.offset)
                logger.info("msg timestamp: %s | key: %s | value: %s",
                            msg.timestamp, msg.key.decode('utf-8'), msg.value.decode('utf-8'))

                if "SensorName" in msg_dict:
                    logger.info("SensorName found in msg")

                    mongodb_document = {
                    "lineName": msg_dict['LineName'],
                    "machineName": msg_dict['MachineName'],
                    "sensorName": msg_dict['SensorName'],
                    "sensorValue": msg_dict['SensorValue'],
                    # convert unix timestamp to datetime
                    "date": datetime.datetime.fromtimestamp(msg_dict['Timestamp'],
                                                            datetime.timezone.utc)
                    #"date": datetime.datetime.now(tz=datetime.timezone.utc)
                    }
                    col_sensors.insert_one(mongodb_document)

                elif "StateName" in msg_dict:
                    logger.info("StateName found in data")

                    mongodb_document = {
                    "lineName": msg_dict['LineName'],
                    "machineName": msg_dict['MachineName'],
                    "stateName": msg_dict['StateName'],
                    "stateValue": msg_dict['StateValue'],
                    "date": datetime.datetime.fromtimestamp(msg_dict['Timestamp'],
                                                            datetime.timezone.utc)
                    }
                    col_states.insert_one(mongodb_document)
                time.sleep(0.02)
                logger.debug("msg data: %s", msg_dict)




