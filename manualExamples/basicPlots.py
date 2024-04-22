from dataLib import DataManager as dm
from dataLib import Chunk
from dataLib import Messenger
from dataLib import draw


# set Messenger min print level (0 = debug)
Messenger.Messenger.min_level = 0

# create a Data Manager
d = dm.DataManager()

# load Files
d.read_timing("../../raw_time_data/allreduce_10/32_1/1.dat", "test1")
d.read_timing("../../raw_time_data/allreduce_10/32_1/2.dat", "test2")
d.read_timing("../../raw_time_data/allreduce_10/32_1/3.dat", "test3")

c1 = d.get_timing_data("test1").create_chunk()
c2 = d.get_timing_data("test2").create_chunk()
c3 = d.get_timing_data("test3").create_chunk()

fig = draw.gen_fig_scatter([c1, c2, c3])
fig.show()
