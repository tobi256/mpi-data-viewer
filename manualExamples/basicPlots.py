from dataLib import DataManager as dm
from dataLib import Chunk
from dataLib import Messenger
from dataLib import draw


# set Messenger min print level (0 = debug)
Messenger.Messenger.min_level = 1

# create a Data Manager
ds = dm.DataManager()
db = dm.DataManager()

# load Files
ds.read_timing("../../raw_time_data/allreduce_10/32_1/1.dat", "test1")
ds.read_timing("../../raw_time_data/allreduce_10/32_1/2.dat", "test2")
ds.read_timing("../../raw_time_data/allreduce_10/32_1/3.dat", "test3")

db.read_timing("../../raw_time_data/allreduce_10/32_32/1.dat", "test1")
db.read_timing("../../raw_time_data/allreduce_10/32_32/2.dat", "test2")
db.read_timing("../../raw_time_data/allreduce_10/32_32/3.dat", "test3")

# draw scatter plots
fig = draw.gen_fig_scatter(ds.create_chunks())
fig.show()

draw.gen_fig_scatter(db.get_timing_data("test3").create_chunk()).show()

cl = db.create_chunks(idx_start=2, idx_end=5)
cl.each_time_starts_zero_at_first()
draw.gen_fig_scatter(cl, show_end=False, show_mean=True).show()