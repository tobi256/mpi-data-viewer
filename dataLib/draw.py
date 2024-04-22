from dataLib import Chunk
from typing import List
import plotly.graph_objects as go


def _gen_full_hover_text(row):
    return f"p: {row['p']}\ni: {row['idx']}\nstart: {row['start']}\nend: {row['end']}"


def gen_fig_scatter(data: List[Chunk], show_start: bool = True, show_end: bool = True):
    fig = go.Figure(layout=dict(height=800))

    for frame in data:
        fd = frame.get_data()
        desc = fd.apply(_gen_full_hover_text, axis=1)
        if show_start:
            fig.add_scatter(x=fd['start'], y=fd['p'], name=f"{frame.td.name}: start", mode='markers', hovertext=desc)
        if show_end:
            fig.add_scatter(x=fd['end'], y=fd['p'], name=f"{frame.td.name}: end", mode='markers', hovertext=desc)

    return fig
