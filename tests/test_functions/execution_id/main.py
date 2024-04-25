import logging

logger = logging.getLogger(__name__)


def print_message(request):
    json = request.get_json(silent=True)
    print(json.get("message"))
    return 200


def log_message(request):
    json = request.get_json(silent=True)
    logger.info(json.get("message"))
    return 200


def function(request):
    return {"execution_id": request.headers.get("Function-Execution-Id")}


def error(request):
    return 1 / 0
