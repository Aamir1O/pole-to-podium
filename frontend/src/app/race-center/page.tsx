'use client';

import React, { useEffect, useState } from 'react';
import { 
  Trophy, 
  Flag, 
  BarChart2, 
  LineChart, 
  Sliders, 
  Activity, 
  Eye,
  AlertTriangle
} from 'lucide-react';
import PlotlyChart from '@/components/PlotlyChart';
import { API_URL } from '@/lib/api';

interface RaceItem {
  race_id: string;
  race_name: string;
}

interface DriverInRace {
  code: string;
  name: string;
  color: string;
}

interface TelemetryData {
  grid: number[];
  driver_a: {
    speed: number[];
    throttle: number[];
    brake: boolean[];
    gear: number[];
    lap_time: number;
  };
  driver_b: {
    speed: number[];
    throttle: number[];
    brake: boolean[];
    gear: number[];
    lap_time: number;
  };
  delta: number[];
}

interface TelemetryPayload {
  driver_a_meta: { name: string; code: string; color: string };
  driver_b_meta: { name: string; code: string; color: string };
  telemetry: TelemetryData;
}

export default function RaceCenterPage() {
  const [races, setRaces] = useState<RaceItem[]>([]);
  const [selectedRace, setSelectedRace] = useState<string>('');
  const [analyticsData, setAnalyticsData] = useState<any>(null);
  const [telemetryData, setTelemetryData] = useState<TelemetryPayload | null>(null);
  const [telemetryLoading, setTelemetryLoading] = useState(false);
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState<'overview' | 'analytics' | 'telemetry'>('overview');
  const [error, setError] = useState<string | null>(null);
  const [selectedDrivers, setSelectedDrivers] = useState<string[]>([]);

  const fetchTelemetry = (round: number, drvA: string, drvB: string) => {
    setTelemetryLoading(true);
    fetch(`${API_URL}/api/v1/telemetry?season=2026&round=${round}&session=R&driver_a=${drvA}&driver_b=${drvB}`)
      .then((res) => {
        if (!res.ok) throw new Error('No telemetry');
        return res.json();
      })
      .then((data) => {
        setTelemetryData(data);
        setTelemetryLoading(false);
      })
      .catch(() => {
        setTelemetryData(null);
        setTelemetryLoading(false);
      });
  };

  const fetchRaceDetails = (raceId: string, driverCodes?: string[]) => {
    setLoading(true);
    let url = `${API_URL}/api/v1/analytics?race_id=${raceId}`;
    if (driverCodes && driverCodes.length > 0) {
      const queryParams = new URLSearchParams();
      queryParams.append('race_id', raceId);
      driverCodes.forEach(d => queryParams.append('drivers', d));
      url = `${API_URL}/api/v1/analytics?${queryParams.toString()}`;
    }
    fetch(url)
      .then((res) => res.json())
      .then((data) => {
        setAnalyticsData(data);
        if (data.selected_drivers) {
          setSelectedDrivers(data.selected_drivers);
        }
        setLoading(false);
        
        // Auto-fetch telemetry for the top two drivers in this race if finished
        const roundNum = parseInt(raceId.split('_R')[1], 10);
        if (data.drivers_in_race && data.drivers_in_race.length >= 2) {
          const drvA = data.drivers_in_race[0].code;
          const drvB = data.drivers_in_race[1].code;
          fetchTelemetry(roundNum, drvA, drvB);
        } else {
          setTelemetryData(null);
        }
      })
      .catch(() => setLoading(false));
  };

  // 1. Fetch initial list of races and default analytics
  useEffect(() => {
    fetch(`${API_URL}/api/v1/analytics`)
      .then((res) => {
        if (!res.ok) throw new Error('Failed to load F1 races list');
        return res.json();
      })
      .then((data) => {
        setRaces(data.races || []);
        if (data.races && data.races.length > 0) {
          const defaultRaceId = data.races[0].race_id;
          setSelectedRace(defaultRaceId);
          fetchRaceDetails(defaultRaceId);
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
    fetchRaceDetails(raceId);
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
        <h3 className="text-lg font-bold text-white">Error Loading Race Center</h3>
        <p className="mt-2 text-sm text-neutral-400">{error}</p>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      
      {/* Header Selector bar */}
      <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between rounded-xl border border-neutral-900 bg-neutral-950/30 p-5">
        <div>
          <h1 className="text-2xl font-black text-white uppercase tracking-tight flex items-center gap-2">
            <Flag className="h-6 w-6 text-red-600" />
            Race Center
          </h1>
          <p className="text-xs text-neutral-500 font-mono uppercase tracking-wider mt-1">Flagship Race Intelligence Center</p>
        </div>
        
        {/* Race Selector dropdown */}
        <div className="w-full sm:w-72">
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
      </div>

      {analyticsData && (
        <div className="space-y-6">
          
          {/* Navigation tabs */}
          <div className="flex border-b border-neutral-900">
            {(['overview', 'analytics', 'telemetry'] as const).map((tab) => (
              <button
                key={tab}
                onClick={() => setActiveTab(tab)}
                className={`px-5 py-3 text-xs font-bold uppercase tracking-widest transition-all ${
                  activeTab === tab 
                    ? 'border-b-2 border-red-600 text-white bg-neutral-950/20' 
                    : 'text-neutral-500 hover:text-neutral-300'
                }`}
              >
                {tab}
              </button>
            ))}
          </div>

          {/* TAB 1: OVERVIEW */}
          {activeTab === 'overview' && (
            <div className="grid grid-cols-1 gap-6 lg:grid-cols-12">
              
              {/* Left Column: Grid change charts */}
              <div className="lg:col-span-7 rounded-xl border border-neutral-900 bg-neutral-950/20 p-5">
                <h2 className="flex items-center gap-2 font-sans text-xs font-bold tracking-widest text-neutral-400 uppercase mb-4">
                  <span className="inline-block h-3.5 w-1 rounded bg-red-600"></span>
                  Grid to Finish Positions
                </h2>
                {analyticsData.charts.position_changes ? (
                  <PlotlyChart 
                    data={analyticsData.charts.position_changes.data} 
                    layout={analyticsData.charts.position_changes.layout} 
                    height={400} 
                  />
                ) : (
                  <div className="flex h-64 items-center justify-center text-xs text-neutral-500">
                    Position change telemetry not loaded.
                  </div>
                )}
              </div>

              {/* Right Column: Driver list/Results */}
              <div className="lg:col-span-5 rounded-xl border border-neutral-900 bg-neutral-950/20 p-5 flex flex-col justify-between">
                <div>
                  <h2 className="flex items-center gap-2 font-sans text-xs font-bold tracking-widest text-neutral-400 uppercase mb-4">
                    <span className="inline-block h-3.5 w-1 rounded bg-red-600"></span>
                    Grand Prix Finishers
                  </h2>
                  <div className="space-y-2 max-h-[380px] overflow-y-auto pr-1">
                    {analyticsData.drivers_in_race.map((d: DriverInRace, idx: number) => (
                      <div key={d.code} className="flex items-center justify-between rounded-lg border border-neutral-900 bg-neutral-950/40 p-3">
                        <div className="flex items-center gap-2.5">
                          <span className="font-mono text-xs font-bold text-neutral-500">P{idx + 1}</span>
                          <span className="w-1 h-3 rounded-[1px]" style={{ backgroundColor: d.color }}></span>
                          <span className="text-sm font-bold text-white">{d.name}</span>
                        </div>
                        <span className="rounded bg-neutral-900 px-2 py-0.5 font-mono text-xs font-bold text-neutral-400">{d.code}</span>
                      </div>
                    ))}
                  </div>
                </div>
              </div>

            </div>
          )}

          {/* TAB 2: IN-DEPTH ANALYTICS */}
          {activeTab === 'analytics' && (
            <div className="space-y-6">
              
              {/* Driver Filter Selector */}
              <div className="rounded-xl border border-neutral-900 bg-neutral-950/30 p-5 space-y-3">
                <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-2">
                  <div>
                    <h3 className="text-xs font-bold text-white uppercase tracking-wider flex items-center gap-2">
                      <Sliders className="h-4 w-4 text-red-600" />
                      Filter Drivers to Analyze
                    </h3>
                    <p className="text-[10px] text-neutral-500 mt-1">Select which drivers' data to compare in the charts below (maximum recommended: 8-10 for readability)</p>
                  </div>
                  <div className="flex gap-2">
                    <button
                      onClick={() => {
                        const allCodes = analyticsData.drivers_in_race.map((d: any) => d.code);
                        setSelectedDrivers(allCodes);
                        fetchRaceDetails(selectedRace, allCodes);
                      }}
                      className="px-2.5 py-1 text-[9px] font-mono font-bold text-neutral-400 bg-neutral-900 border border-neutral-850 rounded hover:text-white hover:border-neutral-700 transition"
                    >
                      SELECT ALL
                    </button>
                    <button
                      onClick={() => {
                        const topOne = [analyticsData.drivers_in_race[0].code];
                        setSelectedDrivers(topOne);
                        fetchRaceDetails(selectedRace, topOne);
                      }}
                      className="px-2.5 py-1 text-[9px] font-mono font-bold text-neutral-400 bg-neutral-900 border border-neutral-850 rounded hover:text-white hover:border-neutral-700 transition"
                    >
                      CLEAR
                    </button>
                  </div>
                </div>

                <div className="flex flex-wrap gap-2 pt-1">
                  {analyticsData.drivers_in_race.map((d: DriverInRace) => {
                    const isSelected = selectedDrivers.includes(d.code);
                    return (
                      <button
                        key={d.code}
                        onClick={() => {
                          let newSelected: string[];
                          if (isSelected) {
                            if (selectedDrivers.length <= 1) return;
                            newSelected = selectedDrivers.filter(c => c !== d.code);
                          } else {
                            newSelected = [...selectedDrivers, d.code];
                          }
                          setSelectedDrivers(newSelected);
                          fetchRaceDetails(selectedRace, newSelected);
                        }}
                        className={`flex items-center gap-2 px-3 py-1.5 rounded-lg border text-xs font-bold uppercase transition ${
                          isSelected
                            ? 'bg-neutral-950 border-red-600 text-white shadow-[0_0_8px_rgba(225,6,0,0.15)]'
                            : 'bg-neutral-950/20 border-neutral-900 text-neutral-500 hover:border-neutral-800 hover:text-neutral-400'
                        }`}
                      >
                        <span className="w-1.5 h-3 rounded-[1px]" style={{ backgroundColor: d.color }}></span>
                        <span>{d.code}</span>
                      </button>
                    );
                  })}
                </div>
              </div>

              {/* Row 1: Tyre Strategy & Degradation */}
              <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
                <div className="rounded-xl border border-neutral-900 bg-neutral-950/20 p-5">
                  <h2 className="flex items-center gap-2 font-sans text-xs font-bold tracking-widest text-neutral-400 uppercase mb-4">
                    <span className="inline-block h-3.5 w-1 rounded bg-red-600"></span>
                    Tyre Strategy (Laps per compound)
                  </h2>
                  <PlotlyChart 
                    data={analyticsData.charts.tyre_usage.data} 
                    layout={analyticsData.charts.tyre_usage.layout} 
                    height={320} 
                  />
                </div>
                
                <div className="rounded-xl border border-neutral-900 bg-neutral-950/20 p-5">
                  <h2 className="flex items-center gap-2 font-sans text-xs font-bold tracking-widest text-neutral-400 uppercase mb-4">
                    <span className="inline-block h-3.5 w-1 rounded bg-red-600"></span>
                    Tyre Degradation (Avg pace vs Age)
                  </h2>
                  <PlotlyChart 
                    data={analyticsData.charts.tyre_degradation.data} 
                    layout={analyticsData.charts.tyre_degradation.layout} 
                    height={320} 
                  />
                </div>
              </div>

              {/* Row 2: Qualifying vs Finish & Pace Dispersion */}
              <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
                <div className="rounded-xl border border-neutral-900 bg-neutral-950/20 p-5">
                  <h2 className="flex items-center gap-2 font-sans text-xs font-bold tracking-widest text-neutral-400 uppercase mb-4">
                    <span className="inline-block h-3.5 w-1 rounded bg-red-600"></span>
                    Qualifying Position vs Finish Position
                  </h2>
                  <PlotlyChart 
                    data={analyticsData.charts.qualifying_vs_race.data} 
                    layout={analyticsData.charts.qualifying_vs_race.layout} 
                    height={320} 
                  />
                </div>
                
                <div className="rounded-xl border border-neutral-900 bg-neutral-950/20 p-5">
                  <h2 className="flex items-center gap-2 font-sans text-xs font-bold tracking-widest text-neutral-400 uppercase mb-4">
                    <span className="inline-block h-3.5 w-1 rounded bg-red-600"></span>
                    Race Pace Distribution (Boxplot)
                  </h2>
                  <PlotlyChart 
                    data={analyticsData.charts.race_pace_distribution.data} 
                    layout={analyticsData.charts.race_pace_distribution.layout} 
                    height={320} 
                  />
                </div>
              </div>

            </div>
          )}

          {/* TAB 3: TELEMETRY HIGHLIGHTS */}
          {activeTab === 'telemetry' && (
            <div className="rounded-xl border border-neutral-900 bg-neutral-950/20 p-5">
              <div className="flex items-center justify-between mb-4">
                <h2 className="flex items-center gap-2 font-sans text-xs font-bold tracking-widest text-neutral-400 uppercase">
                  <span className="inline-block h-3.5 w-1 rounded bg-red-600"></span>
                  Top 2 Telemetry Comparison
                </h2>
                
                {telemetryData && (
                  <div className="flex items-center gap-2 font-mono text-[10px] font-bold text-neutral-500 uppercase">
                    <span className="text-red-500">{telemetryData.driver_a_meta.code}</span>
                    <span>vs</span>
                    <span className="text-blue-500">{telemetryData.driver_b_meta.code}</span>
                  </div>
                )}
              </div>

              {telemetryLoading ? (
                <div className="flex h-72 items-center justify-center">
                  <div className="h-6 w-6 animate-spin rounded-full border-2 border-red-600 border-t-transparent"></div>
                </div>
              ) : telemetryData ? (
                <div className="space-y-4">
                  {/* Speed telemetry visualization using client Plotly */}
                  <PlotlyChart 
                    data={[
                      {
                        x: telemetryData.telemetry.grid,
                        y: telemetryData.telemetry.driver_a.speed,
                        name: telemetryData.driver_a_meta.code,
                        type: 'scatter',
                        mode: 'lines',
                        line: { color: '#e10600', width: 2 }
                      },
                      {
                        x: telemetryData.telemetry.grid,
                        y: telemetryData.telemetry.driver_b.speed,
                        name: telemetryData.driver_b_meta.code,
                        type: 'scatter',
                        mode: 'lines',
                        line: { color: '#3B8BD4', width: 2 }
                      }
                    ]} 
                    layout={{
                      title: 'Lap Speed Trace (km/h)',
                      xaxis: { title: 'Distance (m)', gridcolor: '#111' },
                      yaxis: { title: 'Speed', gridcolor: '#111' },
                      legend: { orientation: 'h', y: 1.15 }
                    }} 
                    height={320} 
                  />
                  
                  <div className="rounded-lg border border-neutral-900 bg-neutral-950 p-4 text-xs font-mono text-neutral-400 flex flex-col sm:flex-row justify-between gap-4">
                    <div>
                      <p className="font-bold text-white uppercase">{telemetryData.driver_a_meta.name} Laptime:</p>
                      <p className="mt-1 text-red-500 font-extrabold text-sm">{telemetryData.telemetry.driver_a.lap_time.toFixed(3)}s</p>
                    </div>
                    <div>
                      <p className="font-bold text-white uppercase">{telemetryData.driver_b_meta.name} Laptime:</p>
                      <p className="mt-1 text-blue-500 font-extrabold text-sm">{telemetryData.telemetry.driver_b.lap_time.toFixed(3)}s</p>
                    </div>
                    <div>
                      <p className="font-bold text-white uppercase">Delta Gap:</p>
                      <p className="mt-1 text-neutral-200 font-extrabold text-sm">
                        {Math.abs(telemetryData.telemetry.driver_a.lap_time - telemetryData.telemetry.driver_b.lap_time).toFixed(3)}s
                      </p>
                    </div>
                  </div>
                </div>
              ) : (
                <div className="flex h-64 items-center justify-center text-center text-xs text-neutral-500">
                  Telemetry channel overlaps not loaded for this race weekend. Check session loader pipelines.
                </div>
              )}
            </div>
          )}

        </div>
      )}

    </div>
  );
}
