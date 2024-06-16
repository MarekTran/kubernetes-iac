from os import path
from dotenv import load_dotenv
from pyinfra import host, inventory, local, state
from pyinfra.operations import apt, files, server, python
from io import StringIO
import logging

# Configure the logger
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("deploy.log"),
        logging.StreamHandler()
    ]
)

# Create a logger instance
logger = logging.getLogger(__name__)




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


def install_dependencies():
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


# Install kubernetes
def install_kubernetes():
  # Add the Kubernetes apt repository key
  keyring_exists = host.fact.file("/etc/apt/keyrings/kubernetes-apt-keyring.gpg")
  if not keyring_exists:
    # Add the Kubernetes repository key if it doesn't exist
    server.shell(
        name="Add the Kubernetes repository key",
        commands=[
            "curl -fsSL https://pkgs.k8s.io/core:/stable:/v1.30/deb/Release.key | sudo gpg --dearmor -o /etc/apt/keyrings/kubernetes-apt-keyring.gpg"
        ],
    )

  # Contents of the kubernetes.list file
  kubernetes_list_content = """
  deb [signed-by=/etc/apt/keyrings/kubernetes-apt-keyring.gpg] https://pkgs.k8s.io/core:/stable:/v1.30/deb/ /
  """
  # Ensure the content of kubernetes.list is correct
  files.file(
      name="Ensure the content of kubernetes.list is correct",
      path="/etc/apt/sources.list.d/kubernetes.list",
      content=kubernetes_list_content,
  )
  apt.packages(
      name='Install kubelet, kubeadm, and kubectl',
      packages=[
          'kubelet',
          'kubeadm',
          'kubectl'
      ],
      update=True,  # Ensure the package list is updated
      # upgrade=True  # Optionally upgrade the packages if they are already installed
  )

  # Apply all sysctl settings
  server.shell(
      name="Apply all sysctl settings",
      commands=["sudo sysctl --system"],
  )


@deploy("Complete deployment")
def completely():
    # Deployment for all hosts
    authorize_ssh_key()
    setup_passwordless_sudo()
    apt_update_upgrade()
    setup_addresses()
    # Kubernetes specific configuration
    add_containerd_config()
    add_kubernetes_cri_sysctl_config()
    install_dependencies()
    install_kubernetes()

    if host.name in inventory.get_group('control-planes'):
        # Do something for control-planes
        new_calico_cidr="10.200.0.0/16"
        # Initialize pod network (Calico default is 192.168.0.0/16) (To avoid conflicts I choose differently)
        server.shell(
            name="Initialize the control plane",
            commands=[
                f"sudo kubeadm init --pod-network-cidr={new_calico_cidr} --kubernetes-version=1.30.1"
            ],
        )

        # Make kubernetes config file in home dir
        files.directory(
            name='Create .kube directory',
            path='/home/marek/.kube',
            present=True
        )

        home_dir = "$HOME"
        kube_dir = f"{home_dir}/.kube"  
        config_dest = f"{kube_dir}/config"
        # By default, kubectl looks for a file named config in the $HOME/.kube
        files.directory(
          name="Ensure the .kube directory exists",
          path=kube_dir,
          present=True,
        )
        # Copy the config to $HOME/.kube/config
        server.shell(
            name="Copy the kube config to the user's home directory",
            commands=[
                f"sudo cp /etc/kubernetes/admin.conf {config_dest}",
                f"sudo chown $(id -u):$(id -g) {config_dest}",
            ],
        )
        # Download Calico manifest
        files.download(
            name="Download Calico manifest",
            src="https://raw.githubusercontent.com/projectcalico/calico/v3.28.0/manifests/calico.yaml",
            dest=f"{home_dir}/calico.yaml",
        )
        # Edit Calico manifest to include the new CIDR
        calico_yaml_block_parts = (
            "            - name: CALICO_IPV4POOL_CIDR\n",
            f'              value: "{new_calico_cidr}"\n'
        )

        calico_yaml_block= ''.join(calico_yaml_block_parts)
        files.block(
            before=True,
            line=".*# - name: CALICO_IPV4POOL_CIDR",
            path=f"{home_dir}/calico.yaml",
            content=[calico_yaml_block],
            present=True,
        )

        # Apply
        server.shell(
            name="Apply Calico network",
            commands=[
                f"kubectl apply -f {home_dir}/calico.yaml"
            ],
        )

        # Get the join command
        # join_command = server.shell(
        #     name="Get the join command",
        #     commands=[
        #         "kubeadm token create --print-join-command"
        #     ],
        # )
        
        # Define a function to handle the command output and store it in a runtime variable
        def save_join_command(state, host):
            # Run the kubeadm command
            status, stdout, stderr = host.run_shell_command(
                command='kubeadm token create --print-join-command',
                sudo=True  # Assuming you need sudo to run this command
            )

            # Check if the command executed successfully
            if status:
                # Save the output to the runtime variable
                state.inventory.vars['join_token'] = '\n'.join(stdout)
            else:
                raise Exception(f"Command failed with stderr: {stderr}")

        # Use python.call to execute the save_join_command function
        python.call(
            name="Save kubeadm join command",
            function=save_join_command
        )

        join_token = state.inventory.vars.get('join_token')
        logger.info(join_token)
        

    # if host.name in inventory.get_group('workers'):
    #     # Do something for workers