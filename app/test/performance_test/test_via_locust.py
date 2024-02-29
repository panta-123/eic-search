from locust import HttpUser, task, between
import json

class WebsiteUser(HttpUser):
    wait_time = between(1, 3)

    @task
    def create_dataset(self):
        headers = {'Content-Type': 'application/json'}
        data = [
            {
                "scope": "string",
                "name": "string2",
                "campaign": "string",
                "detector_config": "string",
                "physics_process": "string",
                "generator": "string",
                "collision": "string",
                "q2": "string",
                "description": "string"
            }
        ]
        response = self.client.post("/create", data=json.dumps(data), headers=headers)
        if response.status_code != 201:
            print("Error creating dataset:", response.text)

    @task
    def search_dataset(self):
        headers = {'Content-Type': 'application/json'}
        data = {"scope": "string"}  # Modify this as per your search criteria
        response = self.client.post("/search", data=json.dumps(data), headers=headers)
        if response.status_code != 200:
            print("Error searching dataset:", response.text)

    @task
    def delete_dataset(self):
        dataset_id = "string:string2"  # Modify this as per your dataset ID
        response = self.client.delete(f"/delete/{dataset_id}")
        if response.status_code != 200:
            print("Error deleting dataset:", response.text)

    @task
    def update_dataset(self):
        dataset_id = "string:string2"  # Modify this as per your dataset ID
        headers = {'Content-Type': 'application/json'}
        data = {
            "scope": "updated_scope",
            "name": "updated_name",
            "campaign": "updated_campaign",
            "detector_config": "updated_detector_config",
            "physics_process": "updated_physics_process",
            "generator": "updated_generator",
            "collision": "updated_collision",
            "q2": "updated_q2",
            "description": "updated_description"
        }
        response = self.client.put(f"/update/{dataset_id}", data=json.dumps(data), headers=headers)
        if response.status_code != 200:
            print("Error updating dataset:", response.text)

    @task
    def get_mapping(self):
        response = self.client.get("/mapping")
        if response.status_code != 200:
            print("Error getting mapping:", response.text)
