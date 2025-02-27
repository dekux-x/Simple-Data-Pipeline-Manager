# Simple Data Pipeline Manager

## Описание
Проект представляет собой систему автоматизации обработки данных с использованием ClickHouse и Apache Airflow. 
Система позволяет организовать загрузку, трансформацию и анализ данных, а также автоматическое обновление витрин данных.

---

## Структура проекта
- **ClickHouse**: Используется как основное хранилище данных.
- **Apache Airflow**: Оркестрация процессов обработки данных.
- **Витрина данных**: Интеграция и объединение данных из таблиц для аналитических целей.

---

## Установка и настройка

### 1. Установка и настройка ClickHouse
1. Использовал Docker-образ clickhouse/clickhouse-server

2. Для проверки подключения:
    curl http://localhost:8123

### 2. Установка и настройка Airflow
1. Скачал файл docker-compose.yaml:
    curl -LfO 'https://airflow.apache.org/docs/apache-airflow/2.7.2/docker-compose.yaml'

2. Файл .env для конфигурации:
    echo -e "AIRFLOW_UID=$(id -u)\nAIRFLOW_GID=0" > .env    

3. Настройка соединения с ClickHouse:
    - Connection Id: `clickhouse_conn`
    - Connection Type: `HTTP`
    - Host: `magnum-clickhouse-server`
    - Port: `8123`

### 3. Создание и Заполнение таблиц
1. Подключился к ClickHouse через CLI
    docker exec -it magnum-clickhouse-server clickhouse-client
2. SQL-запросы для создания и заполнения таблиц:
    ```sql
    CREATE TABLE clients (
        client_id UInt32,
        name String,
        region String
    ) ENGINE = MergeTree()
    ORDER BY client_id;

    CREATE TABLE products (
        product_id UInt32,
        name String,
        category String
    ) ENGINE = MergeTree()
    ORDER BY product_id;

    CREATE TABLE orders (
        order_id UInt32,
        client_id UInt32,
        product_id UInt32,
        order_date Date,
        total_amount Float64
    ) ENGINE = MergeTree()
    ORDER BY order_id;

    CREATE TABLE discounts (
        product_id UInt32,
        discount_percent Float64,
        start_date Date,
        end_date Date
    ) ENGINE = MergeTree()
    ORDER BY product_id;
    ```

    ```sql
    INSERT INTO clients VALUES
    (1, 'Алимжан', 'Алматы'),
    (2, 'Динара', 'Нур-Султан'),
    (3, 'Бекзат', 'Шымкент'),
    (4, 'Айдана', 'Алматы'),
    (5, 'Руслан', 'Нур-Султан'),
    (6, 'Гульнар', 'Павлодар'),
    (7, 'Айгерим', 'Костанай');

    INSERT INTO products VALUES
    (101, 'Смартфон', 'Электроника'),
    (102, 'Ноутбук', 'Электроника'),
    (103, 'Кофе', 'Продукты'),
    (104, 'Холодильник', 'Бытовая техника'),
    (105, 'Телевизор', 'Электроника'),
    (106, 'Шоколад', 'Продукты'),
    (107, 'Кресло', 'Мебель');

    INSERT INTO orders VALUES
    (201, 1, 101, '2024-12-01', 150000),
    (202, 2, 102, '2024-12-02', 200000),
    (203, 3, 103, '2024-12-03', 5000),
    (204, 4, 104, '2024-12-04', 250000),
    (205, 5, 105, '2024-12-05', 300000),
    (206, 6, 106, '2024-12-06', 10000),
    (207, 7, 107, '2024-12-07', 50000);

    INSERT INTO discounts VALUES
    (101, 10, '2024-12-01', '2024-12-31'),
    (102, 15, '2024-12-01', '2024-12-31'),
    (103, 5, '2024-12-01', '2024-12-31'),
    (104, 20, '2024-12-01', '2024-12-31'),
    (105, 10, '2024-12-01', '2024-12-31'),
    (106, 5, '2024-12-01', '2024-12-31'),
    (107, 10, '2024-12-01', '2024-12-31');

    CREATE TABLE orders_with_discounts (
        order_id UInt64,
        client_name String,
        region String,
        product_name String,
        category String,
        order_date Date,
        total_amount Float64,
        discount_percent Float64,
        final_amount Float64
    ) ENGINE = MergeTree()
    ORDER BY order_id;
    ```

---

### 4. Создание витрины данных
1. Создание витрины:
    ```sql
    CREATE TABLE orders_with_discounts AS
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
    FROM orders o
    LEFT JOIN clients c ON o.client_id = c.client_id
    LEFT JOIN products p ON o.product_id = p.product_id
    LEFT JOIN discounts d ON o.product_id = d.product_id
       AND o.order_date BETWEEN d.start_date AND d.end_date;
    ```


---

### 5. Описание данных
1. Описание структуры таблиц    
#### Таблица `clients`

| Колонка   | Тип данных | Назначение                                |
|-----------|------------|-------------------------------------------|
| client_id | UInt32     | Уникальный идентификатор клиента.         |
| name      | String     | Имя клиента.                              |
| region    | String     | Регион, в котором находится клиент.       |

---

#### Таблица `products`

| Колонка    | Тип данных | Назначение                                      |
|------------|------------|-------------------------------------------------|
| product_id | UInt32     | Уникальный идентификатор продукта.              |
| name       | String     | Название продукта.                              |
| category   | String     | Категория продукта (например, "Электроника").   |

---

#### Таблица `orders`

| Колонка     | Тип данных | Назначение                                   |
|-------------|------------|----------------------------------------------|
| order_id    | UInt32     | Уникальный идентификатор заказа.            |
| client_id   | UInt32     | Указатель на клиента (из таблицы `clients`). |
| product_id  | UInt32     | Указатель на продукт (из таблицы `products`).|
| order_date  | Date       | Дата заказа.                                |
| total_amount| Float32    | Общая сумма заказа.                         |

---

#### Таблица `discounts`

| Колонка          | Тип данных | Назначение                                   |
|-------------------|------------|----------------------------------------------|
| product_id        | UInt32     | Указатель на продукт (из таблицы `products`).|
| discount_percent  | Float32    | Процент скидки на продукт.                   |
| start_date        | Date       | Дата начала действия скидки.                |
| end_date          | Date       | Дата окончания действия скидки.             |


2. Описание витрины

#### Таблица `orders_with_discounts`

| Колонка         | Тип данных | Назначение                                                              |
|------------------|------------|-------------------------------------------------------------------------|
| order_id         | UInt32     | Уникальный идентификатор заказа.                                       |
| client_name      | String     | Имя клиента, связанного с заказом.                                     |
| region           | String     | Регион клиента.                                                        |
| product_name     | String     | Название продукта, связанного с заказом.                               |
| category         | String     | Категория продукта.                                                    |
| order_date       | Date       | Дата заказа.                                                           |
| total_amount     | Float32    | Общая сумма заказа до применения скидки.                               |
| discount_percent | Float32    | Применённый процент скидки.                                            |
| final_amount     | Float32    | Итоговая сумма заказа после применения скидки (`total_amount - discount`). |

#### Назначение колонок витрины в анализе

- **`region`, `category`, `order_date`:**  
  По этим столбцам можно провести группировку и:
  - Определить, какие регионы самые активные.  
  - Узнать, какие категории товаров продаются чаще всего.  
  - Выявить месяцы с наибольшим количеством заказов.  

- **`order_date`:**  
  - Анализировать тенденции продаж с течением времени и динамику продаж.  
  - Строить прогнозы спроса на основе исторических данных.  

- **`region`:**  
  - Оптимизировать маркетинговые кампании на основе региональных особенностей.  
  - Анализировать логистические затраты по регионам.  

- **`product_name`:**  
  - Определять наиболее популярные продукты.  
  - Создавать рекомендации по продуктам на основе предпочтений клиентов.  

- **`category`:**  
  - Сегментировать клиентов по категориям покупок.  

- **`total_amount`:**  
  - Оценивать общую выручку без учёта скидок.  
  - Выявлять клиентов с высокими суммами заказов.  

- **`discount_percent`:**  
  - Анализировать эффективность скидочных кампаний (влияют ли скидки на объём продаж).  
  - Выявлять продукты, которые часто покупаются со скидкой.  

- **`final_amount`:**  
  - Подсчитывать фактическую выручку после применения скидок.  
  - Анализировать доходность заказов.  
  - Оценивать влияние скидок на прибыльность.  

## Завершение
После выполнения всех шагов для удобства я добавил контейнер Clickhouse в docker-compose файл что бы упростить развертывание
