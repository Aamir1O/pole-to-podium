import os
import fastf1

os.makedirs("data/cache", exist_ok=True)
fastf1.Cache.enable_cache("data/cache")

for rnd in range(1, 7):
    try:
        race = fastf1.get_session(2026, rnd, "R")
        race.load()

        print(f"\n===== ROUND {rnd} =====")

        print(
            race.results[
                ["Abbreviation", "Position", "Points"]
            ]
            .sort_values("Position")
            .head(10)
            .to_string(index=False)
        )

    except Exception as e:
        print(f"Round {rnd} failed: {e}")