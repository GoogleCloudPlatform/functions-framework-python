import asyncio
import logging

from functions_framework import execution_id

logger = logging.getLogger(__name__)


async def async_print_message(request):
    json = await request.json()
    print(json.get("message"))
    return {"status": "success"}, 200


async def async_log_message(request):
    json = await request.json()
    logger.warning(json.get("message"))
    return {"status": "success"}, 200


async def async_function(request):
    return {"execution_id": request.headers.get("Function-Execution-Id")}


async def async_error(request):
    return 1 / 0


async def async_sleep(request):
    json = await request.json()
    message = json.get("message")
    logger.warning(message)
    await asyncio.sleep(1)
    logger.warning(message)
    return {"status": "success"}, 200


async def async_trace_test(request):
    context = execution_id._get_current_context()
    return {
        "execution_id": context.execution_id if context else None,
        "span_id": context.span_id if context else None,
    }


def sync_function_in_async_context(request):
    return {
        "execution_id": request.headers.get("Function-Execution-Id"),
        "type": "sync",
    }


def sync_cloudevent_with_context(cloud_event):
    context = execution_id._get_current_context()
    if context:
        logger.info(f"Execution ID in sync CloudEvent: {context.execution_id}")
    else:
        logger.error("No execution context in sync CloudEvent function!")
