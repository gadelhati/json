# Arq-Cloud

Python em Arquiteturas Cloud-Native para dados científicos n-dimensionais utilizados em  com Oceanografia Operacional, Clima e Meteorologia em Escala de Múltiplos Terabytes

- Migrar dados de formatos NetCDF e GRIB, para formatos cloud-native Zarr e VirtualiZarr, permitindo acesso eficiente e escalável a dados em escala de múltiplos terabytes
- Armazenamento em object storage;
- Conversão de dados;
- Processamento paralelo utilizando ferramentas como Dask.

## Objetivo

Este pré-curso foi pensado como uma preparação prática para o curso de tratamento de dados meteoceanográficos. O foco não é aprender todas as bibliotecas antecipadamente, mas construir a base necessária para acompanhar as aulas com mais facilidade.

### Prioridades

1. NumPy
2. Pandas
3. Dados multidimensionais
4. Xarray: abertura, fatiamento, plotagem e processamento de dados NetCDF
5. Dask e chunking
6. Zarr
7. Noções de dados geoespaciais e visualização

> **Estratégia:** entender os conceitos e executar pequenos exercícios. Não é necessário decorar APIs.

---

# 1. Preparação do ambiente

## Objetivo

Garantir que o ambiente Python esteja funcionando e reconhecer as principais bibliotecas do curso.

### Exercício

Crie/ative seu ambiente virtual e teste:

```python
import numpy as np
import pandas as pd
import xarray as xr
import dask
import matplotlib
import netCDF4
import zarr

print("NumPy:", np.__version__)
print("Pandas:", pd.__version__)
print("Xarray:", xr.__version__)
print("Dask:", dask.__version__)
print("Matplotlib:", matplotlib.__version__)
print("NetCDF4:", netCDF4.__version__)
print("Zarr:", zarr.__version__)
```

### Checklist

- [x] Ambiente Python funcionando
- [x] Imports funcionando
- [x] Versões conferidas

---

# 2. NumPy — arrays e dados científicos

## Objetivo

Revisar a estrutura que serve de base para boa parte do processamento científico em Python.

### Estudar

- `ndarray`
- `shape`
- `dtype`
- `ndim`
- índices e slicing
- operações vetorizadas
- `axis`
- broadcasting
- valores ausentes/NaN
- agregações

### Exercício

Crie uma matriz representando temperatura em diferentes pontos:

```python
import numpy as np

temperatura = np.array([
    [24.1, 24.5, 25.0],
    [23.8, 24.2, 24.9],
    [23.5, 24.0, 24.6]
])

print(temperatura)
print("shape:", temperatura.shape)
print("dimensões:", temperatura.ndim)
print("tipo:", temperatura.dtype)
```

Depois calcule:

```python
temperatura.mean()
temperatura.min()
temperatura.max()
```

### Perguntas para responder

1. O que representa cada eixo?
2. O que significa `shape == (3, 3)`?
3. Qual a diferença entre `axis=0` e `axis=1`?

### Checklist

- [ ] Entendo `shape`
- [ ] Entendo `axis`
- [ ] Sei fazer slicing
- [ ] Sei calcular estatísticas
- [ ] Entendo operações vetorizadas

---

# 3. Pandas — séries temporais

## Objetivo

Revisar o tratamento de dados tabulares e temporais.

### Estudar

- `Series`
- `DataFrame`
- `datetime`
- índices
- seleção
- valores ausentes
- `groupby`
- `resample`

### Exercício

Crie uma pequena série temporal de temperatura:

```python
import pandas as pd
import numpy as np

datas = pd.date_range(
    "2026-01-01",
    periods=72,
    freq="h"
)

df = pd.DataFrame({
    "temperatura": 24 + np.random.randn(72),
    "umidade": 75 + np.random.randn(72) * 3,
    "vento": 10 + np.random.randn(72) * 2
}, index=datas)

print(df.head())
print(df.info())
```

### Prática

Calcule:

```python
df["temperatura"].mean()
df["temperatura"].max()
df["temperatura"].min()
```

Depois faça uma média diária:

```python
df.resample("D").mean()
```

### Perguntas

1. Por que `datetime` é importante em dados meteorológicos?
2. O que `resample()` permite fazer?
3. Qual a diferença entre uma série temporal e uma tabela comum?

### Checklist

- [ ] Sei trabalhar com `DatetimeIndex`
- [ ] Sei selecionar colunas
- [ ] Sei calcular estatísticas
- [ ] Entendo `resample()`

---

# 4. Do DataFrame para dados multidimensionais

## Objetivo

Entender a principal mudança conceitual antes de estudar xarray.

Imagine uma temperatura medida em:

- 10 horários
- 5 latitudes
- 8 longitudes

Isso produz uma estrutura:

```text
tempo × latitude × longitude
```

Em NumPy:

```python
dados.shape
# (10, 5, 8)
```

O problema é que o array sozinho não sabe necessariamente:

- qual dimensão é tempo;
- quais são as latitudes;
- quais são as longitudes;
- qual unidade representa a temperatura.

É aqui que o **xarray** entra.

### Checklist

- [ ] Entendo dados 1D
- [ ] Entendo dados 2D
- [ ] Entendo dados 3D
- [ ] Entendo o conceito de dimensão
- [ ] Entendo coordenadas

---

# 5. Xarray — DataArray

## Objetivo

Aprender o conceito central de dados científicos multidimensionais.

### Criando um DataArray

```python
import xarray as xr
import numpy as np

tempo = pd.date_range(
    "2026-01-01",
    periods=10,
    freq="D"
)

lat = np.linspace(-23, -20, 5)
lon = np.linspace(-45, -40, 8)

temperatura = np.random.rand(
    len(tempo),
    len(lat),
    len(lon)
) + 25

da = xr.DataArray(
    temperatura,
    dims=["time", "lat", "lon"],
    coords={
        "time": tempo,
        "lat": lat,
        "lon": lon
    },
    name="temperature"
)

print(da)
```

Observe:

```python
da.dims
da.shape
da.coords
da.values
```

### Praticar seleção

Por posição:

```python
da.isel(time=0)
```

Por coordenada:

```python
da.sel(
    lat=-21.5,
    lon=-42.0,
    method="nearest"
)
```

### Praticar redução

```python
da.mean(dim="time")
```

```python
da.max(dim="time")
```

```python
da.mean(dim=["lat", "lon"])
```

### Conceitos essenciais

- `dims`
- `coords`
- `attrs`
- `DataArray`
- `sel()`
- `isel()`
- `mean()`
- `max()`
- `min()`
- `where()`

### Checklist

- [ ] Entendo DataArray
- [ ] Entendo dimensões
- [ ] Entendo coordenadas
- [ ] Sei usar `sel()`
- [ ] Sei usar `isel()`
- [ ] Sei reduzir por dimensão

---

# 6. Xarray — Dataset

## Objetivo

Entender como representar várias variáveis relacionadas.

Exemplo:

```python
ds = xr.Dataset({
    "temperature": (
        ["time", "lat", "lon"],
        temperatura
    ),
    "salinity": (
        ["time", "lat", "lon"],
        35 + np.random.randn(
            len(tempo),
            len(lat),
            len(lon)
        ) * 0.1
    )
}, coords={
    "time": tempo,
    "lat": lat,
    "lon": lon
})

print(ds)
```

Agora temos:

```text
Dataset
├── temperature
├── salinity
├── time
├── lat
└── lon
```

### Praticar

```python
ds["temperature"]
ds["salinity"]
```

```python
ds.sel(time="2026-01-03")
```

```python
ds.mean(dim="time")
```

### Checklist

- [ ] Entendo DataArray × Dataset
- [ ] Sei acessar variáveis
- [ ] Sei selecionar coordenadas
- [ ] Sei fazer operações sobre dimensões

---

# 7. NetCDF — formato científico

## Objetivo

Entender como datasets científicos são armazenados.

### Conceito

NetCDF é muito utilizado para dados ambientais, meteorológicos e oceanográficos porque permite armazenar:

- variáveis;
- dimensões;
- coordenadas;
- atributos;
- unidades;
- metadados.

### Exercício

Salve o Dataset:

```python
ds.to_netcdf("meteo_exemplo.nc")
```

Depois abra:

```python
ds2 = xr.open_dataset("meteo_exemplo.nc")

print(ds2)
```

### Praticar

Compare:

```python
ds
ds2
```

E investigue:

```python
ds2.dims
ds2.coords
ds2.data_vars
ds2.attrs
```

### Checklist

- [ ] Sei o que é NetCDF
- [ ] Sei salvar um Dataset
- [ ] Sei abrir um NetCDF
- [ ] Entendo a relação NetCDF ↔ xarray

---

# 8. Metadados e unidades

## Objetivo

Entender por que dados científicos precisam de contexto.

Adicione atributos:

```python
ds["temperature"].attrs = {
    "long_name": "Sea surface temperature",
    "units": "degC"
}

ds["salinity"].attrs = {
    "long_name": "Sea water salinity",
    "units": "PSU"
}
```

Também adicione atributos ao Dataset:

```python
ds.attrs = {
    "title": "Exemplo de dados meteoceanográficos",
    "source": "Pré-curso"
}
```

### Pergunta importante

Por que `25` sozinho é um dado insuficiente?

Porque não sabemos se representa:

```text
25 °C
25 °F
25 PSU
25 m
25 m/s
```

Em dados científicos, **valor + coordenada + unidade + significado** são fundamentais.

---

# 9. Dask — computação lazy

## Objetivo

Entender como trabalhar com datasets grandes sem carregar tudo imediatamente na memória.

### Conceito

Com NumPy:

```text
arquivo
   ↓
memória
   ↓
cálculo
```

Com Dask:

```text
arquivo
   ↓
chunks
   ↓
grafo de tarefas
   ↓
cálculo quando necessário
```

### Exercício

Crie um array Dask:

```python
import dask.array as da

x = da.random.random(
    (10000, 10000),
    chunks=(1000, 1000)
)

print(x)
```

Observe:

```python
x.shape
x.chunks
```

Calcule:

```python
resultado = x.mean()

print(resultado)
```

Observe que o resultado ainda não foi necessariamente calculado.

Agora:

```python
resultado.compute()
```

### Checklist

- [ ] Entendo lazy computation
- [ ] Entendo chunks
- [ ] Entendo `compute()`
- [ ] Entendo por que Dask ajuda com dados grandes

---

# 10. Xarray + Dask

## Objetivo

Combinar o conhecimento principal do pré-curso.

Crie um Dataset com chunks:

```python
ds_chunked = ds.chunk({
    "time": 2,
    "lat": 2,
    "lon": 4
})

print(ds_chunked)
```

Observe:

```python
ds_chunked["temperature"].data
```

Agora faça:

```python
media = ds_chunked["temperature"].mean(dim="time")

print(media)
```

E finalmente:

```python
resultado = media.compute()

print(resultado)
```

### Conceito-chave

```text
xarray
   +
Dask
   ↓
dados multidimensionais grandes
   ↓
processamento por chunks
```

---

# 11. Zarr — visão inicial

## Objetivo

Entender por que Zarr aparece junto de xarray e Dask.

Não é necessário dominar Zarr antes do curso.

Apenas entenda:

```text
NetCDF
→ normalmente pensado como arquivo científico

Zarr
→ armazenamento chunked de arrays/datasets
→ muito adequado para processamento paralelo e object storage
```

### Exercício

Depois de trabalhar com chunks:

```python
ds_chunked.to_zarr(
    "meteo_exemplo.zarr",
    mode="w"
)
```

Abra:

```python
ds_zarr = xr.open_zarr(
    "meteo_exemplo.zarr"
)

print(ds_zarr)
```

### Checklist

- [ ] Sei por que Zarr é relevante
- [ ] Entendo a relação Zarr ↔ chunks
- [ ] Entendo a relação Zarr ↔ Dask
- [ ] Sei abrir um Zarr com xarray

---

# 12. Visualização rápida

## Objetivo

Visualizar uma variável espacial.

```python
import matplotlib.pyplot as plt

ds["temperature"].isel(time=0).plot()

plt.show()
```

Depois experimente:

```python
ds["temperature"].mean(dim="time").plot()
plt.show()
```

### Perguntas

- O que representam os eixos?
- Qual unidade está sendo exibida?
- O que acontece quando fazemos média no tempo?

---

# 13. Noções de geoespacial

## Objetivo

Preparar a ponte para Cartopy e Shapely.

Você já teve contato com GeoJSON no seu projeto. Agora relacione:

```text
latitude
longitude
   ↓
posição geográfica
   ↓
CRS / projeção
   ↓
mapa
```

Não é necessário estudar projeções profundamente antes do curso.

### Conceitos para reconhecer

- latitude
- longitude
- CRS
- projeção
- geometria
- ponto
- linha
- polígono
- Shapely
- Cartopy

---

# 14. Exercício integrador do pré-curso

## Objetivo

Juntar os conceitos sem ainda transformar isso no projeto final.

Crie um Dataset sintético contendo:

```text
time
latitude
longitude

temperature
salinity
wind_speed
```

### Etapas

1. Criar coordenadas temporais.
2. Criar coordenadas de latitude.
3. Criar coordenadas de longitude.
4. Criar três variáveis.
5. Construir um `xarray.Dataset`.
6. Adicionar unidades e metadados.
7. Salvar em NetCDF.
8. Abrir novamente com xarray.
9. Aplicar chunks.
10. Calcular uma média usando Dask.
11. Salvar em Zarr.
12. Fazer pelo menos um gráfico.

### Fluxo esperado

```text
NumPy
  ↓
dados multidimensionais
  ↓
xarray.DataArray
  ↓
xarray.Dataset
  ↓
NetCDF
  ↓
chunks
  ↓
Dask
  ↓
processamento
  ↓
Zarr
  ↓
visualização
```

---

# 15. Checklist final

Antes do início do curso, tente responder sem consultar material:

### Python científico

- [ ] O que é um ndarray?
- [ ] O que é `shape`?
- [ ] O que é `axis`?
- [ ] O que é broadcasting?

### Pandas

- [ ] O que é um DataFrame?
- [ ] Como trabalhar com datas?
- [ ] O que faz `resample()`?

### Xarray

- [ ] O que é DataArray?
- [ ] O que é Dataset?
- [ ] O que são dimensões?
- [ ] O que são coordenadas?
- [ ] Qual a diferença entre `sel()` e `isel()`?

### NetCDF

- [ ] Para que serve?
- [ ] O que são dimensões e variáveis?
- [ ] O que são atributos/metadados?

### Dask

- [ ] O que é computação lazy?
- [ ] O que são chunks?
- [ ] Para que serve `compute()`?

### Zarr

- [ ] Por que usar chunks?
- [ ] Qual a relação entre Zarr, xarray e Dask?

### Geoespacial

- [ ] O que são latitude e longitude?
- [ ] O que é CRS?
- [ ] Para que servem Cartopy e Shapely?

---

# 16. Depois do curso — mini projeto meteoceanográfico

Este projeto será feito **depois das aulas**, usando o conhecimento adquirido durante o curso.

## Tecnologias principais

- Python
- NumPy
- Pandas
- xarray
- NetCDF
- Dask
- Matplotlib
- Cartopy

Possivelmente também:

- Zarr
- S3/Object Storage
- eccodes/cfgrib, caso o curso trabalhe com GRIB
- Shapely

## Proposta inicial

Construir um pequeno pipeline de análise meteoceanográfica:

```text
dados reais
    ↓
NetCDF / GRIB
    ↓
xarray
    ↓
exploração das dimensões e metadados
    ↓
seleção temporal
    ↓
seleção espacial
    ↓
limpeza / tratamento
    ↓
Dask + chunks
    ↓
estatísticas
    ↓
visualização
    ↓
interpretação dos resultados
```

O tema específico, dataset e perguntas científicas serão definidos **ao final do curso**, com base nas técnicas efetivamente aprendidas.

---

# Estratégia de estudo

Durante o pré-curso, priorize **entender o modelo mental**, e não decorar comandos.

A sequência mais importante é:

```text
Array
  ↓
DataFrame
  ↓
Dados multidimensionais
  ↓
DataArray
  ↓
Dataset
  ↓
NetCDF
  ↓
Chunks
  ↓
Dask
  ↓
Zarr
```

Se essa sequência fizer sentido, você terá uma base muito boa para acompanhar o curso.

## Regra principal

> **Não tente aprender todas as bibliotecas da lista antes do curso.**

Bibliotecas como `icechunk`, `virtualizarr`, `topozarr`, `pystac`, `obstore`, `s3fs`, `OceanDataStore` e `dask_gateway` podem ser estudadas conforme surgirem no curso e conforme entendermos o fluxo de dados.

---

## Próxima etapa

Depois que o pré-curso estiver concluído, cada tópico poderá ser estudado de forma aprofundada, com:

1. explicação conceitual;
2. exemplos práticos;
3. exercícios;
4. desafios;
5. relação com dados meteoceanográficos;
6. análise dos erros encontrados;
7. boas práticas.

Ao final, construiremos juntos o **mini projeto meteoceanográfico com xarray + NetCDF + Dask**, utilizando dados reais.
