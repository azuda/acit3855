import datetime
import json
import logging
import logging.config
import os
import time
import uuid
import connexion
import requests
import yaml
from connexion import NoContent
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from apscheduler.schedulers.background import BackgroundScheduler
from base import Base
from anomaly import Anomaly
from flask_cors import CORS
from pykafka import KafkaClient
from pykafka.common import OffsetType
from threading import Thread


if "TARGET_ENV" in os.environ and os.environ["TARGET_ENV"] == "test":
  print("In Test Environment")
  app_conf_file = "/config/app_conf.yml"
  log_conf_file = "/config/log_conf.yml"
else:
  print("In Dev Environment")
  app_conf_file = "app_conf.yml"
  log_conf_file = "log_conf.yml"

with open(app_conf_file, "r") as f:
  app_config = yaml.safe_load(f.read())

# External Logging Configuration
with open(log_conf_file, "r") as f:
  log_config = yaml.safe_load(f.read())
  logging.config.dictConfig(log_config)

logger = logging.getLogger("basicLogger")
logger.info("App Conf File: %s" % app_conf_file)
logger.info("Log Conf File: %s" % log_conf_file)


filename = app_config["datastore"]["filename"]

# create sqlite file if it does not exist
if not os.path.exists(filename):
  with open(filename, "w") as f:
    f.write("")
  os.system("python3 create_tables.py")

# link to sqlite
DB_ENGINE = create_engine("sqlite:///%s" % filename)
Base.metadata.bind = DB_ENGINE
DB_SESSION = sessionmaker(bind=DB_ENGINE)


# connect to kafka
hostname = "%s:%d" % (app_config["events"]["hostname"],
                      app_config["events"]["port"])

attempts = 0
while attempts < app_config["events"]["max_retries"]:
  try:
    client = KafkaClient(hosts=hostname)
    topic = client.topics[str.encode(app_config["events"]["topic"])]
    logger.info(f"Connecting to Kafka - attempts: {attempts+1}")
    break
  except:
    wait_time = app_config["events"]["retry_interval"]
    logger.error(f"Can't connect to Kafka - retrying in {wait_time}s...")
    time.sleep(wait_time)
    attempts += 1


logger.info("Speed anomaly threshold is:\t" + str(app_config["anomaly"]["speed_cap"]))
logger.info("Vertical anomaly threshold is:\t" + str(app_config["anomaly"]["vertical_cap"]))


def get_anomalies():
  """ gets anomalies """
  logger.info("Request for get_anomalies received")

  # read anomalies from anomaly.sqlite
  session = DB_SESSION()
  anomalies = session.query(Anomaly).order_by(Anomaly.date_created.desc()).all()
  session.close()

  if anomalies == []:
    logger.error("No anomalies found")
    return NoContent, 404
  
  logger.info("Request for get_anomalies returned")
  return anomalies, 200

def process_messages():
  """ process event messages """
  consumer = topic.get_simple_consumer(consumer_group=b'event_group',
                                        reset_offset_on_start=False,
                                        auto_offset_reset=OffsetType.LATEST)

  for msg in consumer:
    msg_str = msg.value.decode("utf-8")
    msg = json.loads(msg_str)
    payload = msg["payload"]
    logger.info("Message consumed payload: %s" % payload)


    if msg["type"] == "speed":
      if payload["speed"] > app_config["anomaly"]["speed_cap"]:
        # store the speed anomaly
        logger.info("Storing speed anomaly")
        speed_anomaly = {
          "event_id": payload["user_id"],
          "trace_id": payload["trace_id"],
          "event_type": msg["type"],
          "anomaly_type": "TooHigh",
          "description": "Speed is too high"
        }
        try:
          row = Anomaly(**speed_anomaly)
          session = DB_SESSION()
          session.add(row)
          session.commit()
          session.close()
        except Exception as e:
          logger.error("An error occurred while storing speed anomaly: %s", e)
        logger.debug("Stored speed anomaly with trace_id %s", payload["trace_id"])
    elif msg["type"] == "vertical":
      if payload["vertical"] > app_config["anomaly"]["vertical_cap"]:
        # store the vertical anomaly
        logger.info("Storing vertical anomaly")
        vertical_anomaly = {
          "event_id": payload["user_id"],
          "trace_id": payload["trace_id"],
          "event_type": msg["type"],
          "anomaly_type": "TooHigh",
          "description": "Vertical is too high"
        }
        try:
          row = Anomaly(**vertical_anomaly)
          session = DB_SESSION()
          session.add(row)
          session.commit()
          session.close()
        except Exception as e:
          logger.error("An error occurred while storing speed anomaly: %s", e)
        logger.debug("Stored vertical anomaly with trace_id %s", payload["trace_id"])

    consumer.commit_offsets()

app = connexion.FlaskApp(__name__, specification_dir="")
app.add_api("openapi.yaml", strict_validation=True, validate_responses=True)

CORS(app.app, resources={r"/*": {"origins": "*"}})

if __name__ == "__main__":
  t1 = Thread(target=process_messages, daemon=True)
  t1.start()
  app.run(port=8130)
