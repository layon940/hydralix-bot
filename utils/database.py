import json
import os
from typing import Dict, List, Any

class Database:
    def __init__(self):
        self.users_file = 'users.json'
        self.settings_file = 'settings.json'
        self.queue_file = 'queue.json'
        
        # Initialize files if they don't exist
        for file in [self.users_file, self.settings_file, self.queue_file]:
            if not os.path.exists(file):
                with open(file, 'w') as f:
                    json.dump({}, f)
    
    def get_users(self) -> List[int]:
        """Get all authorized users"""
        with open(self.users_file, 'r') as f:
            data = json.load(f)
            return list(data.get('authorized_users', []))
    
    def add_user(self, user_id: int):
        """Add authorized user"""
        with open(self.users_file, 'r') as f:
            data = json.load(f)
        
        if 'authorized_users' not in data:
            data['authorized_users'] = []
        
        if user_id not in data['authorized_users']:
            data['authorized_users'].append(user_id)
        
        with open(self.users_file, 'w') as f:
            json.dump(data, f, indent=2)
    
    def remove_user(self, user_id: int):
        """Remove authorized user"""
        with open(self.users_file, 'r') as f:
            data = json.load(f)
        
        if 'authorized_users' in data and user_id in data['authorized_users']:
            data['authorized_users'].remove(user_id)
        
        with open(self.users_file, 'w') as f:
            json.dump(data, f, indent=2)
    
    def get_user_language(self, user_id: int) -> str:
        """Get user language preference"""
        with open(self.settings_file, 'r') as f:
            data = json.load(f)
            return data.get(str(user_id), {}).get('language', 'en')
    
    def set_user_language(self, user_id: int, language: str):
        """Set user language preference"""
        with open(self.settings_file, 'r') as f:
            data = json.load(f)
        
        if str(user_id) not in data:
            data[str(user_id)] = {}
        
        data[str(user_id)]['language'] = language
        
        with open(self.settings_file, 'w') as f:
            json.dump(data, f, indent=2)
    
    def get_queue(self) -> List[Dict[str, Any]]:
        """Get processing queue"""
        with open(self.queue_file, 'r') as f:
            data = json.load(f)
            return data.get('queue', [])
    
    def add_to_queue(self, item: Dict[str, Any]):
        """Add item to processing queue"""
        with open(self.queue_file, 'r') as f:
            data = json.load(f)
        
        if 'queue' not in data:
            data['queue'] = []
        
        data['queue'].append(item)
        
        with open(self.queue_file, 'w') as f:
            json.dump(data, f, indent=2)
    
    def remove_from_queue(self, index: int):
        """Remove item from queue"""
        with open(self.queue_file, 'r') as f:
            data = json.load(f)
        
        if 'queue' in data and len(data['queue']) > index:
            del data['queue'][index]
        
        with open(self.queue_file, 'w') as f:
            json.dump(data, f, indent=2)
    
    def clear_queue(self):
        """Clear the entire queue"""
        with open(self.queue_file, 'w') as f:
            json.dump({'queue': []}, f, indent=2)

db = Database()
