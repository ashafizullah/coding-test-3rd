'use client'

import { useState, useCallback, useEffect, useRef } from 'react'
import { useDropzone } from 'react-dropzone'
import { useQueryClient } from '@tanstack/react-query'
import { Upload, CheckCircle, XCircle, Loader2, Plus, FolderOpen } from 'lucide-react'
import { documentApi, fundApi } from '@/lib/api'

interface Fund {
  id: number
  name: string
  gp_name: string
  fund_type: string
  vintage_year: number
}

export default function UploadPage() {
  const queryClient = useQueryClient()
  const [uploading, setUploading] = useState(false)
  const [uploadStatus, setUploadStatus] = useState<{
    status: 'idle' | 'uploading' | 'processing' | 'success' | 'error'
    message?: string
    documentId?: number
  }>({ status: 'idle' })

  // Fund selection state
  const [funds, setFunds] = useState<Fund[]>([])
  const [loadingFunds, setLoadingFunds] = useState(true)
  const [fundMode, setFundMode] = useState<'existing' | 'new'>('existing')
  const [selectedFundId, setSelectedFundId] = useState<number | null>(null)

  // Use ref to always have the latest selectedFundId
  const selectedFundIdRef = useRef<number | null>(null)

  // Update ref whenever selectedFundId changes
  useEffect(() => {
    selectedFundIdRef.current = selectedFundId
  }, [selectedFundId])

  // New fund form state
  const [newFund, setNewFund] = useState({
    name: '',
    gp_name: '',
    fund_type: 'Venture Capital',
    vintage_year: new Date().getFullYear()
  })
  const [creatingFund, setCreatingFund] = useState(false)

  // Fetch existing funds on mount
  useEffect(() => {
    const fetchFunds = async () => {
      try {
        const data = await fundApi.list()
        setFunds(data)
        // Select first fund by default if exists
        if (data.length > 0) {
          setSelectedFundId(data[0].id)
        }
      } catch (error) {
        console.error('Error fetching funds:', error)
      } finally {
        setLoadingFunds(false)
      }
    }

    fetchFunds()
  }, [])

  const handleCreateFund = async () => {
    if (!newFund.name.trim()) {
      alert('Please enter a fund name')
      return
    }

    setCreatingFund(true)
    try {
      const createdFund = await fundApi.create(newFund)
      setFunds([...funds, createdFund])
      setSelectedFundId(createdFund.id)

      // Invalidate React Query cache so funds page will refetch
      queryClient.invalidateQueries({ queryKey: ['funds'] })

      // Reset form
      setNewFund({
        name: '',
        gp_name: '',
        fund_type: 'Venture Capital',
        vintage_year: new Date().getFullYear()
      })

      // Switch to existing fund tab and show success message
      setFundMode('existing')
      setUploadStatus({
        status: 'success',
        message: `Fund "${createdFund.name}" created successfully! You can now upload documents.`
      })
    } catch (error: any) {
      alert(error.response?.data?.detail || 'Failed to create fund')
    } finally {
      setCreatingFund(false)
    }
  }

  // Clear upload status when switching tabs
  const handleTabSwitch = (mode: 'existing' | 'new') => {
    setFundMode(mode)
    setUploadStatus({ status: 'idle' })
  }

  const pollDocumentStatus = async (documentId: number) => {
    const maxAttempts = 60 // 5 minutes max
    let attempts = 0

    const poll = async () => {
      try {
        const status = await documentApi.getStatus(documentId)

        if (status.status === 'completed') {
          setUploadStatus({
            status: 'success',
            message: 'Document processed successfully!',
            documentId
          })
          setUploading(false)
        } else if (status.status === 'failed') {
          setUploadStatus({
            status: 'error',
            message: status.error_message || 'Processing failed',
            documentId
          })
          setUploading(false)
        } else if (attempts < maxAttempts) {
          attempts++
          setTimeout(poll, 5000) // Poll every 5 seconds
        } else {
          setUploadStatus({
            status: 'error',
            message: 'Processing timeout',
            documentId
          })
          setUploading(false)
        }
      } catch (error) {
        setUploadStatus({
          status: 'error',
          message: 'Failed to check status',
          documentId
        })
        setUploading(false)
      }
    }

    poll()
  }

  const onDrop = useCallback(async (acceptedFiles: File[]) => {
    if (acceptedFiles.length === 0) return

    const file = acceptedFiles[0]

    // Get the current selectedFundId from ref (always up-to-date)
    const currentFundId = selectedFundIdRef.current

    setUploading(true)
    setUploadStatus({ status: 'uploading', message: 'Uploading file...' })

    try {
      const result = await documentApi.upload(file, currentFundId || undefined)

      setUploadStatus({
        status: 'processing',
        message: 'File uploaded. Processing document...',
        documentId: result.document_id
      })

      // Poll for status
      pollDocumentStatus(result.document_id)

    } catch (error: any) {
      setUploadStatus({
        status: 'error',
        message: error.response?.data?.detail || 'Upload failed'
      })
      setUploading(false)
    }
  }, [])

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: {
      'application/pdf': ['.pdf']
    },
    maxFiles: 1,
    disabled: uploading
  })

  return (
    <div className="max-w-4xl mx-auto">
      <div className="mb-8">
        <h1 className="text-4xl font-bold mb-2">
          {fundMode === 'existing' ? 'Upload Fund Document' : 'Create New Fund'}
        </h1>
        <p className="text-gray-600">
          {fundMode === 'existing'
            ? 'Select a fund and upload a PDF performance report to automatically extract and analyze data'
            : 'Create a new fund to start tracking its performance'
          }
        </p>
      </div>

      {/* Fund Selection/Creation */}
      <div className="bg-white rounded-lg shadow-md p-6 mb-6">
        <h2 className="text-lg font-semibold mb-4">Select or Create Fund</h2>

        {/* Mode Toggle */}
        <div className="flex gap-2 mb-4">
          <button
            onClick={() => handleTabSwitch('existing')}
            className={`flex-1 py-2 px-4 rounded-md font-medium transition ${
              fundMode === 'existing'
                ? 'bg-blue-600 text-white'
                : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
            }`}
          >
            <FolderOpen className="w-4 h-4 inline mr-2" />
            Existing Fund
          </button>
          <button
            onClick={() => handleTabSwitch('new')}
            className={`flex-1 py-2 px-4 rounded-md font-medium transition ${
              fundMode === 'new'
                ? 'bg-blue-600 text-white'
                : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
            }`}
          >
            <Plus className="w-4 h-4 inline mr-2" />
            Create New Fund
          </button>
        </div>

        {/* Existing Fund Selection */}
        {fundMode === 'existing' && (
          <div>
            {loadingFunds ? (
              <div className="flex items-center justify-center py-4">
                <Loader2 className="w-5 h-5 animate-spin text-gray-400" />
                <span className="ml-2 text-gray-600">Loading funds...</span>
              </div>
            ) : funds.length === 0 ? (
              <div className="text-center py-4 text-gray-600">
                No funds available. Create a new fund to get started.
              </div>
            ) : (
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Select Fund
                </label>
                <select
                  value={selectedFundId || ''}
                  onChange={(e) => setSelectedFundId(Number(e.target.value))}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                >
                  {funds.map((fund) => (
                    <option key={fund.id} value={fund.id}>
                      {fund.name} ({fund.gp_name}) - {fund.vintage_year}
                    </option>
                  ))}
                </select>
              </div>
            )}
          </div>
        )}

        {/* New Fund Form */}
        {fundMode === 'new' && (
          <div className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Fund Name *
              </label>
              <input
                type="text"
                value={newFund.name}
                onChange={(e) => setNewFund({ ...newFund, name: e.target.value })}
                placeholder="e.g., Tech Ventures Fund II"
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                GP Name
              </label>
              <input
                type="text"
                value={newFund.gp_name}
                onChange={(e) => setNewFund({ ...newFund, gp_name: e.target.value })}
                placeholder="e.g., Acme Capital Partners"
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
              />
            </div>

            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Fund Type
                </label>
                <select
                  value={newFund.fund_type}
                  onChange={(e) => setNewFund({ ...newFund, fund_type: e.target.value })}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                >
                  <option value="Venture Capital">Venture Capital</option>
                  <option value="Private Equity">Private Equity</option>
                  <option value="Growth Equity">Growth Equity</option>
                  <option value="Real Estate">Real Estate</option>
                  <option value="Hedge Fund">Hedge Fund</option>
                  <option value="Other">Other</option>
                </select>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Vintage Year
                </label>
                <input
                  type="number"
                  value={newFund.vintage_year}
                  onChange={(e) => setNewFund({ ...newFund, vintage_year: Number(e.target.value) })}
                  min="2000"
                  max="2099"
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                />
              </div>
            </div>

            <button
              onClick={handleCreateFund}
              disabled={creatingFund || !newFund.name.trim()}
              className="w-full py-2 px-4 bg-blue-600 text-white rounded-md hover:bg-blue-700 transition disabled:opacity-50 disabled:cursor-not-allowed font-medium"
            >
              {creatingFund ? (
                <>
                  <Loader2 className="w-4 h-4 inline mr-2 animate-spin" />
                  Creating Fund...
                </>
              ) : (
                'Create Fund'
              )}
            </button>
          </div>
        )}
      </div>

      {/* Upload Area - Only show in Existing Fund mode */}
      {fundMode === 'existing' && (
        <div
          {...getRootProps()}
          className={`
            border-2 border-dashed rounded-lg p-12 text-center cursor-pointer transition
            ${isDragActive ? 'border-blue-500 bg-blue-50' : 'border-gray-300 hover:border-gray-400'}
            ${uploading ? 'opacity-50 cursor-not-allowed' : ''}
            ${!selectedFundId ? 'opacity-50 cursor-not-allowed' : ''}
          `}
        >
          <input {...getInputProps()} />

          <div className="flex flex-col items-center">
            <Upload className="w-16 h-16 text-gray-400 mb-4" />

            {isDragActive ? (
              <p className="text-lg text-blue-600 font-medium">Drop the file here...</p>
            ) : (
              <>
                <p className="text-lg font-medium mb-2">
                  Drag & drop a PDF file here, or click to select
                </p>
                <p className="text-sm text-gray-500">
                  Maximum file size: 50MB
                </p>
                {!selectedFundId && (
                  <p className="text-sm text-orange-600 mt-2">
                    Please select a fund before uploading
                  </p>
                )}
              </>
            )}
          </div>
        </div>
      )}

      {/* Status Display */}
      {uploadStatus.status !== 'idle' && (
        <div className="mt-8">
          <div className={`
            rounded-lg p-6 border
            ${uploadStatus.status === 'success' ? 'bg-green-50 border-green-200' : ''}
            ${uploadStatus.status === 'error' ? 'bg-red-50 border-red-200' : ''}
            ${uploadStatus.status === 'uploading' || uploadStatus.status === 'processing' ? 'bg-blue-50 border-blue-200' : ''}
          `}>
            <div className="flex items-start">
              <div className="flex-shrink-0">
                {uploadStatus.status === 'success' && (
                  <CheckCircle className="w-6 h-6 text-green-600" />
                )}
                {uploadStatus.status === 'error' && (
                  <XCircle className="w-6 h-6 text-red-600" />
                )}
                {(uploadStatus.status === 'uploading' || uploadStatus.status === 'processing') && (
                  <Loader2 className="w-6 h-6 text-blue-600 animate-spin" />
                )}
              </div>

              <div className="ml-4 flex-1">
                <h3 className={`
                  font-medium
                  ${uploadStatus.status === 'success' ? 'text-green-900' : ''}
                  ${uploadStatus.status === 'error' ? 'text-red-900' : ''}
                  ${uploadStatus.status === 'uploading' || uploadStatus.status === 'processing' ? 'text-blue-900' : ''}
                `}>
                  {uploadStatus.status === 'uploading' && 'Uploading...'}
                  {uploadStatus.status === 'processing' && 'Processing...'}
                  {uploadStatus.status === 'success' && 'Success!'}
                  {uploadStatus.status === 'error' && 'Error'}
                </h3>

                <p className={`
                  mt-1 text-sm
                  ${uploadStatus.status === 'success' ? 'text-green-700' : ''}
                  ${uploadStatus.status === 'error' ? 'text-red-700' : ''}
                  ${uploadStatus.status === 'uploading' || uploadStatus.status === 'processing' ? 'text-blue-700' : ''}
                `}>
                  {uploadStatus.message}
                </p>

                {uploadStatus.status === 'success' && (
                  <div className="mt-4 flex gap-3">
                    <a
                      href="/chat"
                      className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 transition text-sm"
                    >
                      Start Asking Questions
                    </a>
                    <a
                      href="/funds"
                      className="px-4 py-2 bg-white border border-gray-300 text-gray-700 rounded-md hover:bg-gray-50 transition text-sm"
                    >
                      View Fund Dashboard
                    </a>
                  </div>
                )}
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Instructions */}
      <div className="mt-12 bg-white rounded-lg shadow-md p-6">
        <h2 className="text-xl font-semibold mb-4">What happens after upload?</h2>
        <div className="space-y-4">
          <Step
            number="1"
            title="Document Parsing"
            description="The system extracts document structure, identifying tables and text sections."
          />
          <Step
            number="2"
            title="Data Extraction"
            description="Tables containing capital calls, distributions, and adjustments are parsed and stored in the database."
          />
          <Step
            number="3"
            title="Vector Embedding"
            description="Text content is chunked and embedded for semantic search, enabling natural language queries."
          />
          <Step
            number="4"
            title="Ready to Query"
            description="Once processing is complete, you can ask questions about the fund using the chat interface."
          />
        </div>
      </div>
    </div>
  )
}

function Step({ number, title, description }: {
  number: string
  title: string
  description: string
}) {
  return (
    <div className="flex items-start">
      <div className="flex-shrink-0 w-8 h-8 bg-blue-100 text-blue-600 rounded-full flex items-center justify-center font-semibold text-sm">
        {number}
      </div>
      <div className="ml-4">
        <h3 className="font-medium text-gray-900">{title}</h3>
        <p className="text-sm text-gray-600 mt-1">{description}</p>
      </div>
    </div>
  )
}
