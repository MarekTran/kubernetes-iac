import privy
from getpass import getpass

encoding = 'utf-8'
data = '12345678'.encode(encoding)
password = getpass('Please provide the secret password)')
hidden = privy.hide(data, 'password')
# print(hidden)
# print(privy.peek(hidden, 'password').decode(encoding))

# print(str(privy.peek(hidden, 'password'), encoding))

ssh_pub_key='ssh-rsa AAAAB3NzaC1yc2EAAAADAQABAAABgQC63QclHGqI4M+H/kl+75FZpNsU9p5P10mEZgkbdKgaY8LIVC03jQ9wDftZf3vm2FG92DOnHzW2q5m0QWU1719H9nspmqx6jaYIwJPMa/hX2nDUaYMoPkM04D5ZXxClARW4TF748ezqhoEYGZoaDKw4xNS6uUJpiWl1APWox+W7uZsoWTs2hVIS8g5aiWm3ySHpzNX7EeOhw1QTHy0PCpk30J/gXbC+6uho1z2MKtaOpu461jnw226HM4pTkJQKckxtsyctGrkiF29mn5VT2uq/OYXCzgOVy7wHr3Fjux8c598mLAKGYdWA4BoDj3nEoKUPZ/gpF/t54uWI1LQlR77pH96xhdgtO5Dhe0s+NUcdJ8+X3powk+UQC66v6bN9jQ2X17RGJYRspBZGJQbPtnuacrpzzneYbeBzRvTNwOK9D3goPsKiltxrSJTO6uOFcYpgDKy2Jgb4t+yVDndk51I61HnWVKHnNG8zs4vWAPQ7AqChQqgfG8tvtQOszXlQvC0= marek tran@DESKTOP-GOF2M9U'
encrypted_ssh_pub_key = privy.hide(ssh_pub_key.encode(encoding), password)
print(encrypted_ssh_pub_key)
print(password)