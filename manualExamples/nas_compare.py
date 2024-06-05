from dataLib import DataManager as dm
from dataLib import Chunk
from dataLib import Messenger
from dataLib import draw


# set Messenger min print level (0 = debug)
Messenger.Messenger.min_level = 0


# create a Data Manager
db1 = dm.DataManager()
db2 = dm.DataManager()
db3 = dm.DataManager()

# load Files
db1.read_timing_folder("/Users/tobi/projects/bach/raw_time_data/nas_ft_d/alg1", naming="alg1_?", file_pattern="nas_ft_D.*\\.dat")
db2.read_timing_folder("/Users/tobi/projects/bach/raw_time_data/nas_ft_d/alg2", naming="alg2_?", file_pattern="nas_ft_D.*\\.dat")
db3.read_timing_folder("/Users/tobi/projects/bach/raw_time_data/nas_ft_d/alg3", naming="alg3_?", file_pattern="nas_ft_D.*\\.dat")

# create a chunk-list containing same sized chunks from every read data file
cl1 = db1.create_chunks()
cl2 = db2.create_chunks()
cl3 = db3.create_chunks()

# update the data, so the first timestamp of each run starts at 0
cl1.each_time_starts_zero_at_first_value()
cl2.each_time_starts_zero_at_first_value()
cl3.each_time_starts_zero_at_first_value()

# copy chunk lists and filter min max med
mmm1 = cl1.copy().each_filter_entities(additional_selection=Chunk.Filter.MIN_MAX_MED)
mmm2 = cl2.copy().each_filter_entities(additional_selection=Chunk.Filter.MIN_MAX_MED)
mmm3 = cl3.copy().each_filter_entities(additional_selection=Chunk.Filter.MIN_MAX_MED)

# draw all runs below each other as lines, to get an overview
draw.gen_fig_scatter([mmm1, mmm2, mmm3],
                     display_style=draw.DisplayStyle.RUN_LINE,
                     show_real_mean=True,
                     show_real_duration=True,
                     same_colors_run=True).show()

# group datapoints into their nodes
ng1 = cl1.copy().each_group_entities()
ng2 = cl2.copy().each_group_entities()
ng3 = cl3.copy().each_group_entities()

# draw nodes and mmm values
draw.gen_fig_scatter([ng1, mmm1],
                     display_style=draw.DisplayStyle.RUN_SCALED,
                     show_real_mean=True,
                     show_real_duration=True,
                     same_colors_run=True).show()

draw.gen_fig_scatter([ng2, mmm2],
                     display_style=draw.DisplayStyle.RUN_SCALED,
                     show_real_mean=True,
                     show_real_duration=True,
                     same_colors_run=True).show()

draw.gen_fig_scatter([ng3, mmm3],
                     display_style=draw.DisplayStyle.RUN_SCALED,
                     show_real_mean=True,
                     show_real_duration=True,
                     same_colors_run=True).show()
