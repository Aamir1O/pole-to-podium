import html as html_lib


def esc(text):
    return html_lib.escape(str(text))


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