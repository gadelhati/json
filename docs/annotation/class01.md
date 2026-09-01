# _Class 01SET_

[Project List](https://codimd.carpentries.org/2026-brazil)

CPU
    CORE
        PROCESS
            THRED

Posix != Object Store

Formato - 
> Autodescritivos: formato e dado juntos. Ex.: NetCDF(.fc),  e Zarr

- [CF - Climate and Forecast](https://github.com/cf-convention), padronização de _standard names_
- WMO: GRIB, BUFR
- [Parquet e GeoParquet]()
Semantica - 

Dado
Metadado: dado sobre o dado. Ex.: título, resumo, qualidade, licença.
    vocabulário controlado
Dataset


[01](https://noc-oi.github.io/cloud-native-geoscience-course/01-intro.html)
- NetCDF já é padrão estabelescido na arquitetura escolhida no CHM com CF Conventions seria o mais adequado.
- GRIB trata-se do pradrão adotado e largamente estabelescido.

zenodo: github de pesquisadores

## _Setup_

```bash
# Registra ambiente virtual de desenvolvimento para ser usado como Kernel dentro do Jupyter
mamba run -p /work/scratch-nopw2/tobfer/cloud-native-geoscience-course-env python -m ipykernel install --user --name cloud-native-geoscience-course
# Gerenciador de pacotes (alternativa ao Conda)
mamba init
# 
exec bash
```

```bash
# Jupyter launcher by clicking: File > New Launcher. Option named: ´cloud-native-geoscience-course´
# Data access:
ls /gws/ssde/j25b/atlantis_vis/cloud-native-geoscience-course/data/
```