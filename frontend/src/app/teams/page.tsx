'use client';

import React, { useEffect, useState } from 'react';
import { 
  Users2, 
  ChevronRight, 
  Activity, 
  ShieldCheck, 
  AlertTriangle 
} from 'lucide-react';
import PlotlyChart from '@/components/PlotlyChart';

interface TeamListItem {
  position: number;
  team: string;
  team_abbr: string;
  points: number;
  delta: number;
}

interface TeamsPayload {
  standings: TeamListItem[];
  points_chart: any;
}

interface ComparePayload {
  team_a: string;
  team_b: string;
  progression_chart: any;
  qualifying_chart: any;
  driver_contribution_a: any;
  driver_contribution_b: any;
  race_pace_chart: any;
}

export default function TeamsPage() {
  const [data, setData] = useState<TeamsPayload | null>(null);
  const [selectedTeamA, setSelectedTeamA] = useState<string>('Mercedes');
  const [selectedTeamB, setSelectedTeamB] = useState<string>('Ferrari');
  const [compareData, setCompareData] = useState<ComparePayload | null>(null);
  const [compareLoading, setCompareLoading] = useState(false);
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState<'standings' | 'compare'>('standings');
  const [error, setError] = useState<string | null>(null);

  const fetchComparison = (teamA: string, teamB: string) => {
    setCompareLoading(true);
    fetch(`http://127.0.0.1:8000/api/v1/teams/compare?team_a=${encodeURIComponent(teamA)}&team_b=${encodeURIComponent(teamB)}`)
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
    fetch('http://127.0.0.1:8000/api/v1/teams')
      .then((res) => {
        if (!res.ok) throw new Error('Failed to load constructor standings');
        return res.json();
      })
      .then((resData: TeamsPayload) => {
        setData(resData);
        setLoading(false);
        // Load default constructor comparisons
        fetchComparison('Mercedes', 'Ferrari');
      })
      .catch((err) => {
        setError(err.message);
        setLoading(false);
      });
  }, []);

  const handleCompareTrigger = (teamA: string, teamB: string) => {
    if (teamA === teamB) return;
    fetchComparison(teamA, teamB);
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

  const { standings, points_chart } = data;

  return (
    <div className="space-y-6">
      
      {/* Header selector */}
      <div className="rounded-xl border border-neutral-900 bg-neutral-950/30 p-5">
        <h1 className="text-2xl font-black text-white uppercase tracking-tight flex items-center gap-2">
          <Users2 className="h-6 w-6 text-red-600" />
          Constructor Standings
        </h1>
        <p className="text-xs text-neutral-500 font-mono uppercase tracking-wider mt-1">Season Standings & Head-to-Head Constructor Comparisons</p>
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
          Constructor Comparison
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
                Constructor Standings List
              </h2>
              
              <div className="overflow-x-auto">
                <table className="w-full text-left border-collapse">
                  <thead>
                    <tr className="border-b border-neutral-900 font-mono text-[10px] text-neutral-500 uppercase tracking-wider">
                      <th className="py-2 pl-2">Pos</th>
                      <th className="py-2">Constructor</th>
                      <th className="py-2 text-right">Points</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-neutral-900 text-sm">
                    {standings.map((s) => (
                      <tr key={s.team} className="hover:bg-neutral-950/60 transition-colors">
                        <td className="py-4 pl-2 font-mono font-bold text-neutral-400">P{s.position}</td>
                        <td className="py-4 font-semibold text-white">
                          <div className="flex items-center gap-2.5">
                            <span className="rounded bg-neutral-900 border border-neutral-800 px-1.5 py-0.5 font-mono text-xs font-extrabold text-red-500">{s.team_abbr}</span>
                            <span>{s.team}</span>
                          </div>
                        </td>
                        <td className="py-4 text-right font-black text-white font-mono">
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
                <div className="flex-1 w-full min-h-[500px]">
                  <PlotlyChart data={points_chart.data} layout={points_chart.layout} height="100%" />
                </div>
              )}
            </div>

          </div>

        </div>
      )}

      {/* TAB 2: CONSTRUCTOR COMPARISON */}
      {activeTab === 'compare' && (
        <div className="space-y-6">
          
          {/* Team Selectors panel */}
          <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 rounded-xl border border-neutral-900 bg-neutral-950/40 p-5">
            <div>
              <label className="block text-[10px] font-mono font-bold text-neutral-500 uppercase tracking-widest mb-1.5">Constructor A</label>
              <select 
                value={selectedTeamA} 
                onChange={(e) => {
                  setSelectedTeamA(e.target.value);
                  handleCompareTrigger(e.target.value, selectedTeamB);
                }}
                className="w-full rounded-lg border border-neutral-800 bg-neutral-950 px-3 py-2 text-sm font-semibold text-white focus:border-red-600 focus:outline-none"
              >
                {standings.map((s) => (
                  <option key={s.team} value={s.team} disabled={s.team === selectedTeamB}>
                    {s.team}
                  </option>
                ))}
              </select>
            </div>
            
            <div>
              <label className="block text-[10px] font-mono font-bold text-neutral-500 uppercase tracking-widest mb-1.5">Constructor B</label>
              <select 
                value={selectedTeamB} 
                onChange={(e) => {
                  setSelectedTeamB(e.target.value);
                  handleCompareTrigger(selectedTeamA, e.target.value);
                }}
                className="w-full rounded-lg border border-neutral-800 bg-neutral-950 px-3 py-2 text-sm font-semibold text-white focus:border-red-600 focus:outline-none"
              >
                {standings.map((s) => (
                  <option key={s.team} value={s.team} disabled={s.team === selectedTeamA}>
                    {s.team}
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
              
              {/* Point progression line */}
              <div className="rounded-xl border border-neutral-900 bg-neutral-950/20 p-5">
                <h2 className="flex items-center gap-2 font-sans text-xs font-bold tracking-widest text-neutral-400 uppercase mb-4">
                  <span className="inline-block h-3.5 w-1 rounded bg-red-600"></span>
                  Team Points Progression
                </h2>
                <PlotlyChart data={compareData.progression_chart.data} layout={compareData.progression_chart.layout} height={320} />
              </div>

              {/* Qualy vs Pace charts */}
              <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
                <div className="rounded-xl border border-neutral-900 bg-neutral-950/20 p-5">
                  <h2 className="flex items-center gap-2 font-sans text-xs font-bold tracking-widest text-neutral-400 uppercase mb-4">
                    <span className="inline-block h-3.5 w-1 rounded bg-red-600"></span>
                    Avg Qualifying Position (lower = better)
                  </h2>
                  <PlotlyChart data={compareData.qualifying_chart.data} layout={compareData.qualifying_chart.layout} height={300} />
                </div>
                
                <div className="rounded-xl border border-neutral-900 bg-neutral-950/20 p-5">
                  <h2 className="flex items-center gap-2 font-sans text-xs font-bold tracking-widest text-neutral-400 uppercase mb-4">
                    <span className="inline-block h-3.5 w-1 rounded bg-red-600"></span>
                    Avg Finish Position (lower = better)
                  </h2>
                  <PlotlyChart data={compareData.race_pace_chart.data} layout={compareData.race_pace_chart.layout} height={300} />
                </div>
              </div>

              {/* Driver split charts */}
              <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
                <div className="rounded-xl border border-neutral-900 bg-neutral-950/20 p-5">
                  <h2 className="flex items-center gap-2 font-sans text-xs font-bold tracking-widest text-neutral-400 uppercase mb-4">
                    <span className="inline-block h-3.5 w-1 rounded bg-red-600"></span>
                    {selectedTeamA} Driver Point Split
                  </h2>
                  <PlotlyChart data={compareData.driver_contribution_a.data} layout={compareData.driver_contribution_a.layout} height={280} />
                </div>
                
                <div className="rounded-xl border border-neutral-900 bg-neutral-950/20 p-5">
                  <h2 className="flex items-center gap-2 font-sans text-xs font-bold tracking-widest text-neutral-400 uppercase mb-4">
                    <span className="inline-block h-3.5 w-1 rounded bg-red-600"></span>
                    {selectedTeamB} Driver Point Split
                  </h2>
                  <PlotlyChart data={compareData.driver_contribution_b.data} layout={compareData.driver_contribution_b.layout} height={280} />
                </div>
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
