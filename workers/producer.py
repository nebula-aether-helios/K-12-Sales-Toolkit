import csv
import json
import argparse
import pika
from typing import Dict

def autodetect_personnel_columns(header):
    # simple heuristics: names and phone columns
    name_cols = [h for h in header if any(x in h.lower() for x in ("name","first","last","person"))]
    phone_cols = [h for h in header if any(x in h.lower() for x in ("phone","mobile","cell","work"))]
    owner_cols = [h for h in header if any(x in h.lower() for x in ("owner", "registered", "principal", "owner_name"))]
    return name_cols, phone_cols, owner_cols


def publish_tasks(csv_path: str, rabbitmq_url: str, queue_name: str = "enrich_tasks"):
    conn = pika.BlockingConnection(pika.URLParameters(rabbitmq_url))
    ch = conn.channel()
    ch.queue_declare(queue=queue_name, durable=True)
    with open(csv_path, newline='', encoding='utf-8') as fh:
        reader = csv.DictReader(fh)
        header = reader.fieldnames
        name_cols, phone_cols, owner_cols = autodetect_personnel_columns(header)
        for idx, row in enumerate(reader, start=1):
            task = {"row_index": idx, "row": row, "name_cols": name_cols, "phone_cols": phone_cols, "owner_cols": owner_cols}
            ch.basic_publish(
                exchange='',
                routing_key=queue_name,
                body=json.dumps(task),
                properties=pika.BasicProperties(delivery_mode=2),
            )
    conn.close()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--input', required=True)
    parser.add_argument('--rabbitmq-url', required=True)
    parser.add_argument('--queue', default='enrich_tasks')
    args = parser.parse_args()
    publish_tasks(args.input, args.rabbitmq_url, args.queue)


if __name__ == '__main__':
    main()
