"""
Karoo v2.0 — Visualisation Components
Radar chart, score bars, timeline, agent grid.
"""
from typing import Dict, Optional

def radar_chart(agent_scores: Dict[str, int]):
    """Radar chart of all agent scores."""
    try:
        import plotly.graph_objects as go
        import plotly.express as px

        labels = [k.replace('_', ' ').title() for k in agent_scores.keys()]
        values = list(agent_scores.values())
        values_closed = values + [values[0]]
        labels_closed = labels + [labels[0]]

        fig = go.Figure()
        fig.add_trace(go.Scatterpolar(
            r=values_closed, theta=labels_closed,
            fill='toself',
            fillcolor='rgba(21, 101, 192, 0.2)',
            line=dict(color='#1565C0', width=2),
            marker=dict(size=6, color='#1565C0'),
            name='Your CV Score',
        ))
        fig.add_trace(go.Scatterpolar(
            r=[80]*len(labels_closed), theta=labels_closed,
            mode='lines',
            line=dict(color='#E65C00', width=1, dash='dot'),
            name='Target (80)',
        ))
        fig.update_layout(
            polar=dict(
                radialaxis=dict(visible=True, range=[0, 100], tickfont_size=9),
                angularaxis=dict(tickfont_size=10),
            ),
            showlegend=True,
            title=dict(text="CV Performance Radar", font=dict(size=14, color='#1565C0')),
            margin=dict(l=60, r=60, t=60, b=40),
            height=400,
            paper_bgcolor='white',
            plot_bgcolor='white',
        )
        return fig
    except ImportError:
        return None


def score_gauge(score: int):
    """Gauge chart for overall score."""
    try:
        import plotly.graph_objects as go
        color = '#2E7D32' if score >= 80 else '#E65C00' if score >= 60 else '#C62828'
        fig = go.Figure(go.Indicator(
            mode="gauge+number+delta",
            value=score,
            domain={'x': [0, 1], 'y': [0, 1]},
            title={'text': "Overall ATS Score", 'font': {'size': 16, 'color': '#1565C0'}},
            delta={'reference': 75, 'increasing': {'color': '#2E7D32'}, 'decreasing': {'color': '#C62828'}},
            gauge={
                'axis': {'range': [0, 100], 'tickwidth': 1},
                'bar': {'color': color, 'thickness': 0.3},
                'bgcolor': "white",
                'borderwidth': 2,
                'bordercolor': "gray",
                'steps': [
                    {'range': [0, 50], 'color': '#ffebee'},
                    {'range': [50, 70], 'color': '#fff3e0'},
                    {'range': [70, 85], 'color': '#e8f5e9'},
                    {'range': [85, 100], 'color': '#c8e6c9'},
                ],
                'threshold': {
                    'line': {'color': "#1565C0", 'width': 4},
                    'thickness': 0.75,
                    'value': 80,
                }
            }
        ))
        fig.update_layout(height=280, margin=dict(l=20, r=20, t=40, b=10))
        return fig
    except ImportError:
        return None


def agent_bar_chart(agent_scores: Dict[str, int]):
    """Horizontal bar chart for agent scores."""
    try:
        import plotly.graph_objects as go

        names = [k.replace('_', ' ').title() for k in agent_scores.keys()]
        values = list(agent_scores.values())
        colors = ['#2E7D32' if v>=80 else '#E65C00' if v>=60 else '#C62828' for v in values]

        fig = go.Figure(go.Bar(
            x=values, y=names, orientation='h',
            marker_color=colors,
            text=[f"{v}/100" for v in values],
            textposition='outside',
        ))
        fig.add_vline(x=75, line_dash="dot", line_color="#1565C0", annotation_text="Target 75+")
        fig.update_layout(
            title="Agent Score Breakdown",
            xaxis=dict(range=[0, 110], title="Score"),
            yaxis=dict(autorange="reversed"),
            height=380,
            margin=dict(l=160, r=80, t=50, b=30),
        )
        return fig
    except ImportError:
        return None


def improvement_chart(before_score: int, after_scores: Dict[str, int]):
    """Before/after improvement chart."""
    try:
        import plotly.graph_objects as go
        fig = go.Figure()
        labels = ['Before'] + [k.replace('_', ' ').title() for k in after_scores.keys()]
        values = [before_score] + list(after_scores.values())
        fig.add_trace(go.Scatter(
            x=labels, y=values, mode='lines+markers',
            marker=dict(size=10, color='#1565C0'),
            line=dict(color='#1565C0', width=2),
        ))
        fig.update_layout(title="Score Trajectory", yaxis=dict(range=[0,100]), height=250)
        return fig
    except ImportError:
        return None
