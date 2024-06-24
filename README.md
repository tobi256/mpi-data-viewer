# mpi-data-viewer

## DataManager

To read datafiles, use an instance of the `DataManager` class.
```python
from dataLib import DataManager as dm
db = dm.DataManager()
```
Files can be read individually or as entire folders.


``` python
db.read_timing(<path>, <name>)
```
- ***path***: path to file
- ***name***: a name to access data in `DataManager`

``` python
db.read_timing_folder(<folder_path>, <file_pattern>, <naming>)
```
- ***folder_path***: path to folder
- ***file_pattern***: (default=`timings_.*\\.dat`) regex pattern which files in the folder shall be used
- ***naming***: (default=`data?`) the names of the read files. The `?` will be replaced by a unique number for each read file.

The read files can be accessed through a `TimingData` instance which can be accessed through the name.
```python
timingdata = db.get_timing_data(<name>)
```
- ***name***: the name specified when reading the file

It is also possible to directly create `Chunks` for every `TimingData` instance in the `DataManager` by calling `db.create_chunks(<args...>)`.
If used, `create_chunk` is called for every `TimingData` instance with the given arguments.


## TimingData

TimingData holds the actual references to files. 
It reads the data into Dataframes and makes them available.
`TimingData` instances should only be created by usage of `DataManager`.
The most important ability of the `TimingData` class is to creat `Chunks`.
Information on how to access a `TimingData` instance, look at `DataManager` documentation.

```python
chunk = timingdata.create_chunk(<idx_start>, <idx_end>, <p_start>, <p_end>, <standalone>)
```
- ***idx_start***: (default=`0`) the first index to be included
- ***idx_end***: (default=`None`--> max idx) the last index to be included
- ***p_start***: (default=`0`) the first entity to be included
- ***p_end***: (default=`None`--> max p) the last entity to be included
- ***standalone***: (default=`False`) if True, an explicit copy is made. Depending on what the Chunk is used for, this might happen later implicitly anyways

## Chunk / ChunkList

Chunks hold a subset of the information of a file.
They are created by a `TimingData` instance and are used to modify, filter, group and display the data.
A `Chunk` instance can be used alone or in a group of Chunks as `ChunkList`.
A `ChunkList` has many of the same functions as a `Chunk` with the prefix `each_`.
Each of these functions calls the corresponding function of every `Chunk` instance in the `ChunkList` with the given arguments.


Calculates the mean of the start-timestamps of the first operation and shifts all timestamps by this value. 
The result is that the timestamp of the first mean is now exactly 0. Implicitly makes chunk stand alone. 
```python
chunk.(each_)time_starts_zero_at_first_mean()
```

Searches for first timestamp and shifts all timestamps by this value. 
The result is that the value of the first occurring timestamp is now exactly 0. Implicitly makes chunk stand alone. 
```python
chunk.(each_)time_starts_zero_at_first_value()
```

Removes all filters and groups.
```python
chunk.(each_)reset_filters_and_groups()
```

Copies the Chunk(s). Copies are always standalone.
```python
new_chunk = chunk.copy()
```

Filter options for `filter_entities`.
```python
# If there is no singular Median, two points will be selected.
# note: using first and last in combination with other parameters may lead to errors.
#    Points will not be duplicated, and max, min and median are prioritized.
#    If point is first and min, it will be displayed as min.
class Filter(Flag):
    NOTHING = 0  # will be overwritten if used in combination with something else
    FIRST =     0b0000_0001  # entity with the lowest id in the set
    LAST =      0b0000_0010  # entity with the highest id in the set
    MIN =       0b0000_0100  # entity with the lowest value in the set
    MAX =       0b0000_1000  # entity with the highest value in the set
    MEDIAN =    0b0001_0000  # median of value-set, or 2 values which would be used to calculate median
    MIN_MAX_MED = MIN | MAX | MEDIAN
```

Powerful way to filter entities. 
```python
chunk.(each_)filter_entities(
        entity_selection_list: list[int] | None = None,
        entity_selection_lambda: Callable[[int], bool] | None = None,
        additional_selection: Filter = Filter.NOTHING,
        filter_start: bool = True,
        filter_end: bool = True,
        remove_duplicates: bool = True,
        keep_selection_and_drop_unselected: bool = True)
```
- ***entity_selection_list***: define specific entities in a list
- ***entity_selection_lambda***: pass a function which gets the entities and returns a boolean which entities to keep
- ***additional_selection***: pass a Filter like min to be filtered. Applied to every operation individually. different operations may have different max-entities values
- ***filter_start***: defines if start timestamps are filtered
- ***filter_end***: defines if end timestamps are filtered
- ***remove_duplicates***: defines if all but one entity shall be removed if multiple entities are suitable for additional_selection. For example there are 3 entities with identical min timestamps, two of them would be removed.
- ***keep_selection_and_drop_unselected***: weather the selection should be kept or removed

Filter timestamps by column values.
```python
chunk.(each_)filter_column(<column_name>, <filter_lambda>)
```
- ***column_name***: the name of the column
- ***filter_lambda***: a lambda function which gets the values of the selected column and returns true or false

Filter timestamps by row values.
```python
chunk.(each_)filter_rows(<filter_lambda>)
```
- ***filter_lambda***: a lambda function which gets the rows of the chunk and returns true or false


```python
chunk.(each_)group_entities(
        self,
        linear_size: int | None = None,  
        lambda_selector: Callable[[int], int] | None = None, 
        aggr_start_end: Callable = "mean"
):
```
- ***linear_size***: a number N; from first to last always N elements are grouped
- ***lambda_selector***: a function which gets the entity id and returnes a number of which group this entity shall be now a part of
- ***aggr_start_end***: defines what function shall be used to aggregate start and end timestamp values

## Data Format

Files must contain meta-data at the top of the file in following format: `#@ <id>=<value>`.
Following ids are expected:
- ***time***: timestamp of the execution
- ***nprocs***: number of overall processes
- ***nnodes***: number of used compute nodes
- ***ppn***: number of processes per node
- ***num_timestamps***: number of overall operations traced
- ***nb_processes_sampled***: number of overall processes which were traced

Files must contain the following columns:
- ***p***: entity id
- ***idx***: operation index
- ***start***: timestamp of entry in collective operation
- ***exit***: timestamp of exit of collective operation
- ***callid***
- ***region***
- ***buf_size***
- ***comm_size***

## Messenger

Messenger is a helper class to provide consistent messaging. 
Set `Messenger.min_level` to a higher value to restrict the printed messages:
- 0: debug
- 1: info
- 2: warning
- 3: error
- 4: critical