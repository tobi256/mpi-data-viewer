import pandas as pd

from dataLib import DataManager as dm
from dataLib import Chunk
from dataLib import Messenger
from dataLib import draw


# set Messenger min print level (0 = debug)
Messenger.Messenger.min_level = 1

# create a Data Manager
db = dm.DataManager()

# load Files
db.read_timing_folder("/Users/tobi/projects/bach/raw_time_data/new_comp/allreduce_10")

# create a chunk-list containing same sized chunks from every read data file
cl = db.create_chunks()

# update the data, so the first timestamp of each run starts at 0
cl.each_time_starts_zero_at_first_value()

draw.gen_fig_scatter(
    cl,
    display_style=draw.DisplayStyle.RUN_SCALED,
    show_real_mean=True,
    show_real_duration=True,
    same_colors_run=True
).show()

# ADVANCED FILTER goal:
# -> assume: Percent values refer to a percentage of the duration from min to max per idx and entity and start/stop
# Select only the points, which are in the range of 10% smaller and 20% larger than the median.
lower_percent = 0.1
upper_percent = 0.2

# first get the min max median values to simplify later calculation
cl_min = cl.copy()
cl_min.each_filter_entities(additional_selection=Chunk.Filter.MIN)

cl_max = cl.copy()
cl_max.each_filter_entities(additional_selection=Chunk.Filter.MAX)

cl_med = cl.copy()
cl_med.each_filter_entities(additional_selection=Chunk.Filter.MEDIAN)

# iterate over every chunk and calculate the values
filter_cl = cl.copy()
for x in range(0, len(filter_cl)):
    original = filter_cl[x].get_data()  # get the data from the chunk
    med = cl_med[x].get_data()  # get data from median to avoid calculation

    # calculate the wanted dataset
    med = med.drop_duplicates(subset=["idx", "is_start"], keep="first")
    temp = pd.merge(cl_min[x].get_data(), cl_max[x].get_data(),
                        on=["idx", "is_start"], suffixes=("_min", "_max"), validate="1:1")
    temp["duration"] = temp.apply(lambda row:
            ((row["start_max"] - row["start_min"]) if row["is_start"] else (row["end_max"] - row["end_min"])), axis=1)

    temp = pd.merge(temp, med, on=["idx", "is_start"], suffixes=(None, "_med"), validate="1:1")
    temp["median"] = temp.apply(lambda row: row["start"] if row["is_start"] else row["end"], axis=1)

    temp["fil_lower"] = temp.apply(lambda row: row["median"] - row["duration"] * lower_percent, axis=1)
    temp["fil_upper"] = temp.apply(lambda row: row["median"] + row["duration"] * upper_percent, axis=1)
    duration = temp.drop([name for name in temp.columns if name not in ["idx", "is_start", "fil_lower", "fil_upper"]],
                         axis=1)
    temp = pd.merge(original, duration, on=["idx", "is_start"], validate="m:1")
    f_start = temp[(temp["is_start"]) & (temp["start"] >= temp["fil_lower"]) & (temp["start"] <= temp["fil_upper"])]
    f_end = temp[(~temp["is_start"]) & (temp["end"] >= temp["fil_lower"]) & (temp["end"] <= temp["fil_upper"])]
    filtered = pd.concat([f_start, f_end])
    filtered = filtered.drop([name for name in filtered.columns if name not in original.columns], axis=1)  # drop unused cols

    filter_cl[x].set_data(filtered, "f10_20")  # reinsert data into chunk, and name operation

min_max_cl = cl.copy()
min_max_cl.each_filter_entities(additional_selection=Chunk.Filter.MIN | Chunk.Filter.MAX)

# display the filtered data
draw.gen_fig_scatter(
    [filter_cl, min_max_cl],
    display_style=draw.DisplayStyle.RUN_SCALED,
    show_real_mean=True,
    show_real_duration=True,
    same_colors_run=True
).show()

