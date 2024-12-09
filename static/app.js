// Запрос имени пользователя при входе
let username = prompt("Enter your username:", "Guest");

// Если пользователь не ввел никнейм (оставил поле пустым), заменяем его на "Unknown"
if (!username.trim()) {
    username = "Unknown";
}

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
        if (data.username === "System") {
            // Отображение системных сообщений (например, когда пользователь зашел)
            message.innerHTML = `<em>${data.message}</em>`;
        } else {
            message.innerHTML = `<strong>${data.username}:</strong> ${data.message}`;
        }
        messages.appendChild(message);
    }
};

// Отправка сообщения
messageInput.addEventListener("keypress", function(event) {
    if (event.key === "Enter") {
        const message = messageInput.value.trim();
        if (message) {
            ws.send(JSON.stringify({ username, message }));
            messageInput.value = "";
        }
    }
});

// Отправка сообщения о входе в чат
ws.onopen = function() {
    // Отправляем сообщение о новом пользователе
    ws.send(JSON.stringify({ username, message: "" }));
    // Отправляем всем, что пользователь зашел
};
