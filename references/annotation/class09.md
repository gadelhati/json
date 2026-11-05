init_time, lead_time, latitude, longitude

temperature_2m = ds['temperature_2m'].isel(init_time=slice(-1, None))
temperature_2m_local.isel(init_time=0, lead_time=0).plot()
wind_u_10m = ds['wind_u_10m'].sel(init_time="2025-01-01",method="nearest").isel(lead_time=0)
swh = swh.sel(latitude=-23.0, longitude=-43.0, method="nearest").plot(cmap="RdBu_r")