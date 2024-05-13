from pandas.core.common import flatten
from dataLib.Chunk import Chunk
from dataLib.Chunk import ChunkList
import plotly.graph_objects as go
import plotly.express as px
from enum import Enum
import pandas as pd
from dataLib.Messenger import Messenger as m
from datetime import datetime, timedelta


_colors = px.colors.qualitative.G10  # todo add bigger color pallet
_colors.extend(px.colors.qualitative.G10)
_colors.extend(px.colors.qualitative.G10)

# todo refactor everything to use new get_data
# todo add js switch to disable mean visible

def _gen_full_hover_text(row):
    return (f"entity ID: <b>{row['p']}</b><br>"
            f"oper. ID: <b>{row['idx']}</b><br>"
            f"context: {row['context']}<br>"
            f"{"<b>" if row["is_start"] else ""}start: {row['start']}{"</b>" if row["is_start"] else ""}<br>"
            f"{"" if row["is_start"] else "<b>"}end: {row['end']}{"" if row["is_start"] else "</b>"}<br>"
            f"call ID: {row['callid']}<br>"
            f"buf_size: {row['buf_size']}<br>"
            f"comm size: {row['comm_size']}<br>"
            f"region: {row['region']}")

def _gen_full_hover_text_is_start(row):
    return (f"entity ID: <b>{row['p']}</b><br>"
            f"oper. ID: <b>{row['idx']}</b><br>"
            f"context: {row['context']}<br>"
            f"<b>start: {row['start']}</b><br>"
            f"end: {row['end']}<br>"
            f"call ID: {row['callid']}<br>"
            f"buf_size: {row['buf_size']}<br>"
            f"comm size: {row['comm_size']}<br>"
            f"region: {row['region']}")

def _gen_full_hover_text_is_end(row):
    return (f"entity ID: <b>{row['p']}</b><br>"
            f"oper. ID: <b>{row['idx']}</b><br>"
            f"context: {row['context']}<br>"
            f"start: {row['start']}<br>"
            f"<b>end: {row['end']}</b><br>"
            f"call ID: {row['callid']}<br>"
            f"buf_size: {row['buf_size']}<br>"
            f"comm size: {row['comm_size']}<br>"
            f"region: {row['region']}")


class DisplayStyle(Enum):
    # Displays all runs in the same area.
    # x = time
    # y = entities
    CLASSIC = 1

    # Displays every run on its own line. All entities of run 1 are y=1 ...
    # x = time
    # y = runs on integers
    RUN_LINE = 2

    # Displays every run below each other. Entities are scaled to be between two integer values
    # x = time
    # y = floating points - aa.bb - describe: aa = the runID, bb = the floating point representation of the entity id
    RUN_SCALED = 3


__RELATIVE_HEIGHT_OF_BOX = 0.3
__RELATIVE_HEIGHT_OF_LINE = 0.35
__SPACE_BETWEEN_RUNNS = 0.1  # above and below
__SPACE_BETWEEN_LINES = 0
__SPACE_BETWEEN_BOXES = 0.1

til = timedelta(0)
desc_time = timedelta(0)
scattering_time = timedelta(0)
rest_time = timedelta(0)

def __add_scatters_to_fig(fig, shapes, frame, display_style, index, color_id, first_occ, show_real_mean, show_real_duration, is_start):
    start = datetime.now()
    se_name = "start" if is_start else "end"
    fd = frame.get_data()
    p_disp_count = frame.p_end - frame.p_start
    fds = fd[(fd["is_start"] if is_start else ~fd["is_start"])].copy()
    if display_style == DisplayStyle.RUN_LINE:
        fds["xaxis"] = index
    elif display_style == DisplayStyle.RUN_SCALED:
        fds["xaxis"] = fds["p"].apply(
            lambda s: (s / p_disp_count) * (1 - 2 * __SPACE_BETWEEN_RUNNS) + __SPACE_BETWEEN_RUNNS + index)

    global til
    m1 = datetime.now()
    m.debug(f"til:{m1-start} [{til}]")
    til += m1-start

    desc = fds.apply((_gen_full_hover_text_is_start if is_start else _gen_full_hover_text_is_end), axis=1)  # todo improve performance

    global desc_time
    m2 = datetime.now()
    m.debug(f"desc:{m2-m1} [{desc_time}]")
    desc_time += m2-m1

    fig.add_scattergl(x=fds[se_name], y=(fds['p'] if display_style == DisplayStyle.CLASSIC else fds['xaxis']),
                      name=f"{frame.td.name}: {se_name}", mode='markers', marker=dict(color=_colors[color_id]),
                      hovertext=desc, hoverinfo="text")

    global scattering_time
    m3 = datetime.now()
    m.debug(f"scatter:{m3-m2} [{scattering_time}]")
    scattering_time += m3-m2

    if first_occ and show_real_mean:
        for i, x in frame.get_mean_times_by_idx().iterrows():
            if display_style == DisplayStyle.CLASSIC:
                fig.add_vline(x[f"m_{se_name}"], line_color=_colors[color_id])
            else:
                yy = (0, 0)
                if display_style == DisplayStyle.RUN_LINE:
                    yy = (index - __RELATIVE_HEIGHT_OF_LINE, index + __RELATIVE_HEIGHT_OF_LINE)
                elif display_style == DisplayStyle.RUN_SCALED:
                    yy = (index + __SPACE_BETWEEN_LINES, index + 1 - __SPACE_BETWEEN_LINES)
                shapes.append(dict(type="line", x0=x[f"m_{se_name}"], x1=x[f"m_{se_name}"], y0=yy[0], y1=yy[1],
                              line=dict(color=_colors[color_id])))
    if first_occ and show_real_duration:
        max_vals = frame.get_max_times_by_idx().reset_index()
        min_vals = frame.get_min_times_by_idx().reset_index()
        for i, min_row in min_vals.iterrows():
            max_point = max_vals.loc[max_vals["idx"] == min_row["idx"], f"m_{se_name}"].values[0]
            if display_style == DisplayStyle.CLASSIC:
                fig.add_vrect(x0=min_row[f"m_{se_name}"], x1=max_point, fillcolor=_colors[color_id], opacity=0.25,
                              layer="below", line_width=0)
            else:
                yy = (0, 0)
                if display_style == DisplayStyle.RUN_LINE:
                    yy = (index - __RELATIVE_HEIGHT_OF_BOX, index + __RELATIVE_HEIGHT_OF_BOX)
                elif display_style == DisplayStyle.RUN_SCALED:
                    yy = (index + __SPACE_BETWEEN_BOXES, index + 1 - __SPACE_BETWEEN_BOXES)
                shapes.append(dict(type="rect", y0=yy[0], y1=yy[1], x0=min_row[f"m_{se_name}"], x1=max_point,
                              fillcolor=_colors[color_id], opacity=0.25, layer="below", line_width=0))

    global rest_time
    m4 = datetime.now()
    m.debug(f"rest:{m4-m3} [{rest_time}]")
    rest_time += m4-m3

def gen_fig_scatter(
        data: list[ChunkList] | ChunkList | list[Chunk] | Chunk,  # data to plot
        show_start: bool = True,  # shows start timestamps if true
        show_end: bool = True,  # shows end timestamps if true
        show_real_mean: bool = False,  # vertical lines for mean of each idx of each chunk (using real data, not only the displayed points)
        show_real_duration: bool = False,  # shows a box, displaying area in time and entity space, where the datapoints are found (using real data, not only the displayed points)
        display_style: DisplayStyle = DisplayStyle.CLASSIC,
        same_colors_run: bool = False
):
    if type(data) is list:
        data = ChunkList(list(flatten(data)))
    if type(data) is not ChunkList:
        data = ChunkList([data])

    fig = go.Figure()
    shapes = []

    indexes = {}
    color_dict = {}
    new_index = 0
    color_id = 0
    for frame in data:
        index = 0
        first_occ = True
        if frame.td.name in indexes.keys():
            index = indexes[frame.td.name]
            first_occ = False
        else:
            indexes[frame.td.name] = new_index
            color_dict[frame.td.name] = 0
            index = new_index
            new_index += 1

        if show_start:
            __add_scatters_to_fig(fig, shapes, frame, display_style, index,
                                  (color_dict[frame.td.name] if same_colors_run else color_id), first_occ,
                                  show_real_mean, show_real_duration, True)
            color_dict[frame.td.name] += 1
            color_id += 1

        if show_end:
            __add_scatters_to_fig(fig, shapes, frame, display_style, index,
                                  (color_dict[frame.td.name] if same_colors_run else color_id), first_occ,
                                  show_real_mean, show_real_duration, False)
            color_dict[frame.td.name] += 1
            color_id += 1
        m.debug("draw: frame added")
    fig.update_xaxes(title="time")
    fig.update_yaxes(title="Entity ID")
    fig.update_layout(shapes=shapes)
    return fig

def __old_gen_fig_scatter(
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
