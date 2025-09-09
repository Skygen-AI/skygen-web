import React from 'react';
import styles from './ShinyText.module.css';

interface ShinyTextProps {
  text: string;
  disabled?: boolean;
  speed?: number;
  className?: string;
  variant?: 'default' | 'thinking...';
}

const ShinyText = ({ text, disabled = false, speed = 1.7, className = '', variant = 'default' }: ShinyTextProps) => {
  const customStyle = speed !== 1.7 ? {
    '--shine-duration': `${speed}s`
  } as React.CSSProperties : {};

  const variantClass = variant === 'thinking...' ? styles.thinking : '';

  return (
    <span 
      className={`${styles.shinyText} ${variantClass} ${disabled ? styles.disabled : ''} ${className}`}
      style={customStyle}
    >
      {text}
    </span>
  );
};

export default ShinyText;