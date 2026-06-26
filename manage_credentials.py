import requests

local = False
ip = "http://localhost:8000"
if not local:
    ip = "https://bgpscanvisualizer.onrender.com"

print("Credential manager")
admin_key = input("Admin Key: ")
while (option := input("Options: gen, del, quit. Choose: ")) != "quit":
    if option != "gen" and option != "del":
        continue

    username = input("Username ('cancel' to cancel): ")
    if username == "cancel":
        continue

    if option == "gen":
        response = requests.post(
            f"{ip}/auth/generate-credentials",
            headers={
                "Authorization": f"Bearer {admin_key}"
            },
            json={
                "username": username
            }
        )

        response.raise_for_status()

        password = response.json()["password"]

        print(f"Generated credentials: \nUsername: {username}\nPassword: {password}")

    elif option == "del":
        response = requests.post(
            f"{ip}/auth/delete-credentials",
            headers={
                "Authorization": f"Bearer {admin_key}"
            },
            json={
                "username": username
            }
        )

        response.raise_for_status()

        print(f"Deleted: {username}")
