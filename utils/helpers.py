import html as html_lib
import streamlit as st


def esc(text):
    return html_lib.escape(str(text))


def render_html_block(html_content):
    st.markdown(html_content, unsafe_allow_html=True)


def page_head(title, subtitle=""):
    sub = f'<div class="p2p-page-sub">{esc(subtitle)}</div>' if subtitle else ""
    render_html_block(
        f'<div class="p2p-page-head fade-up">'
        f'<div class="p2p-page-title">{esc(title)}</div>{sub}</div>'
    )


def section(title, accent=""):
    t = f'{esc(title)} <span>{esc(accent)}</span>' if accent else esc(title)
    render_html_block(f'<div class="p2p-section-title fade-up">{t}</div>')


def show_chart(fig, **kwargs):
    kwargs.setdefault("use_container_width", True)
    st.plotly_chart(fig, config={"displayModeBar": False}, **kwargs)


def expandable_section(title, accent, key, preview=4, expand_label="See full standings →"):
    if key not in st.session_state:
        st.session_state[key] = False
    col_t, col_b = st.columns([5, 1])
    with col_t:
        render_html_block(
            f'<div class="p2p-section-title" style="margin-bottom:0">'
            f'{esc(title)} <span>{esc(accent)}</span></div>'
        )
    with col_b:
        label = "Show less ↑" if st.session_state[key] else expand_label
        if st.button(label, key=f"btn_{key}", type="tertiary"):
            st.session_state[key] = not st.session_state[key]
            st.rerun()
    return None if st.session_state[key] else preview


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