'use client';

import { useState, useRef, useCallback } from 'react';
import { useDocumentContext } from '@/context/DocumentContext';
import { motion, AnimatePresence } from 'framer-motion';
import { UploadCloud, File, CheckCircle2, Shield, ScanEye, Cpu, Fingerprint, GitCompareArrows, PenTool, Type, Link, IndianRupee } from 'lucide-react';
import AnalysisResults from './AnalysisResults';

const DOC_TYPES = [
  { id: 'auto', label: 'Auto-detect' },
  { id: 'aadhaar', label: 'Aadhaar' },
  { id: 'pan', label: 'PAN Card' },
  { id: 'passport', label: 'Passport' },
  { id: 'payslip', label: 'Salary Slip' },
  { id: 'utility', label: 'Utility Bill' },
];

const BASE_PIPELINE_STEPS = [
  { label: 'Validating document integrity...', icon: Shield, sublabel: 'Checking resolution, blur, MIME type' },
  { label: 'Classifying document type...', icon: ScanEye, sublabel: 'OCR keyword recognition & template matching' },
  { label: 'Extracting OCR text fields...', icon: Cpu, sublabel: 'Parsing Name, DOB, ID Number, Address' },
  { label: 'Running ELA forensic heatmap...', icon: Fingerprint, sublabel: 'Error Level Analysis & pixel tampering' },
  { label: 'EXIF metadata forensics...', icon: Fingerprint, sublabel: 'Checking for Photoshop traces & anomalies' },
  { label: 'Detecting deepfakes...', icon: ScanEye, sublabel: 'Face/document manipulation detection via ViT' },
  { label: 'Executing ML forgery detection...', icon: Cpu, sublabel: 'Spatial anomaly & pixel manipulation detection' },
  { label: 'Verifying signature & seal authenticity...', icon: PenTool, sublabel: 'HSV segmentation, contour analysis, stroke density' },
  { label: 'Analyzing text integrity patterns...', icon: Type, sublabel: 'Font consistency, confidence mapping, spatial anomalies' },
  { label: 'Checking blockchain hash ledger...', icon: Link, sublabel: 'SHA-256 + pHash verification against immutable chain' },
  { label: 'Cross-validating OCR ↔ QR data...', icon: GitCompareArrows, sublabel: 'Correlating printed fields against embedded data' },
  { label: 'Computing weighted fraud score...', icon: Shield, sublabel: 'Aggregating 9-signal confidence engine' },
];

const PAYSLIP_STEP = {
  label: 'Verifying income & employer fields...',
  icon: IndianRupee,
  sublabel: 'Checking gross pay, deductions, employer PAN & PF number consistency',
};

export default function DocumentUploader() {
  const {
    file, setFile,
    preview, setPreview,
    analyzing, setAnalyzing,
    currentStep, setCurrentStep,
    resultReady, setResultReady,
    apiResult, setApiResult,
    docType, setDocType
  } = useDocumentContext();

  const [isDragging, setIsDragging] = useState(false);
  const dropRef = useRef<HTMLDivElement>(null);

  const PIPELINE_STEPS = docType === 'payslip'
    ? [...BASE_PIPELINE_STEPS.slice(0, 3), PAYSLIP_STEP, ...BASE_PIPELINE_STEPS.slice(3)]
    : BASE_PIPELINE_STEPS;

  const processFile = useCallback((f: File) => {
    setFile(f);
    // generate preview for images
    if (f.type.startsWith('image/')) {
      const reader = new FileReader();
      reader.onload = (e) => setPreview(e.target?.result as string);
      reader.readAsDataURL(f);
    }
    runActualAnalysis(f);
  }, [PIPELINE_STEPS]);

  const handleUpload = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files.length > 0) {
      processFile(e.target.files[0]);
    }
  };

  const handleDrop = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);
    if (e.dataTransfer.files && e.dataTransfer.files.length > 0) {
      processFile(e.dataTransfer.files[0]);
    }
  }, [processFile]);

  const handleDragOver = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(true);
  }, []);

  const handleDragLeave = useCallback(() => {
    setIsDragging(false);
  }, []);

  const runActualAnalysis = async (f: File) => {
    setAnalyzing(true);
    setCurrentStep(0);
    setResultReady(false);
    
    // Start dummy progress bar while fetching
    let step = 0;
    const interval = setInterval(() => {
      if (step < PIPELINE_STEPS.length - 1) {
        step++;
        setCurrentStep(step);
      }
    }, 600);

    try {
      const formData = new FormData();
      formData.append('document', f);
      // We pass the doctype hint if it's not auto
      if (docType !== 'auto') {
         formData.append('docType_hint', docType);
      }

      // 120s timeout — first run may download AI models (~400MB)
      const controller = new AbortController();
      const timeoutId = setTimeout(() => controller.abort(new Error('Timeout')), 300000);

      const response = await fetch('http://localhost:8000/api/verify', {
        method: 'POST',
        body: formData,
        signal: controller.signal,
      });

      clearTimeout(timeoutId);

      if (!response.ok) {
        const errText = await response.text().catch(() => 'Unknown error');
        throw new Error(`API Error ${response.status}: ${errText}`);
      }

      const data = await response.json();
      setApiResult(data);
      
      clearInterval(interval);
      setCurrentStep(PIPELINE_STEPS.length - 1);
      
      setTimeout(() => {
        setAnalyzing(false);
        setResultReady(true);
      }, 500);

    } catch (error: any) {
      console.error('Verification error:', error);
      clearInterval(interval);
      setAnalyzing(false);
      if (error?.name === 'AbortError') {
        alert("Analysis timed out. The file might be too large or the backend is downloading AI models. Please try again.");
      } else {
        alert("Verification failed. Please ensure the backend is running on port 8000. Error: " + (error?.message || 'Unknown'));
      }
    }
  };

  const resetUploader = () => {
    setFile(null);
    setPreview(null);
    setResultReady(false);
    setCurrentStep(0);
    setApiResult(null);
  };

  if (resultReady && apiResult) {
    return (
      <AnalysisResults 
        fileName={file?.name || 'Document'} 
        preview={preview}
        onReset={resetUploader} 
        apiData={apiResult} 
        docType={docType}
      />
    );
  }

  const progress = analyzing ? ((currentStep + 1) / PIPELINE_STEPS.length) * 100 : 0;

  return (
    <motion.div
      ref={dropRef}
      onDrop={handleDrop}
      onDragOver={handleDragOver}
      onDragLeave={handleDragLeave}
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.5 }}
      className={`
        w-full h-full min-h-[520px] flex flex-col justify-center items-center rounded-3xl relative overflow-hidden
        transition-all duration-500 ease-out
        ${isDragging 
          ? 'bg-indigo-500/5 border-2 border-indigo-500 shadow-[0_0_60px_rgba(99,102,241,0.15)]' 
          : 'bg-slate-900/60 border-2 border-dashed border-slate-700/80 hover:border-slate-500'}
      `}
      style={{
        backdropFilter: 'blur(16px)',
      }}
    >
      {/* Animated background glow */}
      <div className={`absolute inset-0 pointer-events-none transition-opacity duration-700 ${isDragging ? 'opacity-100' : 'opacity-0'}`}>
        <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-80 h-80 bg-indigo-500/20 rounded-full blur-[100px]" />
      </div>
      <div className="absolute bottom-0 left-0 right-0 h-1/2 bg-gradient-to-t from-indigo-500/[0.03] to-transparent pointer-events-none" />

      <AnimatePresence mode="wait">
        {!analyzing ? (
          /* ─── IDLE STATE ─── */
          <motion.div
            key="idle"
            initial={{ opacity: 0, scale: 0.95 }}
            animate={{ opacity: 1, scale: 1 }}
            exit={{ opacity: 0, scale: 0.9 }}
            transition={{ duration: 0.4 }}
            className="flex flex-col items-center px-10 z-10"
          >
            <motion.div 
              animate={{ y: isDragging ? -8 : 0 }}
              transition={{ type: 'spring', stiffness: 300 }}
              className={`w-24 h-24 rounded-2xl mb-8 flex items-center justify-center transition-colors duration-300
                ${isDragging ? 'bg-indigo-500/20 shadow-[0_0_30px_rgba(99,102,241,0.3)]' : 'bg-slate-800/80'}
              `}
            >
              <UploadCloud className={`w-12 h-12 transition-colors duration-300 ${isDragging ? 'text-indigo-400' : 'text-slate-500'}`} />
            </motion.div>

            <h3 className="text-2xl font-bold text-white mb-2 tracking-tight">
              {isDragging ? 'Release to Scan' : 'Drop KYC Document Here'}
            </h3>
            <p className="text-sm text-slate-400 text-center max-w-sm mb-6 leading-relaxed">
              Supports <span className="text-slate-300 font-medium">Aadhaar</span>, <span className="text-slate-300 font-medium">PAN</span>, <span className="text-slate-300 font-medium">Passport</span>, <span className="text-slate-300 font-medium">Salary Slips</span>, and <span className="text-slate-300 font-medium">Utility Bills</span>.
              <br />JPEG, PNG, or PDF up to 10MB.
            </p>

            {/* Document Type Selector */}
            <div className="flex flex-wrap justify-center gap-2 mb-8">
              {DOC_TYPES.map((type) => (
                <button
                  key={type.id}
                  onClick={() => setDocType(type.id)}
                  className={`px-3 py-1.5 rounded-lg text-xs font-semibold border transition-all duration-200 ${
                    docType === type.id
                      ? type.id === 'payslip'
                        ? 'bg-amber-500/15 border-amber-500/40 text-amber-300'
                        : 'bg-indigo-500/15 border-indigo-500/40 text-indigo-300'
                      : 'bg-slate-800/60 border-slate-700/60 text-slate-500 hover:border-slate-500 hover:text-slate-300'
                  }`}
                >
                  {type.id === 'payslip' && <IndianRupee className="w-3 h-3 inline mr-1 -mt-0.5" />}
                  {type.label}
                </button>
              ))}
            </div>

            {/* Payslip hint */}
            <AnimatePresence>
              {docType === 'payslip' && (
                <motion.div
                  initial={{ opacity: 0, y: -6 }}
                  animate={{ opacity: 1, y: 0 }}
                  exit={{ opacity: 0, y: -6 }}
                  className="flex items-center gap-2 text-xs text-amber-400 bg-amber-500/10 border border-amber-500/20 rounded-lg px-4 py-2.5 mb-6"
                >
                  <IndianRupee className="w-3.5 h-3.5 flex-shrink-0" />
                  Salary Slip mode: income verification & employer PAN checks will run
                </motion.div>
              )}
            </AnimatePresence>

            <label className="relative cursor-pointer group">
              <div className="absolute -inset-1 bg-gradient-to-r from-indigo-600 to-purple-600 rounded-xl blur-sm opacity-60 group-hover:opacity-100 transition-opacity" />
              <div className="relative bg-indigo-600 hover:bg-indigo-500 text-white font-semibold py-3.5 px-10 rounded-xl transition-all flex items-center gap-2">
                <UploadCloud className="w-5 h-5" />
                Browse Files
              </div>
              <input type="file" className="hidden" accept="image/*,.pdf" onChange={handleUpload} />
            </label>
          </motion.div>
        ) : (
          /* ─── SCANNING STATE ─── */
          <motion.div
            key="scanning"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            transition={{ duration: 0.5 }}
            className="flex flex-col items-center w-full max-w-lg px-6 z-10"
          >
            {/* Scanning Icon */}
            <div className="relative w-20 h-20 mb-10">
              <div className="absolute inset-0 rounded-full border-[3px] border-slate-800" />
              <motion.div
                animate={{ rotate: 360 }}
                transition={{ repeat: Infinity, duration: 1.2, ease: 'linear' }}
                className="absolute inset-0 rounded-full border-[3px] border-transparent border-t-indigo-500 border-r-indigo-500/50"
              />
              <div className="absolute inset-0 flex items-center justify-center">
                <File className="w-7 h-7 text-indigo-400" />
              </div>
              {/* Pulse ring */}
              <motion.div 
                animate={{ scale: [1, 1.5], opacity: [0.4, 0] }}
                transition={{ repeat: Infinity, duration: 1.5, ease: 'easeOut' }}
                className="absolute inset-0 rounded-full border-2 border-indigo-500/30"
              />
            </div>

            {/* Step-by-step pipeline readout */}
            <div className="w-full space-y-2 mb-8">
              {PIPELINE_STEPS.map((step, i) => {
                const Icon = step.icon;
                const isActive = i === currentStep;
                const isDone = i < currentStep;
                return (
                  <motion.div
                    key={i}
                    initial={{ opacity: 0, x: -10 }}
                    animate={{ opacity: i <= currentStep ? 1 : 0.25, x: 0 }}
                    transition={{ delay: i * 0.08, duration: 0.3 }}
                    className={`flex items-center gap-3 px-4 py-2.5 rounded-xl transition-all duration-300 ${
                      isActive ? 'bg-indigo-500/10 border border-indigo-500/20' : 
                      isDone ? 'bg-slate-800/30 border border-transparent' : 
                      'border border-transparent'
                    }`}
                  >
                    <div className="flex-shrink-0 w-6 h-6 flex items-center justify-center">
                      {isDone ? (
                        <CheckCircle2 className="w-5 h-5 text-emerald-400" />
                      ) : isActive ? (
                        <motion.div animate={{ rotate: 360 }} transition={{ repeat: Infinity, duration: 1, ease: 'linear' }}>
                          <Icon className="w-5 h-5 text-indigo-400" />
                        </motion.div>
                      ) : (
                        <Icon className="w-5 h-5 text-slate-600" />
                      )}
                    </div>
                    <div className="flex-1 min-w-0">
                      <p className={`text-sm font-medium truncate ${isActive ? 'text-indigo-300' : isDone ? 'text-slate-400' : 'text-slate-600'}`}>
                        {step.label}
                      </p>
                      {isActive && (
                        <motion.p
                          initial={{ opacity: 0, height: 0 }}
                          animate={{ opacity: 1, height: 'auto' }}
                          className="text-xs text-slate-500 mt-0.5"
                        >
                          {step.sublabel}
                        </motion.p>
                      )}
                    </div>
                  </motion.div>
                );
              })}
            </div>

            {/* Progress bar */}
            <div className="w-full h-1.5 bg-slate-800 rounded-full overflow-hidden">
              <motion.div
                className="h-full bg-gradient-to-r from-indigo-600 via-purple-500 to-indigo-600 rounded-full"
                initial={{ width: '0%' }}
                animate={{ width: `${progress}%` }}
                transition={{ duration: 0.4, ease: 'easeOut' }}
              />
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </motion.div>
  );
}
