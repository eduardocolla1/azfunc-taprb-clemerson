import logging
import azure.functions as func
import os
import pyodbc

app = func.FunctionApp()

@app.timer_trigger(
    schedule="0 * * * * *",
    arg_name="myTimer",
    run_on_startup=False,
    use_monitor=False
)
def extract_todas_tabelas(myTimer: func.TimerRequest) -> None:

    host = os.getenv("HOST")
    database = os.getenv("DATABASE")
    user = os.getenv("USER")
    password = os.getenv("PASSWORD")

    conn_str = (
        "DRIVER={ODBC Driver 18 for SQL Server};"
        f"SERVER={host};"
        f"DATABASE={database};"
        f"UID={user};"
        f"PWD={password};"
        "Encrypt=yes;"
        "TrustServerCertificate=no;"
        "Connection Timeout=30;"
    )

    conn = None

    try:
        logging.info("Conectando ao banco de dados...")

        conn = pyodbc.connect(conn_str)

        logging.info("Conexão realizada com sucesso.")

        cursor = conn.cursor()

        query_tabelas = """
            SELECT TABLE_SCHEMA, TABLE_NAME
            FROM INFORMATION_SCHEMA.TABLES
            WHERE TABLE_TYPE = 'BASE TABLE'
            ORDER BY TABLE_SCHEMA, TABLE_NAME
        """

        cursor.execute(query_tabelas)

        tabelas = cursor.fetchall()

        logging.info("Quantidade de tabelas encontradas: %d", len(tabelas))

        for schema, tabela in tabelas:

            logging.info(
                "========================================"
            )
            logging.info(
                "Lendo tabela: %s.%s",
                schema,
                tabela
            )

            query = f"""
                SELECT *
                FROM [{schema}].[{tabela}]
            """

            try:
                cursor.execute(query)

                columns = [column[0] for column in cursor.description]

                rows = cursor.fetchall()

                logging.info(
                    "Tabela %s.%s possui %d registros.",
                    schema,
                    tabela,
                    len(rows)
                )

                logging.info("Colunas: %s", columns)

                for row in rows:
                    logging.info(
                        "%s",
                        dict(zip(columns, row))
                    )

            except pyodbc.Error as e:
                logging.error(
                    "Erro ao acessar %s.%s: %s",
                    schema,
                    tabela,
                    e
                )

        cursor.close()

    except pyodbc.Error as e:
        logging.error(
            "Erro ao acessar o banco de dados: %s",
            e
        )

    except Exception as e:
        logging.exception(
            "Erro inesperado: %s",
            e
        )

    finally:
        if conn is not None:
            conn.close()
            logging.info(
                "Conexão com o banco de dados encerrada."
            )
