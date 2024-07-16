from dataLib import DataManager as dm
from dataLib import Chunk
from dataLib import Messenger
from dataLib import draw


# Listing 3.1
db = dm.DataManager()
db.read_timing_folder("path/to/folder", "trace_.*\\.dat", "name_?")

# Listing 3.2
single_trace = db.get_timing_data("name_of_trace")
single_chunk = single_trace.create_chunk()
chunk_list = db.create_chunks()


