import requests
import os
from typing import Dict, Any

class HydraxAPI:
    def __init__(self):
        self.base_url = "http://up.hydrax.net"
        self.api_key = os.getenv('HYDRAX_API_ID')
    
    def upload_video(self, file_path: str, file_name: str) -> Dict[str, Any]:
        """Upload video to Hydrax"""
        if not self.api_key:
            raise ValueError("HYDRAX_API_ID not configured")
        
        url = f"{self.base_url}/{self.api_key}"
        
        with open(file_path, 'rb') as f:
            files = {'file': (file_name, f, 'video/mp4')}
            response = requests.post(url, files=files)
        
        if response.status_code == 200:
            return response.json()
        else:
            raise Exception(f"Upload failed: {response.text}")
    
    def update_api_key(self, new_key: str):
        """Update Hydrax API key"""
        self.api_key = new_key

hydrax_api = HydraxAPI()
