document.addEventListener('DOMContentLoaded', function() {
    const tableBody = document.getElementById('sessions-table-body');
    const pagination = document.getElementById('pagination');
    const sessionsCount = document.getElementById('sessions-count');
    const deleteAllBtn = document.getElementById('delete-all-btn');
    let currentPage = 1;
    const itemsPerPage = 10;
    let totalSessions = 0;
    let allSessions = [];

    // Загрузка данных
    async function loadSessions() {
        try {
            showLoading();

            const response = await fetch('/admin/get_sessions', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                }
            });

            if (!response.ok) {
                throw new Error(await response.text());
            }

            const data = await response.json();
            allSessions = Object.entries(data).map(([key, value]) => ({
                key,
                userId: value,
                // createdAt: new Date(value.created_at).toLocaleString()
            }));

            totalSessions = allSessions.length;
            updateSessionsCount();
            renderTable();
            renderPagination();

            // Активируем кнопку удалить все, если есть сессии
            deleteAllBtn.disabled = totalSessions === 0;
            deleteAllBtn.addEventListener('click', confirmDeleteAll);

        } catch (error) {
            console.error('Ошибка загрузки сессий:', error);
            showError('Не удалось загрузить сессии');
        }
    }

    // Отображение данных в таблице
    function renderTable() {
        const startIndex = (currentPage - 1) * itemsPerPage;
        const endIndex = Math.min(startIndex + itemsPerPage, totalSessions);
        const sessionsToShow = allSessions.slice(startIndex, endIndex);

        if (sessionsToShow.length === 0) {
            tableBody.innerHTML = `
                <tr>
                    <td colspan="4" class="text-center py-5">
                        <div class="alert alert-info mb-0">
                            <i class="bi bi-info-circle me-2"></i>
                            Активные сессии не найдены
                        </div>
                    </td>
                </tr>
            `;
            return;
        }

        tableBody.innerHTML = sessionsToShow.map(session => `
            <tr>
                <td><code>${session.key}</code></td>
                <td>${session.userId}</td>
<!--                <td>${session.createdAt}</td>-->
                <td>
                    <button type="button" class="btn btn-sm btn-outline-danger delete-btn" data-key="${session.userId}">
                        <i class="bi bi-trash"></i> Удалить
                    </button>
                </td>
            </tr>
        `).join('');

        // Добавляем обработчики для кнопок удаления
        document.querySelectorAll('.delete-btn').forEach(btn => {
            btn.addEventListener('click', () => confirmDeleteSession(btn.dataset.key));
        });
    }

    // Пагинация
    function renderPagination() {
        const totalPages = Math.ceil(totalSessions / itemsPerPage);

        if (totalPages <= 1) {
            pagination.innerHTML = '';
            return;
        }

        let paginationHTML = '';

        // Кнопка "Назад"
        paginationHTML += `
            <li class="page-item ${currentPage === 1 ? 'disabled' : ''}">
                <a class="page-link" href="#" data-page="${currentPage - 1}">Назад</a>
            </li>
        `;

        // Страницы
        for (let i = 1; i <= totalPages; i++) {
            paginationHTML += `
                <li class="page-item ${i === currentPage ? 'active' : ''}">
                    <a class="page-link" href="#" data-page="${i}">${i}</a>
                </li>
            `;
        }

        // Кнопка "Вперед"
        paginationHTML += `
            <li class="page-item ${currentPage === totalPages ? 'disabled' : ''}">
                <a class="page-link" href="#" data-page="${currentPage + 1}">Вперед</a>
            </li>
        `;

        pagination.innerHTML = paginationHTML;

        // Обработчики событий для пагинации
        document.querySelectorAll('.page-link').forEach(link => {
            link.addEventListener('click', (e) => {
                e.preventDefault();
                currentPage = parseInt(link.dataset.page);
                renderTable();
                renderPagination();
            });
        });
    }

    // Обновление счетчика сессий
    function updateSessionsCount() {
        sessionsCount.textContent = `Всего: ${totalSessions}`;
    }

    // Подтверждение удаления одной сессии
    async function confirmDeleteSession(sessionKey) {
        if (!confirm('Вы уверены, что хотите удалить эту сессию?')) {
            return;
        }

        try {
            const response = await fetch(`/admin/sessions_management/delete/${sessionKey}`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                }
            });

            if (!response.ok) {
                throw new Error(await response.text());
            }

            showToast('Сессия успешно удалена', 'success');
            await loadSessions(); // Перезагружаем данные

        } catch (error) {
            console.error('Ошибка удаления сессии:', error);
            showToast('Не удалось удалить сессию', 'danger');
        }
    }

    // Подтверждение удаления всех сессий
    async function confirmDeleteAll() {
        if (!confirm('Вы уверены, что хотите удалить ВСЕ сессии?')) {
            return;
        }

        try {
            // Удаляем каждую сессию по очереди
            for (const session of allSessions) {
                const response = await fetch(`/admin/sessions_management/delete_all`, {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    }
                });

                if (!response.ok) {
                    throw new Error(await response.text());
                }
            }

            showToast('Все сессии успешно удалены', 'success');
            await loadSessions(); // Перезагружаем данные

        } catch (error) {
            console.error('Ошибка удаления сессий:', error);
            showToast('Не удалось удалить все сессии', 'danger');
        }
    }

    // Вспомогательные функции
    function showLoading() {
        tableBody.innerHTML = `
            <tr>
                <td colspan="4" class="text-center py-5">
                    <div class="spinner-border text-primary" role="status">
                        <span class="visually-hidden">Загрузка...</span>
                    </div>
                </td>
            </tr>
        `;
    }

    function showError(message) {
        tableBody.innerHTML = `
            <tr>
                <td colspan="4" class="text-center py-5">
                    <div class="alert alert-danger mb-0">
                        <i class="bi bi-exclamation-triangle me-2"></i>
                        ${message}
                    </div>
                </td>
            </tr>
        `;
    }

    function showToast(message, type = 'danger') {
        const toast = document.createElement('div');
        toast.className = `toast align-items-center text-white bg-${type} border-0 position-fixed bottom-0 end-0 m-3`;
        toast.setAttribute('role', 'alert');
        toast.setAttribute('aria-live', 'assertive');
        toast.setAttribute('aria-atomic', 'true');

        toast.innerHTML = `
            <div class="d-flex">
                <div class="toast-body">${message}</div>
                <button type="button" class="btn-close btn-close-white me-2 m-auto" data-bs-dismiss="toast"></button>
            </div>
        `;

        document.body.appendChild(toast);
        new bootstrap.Toast(toast, {autohide: true, delay: 5000}).show();

        toast.addEventListener('hidden.bs.toast', () => {
            toast.remove();
        });
    }

    // Инициализация
    loadSessions();
});