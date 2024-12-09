const ws = new WebSocket("ws://localhost:8888/chat");
const messageInput = document.getElementById("message-input");
const messages = document.getElementById("messages");
const userList = document.getElementById("user-list");

ws.onmessage = function(event) {
    const data = JSON.parse(event.data);

    if (data.type === "users") {
        userList.innerHTML = data.data.map(user => `<li>${user}</li>`).join("");
    } else {
        const message = document.createElement("div");
        message.textContent = data.message;
        messages.appendChild(message);
    }
};

messageInput.addEventListener("keypress", function(event) {
    if (event.key === "Enter") {
        const message = messageInput.value;
        ws.send(JSON.stringify({ message }));
        messageInput.value = "";
    }
});
