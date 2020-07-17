import json


def test(data, context):
    dict = {"data": json.loads(json.dumps(data)), "context": json.loads(json.dumps(context.__dict__))}

    text_file = open("/app/function_output.json", "w")
    text_file.write(json.dumps(dict))
    text_file.close()
