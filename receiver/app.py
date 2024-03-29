import connexion, json, datetime, requests, time, os
from connexion import NoContent
import yaml, logging, logging.config, uuid
from pykafka import KafkaClient


# MAX_EVENTS = 5
# EVENT_FILE = "events.json"
# url = "http://localhost:8090"

# with open("app_conf.yml", "r") as f:
#   app_config = yaml.safe_load(f.read())

# with open("log_conf.yml", "r") as f:
#   log_config = yaml.safe_load(f.read())
#   logging.config.dictConfig(log_config)
# logger = logging.getLogger("basicLogger")

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


# connect to Kafka
attempts = 0
hostname = app_config["events"]["hostname"]
port = app_config["events"]["port"]
host = f"{hostname}:{port}"
while attempts < app_config["events"]["max_retries"]:
  try:
    client = KafkaClient(hosts=host)
    topic = client.topics[str.encode(app_config["events"]["topic"])]
    producer = topic.get_sync_producer()
    logger.info(f"Connecting to Kafka - attempts: {attempts+1}")
    break
  except:
    wait_time = app_config["events"]["retry_interval"]
    logger.error(f"Can't connect to Kafka - retrying in {wait_time}s...")
    time.sleep(wait_time)
    attempts += 1

# publish message to event_log
event_log_message = {
  "id": str(uuid.uuid4()),
  "message": "0001 ~ Ready to receive messages on RESTful API:8080",
  "code": "0001",
  "datetime": datetime.datetime.now().strftime("%Y-%m-%dT%H:%M:%S")
}
event_log_message_str = json.dumps(event_log_message)
event_log_topic = client.topics[str.encode(app_config["event_log"]["topic"])]
event_log_producer = event_log_topic.get_sync_producer()
event_log_producer.produce(event_log_message_str.encode("utf-8"))
logger.info(f"Published message to event_log:\n{event_log_message_str}")


def add_speed(body):
  """ receives speed event """
  trace_id = str(uuid.uuid4())
  body["trace_id"] = trace_id
  logger.info(f"Received event speed request with a trace id of {trace_id}")
  # response = requests.post(app_config["store_speed_event"]["url"], json = body, headers = {"Content-Type": "application/json"})
  
  # client = KafkaClient(hosts=f"{app_config["events"]["hostname"]}:{app_config["events"]["port"]}")
  # topic = client.topics[str.encode(app_config["events"]["topic"])]
  # producer = topic.get_sync_producer()
  msg = {
    "type": "speed",
    "datetime" : datetime.datetime.now().strftime("%Y-%m-%dT%H:%M:%S"),
    "payload": body
  }
  msg_str = json.dumps(msg)
  producer.produce(msg_str.encode("utf-8"))
  logger.info(f"msg_str:\n{msg_str}")
  # logger.info(f"Returned event speed response (Id: ${trace_id}) with status f{response.status_code}")
  logger.info(f"Returned event speed response (Id: ${trace_id})")

  return NoContent, 201

def add_vertical(body):
  """ receives vertical event """
  trace_id = str(uuid.uuid4())
  body["trace_id"] = trace_id
  logger.info(f"Received event vertical request with a trace id of {trace_id}")
  # response = requests.post(app_config["store_vertical_event"]["url"], json = body, headers = {"Content-Type": "application/json"})
  
  # client = KafkaClient(hosts=f'{app_config["events"]["hostname"]}:{app_config["events"]["port"]}')
  # topic = client.topics[str.encode(app_config["events"]["topic"])]
  # producer = topic.get_sync_producer()
  msg = {
    "type": "vertical",
    "datetime" : datetime.datetime.now().strftime("%Y-%m-%dT%H:%M:%S"),
    "payload": body
  }
  msg_str = json.dumps(msg)
  producer.produce(msg_str.encode("utf-8"))
  logger.info(f"msg_str:\n{msg_str}")
  # logger.info(f"Returned event vertical response (Id: ${trace_id}) with status f{response.status_code}")
  logger.info(f"Returned event vertical response (Id: ${trace_id})")

  return NoContent, 201


app = connexion.FlaskApp(__name__, specification_dir="")
app.add_api("openapi.yaml", strict_validation=True, validate_responses=True)


if __name__ == "__main__":
  app.run(port=8080)

