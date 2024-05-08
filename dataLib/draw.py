from dataLib.Chunk import Chunk
from dataLib.Chunk import ChunkList
import plotly.graph_objects as go
import plotly.express as px
from enum import Enum
import pandas as pd


_colors = px.colors.qualitative.G10  # todo add bigger color pallet
_colors.extend(px.colors.qualitative.G10)
_colors.extend(px.colors.qualitative.G10)

# todo refactor everything to use new get_data
# todo add js switch to disable mean visible
# todo add scatter "run view" or create new scatter plot for this
# todo add background boxes for

def _gen_full_hover_text(row):
    return f"p: {row['p']}\ni: {row['idx']}\nstart: {row['start']}\nend: {row['end']}"


def test_gen_fig_scatter(
        data: ChunkList | Chunk,  # data to plot
        show_start: bool = True,  # shows start timestamps if true
        show_end: bool = True,  # shows end timestamps if true
        show_mean: bool = False  # vertical lines for mean of each idx of each chunk
):
    if type(data) is not ChunkList:
        data = ChunkList([data])

    fig = go.Figure()

    index = 0
    for frame in data:
        fd = frame.get_data()
        desc = fd.apply(_gen_full_hover_text, axis=1)
        if show_start:
            fig.add_scattergl(x=fd[fd['is_start']]['start'], y=fd[fd['is_start']]['p'], name=f"{frame.td.name}: start", mode='markers',
                            marker=dict(color=_colors[index]), hovertext=desc)
            if show_mean:
                for i, x in frame.get_mean_times_by_idx().iterrows():
                    fig.add_vline(x['m_start'], line_color=_colors[index])
            index += 1
        if show_end:
            fig.add_scattergl(x=fd[fd['is_start'] == False]['end'], y=fd[fd['is_start'] == False]['p'], name=f"{frame.td.name}: end", mode='markers',
                            marker=dict(color=_colors[index]), hovertext=desc)
            if show_mean:
                for i, x in frame.get_mean_times_by_idx().iterrows():
                    fig.add_vline(x['m_end'], line_color=_colors[index])
            index += 1
    fig.update_xaxes(title="time")
    fig.update_yaxes(title="Entity ID")
    return fig

def gen_fig_scatter(
        data: ChunkList | Chunk,  # data to plot
        show_start: bool = True,  # shows start timestamps if true
        show_end: bool = True,  # shows end timestamps if true
        show_mean: bool = False  # vertical lines for mean of each idx of each chunk
):
    if type(data) is not ChunkList:
        data = ChunkList([data])

    fig = go.Figure()

    index = 0
    for frame in data:
        fd = frame.get_raw_data()
        desc = fd.apply(_gen_full_hover_text, axis=1)
        if show_start:
            fig.add_scattergl(x=fd['start'], y=fd['p'], name=f"{frame.td.name}: start", mode='markers',
                            marker=dict(color=_colors[index]), hovertext=desc)
            if show_mean:
                for i, x in frame.get_mean_times_by_idx().iterrows():
                    fig.add_vline(x['m_start'], line_color=_colors[index])
            index += 1
        if show_end:
            fig.add_scattergl(x=fd['end'], y=fd['p'], name=f"{frame.td.name}: end", mode='markers',
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
    fig.add_bar
    return fig


def gen_fig_diff_timing(
        base_data: Chunk,  # the data from which the diff will be calculated
        comp_data: Chunk,  # the data to which the diff will be calculated
        show_start_not_end: bool = True,  # defines if start of end values will be used
        show_points: bool = True,
        show_mean: bool = False
):
    fig = gen_fig_scatter(
        ChunkList([base_data, comp_data]),
        show_start=(show_start_not_end and show_points),
        show_end=(not show_start_not_end and show_points),
        show_mean=show_mean)
    col_name = 'start' if show_start_not_end else 'end'
    bfd = base_data.get_data()
    cfd = comp_data.get_data()
    # todo think about what happens if data does not match
    empty_lines = None
    empty_lines_backup = None
    y_line = None
    idxs = bfd['idx'].unique()
    for index in idxs:
        b_block = bfd[bfd['idx'] == index][['p', col_name]].reset_index()
        c_block = cfd[bfd['idx'] == index][['p', col_name]].reset_index()
        if empty_lines is None:
            empty_lines = [0]*len(b_block)
            empty_lines_backup = [0] * len(b_block)
            y_line = [x for x in range(0, len(b_block))]
        line_g = []
        line_r = []
        y_g = []
        y_r = []
        for i, x in b_block.iterrows():
            cur_b = x[col_name]
            cur_c = c_block.loc[c_block['p'] == x['p'], col_name].values[0]
            empty_lines[i] = (min(cur_b, cur_c)) - empty_lines_backup[i]
            #y_line.append(x['p'])
            if cur_b < cur_c:
                line_g.append(cur_c - cur_b)
                y_g.append(x['p'])
            else:
                line_r.append(cur_b - cur_c)
                y_r.append(x['p'])
            empty_lines_backup[i] = max(cur_b, cur_c)

        fig.add_bar(x=empty_lines, y=y_line, name="first", orientation="h", opacity=0)
        fig.add_bar(x=line_g, y=y_g, name="pos delta", orientation="h", marker=dict(color='green'))
        fig.add_bar(x=line_r, y=y_r, name="neg delta", orientation="h", marker=dict(color='red'))

    fig.update_layout(barmode='stack', bargap=0, bargroupgap=0)
    return fig
