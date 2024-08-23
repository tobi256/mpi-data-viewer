from dataLib import DataManager as dm
from dataLib import Chunk
from dataLib import Messenger
from dataLib import draw
from statistics import median
from statistics import mean
import time


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

# generate time table
cls = [cl1, cl2, cl3]
res = [["Execution Count", "Fastest Time", "Average Time", "Median Time", "Slowest Time"]]
for c in cls:
    durations = [x.get_execution_duration() for x in c]
    tempres = [len(durations), min(durations), mean(durations), median(durations), max(durations)]
    res.append(tempres)

for x in range(0, len(res[0])):
    for y in range(0, len(res)):
        if y == 0:
            print(res[y][x], end="")
        elif x == 0:
            print(" & "+str(res[y][x]), end="")
        else:
            print(" & "+str(round(res[y][x], 3))+"s", end="")

    print(" \\\\")

# copy chunk lists and filter min max med
mm1 = cl1.copy().each_filter_entities(additional_selection=Chunk.Filter.MIN | Chunk.Filter.MAX, custom_name_extension="min-max")
mm2 = cl2.copy().each_filter_entities(additional_selection=Chunk.Filter.MIN | Chunk.Filter.MAX, custom_name_extension="min-max")
mm3 = cl3.copy().each_filter_entities(additional_selection=Chunk.Filter.MIN | Chunk.Filter.MAX, custom_name_extension="min-max")


three_alg_comp_min_max = draw.gen_fig_scatter(
    data=[mm1[:2], mm1[11:13], mm1[-2:], mm2[:2], mm2[11:13], mm2[-2:], mm3[:2], mm3[11:13], mm3[-2:]],
    display_style=draw.DisplayStyle.RUN_LINE,
    show_real_mean=True,
    show_real_duration=True,
    same_colors_run=True,
    hide_menu=True)
#three_alg_comp_min_max.show()


alltoall1 = cl1[11].copy().filter_column('callid', filter_lambda=lambda id: id == 2, custom_name_extension="alltoall")
alltoall2 = cl2[11].copy().filter_column('callid', filter_lambda=lambda id: id == 2, custom_name_extension="alltoall")
alltoall3 = cl3[11].copy().filter_column('callid', filter_lambda=lambda id: id == 2, custom_name_extension="alltoall")

other1 = cl1[11].copy().filter_column('callid', filter_lambda=lambda id: id != 2, custom_name_extension="reduce")
other2 = cl2[11].copy().filter_column('callid', filter_lambda=lambda id: id != 2, custom_name_extension="reduce")
other3 = cl3[11].copy().filter_column('callid', filter_lambda=lambda id: id != 2, custom_name_extension="reduce")


three_alg_comp_scaled = draw.gen_fig_scatter(
    data=[alltoall1, alltoall2, alltoall3, other1, other2, other3],
    display_style=draw.DisplayStyle.RUN_SCALED,
    show_real_mean=True,
    show_real_duration=True,
    same_colors_run=True,
    hide_menu=True,
    draw_for_all=True)
#three_alg_comp_scaled.show()

atabow1 = db1.get_timing_data(alltoall1.td.name).create_chunk(idx_start=31, idx_end=41, standalone=True).time_starts_zero_at_first_value().filter_column('callid', filter_lambda=lambda id: id == 2, custom_name_extension="alltoall")
atabow2 = db2.get_timing_data(alltoall2.td.name).create_chunk(idx_start=31, idx_end=41, standalone=True).time_starts_zero_at_first_value().filter_column('callid', filter_lambda=lambda id: id == 2, custom_name_extension="alltoall")
atabow3 = db3.get_timing_data(alltoall3.td.name).create_chunk(idx_start=31, idx_end=41, standalone=True).time_starts_zero_at_first_value().filter_column('callid', filter_lambda=lambda id: id == 2, custom_name_extension="alltoall")


three_alg_comp_scaled_curve = draw.gen_fig_scatter(
    data=[atabow1, atabow2, atabow3],
    display_style=draw.DisplayStyle.RUN_SCALED,
    show_real_mean=True,
    show_real_duration=True,
    same_colors_run=True,
    hide_menu=True,
    draw_for_all=True)
three_alg_comp_scaled_curve.show()

# REMOVE TO GENERATE
#exit(0)

three_alg_comp_min_max.write_image("output/npb/three_alg_comp_min_max.pdf")
time.sleep(2)

three_alg_comp_min_max.update_layout(width=1500, height=800, margin=dict(l=10, r=10, t=10, b=10), showlegend=False)
three_alg_comp_min_max.write_image("output/npb/three_alg_comp_min_max.pdf")

three_alg_comp_scaled.update_layout(width=900, height=300, margin=dict(l=10, r=10, t=10, b=10), showlegend=True)
three_alg_comp_scaled.write_image("output/npb/three_alg_comp_scaled.pdf")

three_alg_comp_scaled.update_layout(width=3000, height=1500, margin=dict(l=10, r=10, t=10, b=10), showlegend=True)
three_alg_comp_scaled.write_image("output/npb/three_alg_comp_scaled_large.pdf")

three_alg_comp_scaled.update_xaxes(range=[5, 10])
three_alg_comp_scaled.update_layout(width=1200, height=400, margin=dict(l=10, r=10, t=10, b=10), showlegend=False)
three_alg_comp_scaled.write_image("output/npb/three_alg_comp_scaled_zoomed_5_10.pdf")

three_alg_comp_scaled.update_layout(width=3000, height=1500, margin=dict(l=10, r=10, t=10, b=10), showlegend=True)
three_alg_comp_scaled.write_image("output/npb/three_alg_comp_scaled_zoomed_5_10_large.pdf")

three_alg_comp_scaled.update_xaxes(range=[6, 7])

three_alg_comp_scaled.update_layout(width=1500, height=750, margin=dict(l=10, r=10, t=10, b=10), showlegend=False)
three_alg_comp_scaled.write_image("output/npb/three_alg_comp_scaled_zoomed_6_7.pdf")

three_alg_comp_scaled_curve.update_layout(width=1500, height=600, margin=dict(l=10, r=10, t=10, b=10), showlegend=False)
three_alg_comp_scaled_curve.write_image("output/npb/three_alg_comp_scaled_curve.pdf")

'''
mm1.each_filter_column('callid', filter_lambda=lambda c: c==2)
mm2.each_filter_column('callid', filter_lambda=lambda c: c==2)
mm3.each_filter_column('callid', filter_lambda=lambda c: c==2)


draw.gen_fig_scatter([ mm1[:2], mm1[11:13], mm1[-2:], mm2[:2], mm2[11:13], mm2[-2:], mm3[:2], mm3[11:13], mm3[-2:] ],
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
'''