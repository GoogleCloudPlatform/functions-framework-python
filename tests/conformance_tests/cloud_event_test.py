import json


def test(cloudevent):
    text_file = open("function_output.json", "w")
    text_file.write(json.dumps(cloudevent.Data()))
    text_file.close()
