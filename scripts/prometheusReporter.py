import argparse
import os
from prometheus_client import CollectorRegistry, Counter, Gauge, multiprocess

def parse_labels(label_list):
    labels = {}
    for label in label_list:
        k, v = label.split("=")
        labels[k] = v
    return labels

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--name', required=True, help="Metric name")
    parser.add_argument('--type', choices=['counter', 'gauge'], required=True)
    parser.add_argument('--action', choices=['inc', 'set'], required=True)
    parser.add_argument('--value', type=float, help="Value for set (gauge only)")
    parser.add_argument('--labels', nargs='*', default=[], help="Labels like key=value")
    args = parser.parse_args()

    # Ensure PROMETHEUS_MULTIPROC_DIR is set
    os.environ.setdefault("PROMETHEUS_MULTIPROC_DIR", "/logs/prometheus")

    # Registry for multiprocess metrics
    registry = CollectorRegistry()
    multiprocess.MultiProcessCollector(registry)

    labels = parse_labels(args.labels)

    if args.type == "counter":
        metric = Counter(args.name, f"{args.name} counter", list(labels.keys()), registry=registry)
    else:
        metric = Gauge(args.name, f"{args.name} gauge", list(labels.keys()), registry=registry)

    if args.action == "inc":
        metric.labels(**labels).inc()
    elif args.action == "set":
        if args.value is None:
            raise ValueError("You must pass --value when using --action set")
        metric.labels(**labels).set(args.value)

if __name__ == "__main__":
    main()