// static/js/script.js
let currentImageId = null;

async function uploadImage() {
    const fileInput = document.getElementById('imageUpload');
    const file = fileInput.files[0];
    
    if (!file) {
        alert('Please select an image first');
        return;
    }
    
    const formData = new FormData();
    formData.append('file', file);
    
    try {
        const response = await fetch('/upload', {
            method: 'POST',
            body: formData
        });
        
        const data = await response.json();
        
        if (response.ok) {
            currentImageId = data.image_id;
            document.getElementById('originalImage').src = data.original_url;
            
            // Now detect corrosion
            const detectResponse = await fetch('/detect', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    image_id: data.image_id,
                    filename: data.filename
                })
            });
            
            const detectData = await detectResponse.json();
            
            if (detectResponse.ok) {
                document.getElementById('processedImage').src = detectData.processed_url;
                document.getElementById('corrosionPercentage').innerHTML = `
                    <strong>Corrosion Percentage: ${detectData.corrosion_percentage.toFixed(2)}%</strong>
                `;
                
                document.getElementById('processingSection').classList.remove('hidden');
                loadHistory();
            } else {
                alert('Error detecting corrosion: ' + detectData.error);
            }
        } else {
            alert('Error uploading image: ' + data.error);
        }
    } catch (error) {
        console.error('Error:', error);
        alert('An error occurred while uploading the image');
    }
}

async function addComment() {
    const commentText = document.getElementById('commentText').value;
    
    if (!commentText) {
        alert('Please enter a comment');
        return;
    }
    
    try {
        const response = await fetch('/comment', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                image_id: currentImageId,
                comment: commentText
            })
        });
        
        const data = await response.json();
        
        if (response.ok) {
            document.getElementById('commentText').value = '';
            loadComments();
        } else {
            alert('Error adding comment: ' + data.error);
        }
    } catch (error) {
        console.error('Error:', error);
        alert('An error occurred while adding the comment');
    }
}

async function loadComments() {
    if (!currentImageId) return;
    
    try {
        // In a real implementation, you would fetch comments for the current image
        // For simplicity, we'll just reload the history which includes comments
        loadHistory();
    } catch (error) {
        console.error('Error loading comments:', error);
    }
}

async function loadHistory() {
    try {
        const response = await fetch('/history');
        const data = await response.json();
        
        if (response.ok) {
            const historyList = document.getElementById('historyList');
            historyList.innerHTML = '';
            
            data.forEach(item => {
                const historyItem = document.createElement('div');
                historyItem.className = 'history-item';
                
                historyItem.innerHTML = `
                    <img src="${item.original_image_url}" alt="${item.filename}">
                    <div class="history-info">
                        <h3>${item.filename}</h3>
                        <p>Uploaded: ${new Date(item.uploaded_at).toLocaleString()}</p>
                        ${item.processed_image_url ? `
                            <p><strong>Corrosion Detected</strong></p>
                            <img src="${item.processed_image_url}" alt="Processed" style="max-width: 100px;">
                        ` : '<p>Processing...</p>'}
                    </div>
                `;
                
                historyList.appendChild(historyItem);
            });
        }
    } catch (error) {
        console.error('Error loading history:', error);
    }
}

// Load history on page load
document.addEventListener('DOMContentLoaded', loadHistory);