import mysql.connector


# conn = mysql.connector.connect(host="localhost", user="root",
#                               password="password", database="events")  # nosec
conn = mysql.connector.connect(host="kafka-acit3855.eastus2.cloudapp.azure.com",
                              user="user", password="password", database="events")  # nosec

cursor = conn.cursor()
cursor.execute('''
          CREATE TABLE speed
          (id INT NOT NULL AUTO_INCREMENT,
          user_id VARCHAR(250) NOT NULL,
          resort_name VARCHAR(250) NOT NULL,
          speed INTEGER NOT NULL,
          timestamp VARCHAR(100) NOT NULL,
          date_created VARCHAR(100) NOT NULL,
          trace_id VARCHAR(250) NOT NULL,
          CONSTRAINT speed_pk PRIMARY KEY (id))
          ''')

cursor.execute('''
          CREATE TABLE vertical
          (id INT NOT NULL AUTO_INCREMENT,
          user_id VARCHAR(250) NOT NULL,
          resort_name VARCHAR(250) NOT NULL,
          vertical INTEGER NOT NULL,
          timestamp VARCHAR(100) NOT NULL,
          date_created VARCHAR(100) NOT NULL,
          trace_id VARCHAR(250) NOT NULL,
          CONSTRAINT vertical_pk PRIMARY KEY (id))
          ''')

conn.commit()
conn.close()
