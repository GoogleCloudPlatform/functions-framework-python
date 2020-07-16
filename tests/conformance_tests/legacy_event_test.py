import marshal


def test(data, context):
    bytes = marshal.dumps(data)
    redata = marshal.loads(bytes)
    text_file = open("/app/function_output.json", "w")
    n = text_file.write(str(redata))
    text_file.close()
