# 🍯 HoneyPot System

<div align="center">
  
![Status](https://img.shields.io/badge/status-active-success?style=flat-square)
![License](https://img.shields.io/badge/license-MIT-blue?style=flat-square)
![Python](https://img.shields.io/badge/Python-3.8+-orange?style=flat-square&logo=python)
![React](https://img.shields.io/badge/React-18+-61dafb?style=flat-square&logo=react)
![Contributions](https://img.shields.io/badge/contributions-welcome-brightgreen?style=flat-square)

**Advanced Cyber Attack Detection & Monitoring System**

[Features](#-features) • [Installation](#-installation) • [Usage](#-usage) • [Architecture](#-architecture)

</div>

---

## 🎯 Project Overview

HoneyPot System is a **smart cybersecurity solution** designed to detect, monitor, and analyze unauthorized network access attempts. It combines real-time threat intelligence with machine learning to identify and visualize attack patterns across your network infrastructure.

> **What is a Honeypot?** A honeypot is a decoy system designed to attract attackers and log their behavior for security analysis and threat intelligence gathering.

---

## ✨ Features

<table>
  <tr>
    <td align="center" width="50%">
      <b>🗺️ Live Attack Map</b><br/>
      Real-time geographic visualization of attack origins and targets
    </td>
    <td align="center" width="50%">
      <b>🔍 Threat Intelligence</b><br/>
      Machine learning-powered attack classification and analysis
    </td>
  </tr>
  <tr>
    <td align="center" width="50%">
      <b>📊 Attack DVR</b><br/>
      Record and playback attack sessions for forensic analysis
    </td>
    <td align="center" width="50%">
      <b>👤 Attacker Profiles</b><br/>
      Detailed profiles of detected attackers and their tactics
    </td>
  </tr>
  <tr>
    <td align="center" width="50%">
      <b>🌐 Node Graph Visualization</b><br/>
      Interactive network topology and traffic flow analysis
    </td>
    <td align="center" width="50%">
      <b>🚨 Swarm Control</b><br/>
      Manage and orchestrate honeypot instances
    </td>
  </tr>
  <tr>
    <td align="center" width="50%">
      <b>📡 Traffic Telemetry</b><br/>
      Real-time network traffic monitoring and anomaly detection
    </td>
    <td align="center" width="50%">
      <b>🔐 SSH Honeypot</b><br/>
      Dedicated SSH service for credential harvesting
    </td>
  </tr>
</table>

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────┐
│                  Frontend (React)                    │
│  • Live Attack Map       • Threat Intelligence      │
│  • Node Graph            • Attack DVR               │
│  • Attacker Profile      • Swarm Control            │
└──────────────┬──────────────────────────────────────┘
               │ HTTP/WebSocket
┌──────────────▼──────────────────────────────────────┐
│               Backend (Flask)                        │
│  • API Server        • Data Processing              │
│  • Authentication    • Real-time Updates            │
└──────────────┬──────────────────────────────────────┘
               │
┌──────────────▼──────────────────────────────────────┐
│          Honeypot Services                           │
│  • SSH Honeypot      • HTTP Mock Service            │
│  • Log Aggregation   • Threat Analysis              │
└─────────────────────────────────────────────────────┘
```

---

## 🚀 Quick Start

### Prerequisites

- **Node.js** 18+ and npm
- **Python** 3.8+
- **Git**

### Installation

```bash
# Clone the repository
git clone https://github.com/DishantSaini55/HoneyPot_System.git
cd HoneyPot_System

# Install frontend dependencies
npm install

# Install backend dependencies
cd backend
pip install -r requirements.txt
cd ..
```

### Running the System

**Terminal 1 - Frontend:**
```bash
npm run dev
```
Open http://localhost:5173 in your browser

**Terminal 2 - Backend:**
```bash
cd backend
python app.py
```

**Terminal 3 - SSH Honeypot:**
```bash
cd backend
python ssh_honeypot.py
```

---

## 📁 Project Structure

```
HoneyPot_System/
├── src/                          # React Frontend
│   ├── components/               # React Components
│   │   ├── LiveAttackMap.jsx    # Real-time attack visualization
│   │   ├── AttackDVR.jsx        # Attack recording & playback
│   │   ├── AttackerProfile.jsx  # Attacker analysis dashboard
│   │   ├── NodeGraph.jsx        # Network topology
│   │   ├── SwarmControl.jsx     # Honeypot orchestration
│   │   ├── ThreatIntelligenceExport.jsx
│   │   └── ...
│   ├── data/                    # Mock data
│   ├── App.jsx                  # Main app component
│   └── main.jsx
├── backend/                      # Python Backend
│   ├── app.py                   # Flask API server
│   ├── ssh_honeypot.py          # SSH honeypot service
│   ├── requirements.txt         # Python dependencies
│   └── ...
├── prototype_ml_classification.py # ML threat classifier
├── package.json                  # Frontend dependencies
├── vite.config.js               # Vite configuration
└── README.md                    # This file
```

---

## 🛠️ Tech Stack

| Component | Technology | Version |
|-----------|-----------|---------|
| **Frontend** | React | 18.3 |
| **UI Framework** | Tailwind CSS | 3.4 |
| **Bundler** | Vite | 5.4 |
| **Map Visualization** | Leaflet + React-Leaflet | 4.2 |
| **Icons** | Lucide React | 1.8 |
| **Routing** | React Router | 7.14 |
| **Backend** | Flask | Latest |
| **ML Classification** | Python scikit-learn | - |

---

## 🎮 Usage Guide

### 1. Monitor Live Attacks
- Navigate to **Live Attack Map** to see real-time attack sources
- View attack origins geographically
- Click on attacks for detailed information

### 2. Analyze Attacker Profiles
- Access **Attacker Profile** section
- Review attack patterns and frequency
- Identify recurring threats

### 3. Export Threat Intelligence
- Use **Threat Intelligence Export** feature
- Generate reports in multiple formats
- Share intelligence with security teams

### 4. Review Attack Recordings
- Open **Attack DVR** to playback recorded sessions
- Timeline scrubbing for detailed forensics
- Export session logs

### 5. Manage Honeypots
- Use **Swarm Control** to manage multiple instances
- Deploy new honeypot sensors
- Monitor system health

---

## 🤖 ML Classification

The system includes a prototype ML classifier (`prototype_ml_classification.py`) that:

✅ Categorizes attack types  
✅ Predicts attacker sophistication  
✅ Identifies attack patterns  
✅ Generates threat scores  

---

## 📊 Dashboard Features

### Real-time Monitoring
- **Live Attack Feeds** - Continuous stream of detected attacks
- **Network Graph** - Interactive visualization of traffic flows
- **Threat Telemetry** - Packet-level analysis and metrics
- **Traffic Ticker** - Scrolling attack notifications

### Analysis Tools
- **Node Graph Analysis** - Relationship mapping between IPs
- **Temporal Analysis** - Time-based attack pattern recognition
- **Geographic Distribution** - World map of attack origins

---

## 🔒 Security Notes

⚠️ **Important:** This is a security research tool. Use only in controlled environments.

- Run honeypots on isolated networks when possible
- Monitor resource usage (honeypots can attract heavy traffic)
- Regularly review and analyze captured data
- Use SSH keys with strong passphrases
- Keep dependencies updated

---

## 📝 Environment Configuration

Create a `.env` file in the backend directory:

```env
FLASK_ENV=development
FLASK_DEBUG=True
API_PORT=5000
SSH_PORT=2222
LOG_LEVEL=INFO
```

---

## 🤝 Contributing

Contributions are welcome! 

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

---

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

---

## 🙋 Support

For issues, questions, or suggestions:
- Open an issue on GitHub
- Check existing documentation
- Review component code comments

---

<div align="center">

### Made with 🍯 by [DishantSaini55](https://github.com/DishantSaini55)

**⭐ If you find this project useful, please consider giving it a star!**

</div>
