import xarray as xr

# Abrindo um conjunto de dados NetCDF
dataset = xr.open_dataset("data/era5_sst/ocean_temperature.nc")

# Inspecionar o conjunto de dados
dataset
print(dataset.attrs)        # attrs: metadados sobre o conjunto de dados, ex.: título, fonte e história.
print(dataset.dims)         # dims: lista nomes e tamanhos de dimensão.
print(dataset.variables)    # variables: dicionário de variáveis do conjunto de dados, incluindo dados e metadados.
print(dataset.data_vars)    # data_vars: são as principais variáveis científicas (como sst).
print(dataset.coords)       # coords: são variáveis de coordenadas utilizadas para indexação (tais como tempo e latitude).
print(dataset["sst"])       # sst: variável de temperatura da superfície do mar. valid_time, latitude, e longitude.

# Indexação e fatiamento
# Seleciona os dados de temperatura da superfície do mar para uma data específica.
dataset["sst"]["valid_time"].sel(valid_time="2025-01-01T00:00:00")  # Indexar por rótulo com `sel`
dataset["sst"]["valid_time"].isel(valid_time=0)                     # Indexar por posição inteira com `isel`
dataset["sst"].sel(valid_time="2025-01-01T00:00:00").isel(latitude=0, longitude=0)