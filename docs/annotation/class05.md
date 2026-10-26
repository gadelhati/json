# _Class 05_

```python
import xarray
import zarr

base_path = "/gws/ssde/j25b/atlantis_vis/cloud-native-geoscience-course/"

# in memory
store = zarr.open_group(f"{base_path}data/era5_sst/ocean_temperature_with_groups.zarr", mode="r")
print(store)

# lazy load
ds = xarray.open_zarr(f"{base_path}data/era5_sst/ocean_temperature.zarr")
ds
print("Dimensions: ", ds.dims)      # Dimensions
print("Data variables: ", ds.data_vars) # Data variables
print("Coordinates: ", ds.coords)    # Coordinate variables
sst = ds["sst"]
print(sst)
print("SST dims:", sst.dims)
```

object store: ?
dataset: zarr
    dataarray: chunk