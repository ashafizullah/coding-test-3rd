"use client";

import React from "react";
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
  ReferenceLine,
} from "recharts";

interface PerformanceDataPoint {
  date: string;
  dpi: number;
  tvpi?: number;
  irr?: number;
}

interface FundPerformanceChartProps {
  data: PerformanceDataPoint[];
  metrics?: ("dpi" | "tvpi" | "irr")[];
}

export default function FundPerformanceChart({
  data,
  metrics = ["dpi", "tvpi"],
}: FundPerformanceChartProps) {
  if (!data || data.length === 0) {
    return (
      <div className="flex items-center justify-center h-64 text-gray-500">
        No performance data available
      </div>
    );
  }

  const formatPercentage = (value: number) => {
    return `${(value * 100).toFixed(1)}%`;
  };

  const formatRatio = (value: number) => {
    return value.toFixed(2) + "x";
  };

  const CustomTooltip = ({ active, payload, label }: any) => {
    if (active && payload && payload.length) {
      return (
        <div className="bg-white p-4 border border-gray-200 rounded shadow-lg">
          <p className="font-semibold mb-2">{label}</p>
          {payload.map((entry: any, index: number) => {
            const value =
              entry.name === "IRR"
                ? formatPercentage(entry.value)
                : formatRatio(entry.value);
            return (
              <p key={index} className="text-sm" style={{ color: entry.color }}>
                {entry.name}: {value}
              </p>
            );
          })}
        </div>
      );
    }
    return null;
  };

  return (
    <ResponsiveContainer width="100%" height={400}>
      <LineChart data={data} margin={{ top: 5, right: 30, left: 20, bottom: 5 }}>
        <CartesianGrid strokeDasharray="3 3" />
        <XAxis dataKey="date" />
        <YAxis
          yAxisId="left"
          tickFormatter={formatRatio}
          label={{ value: "Multiple (x)", angle: -90, position: "insideLeft" }}
        />
        {metrics.includes("irr") && (
          <YAxis
            yAxisId="right"
            orientation="right"
            tickFormatter={formatPercentage}
            label={{ value: "IRR (%)", angle: 90, position: "insideRight" }}
          />
        )}
        <Tooltip content={<CustomTooltip />} />
        <Legend />

        {/* Reference line at 1.0x for DPI/TVPI */}
        {(metrics.includes("dpi") || metrics.includes("tvpi")) && (
          <ReferenceLine
            yAxisId="left"
            y={1}
            stroke="#94a3b8"
            strokeDasharray="3 3"
            label="Break-even (1.0x)"
          />
        )}

        {metrics.includes("dpi") && (
          <Line
            yAxisId="left"
            type="monotone"
            dataKey="dpi"
            name="DPI"
            stroke="#3b82f6"
            strokeWidth={3}
            dot={{ r: 5 }}
            activeDot={{ r: 7 }}
          />
        )}

        {metrics.includes("tvpi") && (
          <Line
            yAxisId="left"
            type="monotone"
            dataKey="tvpi"
            name="TVPI"
            stroke="#8b5cf6"
            strokeWidth={3}
            dot={{ r: 5 }}
            activeDot={{ r: 7 }}
          />
        )}

        {metrics.includes("irr") && (
          <Line
            yAxisId="right"
            type="monotone"
            dataKey="irr"
            name="IRR"
            stroke="#10b981"
            strokeWidth={3}
            strokeDasharray="5 5"
            dot={{ r: 5 }}
            activeDot={{ r: 7 }}
          />
        )}
      </LineChart>
    </ResponsiveContainer>
  );
}
