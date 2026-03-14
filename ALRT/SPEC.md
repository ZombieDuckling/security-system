# Alert Security App - Specification Document

## 1. Project Overview

**Project Name:** ALRT  
**Type:** iOS Mobile Application (SwiftUI)  
**Purpose:** Frontend mockup for a security mobile app that interfaces with a Raspberry Pi-based security system. The app allows users to monitor security status, receive alerts, manage detection features, coordinate with friends/family, and track response progress.  
**Target Users:** Homeowners, family members, and response coordinators who need real-time security monitoring and alert management.

---

## 2. UI/UX Specification

### 2.1 Screen Structure

The app uses a **TabView** navigation structure with 5 main tabs:

1. **Dashboard** - Main status screen with system on/off, threat level, alerts
2. **Detection** - Configure and monitor various detection features
3. **Response** - Response mode, status updates, GPS tracking
4. **Members** - Add/manage family members, face scanning
5. **Settings** - App configuration, sleep time, safe words

### 2.2 Visual Design

#### Color Palette (Dark Security Theme)

| Color Name | Hex Code | Usage |
|------------|----------|-------|
| Background Primary | #0D0D0D | Main screen backgrounds |
| Background Secondary | #1A1A1A | Cards, elevated surfaces |
| Background Tertiary | #262626 | Input fields, inactive elements |
| Accent Green | #00C853 | Safe/Online status, success |
| Accent Red | #FF1744 | Alert/Danger/Active threat |
| Accent Orange | #FF9100 | Warning/Medium threat |
| Accent Blue | #2979FF | Interactive elements, links |
| Accent Purple | #7C4DFF | Response mode indicators |
| Text Primary | #FFFFFF | Headings, important text |
| Text Secondary | #B3B3B3 | Body text, descriptions |
| Text Tertiary | #666666 | Placeholders, disabled |

### 2.3 Features List

| Feature | Tab | Description |
|---------|-----|-------------|
| System Status | Dashboard | Shows connected/disconnected, armed/disarmed |
| Test Mode | Dashboard | High threat / Low threat toggle |
| Forced Entry Noise | Detection | Sound activation |
| Hands Up Gesture | Detection | Gesture recognition |
| Fire/Smoke Detection | Detection | Smoke sensor |
| Screaming Voice | Detection | Voice stress detection |
| Night Vision | Detection | Night vision camera support |
| Unusual Person Detection | Detection | Stranger detection |
| Silence Detection | Detection | Unusual quiet detection |
| Motion Detection | Detection | Movement in home |
| Face Recognition | Members | Scan face, mark as safe |
| Members Management | Members | Add/update family members |
| Response Mode | Response | Switch user/responder mode |
| GPS Tracking | Response | Location sharing |
| Status Updates | Response | En Route, On Scene, Secured, Clear |
| Sleep Time | Settings | Configure sleep schedule |
| Safe Word | Settings | Record safe word |
| False Alarm Comm | Settings | Communication settings |
