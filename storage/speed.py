from sqlalchemy import Column, Integer, String, DateTime
from base import Base
import datetime


class Speed(Base):
  """ Speed """

  __tablename__ = "speed"

  id = Column(Integer, primary_key=True)
  user_id = Column(String(250), nullable=False)
  resort_name = Column(String(250), nullable=False)
  timestamp = Column(String(100), nullable=False)
  date_created = Column(DateTime, nullable=False)
  speed = Column(Integer, nullable=False)
  trace_id = Column(String(250), nullable=False)

  def __init__(self, user_id, resort_name, timestamp, speed, trace_id):
    """ Initializes a speed reading """
    self.user_id = user_id
    self.resort_name = resort_name
    self.timestamp = timestamp
    self.date_created = datetime.datetime.now() # Sets the date/time record is created
    self.speed = speed
    self.trace_id = trace_id

  def to_dict(self):
    """ Dictionary Representation of a speed reading """
    dict = {}
    dict['id'] = self.id
    dict['user_id'] = self.user_id
    dict['resort_name'] = self.resort_name
    dict['timestamp'] = self.timestamp
    dict['date_created'] = self.date_created
    dict['speed'] = self.speed
    dict['trace_id'] = self.trace_id

    return dict
