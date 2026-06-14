'use client';

import React, { useEffect, useState } from 'react';
import { 
  BrainCircuit, 
  Info, 
  Trophy, 
  AlertTriangle 
} from 'lucide-react';
import PlotlyChart from '@/components/PlotlyChart';

interface PredictionItem {
  position: number;
  driver_code: string;
  driver_name: string;
  country: string;
  color: string;
  team: string;
  grid_pos: number;
  win_probability: number;
}

interface Insights {
  model_type: string;
  features_used: string;
  training_source: string;
}

interface PredictionsPayload {
  race_id: string;
  circuit: string;
  data_source: string;
  predictions: PredictionItem[];
  win_prob_chart: any;
  insights: Insights;
}

export default function PredictionsPage() {
  const [data, setData] = useState<PredictionsPayload | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    fetch('http://127.0.0.1:8000/api/v1/predictions')
      .then((res) => {
        if (!res.ok) throw new Error('Failed to load predictions');
        return res.json();
      })
      .then((resData: PredictionsPayload) => {
        setData(resData);
        setLoading(false);
      })
      .catch((err) => {
        setError(err.message);
        setLoading(false);
      });
  }, []);

  if (loading) {
    return (
      <div className="flex h-96 items-center justify-center">
        <div className="h-8 w-8 animate-spin rounded-full border-2 border-red-600 border-t-transparent"></div>
      </div>
    );
  }

  if (error || !data || !data.race_id) {
    return (
      <div className="flex min-h-[400px] flex-col items-center justify-center rounded-xl border border-neutral-900 bg-neutral-950/20 p-6 text-center">
        <BrainCircuit className="mb-4 h-12 w-12 text-neutral-600" />
        <h3 className="text-lg font-bold text-white">No Predictions Loaded</h3>
        <p className="mt-2 text-sm text-neutral-500 max-w-md">
          Predictions will appear here once qualifying or practice telemetry for the upcoming round has been ingested.
        </p>
      </div>
    );
  }

  const { race_id, circuit, data_source, predictions, win_prob_chart, insights } = data;
  const top3 = predictions.slice(0, 3);
  const remainder = predictions.slice(3);

  const medalStyles = [
    { border: 'border-yellow-500/30', bg: 'bg-yellow-500/5', badge: 'bg-yellow-500/10 text-yellow-500 border-yellow-500/20', text: 'text-yellow-400', rank: '🥇 P1 Predicted' },
    { border: 'border-slate-400/30', bg: 'bg-slate-400/5', badge: 'bg-slate-400/10 text-slate-400 border-slate-400/20', text: 'text-slate-300', rank: '🥈 P2 Predicted' },
    { border: 'border-amber-600/30', bg: 'bg-amber-600/5', badge: 'bg-amber-600/10 text-amber-600 border-amber-600/20', text: 'text-amber-500', rank: '🥉 P3 Predicted' }
  ];

  return (
    <div className="space-y-6">
      
      {/* Header bar */}
      <div className="rounded-xl border border-neutral-900 bg-neutral-950/30 p-5">
        <h1 className="text-2xl font-black text-white uppercase tracking-tight flex items-center gap-2">
          <BrainCircuit className="h-6 w-6 text-red-600" />
          Race Predictions
        </h1>
        <p className="text-xs text-neutral-500 font-mono uppercase tracking-wider mt-1">Race Weekend Intelligence Center</p>
      </div>

      {/* Prediction Source Banner */}
      <div className="flex items-center gap-3 rounded-lg border border-red-950/40 bg-red-950/10 p-4 text-sm text-neutral-400">
        <Info className="h-5 w-5 text-red-600 flex-shrink-0" />
        <span>
          Analyzing Round: <strong className="text-white">{race_id}</strong> — <strong className="text-white">{circuit}</strong>. 
          Source: <strong className="text-red-500 uppercase">{data_source}</strong>. 
          Win projections are calculated live using current race weekend parameters.
        </span>
      </div>

      {/* Top 3 Hero Cards */}
      <div className="grid grid-cols-1 gap-6 sm:grid-cols-3">
        {top3.map((p, idx) => {
          const style = medalStyles[idx];
          return (
            <div key={p.driver_code} className={`relative overflow-hidden rounded-xl border ${style.border} ${style.bg} p-6 text-center hover:scale-[1.02] transition-all duration-200`}>
              <div className={`mx-auto mb-3 flex h-10 w-24 items-center justify-center rounded-full border text-[10px] font-mono font-bold uppercase tracking-wider ${style.badge}`}>
                {style.rank}
              </div>
              <p className="text-lg font-black text-white">{p.driver_name}</p>
              <p className="text-xs font-medium text-neutral-500 mt-0.5">{p.team}</p>
              <div className="mt-4">
                <span className={`text-3xl font-black tracking-tight ${style.text}`}>{(p.win_probability * 100).toFixed(1)}%</span>
                <span className="block text-[9px] font-mono font-bold text-neutral-500 uppercase tracking-widest mt-1">Win Probability</span>
              </div>
            </div>
          );
        })}
      </div>

      {/* Win probability distribution chart */}
      {win_prob_chart && (
        <div className="rounded-xl border border-neutral-900 bg-neutral-950/20 p-5">
          <h2 className="flex items-center gap-2 font-sans text-xs font-bold tracking-widest text-neutral-400 uppercase mb-4">
            <span className="inline-block h-3.5 w-1 rounded bg-red-600"></span>
            Win Probability Distribution
          </h2>
          <PlotlyChart data={win_prob_chart.data} layout={win_prob_chart.layout} height={380} />
        </div>
      )}

      {/* Bottom details block */}
      <div className="grid grid-cols-1 gap-6 lg:grid-cols-12">
        
        {/* Left: Table */}
        <div className="lg:col-span-8 rounded-xl border border-neutral-900 bg-neutral-950/20 p-5">
          <h2 className="flex items-center gap-2 font-sans text-xs font-bold tracking-widest text-neutral-400 uppercase mb-4">
            <span className="inline-block h-3.5 w-1 rounded bg-red-600"></span>
            Full Win Probability Table
          </h2>
          <div className="overflow-x-auto">
            <table className="w-full text-left border-collapse">
              <thead>
                <tr className="border-b border-neutral-900 font-mono text-[10px] text-neutral-500 uppercase tracking-wider">
                  <th className="py-2 pl-2">Grid</th>
                  <th className="py-2">Driver</th>
                  <th className="py-2">Team</th>
                  <th className="py-2 text-right">Win Probability</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-neutral-900 text-sm">
                {predictions.map((p) => (
                  <tr key={p.driver_code} className="hover:bg-neutral-950/60 transition-colors">
                    <td className="py-3 pl-2 font-mono font-bold text-neutral-500">P{p.grid_pos}</td>
                    <td className="py-3 font-semibold text-white">
                      <div className="flex items-center gap-2">
                        <span className="w-1 h-3 rounded-[1px]" style={{ backgroundColor: p.color }}></span>
                        <span>{p.driver_name}</span>
                        <span className="rounded bg-neutral-900 px-1 py-0.5 text-[9px] font-mono text-neutral-500">{p.driver_code}</span>
                      </div>
                    </td>
                    <td className="py-3 text-neutral-400 font-medium">{p.team}</td>
                    <td className="py-3 text-right font-mono font-bold text-red-500">{(p.win_probability * 100).toFixed(2)}%</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>

        {/* Right: Model Info cards */}
        <div className="lg:col-span-4 space-y-4 flex flex-col">
          <div className="rounded-xl border border-neutral-900 bg-neutral-950/40 p-5">
            <p className="font-mono text-[10px] font-bold text-neutral-500 uppercase tracking-wider">Model Architecture</p>
            <p className="text-base font-black text-white mt-1.5">{insights.model_type}</p>
          </div>
          
          <div className="rounded-xl border border-neutral-900 bg-neutral-950/40 p-5">
            <p className="font-mono text-[10px] font-bold text-neutral-500 uppercase tracking-wider">Historical Context Source</p>
            <p className="text-base font-black text-white mt-1.5 truncate">{insights.training_source}</p>
          </div>

          <div className="flex-1 rounded-xl border border-neutral-900 bg-neutral-950/40 p-5">
            <p className="font-mono text-[10px] font-bold text-neutral-500 uppercase tracking-wider">Inference Features</p>
            <p className="text-xs text-neutral-400 leading-relaxed mt-2.5">{insights.features_used}</p>
          </div>
        </div>

      </div>

    </div>
  );
}
