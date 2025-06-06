import json


class PrettyJSONEncoder(json.JSONEncoder):
    def __init__(self, *args, indent, **kwargs):
        super().__init__(*args, indent=4, **kwargs)
