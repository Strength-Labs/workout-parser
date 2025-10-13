# Turnkey Coach Tools

A comprehensive toolkit for fitness coaches using the Turnkey Coach platform. Streamline client management, workout analysis, nutrition tracking, and AI-powered programming through an intuitive terminal-based application.

## 🚀 Quick Install for Coaches

### 🍎 **macOS Installation**

1. **Download**: `TurnkeyCoachTools-1.4.0-WithIcon.dmg` from [GitHub Releases](https://github.com/your-org/workout-parser/releases)
2. **Install**: 
   - Click the DMG file
   - Drag the app to Applications folder
   - Admire the beautiful icon! 🎨

3. **⚠️ Security Warning (Expected!)**
   
   **macOS will show a security warning** - this is normal! The app is completely safe.
   
   **Quick Fix:**
   - Try to open the app (it gets blocked)
   - **Right-click** the app → **"Open"**
   - Click **"Open"** in the security dialog
   
   **OR:**
   - Apple menu → **System Settings** → **Privacy & Security**
   - Look for the blocked app message
   - Click **"Open Anyway"**

4. **🎉 You're Ready!** 
   - App launches in Terminal
   - Login with your Turnkey Coach credentials
   - Select a client and start coaching!

---

### 🪟 **Windows Installation**

1. **Download**: `TurnkeyCoachTools-1.4.0-Setup.exe` from [GitHub Releases](https://github.com/your-org/workout-parser/releases)

2. **⚠️ Security Warning (Expected!)**
   
   **Windows will show "Windows protected your PC"** - this is normal!
   
   **Quick Fix:**
   - Click **"More info"** 
   - Click **"Run anyway"**
   - Follow the installation wizard

3. **🎉 You're Ready!**
   - Launch from Start Menu
   - App opens in Command Prompt
   - Login and start coaching!

---

### 🐧 **Linux**
See [Developer Installation](#developer-installation) below for Python setup.

---

## 🛡️ **Why the Security Warnings?**

**Don't panic!** These warnings are **completely normal** and expected:

- ✅ **The app is 100% safe** - no malware, no viruses
- ✅ **Only connects to Turnkey Coach servers** - no data harvesting
- ✅ **Source code is open and inspectable** - full transparency
- ❌ **Not code-signed** - we don't pay Apple/Microsoft's yearly certificate fees

The warnings only appear because we're not paying $99/year to Apple and Microsoft for code signing certificates. The app is identical whether signed or not!

---

## ✨ **What's New in v1.4.0**

🎉 **Major Features Added:**
- **🥗 Nutrition Calendar**: Full nutrition assignment support alongside workout programming
- **📊 Enhanced Metrics System**: Track body composition, RPE, recovery, custom metrics
- **📅 Dual Calendar Support**: Mix training and nutrition assignments in same files  
- **🤖 Improved AI Chat**: Better context loading, date filtering, token management
- **🔍 Fuzzy Metric Matching**: Intelligent metric name mapping (70% similarity)
- **📝 Rich Markup**: Nutrition check-ins, fun facts, educational content

---

## 🎯 **Core Features**

### **Client Management Tools**
1. **📱 Unified Feed** - Timeline of all client interactions (messages + comments)
2. **💪 Estimated 1RMs** - Strength analysis using Wendler's formula + Wilks scores
3. **🏆 Actual PRs** - Official personal records from API
4. **📋 Workout History Browser** - Export formatted histories to your editor
5. **⬆️ Upload Workouts/Nutrition** - Parse text files, upload both training + nutrition
6. **🤖 AI Chat** - LLM programming assistant with workout context
7. **📊 Program Metrics** - Track client metrics (weight, body fat, RPE, etc.)
8. **✅ Validate Markup** - Dry run parser to check files before upload

### **🏋️ Dual Calendar System**
- **Training Calendar** (`Workout Date:`): Exercises, sets, reps, weights, RPE, conditioning
- **Nutrition Calendar** (`Nutrition Date:`): Meal check-ins, body metrics, education, habit tracking

**Both support metrics tracking and can be mixed in the same file!**

### **📊 Metrics System** 
Track any quantifiable client data:
- **Body Composition**: Weight, body fat %, measurements (waist, chest, etc.)
- **Performance**: RPE, recovery scores, sleep quality, energy levels
- **Subjective**: Stress, motivation, fatigue, difficulty ratings
- **Custom**: Coach-defined metrics with intelligent fuzzy matching

### **🤖 AI Integration**
- **Context-aware chat** with recent workout history
- **Date range filtering** (3 months default) to manage token costs
- **Dual LLM support**: OpenAI GPT and xAI Grok models
- **Encrypted API key storage** for security
- **Programming assistance**: Exercise selection, periodization advice, program analysis

---

## 🎬 **Getting Started**

### **First Launch**
1. **Download Exercise Database**: Say **"yes"** when prompted to download `exerciselist.json`
2. **Login**: Use your Turnkey Coach email and password
3. **Select Client**: **Pick a recent client first!** Initial downloads take a while for clients with long histories
4. **Look Around**: Browse workouts, try different tools - but be patient on first loads!

### **For AI Chat (Optional)**
To use the AI programming assistant:
1. **Get API Key**: 
   - **OpenAI**: [platform.openai.com](https://platform.openai.com) (GPT models)
   - **xAI**: [console.x.ai](https://console.x.ai) (Grok models - often cheaper!)
2. **Buy Credits**: Both services require prepaid credits (very affordable)
3. **Save Securely**: Store your API key safely in the app settings

### **File Upload Tips**
- Create workout files in the markup format (see [Markup Guide](markup.md))
- Use **Validate Markup** (option 8) to test files before uploading
- Mix training and nutrition assignments in the same file
- The parser is forgiving - it will help fix common mistakes!

---

## 📝 **Markup Language Examples**

### **Training Assignment**
```markdown
Workout Date: 2025-10-14

Squat
3x5 @ 225
    Focus on hitting depth, keep chest up
    
Bench Press  
1x5 @ RPE 8

Deadlift
1x3 @ 85%
```

### **Nutrition Assignment**
```markdown
Nutrition Date: 2025-10-14
@weight_kgs: 85.5
@body_fat: 15.2%
@waist_in:

Nutrition Check-In
    How are you feeling this week?
    Tell me about your energy levels.
    Any challenges with the meal plan?
    
    Fun fact: Protein needs increase 20-25% during intensive 
    strength training phases to support muscle recovery!
```

### **Mixed Assignment (Both in One File)**
```markdown
Workout Date: 2025-10-14
Squat
3x5 @ 225

---
Nutrition Date: 2025-10-14
@weight_kgs:
@sleep: 8 hours

Nutrition Check-In
    How did you sleep?
    Rate your energy 1-10.
```

---

## 📖 **Documentation**

- **[macOS Installation Guide](COACH-INSTALL-GUIDE.md)** - Detailed setup for macOS
- **[Markup Language Guide](markup.md)** - Complete syntax reference
- **[Build Guide](BUILD-GUIDE.md)** - For developers building apps
- **[DevGuides/](DevGuides/)** - Architecture documentation

---

## 🆘 **Need Help?**

### **Common Issues**
- **"No clients showing"**: Check internet connection and login credentials
- **"App won't open"**: Follow the security warning fixes above
- **"Slow performance"**: Some tools take time with large workout histories - be patient!
- **"Upload failed"**: Use **Validate Markup** first to check your file format

### **You Can't Break Anything!**
**Seriously** - play around, click everything, try all the tools. The worst that happens is you see an error message. All your client data is safely stored on Turnkey's servers.

---

## 👨‍💻 **Developer Installation**

*For Linux users, developers, or those who want to run from Python source:*

### **Prerequisites**
- **Python 3.7+** (3.9+ recommended)
- **pip** package manager  
- **Virtual environment** (highly recommended)

### **Quick Install**
```bash
# 1. Clone repository
git clone https://github.com/your-org/workout-parser.git
cd workout-parser

# 2. Create virtual environment
python3 -m venv venv
source venv/bin/activate  # Linux/macOS
# venv\Scripts\activate  # Windows

# 3. Install dependencies
pip install --upgrade pip
pip install -r requirements.txt

# 4. Run the application
python coach_cli.py
```

### **Linux Distribution Specifics**

**Ubuntu/Debian:**
```bash
sudo apt update
sudo apt install python3 python3-pip python3-venv
# Then follow Quick Install above
```

**CentOS/RHEL/Fedora:**
```bash
sudo dnf install python3 python3-pip  # Fedora
# sudo yum install python3 python3-pip  # RHEL/CentOS
# Then follow Quick Install above
```

**Arch Linux:**
```bash
sudo pacman -S python python-pip
# Then follow Quick Install above
```

### **Development Testing**
```bash
# Run test suite
pytest tests/

# Validate markup parsing
python coach_cli.py  # Choose option 8
```

---

## 📄 **License & Credits**

MIT License - see [LICENSE](LICENSE) for details.

**Built for coaches, by coaches.** 💪

*Questions? Issues? The waterpark can wait! 🏊‍♂️*

---

**Version 1.4.0** • *October 2025* • **[Download Latest Release](https://github.com/your-org/workout-parser/releases)**