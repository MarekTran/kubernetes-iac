from os import path
from dotenv import load_dotenv
from pyinfra import host, inventory, local,
from pyinfra.operations import apt, files, git, pip, server, systemd
from io import StringIO

# local.include(filename=path.join("tasks", "echo_test.py"))


@deploy("Apt update, Apt upgrade")
def apt_update_upgrade():
    apt.update(cache_time=3600)
    apt.upgrade(auto_remove=True)


@deploy("Authorize SSH key")
def authorize_ssh_key():
    server.user(
        user=host.data.ssh_user,
        present=True,
        ensure_home=True,
        unique=True,
        shell="/bin/bash",
        sudo=True,
        password=host.data.ssh_password,
        public_keys=[host.data.ssh_public_key]
    )


@deploy("Setup passwordless sudo")
def setup_passwordless_sudo():
    result = files.line(
        name="Allow passwordless sudo",
        path="/etc/sudoers",
        line=f"{host.data.ssh_user} ALL=(ALL) NOPASSWD:ALL",
        present=True,
    )
    if result.changed:
        validation_result = server.shell(
            name="Validate sudoers file",
            commands=["visudo -cf /etc/sudoers"],
        )
        if validation_result.failed:
            files.line(
                name="Allow passwordless sudo",
                path="/etc/sudoers",
                line=f"{host.data.ssh_user} ALL=(ALL) NOPASSWD:ALL",
                present=False,
            )


@deploy("Setup addresses")
def setup_addresses():
    # Add the control plane IP address to the /etc/hosts file
    # This will add the entry before the localhost entry (top of the file) between # BEGIN and # END markers

    # Let's build the content to add line by line
    content = []
    for node in [i for i in inventory if i.name != "@local"]:
        line_to_append = f"{node.data.get('ipv4')} {node.name}\n"
        content.append(line_to_append)

    files.block(
        name="Add each other to /etc/hosts",
        path="/etc/hosts",
        before=True,
        line=f".*localhost",
        content=content,
    )


# @deploy("Add containerd config")
def add_containerd_config():
    # Define the content of the file
    containerd_conf_content = StringIO("overlay\nbr_netfilter\n")

    # Create the containerd.conf file with the desired content
    files.put(
        name="Create /etc/modules-load.d/containerd.conf",
        src=containerd_conf_content,
        dest="/etc/modules-load.d/containerd.conf",
        mode="644",
    )


# @deploy("Add Kubernetes CRI sysctl config")
def add_kubernetes_cri_sysctl_config():
    # Define the content of the file
    kubernetes_cri_conf_content = StringIO(
        "net.bridge.bridge-nf-call-iptables=1\n"
        "net.ipv4.ip_forward=1\n"
        "net.bridge.bridge-nf-call-ip6tables=1\n"
    )

    # Create the 99-kubernetes-cri.conf file with the desired content
    files.put(
        name="Create /etc/sysctl.d/99-kubernetes-cri.conf",
        src=kubernetes_cri_conf_content,
        dest="/etc/sysctl.d/99-kubernetes-cri.conf",
        mode="644",
        sudo=True,
    )


def install_k8s_dependencies():
  # Install packages
  apt.packages(
      name='Install curl, ca-certificates, gnupg, and containerd',
      packages=[
          'curl',
          'ca-certificates',
          'gnupg',
          'containerd'
      ],
      # update=True,  # Ensure the package list is updated
      # upgrade=True  # Optionally upgrade the packages if they are already installed
  )

  # Create directory for containerd configuration
  files.directory(
      name='Create /etc/containerd directory',
      path='/etc/containerd',
      present=True
  )
  

  # To generate the containerd_config.toml file
  server.shell(
      name='Generate containerd config file locally',
      commands=[
          'containerd config default > containerd_config.toml'
      ]
  )


  # Restart and enable containerd service
  server.service(
      name='Restart containerd service',
      service='containerd',
      running=True,
      restarted=True,
      enabled=True
  )


  # Disable swap
  server.shell(
      name='Disable swap',
      commands=[
          'swapoff -a'
      ]
  )



@deploy("Complete deployment")
def completely():
    # Deployment for all hosts
    authorize_ssh_key()
    setup_passwordless_sudo()
    apt_update_upgrade()
    setup_addresses()
    if host.name in inventory.get_group('control-planes'):
        # Do something for control-planes

    if host.name in inventory.get_group('workers'):
        # Do something for workers
