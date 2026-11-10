# PyMySQL lets Django talk to MySQL without compiling mysqlclient (easier on Windows).
try:
    import pymysql
    pymysql.install_as_MySQLdb()
except ImportError:
    pass
