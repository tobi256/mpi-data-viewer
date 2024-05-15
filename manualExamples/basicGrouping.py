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
draw.gen_fig_scatter(cl, display_style=draw.DisplayStyle.RUN_SCALED).show()
cl.each_group_entities(lambda_selector=lambda x: x % 7)
draw.gen_fig_scatter(cl, display_style=draw.DisplayStyle.RUN_SCALED).show()
cl.each_reset_filters_and_groups()
cl.each_group_entities(linear_size=128)
draw.gen_fig_scatter(cl, display_style=draw.DisplayStyle.RUN_SCALED).show()