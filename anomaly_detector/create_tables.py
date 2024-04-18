import sqlite3


conn = sqlite3.connect('anomaly.sqlite')
c = conn.cursor()

c.execute('''
          CREATE TABLE anomaly
          (id INTEGER PRIMARY KEY ASC, 
          event_id VARCHAR(250) NOT NULL,
          trace_id VARCHAR(250) NOT NULL,
          event_type VARCHAR(100) NOT NULL,
          anomaly_type VARCHAR(100) NOT NULL,
          description VARCHAR(250) NOT NULL,
          date_created VARCHAR(100) NOT NULL)
''')

conn.commit()
conn.close()

