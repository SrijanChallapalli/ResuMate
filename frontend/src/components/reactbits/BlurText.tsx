/**
 * Blur Text Animation Component
 * Animated hero headline with blur-in effect
 */
import React, { useEffect, useState } from 'react'

interface BlurTextProps {
  text: string
  className?: string
  delay?: number
}

export const BlurText: React.FC<BlurTextProps> = ({ 
  text, 
  className = '', 
  delay = 0 
}) => {
  const [isVisible, setIsVisible] = useState(false)

  useEffect(() => {
    const timer = setTimeout(() => {
      setIsVisible(true)
    }, delay)
    return () => clearTimeout(timer)
  }, [delay])

  return (
    <span
      className={`inline-block transition-all duration-1000 ${
        isVisible
          ? 'blur-0 opacity-100'
          : 'blur-md opacity-0'
      } ${className}`}
    >
      {text}
    </span>
  )
}

