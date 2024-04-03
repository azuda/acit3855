import mysql.connector


# conn = mysql.connector.connect(host="localhost", user="root",
#                                   password="password", database="events")  # nosec
conn = mysql.connector.connect(host="kafka-acit3855.eastus2.cloudapp.azure.com",
                              user="user", password="password", database="events")  # nosec


cursor = conn.cursor()
cursor.execute('''
              DROP TABLE speed, vertical
              ''')

conn.commit()
conn.close()