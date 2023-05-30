import typing

if typing.TYPE_CHECKING:  # pragma: no cover
    import flask
    import functions_framework
    from cloudevents.http.event import CloudEvent

    @functions_framework.http
    def hello(request: flask.Request) -> flask.typing.ResponseReturnValue:
        return "Hello world!"

    @functions_framework.cloud_event
    def hello_cloud_event(cloud_event: CloudEvent) -> None:
        print(f"Received event: id={cloud_event['id']} and data={cloud_event.data}")
