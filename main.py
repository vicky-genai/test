{
  "wi_d2c1cc42": {
    "work_item_id": "wi_d2c1cc42",
    "incident_id": "inc_52db62c42",
    "cluster_name": "drift-monitoring-cluster",
    "node_pool": "default-pool",
    "namespace": "default",
    "project_id": "gebu-data-ml-day0-01-333910",
    "region": "us-central1",
    "status": "PENDING"
  }
} 


import json
import base64
from unittest.mock import patch, MagicMock
 
DUMMY_DATA_FILE = "mock_data.json"
 
def load_mock_data():
    with open(DUMMY_DATA_FILE, "r") as f:
        return json.load(f)
 
# --- 1. MOCK DATABASE FUNCTIONS ---
def mock_get_work_item_status(work_item_id):
    print(f"[MOCK DB] Fetching status for: {work_item_id}")
    return load_mock_data().get(work_item_id, {}).get("status", "UNKNOWN")
 
def mock_validate_work_item(work_item_id):
    print(f"[MOCK DB] Validating work item: {work_item_id}")
    data = load_mock_data()
    if work_item_id in data:
        item = data[work_item_id]
        item["status"] = "valid"
        return item
    return {"status": "invalid", "reason": "Not found"}
 
def mock_get_incident_id(work_item_id):
    return load_mock_data().get(work_item_id, {}).get("incident_id", "unknown-incident")
 
def mock_generic_insert(*args, **kwargs):
    print(f"[MOCK DB] Skipped DB Insert/Update. Success.")
    return "mocked_id_123"
 
def mock_update_workflow_status(*args, **kwargs):
    print(f"[MOCK DB] Workflow status updated: {kwargs}")
    return {"status": "success"}
 
# --- 2. APPLY PATCHES (Must happen before importing the app) ---
# This intercepts the functions in memory and replaces them with our mocks
patch('app.cloud_event_handler._get_work_item_status', mock_get_work_item_status).start()
patch('app.tools.tools.validate_work_item', mock_validate_work_item).start()
patch('app.tools.tools._get_incident_id', mock_get_incident_id).start()
patch('app.tools.tools.save_incident_enrichment', mock_generic_insert).start()
patch('app.tools.tools.save_incident_summary', mock_generic_insert).start()
patch('app.tools.tools.record_notification_result', mock_generic_insert).start()
patch('app.tools.tools.set_action_transitions', mock_generic_insert).start()
patch('app.tools.tools.update_work_item_workflow_status', mock_update_workflow_status).start()
 
# We completely disable the SQLAlchemy engine to prevent any network timeouts
patch('app.tools.tools.engine', MagicMock()).start()
patch('app.cloud_event_handler.engine', MagicMock()).start()
 
# --- 3. IMPORT APP & RUN TEST ---
# Now that the DB is mocked, it's safe to import your FastAPI app
from fastapi.testclient import TestClient
from app.fast_api_app import app
 
client = TestClient(app)
 
def run_offline_test():
    print("🚀 Starting Offline Agent Pipeline Test...\n")
    # Create the exact Pub/Sub Base64 payload Eventarc would send
    payload = {"work_item_id": "wi_d2c1cc42"}
    base64_payload = base64.b64encode(json.dumps(payload).encode('utf-8')).decode('utf-8')
    pubsub_message = {"message": {"data": base64_payload}}
    # Fire the request at your endpoint
    response = client.post("/cloudevent", json=pubsub_message)
    print("\n✅ Test Complete!")
    print(f"HTTP Status Code: {response.status_code}")
    print(f"Response Body:\n{json.dumps(response.json(), indent=2)}")
 
if __name__ == "__main__":
    run_offline_test() 
    