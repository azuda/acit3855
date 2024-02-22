import sqlite3


conn = sqlite3.connect('readings.sqlite')

c = conn.cursor()
c.execute('''
          CREATE TABLE speed
          (id INTEGER PRIMARY KEY ASC, 
          user_id VARCHAR(250) NOT NULL,
          resort_name VARCHAR(250) NOT NULL,
          speed INTEGER NOT NULL,
          timestamp VARCHAR(100) NOT NULL,
          date_created VARCHAR(100) NOT NULL,
          trace_id VARCHAR(250) NOT NULL)
          ''')

c.execute('''
          CREATE TABLE vertical
          (id INTEGER PRIMARY KEY ASC, 
          user_id VARCHAR(250) NOT NULL,
          resort_name VARCHAR(250) NOT NULL,
          vertical INTEGER NOT NULL,
          timestamp VARCHAR(100) NOT NULL,
          date_created VARCHAR(100) NOT NULL,
          trace_id VARCHAR(250) NOT NULL)
          ''')

conn.commit()
conn.close()
