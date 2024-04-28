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

cl = db.create_chunks()
cl.each_time_starts_zero_at_first()
draw.gen_fig_scatter(cl[0:4], show_end=False).show()