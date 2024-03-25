import connexion, yaml, logging, logging.config, json, os
from pykafka import KafkaClient
from flask_cors import CORS


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


def get_speed_reading(index):
  """ get speed reading in history """
  hostname = "%s:%d" % (app_config["events"]["hostname"],
                        app_config["events"]["port"])
  client = KafkaClient(hosts=hostname)
  topic = client.topics[str.encode(app_config["events"]["topic"])]

  # Here we reset the offset on start so that we retrieve
  # messages at the beginning of the message queue.
  # To prevent the for loop from blocking, we set the timeout to
  # 100ms. There is a risk that this loop never stops if the
  # index is large and messages are constantly being received!
  consumer = topic.get_simple_consumer(reset_offset_on_start=True, consumer_timeout_ms=1000)

  logger.info("Retrieving speed at index %d" % index)
  try:
    for msg in consumer:
      msg_str = msg.value.decode('utf-8')
      msg = json.loads(msg_str)
      if msg["type"] == "speed":
        if index == 0:
          return msg, 200
        index -= 1
  except:
    print("No more messages found")
    logger.error("No more messages found")

  logger.error("Could not find speed at index %d" % index)
  return { "message": "Not Found"}, 404

def get_vertical_reading(index):
  """ get vertical reading in history """
  hostname = "%s:%d" % (app_config["events"]["hostname"],
                        app_config["events"]["port"])
  client = KafkaClient(hosts=hostname)
  topic = client.topics[str.encode(app_config["events"]["topic"])]
  consumer = topic.get_simple_consumer(reset_offset_on_start=True, consumer_timeout_ms=1000)

  logger.info("Retrieving vertical at index %d" % index)
  try:
    for msg in consumer:
      msg_str = msg.value.decode('utf-8')
      msg = json.loads(msg_str)
      if msg["type"] == "vertical":
        if index == 0:
          return msg, 200
        index -= 1
  except:
    print("No more messages found")
    logger.error("No more messages found")

  logger.error("Could not find vertical at index %d" % index)
  return { "message": "Not Found"}, 404


app = connexion.FlaskApp(__name__, specification_dir='')
app.add_api("openapi.yml", strict_validation=True, validate_responses=True)

CORS(app.app, resources={r"/*": {"origins": "*"}})

if __name__ == "__main__":
  app.run(port=8110)


