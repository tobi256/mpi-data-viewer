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
cl = db.create_chunks()
cl.each_time_starts_zero_at_first_value()
#cl.temp_each_filter_entities(additional_selection=Chunk.Filter.MIN_MAX_MED)
c1 = db.get_timing_data("data0").create_chunk(idx_end=4)
c1.time_starts_zero_at_first_value()
#c1.filter_entities(entity_selection_list=[0,1,2,3,4,5], entity_selection_lambda=lambda x: x % 10 == 0, additional_selection=(Chunk.Filter.ALL))
draw.test_gen_fig_scatter(cl, display_style=draw.DisplayStyle.CLASSIC, show_end=True, show_real_mean=True).show()
draw.test_gen_fig_scatter(cl, display_style=draw.DisplayStyle.RUN_LINE, show_end=True, show_real_mean=True).show()
draw.test_gen_fig_scatter(cl, display_style=draw.DisplayStyle.RUN_SCALED, show_end=True, show_real_mean=True).show()

'''
c2 = db.get_timing_data("data0").create_chunk(idx_end=4)
c2.time_starts_zero_at_first_value()
c2.filter_entities(entity_selection_lambda=lambda x: x < 100)
draw.test_gen_fig_scatter(c2).show()
'''
#draw.test_gen_fig_scatter([c1, c2]).show()



#cl = db.create_chunks(idx_end=4)
#cl.each_time_starts_zero_at_first_value()
#draw.gen_fig_scatter(cl, show_end=False, show_mean=True).show()



#big_data = dm.DataManager()
#big_data.read_timing_folder("/Users/tobi/projects/bach/raw_time_data/new_comp/miniAMR/")

