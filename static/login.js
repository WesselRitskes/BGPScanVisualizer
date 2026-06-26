const local = false

let ip = "";
if (!local)
    ip = "https://bgpscanvisualizer.onrender.com";
let index_page = "/index.html"
if (!local)
    index_page = "BGPScanVisualizer/index.html"

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
            window.location = index_page;
        } else {
            document.getElementById("login-error").textContent =
                "Invalid username or password";
        }

    });