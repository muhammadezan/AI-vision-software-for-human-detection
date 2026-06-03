# AssistiveHands - Project Documentation Index

## 📚 Documentation Overview

Welcome to AssistiveHands! This document serves as your guide to all available documentation.

## 🚀 Getting Started

### New Users - Start Here!

1. **[QUICKSTART.md](QUICKSTART.md)** ⭐ *5-minute setup*
   - Quick installation
   - Running the app
   - First-time use guide
   - Quick troubleshooting

2. **[README.md](README.md)** - *Complete project guide*
   - Feature overview
   - Installation instructions
   - System requirements
   - Usage guide
   - API reference
   - Troubleshooting

## 📖 Detailed Guides

### Installation & Setup

- **[INSTALLATION.md](INSTALLATION.md)** - *Comprehensive installation guide*
  - Step-by-step installation
  - System requirements
  - Detailed troubleshooting
  - Performance tuning
  - Testing procedures
  - Network setup

### Deployment

- **[DEPLOYMENT.md](DEPLOYMENT.md)** - *Production deployment guide*
  - Local development setup
  - Network deployment
  - Docker deployment
  - Cloud deployment (AWS, Azure, Heroku)
  - Production configuration
  - Security hardening
  - Monitoring and logging
  - Backup strategies

### Project Overview

- **[PROJECT_SUMMARY.md](PROJECT_SUMMARY.md)** - *Complete project summary*
  - What's been created
  - Project structure
  - Key features
  - Code statistics
  - Technology stack
  - Next steps

## 🔍 Navigation by Use Case

### I want to...

#### Set up and run AssistiveHands
→ [QUICKSTART.md](QUICKSTART.md)

#### Understand the system
→ [README.md](README.md) → System Overview section

#### Fix a problem
→ [INSTALLATION.md](INSTALLATION.md) → Troubleshooting section

#### Install on a server
→ [DEPLOYMENT.md](DEPLOYMENT.md)

#### Customize settings
→ [README.md](README.md) → Configuration section

#### Access the API
→ [README.md](README.md) → API Endpoints section

#### Deploy to production
→ [DEPLOYMENT.md](DEPLOYMENT.md) → Production Configuration section

#### Monitor performance
→ [DEPLOYMENT.md](DEPLOYMENT.md) → Monitoring & Logging section

## 📁 Project Structure

```
assistive_hands/
├── 📄 QUICKSTART.md           ← Start here!
├── 📄 README.md               ← Main documentation
├── 📄 INSTALLATION.md         ← Setup & troubleshooting
├── 📄 DEPLOYMENT.md           ← Production deployment
├── 📄 PROJECT_SUMMARY.md      ← Project overview
├── 📄 INDEX.md                ← You are here
│
├── app.py                     ← Main Flask app
├── camera_stream.py           ← Video streaming
├── requirements.txt           ← Dependencies
│
├── camera/                    ← Face detection & eye tracking
├── calibration/               ← Calibration system
├── utils/                     ← Signal processing & events
├── config/                    ← System configuration
├── ui/                        ← Frontend (HTML/CSS/JS)
├── data/                      ← User data directory
├── logs/                      ← Application logs
└── docs/                      ← Additional documentation
```

## 🎯 Quick Reference

### Installation Commands

```bash
# Clone/navigate to project
cd assistive_hands

# Create virtual environment
python -m venv venv

# Activate virtual environment
# Windows:
venv\Scripts\activate
# macOS/Linux:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Run application
python app.py

# Open in browser
http://127.0.0.1:5000
```

### Key Configuration Files

- **[config/settings.py](config/settings.py)** - System settings
- **[requirements.txt](requirements.txt)** - Python dependencies
- **[app.py](app.py)** - Flask configuration

### API Endpoints Summary

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/` | GET | Dashboard |
| `/calibration` | GET | Calibration page |
| `/communication` | GET | Text input page |
| `/api/camera/start` | POST | Start camera |
| `/api/camera/stop` | POST | Stop camera |
| `/api/camera/feed` | GET | Video stream |
| `/api/gaze/current` | GET | Current gaze position |
| `/api/calibration/start` | POST | Start calibration |
| `/api/calibration/point` | POST | Submit calibration point |
| `/api/calibration/calculate` | POST | Calculate calibration |
| `/api/gesture/detect` | GET | Detect gestures |
| `/api/settings/get` | GET | Get settings |
| `/api/settings/update` | POST | Update settings |
| `/api/status` | GET | System status |

See [README.md](README.md) for detailed endpoint documentation.

## 🛠 Technology Stack

**Backend:**
- Python 3.11.2
- Flask 3.0.0
- OpenCV 4.8.1.78
- MediaPipe 0.10.3

**Frontend:**
- HTML5 / CSS3
- JavaScript ES6+
- Bootstrap 5

## 📊 Project Statistics

- **Total Code**: 7,350+ lines
- **Python Files**: 10
- **Frontend Files**: 12
- **Documentation**: 1,500+ lines
- **Features**: 50+

## 🎓 Academic Use

Perfect for:
- Final Year Projects (FYP)
- Capstone projects
- Computer vision courses
- Human-computer interaction (HCI)
- Accessibility research

## ❓ Common Questions

### Q: How do I get started?
**A:** Start with [QUICKSTART.md](QUICKSTART.md) for a 5-minute setup.

### Q: What if something doesn't work?
**A:** Check [INSTALLATION.md](INSTALLATION.md) troubleshooting section.

### Q: How do I deploy to production?
**A:** See [DEPLOYMENT.md](DEPLOYMENT.md) for detailed instructions.

### Q: How do I customize the system?
**A:** Edit `config/settings.py` and see [README.md](README.md) configuration section.

### Q: Where are the API docs?
**A:** See [README.md](README.md) API Endpoints section.

### Q: How do I improve accuracy?
**A:** See [README.md](README.md) troubleshooting or [INSTALLATION.md](INSTALLATION.md).

## 📞 Support Resources

1. **Documentation**: Read the relevant guide for your use case
2. **Logs**: Check `logs/assistive_hands.log` for errors
3. **Code Comments**: Inline comments explain complex functionality
4. **API Tests**: Test endpoints with provided Flask routes
5. **Configuration**: Adjust `config/settings.py` for your needs

## 🔗 Related Files

### Core Application
- [app.py](app.py) - Main Flask application
- [camera_stream.py](camera_stream.py) - Video streaming

### Modules
- [camera/](camera/) - Face detection & eye tracking
- [calibration/](calibration/) - Calibration system
- [utils/](utils/) - Signal processing & events
- [config/](config/) - Configuration settings
- [ui/](ui/) - Frontend templates and assets

## 📋 Checklist for First-Time Setup

- [ ] Read QUICKSTART.md (5 min)
- [ ] Install Python 3.11.2+
- [ ] Clone/navigate to project
- [ ] Create virtual environment
- [ ] Install requirements: `pip install -r requirements.txt`
- [ ] Run app: `python app.py`
- [ ] Open browser: `http://127.0.0.1:5000`
- [ ] Complete setup wizard
- [ ] Perform calibration
- [ ] Test text input interface
- [ ] Review README.md for full features

## 🎉 You're Ready!

Everything is set up. Choose your next step:

1. **Get Started Now** → [QUICKSTART.md](QUICKSTART.md)
2. **Learn More** → [README.md](README.md)
3. **Troubleshoot** → [INSTALLATION.md](INSTALLATION.md)
4. **Deploy** → [DEPLOYMENT.md](DEPLOYMENT.md)

---

**Last Updated**: December 28, 2025
**Version**: 1.0.0
**Status**: ✅ Ready for Use

For questions or issues, consult the relevant documentation above.
