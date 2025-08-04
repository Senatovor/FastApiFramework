document.addEventListener('DOMContentLoaded', function () {
    const form = document.getElementById('registerForm');

    form.addEventListener('submit', async function (e) {
        e.preventDefault();
        resetFormErrors(form);

        if (!form.checkValidity()) {
            form.classList.add('was-validated');
            return;
        }

        const formData = {
            username: document.getElementById('username').value,
            email: document.getElementById('email').value,
            password: document.getElementById('password').value
        };

        try {
            const response = await fetch('/auth/register', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(formData)
            });

            if (!response.ok) {
                const errorData = await response.json();
                if (errorData.detail) {
                    showToast(errorData.detail, 'danger');
                    linkErrorToField(errorData.detail); // Связываем ошибку с полем
                }
                return;
            }

            showToast('Регистрация успешна!', 'success');
            setTimeout(() => window.location.href = '/login', 1500);

        } catch (error) {
            console.error('Ошибка:', error);
            showToast('Ошибка соединения с сервером', 'danger');
        }
    });

    function resetFormErrors(form) {
        form.classList.remove('was-validated');
        document.querySelectorAll('.is-invalid').forEach(el => el.classList.remove('is-invalid'));
    }

    function linkErrorToField(errorDetail) {
        const lowerError = errorDetail.toLowerCase();
        if (lowerError.includes('имя') || lowerError.includes('username')) {
            showError('username', errorDetail);
        } else if (lowerError.includes('почт') || lowerError.includes('email')) {
            showError('email', errorDetail);
        } else if (lowerError.includes('пароль')) {
            showError('password', errorDetail);
        }
    }

    function showError(field, message) {
        const input = document.getElementById(field);
        const errorElement = document.getElementById(`${field}Error`);
        input.classList.add('is-invalid');
        errorElement.textContent = message;
    }

    function showToast(message, type = 'danger') {
        const toast = createToast(message, type);
        document.body.appendChild(toast);
        new bootstrap.Toast(toast, { autohide: true, delay: 5000 }).show();
        toast.addEventListener('hidden.bs.toast', () => toast.remove());
    }

    function createToast(message, type) {
        const toast = document.createElement('div');
        toast.className = `toast align-items-center text-white bg-${type} border-0 position-fixed bottom-0 end-0 m-3`;
        toast.setAttribute('role', 'alert');
        toast.innerHTML = `
            <div class="d-flex">
                <div class="toast-body">${message}</div>
                <button type="button" class="btn-close btn-close-white me-2 m-auto" data-bs-dismiss="toast"></button>
            </div>
        `;
        return toast;
    }
});