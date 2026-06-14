'use client';

import React, { useEffect, useState } from 'react';
import { 
  BarChart3, 
  Flag, 
  Activity, 
  AlertTriangle 
} from 'lucide-react';
import PlotlyChart from '@/components/PlotlyChart';

interface RaceItem {
  race_id: string;
  race_name: string;
}

interface DriverInfo {
  code: string;
  name: string;
  color: string;
}

interface AnalyticsPayload {
  races: RaceItem[];
  selected_race_id: string;
  drivers_in_race: DriverInfo[];
  selected_drivers: string[];
  charts: {
    lap_time_evolution: any;
    tyre_degradation: any;
    tyre_usage: any;
    position_changes: any;
    qualifying_vs_race: any;
    race_pace_distribution: any;
  };
}

export default function AnalyticsHubPage() {
  const [races, setRaces] = useState<RaceItem[]>([]);
  const [selectedRace, setSelectedRace] = useState<string>('');
  const [driversInRace, setDriversInRace] = useState<DriverInfo[]>([]);
  const [selectedDrivers, setSelectedDrivers] = useState<string[]>([]);
  
  const [charts, setCharts] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchAnalytics = (raceId: string, driverFilter: string[]) => {
    setLoading(true);
    let url = `http://127.0.0.1:8000/api/v1/analytics?race_id=${raceId}`;
    if (driverFilter && driverFilter.length > 0) {
      driverFilter.forEach((d) => {
        url += `&drivers=${d}`;
      });
    }

    fetch(url)
      .then((res) => res.json())
      .then((data: AnalyticsPayload) => {
        setDriversInRace(data.drivers_in_race || []);
        setSelectedDrivers(data.selected_drivers || []);
        setCharts(data.charts);
        setLoading(false);
      })
      .catch(() => setLoading(false));
  };

  // 1. Fetch initial setup (list of races)
  useEffect(() => {
    fetch('http://127.0.0.1:8000/api/v1/analytics')
      .then((res) => {
        if (!res.ok) throw new Error('Failed to load analytics GP list');
        return res.json();
      })
      .then((data: AnalyticsPayload) => {
        setRaces(data.races || []);
        if (data.races && data.races.length > 0) {
          const defaultRaceId = data.races[0].race_id;
          setSelectedRace(defaultRaceId);
          fetchAnalytics(defaultRaceId, []);
        } else {
          setLoading(false);
        }
      })
      .catch((err) => {
        setError(err.message);
        setLoading(false);
      });
  }, []);

  const handleRaceChange = (e: React.ChangeEvent<HTMLSelectElement>) => {
    const raceId = e.target.value;
    setSelectedRace(raceId);
    // Reset driver filter on race swap
    fetchAnalytics(raceId, []);
  };

  const handleToggleDriver = (code: string) => {
    let updated;
    if (selectedDrivers.includes(code)) {
      // Retain at least one driver
      if (selectedDrivers.length === 1) return;
      updated = selectedDrivers.filter((x) => x !== code);
    } else {
      updated = [...selectedDrivers, code];
    }
    setSelectedDrivers(updated);
    fetchAnalytics(selectedRace, updated);
  };

  if (loading && races.length === 0) {
    return (
      <div className="flex h-96 items-center justify-center">
        <div className="h-8 w-8 animate-spin rounded-full border-2 border-red-600 border-t-transparent"></div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="flex min-h-[400px] flex-col items-center justify-center rounded-xl border border-red-950/50 bg-red-950/10 p-6 text-center">
        <AlertTriangle className="mb-4 h-12 w-12 text-red-500" />
        <h3 className="text-lg font-bold text-white">Error Loading Analytics Hub</h3>
        <p className="mt-2 text-sm text-neutral-400">{error}</p>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      
      {/* Header filter selector bar */}
      <div className="grid grid-cols-1 md:grid-cols-12 gap-5 rounded-xl border border-neutral-900 bg-neutral-950/30 p-5 items-center">
        
        <div className="md:col-span-3">
          <h1 className="text-2xl font-black text-white uppercase tracking-tight flex items-center gap-2">
            <BarChart3 className="h-6 w-6 text-red-600" />
            Analytics Hub
          </h1>
          <p className="text-xs text-neutral-500 font-mono uppercase tracking-wider mt-1">Cross-Race telemetry & Pace breakdowns</p>
        </div>

        <div className="md:col-span-3 w-full">
          <label className="block text-[10px] font-mono font-bold text-neutral-500 uppercase tracking-widest mb-1.5">Select Grand Prix</label>
          <select 
            value={selectedRace} 
            onChange={handleRaceChange}
            className="w-full rounded-lg border border-neutral-800 bg-neutral-950 px-3 py-2 text-sm font-semibold text-white focus:border-red-600 focus:outline-none"
          >
            {races.map((r) => (
              <option key={r.race_id} value={r.race_id}>{r.race_name}</option>
            ))}
          </select>
        </div>

        {/* Interactive Driver Toggle Badges */}
        <div className="md:col-span-6 w-full">
          <label className="block text-[10px] font-mono font-bold text-neutral-500 uppercase tracking-widest mb-2">Toggle Drivers</label>
          <div className="flex flex-wrap gap-1.5">
            {driversInRace.map((d) => {
              const isSelected = selectedDrivers.includes(d.code);
              return (
                <button
                  key={d.code}
                  onClick={() => handleToggleDriver(d.code)}
                  className={`rounded px-2 py-0.5 text-[10px] font-mono font-black border transition-all duration-100 cursor-pointer ${
                    isSelected 
                      ? 'border-red-600/30 bg-red-950/20 text-red-500' 
                      : 'border-neutral-900 bg-neutral-950 text-neutral-600 hover:border-neutral-800 hover:text-neutral-400'
                  }`}
                >
                  {d.code}
                </button>
              );
            })}
          </div>
        </div>

      </div>

      {loading && (
        <div className="flex h-96 items-center justify-center rounded-xl border border-neutral-900 bg-neutral-950/10">
          <div className="h-8 w-8 animate-spin rounded-full border-2 border-red-600 border-t-transparent"></div>
        </div>
      )}

      {!loading && charts && (
        <div className="space-y-6">
          
          {/* Row 1: Lap Evolution & Position changes */}
          <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
            <div className="rounded-xl border border-neutral-900 bg-neutral-950/20 p-5">
              <h2 className="flex items-center gap-2 font-sans text-xs font-bold tracking-widest text-neutral-400 uppercase mb-4">
                <span className="inline-block h-3.5 w-1 rounded bg-red-600"></span>
                Lap Time Evolution
              </h2>
              <PlotlyChart data={charts.lap_time_evolution.data} layout={charts.lap_time_evolution.layout} height={320} />
            </div>

            <div className="rounded-xl border border-neutral-900 bg-neutral-950/20 p-5">
              <h2 className="flex items-center gap-2 font-sans text-xs font-bold tracking-widest text-neutral-400 uppercase mb-4">
                <span className="inline-block h-3.5 w-1 rounded bg-red-600"></span>
                Grid to Finish Changes
              </h2>
              <PlotlyChart data={charts.position_changes.data} layout={charts.position_changes.layout} height={550} />
            </div>
          </div>

          {/* Row 2: Tyre usage & degradation */}
          <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
            <div className="rounded-xl border border-neutral-900 bg-neutral-950/20 p-5">
              <h2 className="flex items-center gap-2 font-sans text-xs font-bold tracking-widest text-neutral-400 uppercase mb-4">
                <span className="inline-block h-3.5 w-1 rounded bg-red-600"></span>
                Tyre Compounding Usage
              </h2>
              <PlotlyChart data={charts.tyre_usage.data} layout={charts.tyre_usage.layout} height={320} />
            </div>

            <div className="rounded-xl border border-neutral-900 bg-neutral-950/20 p-5">
              <h2 className="flex items-center gap-2 font-sans text-xs font-bold tracking-widest text-neutral-400 uppercase mb-4">
                <span className="inline-block h-3.5 w-1 rounded bg-red-600"></span>
                Tyre Degradation Curves
              </h2>
              <PlotlyChart data={charts.tyre_degradation.data} layout={charts.tyre_degradation.layout} height={320} />
            </div>
          </div>

          {/* Row 3: Qualy vs Race Scatter & Pace Distribution */}
          <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
            <div className="rounded-xl border border-neutral-900 bg-neutral-950/20 p-5">
              <h2 className="flex items-center gap-2 font-sans text-xs font-bold tracking-widest text-neutral-400 uppercase mb-4">
                <span className="inline-block h-3.5 w-1 rounded bg-red-600"></span>
                Qualifying vs Finish Position Grid
              </h2>
              <PlotlyChart data={charts.qualifying_vs_race.data} layout={charts.qualifying_vs_race.layout} height={320} />
            </div>

            <div className="rounded-xl border border-neutral-900 bg-neutral-950/20 p-5">
              <h2 className="flex items-center gap-2 font-sans text-xs font-bold tracking-widest text-neutral-400 uppercase mb-4">
                <span className="inline-block h-3.5 w-1 rounded bg-red-600"></span>
                Pace Distribution Boxplot
              </h2>
              <PlotlyChart data={charts.race_pace_distribution.data} layout={charts.race_pace_distribution.layout} height={320} />
            </div>
          </div>

        </div>
      )}

    </div>
  );
}
