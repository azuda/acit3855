import connexion, yaml, logging, logging.config, json, requests, datetime, os
from connexion import NoContent
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from apscheduler.schedulers.background import BackgroundScheduler
from base import Base
from stats import Stats
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


# link to sqlite
DB_ENGINE = create_engine("sqlite:///%s" % app_config["datastore"]["filename"])
Base.metadata.bind = DB_ENGINE
DB_SESSION = sessionmaker(bind=DB_ENGINE)


def get_stats():
  """ gets processed stats of readings """
  logger.info("Request for get_stats started")

  # read most recent stats
  session = DB_SESSION()
  stats = session.query(Stats).order_by(Stats.last_updated.desc()).first()
  session.close()

  # return 404 if no stats found
  if stats == []:
    logger.error("No stats found")
    return "Stats do not exist", 404

  # return current stats
  response = {
    "num_speed_readings":     stats.num_speed_readings,
    "max_speed_reading":      stats.max_speed_reading,
    "num_vertical_readings":  stats.num_vertical_readings,
    "max_vertical_reading":   stats.max_vertical_reading,
    "last_updated":           stats.last_updated.strftime("%Y-%m-%dT%H:%M:%S.%f")
  }
  logger.debug(f"Response:\n{json.dumps(response, indent=2)}")

  logger.info("Request for get_stats completed")
  return response, 200

def populate_stats():
  """ periodically update stats """
  logger.info("Period processing started")
  # print("Period processing started")

  # read stats sorted by last_updated
  session = DB_SESSION()
  current_stats = session.query(Stats).order_by(Stats.last_updated.desc()).all()
  session.close()

  # populate stats table if empty
  if current_stats == []:
    logger.info("Stats table is empty - adding default values")
    # print("Stats table is empty - adding default values")
    defaults = Stats(0, 0, 0, 0,
                    datetime.datetime.strptime("2001-02-10T00:00:00.123456", "%Y-%m-%dT%H:%M:%S.%f"))
    session = DB_SESSION()
    session.add(defaults)
    session.commit()
    session.close()
    return defaults, 201

  # define time range
  start = current_stats[0].last_updated.strftime("%Y-%m-%dT%H:%M:%S.%f")
  current = datetime.datetime.now().strftime("%Y-%m-%dT%H:%M:%S.%f")
  # start = "2001-02-10T00:00:00.123456"

  # get events from storage service within given time range
  speed_response = requests.get(app_config["eventstore"]["url"] + "/readings/speed",
                                headers={"Content-Type": "application/json"},
                                params={"start_time": start + "+00:00",
                                        "end_time": current + "+00:00"})
  vertical_response = requests.get(app_config["eventstore"]["url"] + "/readings/vertical",
                                    headers={"Content-Type": "application/json"},
                                    params={"start_time": start + "+00:00",
                                            "end_time": current + "+00:00"})
  speed_events = speed_response.json()
  vertical_events = vertical_response.json()

  # handle status codes from storage service
  if speed_response.status_code != 200:
    logger.error(f"Bad status: {speed_response.status_code}")
    return "Datastore error", 404
  if vertical_response.status_code != 200:
    logger.error(f"Bad status: {vertical_response.status_code}")
    return "Datastore error", 404

  logger.info(f"Number of speed events between {start} and {current}: {len(speed_events)}")
  logger.info(f"Number of vertical events between {start} and {current}: {len(vertical_events)}")
  # print(f"Number of speed events between {start} and {current}: {len(speed_events)}")
  # print(f"Number of vertical events between {start} and {current}: {len(vertical_events)}")

  # calculate new stats
  max_speed_now = max([x["speed"] for x in speed_events], default=0)
  max_vertical_now = max([x["vertical"] for x in vertical_events], default=0)
  if current_stats[0].max_speed_reading < max_speed_now:
    max_speed = max_speed_now
  else:
    max_speed = current_stats[0].max_speed_reading
  
  if current_stats[0].max_vertical_reading < max_vertical_now:
    max_vertical = max_vertical_now
  else:
    max_vertical = current_stats[0].max_vertical_reading

  stats = {
    "num_speed_readings": current_stats[0].num_speed_readings + len(speed_events),
    "max_speed_reading": max_speed,
    "num_vertical_readings": current_stats[0].num_vertical_readings + len(vertical_events),
    "max_vertical_reading": max_vertical,
    "last_updated": current
  }

  # log trace_id of processed events
  for event in speed_events + vertical_events:
    event_type = "speed" if "speed" in event else "vertical"
    # logger.debug(f"Processed new {event_type} reading with trace_id {event["trace_id"]}")
    # print(f"Processed new {event_type} reading with trace_id {event["trace_id"]}")
  
  # write new row to stats table
  row = Stats(stats["num_speed_readings"],
              stats["max_speed_reading"],
              stats["num_vertical_readings"],
              stats["max_vertical_reading"],
              datetime.datetime.strptime(stats["last_updated"], "%Y-%m-%dT%H:%M:%S.%f"))
  session = DB_SESSION()
  session.add(row)
  session.commit()
  session.close()
  logger.debug(f"Stats updated:\n{json.dumps(stats, indent=2)}")
  # print(f"Stats updated: {json.dumps(stats, indent=2)}")

  logger.info("Period processing completed successfully")
  # print("Period processing completed successfully")
  return stats, 200

def init_scheduler():
  sched = BackgroundScheduler(daemon=True)
  sched.add_job(populate_stats, 'interval',
                seconds=app_config['scheduler']['period_sec'],
                max_instances=2)
  sched.start()


app = connexion.FlaskApp(__name__, specification_dir='')
app.add_api("openapi.yaml", strict_validation=True, validate_responses=True)

CORS(app.app, resources={r"/*": {"origins": "*"}})

if __name__ == "__main__":
  init_scheduler()
  app.run(port=8100)
