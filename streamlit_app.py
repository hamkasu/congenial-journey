# streamlit_app.py
import streamlit as st
import pandas as pd
import numpy as np
from PIL import Image
import tempfile
import os
import uuid
from datetime import datetime

# Try to import your corrosion detection components
try:
    from utils.detection import CorrosionDetector
    from utils.database import SupabaseDB
    from utils.helpers import save_image, generate_presigned_url
except ImportError:
    st.warning("Some components couldn't be imported. Using mock implementations.")
    
    # Mock implementations
    class CorrosionDetector:
        def __init__(self, model_path):
            pass
        
        def detect(self, image_path):
            class MockResult:
                def __init__(self):
                    self.boxes = None
                    self.path = image_path
                
                def save(self, path):
                    import shutil
                    shutil.copy2(self.path, path)
            
            return MockResult()
        
        def calculate_corrosion_percentage(self, result):
            return 15.7  # Mock value
    
    class SupabaseDB:
        def __init__(self, supabase_url, supabase_key):
            pass
        
        def insert_image(self, filename, original_url):
            return str(uuid.uuid4())
        
        def update_image_processed(self, image_id, processed_url):
            pass
        
        def insert_detection(self, image_id, corrosion_percentage, detection_data):
            pass
        
        def insert_comment(self, image_id, comment_text):
            return str(uuid.uuid4())
        
        def get_all_images(self):
            return [
                {
                    'id': 'mock-1',
                    'filename': 'sample1.jpg',
                    'original_image_url': 'https://placehold.co/600x400?text=Sample+1',
                    'processed_image_url': 'https://placehold.co/600x400?text=Processed+1',
                    'uploaded_at': '2023-10-15T12:00:00Z',
                    'corrosion_percentage': 12.5
                },
                {
                    'id': 'mock-2',
                    'filename': 'sample2.jpg',
                    'original_image_url': 'https://placehold.co/600x400?text=Sample+2',
                    'processed_image_url': 'https://placehold.co/600x400?text=Processed+2',
                    'uploaded_at': '2023-10-14T10:30:00Z',
                    'corrosion_percentage': 8.3
                }
            ]
        
        def get_image_comments(self, image_id):
            return [
                {
                    'id': 'comment-1',
                    'comment_text': 'This is a sample comment',
                    'created_at': '2023-10-15T12:30:00Z'
                }
            ]

# Initialize components
@st.cache_resource
def load_detector():
    try:
        return CorrosionDetector('best.pt')
    except:
        return CorrosionDetector('best.pt')  # This will use the mock

@st.cache_resource
def load_database():
    try:
        supabase_url = st.secrets.get("SUPABASE_URL", os.environ.get("SUPABASE_URL", ""))
        supabase_key = st.secrets.get("SUPABASE_KEY", os.environ.get("SUPABASE_KEY", ""))
        return SupabaseDB(supabase_url, supabase_key)
    except:
        return SupabaseDB("", "")  # This will use the mock

detector = load_detector()
db = load_database()

# Streamlit app layout
st.set_page_config(
    page_title="Corrosion AI Detector",
    page_icon="🔍",
    layout="wide"
)

st.title("🔍 Corrosion AI Detection")
st.markdown("Upload an image to detect corrosion and analyze results")

# Sidebar for navigation
st.sidebar.title("Navigation")
app_mode = st.sidebar.selectbox("Choose a page", 
                               ["Upload Image", "View History", "Analysis Dashboard"])

if app_mode == "Upload Image":
    st.header("Upload and Analyze Image")
    
    uploaded_file = st.file_uploader("Choose an image...", type=["jpg", "jpeg", "png"])
    
    if uploaded_file is not None:
        # Display original image
        image = Image.open(uploaded_file)
        st.image(image, caption="Original Image", use_column_width=True)
        
        # Save uploaded file temporarily
        with tempfile.NamedTemporaryFile(delete=False, suffix=".jpg") as tmp_file:
            image.save(tmp_file.name)
            tmp_path = tmp_file.name
        
        # Process image when button is clicked
        if st.button("Detect Corrosion"):
            with st.spinner("Analyzing image for corrosion..."):
                # Perform detection
                result = detector.detect(tmp_path)
                
                # Save processed image temporarily
                processed_filename = f"processed_{uploaded_file.name}"
                processed_path = os.path.join("processed", processed_filename)
                os.makedirs("processed", exist_ok=True)
                result.save(processed_path)
                
                # Calculate corrosion percentage
                corrosion_percentage = detector.calculate_corrosion_percentage(result)
                
                # Display results
                st.success(f"Analysis complete! Corrosion detected: {corrosion_percentage:.2f}%")
                
                col1, col2 = st.columns(2)
                
                with col1:
                    st.image(tmp_path, caption="Original Image", use_column_width=True)
                
                with col2:
                    st.image(processed_path, caption="Processed Image with Detection", use_column_width=True)
                
                # Display metrics
                st.metric("Corrosion Percentage", f"{corrosion_percentage:.2f}%")
                
                # Save to database (if available)
                try:
                    image_id = db.insert_image(uploaded_file.name, tmp_path)
                    db.update_image_processed(image_id, processed_path)
                    db.insert_detection(image_id, corrosion_percentage, {"percentage": corrosion_percentage})
                    
                    st.success("Results saved to database!")
                except Exception as e:
                    st.warning(f"Could not save to database: {str(e)}")
                
                # Comment section
                st.subheader("Add Comment")
                comment = st.text_area("Enter your comments about this detection")
                
                if st.button("Save Comment") and comment:
                    try:
                        db.insert_comment(image_id, comment)
                        st.success("Comment saved!")
                    except Exception as e:
                        st.warning(f"Could not save comment: {str(e)}")

elif app_mode == "View History":
    st.header("Detection History")
    
    try:
        history = db.get_all_images()
        
        if history:
            for item in history:
                with st.expander(f"{item['filename']} - {item.get('uploaded_at', 'Unknown date')}"):
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        st.image(item['original_image_url'], 
                                caption="Original Image", 
                                use_column_width=True)
                    
                    with col2:
                        if item.get('processed_image_url'):
                            st.image(item['processed_image_url'], 
                                    caption="Processed Image", 
                                    use_column_width=True)
                    
                    if item.get('corrosion_percentage'):
                        st.metric("Corrosion Percentage", f"{item['corrosion_percentage']:.2f}%")
                    
                    # Show comments
                    try:
                        comments = db.get_image_comments(item['id'])
                        if comments:
                            st.subheader("Comments")
                            for comment in comments:
                                st.text(f"{comment.get('created_at', 'Unknown date')}: {comment['comment_text']}")
                    except:
                        pass
                    
                    # Add new comment
                    new_comment = st.text_input("Add a comment", key=f"comment_{item['id']}")
                    if st.button("Save Comment", key=f"save_{item['id']}") and new_comment:
                        try:
                            db.insert_comment(item['id'], new_comment)
                            st.success("Comment added!")
                            st.rerun()
                        except Exception as e:
                            st.warning(f"Could not save comment: {str(e)}")
        else:
            st.info("No detection history found.")
    except Exception as e:
        st.error(f"Error loading history: {str(e)}")

elif app_mode == "Analysis Dashboard":
    st.header("Corrosion Analysis Dashboard")
    
    try:
        history = db.get_all_images()
        
        if history:
            # Create a dataframe for analysis
            df_data = []
            for item in history:
                if item.get('corrosion_percentage') is not None:
                    df_data.append({
                        'Filename': item['filename'],
                        'Date': item.get('uploaded_at', ''),
                        'Corrosion (%)': item['corrosion_percentage']
                    })
            
            if df_data:
                df = pd.DataFrame(df_data)
                
                # Convert date strings to datetime objects
                try:
                    df['Date'] = pd.to_datetime(df['Date'])
                    df = df.sort_values('Date')
                except:
                    pass
                
                # Show data table
                st.subheader("Detection Data")
                st.dataframe(df)
                
                # Show statistics
                st.subheader("Statistics")
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    st.metric("Total Detections", len(df))
                
                with col2:
                    st.metric("Average Corrosion", f"{df['Corrosion (%)'].mean():.2f}%")
                
                with col3:
                    st.metric("Maximum Corrosion", f"{df['Corrosion (%)'].max():.2f}%")
                
                # Show chart
                st.subheader("Corrosion Over Time")
                if 'Date' in df.columns and not df['Date'].isnull().all():
                    chart_data = df.set_index('Date')['Corrosion (%)']
                    st.line_chart(chart_data)
                else:
                    st.bar_chart(df.set_index('Filename')['Corrosion (%)'])
            else:
                st.info("No corrosion data available for analysis.")
        else:
            st.info("No detection history found.")
    except Exception as e:
        st.error(f"Error loading data for dashboard: {str(e)}")

# Footer
st.sidebar.markdown("---")
st.sidebar.info(
    "This app uses AI to detect corrosion in images. "
    "Upload an image to get started with analysis."
)