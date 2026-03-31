'use client';

import React, { createContext, useContext, useState, ReactNode } from 'react';

interface DocumentContextType {
  file: File | null;
  setFile: (file: File | null) => void;
  preview: string | null;
  setPreview: (preview: string | null) => void;
  apiResult: any;
  setApiResult: (result: any) => void;
  resultReady: boolean;
  setResultReady: (ready: boolean) => void;
  analyzing: boolean;
  setAnalyzing: (analyzing: boolean) => void;
  currentStep: number;
  setCurrentStep: (step: number) => void;
  docType: string;
  setDocType: (type: string) => void;
}

const DocumentContext = createContext<DocumentContextType | undefined>(undefined);

export function DocumentProvider({ children }: { children: ReactNode }) {
  const [file, setFile] = useState<File | null>(null);
  const [preview, setPreview] = useState<string | null>(null);
  const [apiResult, setApiResult] = useState<any>(null);
  const [resultReady, setResultReady] = useState(false);
  const [analyzing, setAnalyzing] = useState(false);
  const [currentStep, setCurrentStep] = useState(0);
  const [docType, setDocType] = useState('auto');

  return (
    <DocumentContext.Provider value={{
      file, setFile,
      preview, setPreview,
      apiResult, setApiResult,
      resultReady, setResultReady,
      analyzing, setAnalyzing,
      currentStep, setCurrentStep,
      docType, setDocType
    }}>
      {children}
    </DocumentContext.Provider>
  );
}

export function useDocumentContext() {
  const context = useContext(DocumentContext);
  if (context === undefined) {
    throw new Error('useDocumentContext must be used within a DocumentProvider');
  }
  return context;
}
