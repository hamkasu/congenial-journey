# utils/database.py
from supabase import create_client, Client
import json

class SupabaseDB:
    def __init__(self, supabase_url: str, supabase_key: str):
        self.supabase: Client = create_client(supabase_url, supabase_key)
    
    def insert_image(self, filename: str, original_url: str):
        data = {
            'filename': filename,
            'original_image_url': original_url
        }
        result = self.supabase.table('images').insert(data).execute()
        return result.data[0]['id'] if result.data else None
    
    def update_image_processed(self, image_id: str, processed_url: str):
        self.supabase.table('images').update({
            'processed_image_url': processed_url
        }).eq('id', image_id).execute()
    
    def insert_detection(self, image_id: str, corrosion_percentage: float, detection_data: dict):
        data = {
            'image_id': image_id,
            'corrosion_percentage': corrosion_percentage,
            'detection_data': detection_data
        }
        result = self.supabase.table('detections').insert(data).execute()
        return result.data[0]['id'] if result.data else None
    
    def insert_comment(self, image_id: str, comment_text: str):
        data = {
            'image_id': image_id,
            'comment_text': comment_text
        }
        result = self.supabase.table('comments').insert(data).execute()
        return result.data[0]['id'] if result.data else None
    
    def get_all_images(self):
        result = self.supabase.table('images').select('*').order('uploaded_at', desc=True).execute()
        return result.data if result.data else []
    
    def get_image_detections(self, image_id: str):
        result = self.supabase.table('detections').select('*').eq('image_id', image_id).execute()
        return result.data if result.data else []
    
    def get_image_comments(self, image_id: str):
        result = self.supabase.table('comments').select('*').eq('image_id', image_id).order('created_at').execute()
        return result.data if result.data else []