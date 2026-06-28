const local = false

let ip = "";
if (!local)
    ip = "https://bgpscanvisualizer.onrender.com";
let index_page = "/"
if (!local)
    index_page = "/BGPScanVisualizer/"

const loadingOverlay =
    document.getElementById("loading-overlay");

const loadingMessage =
    document.getElementById("loading-message");

const loginButton =
    document.getElementById("login-button")

let loadingInterval = null;

function showLoading(message) {

    let dots = 0;

    loadingInterval = setInterval(() => {

        dots = (dots + 1) % 4;

        document.getElementById(
            "loading-title"
        ).textContent =
            "Loading" + ".".repeat(dots);

    }, 500);

    loadingMessage.textContent = message;

    if (loadingOverlay.classList.contains("hidden")) {
        loginButton.enabled = false;
        loadingOverlay.classList.remove("hidden");
    }
}

function hideLoading() {
    clearInterval(loadingInterval);
    loadingOverlay.classList.add("hidden");
    loginButton.enabled = true;
}

loginButton.addEventListener("click", async () => {
    const username =
        document.getElementById("username").value;

    const password =
        document.getElementById("password").value;

    showLoading("Fetching graph from backend (Due to inactivity spin-down this may take up to one minute)");

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
        hideLoading()
        document.getElementById("login-error").textContent =
            "Invalid username or password";
    }

});