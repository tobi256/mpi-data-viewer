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
cl[0].get_data()
# draw all runs below each other, showing all datapoints
draw.gen_fig_scatter(cl,
                     display_style=draw.DisplayStyle.RUN_SCALED,
                     show_real_mean=True,
                     show_real_duration=True,
                     same_colors_run=True).show()

# filter all data, so that only min, max and median values of each start/end timestamp operation remains
cl.each_filter_entities(additional_selection=Chunk.Filter.MIN_MAX_MED)

# draw all runs below each other, showing only the filtered points
draw.gen_fig_scatter(cl,
                     display_style=draw.DisplayStyle.RUN_LINE,
                     show_real_mean=True,
                     show_real_duration=True,
                     same_colors_run=True).show()

# reset the state of the data to before filters or groups were applied
cl.each_reset_filters_and_groups()

# filter data, drop everything except for the min, max 0-7 and every eighth point
cl.each_filter_entities(entity_selection_list=[0, 1, 2, 3, 4, 5, 6, 7],
                        entity_selection_lambda=lambda x: x % 8 == 0,
                        additional_selection=Chunk.Filter.MIN | Chunk.Filter.MAX)

# draw classic scatter plot
draw.gen_fig_scatter(cl, display_style=draw.DisplayStyle.CLASSIC).show()

# apply another filter on a column
cl.each_filter_column("p", lambda x: x < 100)

draw.gen_fig_scatter(cl, display_style=draw.DisplayStyle.CLASSIC).show()


