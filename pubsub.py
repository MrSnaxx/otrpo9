import tornado.web
import tornado.websocket
import tornado.ioloop
import aioredis
import json

class ChatHandler(tornado.websocket.WebSocketHandler):
    clients = set()

    def initialize(self, redis):
        self.redis = redis

    async def open(self):
        ChatHandler.clients.add(self)
        await self.notify_clients()
        self.stream = await self.redis.subscribe("chat_channel")
        tornado.ioloop.IOLoop.current().spawn_callback(self.listen_to_redis)

    async def on_message(self, message):
        data = json.loads(message)
        await self.redis.publish("chat_channel", json.dumps(data))

    async def on_close(self):
        ChatHandler.clients.remove(self)
        await self.notify_clients()

    async def listen_to_redis(self):
        while True:
            message = await self.stream[0].get()
            if message:
                for client in ChatHandler.clients:
                    client.write_message(message.decode('utf-8'))

    async def notify_clients(self):
        user_list = [f"User {id(client)}" for client in ChatHandler.clients]
        notification = json.dumps({"type": "users", "data": user_list})
        for client in ChatHandler.clients:
            client.write_message(notification)


def make_app(redis):
    return tornado.web.Application([
        (r"/chat", ChatHandler, dict(redis=redis)),
        (r"/(.*)", tornado.web.StaticFileHandler, {"path": "static", "default_filename": "index.html"}),
    ])


async def main():
    redis = await aioredis.from_url("redis://localhost")
    app = make_app(redis)
    app.listen(8888)
    print("Server started on http://localhost:8888")
    await tornado.ioloop.IOLoop.current().start()


if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
