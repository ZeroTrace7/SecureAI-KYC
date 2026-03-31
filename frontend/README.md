# 🛡️ SECUREAI-KYC — Frontend (Next.js & React)

This directory contains the user-facing dashboard for the SecureAI-KYC system, built with Next.js, Tailwind CSS, and Framer Motion for a premium user experience.

---

## 🎨 Design Vision

The frontend is designed to be:
- **Premium Aesthetics**: Migrated the `ai-spark` design language with glowing orbs, glassmorphic cards, and high-performance Framer Motion animations.
- **Micro-interactions**: Hover effects, staggered lists, and glowing gradients for a high-end fintech feel.
- **Dynamic**: Real-time feedback and animated transitions for each verification stage.
- **Secure**: Transparent indicators of ELA forensics and multi-signal fraud scores.

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

- **Forensic Pipeline Visualization**: Real-time progress through all parallel stages (OCR, EXIF, ELA, Seal, Deepfake, etc.).
- **Fraud Score Dashboard**: Deep-dive into 10 signal scores with interactive gauges and weight breakdowns.
- **ELA Heatmap Visualization**: Direct view of tampered document regions.
- **Audit Viewer**: Full history of KYC attempts with searchable compliance results.

---

## 📦 Tech Stack

- **Framework**: Next.js 15+ (App Router)
- **Styling**: Tailwind CSS
- **Animations**: Framer Motion
- **Icons**: Lucide React
- **Verification Engine**: SecureAI-KYC Backend (FastAPI)
