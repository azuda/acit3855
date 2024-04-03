import connexion
import datetime
import json
import logging
import logging.config
import os
import re
import time
import uuid
import yaml
from connexion import NoContent
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from base import Base
from speed import Speed
from vertical import Vertical
from pykafka import KafkaClient
from pykafka.common import OffsetType
from threading import Thread


# with open('app_conf.yml', 'r') as f:
#   app_config = yaml.safe_load(f.read())

# with open('log_conf.yml', 'r') as f:
#   log_config = yaml.safe_load(f.read())
#   logging.config.dictConfig(log_config)
# logger = logging.getLogger('basicLogger')

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
logger.info("App Conf File: %s", app_conf_file)
logger.info("Log Conf File: %s", log_conf_file)


# DB_ENGINE = create_engine("sqlite:///readings.sqlite")
user = app_config['datastore']['user']
password = app_config['datastore']['password']
hostname = app_config['datastore']['hostname']
port = app_config['datastore']['port']
db_name = app_config['datastore']['db']
# DB_ENGINE = create_engine(f"mysql+pymysql://{user}:{password}@{hostname}:{port}/{db_name}")
DB_ENGINE = create_engine(
  f"mysql+pymysql://{user}:{password}@{hostname}:{port}/{db_name}",
  pool_size=20,       # max number of db connections in pool
  pool_recycle=60,    # auto recycle connection after 60 secs
  pool_pre_ping=True  # test connections are alive on each checkout
)
Base.metadata.bind = DB_ENGINE
DB_SESSION = sessionmaker(bind = DB_ENGINE)
logger.info("Connecting to DB ~ Host: %s, Port: %s, DB: %s", hostname, port, db_name)

# def add_speed(body):
#   """ receives speed event """
#   session = DB_SESSION()
#   s = Speed(body['user_id'],
#             body['resort_name'],
#             body['timestamp'],
#             body['speed'],
#             body['trace_id'])
#   session.add(s)
#   session.commit()
#   session.close()
#   logger.debug(f"Stored event speed request with trace_id {body['trace_id']}")
#   return NoContent, 201

# def add_vertical(body):
#   """ receives vertical event """
#   session = DB_SESSION()
#   v = Vertical(body['user_id'],
#               body['resort_name'],
#               body['timestamp'],
#               body['vertical'],
#               body['trace_id'])
#   session.add(v)
#   session.commit()
#   session.close()
#   logger.debug(f"Stored event vertical request with trace_id {body['trace_id']}")
#   return NoContent, 201

def get_speed(start_time, end_time):
  """ gets new speed readings between the start and end timestamps """
  session = DB_SESSION()

  # start_time_datetime = datetime.datetime.strptime(start_time, "%Y-%m-%dT%H:%M:%S")
  # end_time_datetime = datetime.datetime.strptime(end_time, "%Y-%m-%dT%H:%M:%S")
  # start_time_datetime = datetime.datetime.strptime(start_time, "%Y-%m-%dT%H:%M:%S.%f%z")
  # end_time_datetime = datetime.datetime.strptime(end_time, "%Y-%m-%dT%H:%M:%S.%f%z")
  start_time_datetime = parse_datetime_with_tz(start_time)
  end_time_datetime = parse_datetime_with_tz(end_time)

  results = session.query(Speed).filter(Speed.date_created >= start_time_datetime, 
                                        Speed.date_created < end_time_datetime)
  session.close()

  results_list = []
  for reading in results:
    results_list.append(reading.to_dict())

  logger.info("Query for Speed readings after %s returns %d results" % (start_time_datetime, len(results_list)))
  return results_list, 200

def get_vertical(start_time, end_time):
  """ gets new vertical readings between the start and end timestamps """
  session = DB_SESSION()

  # start_time_datetime = datetime.datetime.strptime(start_time, "%Y-%m-%dT%H:%M:%S")
  # end_time_datetime = datetime.datetime.strptime(end_time, "%Y-%m-%dT%H:%M:%S")
  # start_time_datetime = datetime.datetime.strptime(start_time, "%Y-%m-%dT%H:%M:%S.%f%z")
  # end_time_datetime = datetime.datetime.strptime(end_time, "%Y-%m-%dT%H:%M:%S.%f%z")
  start_time_datetime = parse_datetime_with_tz(start_time)
  end_time_datetime = parse_datetime_with_tz(end_time)

  results = session.query(Vertical).filter(Vertical.date_created >= start_time_datetime, 
                                            Vertical.date_created < end_time_datetime)
  session.close()

  results_list = []
  for reading in results:
    results_list.append(reading.to_dict())

  logger.info("Query for Vertical readings after %s returns %d results" % (start_time_datetime, len(results_list)))
  return results_list, 200

def process_messages():
  """ process event messages """
  hostname = "%s:%d" % (app_config["events"]["hostname"],
                        app_config["events"]["port"])
  
  # client = KafkaClient(hosts=hostname)
  # topic = client.topics[str.encode(app_config["events"]["topic"])]

  attempts = 0
  while attempts < app_config["events"]["max_retries"]:
    try:
      client = KafkaClient(hosts=hostname)
      topic = client.topics[str.encode(app_config["events"]["topic"])]
      logger.info("Connecting to Kafka - attempts: %s", attempts+1)
      break
    except:
      wait_time = app_config["events"]["retry_interval"]
      logger.error("Can't connect to Kafka - retrying in %ss...", wait_time)
      time.sleep(wait_time)
      attempts += 1
  
  # publish message to event_log
  event_log_message = {
  "id": str(uuid.uuid4()),
  "message": "0002 ~ Ready to consume messages on topic 'events'",
  "code": "0002",
  "datetime": datetime.datetime.now().strftime("%Y-%m-%dT%H:%M:%S")
  }
  event_log_message_str = json.dumps(event_log_message)
  event_log_topic = client.topics[str.encode(app_config["events"]["topic2"])]
  event_log_producer = event_log_topic.get_sync_producer()
  event_log_producer.produce(event_log_message_str.encode("utf-8"))
  logger.info("Published message to event_log:\n%s", event_log_message_str)

  # Create a consume on a consumer group, that only reads new messages
  # (uncommitted messages) when the service re-starts (i.e., it doesn't
  # read all the old messages from the history in the message queue).
  consumer = topic.get_simple_consumer(consumer_group=b'event_group',
                                        reset_offset_on_start=False,
                                        auto_offset_reset=OffsetType.LATEST)

  # This is blocking - it will wait for a new message
  for msg in consumer:
    msg_str = msg.value.decode("utf-8")
    msg = json.loads(msg_str)
    logger.info("Message: %s" % msg)

    payload = msg["payload"]

    if msg["type"] == "speed":
      # Store the event1 (i.e., the payload) to the DB
      session = DB_SESSION()
      speed_event = Speed(payload['user_id'],
                          payload['resort_name'],
                          payload['timestamp'],
                          payload['speed'],
                          payload['trace_id'])
      session.add(speed_event)
      session.commit()
      session.close()
      logger.debug("Stored event speed request with trace_id %s", payload['trace_id'])
    elif msg["type"] == "vertical":
      # Store the event2 (i.e., the payload) to the DB
      session = DB_SESSION()
      vert_event = Vertical(payload['user_id'],
                            payload['resort_name'],
                            payload['timestamp'],
                            payload['vertical'],
                            payload['trace_id'])
      session.add(vert_event)
      session.commit()
      session.close()
      logger.debug("Stored event vertical request with trace_id %s", payload['trace_id'])

    # Commit the new message as being read
    consumer.commit_offsets()

def parse_datetime_with_tz(dt_str):
  match = re.match(r"(.*)(\.\d+)([-+]\d+:\d+)", dt_str)
  if match is not None:
    dt_str, us_str, tz_str = match.groups()
    micro_sec = int(us_str.lstrip("."), 10)
    tz_hours, tz_minutes = map(int, tz_str.split(":"))
    tz_delta = datetime.timedelta(hours=tz_hours, minutes=tz_minutes)
    t_zone = datetime.timezone(tz_delta)
    out_dt = datetime.datetime.strptime(dt_str, "%Y-%m-%dT%H:%M:%S")
    return out_dt.replace(microsecond=micro_sec, tzinfo=t_zone)



app = connexion.FlaskApp(__name__, specification_dir='')
app.add_api("openapi.yaml", strict_validation=True, validate_responses=True)


if __name__ == "__main__":
  t1 = Thread(target=process_messages, daemon=True)
  # t1.setDaemon(True)
  t1.start()
  app.run(port=8090)

