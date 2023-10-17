import json
import argparse
from kubernetes import client, config

def filter_pod_security_labels(labels):
    return {k: v for k, v in labels.items() if k.startswith("pod-security.kubernetes.io/")}

def list_labels():
    config.load_kube_config()
    v1 = client.CoreV1Api()
    all_namespaces = v1.list_namespace().items
    labels_dict = {}

    for namespace in all_namespaces:
        name = namespace.metadata.name
        labels = namespace.metadata.labels
        filtered_labels = filter_pod_security_labels(labels) if labels else {}
        labels_dict[name] = filtered_labels

    with open("pod_security_labels.json", "w") as f:
        json.dump(labels_dict, f, indent=4)

def check_cluster():
    config.load_kube_config()
    v1 = client.CoreV1Api()
    all_namespaces = v1.list_namespace().items

    with open("pod_security_labels.json", "r") as f:
        labels_dict = json.load(f)

    for namespace in all_namespaces:
        name = namespace.metadata.name
        labels = namespace.metadata.labels
        filtered_labels = filter_pod_security_labels(labels) if labels else {}
        if name in labels_dict:
            if filtered_labels != labels_dict[name]:
                print(f"Namespace {name} pod-security labels are different.")
        else:
            print(f"Namespace {name} not found in label file.")

def apply_labels():
    config.load_kube_config()
    v1 = client.CoreV1Api()

    with open("pod_security_labels.json", "r") as f:
        labels_dict = json.load(f)

    for name in labels_dict.keys():
        namespace = v1.read_namespace(name=name)
        existing_labels = namespace.metadata.labels if namespace.metadata.labels else {}

        # Add or update labels
        for key, value in labels_dict[name].items():
            existing_labels[key] = value

        # Remove pod-security labels that are not in the file
        for key in list(existing_labels.keys()):
            if key.startswith("pod-security.kubernetes.io/"):
                if key not in labels_dict[name] or existing_labels[key] != labels_dict[name].get(key, None):
                    del existing_labels[key]

        body = {"metadata": {"labels": existing_labels}}
        v1.patch_namespace(name, body)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Manage Kubernetes pod-security labels.")
    parser.add_argument("command", choices=["list", "check", "apply"], help="Command to execute.")

    args = parser.parse_args()
    if args.command == "list":
        list_labels()
    elif args.command == "check":
        check_cluster()
    elif args.command == "apply":
        apply_labels()
