import json
from aio_pika import IncomingMessage, Message, DeliveryMode
from app.messaging import rabbitmq
from app.rag.file_download.tem_file_download import processing_file_message
from app.services.content_generation.intent_parser import intent_parser
from app.config.connect_supabase import get_supabase_client
from app.config.database import AsyncSessionLocal
from app.config.redis import get_redis

MAX_RETRIES = 3

async def handle_message(message: IncomingMessage):
    # 1. The Safety Net
    # "process(requeue=False)" means: "If I crash unexpectedly, DO NOT put this 
 
    async with message.process(requeue=False):
        
        
        data = json.loads(message.body)
        supabase = await get_supabase_client()
        redis = await get_redis()

        try:
            print(f"LOG: Processing task {data['message_id']} (Attempt {data['retry_count']})")
            
            if data["task_type"] == "file_processing":
                payload = data["payload"]
                unique_file_id = payload["file_name"].split(".")[0]

                # --- BUSINESS LOGIC---
                is_success = await processing_file_message(
                    file_path=payload["storage_path"],
                    user_id=payload["user_id"],
                    file_id=payload["id"],
                    file_name=payload["file_name"],
                    supabase=supabase
                )

                if is_success:
                    print("Task Success. Message will be Auto-Acked.")
             
                    await redis.set(unique_file_id, "DONE", ex=600)
                    
                    return
                
                else:
                    await redis.set(unique_file_id, "FAILED", ex=600)
                    raise Exception("Business Logic returned False Save Failed")
                
                
            elif data["task_type"] == "content_generation":

                payload = data["payload"]

                if isinstance(payload, str):
                    payload = json.loads(payload)

                async with AsyncSessionLocal() as session:
                    try:
                        await intent_parser(session, payload, payload["topic"])
                        await session.commit()
                    except Exception as e:
                        await session.rollback()
                        raise 

                # if is_success:
                #     print("Task Success. Message will be Auto-Acked.")
                #     return
                
                # else:
                #     raise Exception("Business Logic returned False (Save Failed)" )
    

        except Exception as e:
            print(f"ERROR: Task failed: {e}")
           
            # 2. Retry Logic
            current_retries = data["retry_count"]
            
            if current_retries < MAX_RETRIES:
                # INCREMENT RETRY COUNT
                data["retry_count"] += 1
                
                # CREATE A FRESH MESSAGE
                
                new_message = Message(
                    body=json.dumps(data).encode(),
                    delivery_mode=DeliveryMode.PERSISTENT,
                    correlation_id=message.correlation_id # Keep the same ID for tracking
                )

               
                await rabbitmq.channel.default_exchange.publish(
                    new_message,
                    routing_key=rabbitmq.RETRY_QUEUE
                )
                print(f"LOG: Sent to Retry Queue (Wait 5s)")
                
            else:
                # 3. Dead Letter Logic (Max Retries Exceeded)
                print(f"CRITICAL: Max retries reached. Moving to DLQ.")
                
                # Create message for DLQ
                dlq_message = Message(
                    body=message.body, 
                    delivery_mode=DeliveryMode.PERSISTENT,
                    headers={"x-error": str(e)} 
                )
                
                await rabbitmq.channel.default_exchange.publish(
                    dlq_message,
                    routing_key=rabbitmq.DLQ_QUEUE
                )

async def start_consumer():

    queue = await rabbitmq.channel.get_queue(rabbitmq.MAIN_QUEUE)
    await queue.consume(handle_message)