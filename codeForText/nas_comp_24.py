from dataLib import DataManager as dm
from dataLib import Chunk
from dataLib import Messenger
from dataLib import draw


# set Messenger min print level (0 = debug)
Messenger.Messenger.min_level = 0

'''
In this file, the comparison between three alltoall algorithms is analyzed by 24 runs each on 32 Nodes with 32 Processes.
'''


# create a Data Manager
db1 = dm.DataManager()
db2 = dm.DataManager()
db3 = dm.DataManager()

# load Files
db1.read_timing_folder("/Users/tobi/projects/bach/raw_time_data/bach_files/nas/data", naming="alg1_?", file_pattern=".*alg1.*")
db2.read_timing_folder("/Users/tobi/projects/bach/raw_time_data/bach_files/nas/data", naming="alg2_?", file_pattern=".*alg2.*")
db3.read_timing_folder("/Users/tobi/projects/bach/raw_time_data/bach_files/nas/data", naming="alg3_?", file_pattern=".*alg3.*")

# create a chunk-list containing same sized chunks from every read data file
cl1 = db1.create_chunks()
cl2 = db2.create_chunks()
cl3 = db3.create_chunks()

# update the data, so the first timestamp of each run starts at 0
cl1.each_time_starts_zero_at_first_value().sort_by_duration()
cl2.each_time_starts_zero_at_first_value().sort_by_duration()
cl3.each_time_starts_zero_at_first_value().sort_by_duration()

# copy chunk lists and filter min max med
mm1 = cl1.copy().each_filter_entities(additional_selection=Chunk.Filter.MIN | Chunk.Filter.MAX)
mm2 = cl2.copy().each_filter_entities(additional_selection=Chunk.Filter.MIN | Chunk.Filter.MAX)
mm3 = cl3.copy().each_filter_entities(additional_selection=Chunk.Filter.MIN | Chunk.Filter.MAX)

'''
# draw all runs below each other as lines, to get an overview
draw.gen_fig_scatter([mm1],
                     display_style=draw.DisplayStyle.RUN_LINE,
                     show_real_mean=True,
                     show_real_duration=True,
                     same_colors_run=True).show()

draw.gen_fig_scatter([mm2],
                     display_style=draw.DisplayStyle.RUN_LINE,
                     show_real_mean=True,
                     show_real_duration=True,
                     same_colors_run=True).show()

draw.gen_fig_scatter([mm3],
                     display_style=draw.DisplayStyle.RUN_LINE,
                     show_real_mean=True,
                     show_real_duration=True,
                     same_colors_run=True).show()
'''

draw.gen_fig_scatter([ mm1[:2], mm1[11:13], mm1[-2:], mm2[:2], mm2[11:13], mm2[-2:], mm3[:2], mm3[11:13], mm3[-2:] ],
                     display_style=draw.DisplayStyle.RUN_LINE,
                     show_real_mean=True,
                     show_real_duration=True,
                     same_colors_run=True).show()

mm1.each_filter_column('callid', filter_lambda=lambda c: c==2)
mm2.each_filter_column('callid', filter_lambda=lambda c: c==2)
mm3.each_filter_column('callid', filter_lambda=lambda c: c==2)


draw.gen_fig_scatter([ mm1[:2], mm1[11:13], mm1[-2:], mm2[:2], mm2[11:13], mm2[-2:], mm3[:2], mm3[11:13], mm3[-2:] ],
                     display_style=draw.DisplayStyle.RUN_LINE,
                     show_real_mean=True,
                     show_real_duration=True,
                     same_colors_run=True).show()


'''
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
'''