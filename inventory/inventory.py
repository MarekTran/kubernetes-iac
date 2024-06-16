from pyinfra.api.inventory import Inventory

# Define hosts with their IP addresses
local_k8s = [
    ("k8s-control", {"ipv4": "192.168.179.244"}),
    ("k8s-worker1", {"ipv4": "192.168.179.243"}),
    ("k8s-worker2", {"ipv4": "192.168.179.242"}),
]

# Define groups
groups = {
    'control-planes': ['k8s-control'],
    'workers': ['k8s-worker1', 'k8s-worker2'],
}

# Create the inventory object
inventory = Inventory(
    hosts=[host[0] for host in local_k8s] + ['@local'],
    group_data={
        'control-planes': {},
        'workers': {},
    },
    host_data={host[0]: host[1] for host in local_k8s},
)
