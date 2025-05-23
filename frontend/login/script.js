CACHE_USER_ID_KEY = 'user_id';
CACHE_USER_NAME_KEY = 'user_name';

document.addEventListener('DOMContentLoaded', function() {
    const showLoginPassword = document.getElementById('showLoginPassword');
    const showRegisterPassword = document.getElementById('showRegisterPassword');
    const loginForm = document.getElementById('loginForm');
    const registerForm = document.getElementById('registerForm');
    const loginError = document.getElementById('loginError');
    const registerError = document.getElementById('registerError');
    const user_id = localStorage.getItem('user_id');
    const user_name = localStorage.getItem('user_name');

     // Check if user is logged in when the user clicked 'previous/forward page'
     window.addEventListener('popstate', function() {
        user_id = localStorage.getItem('user_id');
        user_name = localStorage.getItem('user_name');
        if (user_id && user_name) {
            verifyUser(user_id, user_name);
        }
     });

    // Check if user is logged in when the DOM finished  to load
    if (user_id && user_name) {
        verifyUser(user_id, user_name);
    }

    showLoginPassword.addEventListener('click', function() {
        const passwordField = document.getElementById('loginPassword');
        if (passwordField.type === 'password') {
            passwordField.type = 'text';
            this.innerHTML = '<i class="fas fa-eye-slash"></i>';
        } else {
            passwordField.type = 'password';
            this.innerHTML = '<i class="fas fa-eye"></i>';
        }
    });

    showRegisterPassword.addEventListener('click', function() {
        const passwordField = document.getElementById('registerPassword');
        if (passwordField.type === 'password') {
            passwordField.type = 'text';
            this.innerHTML = '<i class="fas fa-eye-slash"></i>';
        } else {
            passwordField.type = 'password';
            this.innerHTML = '<i class="fas fa-eye"></i>';
        }
    });

    loginForm.addEventListener('submit', async function(event) {
        event.preventDefault();
        const username = document.getElementById('loginUsername').value;
        const password = document.getElementById('loginPassword').value;

        try {
            const response = await fetch('/login', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ username, password })
            });

            if (!response.ok) {
                const errorData = await response.json();
                loginError.textContent = `${errorData.detail}`;
                return;
            }

            const data = await response.json();
            console.log('user logged in:', data);
            localStorage.setItem('user_id', data.user_id);
            localStorage.setItem('user_name', data.user_name);
            window.location.href = '/static/recommendation/index.html';

        } catch (error) {
            loginError.textContent = "An unexpected error occurred.";
        }
    });

    registerForm.addEventListener('submit', async function(event) {
        event.preventDefault();
        const username = document.getElementById('registerUsername').value;
        const password = document.getElementById('registerPassword').value;

        try {
            const response = await fetch('/register', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ username, password })
            });

            if (!response.ok) {
                const errorData = await response.json();
                registerError.textContent = `${errorData.detail}`;
                return;
            }

            const data = await response.json();
            console.log('user logged in:', data);
            localStorage.setItem('user_id', data.user_id);
            localStorage.setItem('user_name', data.user_name);
            window.location.href = '/static/recommendation/index.html';
        } catch (error) {
            registerError.textContent = "An unexpected error occurred.";
        }
    });
});

function handleUnauthorizedUser() {
    alert('Invalid User!!');
    localStorage.removeItem(CACHE_USER_ID_KEY);
    localStorage.removeItem(CACHE_USER_NAME_KEY);
    window.location.href = '/';
}

function verifyUser(user_id, user_name) {
    fetch(`/verify_user?user_id=${user_id}&user_name=${user_name}`, {
        method: 'GET',
        headers: {
            'Content-Type': 'application/json'
        }
    })
    .then(response => {
        if (response.status === 404) {
           handleUnauthorizedUser()
           return { unauthorized: true };
        }
        return response.json();
    })
    .then(data => {
        window.location.href = '/static/recommendation/index.html';
    })
    .catch(error => {
        console.error("An error occurred while verifying the user:", error);
        localStorage.removeItem('user_id');
        localStorage.removeItem('user_name');
    });
}