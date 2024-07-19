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

# Listing 3.3
single_chunk.filter_column("callid", lambda id: id == 1)

# Listing 3.4
chunk_list.each_filter_entities(
    entity_selection_list=[0, 1, 2, 3, 4, 5, 6, 7],
    entity_selection_lambda=lambda x: x % 8 == 0,
    additional_selection=Chunk.Filter.MIN | Chunk.Filter.MAX)