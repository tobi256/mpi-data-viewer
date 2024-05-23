from dataLib import DataManager as dm
from dataLib import Chunk
from dataLib import Messenger
from dataLib import draw


# set Messenger min print level (0 = debug)
Messenger.Messenger.min_level = 1


# create a Data Manager
db = dm.DataManager()
# big_data = dm.DataManager()

# load Files
db.read_timing_folder("/Users/tobi/projects/bach/raw_time_data/new_comp/allreduce_10")
# big_data.read_timing_folder("/Users/tobi/projects/bach/raw_time_data/new_comp/miniAMR/")

# create a chunk-list containing same sized chunks from every read data file
cl = db.create_chunks()

# update the data, so the first timestamp of each run starts at 0
cl.each_time_starts_zero_at_first_value()

# create a copy of the ChunkList and filter the min, max and median values
min_max_median = cl.copy()
min_max_median.each_filter_entities(additional_selection=Chunk.Filter.MIN_MAX_MED)

# create a copy of the ChunkList and group them by their nodes
node_groups = cl.copy()
node_groups.each_group_entities()

# draw scatter graph with all data
draw.gen_fig_scatter(
    [node_groups, min_max_median],
    display_style=draw.DisplayStyle.RUN_SCALED,
    show_real_mean=True,
    show_real_duration=True,
    same_colors_run=True
).show()

# apply a row filter, select all values where the difference of the start and end is bigger than n
n = 0.00008
node_groups.each_filter_rows(lambda row: (row["end"] - row["start"]) > n)
draw.gen_fig_scatter(
    node_groups,
    display_style=draw.DisplayStyle.RUN_SCALED,
    same_colors_run=True
).show()

