# mpi-data-viewer

## dataLib

### TimingData

TimingData is a wrapper for an MPI timestamp log file. 
It saves the meta information like which cores and nodes were used.
It provides access to the whole dataset or subsets (Chunks) of it.
It may drop the Dataframe to free memory for other data. It can be instructed to load the data again.

### Chunk

A chunk is a subset of the data of a TimingData object.
It is to be used, when specific parts of the file are needed.
It references per default the data from a TimingData object, but may be instructed to make a local copy.
If a copy is made, it acts as standalone and the data of the TimingData may be dropped.
If not, the Chunk is registered in the TimingData object and blocks the dropping of the data.
The `get_data` function of the Chunk object is therefore always safe to use. 
A Chunk object works with the data which was specified at creation. 
If not all entities were selected, the mean will only be applied to the selected entities, which may result in
unexpected results. To keep data-consistency, select the whole range of entities and use the filter functionality of the
Chunk to cut down the display size. Filter and Group functionality of the Chunk change only what is displayed, but 
use the real full dataset in the background. Keep in mind that using functions which truly change the data of the Chunk,
like `time_starts_zero_at_first_value`, will change the underlying data and then recalculate the filters and groupings.

### DataManager

DataManager organizes a set of TimingData objects and enables operations over all or some of its TimingData objects.

### Messenger

Messenger is a helper class to provide consistent messaging. 
Set `Messenger.min_level` to a higher value to restrict the printed messages:
- 0: debug
- 1: info
- 2: warning
- 3: error
- 4: critical