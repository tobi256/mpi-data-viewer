import time

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
db.read_timing_folder("/Users/tobi/projects/bach/raw_time_data/bach_files/min_example", file_pattern="dat.?\\.dat", naming="run ?")
# big_data.read_timing_folder("/Users/tobi/projects/bach/raw_time_data/new_comp/miniAMR/")

# create a chunk-list containing same sized chunks from every read data file
cl = db.create_chunks()

# update the data, so the first timestamp of each run starts at 0
cl.each_time_starts_zero_at_first_value()

min_exam_classic = draw.gen_fig_scatter(
    data=cl[0],
    show_real_mean=True,
    show_real_duration=True,
    display_style=draw.DisplayStyle.CLASSIC,
    hide_menu=True)

min_exam_scaled = draw.gen_fig_scatter(
    data=cl,
    show_real_mean=True,
    show_real_duration=True,
    display_style=draw.DisplayStyle.RUN_SCALED,
    hide_menu=True,
    same_colors_run=True)

cl.each_filter_entities(additional_selection=Chunk.Filter.MIN|Chunk.Filter.MAX)

min_exam_line = draw.gen_fig_scatter(
    data=cl,
    show_real_mean=True,
    show_real_duration=True,
    display_style=draw.DisplayStyle.RUN_LINE,
    hide_menu=True,
    same_colors_run=True)

# print once to get rid of bug; info box bottom left corner
min_exam_classic.write_image("output/min_example_classic.pdf")
time.sleep(2)

min_exam_classic.update_layout(width=1000, height=600, margin=dict(l=10, r=10, t=10, b=10))
min_exam_classic.write_image("output/min_example_classic.pdf")

min_exam_line.update_layout(width=1000, height=450, margin=dict(l=10, r=10, t=10, b=10))
min_exam_line.write_image("output/min_example_line.pdf")

min_exam_scaled.update_layout(width=1000, height=600, margin=dict(l=10, r=10, t=10, b=10))
min_exam_scaled.write_image("output/min_example_scaled.pdf")