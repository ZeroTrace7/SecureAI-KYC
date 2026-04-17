'use client';

import { useState, useEffect, useRef } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { RefreshCcw, Fingerprint, Database, Maximize, Shield, ScanEye, FileText, AlertTriangle, CheckCircle2, Eye, Terminal, ChevronRight, Brain, PenTool, Type, Link, Cpu, IndianRupee } from 'lucide-react';

interface Props {
  fileName: string;
  preview: string | null;
  onReset: () => void;
  apiData: any;
  docType?: string;
}

/* ─── Typewriter Hook ─── */
function useTypewriter(text: string, speed = 30) {
  const [displayed, setDisplayed] = useState('');
  const [done, setDone] = useState(false);

  useEffect(() => {
    setDisplayed('');
    setDone(false);
    let i = 0;
    const interval = setInterval(() => {
      i++;
      setDisplayed(text.slice(0, i));
      if (i >= text.length) {
        clearInterval(interval);
        setDone(true);
      }
    }, speed);
    return () => clearInterval(interval);
  }, [text, speed]);

  return { displayed, done };
}

/* ─── Animated Score Counter ─── */
function AnimatedScore({ target, color }: { target: number; color: string }) {
  const [count, setCount] = useState(0);

  useEffect(() => {
    let current = 0;
    const step = target / 40;
    const interval = setInterval(() => {
      current += step;
      if (current >= target) {
        setCount(target);
        clearInterval(interval);
      } else {
        setCount(Math.round(current));
      }
    }, 30);
    return () => clearInterval(interval);
  }, [target]);

  return (
    <span className={`text-6xl font-black tabular-nums ${color}`}>
      {count}
    </span>
  );
}

/* ─── Agent Check Card ─── */
function AgentCard({ icon: Icon, title, description, passed, failed, delay }: {
  icon: React.ElementType; title: string; description: string; passed?: boolean; failed?: boolean; delay: number;
}) {
  return (
    <motion.div
      initial={{ opacity: 0, y: 15 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ delay, duration: 0.4 }}
      className={`p-5 rounded-xl border flex items-start gap-4 transition-all
        ${failed ? 'bg-red-500/5 border-red-500/20' :
          passed ? 'bg-emerald-500/5 border-emerald-500/20' :
          'bg-slate-800/30 border-slate-700/50'}
      `}
      style={{ backdropFilter: 'blur(12px)' }}
    >
      <div className={`flex-shrink-0 w-10 h-10 rounded-lg flex items-center justify-center ${
        failed ? 'bg-red-500/10' : passed ? 'bg-emerald-500/10' : 'bg-slate-800'
      }`}>
        <Icon className={`w-5 h-5 ${failed ? 'text-red-400' : passed ? 'text-emerald-400' : 'text-indigo-400'}`} />
      </div>
      <div className="flex-1 min-w-0">
        <div className="flex items-center justify-between mb-1">
          <h4 className="text-sm font-semibold text-slate-200">{title}</h4>
          {failed && <span className="text-[10px] uppercase font-bold text-red-400 border border-red-500/30 px-2 py-0.5 rounded">FAILED</span>}
          {passed && <span className="text-[10px] uppercase font-bold text-emerald-400 border border-emerald-500/30 px-2 py-0.5 rounded">PASSED</span>}
        </div>
        <p className="text-xs text-slate-400 leading-relaxed">{description}</p>
      </div>
    </motion.div>
  );
}

/* ═════════════════════════════════════════════════
   MAIN ANALYSIS RESULTS COMPONENT
   ═════════════════════════════════════════════════ */
export default function AnalysisResults({ fileName, preview, onReset, apiData, docType = 'auto' }: Props) {
  const riskScore = apiData?.fraud_score || 0;
  const decision = apiData?.decision || 'UNKNOWN';
  const isForged = decision === 'FORGED' || decision === 'REJECTED';
  const isSuspicious = decision === 'SUSPICIOUS' || decision === 'MANUAL_REVIEW';
  const isClean = decision === 'GENUINE';
  const circumference = 2 * Math.PI * 80;

  const aiExplanation = apiData?.explanation || "Analysis complete. Awaiting detailed explanation.";

  const { displayed: typedExplanation, done: typingDone } = useTypewriter(aiExplanation, 18);

  // ── Derived states for agents ──
  const elaData = apiData?.ela || {};
  const elaScore = elaData?.ela_score ?? null;

  const sigSeal = apiData?.signature_seal || {};
  const sealFound = sigSeal?.seal?.seal_found || false;
  const sigFound = sigSeal?.signature?.signature_found || false;
  const sigSealScore = sigSeal?.signature_seal_score || 0;
  const sigSealAnomalies = sigSeal?.anomalies || [];

  const textIntegrity = apiData?.text_integrity || {};
  const tiScore = textIntegrity?.text_integrity_score || 0;
  const fontOk = textIntegrity?.font_analysis?.font_consistent !== false;
  const confOk = textIntegrity?.confidence_analysis?.confidence_consistent !== false;
  const layoutOk = textIntegrity?.spatial_analysis?.layout_consistent !== false;

  const blockchain = apiData?.blockchain || {};
  const bcSeen = blockchain?.previously_seen || false;
  const bcChainValid = blockchain?.chain_valid !== false;
  const bcTotalBlocks = blockchain?.total_blocks || 0;

  const mlForgeryData = apiData?.ml_forgery || {};
  const mlScore = mlForgeryData?.ml_forgery_score !== null && mlForgeryData?.ml_forgery_score !== undefined ? mlForgeryData?.ml_forgery_score : null;

  const structuredData = apiData?.structured_validation || {};
  const structuredScore = structuredData?.structured_validation_score ?? null;
  const structuredIssues = structuredData?.issues || structuredData?.failures || [];

  return (
    <motion.div
      initial={{ opacity: 0, y: 30 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.6, ease: 'easeOut' }}
      className="w-full"
    >
      {/* ─── Header ─── */}
      <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4 mb-8">
        <div>
          <p className="text-xs font-bold text-indigo-400 uppercase tracking-widest mb-2 flex items-center gap-1.5">
            <span className="w-1.5 h-1.5 rounded-full bg-indigo-400 animate-pulse" />
            Analysis Complete
          </p>
          <h2 className="text-2xl font-bold text-white flex items-center gap-3 flex-wrap">
            {fileName}
            <motion.span 
              initial={{ scale: 0 }} 
              animate={{ scale: 1 }} 
              transition={{ type: 'spring', delay: 0.3 }}
              className={`text-xs px-3 py-1.5 border rounded-full font-bold ${
                isForged 
                  ? 'bg-red-500/10 border-red-500/20 text-red-400' 
                  : isSuspicious
                  ? 'bg-amber-500/10 border-amber-500/20 text-amber-400'
                  : 'bg-emerald-500/10 border-emerald-500/20 text-emerald-400'
              }`}
            >
              {isForged ? (decision === 'REJECTED' ? '⛔ Rejected — Invalid Document' : '⚠ Forged / Tampered') : isSuspicious ? (decision === 'MANUAL_REVIEW' ? '⏳ Manual Review Required' : '⚠ Suspicious') : '✓ Genuine'}
            </motion.span>
          </h2>
        </div>
        <button 
          onClick={onReset} 
          className="flex items-center gap-2 px-5 py-2.5 border border-slate-700 rounded-xl text-sm font-medium text-slate-300 hover:bg-slate-800 hover:border-slate-600 transition-all bg-slate-900/50"
        >
          <RefreshCcw className="w-4 h-4" /> Scan Another
        </button>
      </div>

      {/* ─── Top Row: Score + Cross-Validation ─── */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-6">
        
        {/* Risk Score Gauge */}
        <motion.div 
          initial={{ opacity: 0, scale: 0.9 }}
          animate={{ opacity: 1, scale: 1 }}
          transition={{ delay: 0.2, duration: 0.5 }}
          className="col-span-1 p-8 rounded-2xl border border-slate-800/80 flex flex-col items-center justify-center text-center relative overflow-hidden"
          style={{ backdropFilter: 'blur(16px)', background: 'rgba(15, 23, 42, 0.6)' }}
        >
          {/* Background glow */}
          <div className={`absolute top-0 right-0 w-40 h-40 blur-[80px] opacity-25 rounded-full ${isForged ? 'bg-red-500' : isSuspicious ? 'bg-amber-500' : 'bg-emerald-500'}`} />
          
          <p className="text-xs font-bold text-slate-500 uppercase tracking-widest mb-8">Fraud Risk Score</p>
          
          {/* SVG Ring Gauge */}
          <div className="relative w-44 h-44 flex items-center justify-center mb-6">
            <svg className="absolute inset-0 w-full h-full transform -rotate-90" viewBox="0 0 180 180">
              {/* Background ring */}
              <circle cx="90" cy="90" r="80" fill="transparent" stroke="currentColor" strokeWidth="8" className="text-slate-800/80" />
              {/* Score arc */}
              <motion.circle
                cx="90" cy="90" r="80"
                fill="transparent"
                strokeWidth="8"
                strokeLinecap="round"
                className={isForged ? 'text-red-500' : isSuspicious ? 'text-amber-500' : 'text-emerald-500'}
                stroke="currentColor"
                strokeDasharray={circumference}
                initial={{ strokeDashoffset: circumference }}
                animate={{ strokeDashoffset: circumference - (circumference * riskScore) / 100 }}
                transition={{ duration: 1.5, ease: 'easeOut', delay: 0.5 }}
              />
            </svg>
            <div className="flex flex-col items-center">
              <AnimatedScore target={riskScore} color={isForged ? 'text-red-400' : isSuspicious ? 'text-amber-400' : 'text-emerald-400'} />
              <span className="text-xs text-slate-500 font-bold mt-1">/ 100</span>
            </div>
          </div>
          
          <p className={`text-sm font-medium ${isForged ? 'text-red-400' : isSuspicious ? 'text-amber-400' : 'text-emerald-400'}`}>
            {decision === 'GENUINE' ? 'Genuine — Verified' : decision === 'MANUAL_REVIEW' ? 'Manual Review Required' : decision === 'SUSPICIOUS' ? 'Suspicious — Needs Review' : decision === 'REJECTED' ? 'Rejected — Invalid Document' : 'Forged — Auto-Rejected'}
          </p>
        </motion.div>

        {/* Cross-Validation Component */}
        <motion.div
          initial={{ opacity: 0, scale: 0.9 }}
          animate={{ opacity: 1, scale: 1 }}
          transition={{ delay: 0.35, duration: 0.5 }}
          className="col-span-1 md:col-span-2"
        >
          <motion.div
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.6 }}
            className="h-full p-8 rounded-2xl border border-slate-800/80 flex flex-col justify-center"
            style={{ backdropFilter: 'blur(16px)', background: 'rgba(15, 23, 42, 0.6)' }}
          >
            <h3 className="text-sm font-semibold text-slate-300 mb-4 flex items-center gap-2">
              <Database className="w-4 h-4 text-indigo-400" /> Cross-Validation: OCR ↔ QR Data
            </h3>
            <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
              {(() => {
                const hasQR = apiData?.qr?.has_qr;
                const crossValAvailable = apiData?.cross_validation?.qr_ocr_match !== null && apiData?.cross_validation?.qr_ocr_match !== undefined;
                const fields = [
                  { label: 'OCR Name', value: apiData?.ocr?.fields?.name || 'N/A', match: true, skipped: false },
                  { label: 'QR Name', value: hasQR ? (apiData?.qr?.qr_name || 'N/A') : 'N/A', match: hasQR ? apiData?.cross_validation?.name_similarity > 80 : true, skipped: !hasQR },
                  { label: 'Similarity Score', value: crossValAvailable ? `${apiData?.cross_validation?.name_similarity || 0}%` : 'N/A', match: true, skipped: !crossValAvailable },
                  { label: 'QR Found', value: hasQR ? 'Yes' : 'No', match: hasQR, skipped: false },
                ];
                return fields.map((field, i) => (
                  <div key={i} className="space-y-1">
                    <span className="text-[10px] uppercase tracking-wider text-slate-500 font-bold">{field.label}</span>
                    <p className={`text-sm font-medium ${field.skipped ? 'text-slate-500 italic' : field.match ? 'text-slate-200' : 'text-red-400 line-through'}`}>
                      {field.value}
                    </p>
                    {field.skipped && <span className="text-[10px] text-slate-500 font-bold">SKIPPED</span>}
                    {!field.skipped && !field.match && <span className="text-[10px] text-red-400 font-bold">MISMATCH</span>}
                  </div>
                ));
              })()}
            </div>
          </motion.div>
        </motion.div>
      </div>

      {/* ─── Multi-Agent Forensic Grid (11 signals) ─── */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4 mb-6">

        {/* 1. Quality Gate */}
        <AgentCard
          icon={Shield}
          title="Integrity Validation"
          description={apiData?.quality?.quality_pass 
            ? 'Image passes all integrity checks. Resolution and focus are within acceptable bounds.'
            : `Failed integrity checks: ${apiData?.quality?.details || 'Unknown blur or resolution issues.'}`}
          passed={apiData?.quality?.quality_pass}
          failed={!apiData?.quality?.quality_pass}
          delay={0.4}
        />

        {/* 2. Classifier + OCR */}
        <AgentCard
          icon={ScanEye}
          title="Classification & OCR"
          description={`Identified as ${apiData?.document_type || 'Unknown'}. OCR extracted ${Object.keys(apiData?.ocr?.fields || {}).length} target fields.`}
          passed={apiData?.document_type !== 'unknown'}
          failed={apiData?.document_type === 'unknown'}
          delay={0.45}
        />

        {/* 3. ELA Pixel Forensics */}
        <AgentCard
          icon={Fingerprint}
          title="ELA Pixel Forensics"
          description={
            elaScore !== null
              ? (elaScore < 0.3
                ? `No significant compression artifacts detected. Error level variance: ${elaScore.toFixed(3)}.`
                : `⚠ Compression inconsistencies detected — possible pixel manipulation. ELA variance: ${elaScore.toFixed(3)}.`)
              : 'ELA analysis not available for this document.'
          }
          passed={elaScore !== null && elaScore < 0.3}
          failed={elaScore !== null && elaScore >= 0.3}
          delay={0.5}
        />

        {/* 4. EXIF Metadata Analysis */}
        <AgentCard
          icon={Eye}
          title="EXIF Metadata Analysis"
          description={`EXIF flag: ${apiData?.exif?.exif_flag || 'clean'}. ${apiData?.exif?.software ? `Editing software detected: ${apiData.exif.software}.` : 'No editing software signatures found.'}`}
          passed={apiData?.exif?.exif_flag === 'clean'}
          failed={apiData?.exif?.exif_flag !== 'clean'}
          delay={0.55}
        />

        {/* 5. Deepfake Detection */}
        <AgentCard
          icon={AlertTriangle}
          title="Deepfake Detection"
          description={
            apiData?.deepfake?.deepfake_score !== null && apiData?.deepfake?.deepfake_score !== undefined
              ? (apiData.deepfake.deepfake_score < 0.5
                ? `Face appears authentic. Confidence: ${((1 - apiData.deepfake.deepfake_score) * 100).toFixed(1)}% real.`
                : `⚠ Synthetic face artifacts detected. Deepfake probability: ${(apiData.deepfake.deepfake_score * 100).toFixed(1)}%.`)
              : 'No face detected or deepfake analysis was not triggered.'
          }
          passed={!apiData?.deepfake?.deepfake_score || apiData?.deepfake?.deepfake_score < 0.5}
          failed={apiData?.deepfake?.deepfake_score && apiData?.deepfake?.deepfake_score >= 0.5}
          delay={0.6}
        />

        {/* 6. ML Forgery Engine */}
        <AgentCard
          icon={Cpu}
          title="ML Spatial Forgery"
          description={
            mlScore !== null
              ? (mlScore < 0.5
                ? `No severe spatial manipulation detected. Confidence score: ${(1 - mlScore).toFixed(2)}.`
                : `⚠ Forgery detected in spatial domain. Anomaly score: ${mlScore.toFixed(2)}.`)
              : 'ML forgery analysis not available or bypassed.'
          }
          passed={mlScore !== null && mlScore < 0.5}
          failed={mlScore !== null && mlScore >= 0.5}
          delay={0.65}
        />

        {/* 7. QR Signature Verification */}
        <AgentCard
          icon={FileText}
          title="QR Signature Verification"
          description={apiData?.qr?.has_qr 
            ? 'UIDAI secure QR decoded successfully. Payload cross-verified against OCR fields.'
            : 'No QR code detected or decoding failed on this standard document format.'}
          passed={apiData?.qr?.has_qr}
          failed={!apiData?.qr?.has_qr && apiData?.document_type === 'aadhaar'}
          delay={0.7}
        />

        {/* 8. Signature & Seal Verification */}
        <AgentCard
          icon={PenTool}
          title="Signature & Seal Verification"
          description={
            sigSealAnomalies.length > 0
              ? `Anomalies detected: ${sigSealAnomalies.slice(0, 2).join('; ')}. Seal: ${sealFound ? 'Found' : 'None'}. Signature: ${sigFound ? 'Found' : 'None'}.`
              : `Seal: ${sealFound ? 'Detected ✓' : 'Not detected'}. Signature: ${sigFound ? 'Detected ✓' : 'Not detected'}. No irregularities found.`
          }
          passed={sigSealScore < 0.25}
          failed={sigSealScore >= 0.25}
          delay={0.75}
        />

        {/* 9. Text Integrity Analysis */}
        <AgentCard
          icon={Type}
          title="Text Integrity Analysis"
          description={
            tiScore > 0.25
              ? `Anomalies detected — Font: ${fontOk ? 'OK' : '⚠ Inconsistent'}, Confidence: ${confOk ? 'OK' : '⚠ Variable'}, Layout: ${layoutOk ? 'OK' : '⚠ Irregular'}. Score: ${tiScore.toFixed(3)}.`
              : `All checks passed — Font consistency: OK, OCR confidence: Uniform, Spatial layout: Regular. Score: ${tiScore.toFixed(3)}.`
          }
          passed={tiScore <= 0.25}
          failed={tiScore > 0.25}
          delay={0.8}
        />

        {/* 10. Blockchain Hash Ledger */}
        <AgentCard
          icon={Link}
          title="Blockchain Hash Ledger"
          description={
            bcSeen
              ? `Document previously registered in ledger. Chain integrity: ${bcChainValid ? 'Valid ✓' : '⚠ Broken'}. Total blocks: ${bcTotalBlocks}.`
              : `First-time submission — no prior record. Registered in hash chain. Chain integrity: ${bcChainValid ? 'Valid ✓' : '⚠ Broken'}. Blocks: ${bcTotalBlocks}.`
          }
          passed={bcChainValid && !(bcSeen && (blockchain?.blockchain_score || 0) > 0.5)}
          failed={!bcChainValid || (bcSeen && (blockchain?.blockchain_score || 0) > 0.5)}
          delay={0.85}
        />

        {/* 11. Structured Document Validation (shows when structured data exists) */}
        {structuredScore !== null && structuredScore !== undefined && (
          <AgentCard
            icon={IndianRupee}
            title="Structured Document Validation"
            description={
              structuredScore < 0.25
                ? `All field-level checks passed. Arithmetic totals, format checksums, and character-class validations are consistent. Score: ${structuredScore.toFixed(3)}.`
                : `⚠ Structural anomalies detected${structuredIssues.length > 0 ? `: ${structuredIssues.slice(0, 2).join('; ')}` : ''}. Arithmetic or format inconsistencies found. Score: ${structuredScore.toFixed(3)}.`
            }
            passed={structuredScore < 0.25}
            failed={structuredScore >= 0.25}
            delay={0.9}
          />
        )}
      </div>

      {/* ─── AI Explanation Terminal ─── */}
      <motion.div
        initial={{ opacity: 0, y: 15 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 1.1, duration: 0.4 }}
        className="rounded-xl border border-slate-800/80 overflow-hidden"
        style={{ backdropFilter: 'blur(12px)', background: 'rgba(15, 23, 42, 0.5)' }}
      >
        <div className="flex items-center gap-2 px-4 py-3 border-b border-slate-800/80 bg-slate-900/50">
          <Brain className="w-4 h-4 text-purple-400" />
          <span className="text-xs font-bold text-slate-400 uppercase tracking-wider">AI Reasoning</span>
          <div className="ml-auto flex items-center gap-1.5">
            <div className="w-2 h-2 rounded-full bg-red-500/80" />
            <div className="w-2 h-2 rounded-full bg-yellow-500/80" />
            <div className="w-2 h-2 rounded-full bg-green-500/80" />
          </div>
        </div>
        <div className="p-5 font-mono">
          <div className="flex items-start gap-2">
            <Terminal className="w-4 h-4 text-indigo-400 mt-0.5 flex-shrink-0" />
            <p className="text-sm text-slate-300 leading-relaxed">
              {typedExplanation}
              {!typingDone && <span className="inline-block w-2 h-4 bg-indigo-400 animate-pulse ml-0.5 align-middle" />}
            </p>
          </div>
        </div>
      </motion.div>
    </motion.div>
  );
}
