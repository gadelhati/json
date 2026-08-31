# _JSON_

![PostgreSQL](https://img.shields.io/badge/PostgreSQL-17.5-blue?logo=postgresql)
![Python](https://img.shields.io/badge/Python-3.13.5-blue?logo=python)
![FastAPI](https://img.shields.io/badge/FastAPI-0.115.13-009688?logo=fastapi)

## install
```
# create virtual environment
python -m venv .venv

# activate virtual environment
.venv/Scripts/activate

# udpate pip
python.exe -m pip install --upgrade pip

# install dependencies
pip install --upgrade -r requirements.txt

# run application
uvicorn src.app:app --reload

pip install --proxy http://user:password@proxy.fqdn:6060 -r requirements.txt
git config --global http.proxy http://user:password@proxy.fqdn:6060
```

## Roadmap
- [x] Upload .json
- [x] Crud .json
- [x] Donwload .json
- [x] Upload .geojson
- [x] Crud .geojson
- [x] Donwload .geojson
- [x] Upload .tiff
- [ ] Crud .tiff
- [ ] Donwload .tiff
- [ ] Dataset > DataArray
- [ ] NetCDF(Network Common Data Form) > xarray > Zarr
- [ ] Chunking - Divisão dos dados multidimensionais em blocos menores.
- [ ] Dask > Object Storage

---

- [ ] NumPy
- [ ] dados multidimensionais
- [ ] Xarray DataArray
- [ ] Xarray Dataset
- [ ] NetCDF
- [ ] Dask
- [ ] Zarr