const local = false

let ip = "";
if (!local)
    ip = "https://bgpscanvisualizer.onrender.com";

document
    .getElementById("login-button")
    .addEventListener("click", async () => {

        const username =
            document.getElementById("username").value;

        const password =
            document.getElementById("password").value;

        const response = await fetch(`${ip}/auth/login`, {
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            },
            credentials: "include",
            body: JSON.stringify({
                username,
                password
            })
        });

        if (response.ok) {
            window.location = "/index.html";
        } else {
            document.getElementById("login-error").textContent =
                "Invalid username or password";
        }

    });