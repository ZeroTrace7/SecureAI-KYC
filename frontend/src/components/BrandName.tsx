'use client';

import { useEffect, useState } from 'react';

interface BrandNameProps {
  className?: string;
  wrapperClassName?: string;
}

/**
 * Crossfades between English "Satya KYC" and Hindi "सत्य KYC"
 * every 3 seconds — no 3-D flip, so text stays crisp the whole time.
 */
export default function BrandName({ className = '', wrapperClassName = '' }: BrandNameProps) {
  const [showHindi, setShowHindi] = useState(false);

  useEffect(() => {
    const interval = setInterval(() => setShowHindi((p) => !p), 3000);
    return () => clearInterval(interval);
  }, []);

  return (
    <span className={`brand-name-wrapper ${wrapperClassName}`} style={{ display: 'inline-block', position: 'relative' }}>
      {/* English */}
      <span
        className={`brand-label ${className}`}
        style={{
          display: 'inline-block',
          transition: 'opacity 0.55s ease, transform 0.55s cubic-bezier(0.22,1,0.36,1)',
          opacity: showHindi ? 0 : 1,
          transform: showHindi ? 'translateY(-6px)' : 'translateY(0)',
          pointerEvents: showHindi ? 'none' : 'auto',
        }}
      >
        Satya KYC
      </span>

      {/* Hindi — absolutely stacked on top */}
      <span
        className={`brand-label ${className}`}
        lang="hi"
        style={{
          position: 'absolute',
          left: 0,
          top: 0,
          whiteSpace: 'nowrap',
          display: 'inline-block',
          transition: 'opacity 0.55s ease, transform 0.55s cubic-bezier(0.22,1,0.36,1)',
          opacity: showHindi ? 1 : 0,
          transform: showHindi ? 'translateY(0)' : 'translateY(6px)',
          pointerEvents: showHindi ? 'auto' : 'none',
        }}
      >
        सत्य KYC
      </span>
    </span>
  );
}
