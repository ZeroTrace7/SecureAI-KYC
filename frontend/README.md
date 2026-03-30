# 🛡️ SECUREAI-KYC — Frontend (Next.js & React)

This directory contains the user-facing dashboard for the SecureAI-KYC system, built with Next.js, Tailwind CSS, and Framer Motion for a premium user experience.

---

## 🎨 Design Vision

The frontend is designed to be:
- **Premium & Modern**: Using sleek dark modes and elegant layouts.
- **Dynamic**: Real-time feedback and animated transitions for each verification stage.
- **Secure**: Transparent indicators of ELA forensics and fraud scores.

---

## 🚀 Getting Started

1. **Install Dependencies**:
   ```bash
   npm install
   ```

2. **Configure Environment**:
   Create a `.env.local` to connect to the backend:
   ```env
   NEXT_PUBLIC_API_URL=http://localhost:8000/api
   ```

3. **Run Development Server**:
   ```bash
   npm run dev
   ```

4. **Visit**: http://localhost:3000

---

## 📋 Features

- **Document Upload**: Multi-format support (JPG, PNG, PDF).
- **Audit Viewer**: Browse through past verification logs.
- **Fraud Score Dashboard**: Deep dive into individual signal scores (ELA, OCR, QR).
- **ELA Heatmap Visualization**: Direct view of tampered document regions.

---

## 📦 Tech Stack

- **Framework**: Next.js 15+ (App Router)
- **Styling**: Tailwind CSS
- **Animations**: Framer Motion
- **Icons**: Lucide React
- **Verification Engine**: SecureAI-KYC Backend (FastAPI)
