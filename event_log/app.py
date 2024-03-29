import connexion, json, time, os
import yaml, logging, logging.config
from pykafka import KafkaClient
from pykafka.common import OffsetType
from apscheduler.schedulers.background import BackgroundScheduler


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


def process_messages():
  """ process event_log messages """
  logger.info("Periodic processing started")

  datastore = app_config["datastore"]["filename"]
  if not os.path.exists(datastore):
    with open(datastore, "w") as f:
      f.write("[]")

  hostname = "%s:%d" % (app_config["event_log"]["hostname"],
                        app_config["event_log"]["port"])

  attempts = 0
  while attempts < app_config["event_log"]["max_retries"]:
    try:
      client = KafkaClient(hosts=hostname)
      topic = client.topics[str.encode(app_config["event_log"]["topic"])]
      logger.info(f"Connecting to Kafka - attempts: {attempts+1}")
      break
    except:
      wait_time = app_config["event_log"]["retry_interval"]
      logger.error(f"Can't connect to Kafka - retrying in {wait_time}s...")
      time.sleep(wait_time)
      attempts += 1

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

    # load datastore and add new message
    with open(datastore, "r") as f:
      data = json.loads(f.read())

    data.append(payload)

    with open(datastore, "w") as f:
      f.write(json.dumps(data, indent=4))

    logger.debug(f"Stored event_log message to {datastore}")

    # Commit the new message as being read
    consumer.commit_offsets()

def event_stats():
  # get results from event_stats.json
  with open(app_config["datastore"]["filename"], "r") as f:
    msg_raw = json.loads(f.read())

  # count the number of messages for each code
  results = {}
  for msg in msg_raw:
    code = msg["code"]
    if code not in results:
      results[code] = 1
    else:
      results[code] += 1

  return results, 200

def init_scheduler():
  sched = BackgroundScheduler(daemon=True)
  sched.add_job(process_messages, "interval",
                seconds=app_config["scheduler"]["period_sec"],
                max_instances=2)
  sched.start()


app = connexion.FlaskApp(__name__, specification_dir="")
app.add_api("openapi.yaml", strict_validation=True, validate_responses=True)


if __name__ == "__main__":
  init_scheduler()
  app.run(port=8120)

