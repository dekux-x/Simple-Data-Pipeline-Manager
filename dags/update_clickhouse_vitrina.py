from airflow import DAG
from airflow.providers.http.operators.http import SimpleHttpOperator
from airflow.operators.python import PythonOperator
from datetime import datetime

TRUNCATE_QUERY = "TRUNCATE TABLE magnum_db.orders_with_discounts;"
INSERT_QUERY = """
INSERT INTO magnum_db.orders_with_discounts
SELECT
    o.order_id,
    c.name AS client_name,
    c.region,
    p.name AS product_name,
    p.category,
    o.order_date,
    o.total_amount,
    d.discount_percent,
    o.total_amount * (1 - d.discount_percent / 100) AS final_amount
FROM
    magnum_db.orders o
INNER JOIN
    magnum_db.clients c ON o.client_id = c.client_id
INNER JOIN
    magnum_db.products p ON o.product_id = p.product_id
LEFT JOIN
    magnum_db.discounts d ON o.product_id = d.product_id
   AND o.order_date BETWEEN d.start_date AND d.end_date;
"""

default_args = {
    "owner": "airflow",
    "depends_on_past": False,
    "email_on_failure": False,
    "email_on_retry": False,
    "retries": 1,
}

def log_message(message):
    print(message)

with DAG(
    dag_id="update_clickhouse_vitrina",
    default_args=default_args,
    description="DAG для обновления витрины в ClickHouse",
    schedule_interval=None,
    start_date=datetime(2024, 1, 1),
    catchup=False,
) as dag:

    # Логирование начала
    start_log = PythonOperator(
        task_id="start_log",
        python_callable=log_message,
        op_args=["Начало выполнения DAG"],
    )

    # Очистка витрины
    truncate_vitrina = SimpleHttpOperator(
        task_id="truncate_vitrina",
        http_conn_id="clickhouse_conn",
        endpoint="/",
        method="POST",
        data=TRUNCATE_QUERY,
        headers={"Content-Type": "application/json"},
    )

    # Обновление витрины
    update_vitrina = SimpleHttpOperator(
        task_id="update_vitrina",
        http_conn_id="clickhouse_conn",
        endpoint="/",
        method="POST",
        data=INSERT_QUERY,
        headers={"Content-Type": "application/json"},
    )

    # Логирование завершения
    end_log = PythonOperator(
        task_id="end_log",
        python_callable=log_message,
        op_args=["DAG выполнен успешно"],
    )

    # Последовательность выполнения задач
    start_log >> truncate_vitrina >> update_vitrina >> end_log
