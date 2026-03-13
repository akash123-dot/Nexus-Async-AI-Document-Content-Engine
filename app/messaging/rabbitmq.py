import aio_pika
from aio_pika import ExchangeType
from app.config.settings import settings

connection = None
channel = None

EXCHANGE_NAME = "task_exchange"
MAIN_QUEUE = "task.main"
RETRY_QUEUE = "task.retry"
DLQ_QUEUE = "task.dlq"

async def connect_rabbitmq():
    global connection, channel
    

    # connection = await aio_pika.connect_robust("amqp://guest:guest@rabbitmq/")
    connection = await aio_pika.connect_robust(settings.RABBITMQ_URL)

    channel = await connection.channel()

    await channel.set_qos(prefetch_count=5)


    exchange = await channel.declare_exchange(
        EXCHANGE_NAME,
        ExchangeType.DIRECT,
        durable=True, # If RabbitMQ restarts, the exchange survives.
    )

# 4. DLQ (Dead Letter Queue):
 
    dlq = await channel.declare_queue(DLQ_QUEUE, durable=True)
    await dlq.bind(exchange, routing_key=DLQ_QUEUE)

    retry_queue = await channel.declare_queue(
            RETRY_QUEUE,
            durable=True,
            arguments={
          
                "x-message-ttl": 5000, 
                
                "x-dead-letter-exchange": EXCHANGE_NAME,
                
                "x-dead-letter-routing-key": MAIN_QUEUE,
            },
        )
    await retry_queue.bind(exchange, routing_key=RETRY_QUEUE)

    main_queue = await channel.declare_queue(
        MAIN_QUEUE,
        durable=True,
        arguments={
        
            "x-dead-letter-exchange": EXCHANGE_NAME,
            
            "x-dead-letter-routing-key": RETRY_QUEUE,
        },
    )
    await main_queue.bind(exchange, routing_key=MAIN_QUEUE)

async def close_rabbitmq():
    global connection
    if connection:
        await connection.close()
        print("LOG: RabbitMQ connection closed.")