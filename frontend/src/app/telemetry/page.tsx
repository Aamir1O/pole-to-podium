'use client';

import React, { useState } from 'react';
import { 
  Spline, 
  Activity, 
  Search, 
  AlertTriangle,
  ChevronRight 
} from 'lucide-react';
import PlotlyChart from '@/components/PlotlyChart';
import { API_URL } from '@/lib/api';

interface DriverMeta {
  name: string;
  code: string;
  country: string;
  color: string;
}

interface TelemetryPayload {
  session_id: number;
  circuit_key: string;
  driver_a_meta: DriverMeta;
  driver_b_meta: DriverMeta;
  telemetry: {
    grid: number[];
    driver_a: {
      speed: number[];
      throttle: number[];
      brake: boolean[];
      gear: number[];
      rpm: number[];
      lap_time: number;
    };
    driver_b: {
      speed: number[];
      throttle: number[];
      brake: boolean[];
      gear: number[];
      rpm: number[];
      lap_time: number;
    };
    delta: number[];
  };
  corners: Array<{
    corner_number: number;
    dist_start_m: number;
    dist_apex_m: number;
    dist_end_m: number;
  }>;
  cpi_breakdown: Array<{
    driver_code: string;
    corner_number: number;
    corner_name: string;
    entry_score: number;
    apex_score: number;
    exit_score: number;
    cpi: number;
    corner_time_s: number;
    entry_speed_kph: number;
    apex_speed_kph: number;
    exit_speed_kph: number;
    brake_point_m: number;
    throttle_point_m: number;
    time_to_full_throttle_s: number;
  }>;
  engineering_insights: Array<{
    corner_number: number;
    delta_s: number;
    driver_gaining: string;
    driver_losing: string;
    reason: string;
  }>;
}

export default function TelemetryPage() {
  const [season, setSeason] = useState<number>(2026);
  const [roundNum, setRoundNum] = useState<number>(1);
  const [sessionType, setSessionType] = useState<string>('Q');
  const [driverA, setDriverA] = useState<string>('ANT');
  const [driverB, setDriverB] = useState<string>('RUS');
  
  const [data, setData] = useState<TelemetryPayload | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleLoadTelemetry = () => {
    setLoading(true);
    setError(null);
    setData(null);

    const query = `season=${season}&round=${roundNum}&session=${sessionType}&driver_a=${driverA}&driver_b=${driverB}`;
    fetch(`${API_URL}/api/v1/telemetry?${query}`)
      .then((res) => {
        if (!res.ok) {
          return res.json().then((errData) => {
            throw new Error(errData.detail || 'Failed to fetch telemetry data');
          });
        }
        return res.json();
      })
      .then((resData: TelemetryPayload) => {
        setData(resData);
        setLoading(false);
      })
      .catch((err) => {
        setError(err.message);
        setLoading(false);
      });
  };

  // Build Plotly layouts with apex overlay vertical lines
  const buildOverlayLayout = (title: string, yTitle: string, corners: any[], yRange?: [number, number]) => {
    const shapes = corners.map((c: any) => ({
      type: 'line',
      x0: c.dist_apex_m,
      x1: c.dist_apex_m,
      y0: 0,
      y1: 1,
      yref: 'paper',
      line: {
        color: 'rgba(255,255,255,0.06)',
        width: 1,
        dash: 'dashdot'
      }
    }));

    const annotations = corners.map((c: any) => ({
      x: c.dist_apex_m,
      y: 1.02,
      yref: 'paper',
      text: `T${c.corner_number}`,
      showarrow: false,
      font: { size: 9, color: '#555555', family: 'JetBrains Mono' },
      xanchor: 'center'
    }));

    return {
      title: title,
      xaxis: { 
        title: 'Distance (m)', 
        gridcolor: 'rgba(255,255,255,0.03)',
        linecolor: 'rgba(255,255,255,0.06)'
      },
      yaxis: { 
        title: yTitle, 
        gridcolor: 'rgba(255,255,255,0.03)',
        linecolor: 'rgba(255,255,255,0.06)',
        range: yRange
      },
      shapes: shapes,
      annotations: annotations,
      legend: { orientation: 'h', y: 1.15, x: 0 }
    };
  };

  return (
    <div className="space-y-6">
      
      {/* Header bar */}
      <div className="rounded-xl border border-neutral-900 bg-neutral-950/30 p-5">
        <h1 className="text-2xl font-black text-white uppercase tracking-tight flex items-center gap-2">
          <Spline className="h-6 w-6 text-red-600" />
          Telemetry Analysis
        </h1>
        <p className="text-xs text-neutral-500 font-mono uppercase tracking-wider mt-1">Overlay traces over distance grids</p>
      </div>

      {/* Inputs Form Selector Grid */}
      <div className="grid grid-cols-2 gap-4 md:grid-cols-6 rounded-xl border border-neutral-900 bg-neutral-950/40 p-5 items-end">
        <div>
          <label className="block text-[10px] font-mono font-bold text-neutral-500 uppercase tracking-widest mb-1.5">Season</label>
          <select 
            value={season} 
            onChange={(e) => setSeason(Number(e.target.value))}
            className="w-full rounded-lg border border-neutral-800 bg-neutral-950 px-3 py-2 text-sm font-semibold text-white focus:border-red-600 focus:outline-none"
          >
            <option value={2026}>2026</option>
            <option value={2025}>2025</option>
          </select>
        </div>
        
        <div>
          <label className="block text-[10px] font-mono font-bold text-neutral-500 uppercase tracking-widest mb-1.5">Round</label>
          <input 
            type="number" 
            min={1} 
            max={24} 
            value={roundNum} 
            onChange={(e) => setRoundNum(Number(e.target.value))}
            className="w-full rounded-lg border border-neutral-800 bg-neutral-950 px-3 py-2 text-sm font-semibold text-white focus:border-red-600 focus:outline-none"
          />
        </div>

        <div>
          <label className="block text-[10px] font-mono font-bold text-neutral-500 uppercase tracking-widest mb-1.5">Session</label>
          <select 
            value={sessionType} 
            onChange={(e) => setSessionType(e.target.value)}
            className="w-full rounded-lg border border-neutral-800 bg-neutral-950 px-3 py-2 text-sm font-semibold text-white focus:border-red-600 focus:outline-none"
          >
            <option value="Q">Qualifying (Q)</option>
            <option value="R">Race (R)</option>
            <option value="FP1">FP1</option>
            <option value="FP2">FP2</option>
            <option value="FP3">FP3</option>
          </select>
        </div>

        <div>
          <label className="block text-[10px] font-mono font-bold text-neutral-500 uppercase tracking-widest mb-1.5">Driver A</label>
          <input 
            type="text" 
            value={driverA} 
            onChange={(e) => setDriverA(e.target.value.toUpperCase())}
            className="w-full rounded-lg border border-neutral-800 bg-neutral-950 px-3 py-2 text-sm font-semibold text-white focus:border-red-600 focus:outline-none"
          />
        </div>

        <div>
          <label className="block text-[10px] font-mono font-bold text-neutral-500 uppercase tracking-widest mb-1.5">Driver B</label>
          <input 
            type="text" 
            value={driverB} 
            onChange={(e) => setDriverB(e.target.value.toUpperCase())}
            className="w-full rounded-lg border border-neutral-800 bg-neutral-950 px-3 py-2 text-sm font-semibold text-white focus:border-red-600 focus:outline-none"
          />
        </div>

        <button 
          onClick={handleLoadTelemetry}
          disabled={loading}
          className="w-full h-[38px] rounded-lg bg-red-600 text-black text-xs font-black tracking-widest uppercase hover:bg-red-500 transition-colors disabled:opacity-50 cursor-pointer flex items-center justify-center gap-1.5"
        >
          <Search className="h-4 w-4" />
          <span>Load</span>
        </button>
      </div>

      {loading && (
        <div className="flex h-96 items-center justify-center rounded-xl border border-neutral-900 bg-neutral-950/20">
          <div className="h-8 w-8 animate-spin rounded-full border-2 border-red-600 border-t-transparent"></div>
        </div>
      )}

      {error && (
        <div className="flex min-h-[300px] flex-col items-center justify-center rounded-xl border border-neutral-900 bg-neutral-950/20 p-6 text-center">
          <AlertTriangle className="mb-4 h-12 w-12 text-neutral-600" />
          <h3 className="text-base font-bold text-white">Telemetry Unavailable</h3>
          <p className="mt-2 text-xs text-neutral-500 max-w-md">{error}</p>
        </div>
      )}

      {data && (
        <div className="space-y-6">
          
          {/* Summary KPIs bar */}
          <div className="grid grid-cols-1 gap-4 sm:grid-cols-3 rounded-xl border border-neutral-900 bg-neutral-950/20 p-5 font-mono text-xs">
            <div>
              <p className="text-neutral-500 uppercase font-bold">{data.driver_a_meta.name} Lap:</p>
              <p className="mt-1 text-base font-black text-red-500">{data.telemetry.driver_a.lap_time.toFixed(3)}s</p>
            </div>
            <div>
              <p className="text-neutral-500 uppercase font-bold">{data.driver_b_meta.name} Lap:</p>
              <p className="mt-1 text-base font-black text-blue-500">{data.telemetry.driver_b.lap_time.toFixed(3)}s</p>
            </div>
            <div>
              <p className="text-neutral-500 uppercase font-bold">Delta Gap:</p>
              <p className="mt-1 text-base font-black text-white">
                {Math.abs(data.telemetry.driver_a.lap_time - data.telemetry.driver_b.lap_time).toFixed(3)}s
              </p>
            </div>
          </div>

          {/* Speed trace card */}
          <div className="rounded-xl border border-neutral-900 bg-neutral-950/20 p-5">
            <PlotlyChart 
              data={[
                {
                  x: data.telemetry.grid,
                  y: data.telemetry.driver_a.speed,
                  name: data.driver_a_meta.code,
                  type: 'scatter',
                  mode: 'lines',
                  line: { color: data.driver_a_meta.color, width: 2 }
                },
                {
                  x: data.telemetry.grid,
                  y: data.telemetry.driver_b.speed,
                  name: data.driver_b_meta.code,
                  type: 'scatter',
                  mode: 'lines',
                  line: { color: '#3B8BD4', width: 2 } // Contrast blue
                }
              ]} 
              layout={buildOverlayLayout('Speed Comparison (km/h)', 'Speed', data.corners)} 
              height={320} 
            />
          </div>

          {/* Delta gap over the lap */}
          {data.telemetry.delta.length > 0 && (
            <div className="rounded-xl border border-neutral-900 bg-neutral-950/20 p-5">
              <PlotlyChart 
                data={[
                  {
                    x: data.telemetry.grid,
                    y: data.telemetry.delta,
                    name: 'Delta Trace',
                    type: 'scatter',
                    mode: 'lines',
                    line: { color: '#ffffff', width: 1.5 },
                    fill: 'tozeroy',
                    fillcolor: 'rgba(255,255,255,0.02)'
                  }
                ]} 
                layout={buildOverlayLayout('Cumulative Delta Trace (seconds)', 'Delta', data.corners)} 
                height={260} 
              />
              <p className="mt-2 text-[10px] font-mono text-neutral-600 text-center uppercase">Positive = {data.driver_a_meta.code} faster | Negative = {data.driver_b_meta.code} faster</p>
            </div>
          )}

          {/* Throttle & Brake trace overlays */}
          <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
            
            <div className="rounded-xl border border-neutral-900 bg-neutral-950/20 p-5">
              <PlotlyChart 
                data={[
                  {
                    x: data.telemetry.grid,
                    y: data.telemetry.driver_a.throttle,
                    name: data.driver_a_meta.code,
                    type: 'scatter',
                    mode: 'lines',
                    line: { color: data.driver_a_meta.color, width: 1.5 }
                  },
                  {
                    x: data.telemetry.grid,
                    y: data.telemetry.driver_b.throttle,
                    name: data.driver_b_meta.code,
                    type: 'scatter',
                    mode: 'lines',
                    line: { color: '#3B8BD4', width: 1.5 }
                  }
                ]} 
                layout={buildOverlayLayout('Throttle Trace (%)', 'Throttle %', data.corners, [0, 105])} 
                height={260} 
              />
            </div>
            
            <div className="rounded-xl border border-neutral-900 bg-neutral-950/20 p-5">
              <PlotlyChart 
                data={[
                  {
                    x: data.telemetry.grid,
                    y: data.telemetry.driver_a.brake.map(b => b ? 1 : 0),
                    name: data.driver_a_meta.code,
                    type: 'scatter',
                    mode: 'lines',
                    line: { color: data.driver_a_meta.color, width: 1.5, shape: 'hv' }
                  },
                  {
                    x: data.telemetry.grid,
                    y: data.telemetry.driver_b.brake.map(b => b ? 1 : 0),
                    name: data.driver_b_meta.code,
                    type: 'scatter',
                    mode: 'lines',
                    line: { color: '#3B8BD4', width: 1.5, shape: 'hv' }
                  }
                ]} 
                layout={buildOverlayLayout('Brake Activation (0/1)', 'Brake', data.corners, [-0.1, 1.2])} 
                height={260} 
              />
            </div>

          </div>

          {/* Gear overlay */}
          <div className="rounded-xl border border-neutral-900 bg-neutral-950/20 p-5">
            <PlotlyChart 
              data={[
                {
                  x: data.telemetry.grid,
                  y: data.telemetry.driver_a.gear,
                  name: data.driver_a_meta.code,
                  type: 'scatter',
                  mode: 'lines',
                  line: { color: data.driver_a_meta.color, width: 1.5, shape: 'hv' }
                },
                {
                  x: data.telemetry.grid,
                  y: data.telemetry.driver_b.gear,
                  name: data.driver_b_meta.code,
                  type: 'scatter',
                  mode: 'lines',
                  line: { color: '#3B8BD4', width: 1.5, shape: 'hv' }
                }
              ]} 
              layout={buildOverlayLayout('Gear Shifts (nGear)', 'Gear', data.corners, [0, 9])} 
              height={260} 
            />
          </div>

          {/* Turn performance breakdown */}
          <div className="grid grid-cols-1 gap-6 lg:grid-cols-12">
            
            {/* Table */}
            <div className="lg:col-span-8 rounded-xl border border-neutral-900 bg-neutral-950/20 p-5">
              <h2 className="flex items-center gap-2 font-sans text-xs font-bold tracking-widest text-neutral-400 uppercase mb-4">
                <span className="inline-block h-3.5 w-1 rounded bg-red-600"></span>
                Turn Breakdown table
              </h2>
              <div className="overflow-x-auto">
                <table className="w-full text-left border-collapse">
                  <thead>
                    <tr className="border-b border-neutral-900 font-mono text-[10px] text-neutral-500 uppercase tracking-wider">
                      <th className="py-2 pl-2">Turn</th>
                      <th className="py-2">Driver</th>
                      <th className="py-2 text-center">Entry</th>
                      <th className="py-2 text-center">Apex</th>
                      <th className="py-2 text-center">Exit</th>
                      <th className="py-2 text-right">CPI</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-neutral-900 text-sm">
                    {data.cpi_breakdown.map((row) => (
                      <tr key={`${row.corner_number}-${row.driver_code}`} className="hover:bg-neutral-950/60 transition-colors">
                        <td className="py-2.5 pl-2 font-mono font-bold text-neutral-400">T{row.corner_number}</td>
                        <td className="py-2.5 font-semibold text-white">
                          <span className={`rounded px-1.5 py-0.5 text-[10px] font-mono font-bold ${
                            row.driver_code === data.driver_a_meta.code ? 'bg-red-950/30 text-red-500 border border-red-900/30' : 'bg-blue-950/30 text-blue-400 border border-blue-900/30'
                          }`}>{row.driver_code}</span>
                        </td>
                        <td className="py-2.5 text-center text-neutral-300 font-mono">{row.entry_score.toFixed(1)}</td>
                        <td className="py-2.5 text-center text-neutral-300 font-mono">{row.apex_score.toFixed(1)}</td>
                        <td className="py-2.5 text-center text-neutral-300 font-mono">{row.exit_score.toFixed(1)}</td>
                        <td className="py-2.5 text-right font-black text-white font-mono">{row.cpi.toFixed(1)}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>

            {/* Engineering Insights */}
            <div className="lg:col-span-4 rounded-xl border border-neutral-900 bg-neutral-950/20 p-5 flex flex-col justify-between">
              <div>
                <h2 className="flex items-center gap-2 font-sans text-xs font-bold tracking-widest text-neutral-400 uppercase mb-4">
                  <span className="inline-block h-3.5 w-1 rounded bg-red-600"></span>
                  Engineering Insights
                </h2>
                <div className="space-y-3.5 max-h-[360px] overflow-y-auto pr-1 text-xs">
                  {data.engineering_insights.map((insight) => (
                    <div key={insight.corner_number} className="rounded-lg border border-neutral-900 bg-neutral-950/40 p-3">
                      <div className="flex justify-between items-center font-mono">
                        <span className="text-white font-bold">Turn {insight.corner_number}</span>
                        <span className={`font-black ${insight.delta_s > 0 ? 'text-red-500' : 'text-blue-500'}`}>
                          {insight.delta_s > 0 ? `+${insight.delta_s.toFixed(3)}s` : `${insight.delta_s.toFixed(3)}s`}
                        </span>
                      </div>
                      <p className="mt-1.5 text-neutral-400 font-medium">
                        <span className={insight.delta_s > 0 ? 'text-red-400 font-semibold' : 'text-blue-400 font-semibold'}>
                          {insight.driver_gaining}
                        </span>{' '}
                        gains {insight.reason}.
                      </p>
                    </div>
                  ))}
                </div>
              </div>
            </div>

          </div>

        </div>
      )}

    </div>
  );
}
