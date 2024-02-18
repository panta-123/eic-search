from elasticsearch import Elasticsearch

def create_index_if_not_exists(es: Elasticsearch):
    INDEX_NAME = "dataset_index"
    mapping = {
        "properties": {
            "id": {"type": "keyword"},
            "scope": {"type": "keyword"},
            "name": {"type": "text", "analyzer": "standard"},
            "campaign": {"type": "keyword"},
            "detector_config": {"type": "keyword"},
            "physics_process": {"type": "keyword"},
            "generator": {"type": "keyword"},
            "collision": {"type": "keyword"},
            "q2": {"type": "keyword"},
            }
    }

    if not es.indices.exists(INDEX_NAME):
        es.indices.create(index=INDEX_NAME, body=mapping)
        print(f"Index '{INDEX_NAME}' created with mapping.")
    else:
        print(f"Index '{INDEX_NAME}' already exists.")

