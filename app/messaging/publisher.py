import json
import uuid
from datetime import datetime, timezone
from aio_pika import Message, DeliveryMode
from app.messaging import rabbitmq


async def publish_user_task(*, user_id: str, task_type: str, payload: dict):
    
    # Safety Check
    if rabbitmq.channel is None:
        raise RuntimeError("RabbitMQ connection is not ready yet.")

    message_id = str(uuid.uuid4())
    
    message_body = {
        "message_id": message_id,
        "task_type": task_type,
        "user_id": user_id,
        "retry_count": 0,               
        "payload": payload,               
        "created_at": datetime.now(timezone.utc).isoformat(),
    }

    message = Message(
        body=json.dumps(message_body).encode(),
        delivery_mode=DeliveryMode.PERSISTENT, 
        content_type="application/json",      
        correlation_id=message_body["message_id"]
    )


    exchange = await rabbitmq.channel.get_exchange(rabbitmq.EXCHANGE_NAME)

    await exchange.publish(
        message,
        routing_key=rabbitmq.MAIN_QUEUE, # This matches the binding in rabbitmq.py
    )

    # print(f"LOG: Published task {message_body['message_id']} for user {user_id}")

    return message_id   # this is for our api


