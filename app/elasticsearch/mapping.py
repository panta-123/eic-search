def create_index_if_not_exists(es):
    index_name = "dataset_index"
    mapping = {
        "properties": {
            "scope": {"type": "keyword"},
            "name": {"type": "text", "analyzer": "standard"},
            "campaign": {"type": "keyword"},
            "detector_config": {"type": "keyword"},
            "physics_process": {"type": "keyword"},
            "generator": {"type": "keyword"},
            "collision": {"type": "keyword"},
            "q2": {"type": "keyword"},
            "description": {"type": "text", "analyzer": "standard"}
            }
    }
    index_body = {
            'settings': {
                'index': {
                'number_of_shards': 4
                }
            },
            'mappings': mapping
            }
    if not es.indices.exists(index_name):
        es.indices.create(index=index_name, body=index_body)
        print(f"Index '{index_name}' created with mapping.")
    else:
        print(f"Index '{index_name}' already exists.")

