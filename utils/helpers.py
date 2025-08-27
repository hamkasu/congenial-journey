# utils/helpers.py
from supabase import create_client, Client
import os
from datetime import datetime, timedelta

def save_image(image_path: str, storage_path: str):
    supabase_url = os.getenv('SUPABASE_URL')
    supabase_key = os.getenv('SUPABASE_KEY')
    supabase: Client = create_client(supabase_url, supabase_key)
    
    with open(image_path, 'rb') as f:
        supabase.storage.from_('corrosion-images').upload(
            file=f.read(),
            path=storage_path,
            file_options={"content-type": "image/jpeg"}
        )
    
    return generate_presigned_url(storage_path)

def generate_presigned_url(storage_path: str):
    supabase_url = os.getenv('SUPABASE_URL')
    supabase_key = os.getenv('SUPABASE_KEY')
    supabase: Client = create_client(supabase_url, supabase_key)
    
    # Generate signed URL that's valid for 1 hour
    expiration = int((datetime.now() + timedelta(hours=1)).timestamp())
    
    response = supabase.storage.from_('corrosion-images').create_signed_url(
        storage_path, expiration
    )
    
    return response.signed_url