from arq.connections import RedisSettings

async def startup(ctx):
    print("Worker starting up...")

class WorkerSettings:
    functions = []
    redis_settings = RedisSettings(host='localhost', port=6379)
    on_startup = startup