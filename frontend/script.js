const loginForm = document.getElementById("loginForm");
const usernameInput = document.getElementById("username");
const passwordInput = document.getElementById("password");
const loginMessage = document.getElementById("loginMessage");

loginForm.addEventListener("submit", function (event) {
    event.preventDefault();

    const username = usernameInput.value.trim();
    const password = passwordInput.value.trim();

    if (!username || !password) {
        showMessage("Please enter username and password.", false);
        return;
    }

    // Demo credentials for now.
    // We will connect this to Flask later.
    if (username === "admin" && password === "hyper123") {

        showMessage("ACCESS GRANTED — SYSTEM INITIALIZING...", true);

        setTimeout(() => {
            window.location.href = "/dashboard";
        }, 1200);

    } else {

        showMessage("ACCESS DENIED — INVALID CREDENTIALS", false);

        passwordInput.value = "";
        passwordInput.focus();
    }
});

function showMessage(message, success) {
    loginMessage.textContent = message;

    if (success) {
        loginMessage.style.color = "#20e070";
    } else {
        loginMessage.style.color = "#ff5c5c";
    }
}