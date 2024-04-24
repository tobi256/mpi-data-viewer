from dataLib.Chunk import Chunk
from dataLib.Chunk import ChunkList
import plotly.graph_objects as go
import plotly.express as px
from enum import Enum
import pandas as pd


_colors = px.colors.qualitative.G10


class RunOrOperation(Enum):
    run = 1
    operation = 2

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
                    fig.add_vline(x['m_start'], line_color=_colors[index])
            index += 1
        if show_end:
            fig.add_scatter(x=fd['end'], y=fd['p'], name=f"{frame.td.name}: end", mode='markers',
                            marker=dict(color=_colors[index]), hovertext=desc)
            if show_mean:
                for i, x in frame.get_mean_times_by_idx().iterrows():
                    fig.add_vline(x['m_end'], line_color=_colors[index])
            index += 1
    fig.update_xaxes(title="time")
    fig.update_yaxes(title="Entity ID")
    return fig

# generates a figure, which displays the time data relative to the indexes mean
def gen_fig_histo_rel_to_mean(
        data: ChunkList | Chunk,
        show_run_not_operation: bool = True,  # shows the colors of the different runs, else operations are colord
        show_start_not_end: bool = True  # shows start values, else end values
):
    if type(data) is not ChunkList:
        data = ChunkList([data])
    storen = 'start' if show_start_not_end else 'end'
    index = 0
    collected = []
    for frame in data:
        fd = frame.get_data()
        me = frame.get_mean_times_by_idx()

        temp = pd.merge(fd, me, on='idx')
        temp['runidx'] = index
        temp[f"norm_{storen}"] = temp.apply(lambda row: row[f"{storen}"] - row[f"m_{storen}"], axis=1)
        collected.append(temp)
        index += 1
    concat = pd.concat(collected)
    fig = px.histogram(concat, x=f"norm_{storen}", color=('runidx' if show_run_not_operation else 'idx'),
                       color_discrete_sequence=_colors, labels={})
    fig.for_each_trace(lambda t: t.update(name = f"run {t.name}: {data[int(t.name)].td.name}" if show_run_not_operation
                       else f"oper. idx: {t.name}"))
    fig.update_xaxes(title="time relative to mean per idx and run")
    return fig