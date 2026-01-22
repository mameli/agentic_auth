from typing import Any
from trino.dbapi import connect
from trino.auth import OAuth2Authentication
from trino.exceptions import TrinoUserError
import urllib3
from rich.table import Table
from rich.console import Console

def print_rows(rows: list[list[Any]]) -> None:
    
    columns = [d[0] for d in cur.description] if cur.description else []
    table = Table(show_header=True, header_style="bold magenta")
    for col in columns:
        table.add_column(col)
    for row in rows:
        table.add_row(*[str(x) if x is not None else "" for x in row])
    console = Console()
    console.print(table)

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
    cur.execute("SELECT * FROM test.nation_view")
    print_rows(rows = cur.fetchall())
    try:
        cur.execute("SELECT * FROM private.nation_view")
        print("Experiment failed, andrea should not be able to private schema")
        print_rows(cur.fetchall())
        exit(1)
    except TrinoUserError:
        print("Experiment successful, andrea should not be able to [private] schema")
    