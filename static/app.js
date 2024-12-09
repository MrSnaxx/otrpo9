// Запрос имени пользователя при входе
const username = prompt("Enter your username:", "Guest");

// Инициализация WebSocket
const ws = new WebSocket("ws://localhost:8888/chat");
const messageInput = document.getElementById("message-input");
const messages = document.getElementById("messages");
const userList = document.getElementById("user-list");

// Обработка входящих сообщений
ws.onmessage = function(event) {
    const data = JSON.parse(event.data);

    if (data.type === "users") {
        // Обновление списка пользователей
        userList.innerHTML = data.data.map(user => `<li>${user}</li>`).join("");
    } else {
        // Отображение сообщений
        const message = document.createElement("div");
        message.innerHTML = `<strong>${data.username}:</strong> ${data.message}`;
        messages.appendChild(message);
    }
};

// Отправка сообщений
messageInput.addEventListener("keypress", function(event) {
    if (event.key === "Enter") {
        const message = messageInput.value.trim();
        if (message) {
            ws.send(JSON.stringify({ username, message }));
            messageInput.value = "";
        }
    }
});
