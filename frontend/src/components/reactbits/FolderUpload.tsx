/**
 * Folder Upload Component
 * Premium drag-and-drop file upload with folder-like UI
 */
import React, { useCallback, useState, useRef } from 'react'

interface FolderUploadProps {
  onFileSelect: (file: File) => void
  uploadedFile: File | null
  onRemove: () => void
  uploading?: boolean
  acceptedTypes?: string[]
  maxSizeMB?: number
}

export const FolderUpload: React.FC<FolderUploadProps> = ({
  onFileSelect,
  uploadedFile,
  onRemove,
  uploading = false,
  acceptedTypes = ['.pdf', '.docx', '.txt'],
  maxSizeMB = 5,
}) => {
  const [isDragging, setIsDragging] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const fileInputRef = useRef<HTMLInputElement>(null)

  const validateFile = (file: File): string | null => {
    const fileExt = '.' + file.name.split('.').pop()?.toLowerCase()
    if (!acceptedTypes.includes(fileExt)) {
      return `Unsupported file type. Allowed: ${acceptedTypes.join(', ')}`
    }
    if (file.size > maxSizeMB * 1024 * 1024) {
      return `File too large. Maximum size: ${maxSizeMB}MB`
    }
    return null
  }

  const handleFile = useCallback(
    (file: File) => {
      const validationError = validateFile(file)
      if (validationError) {
        setError(validationError)
        return
      }
      setError(null)
      onFileSelect(file)
    },
    [onFileSelect, acceptedTypes, maxSizeMB]
  )

  const handleDragOver = useCallback((e: React.DragEvent) => {
    e.preventDefault()
    setIsDragging(true)
  }, [])

  const handleDragLeave = useCallback((e: React.DragEvent) => {
    e.preventDefault()
    setIsDragging(false)
  }, [])

  const handleDrop = useCallback(
    (e: React.DragEvent) => {
      e.preventDefault()
      setIsDragging(false)
      const file = e.dataTransfer.files[0]
      if (file) {
        handleFile(file)
      }
    },
    [handleFile]
  )

  const handleFileInput = useCallback(
    (e: React.ChangeEvent<HTMLInputElement>) => {
      const file = e.target.files?.[0]
      if (file) {
        handleFile(file)
      }
    },
    [handleFile]
  )

  if (uploadedFile) {
    return (
      <div className="bg-white dark:bg-slate-800 rounded-2xl shadow-xl p-6 border border-gray-200 dark:border-slate-700">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-4">
            <div className="p-3 bg-blue-100 dark:bg-blue-900/30 rounded-xl">
              <svg
                className="w-8 h-8 text-blue-600 dark:text-blue-400"
                fill="none"
                viewBox="0 0 24 24"
                stroke="currentColor"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"
                />
              </svg>
            </div>
            <div>
              <p className="font-semibold text-gray-900 dark:text-slate-100">
                {uploadedFile.name}
              </p>
              <p className="text-sm text-gray-500 dark:text-slate-400">
                {(uploadedFile.size / 1024).toFixed(1)} KB
                {uploading && ' • Uploading...'}
              </p>
            </div>
          </div>
          <button
            onClick={onRemove}
            className="px-4 py-2 text-red-600 dark:text-red-400 hover:bg-red-50 dark:hover:bg-red-900/20 rounded-lg transition-colors font-medium"
          >
            Remove
          </button>
        </div>
      </div>
    )
  }

  return (
    <div>
      <div
        onDragOver={handleDragOver}
        onDragLeave={handleDragLeave}
        onDrop={handleDrop}
        className={`relative border-2 border-dashed rounded-2xl p-12 text-center transition-all duration-300 ${
          isDragging
            ? 'border-blue-500 bg-blue-50 dark:bg-blue-900/20 scale-[1.02] shadow-xl'
            : 'border-gray-300 dark:border-slate-600 bg-white dark:bg-slate-800 hover:border-blue-400 dark:hover:border-blue-500 hover:bg-blue-50/50 dark:hover:bg-blue-900/10'
        }`}
      >
        {/* Folder icon */}
        <div className="mb-6 flex justify-center">
          <div
            className={`p-6 rounded-2xl transition-all duration-300 ${
              isDragging
                ? 'bg-blue-100 dark:bg-blue-900/30 scale-110'
                : 'bg-gray-100 dark:bg-slate-700'
            }`}
          >
            <svg
              className={`w-16 h-16 transition-colors ${
                isDragging
                  ? 'text-blue-600 dark:text-blue-400'
                  : 'text-gray-400 dark:text-slate-500'
              }`}
              fill="none"
              viewBox="0 0 24 24"
              stroke="currentColor"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={1.5}
                d="M3 7v10a2 2 0 002 2h14a2 2 0 002-2V9a2 2 0 00-2-2h-6l-2-2H5a2 2 0 00-2 2z"
              />
            </svg>
          </div>
        </div>

        <h3 className="text-xl font-semibold text-gray-900 dark:text-slate-100 mb-2">
          {isDragging ? 'Drop your resume here' : 'Drop your resume here'}
        </h3>
        <p className="text-gray-600 dark:text-slate-400 mb-6">
          Supports {acceptedTypes.join(', ').toUpperCase()} files (max {maxSizeMB}MB)
        </p>

        <button
          type="button"
          onClick={() => {
            fileInputRef.current?.click()
          }}
          className="px-8 py-3 bg-gradient-to-r from-blue-600 to-indigo-600 hover:from-blue-700 hover:to-indigo-700 text-white font-semibold rounded-xl shadow-lg transition-all hover:shadow-xl transform hover:scale-105 cursor-pointer"
        >
          Choose File
        </button>
        <input
          ref={fileInputRef}
          type="file"
          accept={acceptedTypes.join(',')}
          onChange={handleFileInput}
          className="hidden"
        />
      </div>

      {error && (
        <div className="mt-4 p-4 bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg">
          <p className="text-sm text-red-700 dark:text-red-400">{error}</p>
        </div>
      )}
    </div>
  )
}

