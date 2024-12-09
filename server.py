import tornado.web
import tornado.websocket
import tornado.ioloop
import asyncio
import redis.asyncio as aioredis
import json

class ChatHandler(tornado.websocket.WebSocketHandler):
    clients = set()

    def initialize(self, redis):
        self.redis = redis

    async def open(self):
        ChatHandler.clients.add(self)
        await self.notify_clients()

    async def on_message(self, message):
        # Распаковываем сообщение от клиента
        data = json.loads(message)
        username = data.get("username", "Unknown")  # Имя пользователя
        message_text = data.get("message", "")

        # Формируем сообщение для отправки
        redis_message = json.dumps({"username": username, "message": message_text})

        # Публикуем сообщение в Redis
        await self.redis.publish("chat_channel", redis_message)

    async def on_close(self):
        ChatHandler.clients.remove(self)
        await self.notify_clients()

    @classmethod
    async def broadcast_message(cls, message):
        for client in list(cls.clients):
            if client.ws_connection:
                client.write_message(message)

    @classmethod
    async def notify_clients(cls):
        user_list = [f"User {id(client)}" for client in cls.clients]
        notification = json.dumps({"type": "users", "data": user_list})
        await cls.broadcast_message(notification)


async def redis_listener(redis):
    pubsub = redis.pubsub()
    await pubsub.subscribe("chat_channel")

    while True:
        message = await pubsub.get_message(ignore_subscribe_messages=True)
        if message and message["type"] == "message":
            # Рассылаем сообщение всем клиентам
            data = message["data"].decode("utf-8")
            await ChatHandler.broadcast_message(data)


def make_app(redis):
    return tornado.web.Application([
        (r"/chat", ChatHandler, dict(redis=redis)),
        (r"/(.*)", tornado.web.StaticFileHandler, {"path": "static", "default_filename": "index.html"}),
    ])


async def main():
    redis = aioredis.from_url("redis://localhost:6379")

    await redis.set("test_key", "Hello, Redis!")
    value = await redis.get("test_key")
    print(value.decode("utf-8"))

    app = make_app(redis)
    app.listen(8888)
    print("Server started on http://localhost:8888")

    await asyncio.gather(redis_listener(redis))


if __name__ == "__main__":
    asyncio.run(main())
