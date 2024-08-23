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

def __add_scatters_to_fig(fig, shapes, frame, display_style, index, color_id, first_occ, show_real_mean, show_real_duration, is_start):
    se_name = "start" if is_start else "end"
    fd = frame.get_data()
    p_disp_count = frame.p_end - frame.p_start
    fds = fd[(fd["is_start"] if is_start else ~fd["is_start"])].copy()
    if display_style == DisplayStyle.RUN_LINE:
        fds["xaxis"] = index
    elif display_style == DisplayStyle.RUN_SCALED:
        fds["xaxis"] = fds["p"].apply(
            lambda s: (s / p_disp_count) * (1 - 2 * __SPACE_BETWEEN_RUNNS) + __SPACE_BETWEEN_RUNNS + index)

    desc = fds.apply((_gen_full_hover_text_is_start if is_start else _gen_full_hover_text_is_end), axis=1)

    fig.add_scattergl(x=fds[se_name], y=(fds['p'] if display_style == DisplayStyle.CLASSIC else fds['xaxis']),
                      name=f"{frame.td.name} {frame.get_name_extension()} [{se_name}]", mode='markers', marker=dict(color=_colors[color_id]),
                      hovertext=desc, hoverinfo="text")

    if first_occ and show_real_mean:
        for i, x in frame.get_mean_times_by_idx().iterrows():
            if fd['idx'].isin([i]).any():
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
            if fd['idx'].isin([min_row['idx']]).any():
                max_point = max_vals.loc[max_vals["idx"] == min_row["idx"], f"m_{se_name}"].values[0]
                if display_style == DisplayStyle.CLASSIC:
                    fig.add_vrect(x0=min_row[f"m_{se_name}"], x1=max_point, fillcolor=_colors[color_id], opacity=0.25,
                                  layer="below", line_width=0, line=dict(width=0))
                else:
                    yy = (0, 0)
                    if display_style == DisplayStyle.RUN_LINE:
                        yy = (index - __RELATIVE_HEIGHT_OF_BOX, index + __RELATIVE_HEIGHT_OF_BOX)
                    elif display_style == DisplayStyle.RUN_SCALED:
                        yy = (index + __SPACE_BETWEEN_BOXES, index + 1 - __SPACE_BETWEEN_BOXES)
                    shapes.append(dict(type="rect", y0=yy[0], y1=yy[1], x0=min_row[f"m_{se_name}"], x1=max_point,
                                  fillcolor=_colors[color_id], opacity=0.25, layer="below", line_width=0, line=dict(width=0)))


def gen_fig_scatter(
        data: list[ChunkList] | ChunkList | list[Chunk] | Chunk,  # data to plot
        show_start: bool = True,  # shows start timestamps if true
        show_end: bool = True,  # shows end timestamps if true
        show_real_mean: bool = False,  # vertical lines for mean of each idx of each chunk (using real data, not only the displayed points)
        show_real_duration: bool = False,  # shows a box, displaying area in time and entity space, where the datapoints are found (using real data, not only the displayed points)
        display_style: DisplayStyle = DisplayStyle.CLASSIC,
        same_colors_run: bool = False,
        hide_menu: bool = False
):
    print(data)
    if type(data) is list:
        data = ChunkList(list(flatten(data)))
    if type(data) is not ChunkList:
        data = ChunkList([data])
    print(data)
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
            if display_style == DisplayStyle.RUN_LINE or display_style == DisplayStyle.RUN_SCALED:
                fig.add_annotation(
                    x=0,
                    y=(index if display_style == DisplayStyle.RUN_LINE else index+0.5),
                    text=f"{frame.td.name} ",
                    showarrow=False,
                    font=dict(size=20),
                    xanchor="right",
                    hovertext=f"file: {frame.td.file_path}")

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
    fig.update_xaxes(title="Time (s)")
    if display_style == DisplayStyle.CLASSIC:
        fig.update_yaxes(title="Process ID")
    elif display_style == DisplayStyle.RUN_LINE or display_style == DisplayStyle.RUN_SCALED:
        fig.update_yaxes(title="Runs", showticklabels=False)
    if not hide_menu and (show_real_mean or show_real_duration):
        fig.update_layout(
            updatemenus=[
                dict(
                    type="buttons",
                    direction="left",
                    buttons=list([
                        dict(
                            args=[{"shapes": []}],
                            label="Hide",
                            method="relayout"
                        ),
                        dict(
                            args=[{"shapes": shapes}],
                            label="Show",
                            method="relayout"
                        )
                    ]),
                    pad={"r": 10, "t": 10},
                    showactive=True,
                    x=0.11,
                    xanchor="left",
                    y=1.1,
                    yanchor="top"
                ),
            ]
        )
        fig.add_annotation(
            x=0,
            y=1.08,
            text=f"Real mean and boxes: ",
            showarrow=False,
            font=dict(size=12),
            yref="paper",
            align="left")
    fig.update_layout(shapes=shapes)
    return fig