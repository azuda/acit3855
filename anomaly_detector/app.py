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


def get_anomalies():
  """ gets anomalies """
  logger.info("Request for get_anomalies started")

  consumer = topic.get_simple_consumer(consumer_group=b'event_group',
                                      reset_offset_on_start=False,
                                      auto_offset_reset=OffsetType.LATEST)

  for msg in consumer:
    msg_str = msg.value.decode("utf-8")
    msg = json.loads(msg_str)
    logger.info("Message: %s" % msg)

  #   # load datastore and add new message
  #   with open(filename, "r") as f:
  #     data = json.loads(f.read())

  #   data.append(msg)
  #   logger.info(f"Message added to file {filename}: {msg}")

  #   with open(filename, "w") as f:
  #     f.write(json.dumps(data, indent=4))

  #   logger.debug(f"Stored event_log message to {filename}")

  #   # read recent anomalies
  #   session = DB_SESSION()
  #   anomalies = session.query(Anomaly)#.order_by(Anomaly.last_updated.desc()).first()
  #   session.close()

  #   # Commit the new message as being read
  #   consumer.commit_offsets()

  # # return anomaly
  # response = {
  #   "id":           anomalies.id,
  #   "event_id":     anomalies.event_id,
  #   "trace_id":     anomalies.trace_id,
  #   "event_type":   anomalies.event_type,
  #   "anomaly_type": anomalies.anomaly_type,
  #   "description":  anomalies.description
  # }
  # logger.debug(f"Response:\n{json.dumps(response, indent=2)}")

  # logger.info("Request for get_anomalies completed")
  # return response, 200
  return

# def init_scheduler():
#   sched = BackgroundScheduler(daemon=True)
#   sched.add_job(populate_stats, "interval",
#                 seconds=app_config["scheduler"]["period_sec"],
#                 max_instances=2)
#   sched.start()


app = connexion.FlaskApp(__name__, specification_dir="")
app.add_api("openapi.yaml", strict_validation=True, validate_responses=True)

CORS(app.app, resources={r"/*": {"origins": "*"}})

if __name__ == "__main__":
  # init_scheduler()
  app.run(port=8130)
