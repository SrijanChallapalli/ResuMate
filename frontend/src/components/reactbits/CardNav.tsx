/**
 * Card Navigation Component
 * 3-step flow indicator with animated progress
 */
import React from 'react'

interface Step {
  number: number
  title: string
  description: string
}

interface CardNavProps {
  steps: Step[]
  currentStep?: number
}

export const CardNav: React.FC<CardNavProps> = ({ steps, currentStep = 1 }) => {
  return (
    <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-12">
      {steps.map((step, index) => {
        const isActive = step.number === currentStep
        const isCompleted = step.number < currentStep
        
        return (
          <div
            key={step.number}
            className={`relative p-6 rounded-xl border-2 transition-all duration-300 ${
              isActive
                ? 'border-blue-500 bg-blue-50 dark:bg-blue-900/20 shadow-lg scale-105'
                : isCompleted
                ? 'border-green-300 bg-green-50 dark:bg-green-900/20'
                : 'border-gray-200 bg-white dark:bg-slate-800 dark:border-slate-700'
            }`}
          >
            {/* Step number badge */}
            <div
              className={`absolute -top-4 -left-4 w-10 h-10 rounded-full flex items-center justify-center font-bold text-sm transition-all duration-300 ${
                isActive
                  ? 'bg-blue-500 text-white shadow-lg scale-110'
                  : isCompleted
                  ? 'bg-green-500 text-white'
                  : 'bg-gray-300 text-gray-600 dark:bg-slate-700 dark:text-slate-300'
              }`}
            >
              {isCompleted ? '✓' : step.number}
            </div>
            
            <h3
              className={`text-lg font-semibold mb-2 mt-2 ${
                isActive
                  ? 'text-blue-900 dark:text-blue-100'
                  : isCompleted
                  ? 'text-green-900 dark:text-green-100'
                  : 'text-gray-700 dark:text-slate-300'
              }`}
            >
              {step.title}
            </h3>
            <p className="text-sm text-gray-600 dark:text-slate-400">
              {step.description}
            </p>
            
            {/* Progress line */}
            {index < steps.length - 1 && (
              <div className="hidden md:block absolute top-1/2 -right-3 w-6 h-0.5 bg-gray-200 dark:bg-slate-700">
                <div
                  className={`h-full transition-all duration-500 ${
                    isCompleted ? 'bg-green-500 w-full' : 'bg-gray-300 w-0'
                  }`}
                />
              </div>
            )}
          </div>
        )
      })}
    </div>
  )
}

