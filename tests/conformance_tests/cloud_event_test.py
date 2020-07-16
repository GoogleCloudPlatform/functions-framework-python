from cloudevents.sdk import converters
from cloudevents.sdk import marshaller
from cloudevents.sdk.converters import structured

def test(cloudevent):
    m = marshaller.NewHTTPMarshaller([structured.NewJSONHTTPCloudEventConverter()])
    headers, body = m.ToRequest(cloudevent, converters.TypeStructured, lambda x: x)
    text_file = open("function_output.json", "w")
    text_file.write(body.getvalue().decode("utf-8"))
    text_file.close()
