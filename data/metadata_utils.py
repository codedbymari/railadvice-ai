import json

def serialize_metadata(meta: dict) -> dict:
    """
    Convert all metadata values to ChromaDB-compatible types:
    - Lists/dicts → JSON string
    - None → empty string
    """
    new_meta = {}
    for k, v in meta.items():
        if v is None:
            new_meta[k] = ""
        elif isinstance(v, (list, dict)):
            # Convert list/dict to JSON string
            new_meta[k] = json.dumps(v, ensure_ascii=False)
        elif isinstance(v, (str, int, float, bool)):
            new_meta[k] = v
        else:
            # fallback for unexpected types
            new_meta[k] = str(v)
    return new_meta

def deserialize_metadata(meta: dict) -> dict:
    """
    Convert JSON string values back to list/dict where possible.
    """
    new_meta = {}
    for k, v in meta.items():
        try:
            new_meta[k] = json.loads(v)
        except (json.JSONDecodeError, TypeError):
            new_meta[k] = v
    return new_meta
