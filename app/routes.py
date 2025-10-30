# app/routes.py
import os
import secrets
from PIL import Image
from flask import Blueprint, render_template, redirect, url_for, flash, request, current_app, abort
from flask_login import current_user, login_user, logout_user, login_required
from .models import db, User, Investigation, Report, ThreadFeedItem, Capture
from .forms import SignUpForm, LoginForm, UpdateProfileForm, NewInvestigationForm, EditInvestigationForm
from collections import defaultdict,  OrderedDict
from datetime import datetime, date, timedelta
# THIS IS THE ONLY LINE THAT WAS CHANGED
from sqlalchemy import func, case 
import json
import base64
from flask import jsonify
import re
import app.analysis_utils as analysis_utils
import asyncio
import sounddevice as sd
import numpy as np
import scipy.io.wavfile as wav
import tempfile
from groq import Groq
import edge_tts
import pytz
IST = pytz.timezone("Asia/Kolkata")

main = Blueprint('main', __name__)

# --- Context Processor ---
@main.app_context_processor
def inject_forms():
    return dict(
        new_investigation_form=NewInvestigationForm(),
        edit_investigation_form=EditInvestigationForm()
    )

# --- Helper Function for Saving Picture ---
def save_picture(form_picture):
    random_hex = secrets.token_hex(8)
    _, f_ext = os.path.splitext(form_picture.filename)
    picture_fn = random_hex + f_ext
    upload_path = os.path.join(current_app.root_path, 'static/profile_pics')
    picture_path = os.path.join(upload_path, picture_fn)
    output_size = (150, 150)
    i = Image.open(form_picture)
    i.thumbnail(output_size)
    i.save(picture_path)
    return picture_fn

# --- AI Assistant Configuration (can be placed before your 'main' blueprint) ---
try:
    groq_client = Groq(api_key=os.environ.get("GROQ_API_KEY"))
except Exception as e:
    groq_client = None
    print(f"Warning: Groq client could not be initialized. AI Assistant will not work. Error: {e}")

# --- AI Assistant Helper Functions ---
def transcribe_audio_from_file(path):
    if not groq_client:
        return "AI client not initialized."
    with open(path, "rb") as f:
        transcription = groq_client.audio.transcriptions.create(
            model="whisper-large-v3",
            file=(os.path.basename(path), f.read())
        )
    return transcription.text.strip()

def get_ai_response_from_text(user_text, history):
    if not groq_client:
        return "AI client not initialized."
    messages = history + [{"role": "user", "content": user_text}]
    completion = groq_client.chat.completions.create(
        model="llama-3.1-8b-instant",
        messages=messages,
        temperature=0.3
    )
    return completion.choices[0].message.content.strip()

async def generate_speech_from_text(text):
    # ADD THIS CHECK AT THE BEGINNING OF THE FUNCTION
    if not text or not text.strip():
        return "" # Return empty string if there is no text to speak

    tmp_file = ""
    try:
        tmp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".mp3").name
        lang = "hi-IN" if any("\u0900" <= c <= "\u097F" for c in text) else "en-IN"
        voice = "hi-IN-MadhurNeural" if lang == "hi-IN" else "en-IN-NeerjaNeural"
        
        communicate = edge_tts.Communicate(text, voice=voice)
        await communicate.save(tmp_file)
        
        with open(tmp_file, 'rb') as f:
            audio_data = f.read()
        
        return base64.b64encode(audio_data).decode('utf-8')
    finally:
        if tmp_file and os.path.exists(tmp_file):
            os.remove(tmp_file)
    
# --- Authentication Routes ---
@main.route('/signup', methods=['GET', 'POST'])
def signup():
    if current_user.is_authenticated:
        return redirect(url_for('main.home'))
    form = SignUpForm()
    if form.validate_on_submit():
        user = User(username=form.username.data, email=form.email.data)
        user.set_password(form.password.data)
        db.session.add(user)
        db.session.commit()
        flash('Your account has been created! You can now log in.', 'success')
        return redirect(url_for('main.login'))
    return render_template('signup.html', title='Sign Up', form=form)

@main.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('main.home'))
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user and user.check_password(form.password.data):
            login_user(user, remember=form.remember.data)
            next_page = request.args.get('next')
            return redirect(next_page) if next_page else redirect(url_for('main.home'))
        else:
            flash('Login Unsuccessful. Please check email and password.', 'danger')
    return render_template('login.html', title='Login', form=form)

@main.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('main.login'))

# --- Dashboard & Page Routes ---
@main.route('/')
@login_required
def home():
    active_investigations = Investigation.query.filter_by(author=current_user).order_by(Investigation.timestamp.desc()).limit(6).all()
    total_investigations_count = Investigation.query.filter_by(author=current_user).count()
    recent_reports = Report.query.filter_by(author=current_user).limit(4).all()
    thread_feed = ThreadFeedItem.query.order_by(ThreadFeedItem.timestamp.desc()).limit(5).all()
    return render_template('home.html', 
                           active_page='home',
                           investigations=active_investigations,
                           total_investigations_count=total_investigations_count,
                           reports=recent_reports,
                           feed_items=thread_feed)

@main.route('/investigations')
@login_required
def investigations():
    all_investigations = (
        Investigation.query.filter_by(author=current_user)
        .order_by(Investigation.timestamp.desc())
        .all()
    )

    grouped_investigations = defaultdict(list)

    # 1. Fill groups
    for inv in all_investigations:
        # Ensure conversion before grouping
        local_time = inv.timestamp.astimezone(IST)
        date_key = local_time.date()
        grouped_investigations[date_key].append(inv)

    # 2. Sort after filling
    sorted_grouped_investigations = OrderedDict(
        sorted(grouped_investigations.items(), key=lambda x: x[0], reverse=True)
    )

    return render_template(
        'investigations.html',
        active_page='investigations',
        grouped_investigations=sorted_grouped_investigations
    )


@main.route('/reports')
@login_required
def reports():
    # --- Card Counts (No changes) ---
    total_count = Investigation.query.filter_by(author=current_user).count()
    live_count = Investigation.query.filter_by(author=current_user, status='Live').count()
    ongoing_count = Investigation.query.filter_by(author=current_user, status='Pending').count()
    completed_count = Investigation.query.filter_by(author=current_user, status='Completed').count()

    # ===== START: NEW CHART 1 LOGIC =====
    
    # 1. Prepare the date range for the last 7 days
    today = date.today()
    seven_days_ago = today - timedelta(days=6)
    
    # Create an ordered dictionary to hold data for each of the last 7 days, initialized to zero
    daily_stats = OrderedDict()
    for i in range(7):
        current_day = seven_days_ago + timedelta(days=i)
        # Use weekday abbreviation ('Mon', 'Tue', etc.) as the key
        day_key = current_day.strftime('%a') 
        daily_stats[day_key] = {'total': 0, 'completed': 0}

    # 2. Query the database for investigations in the last 7 days
    recent_investigations = db.session.query(
        Investigation.timestamp,
        Investigation.status
    ).filter(
        Investigation.author == current_user,
        func.date(Investigation.timestamp) >= seven_days_ago
    ).all()

    # 3. Populate the dictionary with real data from the query
    for timestamp, status in recent_investigations:
        day_key = timestamp.strftime('%a')
        if day_key in daily_stats:
            daily_stats[day_key]['total'] += 1
            if status == 'Completed':
                daily_stats[day_key]['completed'] += 1

    # 4. Extract the labels and data for the chart
    chart1_labels = list(daily_stats.keys())
    chart1_total_data = [day['total'] for day in daily_stats.values()]
    chart1_completed_data = [day['completed'] for day in daily_stats.values()]
    
    # ===== END: NEW CHART 1 LOGIC =====

    # ===== START: MODIFIED SLIDER QUERY =====
    # Query for the investigation cards and include the count of captures for each
    report_investigations_query = db.session.query(
        Investigation, 
        func.count(Capture.id).label('capture_count')
    ).outerjoin(Capture).filter(
        Investigation.author == current_user
    ).group_by(Investigation.id).order_by(Investigation.timestamp.desc()).all()
    
    # Process the query results into a more usable format
    report_investigations = []
    for inv, count in report_investigations_query:
        inv.capture_count = count  # Attach the count to the investigation object
        report_investigations.append(inv)
    # ===== END: MODIFIED SLIDER QUERY =====
    
    return render_template('reports.html', 
                           active_page='reports',
                           total_count=total_count,
                           live_count=live_count,
                           ongoing_count=ongoing_count,
                           completed_count=completed_count,
                           chart1_labels=json.dumps(chart1_labels),
                           chart1_total_data=json.dumps(chart1_total_data),
                           chart1_completed_data=json.dumps(chart1_completed_data),
                           report_investigations=report_investigations,
                           datetime=datetime,
                           )

@main.route('/settings')
@login_required
def settings():
    return render_template('settings.html', active_page='settings')

@main.route('/messages')
@login_required
def messages():
    return render_template('messages.html', active_page='messages')

# --- Profile Routes ---
@main.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():
    form = UpdateProfileForm()
    if form.validate_on_submit():
        if form.picture.data:
            picture_file = save_picture(form.picture.data)
            current_user.profile_pic_url = picture_file
        
        current_user.username = form.username.data
        current_user.email = form.email.data
        current_user.first_name = form.first_name.data
        current_user.last_name = form.last_name.data
        current_user.role = form.role.data
        current_user.organization = form.organization.data
        current_user.website_url = form.website_url.data
        current_user.bio = form.bio.data
        db.session.commit()
        flash('Your profile has been updated!', 'success')
        return redirect(url_for('main.profile'))
        
    elif request.method == 'GET':
        form.username.data = current_user.username
        form.email.data = current_user.email
        form.first_name.data = current_user.first_name
        form.last_name.data = current_user.last_name
        form.role.data = current_user.role
        form.organization.data = current_user.organization
        form.website_url.data = current_user.website_url
        form.bio.data = current_user.bio
    
    if current_user.profile_pic_url == 'default-profile-pic.png':
        image_file = url_for('static', filename='images/' + current_user.profile_pic_url)
    else:
        image_file = url_for('static', filename='profile_pics/' + current_user.profile_pic_url)
        
    return render_template('profile.html', title='Profile', active_page='profile', form=form, image_file=image_file)

@main.route('/profile/delete', methods=['POST'])
@login_required
def delete_account():
    db.session.delete(current_user)
    db.session.commit()
    logout_user()
    flash('Your account has been permanently deleted.', 'info')
    return redirect(url_for('main.login'))

# --- Create Investigation Route ---
@main.route('/investigation/new', methods=['POST'])
@login_required
def new_investigation():
    form = NewInvestigationForm()
    if form.validate_on_submit():
        investigation = Investigation(
            title=form.title.data,
            location=form.location.data,
            drone_type=form.drone_type.data,
            description=form.description.data,
            author=current_user
        )
        if form.drone_photo.data:
            photo_file = save_picture(form.drone_photo.data) 
            investigation.drone_photo = photo_file
        
        db.session.add(investigation)
        db.session.commit()
        flash('Investigation Established Successfully! Status is now LIVE.', 'success')
    else:
        for field, errors in form.errors.items():
            for error in errors:
                flash(f"Error in {getattr(form, field).label.text}: {error}", 'danger')
    return redirect(url_for('main.home'))



@main.route('/investigation/<int:investigation_id>/delete', methods=['POST'])
@login_required
def delete_investigation(investigation_id):
    inv = Investigation.query.get_or_404(investigation_id)
    if inv.author != current_user:
        abort(403) # Forbidden
    db.session.delete(inv)
    db.session.commit()
    flash('Investigation has been deleted.', 'success')
    return redirect(url_for('main.investigations'))


# =============================================
# START OF UPDATED ROUTE
# =============================================
@main.route('/investigation/<int:investigation_id>/update_status', methods=['POST'])
@login_required
def update_status(investigation_id):
    inv = Investigation.query.get_or_404(investigation_id)
    if inv.author != current_user:
        abort(403)
    
    # This is an extra check we get from the JS to know if we should redirect
    should_go_live = request.form.get('go_live')

    new_status = request.form.get('new_status')
    if new_status:
        inv.status = new_status
        db.session.commit()
        flash(f'Investigation status updated to {new_status}.', 'success')
    
    # If the action was 'Start' or 'Continue', the JS will send 'go_live'.
    # This tells our backend to redirect to the live page.
    if should_go_live:
         return redirect(url_for('main.live_investigation', investigation_id=inv.id))

    # For any other status change (Pause, Complete), go back to the main list.
    return redirect(url_for('main.investigations'))
# =============================================
# END OF UPDATED ROUTE
# =============================================




@main.route('/investigation/<int:investigation_id>/edit', methods=['POST'])
@login_required
def edit_investigation(investigation_id):
    inv = Investigation.query.get_or_404(investigation_id)
    if inv.author != current_user:
        abort(403)
    
    form = EditInvestigationForm() # Use the new edit form
    if form.validate_on_submit():
        inv.title = form.title.data
        inv.location = form.location.data
        inv.description = form.description.data
        if form.drone_photo.data:
            photo_file = save_picture(form.drone_photo.data)
            inv.drone_photo = photo_file
        db.session.commit()
        flash('Investigation details have been updated!', 'success')
    else:
        for field, errors in form.errors.items():
            for error in errors:
                flash(f"Error in {getattr(form, field).label.text}: {error}", 'danger')
                
    return redirect(url_for('main.investigations'))


@main.route('/investigation/<int:investigation_id>/live')
@login_required
def live_investigation(investigation_id):
    inv = Investigation.query.get_or_404(investigation_id)
    if inv.author != current_user: abort(403)
    
    if inv.status != 'Live':
        inv.status = 'Live'
        db.session.commit()

    # ADD THIS LOGIC
    # Fetch the 12 most recent captures for this investigation
    recent_captures = Capture.query.filter_by(investigation_id=inv.id)\
                                   .order_by(Capture.timestamp.desc())\
                                   .limit(12).all()

    # PASS THE CAPTURES TO THE TEMPLATE
    return render_template('live_investigation.html', 
                           investigation=inv, 
                           recent_captures=recent_captures)



@main.route('/investigation/<int:investigation_id>/capture', methods=['POST'])
@login_required
def save_capture(investigation_id):
    inv = Investigation.query.get_or_404(investigation_id)
    if inv.author != current_user:
        abort(403)

    data = request.get_json()
    if not data or 'image_data' not in data:
        return jsonify({'error': 'Missing image data'}), 400

    try:
        image_data = re.sub('^data:image/.+;base64,', '', data['image_data'])
        image_bytes = base64.b64decode(image_data)
    except (TypeError, base64.binascii.Error):
        return jsonify({'error': 'Invalid base64 data'}), 400

    random_hex = secrets.token_hex(16)
    filename = f"{random_hex}.jpg"
    
    captures_dir = os.path.join(current_app.root_path, 'static/captures')
    os.makedirs(captures_dir, exist_ok=True)
    file_path = os.path.join(captures_dir, filename)

    with open(file_path, 'wb') as f:
        f.write(image_bytes)
        
    new_capture = Capture(image_filename=filename, investigation_id=inv.id)
    db.session.add(new_capture)
    db.session.commit()

    image_url = url_for('static', filename=f'captures/{filename}')
    return jsonify({'success': True, 'image_url': image_url})


@main.route('/investigation/<int:investigation_id>/captures', methods=['GET'])
@login_required
def get_captures(investigation_id):
    inv = Investigation.query.get_or_404(investigation_id)
    if inv.author != current_user:
        abort(403)

    captures = Capture.query.filter_by(investigation_id=inv.id).order_by(Capture.timestamp.desc()).all()

    captures_data = [{
        'id': capture.id, # <-- ADDED THIS LINE
        'url': url_for('static', filename=f'captures/{capture.image_filename}'),
        'timestamp': capture.timestamp.strftime('%Y-%m-%d %H:%M:%S')
    } for capture in captures]

    return jsonify(captures_data)


# ================================================
# START: NEW ROUTE FOR CAPTURE ANALYSIS
# ================================================
@main.route('/capture/<int:capture_id>/analyze', methods=['POST'])
@login_required
def analyze_capture(capture_id):
    capture = Capture.query.get_or_404(capture_id)
    investigation = Investigation.query.get_or_404(capture.investigation_id)

    if investigation.author != current_user:
        abort(403) # Ensure user has permission

    # Construct the full path to the image file
    image_path = os.path.join(current_app.root_path, 'static/captures', capture.image_filename)

    if not os.path.exists(image_path):
        return jsonify({"error": "Capture file not found."}), 404

    # Call the analysis function from our utility file
    analysis_results = analysis_utils.analyze_image_from_path(image_path)

    if "error" in analysis_results:
        return jsonify(analysis_results), 500

    # ===== START: NEW CODE TO SAVE ANALYSIS =====
    try:
        # Check if analysis already exists to avoid duplicates
        existing_analysis = AnalysisResult.query.filter_by(capture_id=capture.id).first()
        if not existing_analysis:
            existing_analysis = AnalysisResult(capture_id=capture.id)

        group_stats = analysis_results.get('group_stats', {})
        existing_analysis.male_count = group_stats.get('male_count', 0)
        existing_analysis.female_count = group_stats.get('female_count', 0)
        existing_analysis.panic_score = group_stats.get('panic_score', 0.0)
        
        # Aggregate emotions from individual faces into a dictionary
        emotions = [face.get('emotion_label', 'unknown') for face in analysis_results.get('faces', [])]
        emotion_counts = {emotion: emotions.count(emotion) for emotion in set(emotions) if emotion != 'unknown'}
        existing_analysis.emotion_summary = emotion_counts

        db.session.add(existing_analysis)
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        print(f"Error saving analysis result: {e}")
    # ===== END: NEW CODE TO SAVE ANALYSIS =====

    return jsonify(analysis_results)
# ================================================
# END: NEW ROUTE FOR CAPTURE ANALYSIS
# ================================================

# ===== ADD THIS NEW ROUTE AT THE END OF THE FILE =====
@main.route('/voice-assistant', methods=['POST'])
@login_required
async def voice_assistant():
    if 'audio_data' not in request.files:
        return jsonify({"error": "No audio file part"}), 400
    
    file = request.files['audio_data']
    if file.filename == '':
        return jsonify({"error": "No selected file"}), 400

    history_json = request.form.get('history', '[]')
    history = json.loads(history_json)
    
    # Initialize variables
    user_text = ""
    ai_reply_text = ""
    ai_reply_audio_b64 = ""
    tmp_path = ""

    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as tmp:
            file.save(tmp.name)
            tmp_path = tmp.name
        
        # 1. Transcribe User's Speech
        user_text = transcribe_audio_from_file(tmp_path)
        if not user_text:
            # If no speech is detected, return an empty success response
            return jsonify({"user_text": "", "ai_reply_text": "", "ai_reply_audio": ""})

        # 2. Get AI Text Response
        ai_reply_text = get_ai_response_from_text(user_text, history)

        # 3. Generate AI Speech
        if ai_reply_text: # Only generate speech if there is a reply
             ai_reply_audio_b64 = await generate_speech_from_text(ai_reply_text)
        
        return jsonify({
            "user_text": user_text,
            "ai_reply_text": ai_reply_text,
            "ai_reply_audio": ai_reply_audio_b64
        })
    except Exception as e:
        # Catch any other unexpected errors during the process
        print(f"Error in voice_assistant route: {e}")
        # Return a response that the frontend can handle, but still includes the user's text
        return jsonify({
            "user_text": user_text,
            "ai_reply_text": "Sorry, an error occurred.",
            "ai_reply_audio": "" # Send no audio on error
        }), 500
    finally:
        # Ensure the temp file is always cleaned up
        if tmp_path and os.path.exists(tmp_path):
            os.remove(tmp_path)