import sys

from com.ziclix.python.sql import zxJDBC
sys.path.append("/home/pi/tt/postgresql-42.5.1.jar")
sys.path.append("/home/pi/tt/helloworld.jar")
print(sys.path)

DATABASE    = "layout"
JDBC_URL    = jdbc_url =  "jdbc:postgresql:layout"
JDBC_DRIVER = "org.postgresql.Driver"

dbConn = zxJDBC.connect(JDBC_URL, 'pi', '12345678', JDBC_DRIVER)
