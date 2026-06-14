'use client';

import React, { useEffect, useState } from 'react';
import Link from 'next/link';
import { 
  Trophy, 
  Activity, 
  Flag, 
  ChevronRight, 
  AlertTriangle 
} from 'lucide-react';
import PlotlyChart from '@/components/PlotlyChart';

interface HeroStats {
  races_complete: number;
  championship_leader: string;
  leader_points: number;
  leader_team: string;
  wins_count: number;
}

interface NextRace {
  name: string;
  circuit: string;
  dt: string;
  tz: string;
}

interface DriverStanding {
  position: number;
  driver_code: string;
  driver_name: string;
  team: string;
  points: number;
  wins: number;
  podiums: number;
  delta: number;
  color: string;
}

interface TeamStanding {
  position: number;
  team: string;
  team_abbr: string;
  points: number;
  delta: number;
}

interface RaceScheduleItem {
  race_id: string;
  race_name: string;
  circuit: string;
  date: string;
  status: string;
  winner_code: string | null;
}

interface WinProbPreview {
  driver_code: string;
  driver_name: string;
  team: string;
  win_probability: number;
  grid_pos: number;
}

interface DashboardData {
  hero_stats: HeroStats;
  next_race: NextRace;
  driver_standings: DriverStanding[];
  team_standings: TeamStanding[];
  race_schedule: RaceScheduleItem[];
  championship_battle_chart: any;
  win_probability_preview: WinProbPreview[];
}

export default function DashboardPage() {
  const [data, setData] = useState<DashboardData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    fetch('http://127.0.0.1:8000/api/v1/dashboard')
      .then((res) => {
        if (!res.ok) throw new Error('Failed to load dashboard data');
        return res.json();
      })
      .then((resData: DashboardData) => {
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
      <div className="space-y-6">
        {/* Skeletons for KPIs */}
        <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
          {[1, 2, 3, 4].map((i) => (
            <div key={i} className="h-24 animate-pulse rounded-xl border border-neutral-900 bg-neutral-950/40" />
          ))}
        </div>
        {/* Skeleton for Hero Chart */}
        <div className="h-96 animate-pulse rounded-xl border border-neutral-900 bg-neutral-950/40" />
        {/* Two column layout skeletons */}
        <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
          <div className="h-80 animate-pulse rounded-xl border border-neutral-900 bg-neutral-950/40" />
          <div className="h-80 animate-pulse rounded-xl border border-neutral-900 bg-neutral-950/40" />
        </div>
      </div>
    );
  }

  if (error || !data) {
    return (
      <div className="flex min-h-[400px] flex-col items-center justify-center rounded-xl border border-red-950/50 bg-red-950/10 p-6 text-center">
        <AlertTriangle className="mb-4 h-12 w-12 text-red-500" />
        <h3 className="text-lg font-bold text-white">Data Fetch Error</h3>
        <p className="mt-2 text-sm text-neutral-400 max-w-md">
          {error || 'Unable to communicate with the FastAPI backend server. Ensure uvicorn is running on port 8000.'}
        </p>
      </div>
    );
  }

  const { hero_stats, next_race, driver_standings, team_standings, race_schedule, championship_battle_chart, win_probability_preview } = data;

  return (
    <div className="space-y-8">
      {/* Hero Header KPIs */}
      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
        
        <div className="relative overflow-hidden rounded-xl border border-neutral-900 bg-neutral-950/40 p-5">
          <div className="absolute top-0 left-0 h-[2px] w-full bg-neutral-800"></div>
          <p className="font-mono text-xs font-semibold tracking-wider text-neutral-500 uppercase">Races Complete</p>
          <p className="mt-2 text-3xl font-black text-white">{hero_stats.races_complete}</p>
        </div>

        <div className="relative overflow-hidden rounded-xl border border-neutral-900 bg-neutral-950/40 p-5">
          <div className="absolute top-0 left-0 h-[2px] w-full bg-red-600"></div>
          <p className="font-mono text-xs font-semibold tracking-wider text-neutral-500 uppercase">Championship Leader</p>
          <p className="mt-2 text-2xl font-black text-white truncate">{hero_stats.championship_leader}</p>
        </div>

        <div className="relative overflow-hidden rounded-xl border border-neutral-900 bg-neutral-950/40 p-5">
          <div className="absolute top-0 left-0 h-[2px] w-full bg-neutral-800"></div>
          <p className="font-mono text-xs font-semibold tracking-wider text-neutral-500 uppercase">Leader Points</p>
          <div className="mt-2 flex items-baseline gap-1">
            <span className="text-3xl font-black text-white">{hero_stats.leader_points}</span>
            <span className="text-xs font-bold text-red-500 uppercase tracking-widest">pts</span>
            <span className="ml-2 text-xs text-neutral-500 truncate">({hero_stats.leader_team})</span>
          </div>
        </div>

        <div className="relative overflow-hidden rounded-xl border border-neutral-900 bg-neutral-950/40 p-5">
          <div className="absolute top-0 left-0 h-[2px] w-full bg-neutral-800"></div>
          <p className="font-mono text-xs font-semibold tracking-wider text-neutral-500 uppercase">Total Race Wins</p>
          <p className="mt-2 text-3xl font-black text-white">{hero_stats.wins_count}</p>
        </div>

      </div>

      {/* Flagship Championship Battle Plot */}
      {championship_battle_chart && (
        <div className="rounded-xl border border-neutral-900 bg-neutral-950/20 p-5">
          <h2 className="flex items-center gap-2 font-sans text-xs font-bold tracking-widest text-neutral-400 uppercase">
            <span className="inline-block h-3.5 w-1 rounded bg-red-600"></span>
            Championship Battle <span className="text-neutral-600">|</span> <span className="text-neutral-500">Top 5 Drivers</span>
          </h2>
          <div className="mt-4">
            <PlotlyChart data={championship_battle_chart.data} layout={championship_battle_chart.layout} height={380} />
          </div>
        </div>
      )}

      {/* Main Standings & Previews Block */}
      <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
        
        {/* Left: Driver Standings Preview */}
        <div className="rounded-xl border border-neutral-900 bg-neutral-950/20 p-5 flex flex-col">
          <div className="flex items-center justify-between">
            <h2 className="flex items-center gap-2 font-sans text-xs font-bold tracking-widest text-neutral-400 uppercase">
              <span className="inline-block h-3.5 w-1 rounded bg-red-600"></span>
              Drivers Standing
            </h2>
            <Link href="/drivers" className="flex items-center gap-0.5 text-xs font-bold text-red-500 hover:text-red-400 transition-colors uppercase tracking-wider">
              <span>Full Standings</span>
              <ChevronRight className="h-3 w-3" />
            </Link>
          </div>
          
          <div className="mt-4 flex-1 overflow-x-auto">
            <table className="w-full text-left border-collapse">
              <thead>
                <tr className="border-b border-neutral-900 font-mono text-[10px] text-neutral-500 uppercase tracking-wider">
                  <th className="py-2 pl-2">Pos</th>
                  <th className="py-2">Driver</th>
                  <th className="py-2">Team</th>
                  <th className="py-2 text-center">Wins</th>
                  <th className="py-2 text-right">Points</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-neutral-900 text-sm">
                {driver_standings.map((d) => (
                  <tr key={d.driver_code} className="hover:bg-neutral-950/60 transition-colors">
                    <td className="py-3 pl-2 font-mono font-bold text-neutral-400">P{d.position}</td>
                    <td className="py-3 font-semibold text-white">
                      <div className="flex items-center gap-2">
                        <span className="w-1 h-3 rounded-[1px]" style={{ backgroundColor: d.color }}></span>
                        <span>{d.driver_name}</span>
                        <span className="rounded bg-neutral-900 px-1 py-0.5 text-[9px] font-mono text-neutral-500">{d.driver_code}</span>
                      </div>
                    </td>
                    <td className="py-3 text-neutral-400 font-medium">{d.team}</td>
                    <td className="py-3 text-center text-neutral-300 font-semibold">{d.wins}</td>
                    <td className="py-3 text-right font-black text-white">
                      {d.points}
                      {d.delta > 0 && <span className="text-[10px] text-green-500 ml-1">+{d.delta}</span>}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>

        {/* Right: Race Schedule Preview */}
        <div className="rounded-xl border border-neutral-900 bg-neutral-950/20 p-5 flex flex-col">
          <div className="flex items-center justify-between">
            <h2 className="flex items-center gap-2 font-sans text-xs font-bold tracking-widest text-neutral-400 uppercase">
              <span className="inline-block h-3.5 w-1 rounded bg-red-600"></span>
              Race Schedule
            </h2>
            <Link href="/race-center" className="flex items-center gap-0.5 text-xs font-bold text-red-500 hover:text-red-400 transition-colors uppercase tracking-wider">
              <span>Full Schedule</span>
              <ChevronRight className="h-3 w-3" />
            </Link>
          </div>
          
          <div className="mt-4 flex-1 space-y-3">
            {race_schedule.map((race) => (
              <div key={race.race_id} className="flex items-center justify-between rounded-lg border border-neutral-900 bg-neutral-950/40 p-3 hover:border-neutral-800 transition-all duration-150">
                <div>
                  <p className="text-sm font-bold text-white">{race.race_name}</p>
                  <p className="text-xs font-medium text-neutral-500 mt-0.5">{race.date} · {race.circuit}</p>
                </div>
                <div className="text-right">
                  {race.status === 'Finished' ? (
                    <span className="inline-block rounded-full border border-neutral-800 px-2 py-0.5 font-mono text-[9px] font-bold text-neutral-500 uppercase">
                      Winner: {race.winner_code}
                    </span>
                  ) : (
                    <span className="inline-block rounded-full border border-red-950/50 bg-red-950/25 px-2 py-0.5 font-mono text-[9px] font-bold text-red-500 uppercase">
                      Upcoming
                    </span>
                  )}
                </div>
              </div>
            ))}
          </div>
        </div>

      </div>

      {/* Constructor Standing + Win Probability Preview */}
      <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
        
        {/* Constructor Standings */}
        <div className="rounded-xl border border-neutral-900 bg-neutral-950/20 p-5">
          <div className="flex items-center justify-between">
            <h2 className="flex items-center gap-2 font-sans text-xs font-bold tracking-widest text-neutral-400 uppercase">
              <span className="inline-block h-3.5 w-1 rounded bg-red-600"></span>
              Constructor Standings
            </h2>
            <Link href="/teams" className="flex items-center gap-0.5 text-xs font-bold text-red-500 hover:text-red-400 transition-colors uppercase tracking-wider">
              <span>Constructor Details</span>
              <ChevronRight className="h-3 w-3" />
            </Link>
          </div>
          
          <div className="mt-4 overflow-x-auto">
            <table className="w-full text-left border-collapse">
              <thead>
                <tr className="border-b border-neutral-900 font-mono text-[10px] text-neutral-500 uppercase tracking-wider">
                  <th className="py-2 pl-2">Pos</th>
                  <th className="py-2">Constructor</th>
                  <th className="py-2 text-right">Points</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-neutral-900 text-sm">
                {team_standings.map((t) => (
                  <tr key={t.team} className="hover:bg-neutral-950/60 transition-colors">
                    <td className="py-3.5 pl-2 font-mono font-bold text-neutral-400">P{t.position}</td>
                    <td className="py-3.5 font-semibold text-white">
                      <div className="flex items-center gap-2">
                        <span className="rounded bg-neutral-900 border border-neutral-800 px-1.5 py-0.5 font-mono text-xs font-extrabold text-red-500">{t.team_abbr}</span>
                        <span>{t.team}</span>
                      </div>
                    </td>
                    <td className="py-3.5 text-right font-black text-white">
                      {t.points}
                      {t.delta > 0 && <span className="text-[10px] text-green-500 ml-1">+{t.delta}</span>}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>

        {/* Win Probability Preview for next round */}
        <div className="rounded-xl border border-neutral-900 bg-neutral-950/20 p-5 flex flex-col justify-between">
          <div>
            <div className="flex items-center justify-between">
              <h2 className="flex items-center gap-2 font-sans text-xs font-bold tracking-widest text-neutral-400 uppercase">
                <span className="inline-block h-3.5 w-1 rounded bg-red-600"></span>
                Next Race Win Probability
              </h2>
              <Link href="/predictions" className="flex items-center gap-0.5 text-xs font-bold text-red-500 hover:text-red-400 transition-colors uppercase tracking-wider">
                <span>Predictions center</span>
                <ChevronRight className="h-3 w-3" />
              </Link>
            </div>
            
            <div className="mt-5 space-y-3.5">
              {win_probability_preview.length > 0 ? (
                win_probability_preview.map((p) => (
                  <div key={p.driver_code} className="space-y-1.5">
                    <div className="flex justify-between text-xs">
                      <span className="font-semibold text-white">
                        {p.driver_name} <span className="text-neutral-500 font-mono text-[10px]">({p.driver_code}) · {p.team}</span>
                      </span>
                      <span className="font-mono font-bold text-red-500">{(p.win_probability * 100).toFixed(1)}%</span>
                    </div>
                    {/* Aligned Probability Bar */}
                    <div className="h-1.5 w-full rounded-full bg-neutral-900 overflow-hidden">
                      <div className="h-full bg-red-600 rounded-full" style={{ width: `${p.win_probability * 100}%` }}></div>
                    </div>
                  </div>
                ))
              ) : (
                <div className="flex h-36 items-center justify-center text-center text-xs text-neutral-500">
                  No practice or qualifying predictions loaded yet for the upcoming round.
                </div>
              )}
            </div>
          </div>
        </div>

      </div>

    </div>
  );
}
