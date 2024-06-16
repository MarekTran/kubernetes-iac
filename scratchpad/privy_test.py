import privy
from getpass import getpass

encoding = 'utf-8'
data = '12345678'.encode(encoding)
password = getpass('Please provide the secret password)')
hidden = privy.hide(data, 'password')
# print(hidden)
# print(privy.peek(hidden, 'password').decode(encoding))

# print(str(privy.peek(hidden, 'password'), encoding))
