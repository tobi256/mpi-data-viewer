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
#draw.gen_fig_scatter(cl[0:4], show_end=False, show_mean=True).show()
#draw.gen_fig_scatter(cl, show_end=False, show_mean=True).show()
draw.gen_fig_diff_timing(cl[0], cl[1], show_points=False).show()

big_data = dm.DataManager()
big_data.read_timing_folder("/Users/tobi/projects/bach/raw_time_data/new_comp/miniAMR/")
second_hundred = big_data.create_chunks(idx_start=100, idx_end=119)
second_hundred.each_time_starts_zero_at_first()
draw.gen_fig_scatter(second_hundred, show_end=False, show_mean=True).show()
draw.gen_fig_diff_timing(second_hundred[0], second_hundred[1], show_points=True, show_mean=True).show()
all = big_data.create_chunks().each_time_starts_zero_at_first_value()
draw.gen_fig_histo_rel_to_mean(all).show()

