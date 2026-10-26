import xarray as xr
import fsspec
import os

ds_nc = xr.open_mfdataset(f"{base_path}data/glorys/*.nc", combine="by_coords")
ds_chunked = ds_nc.chunk({"time": 5, "latitude": 400, "longitude": 400, "depth": 10})
ds_chunked.to_zarr("data/glorys.zarr", mode="w", consolidated=True)

store_url = "s3://training17/glorys.zarr"

os.environ["AWS_ACCESS_KEY_ID"] = "dfa72205c58e9d018341d09478a26d65"
os.environ["AWS_SECRET_ACCESS_KEY"] = "TiLmLsLDJB7OiCUVFCmBYLihdc0O3Q75CmL7VYqxiT7NKR1hXBTajwuQVlNvVpHD"

storage_options = {
    "key": os.environ["AWS_ACCESS_KEY_ID"],
    "secret": os.environ["AWS_SECRET_ACCESS_KEY"],
    "client_kwargs": {"endpoint_url": "https://atlantis-vis-o.s3-ext.jc.rl.ac.uk"},
    # The `config_kwargs` is required for JASMIN S3 object store.
    "config_kwargs": {
        "request_checksum_calculation": "when_required",
        "response_checksum_validation": "when_required",
    },
}

mapper = fsspec.get_mapper(
    store_url,
    **storage_options,
)

ds_nc_multi = xr.open_mfdataset(
    f"{base_path}data/glorys/*.nc",
    combine="by_coords",
)
print(ds_nc_multi)

ds_chunked.to_zarr(
    mapper,
    mode="w",
    consolidated=True,
)

ds_zarr = xr.open_zarr("data/glorys.zarr", consolidated=True)
print(ds_zarr)