from dataLib import DataManager as dm
from dataLib import Messenger


# set Messenger min print level (0 = debug)
Messenger.Messenger.min_level = 0

# create a Data Manager
d = dm.DataManager()

# load Files
d.read_timing("../raw_time_data/allreduce_10/32_1/1.dat", "test")

data = d.get_timing_data("test")

if data is None:
    print("no data")
else:
    #print(data.get_complete_raw_data_frame())
    data.load_range(1, 1)
    data.temp_print_df()
    data.load_range(0, 3)
    data.temp_print_df()
    data.load_range(1, 1)
    data.temp_print_df()

