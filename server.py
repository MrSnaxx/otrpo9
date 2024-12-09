import tornado.web
import tornado.websocket
import tornado.ioloop
import asyncio
import redis.asyncio as aioredis
import json

class ChatHandler(tornado.websocket.WebSocketHandler):
    clients = set()  # Множество клиентов
    usernames = {}  # Словарь с соответствием клиент -> никнейм

    def initialize(self, redis):
        self.redis = redis

    async def open(self):
        # Запрашиваем никнейм пользователя
        self.username = None

    async def on_message(self, message):
        data = json.loads(message)
        if self.username is None:
            # Если никнейм не был установлен, сохраняем его
            self.username = data.get("username", "Unknown")
            ChatHandler.usernames[self] = self.username
            ChatHandler.clients.add(self)
            await self.notify_clients()  # Уведомляем остальных пользователей
            # Отправляем всем сообщение о новом пользователе
            system_message = json.dumps({"username": "System", "message": f"{self.username} has joined the chat"})
            await self.redis.publish("chat_channel", system_message)
        else:
            # Отправляем сообщение в Redis, как было раньше
            message_text = data.get("message", "")
            redis_message = json.dumps({"username": self.username, "message": message_text})
            await self.redis.publish("chat_channel", redis_message)

    def on_close(self):
        # Удаляем клиента из списка и уведомляем об этом
        if self in ChatHandler.usernames:
            del ChatHandler.usernames[self]
        ChatHandler.clients.remove(self)
        asyncio.create_task(self.notify_clients())
        # Отправляем всем сообщение о выходе пользователя
        system_message = json.dumps({"username": "System", "message": f"{self.username} has left the chat"})
        asyncio.create_task(self.redis.publish("chat_channel", system_message))

    @classmethod
    async def broadcast_message(cls, message):
        for client in list(cls.clients):
            if client.ws_connection:
                client.write_message(message)

    @classmethod
    async def notify_clients(cls):
        # Формируем список никнеймов
        user_list = list(cls.usernames.values())
        notification = json.dumps({"type": "users", "data": user_list})
        await cls.broadcast_message(notification)

async def redis_listener(redis):
    pubsub = redis.pubsub()
    await pubsub.subscribe("chat_channel")

    while True:
        message = await pubsub.get_message(ignore_subscribe_messages=True)
        if message and message["type"] == "message":
            data = message["data"].decode("utf-8")
            await ChatHandler.broadcast_message(data)

def make_app(redis):
    return tornado.web.Application([
        (r"/chat", ChatHandler, dict(redis=redis)),
        (r"/(.*)", tornado.web.StaticFileHandler, {"path": "static", "default_filename": "index.html"}),
    ])

async def main():
    redis = aioredis.from_url("redis://localhost:6379")

    app = make_app(redis)
    app.listen(8888)
    print("Server started on http://localhost:8888")

    await asyncio.gather(redis_listener(redis))

if __name__ == "__main__":
    asyncio.run(main())
