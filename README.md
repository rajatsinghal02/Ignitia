# Ignitia - Advanced Drone Investigation Platform

Ignitia is a sophisticated Flask-based web application designed for managing and conducting drone-based investigations. It provides a comprehensive suite of tools for investigators, researchers, and drone operators to manage their investigations, analyze data, and generate reports.

## Features

### Core Functionality

- **Live Investigation Management**: Real-time drone investigation tracking and monitoring
- **AI-Powered Analysis**: Built-in AI assistant with speech recognition and response capabilities
- **Image Capture & Analysis**: Advanced image processing and analysis tools
- **Report Generation**: Comprehensive reporting system for investigation findings
- **User Profile Management**: Detailed user profiles with customizable fields

### Key Components

- **Dashboard**: Overview of active investigations and recent reports
- **Investigation Management**: Create, edit, and track multiple investigations
- **Live Monitoring**: Real-time capture and analysis during active investigations
- **Voice Assistant**: AI-powered voice interaction system
- **Analytical Tools**: Built-in tools for image and data analysis

## Technical Stack

### Backend

- **Framework**: Flask (Python)
- **Database**: SQLAlchemy
- **Authentication**: Flask-Login
- **Form Handling**: Flask-WTF
- **Real-time Communication**: Flask-SocketIO

### Frontend

- **Templating**: Jinja2
- **Styling**: CSS3 with responsive design
- **JavaScript**: Modern JS with async/await support
- **UI Components**: Custom modals and interactive elements

### AI & Analysis

- **Speech Processing**: Edge TTS
- **AI Integration**: Groq API
- **Image Processing**: PIL, OpenCV
- **Audio Processing**: sounddevice, scipy

## Installation

1. Clone the repository:

```bash
git clone https://github.com/770navyasharma/IgnitiaTech.git
cd Ignitia
```

2. Create a virtual environment and activate it:

```bash
python -m venv venv
source venv/bin/activate  # On Windows use: venv\Scripts\activate
```

3. Install required packages:

```bash
pip install -r requirements.txt
```

4. Set up environment variables:

```bash
export GROQ_API_KEY="your_api_key"
# Add other necessary environment variables
```

5. Initialize the database:

```bash
flask db upgrade
```
Also create .env file and load them to your project for better structure.

6. Run the application:

```bash
python run.py
```

## Project Structure

```
Ignitia/
├── app/
│   ├── static/
│   │   ├── css/
│   │   ├── js/
│   │   ├── images/
│   │   └── captures/
│   ├── templates/
│   ├── __init__.py
│   ├── models.py
│   ├── routes.py
│   ├── forms.py
│   └── analysis_utils.py
├── migrations/
├── instance/
├── requirements.txt
├── run.py
└── README.md
```

## Configuration

The application requires several configuration settings:

- Database URI
- Secret key for session management
- API keys for AI services
- File upload configurations
- Timezone settings (default: Asia/Kolkata)

## Usage

1. Create an account using the signup page
2. Set up your profile with relevant information
3. Create new investigations with drone details
4. Use the live investigation feature to capture and analyze data
5. Generate reports based on investigation findings
6. Use the AI assistant for voice-based interaction

## Contributing

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgments

- Flask framework and its extensions
- Groq API for AI capabilities
- Edge TTS for speech synthesis
- All other open-source libraries used in this project

## Support

For support, email support@ignitiatech.com or create an issue in the GitHub repository.
