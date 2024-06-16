import os
import privy
from getpass import getpass
# Default SSH user
ssh_user = "marek"

# Default SSH port
ssh_port = 22

# Encrypted SSH public key
ssh_public_key_secret = '1$2$WPsZMzX24WxSP4SWXguwZ0E-cGxjNtAPk1JinEWB-rI=$Z0FBQUFBQm1idTk5Z3p3SW0tN0NzVi1PajdmdXJVWkRjMWF1SlVJQVM4eGtqZ0JEQnNyYTZZRVo0eEFhTHNXTlNCaUNwelowa0tWVkhOQXlwSFMtSFZ1QVEtR1VvaU5RUGVCaXpiQW9NbEM1cUFJaHBSTGNYMHlhSUZjYk5QV3YzSmU5cGQtQXI5elFIV3liRUt1OXFNRDlJWkxVbnJGSEQ1c1paMW1PSVR0RVFDbHh3Y2E1U3pyUEVWM3hoTkhTNUZsd2VYMW5KVnJwZTY5eEtucXJrejdVRGJDNjlhV2hhaExLOUo4RmpibF83dkRJSWdldldxeDVzN2t0TmdMU18ybVlCNncyaUtwdUt2Wm1kdTFDdElrcTh3RklvZFpSbm9yRUlKaEFXQVNJVTZTWXBGc1l3ejcwOTgyVThTbWZFd2ZvbGpPMDVNLXdJeGktTC16TlVmVFlaTF9mT0lLYTRLX25XcF8xUTlmM2Z4bWZKbklaekNEa0gwUjU2VU1PbnVRcEhlS2tqR3dzNDE1SzZqcEc2MHBwS0JvVTFVNTdMcUlGZWctUkNmbi12cktCaTQxV0lkZ3AzWUI4a3BscUFnV2JuNFhSUm11QkVGWW56MmxNcC1XY3NjWUNDMmhaQmlqN1MzUTlFV3Q0MDhnMkpDelJJZ1E3RnVuNnYxUGJORzA5S1JwX1F0aDFBNGpNLTFONWhtQTNoX1MxUE1GdEZuRGpQWklkME5YekQ3SnNtQ3laR182S19pOHZ3aEVDVWxaUzFDbGFPbHJMVFFNWFRNQjVEWU5yVnY2TTVMN3MyZS03aXhJamRpOGx2amN1dm1VMHFOWlNGU3NPZzZTOVhkVmJfSzFLd2Rzb0lwQ3l5bVl3UWYzNWcxczg2TWVTOFN2YUtDVEJfR0ROZ0lXREEyM1ZiM0pvWGhETHZNaGhlbU5HdWVhcVU5b1Nrb2xMRUN0alpXQmNseXJIREZMQVk2YUlYelB0d2F4c2pVa1ZrTGp6bUhmQnZyYkRkMERjV1JHV2hSak5WaFM1aVFDemtQNmFtVEh0Ymg1N2JzMm9IbzVxb3BsWGd6NTdsbk5iclB0VHVOcWtXM25sN1Yxak5uTHZ0QkhjMlVLV2daRzRRRFU1VzRpd3BHclRscWt4dEE9PQ=='

master_password = getpass('Please provide the master secret password: ')

def get_secret(encrypted_secret, password):
    encoding = 'utf-8'
    return privy.peek(encrypted_secret, password).decode(encoding)

# SSH key
ssh_public_key = get_secret(ssh_public_key_secret, master_password)

# SSH password
ssh_password = master_password
message = "Kubernetes at home."