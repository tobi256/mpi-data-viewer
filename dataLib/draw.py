from dataLib import Chunk
from typing import List
import plotly.graph_objects as go


def gen_fig_scatter(data: List[Chunk], show_start: bool = True, show_end: bool = True):
    fig = go.Figure(layout=dict(height=800))

    for frame in data:
        fd = frame.get_data()
        if show_start:
            fig.add_scatter(x=fd['start'], y=fd['p'], name=f"{frame.td.name}: start", mode='markers')
        if show_end:
            fig.add_scatter(x=fd['end'], y=fd['p'], name=f"{frame.td.name}: end", mode='markers')

    return fig
