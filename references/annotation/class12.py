import os
import xarray as xr
import icechunk as ic

os.environ["AWS_ACCESS_KEY_ID"] = "dfa72205c58e9d018341d09478a26d65"
os.environ["AWS_SECRET_ACCESS_KEY"] = "TiLmLsLDJB7OiCUVFCmBYLihdc0O3Q75CmL7VYqxiT7NKR1hXBTajwuQVlNvVpHD"

storage_options = {
    "key": os.environ["AWS_ACCESS_KEY_ID"],
    "secret": os.environ["AWS_SECRET_ACCESS_KEY"],
    "client_kwargs": {
        "endpoint_url": "https://atlantis-vis-o.s3-ext.jc.rl.ac.uk"
    },
    "config_kwargs": {
        "request_checksum_calculation": "when_required",
        "response_checksum_validation": "when_required",
    },
}

base_path = "/gws/ssde/j25b/atlantis_vis/cloud-native-geoscience-course/"

ds = xr.open_zarr(f"{base_path}data/era5_sst/ocean_temperature.zarr")

#print(ds)

storage_settings = ic.StorageSettings(
    unsafe_use_conditional_update=False,
    unsafe_use_conditional_create=False,
)

repo_config = ic.RepositoryConfig(storage=storage_settings)
repo = ic.Repository.open_or_create(storage, config=repo_config)

from icechunk.xarray import to_icechunk

session = repo.writable_session("main")

to_icechunk(
    ds,
    session,
)

snapshot = session.commit("Initial import of local Zarr dataset")

print(snapshot)

ro_session = repo.readonly_session("main")