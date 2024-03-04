import connexion, yaml, logging, logging.config, datetime, json
from connexion import NoContent
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from base import Base
from speed import Speed
from vertical import Vertical
from pykafka import KafkaClient
from pykafka.common import OffsetType
from threading import Thread


with open('app_conf.yml', 'r') as f:
  app_config = yaml.safe_load(f.read())

with open('log_conf.yml', 'r') as f:
  log_config = yaml.safe_load(f.read())
  logging.config.dictConfig(log_config)
logger = logging.getLogger('basicLogger')

# DB_ENGINE = create_engine("sqlite:///readings.sqlite")
user = app_config['datastore']['user']
password = app_config['datastore']['password']
hostname = app_config['datastore']['hostname']
port = app_config['datastore']['port']
db_name = app_config['datastore']['db']
DB_ENGINE = create_engine(f"mysql+pymysql://{user}:{password}@{hostname}:{port}/{db_name}")
Base.metadata.bind = DB_ENGINE
DB_SESSION = sessionmaker(bind = DB_ENGINE)
logger.info(f"Connecting to DB ~ Host: {hostname}, Port: {port}, DB: {db_name}")

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
  start_time_datetime = datetime.datetime.strptime(start_time, "%Y-%m-%dT%H:%M:%S.%f%z")
  end_time_datetime = datetime.datetime.strptime(end_time, "%Y-%m-%dT%H:%M:%S.%f%z")

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
  start_time = start_time.replace(':', '', 1)
  end_time = end_time.replace(':', '', 1)
  start_time_datetime = datetime.datetime.strptime(start_time, "%Y-%m-%dT%H:%M:%S.%f%Z")
  end_time_datetime = datetime.datetime.strptime(end_time, "%Y-%m-%dT%H:%M:%S.%f%Z")

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
  client = KafkaClient(hosts=hostname)
  topic = client.topics[str.encode(app_config["events"]["topic"])]

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
      s = Speed(payload['user_id'],
                payload['resort_name'],
                payload['timestamp'],
                payload['speed'],
                payload['trace_id'])
      session.add(s)
      session.commit()
      session.close()
      logger.debug(f"Stored event speed request with trace_id {payload['trace_id']}")
    elif msg["type"] == "vertical":
      # Store the event2 (i.e., the payload) to the DB
      session = DB_SESSION()
      v = Vertical(payload['user_id'],
                payload['resort_name'],
                payload['timestamp'],
                payload['vertical'],
                payload['trace_id'])
      session.add(v)
      session.commit()
      session.close()
      logger.debug(f"Stored event vertical request with trace_id {payload['trace_id']}")

    # Commit the new message as being read
    consumer.commit_offsets()


app = connexion.FlaskApp(__name__, specification_dir='')
app.add_api("openapi.yaml", strict_validation=True, validate_responses=True)


if __name__ == "__main__":
  t1 = Thread(target=process_messages, daemon=True)
  # t1.setDaemon(True)
  t1.start()
  app.run(port=8090)

