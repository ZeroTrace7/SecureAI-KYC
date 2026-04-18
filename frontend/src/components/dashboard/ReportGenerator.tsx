'use client';

import { useState } from 'react';
import { Download, Loader2 } from 'lucide-react';
import { useDocumentContext } from '@/context/DocumentContext';

/* ═══════════════════════════════════════════════════════════
   PDF Report Generator — Client-side using jsPDF
   ═══════════════════════════════════════════════════════════ */

interface AgentRow {
  name: string;
  status: 'PASS' | 'FAIL' | 'N/A';
  score: string;
  details: string;
}

function buildAgentRows(apiData: any): AgentRow[] {
  const rows: AgentRow[] = [];

  // 1. Integrity Validation (Quality Gate)
  rows.push({
    name: 'Integrity Validation',
    status: apiData?.quality_pass !== false ? 'PASS' : 'FAIL',
    score: '-',
    details: apiData?.quality_pass !== false
      ? 'Image passes all integrity checks.'
      : 'Image quality below threshold.',
  });

  // 2. Classification & OCR
  const docType = apiData?.document_type || 'unknown';
  rows.push({
    name: 'Classification & OCR',
    status: 'PASS',
    score: '-',
    details: `Identified as ${docType}. OCR extracted ${apiData?.ocr_line_count || 'N/A'} lines.`,
  });

  // 3. ELA Pixel Forensics
  const elaScore = apiData?.ela?.ela_score;
  rows.push({
    name: 'ELA Pixel Forensics',
    status: elaScore != null ? (elaScore > 0.35 ? 'FAIL' : 'PASS') : 'N/A',
    score: elaScore != null ? elaScore.toFixed(3) : '-',
    details: elaScore != null
      ? (elaScore > 0.35 ? 'Compression artifacts detected.' : 'No significant artifacts detected.')
      : 'Analysis not available.',
  });

  // 4. EXIF Metadata
  const exifFlag = apiData?.exif?.flag || apiData?.exif?.exif_flag;
  rows.push({
    name: 'EXIF Metadata',
    status: exifFlag === 'suspicious' ? 'FAIL' : exifFlag === 'notable' ? 'FAIL' : exifFlag ? 'PASS' : 'N/A',
    score: '-',
    details: exifFlag === 'suspicious'
      ? `Editing software detected: ${apiData?.exif?.software || 'unknown'}.`
      : exifFlag === 'notable'
      ? 'EXIF flag notable. No editing software signatures found.'
      : exifFlag === 'clean'
      ? 'EXIF metadata is clean.'
      : 'No EXIF data available.',
  });

  // 5. Deepfake Detection
  const dfScore = apiData?.deepfake?.deepfake_score;
  rows.push({
    name: 'Deepfake Detection',
    status: dfScore != null ? (dfScore > 0.5 ? 'FAIL' : 'PASS') : 'PASS',
    score: dfScore != null ? dfScore.toFixed(3) : '-',
    details: dfScore != null
      ? (dfScore > 0.5 ? 'Elevated artificiality score.' : 'No deepfake indicators.')
      : 'No face detected or analysis not triggered.',
  });

  // 6. ML Spatial Forgery
  const mlScore = apiData?.ml_forgery?.ml_forgery_score;
  rows.push({
    name: 'ML Spatial Forgery',
    status: mlScore != null ? (mlScore > 0.5 ? 'FAIL' : 'PASS') : 'N/A',
    score: mlScore != null ? mlScore.toFixed(3) : '-',
    details: mlScore != null ? 'ML residual analysis complete.' : 'ML forgery analysis not available or bypassed.',
  });

  // 7. QR Verification
  const hasQr = apiData?.qr?.has_qr;
  rows.push({
    name: 'QR Verification',
    status: hasQr ? 'PASS' : 'N/A',
    score: '-',
    details: hasQr ? 'QR code decoded and cross-validated.' : 'No QR code detected.',
  });

  // 8. Signature & Seal
  const sigSeal = apiData?.signature_seal || {};
  const ssScore = sigSeal?.signature_seal_score || 0;
  rows.push({
    name: 'Signature & Seal',
    status: ssScore > 0.25 ? 'FAIL' : 'PASS',
    score: ssScore.toFixed(3),
    details: ssScore > 0.25
      ? `Anomalies detected. Seal: ${sigSeal?.seal?.seal_found ? 'Found' : 'None'}. Sig: ${sigSeal?.signature?.signature_found ? 'Found' : 'None'}.`
      : `Seal: ${sigSeal?.seal?.seal_found ? 'Found' : 'None'}. Sig: ${sigSeal?.signature?.signature_found ? 'Found' : 'None'}. No irregularities.`,
  });

  // 9. Text Integrity
  const ti = apiData?.text_integrity || {};
  const tiScore = ti?.text_integrity_score || 0;
  const fontOk = ti?.font_analysis?.font_consistent !== false;
  const confOk = ti?.confidence_analysis?.confidence_consistent !== false;
  const layoutOk = ti?.spatial_analysis?.layout_consistent !== false;
  rows.push({
    name: 'Text Integrity',
    status: tiScore > 0.25 ? 'FAIL' : 'PASS',
    score: tiScore.toFixed(3),
    details: tiScore > 0.25
      ? `Font: ${fontOk ? 'OK' : 'Inconsistent'}, Confidence: ${confOk ? 'OK' : 'Variable'}, Layout: ${layoutOk ? 'OK' : 'Irregular'}.`
      : 'Font, confidence, and layout all consistent.',
  });

  // 10. Blockchain Ledger
  const bc = apiData?.blockchain || {};
  const bcSeen = bc?.previously_seen;
  const bcValid = bc?.chain_valid !== false;
  rows.push({
    name: 'Blockchain Ledger',
    status: bcValid && !(bcSeen && (bc?.blockchain_score || 0) > 0.5) ? 'PASS' : 'FAIL',
    score: '-',
    details: bcSeen
      ? `Previously registered. Chain: ${bcValid ? 'Valid' : 'Broken'}. Blocks: ${bc?.total_blocks || 0}.`
      : `First submission. Chain: ${bcValid ? 'Valid' : 'Broken'}. Blocks: ${bc?.total_blocks || 0}.`,
  });

  // 11. Structured Document Validation
  const sv = apiData?.structured_validation || {};
  const svScore = sv?.structured_validation_score;
  if (svScore != null && svScore !== undefined) {
    rows.push({
      name: 'Structured Validation',
      status: svScore >= 0.25 ? 'FAIL' : 'PASS',
      score: svScore.toFixed(3),
      details: svScore >= 0.25
        ? `Anomalies: ${(sv?.details || sv?.issues || []).slice(0, 2).join('; ') || 'format/arithmetic issues'}.`
        : 'All field-level checks passed.',
    });
  }

  return rows;
}

async function generatePDF(apiData: any, fileName: string) {
  const { jsPDF } = await import('jspdf');
  const doc = new jsPDF('p', 'mm', 'a4');
  const pageW = 210;
  const marginL = 18;
  const marginR = 18;
  const contentW = pageW - marginL - marginR;
  let y = 18;

  const decision = apiData?.decision || 'UNKNOWN';
  const score = apiData?.fraud_score || 0;
  const docType = (apiData?.document_type || 'unknown').toUpperCase();
  const explanation = apiData?.explanation || 'No AI reasoning available.';
  const timestamp = new Date().toLocaleString('en-IN', { 
    timeZone: 'Asia/Kolkata',
    year: 'numeric', month: '2-digit', day: '2-digit',
    hour: '2-digit', minute: '2-digit', second: '2-digit'
  });

  // ── Colors ──
  const darkBg: [number, number, number] = [15, 23, 42];
  const cardBg: [number, number, number] = [30, 41, 59];
  const accentBlue: [number, number, number] = [99, 102, 241];
  const green: [number, number, number] = [16, 185, 129];
  const red: [number, number, number] = [239, 68, 68];
  const amber: [number, number, number] = [245, 158, 11];
  const white: [number, number, number] = [241, 245, 249];
  const muted: [number, number, number] = [148, 163, 184];

  const verdictColor = decision === 'FORGED' || decision === 'REJECTED' ? red
    : decision === 'SUSPICIOUS' || decision === 'MANUAL_REVIEW' ? amber : green;

  // ── Page Background ──
  function drawBackground() {
    doc.setFillColor(...darkBg);
    doc.rect(0, 0, pageW, 297, 'F');
  }
  drawBackground();

  // ── Header ──
  doc.setFillColor(...accentBlue);
  doc.rect(0, 0, pageW, 38, 'F');
  doc.setFont('helvetica', 'bold');
  doc.setFontSize(20);
  doc.setTextColor(...white);
  doc.text('DOCUMENT VERIFICATION REPORT', marginL, 16);
  doc.setFontSize(10);
  doc.setFont('helvetica', 'normal');
  doc.setTextColor(200, 210, 230);
  doc.text('Satya KYC — SecureAI Intelligent Document Forensics', marginL, 24);
  doc.setFontSize(8);
  doc.text(`Generated: ${timestamp}`, marginL, 31);
  y = 46;

  // ── Document Info Card ──
  doc.setFillColor(...cardBg);
  doc.roundedRect(marginL, y, contentW, 28, 3, 3, 'F');
  doc.setFontSize(8);
  doc.setTextColor(...muted);
  doc.text('DOCUMENT', marginL + 6, y + 7);
  doc.text('TYPE', marginL + 6, y + 16);
  doc.text('REFERENCE', marginL + 100, y + 7);

  doc.setFontSize(10);
  doc.setTextColor(...white);
  doc.setFont('helvetica', 'bold');
  doc.text(fileName.length > 45 ? fileName.slice(0, 42) + '...' : fileName, marginL + 35, y + 7);
  doc.text(docType, marginL + 21, y + 16);

  // Reference ID
  const refId = `#${Math.floor(Math.random() * 9000 + 1000)}`;
  doc.text(refId, marginL + 122, y + 7);
  y += 34;

  // ── Score + Verdict Box ──
  const scoreBoxW = 55;
  const verdictBoxW = contentW - scoreBoxW - 4;
  
  // Score box
  doc.setFillColor(...cardBg);
  doc.roundedRect(marginL, y, scoreBoxW, 32, 3, 3, 'F');
  doc.setFontSize(8);
  doc.setTextColor(...muted);
  doc.text('FRAUD RISK SCORE', marginL + 6, y + 8);
  doc.setFontSize(26);
  doc.setFont('helvetica', 'bold');
  doc.setTextColor(...verdictColor);
  doc.text(`${score}`, marginL + 6, y + 25);
  doc.setFontSize(10);
  doc.setTextColor(...muted);
  doc.text('/ 100', marginL + 6 + doc.getTextWidth(`${score}`) + 2, y + 25);

  // Verdict box
  doc.setFillColor(verdictColor[0], verdictColor[1], verdictColor[2]);
  doc.roundedRect(marginL + scoreBoxW + 4, y, verdictBoxW, 32, 3, 3, 'F');
  doc.setFontSize(11);
  doc.setFont('helvetica', 'bold');
  doc.setTextColor(255, 255, 255);
  const verdictText = decision === 'FORGED' ? 'FORGED — Auto-Rejected'
    : decision === 'REJECTED' ? 'REJECTED — Invalid Document'
    : decision === 'SUSPICIOUS' ? 'SUSPICIOUS — Needs Review'
    : decision === 'MANUAL_REVIEW' ? 'MANUAL REVIEW Required'
    : 'GENUINE — Verified';
  doc.text(verdictText, marginL + scoreBoxW + 12, y + 14);
  doc.setFontSize(8);
  doc.setFont('helvetica', 'normal');
  doc.setTextColor(255, 255, 255);
  doc.text('Automated forensic analysis verdict', marginL + scoreBoxW + 12, y + 22);
  y += 38;

  // ── Agent Breakdown Table ──
  doc.setFontSize(9);
  doc.setFont('helvetica', 'bold');
  doc.setTextColor(...accentBlue);
  doc.text('AGENT ANALYSIS BREAKDOWN', marginL, y);
  y += 5;

  // Table header
  doc.setFillColor(51, 65, 85);
  doc.roundedRect(marginL, y, contentW, 7, 1.5, 1.5, 'F');
  doc.setFontSize(7);
  doc.setFont('helvetica', 'bold');
  doc.setTextColor(...white);
  doc.text('#', marginL + 3, y + 5);
  doc.text('AGENT', marginL + 10, y + 5);
  doc.text('STATUS', marginL + 80, y + 5);
  doc.text('SCORE', marginL + 102, y + 5);
  doc.text('DETAILS', marginL + 120, y + 5);
  y += 9;

  const agentRows = buildAgentRows(apiData);
  agentRows.forEach((row, i) => {
    // Check if we need a new page
    if (y > 270) {
      doc.addPage();
      drawBackground();
      y = 18;
    }

    // Alternating row bg
    if (i % 2 === 0) {
      doc.setFillColor(30, 41, 59);
    } else {
      doc.setFillColor(22, 33, 50);
    }
    doc.roundedRect(marginL, y, contentW, 8, 0.5, 0.5, 'F');

    // Status indicator dot
    const statusColor = row.status === 'PASS' ? green : row.status === 'FAIL' ? red : muted;
    doc.setFillColor(...statusColor);
    doc.circle(marginL + 82.5, y + 4, 1.5, 'F');

    doc.setFontSize(7);
    doc.setFont('helvetica', 'normal');
    doc.setTextColor(...muted);
    doc.text(`${i + 1}`, marginL + 3, y + 5.5);

    doc.setTextColor(...white);
    doc.setFont('helvetica', 'bold');
    doc.text(row.name, marginL + 10, y + 5.5);

    doc.setFont('helvetica', 'normal');
    doc.setTextColor(...statusColor);
    doc.text(row.status, marginL + 86, y + 5.5);

    doc.setTextColor(...muted);
    doc.text(row.score, marginL + 102, y + 5.5);

    // Details (truncated to fit)
    doc.setFontSize(6);
    doc.setTextColor(120, 140, 170);
    const maxDetailsW = contentW - 122;
    const truncDetails = doc.splitTextToSize(row.details, maxDetailsW)[0] || '';
    doc.text(truncDetails, marginL + 120, y + 5.5);

    y += 9;
  });

  y += 4;

  // ── Cross-Validation Section ──
  if (y > 250) { doc.addPage(); drawBackground(); y = 18; }
  doc.setFontSize(9);
  doc.setFont('helvetica', 'bold');
  doc.setTextColor(...accentBlue);
  doc.text('CROSS-VALIDATION: OCR ↔ QR DATA', marginL, y);
  y += 5;

  doc.setFillColor(...cardBg);
  doc.roundedRect(marginL, y, contentW, 16, 2, 2, 'F');
  doc.setFontSize(7);
  doc.setFont('helvetica', 'normal');
  doc.setTextColor(...muted);
  const ocrName = apiData?.ocr_fields?.name || 'N/A';
  const qrName = apiData?.qr?.qr_name || 'N/A';
  const simScore = apiData?.cross_validation?.name_similarity || 'N/A';
  const qrFound = apiData?.qr?.has_qr ? 'Yes' : 'No';
  doc.text(`OCR Name: ${ocrName}`, marginL + 5, y + 6);
  doc.text(`QR Name: ${qrName}`, marginL + 60, y + 6);
  doc.text(`Similarity: ${simScore}%`, marginL + 115, y + 6);
  doc.text(`QR Found: ${qrFound}`, marginL + 150, y + 6);
  y += 22;

  // ── AI Reasoning Section ──
  if (y > 240) { doc.addPage(); drawBackground(); y = 18; }
  doc.setFontSize(9);
  doc.setFont('helvetica', 'bold');
  doc.setTextColor(...accentBlue);
  doc.text('AI REASONING', marginL, y);
  y += 5;

  doc.setFillColor(...cardBg);
  const explLines = doc.splitTextToSize(explanation, contentW - 10);
  const explH = Math.max(16, explLines.length * 4 + 8);
  doc.roundedRect(marginL, y, contentW, explH, 2, 2, 'F');
  doc.setFontSize(7.5);
  doc.setFont('helvetica', 'normal');
  doc.setTextColor(180, 195, 215);
  doc.text(explLines, marginL + 5, y + 6);
  y += explH + 6;

  // ── Compliance Footer ──
  if (y > 265) { doc.addPage(); drawBackground(); y = 18; }
  doc.setDrawColor(51, 65, 85);
  doc.line(marginL, y, pageW - marginR, y);
  y += 5;
  doc.setFontSize(6.5);
  doc.setFont('helvetica', 'normal');
  doc.setTextColor(100, 116, 139);
  doc.text('REGULATORY REFERENCE', marginL, y);
  y += 4;
  doc.setFontSize(6);
  doc.text('RBI KYC Master Direction 2016 (updated 2024) — Sections 16, 38(c), 56', marginL, y);
  y += 3;
  doc.text('Section 16: Regulated entities must maintain records of rejection reasons.', marginL, y);
  y += 3;
  doc.text('Section 38(c): Document integrity failure constitutes valid grounds for rejection.', marginL, y);
  y += 3;
  doc.text('Section 56: Every CDD decision must be auditable with specific justification.', marginL, y);
  y += 5;
  doc.setDrawColor(51, 65, 85);
  doc.line(marginL, y, pageW - marginR, y);
  y += 4;
  doc.setFontSize(6);
  doc.setTextColor(80, 96, 119);
  doc.text('This report is generated by Satya KYC — SecureAI Intelligent Document Verification System.', marginL, y);
  y += 3;
  doc.text('For internal compliance use only. Not intended for external distribution.', marginL, y);
  y += 3;
  doc.text(`Report ID: RPT-${Date.now().toString(36).toUpperCase()} | ${timestamp}`, marginL, y);

  // ── Save ──
  const safeName = fileName.replace(/\.[^.]+$/, '').replace(/[^a-zA-Z0-9_-]/g, '_');
  doc.save(`SatyaKYC_Report_${safeName}.pdf`);
}


/* ═══════════════════════════════════════════════════════════
   Download Report Button Component
   ═══════════════════════════════════════════════════════════ */
export default function ReportGenerator() {
  const { apiResult, file, resultReady } = useDocumentContext();
  const [generating, setGenerating] = useState(false);

  if (!resultReady || !apiResult) return null;

  const handleDownload = async () => {
    setGenerating(true);
    try {
      await generatePDF(apiResult, file?.name || 'document');
    } catch (err) {
      console.error('PDF generation failed:', err);
    }
    setGenerating(false);
  };

  return (
    <button
      id="download-report-btn"
      onClick={handleDownload}
      disabled={generating}
      className="w-full flex items-center justify-center gap-2.5 px-4 py-3 rounded-xl text-sm font-semibold transition-all duration-200 disabled:opacity-50 disabled:cursor-not-allowed"
      style={{
        background: 'linear-gradient(135deg, rgba(249, 115, 22, 0.08) 0%, rgba(239, 68, 68, 0.08) 100%)',
        border: '1px solid rgba(249, 115, 22, 0.3)',
        color: '#c2410c',
      }}
      onMouseEnter={(e) => {
        (e.target as HTMLButtonElement).style.background = 'linear-gradient(135deg, rgba(249, 115, 22, 0.15) 0%, rgba(239, 68, 68, 0.15) 100%)';
        (e.target as HTMLButtonElement).style.borderColor = 'rgba(249, 115, 22, 0.5)';
      }}
      onMouseLeave={(e) => {
        (e.target as HTMLButtonElement).style.background = 'linear-gradient(135deg, rgba(249, 115, 22, 0.08) 0%, rgba(239, 68, 68, 0.08) 100%)';
        (e.target as HTMLButtonElement).style.borderColor = 'rgba(249, 115, 22, 0.3)';
      }}
    >
      {generating ? (
        <>
          <Loader2 className="w-4 h-4 animate-spin" />
          Generating Report...
        </>
      ) : (
        <>
          <Download className="w-4 h-4" />
          Download Report
        </>
      )}
    </button>
  );
}
