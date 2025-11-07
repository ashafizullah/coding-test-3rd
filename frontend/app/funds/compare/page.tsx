"use client";

import React, { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import MetricsComparisonChart from "@/components/charts/MetricsComparisonChart";

interface Fund {
  id: number;
  name: string;
  gp_name: string;
  fund_type: string;
  vintage_year: number;
}

interface FundMetrics {
  pic: number;
  total_distributions: number;
  dpi: number;
  irr: number;
  nav: number;
  tvpi: number;
  rvpi: number;
}

export default function CompareFundsPage() {
  const [selectedFundIds, setSelectedFundIds] = useState<number[]>([]);
  const [selectedMetric, setSelectedMetric] = useState<"dpi" | "irr" | "tvpi" | "pic">("dpi");

  // Fetch all funds
  const { data: funds, isLoading: fundsLoading } = useQuery<Fund[]>({
    queryKey: ["funds"],
    queryFn: async () => {
      const response = await fetch("http://localhost:8000/api/funds");
      if (!response.ok) throw new Error("Failed to fetch funds");
      return response.json();
    },
  });

  // Fetch metrics for selected funds
  const { data: metricsData, isLoading: metricsLoading } = useQuery<FundMetrics[]>({
    queryKey: ["fund-metrics", selectedFundIds],
    queryFn: async () => {
      if (selectedFundIds.length === 0) return [];

      const promises = selectedFundIds.map((fundId) =>
        fetch(`http://localhost:8000/api/funds/${fundId}/metrics`)
          .then((res) => {
            if (!res.ok) throw new Error(`Failed to fetch metrics for fund ${fundId}`);
            return res.json();
          })
      );

      return Promise.all(promises);
    },
    enabled: selectedFundIds.length > 0,
  });

  const handleFundToggle = (fundId: number) => {
    setSelectedFundIds((prev) =>
      prev.includes(fundId)
        ? prev.filter((id) => id !== fundId)
        : [...prev, fundId]
    );
  };

  const handleSelectAll = () => {
    if (funds) {
      setSelectedFundIds(funds.map((fund) => fund.id));
    }
  };

  const handleClearAll = () => {
    setSelectedFundIds([]);
  };

  // Combine fund names with metrics data
  const comparisonData = React.useMemo(() => {
    if (!funds || !metricsData || selectedFundIds.length === 0) return [];

    return selectedFundIds.map((fundId, index) => {
      const fund = funds.find((f) => f.id === fundId);
      const metrics = metricsData[index];

      return {
        fundName: fund?.name || `Fund ${fundId}`,
        dpi: metrics?.dpi || 0,
        irr: metrics?.irr ? metrics.irr / 100 : 0, // Convert percentage to decimal for chart
        tvpi: metrics?.tvpi || 0,
        pic: metrics?.pic || 0,
      };
    });
  }, [funds, metricsData, selectedFundIds]);

  if (fundsLoading) {
    return (
      <div className="flex justify-center items-center h-screen">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
      </div>
    );
  }

  return (
    <div className="container mx-auto px-4 py-8">
      <div className="mb-8">
        <h1 className="text-3xl font-bold mb-2">Compare Funds</h1>
        <p className="text-gray-600">
          Select multiple funds to compare their performance metrics
        </p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        {/* Fund Selection Panel */}
        <div className="lg:col-span-1">
          <div className="bg-white rounded-lg shadow-md p-6 sticky top-4">
            <div className="flex justify-between items-center mb-4">
              <h2 className="text-xl font-semibold">Select Funds</h2>
              <div className="flex gap-2">
                <button
                  onClick={handleSelectAll}
                  className="text-sm text-blue-600 hover:text-blue-800 font-medium"
                >
                  Select All
                </button>
                <span className="text-gray-400">|</span>
                <button
                  onClick={handleClearAll}
                  className="text-sm text-gray-600 hover:text-gray-800 font-medium"
                >
                  Clear
                </button>
              </div>
            </div>

            <div className="mb-4 text-sm text-gray-500">
              {selectedFundIds.length} of {funds?.length || 0} funds selected
            </div>

            <div className="space-y-2 max-h-96 overflow-y-auto">
              {funds?.map((fund) => (
                <label
                  key={fund.id}
                  className={`flex items-start p-3 rounded-lg border-2 cursor-pointer transition-all ${
                    selectedFundIds.includes(fund.id)
                      ? "border-blue-500 bg-blue-50"
                      : "border-gray-200 hover:border-gray-300"
                  }`}
                >
                  <input
                    type="checkbox"
                    checked={selectedFundIds.includes(fund.id)}
                    onChange={() => handleFundToggle(fund.id)}
                    className="mt-1 mr-3 h-4 w-4 text-blue-600 rounded focus:ring-blue-500"
                  />
                  <div className="flex-1">
                    <div className="font-medium text-gray-900">{fund.name}</div>
                    <div className="text-sm text-gray-500">
                      {fund.gp_name && <span>{fund.gp_name} • </span>}
                      {fund.vintage_year && <span>{fund.vintage_year}</span>}
                    </div>
                  </div>
                </label>
              ))}
            </div>

            {(!funds || funds.length === 0) && (
              <div className="text-center py-8 text-gray-500">
                No funds available. Please create funds first.
              </div>
            )}
          </div>
        </div>

        {/* Comparison Charts Panel */}
        <div className="lg:col-span-2">
          {selectedFundIds.length === 0 ? (
            <div className="bg-white rounded-lg shadow-md p-12 text-center">
              <svg
                className="mx-auto h-24 w-24 text-gray-400 mb-4"
                fill="none"
                viewBox="0 0 24 24"
                stroke="currentColor"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={1.5}
                  d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z"
                />
              </svg>
              <h3 className="text-lg font-semibold text-gray-700 mb-2">
                No Funds Selected
              </h3>
              <p className="text-gray-500">
                Select at least one fund from the left panel to view comparison charts
              </p>
            </div>
          ) : metricsLoading ? (
            <div className="bg-white rounded-lg shadow-md p-12 flex justify-center items-center">
              <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
            </div>
          ) : (
            <div className="space-y-6">
              {/* Metric Selector */}
              <div className="bg-white rounded-lg shadow-md p-6">
                <h2 className="text-xl font-semibold mb-4">Select Metric to Compare</h2>
                <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
                  {[
                    { key: "dpi" as const, label: "DPI", desc: "Distributions to Paid-In" },
                    { key: "irr" as const, label: "IRR", desc: "Internal Rate of Return" },
                    { key: "tvpi" as const, label: "TVPI", desc: "Total Value to Paid-In" },
                    { key: "pic" as const, label: "PIC", desc: "Paid-In Capital" },
                  ].map((metric) => (
                    <button
                      key={metric.key}
                      onClick={() => setSelectedMetric(metric.key)}
                      className={`p-4 rounded-lg border-2 text-left transition-all ${
                        selectedMetric === metric.key
                          ? "border-blue-500 bg-blue-50"
                          : "border-gray-200 hover:border-gray-300"
                      }`}
                    >
                      <div className="font-semibold text-gray-900">{metric.label}</div>
                      <div className="text-xs text-gray-500 mt-1">{metric.desc}</div>
                    </button>
                  ))}
                </div>
              </div>

              {/* Comparison Chart */}
              <div className="bg-white rounded-lg shadow-md p-6">
                <MetricsComparisonChart funds={comparisonData} metric={selectedMetric} />
              </div>

              {/* Metrics Table */}
              <div className="bg-white rounded-lg shadow-md p-6">
                <h2 className="text-xl font-semibold mb-4">Detailed Metrics Comparison</h2>
                <div className="overflow-x-auto">
                  <table className="min-w-full divide-y divide-gray-200">
                    <thead className="bg-gray-50">
                      <tr>
                        <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                          Fund Name
                        </th>
                        <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">
                          PIC
                        </th>
                        <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">
                          DPI
                        </th>
                        <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">
                          IRR
                        </th>
                        <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">
                          TVPI
                        </th>
                        <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">
                          NAV
                        </th>
                        <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">
                          RVPI
                        </th>
                      </tr>
                    </thead>
                    <tbody className="bg-white divide-y divide-gray-200">
                      {selectedFundIds.map((fundId, index) => {
                        const fund = funds?.find((f) => f.id === fundId);
                        const metrics = metricsData?.[index];

                        return (
                          <tr key={fundId} className="hover:bg-gray-50">
                            <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">
                              {fund?.name}
                            </td>
                            <td className="px-6 py-4 whitespace-nowrap text-sm text-right text-gray-700">
                              ${metrics?.pic?.toLocaleString() || "0"}
                            </td>
                            <td className="px-6 py-4 whitespace-nowrap text-sm text-right text-gray-700">
                              {metrics?.dpi?.toFixed(2) || "0.00"}x
                            </td>
                            <td className="px-6 py-4 whitespace-nowrap text-sm text-right text-gray-700">
                              {metrics?.irr?.toFixed(1) || "0.0"}%
                            </td>
                            <td className="px-6 py-4 whitespace-nowrap text-sm text-right text-gray-700">
                              {metrics?.tvpi?.toFixed(2) || "0.00"}x
                            </td>
                            <td className="px-6 py-4 whitespace-nowrap text-sm text-right text-gray-700">
                              ${metrics?.nav?.toLocaleString() || "0"}
                            </td>
                            <td className="px-6 py-4 whitespace-nowrap text-sm text-right text-gray-700">
                              {metrics?.rvpi?.toFixed(2) || "0.00"}x
                            </td>
                          </tr>
                        );
                      })}
                    </tbody>
                  </table>
                </div>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
