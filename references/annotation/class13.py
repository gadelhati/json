import xarray as xr

base_path = "/gws/ssde/j25b/atlantis_vis/cloud-native-geoscience-course/" # or "" if you have the data in your current working directory

ds_nc = xr.open_mfdataset(f"{base_path}data/daily_swh/swh_*.nc", combine="by_coords")

print(ds_nc)
print(ds_nc.dims)
print(ds_nc.data_vars)
print(ds_nc.coords)

import glob

# obstore é melhor que boto3, para trabalhar com object stores locais

from obstore.store import LocalStore
from obspec_utils.registry import ObjectStoreRegistry
from virtualizarr import open_virtual_mfdataset
from virtualizarr.parsers import HDFParser

data_dir = f"{base_path}data/daily_swh/"

file_paths = sorted(glob.glob(f"{data_dir}*.nc"))
urls = [f"file://{path}" for path in file_paths]

store = LocalStore(data_dir)
registry = ObjectStoreRegistry({f"file://{data_dir}": store})

parser = HDFParser()

vds = open_virtual_mfdataset(
    urls=urls,
    parser=parser,
    registry=registry,
    combine="nested",
    concat_dim="time", # the files are combined along the time dimension
)

print(vds)

##

import icechunk as ic

# This is the path where the Icechunk repository will be created
storage = ic.local_filesystem_storage("data/daily_swh_icechunk/")

# Because we are using a virtual dataset, we need to tell Icechunk where to find the original NetCDF files when reopening the snapshot. This is done by creating a virtual chunk container that points to the local filesystem store.
config = ic.RepositoryConfig.default()
config.set_virtual_chunk_container(
    ic.VirtualChunkContainer(f"file://{data_dir}", ic.local_filesystem_store(data_dir))
)

repo = ic.Repository.create(storage, config)
repo.save_config()

session = repo.writable_session("main")

vds.vz.to_icechunk(session.store)

snapshot_id = session.commit("Initial virtual reference set for daily_swh NetCDF files")
print("Committed snapshot:", snapshot_id)