from dataLib import DataManager as dm
from dataLib import Chunk
from dataLib import Messenger
from dataLib import draw


# set Messenger min print level (0 = debug)
Messenger.Messenger.min_level = 0

# create a Data Manager
db = dm.DataManager()

# load Files
db.read_timing_folder("/Users/tobi/projects/bach/raw_time_data/new_comp/allreduce_10")

c1 = db.get_timing_data("data0").create_chunk(idx_end=4)
c1.time_starts_zero_at_first_value()
draw.test_gen_fig_scatter(c1).show()
c1.filter_entities(entity_selection_list=[0,1,2,3,4,5], entity_selection_lambda=lambda x: x > 100, additional_selection=(Chunk.Filter.ALL))
draw.test_gen_fig_scatter(c1).show()


#cl = db.create_chunks(idx_end=4)
#cl.each_time_starts_zero_at_first_value()
#draw.gen_fig_scatter(cl, show_end=False, show_mean=True).show()



#big_data = dm.DataManager()
#big_data.read_timing_folder("/Users/tobi/projects/bach/raw_time_data/new_comp/miniAMR/")

