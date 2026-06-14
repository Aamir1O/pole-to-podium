import numpy as np
from fastapi import APIRouter, HTTPException, Query
from backend.services.db_service import (
    get_session_info,
    get_driver_telemetry,
    get_delta_trace,
    get_corners_by_circuit,
    get_corner_metrics
)
from pipeline.delta_calculator import attribute_delta_to_corners
from backend.utils.helpers import get_driver_display

router = APIRouter(tags=["telemetry"])

@router.get("/telemetry")
def get_session_telemetry(
    season: int = Query(2026, description="Season year (e.g. 2026)"),
    round_num: int = Query(1, alias="round", description="Round number index (1-24)"),
    session_type: str = Query("Q", alias="session", description="Session type: FP1, FP2, FP3, Q, R"),
    driver_a: str = Query("VER", description="Driver code A"),
    driver_b: str = Query("NOR", description="Driver code B")
):
    try:
        driver_a = driver_a.upper()
        driver_b = driver_b.upper()
        
        # 1. Fetch telemetry session ID and circuit name from sessions_f1
        session = get_session_info(season, round_num, session_type)
        if not session:
            raise HTTPException(
                status_code=404, 
                detail=f"Telemetry session not found for {season} R{round_num} {session_type}."
            )
            
        session_id = session["id"]
        circuit_key = session["circuit_key"]
        
        # 2. Fetch telemetry channel traces for both drivers
        tel_a = get_driver_telemetry(session_id, driver_a)
        tel_b = get_driver_telemetry(session_id, driver_b)
        
        if not tel_a or not tel_b:
            raise HTTPException(
                status_code=404,
                detail=f"Telemetry traces not found for one or both drivers ({driver_a} vs {driver_b}) in this session."
            )
            
        # 3. Fetch pre-computed delta trace
        delta_trace = get_delta_trace(session_id, driver_a, driver_b)
        
        # 4. Fetch corner boundaries
        corners = get_corners_by_circuit(circuit_key)
        
        # 5. Fetch corner metrics (CPI breakdown)
        metrics_df = get_corner_metrics(session_id, driver_a, driver_b)
        
        # 6. Calculate corner-by-corner delta attributions and generate insights
        insights = []
        cpi_breakdown = []
        
        # Format Pydantic/JSON safe corner metrics
        if not metrics_df.empty:
            for _, row in metrics_df.iterrows():
                cpi_breakdown.append({
                    "driver_code": row["driver_code"],
                    "corner_number": int(row["corner_number"]),
                    "corner_name": row["corner_name"] if row["corner_name"] else f"Turn {row['corner_number']}",
                    "entry_score": float(row["entry_score"]),
                    "apex_score": float(row["apex_score"]),
                    "exit_score": float(row["exit_score"]),
                    "cpi": float(row["cpi"]),
                    "corner_time_s": float(row["corner_time_s"]) if row["corner_time_s"] else 0.0,
                    "entry_speed_kph": float(row["entry_speed_kph"]) if row["entry_speed_kph"] else 0.0,
                    "apex_speed_kph": float(row["apex_speed_kph"]) if row["apex_speed_kph"] else 0.0,
                    "exit_speed_kph": float(row["exit_speed_kph"]) if row["exit_speed_kph"] else 0.0,
                    "brake_point_m": float(row["brake_point_m"]) if row["brake_point_m"] else 0.0,
                    "throttle_point_m": float(row["throttle_point_m"]) if row["throttle_point_m"] else 0.0,
                    "time_to_full_throttle_s": float(row["time_to_full_throttle_s"]) if row["time_to_full_throttle_s"] else 0.0,
                })
                
        # Generate engineering text insights
        if delta_trace and corners:
            distance_arr = np.array(delta_trace["distance_m"])
            delta_arr = np.array(delta_trace["delta_s"])
            
            # Map standard structure required by delta calculator
            corners_input = [
                {
                    "corner_number": c["corner_number"],
                    "dist_start_m": c["dist_start_m"],
                    "dist_end_m": c["dist_end_m"]
                }
                for c in corners
            ]
            
            corner_deltas = attribute_delta_to_corners(distance_arr, delta_arr, corners_input)
            
            for c_delta in corner_deltas:
                c_num = c_delta["corner_number"]
                net_delta = c_delta["delta_s"]
                
                gainer = driver_a if net_delta > 0 else driver_b
                loser = driver_b if net_delta > 0 else driver_a
                
                # Extract reasons from CPI metric delta
                reason = "combination of entry and exit technique"
                m_a = metrics_df[(metrics_df.driver_code == driver_a) & (metrics_df.corner_number == c_num)]
                m_b = metrics_df[(metrics_df.driver_code == driver_b) & (metrics_df.corner_number == c_num)]
                
                if not m_a.empty and not m_b.empty:
                    apex_diff = float(m_a["apex_speed_kph"].values[0]) - float(m_b["apex_speed_kph"].values[0])
                    if abs(apex_diff) > 3:
                        diff = abs(apex_diff)
                        reason = f"due to {diff:.1f} km/h higher minimum speed at apex"
                    else:
                        exit_diff = float(m_a["exit_speed_kph"].values[0]) - float(m_b["exit_speed_kph"].values[0])
                        if abs(exit_diff) > 5:
                            diff = abs(exit_diff)
                            reason = f"due to earlier throttle application (+{diff:.1f} km/h on exit)"
                        else:
                            brake_diff = (float(m_b["brake_point_m"].values[0]) - float(m_a["brake_point_m"].values[0])
                                          if net_delta > 0 else
                                          float(m_a["brake_point_m"].values[0]) - float(m_b["brake_point_m"].values[0]))
                            if brake_diff > 5:
                                reason = f"due to a {abs(brake_diff):.0f}m later brake point"
                                
                insights.append({
                    "corner_number": c_num,
                    "delta_s": net_delta,
                    "driver_gaining": gainer,
                    "driver_losing": loser,
                    "reason": reason
                })
                
        return {
            "session_id": session_id,
            "circuit_key": circuit_key,
            "driver_a_meta": get_driver_display(driver_a),
            "driver_b_meta": get_driver_display(driver_b),
            "telemetry": {
                "grid": tel_a["distance_m"],  # Shared distance grid
                "driver_a": {
                    "speed": tel_a["speed_kph"],
                    "throttle": tel_a["throttle_pct"],
                    "brake": tel_a["brake"],
                    "gear": tel_a["gear"],
                    "rpm": tel_a["rpm"],
                    "lap_time": tel_a["lap_time_s"]
                },
                "driver_b": {
                    "speed": tel_b["speed_kph"],
                    "throttle": tel_b["throttle_pct"],
                    "brake": tel_b["brake"],
                    "gear": tel_b["gear"],
                    "rpm": tel_b["rpm"],
                    "lap_time": tel_b["lap_time_s"]
                },
                "delta": delta_trace["delta_s"] if delta_trace else []
            },
            "corners": corners,
            "cpi_breakdown": cpi_breakdown,
            "engineering_insights": insights
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to load aligned telemetry: {str(e)}")
