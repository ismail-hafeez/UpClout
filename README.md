# UpClout Frontend

A professional React + TypeScript frontend for the **UpClout** influencer marketing platform.

---

## 📁 Project Structure

```
upclout/
├── public/
│   └── index.html
├── src/
│   ├── components/
│   │   └── OwlIcon.tsx          # SVG owl mascot component
│   ├── data/
│   │   └── mockData.ts          # Mock chats, messages, avatars
│   ├── pages/
│   │   ├── LoginPage.tsx / .css     # Split-layout login
│   │   ├── MainPage.tsx / .css      # Landing/dashboard
│   │   ├── OwlyIntro.tsx / .css     # Owly intro card
│   │   ├── OwlyChat.tsx / .css      # AI chatbot interface
│   │   └── UserChat.tsx / .css      # User-to-user messaging
│   ├── styles/
│   │   └── globals.css          # CSS variables, resets, animations
│   ├── App.tsx                  # Page router
│   └── index.tsx                # Entry point
├── package.json
└── tsconfig.json
```

---

## 🚀 How to Run in VS Code

### Prerequisites
Make sure you have installed:
- **Node.js** (v16 or higher) — https://nodejs.org
- **npm** (comes with Node.js)

To check: open Terminal and run:
```bash
node -v
npm -v
```

---

### Step-by-Step Setup

**1. Open the project in VS Code**
```
File → Open Folder → select the "upclout" folder
```

**2. Open the integrated terminal**
```
View → Terminal   (or press  Ctrl + ` )
```

**3. Install dependencies**
```bash
npm install
```
This takes ~1-2 minutes and downloads all required packages.

**4. Start the development server**
```bash
npm start
```

**5. Open in browser**

The app automatically opens at: **http://localhost:3000**

If it doesn't open automatically, visit that URL in your browser.

---

## 🧭 App Navigation Flow

```
Login Page
    ↓ (click LOGIN with any input + tick reCAPTCHA)
Owly Intro Screen
    ↓ (click "Start chatting with Owly")
Owly AI Chat
    ↓ (click ← back)
Main Dashboard
    ↓ (click "Browse Chats")
User-to-User Chat
```

From the **Main Dashboard** you can also:
- Click **"Ask Owly AI"** → Owly Intro
- Click the chat icon in the navbar → User Chat

---

## 🎨 Design System

| Token | Value |
|-------|-------|
| Primary blue | `#2563eb` |
| Dark navy | `#1e4da1` |
| Background | `#b8bfc9` |
| Surface | `#d1d5db` |
| Display font | Sora (Google Fonts) |
| Body font | DM Sans (Google Fonts) |

---

## 🔌 Ready for Backend Integration

All pages are built with clean props interfaces. To connect a real backend:

- **LoginPage** — replace `setTimeout` in `handleLogin` with a real auth API call
- **OwlyChat** — replace the mock response with a streaming AI API endpoint  
- **UserChat** — replace mock messages with WebSocket or polling
- **mockData.ts** — replace with real API calls using `fetch` or `axios`

---

## 📦 Build for Production

```bash
npm run build
```

Output goes to the `build/` folder — ready to deploy on Vercel, Netlify, or any static host.
