import requests
import json
from config import Config

class WireMockService:
    def __init__(self, base_url=None):
        self.base_url = base_url or Config.WIREMOCK_ADMIN_API
    
    def sync_mapping(self, mapping):
        """Sync a single mapping to WireMock"""
        try:
            # Parse response headers if stored as JSON string
            headers = {}
            if mapping['response_headers']:
                try:
                    headers = json.loads(mapping['response_headers'])
                except:
                    pass
            
            # Build WireMock stub mapping
            stub = {
                "request": {
                    "method": mapping['request_method'],
                    "urlPath": mapping['request_url']
                },
                "response": {
                    "status": mapping['response_status'],
                    "body": mapping['response_body'] or "",
                    "headers": headers
                },
                "priority": mapping['priority']
            }
            
            # Send to WireMock
            response = requests.post(
                f"{self.base_url}/mappings",
                json=stub,
                headers={'Content-Type': 'application/json'}
            )
            
            if response.status_code in [200, 201]:
                return True, response.json()
            else:
                return False, f"WireMock error: {response.status_code} - {response.text}"
        except Exception as e:
            return False, f"Error syncing to WireMock: {str(e)}"
    
    def sync_all_mappings(self, mappings):
        """Sync all active mappings to WireMock"""
        # First, reset all mappings
        try:
            requests.post(f"{self.base_url}/mappings/reset")
        except:
            pass
        
        results = []
        for mapping in mappings:
            success, result = self.sync_mapping(mapping)
            results.append({
                'mapping_id': mapping['id'],
                'name': mapping['name'],
                'success': success,
                'result': result
            })
        
        return results
    
    def delete_all_mappings(self):
        """Delete all mappings from WireMock"""
        try:
            response = requests.post(f"{self.base_url}/mappings/reset")
            return response.status_code == 200
        except Exception as e:
            return False
    
    def test_connection(self):
        """Test WireMock connection"""
        try:
            response = requests.get(f"{self.base_url}/mappings")
            return response.status_code == 200
        except:
            return False
