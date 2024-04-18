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

message_limit = app_config["event_anomaly"]["limit"]


# connect to kafka
hostname = "%s:%d" % (app_config["event_anomaly"]["hostname"],
                      app_config["event_anomaly"]["port"])

attempts = 0
while attempts < app_config["event_anomaly"]["max_retries"]:
  try:
    client = KafkaClient(hosts=hostname)
    topic = client.topics[str.encode(app_config["event_anomaly"]["topic"])]
    logger.info(f"Connecting to Kafka - attempts: {attempts+1}")
    break
  except:
    wait_time = app_config["event_anomaly"]["retry_interval"]
    logger.error(f"Can't connect to Kafka - retrying in {wait_time}s...")
    time.sleep(wait_time)
    attempts += 1


def get_anomalies():
  """ gets anomalies """
  logger.info("Request for get_anomalies started")

  # read recent anomalies
  session = DB_SESSION()
  anomalies = session.query(Anomaly)#.order_by(Anomaly.last_updated.desc()).first()
  session.close()

  # return 404 if no anomalies found
  if anomalies == []:
    logger.error("No anomalies found")
    return "Anomalies do not exist", 404

  # return anomaly
  response = {
    "id":           anomalies.id,
    "event_id":     anomalies.event_id,
    "trace_id":     anomalies.trace_id,
    "event_type":   anomalies.event_type,
    "anomaly_type": anomalies.anomaly_type,
    "description":  anomalies.description
  }
  logger.debug(f"Response:\n{json.dumps(response, indent=2)}")

  logger.info("Request for get_anomalies completed")
  return response, 200

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
