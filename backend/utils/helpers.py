import json
import plotly.utils
from datetime import datetime, timezone
import pytz
from backend.utils.metadata import UPCOMING_RACES, DRIVER_NAMES

def get_next_race():
    """Locates the next race relative to current time."""
    now = datetime.now(timezone.utc)
    for r in UPCOMING_RACES:
        tz = pytz.timezone(r["tz"])
        race_dt = tz.localize(
            datetime.strptime(r["dt"], "%Y-%m-%d %H:%M")
        ).astimezone(timezone.utc)
        if race_dt > now:
            return r
    return {"name": "Season Complete", "circuit": "", "dt": "", "tz": ""}

def get_driver_display(code: str) -> dict:
    """Returns details for a driver code."""
    info = DRIVER_NAMES.get(code, (code, "INT", "#ffffff"))
    return {
        "name": info[0],
        "country": info[1],
        "color": info[2],
        "code": code
    }

def fig_to_json(fig):
    """Converts a Plotly figure to a JSON-serializable dictionary."""
    if fig is None:
        return None
    # Safe serialization of numpy/pandas fields inside Plotly structure
    json_str = json.dumps(fig, cls=plotly.utils.PlotlyJSONEncoder)
    return json.loads(json_str)


def themed(fig, title=""):
    fig.update_layout(
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(family="Outfit, sans-serif", color="#777", size=11),
        margin=dict(l=8, r=8, t=44, b=8),
        title=dict(text=title, font=dict(size=13, color="#999", family="Outfit")) if title else {},
        legend=dict(bgcolor="rgba(0,0,0,0)", font=dict(size=10, color="#777")),
        hoverlabel=dict(
            bgcolor="#111", bordercolor="#e10600",
            font=dict(family="Outfit", color="#fff")
        ),
    )
    fig.update_xaxes(
        gridcolor="rgba(255,255,255,0.04)",
        linecolor="rgba(255,255,255,0.06)",
        zeroline=False,
        tickcolor="rgba(255,255,255,0.1)",
        tickfont=dict(color="#666"),
    )
    fig.update_yaxes(
        gridcolor="rgba(255,255,255,0.04)",
        linecolor="rgba(255,255,255,0.06)",
        zeroline=False,
        tickcolor="rgba(255,255,255,0.1)",
        tickfont=dict(color="#666"),
    )
    return fig
