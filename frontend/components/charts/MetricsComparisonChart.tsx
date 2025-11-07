"use client";

import React from "react";
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
  Cell,
} from "recharts";

interface FundMetrics {
  fundName: string;
  dpi: number;
  irr: number;
  tvpi?: number;
  pic?: number;
}

interface MetricsComparisonChartProps {
  funds: FundMetrics[];
  metric?: "dpi" | "irr" | "tvpi" | "pic";
}

export default function MetricsComparisonChart({
  funds,
  metric = "dpi",
}: MetricsComparisonChartProps) {
  if (!funds || funds.length === 0) {
    return (
      <div className="flex items-center justify-center h-64 text-gray-500">
        No fund data available for comparison
      </div>
    );
  }

  const COLORS = [
    "#3b82f6", // blue
    "#10b981", // green
    "#f59e0b", // amber
    "#ef4444", // red
    "#8b5cf6", // purple
    "#ec4899", // pink
    "#14b8a6", // teal
    "#f97316", // orange
  ];

  const formatValue = (value: number) => {
    if (metric === "irr") {
      return `${(value * 100).toFixed(1)}%`;
    } else if (metric === "pic") {
      return new Intl.NumberFormat("en-US", {
        style: "currency",
        currency: "USD",
        notation: "compact",
        maximumFractionDigits: 1,
      }).format(value);
    } else {
      return value.toFixed(2) + "x";
    }
  };

  const getMetricLabel = () => {
    switch (metric) {
      case "dpi":
        return "DPI (Distributions to Paid-In)";
      case "irr":
        return "IRR (Internal Rate of Return)";
      case "tvpi":
        return "TVPI (Total Value to Paid-In)";
      case "pic":
        return "PIC (Paid-In Capital)";
      default:
        return "Metric";
    }
  };

  const data = funds.map((fund) => ({
    name: fund.fundName,
    value: fund[metric] || 0,
  }));

  const CustomTooltip = ({ active, payload }: any) => {
    if (active && payload && payload.length) {
      const data = payload[0];
      return (
        <div className="bg-white p-4 border border-gray-200 rounded shadow-lg">
          <p className="font-semibold mb-1">{data.payload.name}</p>
          <p className="text-sm text-gray-600">
            {getMetricLabel()}: <span className="font-semibold">{formatValue(data.value)}</span>
          </p>
        </div>
      );
    }
    return null;
  };

  return (
    <div>
      <h3 className="text-lg font-semibold mb-4">{getMetricLabel()} Comparison</h3>
      <ResponsiveContainer width="100%" height={400}>
        <BarChart data={data} margin={{ top: 20, right: 30, left: 20, bottom: 60 }}>
          <CartesianGrid strokeDasharray="3 3" />
          <XAxis
            dataKey="name"
            angle={-45}
            textAnchor="end"
            height={100}
            interval={0}
          />
          <YAxis
            tickFormatter={(value) => formatValue(value)}
            label={{
              value: getMetricLabel(),
              angle: -90,
              position: "insideLeft",
            }}
          />
          <Tooltip content={<CustomTooltip />} />
          <Bar dataKey="value" radius={[8, 8, 0, 0]}>
            {data.map((entry, index) => (
              <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
            ))}
          </Bar>
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
}
