import json
import datetime
from aio_pika import IncomingMessage, Message, DeliveryMode
from aiobreaker import CircuitBreaker, CircuitBreakerError

from app.services.health import check_infrastructure_health
from app.messaging import rabbitmq
from app.rag.file_download.tem_file_download import processing_file_message
from app.services.content_generation.intent_parser import intent_parser
from app.config.connect_supabase import get_supabase_client
from app.config.database import AsyncSessionLocal
from app.config.redis import get_redis

MAX_RETRIES = 3


infra_breaker = CircuitBreaker(
    fail_max=5,
    timeout_duration=datetime.timedelta(seconds=30),
)



class TransientInfraError(Exception):
    """DB / Redis / Supabase blips. Safe, and worth, retrying."""


class PermanentDataError(Exception):
    """Bad payload, business-rule failure, etc."""


class PoisonMessageError(Exception):
    """Message body couldn't even be parsed / is missing required keys."""

class EmbeddingProviderError(TransientInfraError):
    """Gemini/embedding API is slow, timing out, or rate-limited."""


def classify_exception(exc: Exception) -> Exception:
    
    if isinstance(exc, (KeyError, ValueError, TypeError, json.JSONDecodeError)):
        return PermanentDataError(str(exc))

    embedding_error_names = ("GoogleGenerativeAIError", "ResourceExhausted", "ServerError")
    if type(exc).__name__ in embedding_error_names:
        return EmbeddingProviderError(str(exc))

   
    infra_exception_names = (
        "ConnectionError", "TimeoutError", "OperationalError",
        "PoolTimeout", "ConnectTimeout", "AMQPConnectionError",
    )
    if type(exc).__name__ in infra_exception_names:
        return TransientInfraError(str(exc))
 
    return TransientInfraError(str(exc))




@infra_breaker
async def guarded_health_check() -> bool:
    ok = await check_infrastructure_health()
    if not ok:
       
        raise TransientInfraError("infrastructure health check failed")
    return True



async def schedule_delayed_retry(message: IncomingMessage, data: dict):
    new_message = Message(
        body=json.dumps(data).encode(),
        delivery_mode=DeliveryMode.PERSISTENT,
        correlation_id=message.correlation_id,
    )
    await rabbitmq.exchange.publish(new_message, routing_key=rabbitmq.RETRY_QUEUE)


async def schedule_circuit_cooldown_retry(message: IncomingMessage):
    
    new_message = Message(
        body=message.body,
        delivery_mode=DeliveryMode.PERSISTENT,
        correlation_id=message.correlation_id,
    )
    await rabbitmq.exchange.publish(new_message, routing_key=rabbitmq.RETRY_QUEUE)


async def send_to_dlq(message: IncomingMessage, data: dict, error: Exception, task_type: str):
    print(f"LOG: Sending task {data['message_id']} to DLQ. Error: {error}")
    
    dlq_message = Message(
        body=message.body,
        delivery_mode=DeliveryMode.PERSISTENT,
        headers={
            "x-error": str(error),
            "x-error-type": type(error).__name__,
            "x-original-task": task_type,
        },
    )
    await rabbitmq.exchange.publish(dlq_message, routing_key=rabbitmq.DLQ_QUEUE)




async def handle_message(message: IncomingMessage):
    async with message.process(requeue=False):
        try:
            data = json.loads(message.body)
        except json.JSONDecodeError as e:
            
            await send_to_dlq(message, {}, PoisonMessageError(str(e)), "unknown")
            return

        required_keys = ("message_id", "retry_count", "task_type")
        if any(k not in data for k in required_keys):
            await send_to_dlq(
                message, data,
                PoisonMessageError(f"missing required keys, have: {list(data.keys())}"),
                data.get("task_type", "unknown"),
            )
            return

        supabase = await get_supabase_client()
        redis = await get_redis()
        payload = data.get("payload", {})
        unique_file_id = None
        if "file_name" in payload and "user_id" in payload:
            
            unique_file_id = payload["file_name"].split(".")[0]

        try:
            print(f"LOG: Processing task {data['message_id']} (Attempt {data['retry_count']})")

            if data["task_type"] == "file_processing":
                is_success = await processing_file_message(
                    file_path=payload["storage_path"],
                    user_id=payload["user_id"],
                    file_id=payload["id"],
                    file_name=payload["file_name"],
                    supabase=supabase,
                )
                if is_success:
                    if unique_file_id:
                        try:
                            await redis.set(unique_file_id, "DONE", ex=600)
                        except Exception as redis_error:
                            print(f"Redis error: {redis_error}")
                    return
                else:
                    if unique_file_id:
                        await redis.set(unique_file_id, "FAILED", ex=600)
                    raise PermanentDataError("Business logic returned False for file processing.")

            elif data["task_type"] == "content_generation":
                if isinstance(payload, str):
                    payload = json.loads(payload)
                async with AsyncSessionLocal() as session:
                    try:
                        await intent_parser(session, payload, payload["topic"])
                        await session.commit()
                    except Exception as e:
                        await session.rollback()
                        raise classify_exception(e) from e

        except PermanentDataError as e:
           
            print(f"ERROR (permanent, not retrying): {e}")
            if unique_file_id:
                await redis.set(unique_file_id, "FAILED_PERMANENT", ex=600)
            await send_to_dlq(message, data, e, data["task_type"])

        except Exception as raw_exc:
            classified = classify_exception(raw_exc) if not isinstance(raw_exc, (TransientInfraError, PermanentDataError)) else raw_exc
            print(f"ERROR: Task failed: {classified}")

            if isinstance(classified, PermanentDataError):
                if unique_file_id:
                    await redis.set(unique_file_id, "FAILED", ex=600)
                await send_to_dlq(message, data, classified, data["task_type"])
                return
            

            if isinstance(classified, EmbeddingProviderError):
                print(f"Embedding provider issue, retrying without infra check: {classified}")
                current_retries = data["retry_count"]
                if current_retries < MAX_RETRIES:
                    data["retry_count"] += 1
                    await schedule_delayed_retry(message, data)
                else:
                    if unique_file_id:
                        await redis.set(unique_file_id, "FAILED", ex=600)
                    await send_to_dlq(message, data, classified, data["task_type"])
                return

            # TransientInfraError consult the circuit breaker
            try:
                await guarded_health_check()
                circuit_open = False
            except CircuitBreakerError:
                circuit_open = True
            except TransientInfraError:
                circuit_open = infra_breaker.current_state == "open"

            if circuit_open:
                print("CIRCUIT OPEN: routing message to cooldown queue, no local sleep.")
                await schedule_circuit_cooldown_retry(message)
                return

            # Standard bounded retry with real delayed requeue 
            current_retries = data["retry_count"]
            if current_retries < MAX_RETRIES:
                data["retry_count"] += 1
                print(f"LOG: Scheduling retry {data['retry_count']} via retry queue TTL.")
                await schedule_delayed_retry(message, data)
            else:
                print("CRITICAL: Max retries reached. Moving to DLQ.")
                if unique_file_id:
                    await redis.set(unique_file_id, "FAILED", ex=600)
                await send_to_dlq(message, data, classified, data["task_type"])


async def start_consumer():

    await rabbitmq.channel.set_qos(prefetch_count=10)
    queue = await rabbitmq.channel.get_queue(rabbitmq.MAIN_QUEUE)
    await queue.consume(handle_message)