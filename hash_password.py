from werkzeug.security import generate_password_hash
import getpass

# Use getpass to securely ask for the password without showing it on screen
password = getpass.getpass("Enter the new password you want to use: ")

# Generate the secure hash
hashed_password = generate_password_hash(password)

print("\nPassword hashing complete.")
print("Copy the entire line below and paste it into your users.json file:\n")
print(hashed_password)