'use client';

import dynamic from 'next/dynamic';
import React from 'react';

// Load Plotly React wrapper dynamically to prevent SSR failures
const Plot = dynamic(() => import('react-plotly.js'), {
  ssr: false,
  loading: () => (
    <div className="flex min-h-[300px] w-full items-center justify-center rounded-xl border border-neutral-900 bg-neutral-950/40 text-neutral-400">
      <div className="h-6 w-6 animate-spin rounded-full border-2 border-red-600 border-t-transparent"></div>
    </div>
  ),
});

function getXValues(x: unknown): number[] {
  if (Array.isArray(x)) {
    return x.map(Number);
  }
  if (x && typeof x === 'object') {
    const xObj = x as { dtype?: string; bdata?: string };
    if (typeof xObj.bdata === 'string') {
      try {
        const binaryString = atob(xObj.bdata);
        const len = binaryString.length;
        const bytes = new Uint8Array(len);
        for (let i = 0; i < len; i++) {
          bytes[i] = binaryString.charCodeAt(i);
        }
        
        if (xObj.dtype === 'f8') {
          return Array.from(new Float64Array(bytes.buffer, bytes.byteOffset, bytes.byteLength / 8));
        }
        if (xObj.dtype === 'f4') {
          return Array.from(new Float32Array(bytes.buffer, bytes.byteOffset, bytes.byteLength / 4));
        }
        if (xObj.dtype === 'i4') {
          return Array.from(new Int32Array(bytes.buffer, bytes.byteOffset, bytes.byteLength / 4));
        }
        return Array.from(new Float64Array(bytes.buffer, bytes.byteOffset, bytes.byteLength / 8));
      } catch (e) {
        console.error("Failed to decode base64 chart data", e);
      }
    }
  }
  return [];
}

interface PlotlyChartProps {
  data: any;
  layout: any;
  className?: string;
  height?: number | string;
}

export default function PlotlyChart({ data, layout, className = '', height = 350 }: PlotlyChartProps) {
  if (!data || !layout) {
    return (
      <div className="flex min-h-[200px] w-full items-center justify-center rounded-xl border border-neutral-900 bg-neutral-950/40 text-sm text-neutral-500">
        Chart trace not available
      </div>
    );
  }

  // Check if we have horizontal bar chart to ensure sufficient left margin and right headroom
  const isHorizontalBar = Array.isArray(data) && data.some((trace) => {
    const t = trace as { type?: string; orientation?: string };
    return t?.type === 'bar' && t?.orientation === 'h';
  });

  const marginL = isHorizontalBar ? Math.max(layout.margin?.l || 0, 130) : (layout.margin?.l || 30);
  const marginR = isHorizontalBar ? 40 : (layout.margin?.r || 20);

  // Inject visual defaults corresponding to F1 theme styling
  const customLayout = {
    ...layout,
    paper_bgcolor: 'rgba(0,0,0,0)',
    plot_bgcolor: 'rgba(0,0,0,0)',
    font: {
      family: 'Outfit, system-ui, sans-serif',
      color: '#888888',
      ...layout.font,
    },
    margin: {
      l: marginL,
      r: marginR,
      t: layout.margin?.t || 50,
      b: layout.margin?.b || 40,
    },
  };

  if (isHorizontalBar && !layout.xaxis?.range) {
    let maxX = 0;
    (data as Array<{ type?: string; orientation?: string; x?: unknown }>).forEach((trace) => {
      if (trace.type === 'bar' && trace.orientation === 'h' && trace.x) {
        const values = getXValues(trace.x);
        values.forEach((val) => {
          if (!isNaN(val) && val > maxX) {
            maxX = val;
          }
        });
      }
    });

    const headroomX = maxX > 0 ? maxX * 1.30 : 10;
    console.log("PlotlyChart Horizontal Bar: maxX =", maxX, "headroomX =", headroomX);
    customLayout.xaxis = {
      ...layout.xaxis,
      range: [0, headroomX],
    };
  }

  if (isHorizontalBar) {
    // Hide default yaxis tick labels to prevent duplication and disable automargin
    customLayout.yaxis = {
      ...layout.yaxis,
      showticklabels: false,
      automargin: false,
    };

    // Render left-aligned category labels using container-anchored annotations
    const firstTrace = data[0] as { y?: unknown[] };
    if (firstTrace && Array.isArray(firstTrace.y)) {
      const categories = firstTrace.y.map(String);
      customLayout.annotations = [
        ...(layout.annotations || []),
        ...categories.map((name) => ({
          xref: 'paper',
          yref: 'y',
          x: 0,
          xshift: -120,
          y: name,
          text: name,
          showarrow: false,
          xanchor: 'left',
          yanchor: 'middle',
          font: {
            family: 'Outfit, system-ui, sans-serif',
            size: 11,
            color: '#888888',
          },
        })),
      ];
    }
  }

  return (
    <div className={`w-full ${className}`} style={{ height: height }}>
      <Plot
        data={data}
        layout={customLayout}
        config={{ displayModeBar: false, responsive: true }}
        style={{ width: '100%', height: '100%' }}
        useResizeHandler={true}
      />
    </div>
  );
}
