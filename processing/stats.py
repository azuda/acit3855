from sqlalchemy import Column, Integer, DateTime
from base import Base


class Stats(Base):
  """ Processing Statistics """
  __tablename__ = "stats"
  id = Column(Integer, primary_key=True)
  num_speed_readings = Column(Integer, nullable=False)
  max_speed_reading = Column(Integer, nullable=True)
  num_vertical_readings = Column(Integer, nullable=False)
  max_vertical_reading = Column(Integer, nullable=True)
  last_updated = Column(DateTime, nullable=False)

  def __init__(self, num_speed_readings, max_speed_reading,
              num_vertical_readings, max_vertical_reading,
              last_updated):
    """ initializes a processing stats object """
    self.num_speed_readings = num_speed_readings
    self.max_speed_reading = max_speed_reading
    self.num_vertical_readings = num_vertical_readings
    self.max_vertical_reading = max_vertical_reading
    self.last_updated = last_updated

  def to_dict(self):
    """ Dictionary Representation of a statistics """
    dict = {}
    dict['num_speed_readings'] = self.num_speed_readings
    dict['max_speed_reading'] = self.max_speed_reading
    dict['num_vertical_readings'] = self.num_vertical_readings
    dict['max_vertical_reading'] = self.max_vertical_reading
    dict['last_updated'] = self.last_updated.strftime("%Y-%m-%dT%H:%M:%S")
    return dict

