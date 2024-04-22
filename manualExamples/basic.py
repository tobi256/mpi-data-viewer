from dataLib import DataManager as dm
from dataLib import Chunk
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
    # create chunk containing only the first timestamp and only Processes 0 to 7
    c1 = data.create_chunk(0, 0, 0, 7)
    c1.make_standalone()  # keeps its on copy of the selected data, independent of TimingData object
    print(c1.get_data())

    # create chunk containing all data (needs to reload data)
    c2 = data.create_chunk()
    print(c2.get_data())

    # create chunk containing all processes for timestamps 4 and 5 (no need to reload data)
    c3 = data.create_chunk(4, 5)
    print(c3.get_data())



