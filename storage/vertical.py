from sqlalchemy import Column, Integer, String, DateTime
from base import Base
import datetime


class Vertical(Base):
  """ vertical """

  __tablename__ = "vertical"

  id = Column(Integer, primary_key=True)
  user_id = Column(String(250), nullable=False)
  resort_name = Column(String(250), nullable=False)
  timestamp = Column(String(100), nullable=False)
  date_created = Column(DateTime, nullable=False)
  vertical = Column(Integer, nullable=False)
  trace_id = Column(String(250), nullable=False)

  def __init__(self, user_id, resort_name, timestamp, vertical, trace_id):
    """ Initializes a vertical reading """
    self.user_id = user_id
    self.resort_name = resort_name
    self.timestamp = timestamp
    self.date_created = datetime.datetime.now() # Sets the date/time record is created
    self.vertical = vertical
    self.trace_id = trace_id

  def to_dict(self):
    """ Dictionary Representation of a vertical reading """
    dict = {}
    dict['id'] = self.id
    dict['user_id'] = self.user_id
    dict['resort_name'] = self.resort_name
    dict['vertical'] = self.vertical
    dict['timestamp'] = self.timestamp
    dict['date_created'] = self.date_created
    dict['trace_id'] = self.trace_id

    return dict
