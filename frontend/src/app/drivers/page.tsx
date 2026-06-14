'use client';

import React, { useEffect, useState } from 'react';
import { 
  User, 
  ChevronRight, 
  Activity, 
  UserCheck, 
  AlertTriangle 
} from 'lucide-react';
import PlotlyChart from '@/components/PlotlyChart';

interface DriverListItem {
  position: number;
  driver_code: string;
  driver_name: string;
  country: string;
  color: string;
  team: string;
  points: number;
  wins: number;
  podiums: number;
  delta: number;
}

interface CompareStats {
  points: number;
  wins: number;
  podiums: number;
  avg_finish: number;
  avg_grid: number;
}

interface CompareDriverPayload {
  code: string;
  display: { name: string; country: string; color: string };
  stats: CompareStats;
}

interface DriversPayload {
  standings: DriverListItem[];
  points_chart: any;
  progression_chart: any;
}

interface ComparePayload {
  driver_a: CompareDriverPayload;
  driver_b: CompareDriverPayload;
  progression_chart: any;
  finish_trend_chart: any;
  head_to_head_chart: any;
}

export default function DriversPage() {
  const [data, setData] = useState<DriversPayload | null>(null);
  const [selectedDriverA, setSelectedDriverA] = useState<string>('ANT');
  const [selectedDriverB, setSelectedDriverB] = useState<string>('HAM');
  const [compareData, setCompareData] = useState<ComparePayload | null>(null);
  const [compareLoading, setCompareLoading] = useState(false);
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState<'standings' | 'compare'>('standings');
  const [error, setError] = useState<string | null>(null);

  const fetchComparison = (drvA: string, drvB: string) => {
    setCompareLoading(true);
    fetch(`http://127.0.0.1:8000/api/v1/drivers/compare?driver_a=${drvA}&driver_b=${drvB}`)
      .then((res) => {
        if (!res.ok) throw new Error('Comparison failed');
        return res.json();
      })
      .then((resData: ComparePayload) => {
        setCompareData(resData);
        setCompareLoading(false);
      })
      .catch(() => setCompareLoading(false));
  };

  useEffect(() => {
    fetch('http://127.0.0.1:8000/api/v1/drivers')
      .then((res) => {
        if (!res.ok) throw new Error('Failed to load driver standings');
        return res.json();
      })
      .then((resData: DriversPayload) => {
        setData(resData);
        setLoading(false);
        // Load default comparison
        fetchComparison('ANT', 'HAM');
      })
      .catch((err) => {
        setError(err.message);
        setLoading(false);
      });
  }, []);

  const handleCompareTrigger = (drvA: string, drvB: string) => {
    if (drvA === drvB) return;
    fetchComparison(drvA, drvB);
  };

  if (loading && !data) {
    return (
      <div className="flex h-96 items-center justify-center">
        <div className="h-8 w-8 animate-spin rounded-full border-2 border-red-600 border-t-transparent"></div>
      </div>
    );
  }

  if (error || !data) {
    return (
      <div className="flex min-h-[400px] flex-col items-center justify-center rounded-xl border border-red-950/50 bg-red-950/10 p-6 text-center">
        <AlertTriangle className="mb-4 h-12 w-12 text-red-500" />
        <h3 className="text-lg font-bold text-white">Error</h3>
        <p className="mt-2 text-sm text-neutral-400">{error}</p>
      </div>
    );
  }

  const { standings, points_chart, progression_chart } = data;

  return (
    <div className="space-y-6">
      
      {/* Header selector */}
      <div className="rounded-xl border border-neutral-900 bg-neutral-950/30 p-5">
        <h1 className="text-2xl font-black text-white uppercase tracking-tight flex items-center gap-2">
          <User className="h-6 w-6 text-red-600" />
          Driver standings
        </h1>
        <p className="text-xs text-neutral-500 font-mono uppercase tracking-wider mt-1">Season Standings & Head-to-Head Comparison</p>
      </div>

      {/* Tabs */}
      <div className="flex border-b border-neutral-900">
        <button
          onClick={() => setActiveTab('standings')}
          className={`px-5 py-3 text-xs font-bold uppercase tracking-widest transition-all ${
            activeTab === 'standings' 
              ? 'border-b-2 border-red-600 text-white bg-neutral-950/20' 
              : 'text-neutral-500 hover:text-neutral-300'
          }`}
        >
          Standings
        </button>
        <button
          onClick={() => setActiveTab('compare')}
          className={`px-5 py-3 text-xs font-bold uppercase tracking-widest transition-all ${
            activeTab === 'compare' 
              ? 'border-b-2 border-red-600 text-white bg-neutral-950/20' 
              : 'text-neutral-500 hover:text-neutral-300'
          }`}
        >
          Driver Comparison
        </button>
      </div>

      {/* TAB 1: STANDINGS */}
      {activeTab === 'standings' && (
        <div className="space-y-6">
          
          <div className="grid grid-cols-1 gap-6 lg:grid-cols-12">
            
            {/* Table */}
            <div className="lg:col-span-8 rounded-xl border border-neutral-900 bg-neutral-950/20 p-5">
              <h2 className="flex items-center gap-2 font-sans text-xs font-bold tracking-widest text-neutral-400 uppercase mb-4">
                <span className="inline-block h-3.5 w-1 rounded bg-red-600"></span>
                Driver Standings list
              </h2>
              
              <div className="overflow-x-auto">
                <table className="w-full text-left border-collapse">
                  <thead>
                    <tr className="border-b border-neutral-900 font-mono text-[10px] text-neutral-500 uppercase tracking-wider">
                      <th className="py-2 pl-2">Pos</th>
                      <th className="py-2">Driver</th>
                      <th className="py-2">Team</th>
                      <th className="py-2 text-center">Wins</th>
                      <th className="py-2 text-center">Podiums</th>
                      <th className="py-2 text-right">Points</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-neutral-900 text-sm">
                    {standings.map((s) => (
                      <tr key={s.driver_code} className="hover:bg-neutral-950/60 transition-colors">
                        <td className="py-3.5 pl-2 font-mono font-bold text-neutral-400">P{s.position}</td>
                        <td className="py-3.5 font-semibold text-white">
                          <div className="flex items-center gap-2.5">
                            <span className="w-1 h-3 rounded-[1px]" style={{ backgroundColor: s.color }}></span>
                            <span>{s.driver_name}</span>
                            <span className="rounded bg-neutral-900 px-1.5 py-0.5 text-[9px] font-mono text-neutral-500">{s.driver_code}</span>
                          </div>
                        </td>
                        <td className="py-3.5 text-neutral-400 font-medium">{s.team}</td>
                        <td className="py-3.5 text-center font-mono text-neutral-300">{s.wins}</td>
                        <td className="py-3.5 text-center font-mono text-neutral-300">{s.podiums}</td>
                        <td className="py-3.5 text-right font-black text-white font-mono">
                          {s.points}
                          {s.delta > 0 && <span className="text-[10px] text-green-500 ml-1.5 font-normal">+{s.delta}</span>}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>

            {/* Standings bar chart */}
            <div className="lg:col-span-4 rounded-xl border border-neutral-900 bg-neutral-950/20 p-5 flex flex-col">
              <h2 className="flex items-center gap-2 font-sans text-xs font-bold tracking-widest text-neutral-400 uppercase mb-4">
                <span className="inline-block h-3.5 w-1 rounded bg-red-600"></span>
                Points overview
              </h2>
              {points_chart && (
                <div className="flex-1 w-full min-h-[550px]">
                  <PlotlyChart data={points_chart.data} layout={points_chart.layout} height="100%" />
                </div>
              )}
            </div>

          </div>

          {/* Points progression line */}
          {progression_chart && (
            <div className="rounded-xl border border-neutral-900 bg-neutral-950/20 p-5">
              <h2 className="flex items-center gap-2 font-sans text-xs font-bold tracking-widest text-neutral-400 uppercase mb-4">
                <span className="inline-block h-3.5 w-1 rounded bg-red-600"></span>
                Points Progression (Top 10 Drivers)
              </h2>
              <PlotlyChart data={progression_chart.data} layout={progression_chart.layout} height={340} />
            </div>
          )}

        </div>
      )}

      {/* TAB 2: DRIVER COMPARISON */}
      {activeTab === 'compare' && (
        <div className="space-y-6">
          
          {/* Driver Selectors panel */}
          <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 rounded-xl border border-neutral-900 bg-neutral-950/40 p-5">
            <div>
              <label className="block text-[10px] font-mono font-bold text-neutral-500 uppercase tracking-widest mb-1.5">Driver A</label>
              <select 
                value={selectedDriverA} 
                onChange={(e) => {
                  setSelectedDriverA(e.target.value);
                  handleCompareTrigger(e.target.value, selectedDriverB);
                }}
                className="w-full rounded-lg border border-neutral-800 bg-neutral-950 px-3 py-2 text-sm font-semibold text-white focus:border-red-600 focus:outline-none"
              >
                {standings.map((s) => (
                  <option key={s.driver_code} value={s.driver_code} disabled={s.driver_code === selectedDriverB}>
                    {s.driver_name} ({s.driver_code})
                  </option>
                ))}
              </select>
            </div>
            
            <div>
              <label className="block text-[10px] font-mono font-bold text-neutral-500 uppercase tracking-widest mb-1.5">Driver B</label>
              <select 
                value={selectedDriverB} 
                onChange={(e) => {
                  setSelectedDriverB(e.target.value);
                  handleCompareTrigger(selectedDriverA, e.target.value);
                }}
                className="w-full rounded-lg border border-neutral-800 bg-neutral-950 px-3 py-2 text-sm font-semibold text-white focus:border-red-600 focus:outline-none"
              >
                {standings.map((s) => (
                  <option key={s.driver_code} value={s.driver_code} disabled={s.driver_code === selectedDriverA}>
                    {s.driver_name} ({s.driver_code})
                  </option>
                ))}
              </select>
            </div>
          </div>

          {compareLoading ? (
            <div className="flex h-72 items-center justify-center">
              <div className="h-6 w-6 animate-spin rounded-full border-2 border-red-600 border-t-transparent"></div>
            </div>
          ) : compareData ? (
            <div className="space-y-6">
              
              {/* Head-to-Head KPI comparisons grid */}
              <div className="grid grid-cols-2 gap-4 sm:grid-cols-5">
                {[
                  { label: 'Points', key: 'points' },
                  { label: 'Race Wins', key: 'wins' },
                  { label: 'Podiums', key: 'podiums' },
                  { label: 'Avg Finish Pos', key: 'avg_finish' },
                  { label: 'Avg Grid Pos', key: 'avg_grid' },
                ].map((item) => (
                  <div key={item.key} className="rounded-xl border border-neutral-900 bg-neutral-950/20 p-4 text-center">
                    <p className="font-mono text-[9px] font-bold text-neutral-500 uppercase tracking-wider">{item.label}</p>
                    <div className="mt-3 flex items-baseline justify-center gap-1.5">
                      <span className="text-lg font-black text-red-500">{(compareData.driver_a.stats as any)[item.key]}</span>
                      <span className="text-[10px] text-neutral-600 font-bold uppercase">vs</span>
                      <span className="text-lg font-black text-blue-500">{(compareData.driver_b.stats as any)[item.key]}</span>
                    </div>
                  </div>
                ))}
              </div>

              {/* Point progression + position trend charts */}
              <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
                <div className="rounded-xl border border-neutral-900 bg-neutral-950/20 p-5">
                  <h2 className="flex items-center gap-2 font-sans text-xs font-bold tracking-widest text-neutral-400 uppercase mb-4">
                    <span className="inline-block h-3.5 w-1 rounded bg-red-600"></span>
                    Points Progression
                  </h2>
                  <PlotlyChart data={compareData.progression_chart.data} layout={compareData.progression_chart.layout} height={300} />
                </div>
                
                <div className="rounded-xl border border-neutral-900 bg-neutral-950/20 p-5">
                  <h2 className="flex items-center gap-2 font-sans text-xs font-bold tracking-widest text-neutral-400 uppercase mb-4">
                    <span className="inline-block h-3.5 w-1 rounded bg-red-600"></span>
                    Finishing Position Trend
                  </h2>
                  <PlotlyChart data={compareData.finish_trend_chart.data} layout={compareData.finish_trend_chart.layout} height={300} />
                </div>
              </div>

              {/* Group Bar comparisons */}
              <div className="rounded-xl border border-neutral-900 bg-neutral-950/20 p-5">
                <h2 className="flex items-center gap-2 font-sans text-xs font-bold tracking-widest text-neutral-400 uppercase mb-4">
                  <span className="inline-block h-3.5 w-1 rounded bg-red-600"></span>
                  Head to Head comparison
                </h2>
                <PlotlyChart data={compareData.head_to_head_chart.data} layout={compareData.head_to_head_chart.layout} height={320} />
              </div>

            </div>
          ) : (
            <div className="flex h-48 items-center justify-center text-xs text-neutral-500">
              No comparison metrics generated.
            </div>
          )}

        </div>
      )}

    </div>
  );
}
