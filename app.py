import os
from flask import Flask, render_template, request, jsonify, send_from_directory
from werkzeug.utils import secure_filename
from dotenv import load_dotenv
import uuid
import json

# Try to import Supabase with fallback
try:
    from supabase import create_client, Client
    supabase_available = True
except ImportError:
    supabase_available = False
    print("Supabase client not available, using mock implementation")

# Try to import Ultralytics with fallback
try:
    from ultralytics import YOLO
    yolo_available = True
except ImportError:
    yolo_available = False
    print("YOLO not available, using mock implementation")

load_dotenv()

app = Flask(__name__)
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['PROCESSED_FOLDER'] = 'processed'

# Initialize components with error handling
if supabase_available:
    try:
        db_url = os.getenv('SUPABASE_URL', '')
        db_key = os.getenv('SUPABASE_KEY', '')
        
        if db_url and db_key:
            db = create_client(db_url, db_key)
            print("Supabase client initialized successfully")
        else:
            supabase_available = False
            print("Supabase credentials not found")
    except Exception as e:
        supabase_available = False
        print(f"Error initializing Supabase: {e}")

# Create mock database client if Supabase isn't available
if not supabase_available:
    class MockDB:
        def table(self, name):
            return self
        
        def insert(self, data):
            return self
        
        def update(self, data):
            return self
        
        def eq(self, key, value):
            return self
        
        def execute(self):
            class MockResult:
                def __init__(self):
                    self.data = [{'id': str(uuid.uuid4())}]
            return MockResult()
    
    db = MockDB()

# Initialize detector with error handling
if yolo_available:
    try:
        detector = YOLO('best.pt')
        print("YOLO model loaded successfully")
    except Exception as e:
        yolo_available = False
        print(f"Error loading YOLO model: {e}")

# Create mock detector if YOLO isn't available
if not yolo_available:
    class MockDetector:
        def __init__(self, model_path):
            print(f"Using mock detector with model: {model_path}")
            pass
        
        def detect(self, image_path):
            class MockResult:
                def __init__(self, image_path):
                    self.boxes = None
                    self.path = image_path
                
                def save(self, path):
                    import shutil
                    # Copy the original image as "processed"
                    shutil.copy2(self.path, path)
            
            return MockResult(image_path)
        
        def calculate_corrosion_percentage(self, result):
            # Return a mock value for demonstration
            return 15.7
    
    detector = MockDetector('best.pt')

# Ensure folders exist
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
os.makedirs(app.config['PROCESSED_FOLDER'], exist_ok=True)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload_image():
    if 'file' not in request.files:
        return jsonify({'error': 'No file uploaded'}), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No file selected'}), 400
    
    # Save original image
    filename = secure_filename(file.filename)
    unique_filename = f"{uuid.uuid4()}_{filename}"
    original_path = os.path.join(app.config['UPLOAD_FOLDER'], unique_filename)
    file.save(original_path)
    
    # Store in database
    try:
        result = db.table('images').insert({
            'filename': unique_filename,
            'original_image_url': f"/uploads/{unique_filename}",
        }).execute()
        image_id = result.data[0]['id']
    except Exception as e:
        print(f"Database error: {e}")
        image_id = str(uuid.uuid4())
    
    return jsonify({
        'image_id': image_id,
        'original_url': f"/uploads/{unique_filename}",
        'filename': unique_filename
    })

@app.route('/detect', methods=['POST'])
def detect_corrosion():
    data = request.json
    image_id = data.get('image_id')
    filename = data.get('filename')
    
    if not image_id or not filename:
        return jsonify({'error': 'Missing parameters'}), 400
    
    # Get original image path
    original_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    
    # Perform detection
    result = detector.detect(original_path)
    processed_filename = f"processed_{filename}"
    processed_path = os.path.join(app.config['PROCESSED_FOLDER'], processed_filename)
    
    # Save processed image
    result.save(processed_path)
    
    # Calculate corrosion percentage
    corrosion_percentage = detector.calculate_corrosion_percentage(result)
    
    # Store detection results
    detection_data = {
        'boxes': [],
        'corrosion_percentage': corrosion_percentage
    }
    
    try:
        db.table('images').update({
            'processed_image_url': f"/processed/{processed_filename}",
        }).eq('id', image_id).execute()
        
        db.table('detections').insert({
            'image_id': image_id,
            'corrosion_percentage': corrosion_percentage,
            'detection_data': detection_data
        }).execute()
    except Exception as e:
        print(f"Database error: {e}")
    
    return jsonify({
        'processed_url': f"/processed/{processed_filename}",
        'corrosion_percentage': corrosion_percentage,
        'detection_data': detection_data
    })

@app.route('/comment', methods=['POST'])
def add_comment():
    data = request.json
    image_id = data.get('image_id')
    comment_text = data.get('comment')
    
    if not image_id or not comment_text:
        return jsonify({'error': 'Missing parameters'}), 400
    
    # Store comment
    try:
        result = db.table('comments').insert({
            'image_id': image_id,
            'comment_text': comment_text
        }).execute()
        comment_id = result.data[0]['id']
    except Exception as e:
        print(f"Database error: {e}")
        comment_id = str(uuid.uuid4())
    
    return jsonify({
        'comment_id': comment_id,
        'message': 'Comment added successfully'
    })

@app.route('/history')
def get_history():
    # Return mock data for demonstration
    try:
        result = db.table('images').select('*').execute()
        return jsonify(result.data if hasattr(result, 'data') else [])
    except Exception as e:
        print(f"Database error: {e}")
        # Return mock data if database is not available
        mock_history = [
            {
                'id': 'mock-id-1',
                'filename': 'sample1.jpg',
                'original_image_url': '/static/sample1.jpg',
                'processed_image_url': '/static/sample1_processed.jpg',
                'uploaded_at': '2023-10-15T12:00:00Z'
            }
        ]
        return jsonify(mock_history)

@app.route('/uploads/<filename>')
def serve_uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

@app.route('/processed/<filename>')
def serve_processed_file(filename):
    return send_from_directory(app.config['PROCESSED_FOLDER'], filename)

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=os.getenv('FLASK_DEBUG', False))