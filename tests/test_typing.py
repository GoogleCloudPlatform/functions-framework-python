import typing

if typing.TYPE_CHECKING:  # pragma: no cover
    import flask

    from cloudevents.http.event import CloudEvent

    import functions_framework

    @functions_framework.http
    def hello(request: flask.Request) -> flask.typing.ResponseReturnValue:
        return "Hello world!"

    @functions_framework.cloud_event
    def hello_cloud_event(cloud_event: CloudEvent) -> None:
        print(f"Received event: id={cloud_event['id']} and data={cloud_event.data}")

    from starlette.requests import Request

    import functions_framework.aio

    @functions_framework.aio.http
    async def hello_async(request: Request) -> str:
        return "Hello world!"

    @functions_framework.aio.cloud_event
    async def hello_cloud_event_async(cloud_event: CloudEvent) -> None:
        print(f"Received event: id={cloud_event['id']} and data={cloud_event.data}")
