from pyinfra import host, inventory
from pyinfra.operations import server
server.shell(
    name="Echo message",
    commands=[f"echo {host.data.message}"],
)