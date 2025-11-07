'use client'

import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import Link from 'next/link'
import Swal from 'sweetalert2'
import { fundApi } from '@/lib/api'
import { formatCurrency, formatPercentage } from '@/lib/utils'
import { TrendingUp, TrendingDown, ArrowRight, Loader2, Trash2 } from 'lucide-react'

export default function FundsPage() {
  const queryClient = useQueryClient()
  const { data: funds, isLoading, error } = useQuery({
    queryKey: ['funds'],
    queryFn: () => fundApi.list()
  })

  const deleteMutation = useMutation({
    mutationFn: (fundId: number) => fundApi.delete(fundId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['funds'] })
      Swal.fire({
        icon: 'success',
        title: 'Deleted!',
        text: 'Fund has been deleted successfully.',
        timer: 2000,
        showConfirmButton: false
      })
    },
    onError: (error: any) => {
      Swal.fire({
        icon: 'error',
        title: 'Error',
        text: error.response?.data?.detail || 'Failed to delete fund'
      })
    }
  })

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <Loader2 className="w-8 h-8 animate-spin text-blue-600" />
      </div>
    )
  }

  if (error) {
    return (
      <div className="bg-red-50 border border-red-200 rounded-lg p-4">
        <p className="text-red-800">Error loading funds: {(error as Error).message}</p>
      </div>
    )
  }

  return (
    <div className="max-w-7xl mx-auto">
      <div className="mb-8 flex items-center justify-between">
        <div>
          <h1 className="text-4xl font-bold mb-2">Fund Portfolio</h1>
          <p className="text-gray-600">
            View and analyze your fund investments
          </p>
        </div>
        <Link
          href="/upload"
          className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition"
        >
          Add New Fund
        </Link>
      </div>

      {funds && funds.length === 0 ? (
        <div className="bg-white rounded-lg shadow-md p-12 text-center">
          <p className="text-gray-600 mb-4">No funds found. Upload a fund document to get started.</p>
          <Link
            href="/upload"
            className="inline-block px-6 py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition"
          >
            Upload Document
          </Link>
        </div>
      ) : (
        <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-6">
          {funds?.map((fund: any) => (
            <FundCard
              key={fund.id}
              fund={fund}
              onDelete={async (id) => {
                const result = await Swal.fire({
                  title: 'Are you sure?',
                  html: `You are about to delete <strong>"${fund.name}"</strong>.<br/>This will also delete all related documents.`,
                  icon: 'warning',
                  showCancelButton: true,
                  confirmButtonColor: '#dc2626',
                  cancelButtonColor: '#6b7280',
                  confirmButtonText: 'Yes, delete it!',
                  cancelButtonText: 'Cancel'
                })

                if (result.isConfirmed) {
                  deleteMutation.mutate(id)
                }
              }}
            />
          ))}
        </div>
      )}
    </div>
  )
}

function FundCard({ fund, onDelete }: { fund: any; onDelete: (id: number) => void }) {
  const metrics = fund.metrics || {}
  const dpi = metrics.dpi || 0
  const irr = metrics.irr || 0

  return (
    <div className="bg-white rounded-lg shadow-md hover:shadow-lg transition p-6 h-full flex flex-col">
      <div className="mb-4">
        <div className="flex items-start justify-between">
          <div className="flex-1">
            <h3 className="text-xl font-semibold text-gray-900 mb-1">
              {fund.name}
            </h3>
            {fund.gp_name && (
              <p className="text-sm text-gray-600">GP: {fund.gp_name}</p>
            )}
            {fund.vintage_year && (
              <p className="text-sm text-gray-500">Vintage: {fund.vintage_year}</p>
            )}
          </div>
          <button
            onClick={(e) => {
              e.stopPropagation()
              onDelete(fund.id)
            }}
            className="text-red-600 hover:text-red-800 p-2 hover:bg-red-50 rounded-lg transition"
            title="Delete fund"
          >
            <Trash2 className="w-5 h-5" />
          </button>
        </div>
      </div>

      <div className="space-y-3 mb-4 flex-1">
        <MetricRow
          label="DPI"
          value={dpi.toFixed(2) + 'x'}
          positive={dpi >= 1}
        />
        <MetricRow
          label="IRR"
          value={formatPercentage(irr)}
          positive={irr >= 0}
        />
        {metrics.pic > 0 && (
          <MetricRow
            label="Paid-In Capital"
            value={formatCurrency(metrics.pic)}
          />
        )}
      </div>

      <Link href={`/funds/${fund.id}`} className="flex items-center text-blue-600 text-sm font-medium hover:text-blue-800">
        View Details <ArrowRight className="w-4 h-4 ml-1" />
      </Link>
    </div>
  )
}

function MetricRow({ label, value, positive }: { 
  label: string
  value: string
  positive?: boolean 
}) {
  return (
    <div className="flex items-center justify-between">
      <span className="text-sm text-gray-600">{label}</span>
      <div className="flex items-center space-x-1">
        <span className="font-semibold text-gray-900">{value}</span>
        {positive !== undefined && (
          positive ? (
            <TrendingUp className="w-4 h-4 text-green-600" />
          ) : (
            <TrendingDown className="w-4 h-4 text-red-600" />
          )
        )}
      </div>
    </div>
  )
}
