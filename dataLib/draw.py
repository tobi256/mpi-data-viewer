from dataLib.Chunk import Chunk
from dataLib.Chunk import ChunkList
import plotly.graph_objects as go
import plotly.express as px


_colors = px.colors.qualitative.G10


def _gen_full_hover_text(row):
    return f"p: {row['p']}\ni: {row['idx']}\nstart: {row['start']}\nend: {row['end']}"


def gen_fig_scatter(
        data: ChunkList | Chunk,  # data to plot
        show_start: bool = True,  # shows start timestamps if true
        show_end: bool = True,  # shows end timestamps if true
        show_mean: bool = False  # vertical lines for mean of each idx of each chunk
):
    if type(data) is not ChunkList:
        data = ChunkList([data])

    fig = go.Figure(layout=dict(height=800))

    index = 0
    for frame in data:
        fd = frame.get_data()
        desc = fd.apply(_gen_full_hover_text, axis=1)
        if show_start:
            fig.add_scatter(x=fd['start'], y=fd['p'], name=f"{frame.td.name}: start", mode='markers',
                            marker=dict(color=_colors[index]), hovertext=desc)
            if show_mean:
                for i, x in frame.get_mean_times_by_idx().iterrows():
                    fig.add_vline(x['start'], line_color=_colors[index])
            index += 1
        if show_end:
            fig.add_scatter(x=fd['end'], y=fd['p'], name=f"{frame.td.name}: end", mode='markers',
                            marker=dict(color=_colors[index]), hovertext=desc)
            if show_mean:
                for i, x in frame.get_mean_times_by_idx().iterrows():
                    fig.add_vline(x['end'], line_color=_colors[index])
            index += 1

    return fig
