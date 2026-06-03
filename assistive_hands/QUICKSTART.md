# Quick Start Guide - AssistiveHands

## 🚀 Get Started in 5 Minutes

### Prerequisites
- Python 3.11.2+
- Webcam
- Modern web browser

### Step 1: Install Dependencies (2 min)

```bash
cd assistive_hands
pip install -r requirements.txt
```

### Step 2: Start the Application (1 min)

```bash
python app.py
```

Expected output:
```
INFO:__main__:Initializing AssistiveHands system...
INFO:__main__:System initialization complete
INFO:__main__:Starting Flask server on 127.0.0.1:5000
```

### Step 3: Open in Browser (30 sec)

Open your browser and navigate to:
```
http://127.0.0.1:5000
```

### Step 4: Complete Setup Wizard (1.5 min)

1. Enter your name and select accessibility settings
2. Position camera at eye level
3. Complete 9-point calibration
4. Start using the interface!

## 📖 First Time Use

### Dashboard
- See real-time gaze tracking
- Monitor system status
- Access main features

### Communication Interface
- Type messages using gaze-controlled keyboard
- Use quick phrases for fast communication
- Enable text-to-speech

### Calibration
- Run whenever accuracy decreases
- Takes ~2 minutes
- Follow on-screen instructions

## ⚙️ Key Settings

Adjust in `/config/settings.py`:

```python
# Make selection faster
DWELL_TIME = 0.7  # was 1.0

# Smoother tracking
GAZE_SMOOTHING_WINDOW = 7  # was 5

# More sensitive
GAZE_KALMAN_MEASUREMENT_VARIANCE = 2.0  # was 4.0
```

## 🔧 Common Issues

| Issue | Solution |
|-------|----------|
| Camera not detected | Check permissions, try different device |
| Face not detected | Improve lighting, position camera at eye level |
| Inaccurate gaze | Recalibrate, reduce head movement |
| Slow performance | Reduce resolution, enable performance mode |

## 📱 Browser Compatibility

| Browser | Status |
|---------|--------|
| Chrome/Edge | ✅ Recommended |
| Firefox | ✅ Supported |
| Safari | ✅ Supported |
| Opera | ✅ Supported |

## 🎓 Educational Use

Perfect for demonstrating:
- Computer vision techniques
- Real-time signal processing
- Web-based accessibility solutions
- Human-computer interaction

## 📞 Need Help?

1. Check [README.md](README.md) for detailed documentation
2. Review troubleshooting section
3. Check application logs in `logs/assistive_hands.log`
4. Refer to inline code comments for technical details

## 💡 Pro Tips

1. **Best Lighting**: Diffuse, front-facing light without glare
2. **Optimal Distance**: 2-3 feet from camera
3. **Head Position**: Keep head relatively still during calibration
4. **Frequent Calibration**: Calibrate when accuracy drops
5. **Dwell Time**: Lower = faster response, Higher = less accidental selections

## 🎯 Next Steps

After initial setup:
1. Customize settings for your preferences
2. Save calibration profile
3. Practice with text entry
4. Explore all features

---

**Ready?** Run `python app.py` and start!
