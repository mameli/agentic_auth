from trino.dbapi import connect
from trino.auth import OAuth2Authentication
import urllib3

if __name__ == "__main__":
    urllib3.disable_warnings()
    conn = connect(
        host="trinodb",
        port=8543,
        auth=OAuth2Authentication(),
        http_scheme="https",
        verify=False,
        catalog="hive",
    )
    cur = conn.cursor()
    cur.execute("SHOW SCHEMAS FROM hive")
    
    view_name = "test.nation_view"
    cur.execute("CREATE SCHEMA IF NOT EXISTS test")
    # # create a view inside schema `test` that selects from tpch.tiny.nation
    cur.execute(f"CREATE OR REPLACE VIEW {view_name} AS SELECT * FROM tpch.tiny.nation")
    print(f"view created successfully [{view_name}]")
    
    view_name = "private.nation_view"
    cur.execute("CREATE SCHEMA IF NOT EXISTS private")
    # # create a view inside schema `test` that selects from tpch.tiny.nation
    cur.execute(f"CREATE OR REPLACE VIEW {view_name} AS SELECT * FROM tpch.tiny.nation")
    print(f"view created successfully [{view_name}]")
    # Revoke access from all users
    # Grant access only to the current user
    # run a quick verification query and print results