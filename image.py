from flask import Flask, render_template, request, redirect, url_for, flash
import pymysql
import os
from werkzeug.utils import secure_filename
import cv2

# Initialize Flask app
app = Flask(__name__)

# Set a secret key for the session
app.secret_key = b'\x1d\xed\xcf\x13\xe5\xa5\x17\x16\x85\x85\x97\x1e\x9c\xde\x6f\xbb\x2b\x7e\x7e\x6a\xab\xdf\x4c\x56'

# Database configuration
db_config = {
    'host': 'localhost',
    'user': 'root',
    'password': '',
    'database': 'image'  # Change this to your actual database name
}

# Directory for uploaded files
UPLOAD_FOLDER = 'static/uploads'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Ensure the upload folder exists
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

# Function to find the best match for an image
def find_best_match(uploaded_image_path):
    uploaded_img = cv2.imread(uploaded_image_path)
    uploaded_hist = cv2.calcHist([uploaded_img], [0, 1, 2], None, [8, 8, 8], [0, 256, 0, 256, 0, 256])
    uploaded_hist = cv2.normalize(uploaded_hist, uploaded_hist).flatten()

    best_match = None
    min_distance = float('inf')
    similar_images = []

    # Compare with each image in the dataset
    DATASET_FOLDER = 'static/dataset'  # Dataset folder path (ensure it's correct)
    for img_name in os.listdir(DATASET_FOLDER):
        dataset_img_path = os.path.join(DATASET_FOLDER, img_name)
        dataset_img = cv2.imread(dataset_img_path)

        # Compute color histogram for dataset image
        dataset_hist = cv2.calcHist([dataset_img], [0, 1, 2], None, [8, 8, 8], [0, 256, 0, 256, 0, 256])
        dataset_hist = cv2.normalize(dataset_hist, dataset_hist).flatten()

        # Compute chi-squared distance
        distance = cv2.compareHist(uploaded_hist, dataset_hist, cv2.HISTCMP_CHISQR)

        # Track the closest match
        if distance < min_distance:
            min_distance = distance
            best_match = img_name

        # Store distances for similar images
        similar_images.append((img_name, distance))

    # Sort similar images based on distance
    similar_images.sort(key=lambda x: x[1])

    return {
        "best_match": best_match,
        "similar_images": [img[0] for img in similar_images[:3]]
    }

# Home route
@app.route('/')
def home():
    return render_template('index.html')

# About route
@app.route('/about')
def about():
    return render_template('about.html')

# Course route
@app.route('/course')
def course():
    return render_template('course.html')

# Contact route
@app.route('/contact', methods=['GET', 'POST'])
def contact():
    if request.method == 'POST':
        # Get form data
        name = request.form['name']
        email = request.form['email']
        subject = request.form['subject']
        message = request.form['message']

        try:
            # Connect to the database
            conn = pymysql.connect(**db_config)
            cursor = conn.cursor()
            # Insert the form data into the database
            query = "INSERT INTO contact (name, email, subject, message) VALUES (%s, %s, %s, %s)"
            cursor.execute(query, (name, email, subject, message))
            conn.commit()
            flash('Message sent successfully!', 'success')
        except Exception as e:
            flash(f'Error: {str(e)}', 'danger')
        finally:
            conn.close()

        return redirect(url_for('contact'))
    return render_template('contact.html')

# Blog route (Image Upload)
@app.route('/blog', methods=['GET', 'POST'])
def blog():
    if request.method == 'POST':
        # Get the uploaded file
        file = request.files['file']
        if file:
            # Secure and save the file
            filename = secure_filename(file.filename)
            file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(file_path)

            flash('Image uploaded successfully!', 'success')

            # Find best match for the uploaded image
            match_result = find_best_match(file_path)
            best_match = match_result['best_match']

            # Get the name from the best match
            res_name = best_match[:-7].lower()  # Normalize name for matching

            # Route templates based on res_name
            templates = {
                'taj_mahal': 'taj_mahal.html',
                'qutub_minar': 'qutub_minar.html',
                'mysore_palace': 'mysore_palace.html',
                'jantar_mantar': 'jantar_mantar.html',
                'hawa_mahal': 'hawa_mahal.html',
                'red_fort': 'red_fort.html',
                'gateway': 'gatway_of_india.html',
                'lotus_temple': 'lotus_temple.html',
                'virupaksha': 'virupaksha_temple.html',
                'gol_gumbaz': 'gol_gumbaz.html',
                'golden_temple': 'golden_temple.html',
                'jama_masjid': 'jamma_masjid.html'
            }

            if res_name in templates:
                return render_template(templates[res_name])
            else:
                return render_template('image.html')

    return render_template('blog.html')

# Run the Flask app
if __name__ == '__main__':
    app.run(debug=True)
