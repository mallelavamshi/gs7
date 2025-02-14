from passlib.hash import bcrypt
new_password="Mallela"
hashed_password=bcrypt.hash(new_password)
print(hashed_password)