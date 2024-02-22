import sqlite3

conn = sqlite3.connect('readings.sqlite')

c = conn.cursor()
c.execute('''
          DROP TABLE speed
          ''')

c.execute('''
          DROP TABLE vertical
          ''')

conn.commit()
conn.close()
