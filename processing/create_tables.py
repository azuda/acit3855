import sqlite3


conn = sqlite3.connect('stats.sqlite')
c = conn.cursor()

c.execute('''
          CREATE TABLE stats
          (id INTEGER PRIMARY KEY ASC,
          num_speed_readings INTEGER NOT NULL,
          max_speed_reading INTEGER,
          num_vertical_readings INTEGER NOT NULL,
          max_vertical_reading INTEGER,
          last_updated VARCHAR(100) NOT NULL)
        ''')

conn.commit()
conn.close()

