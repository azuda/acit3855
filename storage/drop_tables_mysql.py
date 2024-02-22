import mysql.connector


# conn = mysql.connector.connect(host="localhost", user="root",
#                                   password="password", database="events")
conn = mysql.connector.connect(host="kafka-acit3855.eastus2.cloudapp.azure.com",
                              user="user", password="password", database="events")


cursor = conn.cursor()
cursor.execute('''
              DROP TABLE speed, vertical
              ''')

conn.commit()
conn.close()