from fastapi.testclient import TestClient
from app.main import app
from app import database

client_context = TestClient(app)
client = client_context.__enter__()

def test_health_endpoint():
    response = client.get('/api/health')
    assert response.status_code == 200
    assert response.json()['status'] == 'ok'

def test_process_save_export_and_delete():
    response = client.post('/api/process', json={
        'title': 'API test conversation',
        'text': 'We decided to use SQLite. Actually, we decided to use MongoDB instead of SQLite.',
        'save': True
    })
    assert response.status_code == 200
    data = response.json()
    cid = data['id']
    assert cid is not None
    assert client.get(f'/api/conversations/{cid}').status_code == 200
    assert client.get(f'/api/conversations/{cid}/export?format=json').status_code == 200
    assert client.get(f'/api/conversations/{cid}/export?format=txt').status_code == 200
    assert client.delete(f'/api/conversations/{cid}').status_code == 200
    assert client.get(f'/api/conversations/{cid}').status_code == 404

def test_invalid_process_input():
    response = client.post('/api/process', json={'text': '   '})
    assert response.status_code == 422
