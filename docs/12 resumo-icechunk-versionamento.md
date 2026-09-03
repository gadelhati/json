# Resumo: Versionamento de Dados com Icechunk (Cloud-Native Geoscience Course)

**Fonte:** [noc-oi.github.io/cloud-native-geoscience-course/12-icechunk.html](https://noc-oi.github.io/cloud-native-geoscience-course/12-icechunk.html)
Capítulo 12 do curso "Cloud-Native Geoscience Data Workflows".

## Objetivo do capítulo

Explicar quais problemas surgem ao usar Zarr puro para datasets compartilhados e em evolução, como o Icechunk adiciona segurança, consistência e reprodutibilidade sobre o Zarr, como usar transações para atualizar dados atomicamente (evitando escritas parciais), e como referenciar e reabrir versões específicas dos dados para análises reprodutíveis.

## Por que o versionamento de dados importa

O Zarr é um formato robusto para acesso a dados em nuvem e em paralelo, mas por si só não oferece transações, histórico de versões, nem uma forma nativa de se recuperar de erros. Isso pode ser um problema para datasets científicos compartilhados: se várias pessoas atualizam os dados, leitores podem ver alterações incompletas, sobrescritas acidentais podem ser difíceis de reverter, e análises podem se tornar difíceis de reproduzir depois.

O **[Icechunk](https://icechunk.io/en/stable/)** adiciona controle de versão sobre o Zarr. Ele permite gerenciar dados em um repositório com transações, snapshots, branches (ramos) e tags, possibilitando atualizar dados atomicamente, recuperar-se de erros e referenciar versões exatas em análises futuras.

## Conceitos do Icechunk

O Icechunk envolve repositórios Zarr em "repositórios" que rastreiam mudanças ao longo do tempo, de forma semelhante ao Git rastreando mudanças em código. Os principais conceitos:

- **Repository (repositório)**: o objeto de nível superior que gerencia uma hierarquia Zarr mais seu histórico de versões.
- **Transaction (transação)**: uma sessão de escrita atômica onde múltiplas atualizações acontecem juntas — ou todas têm sucesso, ou nenhuma é aplicada.
- **Snapshot**: uma versão imutável dos dados após a conclusão de uma transação.
- **Branch (ramo)**: uma linha de desenvolvimento nomeada, como `main` ou `dev`.
- **Tag**: um rótulo legível por humanos apontando para um snapshot específico, útil para referências reprodutíveis.

A ideia central é simples: as escritas acontecem em transações, os commits criam snapshots, e os leitores abrem sessões somente-leitura que sempre veem uma versão completa e consistente do dataset.

### Zarr puro vs. Icechunk — comparação

A lição demonstra que, se você tentar ler um repositório Zarr puro enquanto ele está sendo atualizado, pode ver uma mistura de dados antigos e novos. Já ao tentar ler um repositório Icechunk durante uma atualização, você verá ou o snapshot antigo, ou o novo — nunca uma mistura.

Exemplo de leitura de um repositório Icechunk (somente leitura, branch `main`):

```python
import icechunk as ic

storage = ic.s3_storage(
    bucket="icechunk-demo",
    prefix="icechunk",
    endpoint_url="https://atlantis-vis-o.s3-ext.jc.rl.ac.uk",
    anonymous=True,
    force_path_style=True,
)

ic_repo = ic.Repository.open(storage)
session = ic_repo.readonly_session("main")
store = session.store

import zarr
root = zarr.open_group(store=store, mode='r')
arr = root['image']
img_data = arr[:]
```

Isso mostra que o Icechunk oferece uma forma segura, consistente e reprodutível de gerenciar datasets Zarr em evolução, adequada a fluxos de trabalho científicos colaborativos.

### Mapeando conceitos do Git para o Icechunk

Conceitos familiares do Git mapeiam naturalmente para o Icechunk: repositório Git → repositório Icechunk; commit Git → snapshot Icechunk; branch Git → branch Icechunk; tag Git → tag Icechunk. Esses conceitos facilitam rastrear mudanças, experimentar com segurança e entender como os dados evoluem. O recurso de "viagem no tempo" do Icechunk permite acessar snapshots anteriores, tornando as análises reprodutíveis ao garantir que a versão exata do dataset possa sempre ser revisitada.

## Fluxo básico de trabalho com Icechunk

Um fluxo comum:

1. Configurar o acesso ao object store.
2. Criar ou abrir um repositório Icechunk nesse object store.
3. Iniciar uma sessão gravável em um branch (ex.: `main`).
4. Adicionar dados ao repositório, escrevendo um dataset diretamente ou criando uma camada virtual sobre um repositório Zarr existente.
5. Fazer o commit da sessão para criar um snapshot.
6. Reabrir o repositório em modo somente-leitura para análise.

### Etapa 1 — Conectar ao object store

```python
import os
import xarray as xr
import icechunk as ic

os.environ["AWS_ACCESS_KEY_ID"] = "your-access-key"
os.environ["AWS_SECRET_ACCESS_KEY"] = "your-secret-key"

storage_options = {
    "key": os.environ["AWS_ACCESS_KEY_ID"],
    "secret": os.environ["AWS_SECRET_ACCESS_KEY"],
    "client_kwargs": {"endpoint_url": "https://atlantis-vis-o.s3-ext.jc.rl.ac.uk"},
    "config_kwargs": {
        "request_checksum_calculation": "when_required",
        "response_checksum_validation": "when_required",
    },
}
```

### Etapa 2 — Abrir o repositório Zarr local

```python
ds = xr.open_zarr(f"{base_path}data/era5_sst/ocean_temperature.zarr")
```

### Etapa 3 — Criar o repositório Icechunk

```python
storage = ic.s3_storage(
    bucket="cloud-native-geoscience-course",
    prefix="icechunk-repo",
    endpoint_url=storage_options["client_kwargs"]["endpoint_url"],
    access_key_id=storage_options["key"],
    secret_access_key=storage_options["secret"],
    region="us-east-1",
    force_path_style=True,
    checksum_algorithm=None,
)

# Necessário quando o object store não suporta atualizações condicionais (ex.: JASMIN)
storage_settings = ic.StorageSettings(
    unsafe_use_conditional_update=False,
    unsafe_use_conditional_create=False,
)

repo_config = ic.RepositoryConfig(storage=storage_settings)
repo = ic.Repository.open_or_create(storage, config=repo_config)
```

> Ao usar object stores que não suportam atualizações condicionais (como o JASMIN), é preciso desabilitar as verificações de segurança correspondentes no Icechunk. Isso é opcional em stores que as suportam nativamente, como o AWS S3.

Escrever o dataset no repositório e fazer commit:

```python
from icechunk.xarray import to_icechunk

session = repo.writable_session("main")
to_icechunk(ds, session)

snapshot = session.commit("Initial import of local Zarr dataset")
```

Após o commit, o dataset fica armazenado como um repositório Icechunk no object store. Mudanças futuras podem ser feitas como novos snapshots, sem modificar as versões anteriores.

### Etapa 4 — Ler a partir do branch `main`

```python
ro_session = repo.readonly_session("main")
ds_main = xr.open_zarr(ro_session.store, consolidated=False)
```

Abrir uma sessão somente-leitura no branch `main` fornece um snapshot consistente do dataset, garantindo que as análises sempre usem uma versão bem definida dos dados.

## Fazendo uma atualização atômica

Transações do Icechunk permitem fazer múltiplas atualizações a um dataset de forma atômica: ou todas as mudanças são aplicadas juntas, ou nenhuma é aplicada. Isso é importante para manter a consistência do dataset, especialmente quando várias variáveis/passos de tempo são atualizados simultaneamente ou quando múltiplos usuários acessam os dados.

```python
import zarr
import numpy as np

with repo.transaction("main", message="Update temperature values") as store:
    root = zarr.open_group(store)
    ny, nx = root["sst"].shape[1:]

    root["sst"][0, :, :] = np.random.rand(ny, nx).astype(np.float32)
    root["sst"][1, :, :] = np.random.rand(ny, nx).astype(np.float32)
```

Nesse exemplo, uma transação no branch `main` atualiza dois passos de tempo da variável `sst` com valores aleatórios. A transação garante que ambas as atualizações sejam aplicadas juntas — se qualquer parte falhar, nenhuma mudança é aplicada, preservando a integridade do dataset.

Com Zarr puro, um leitor pode ver uma mistura de valores antigos e novos se acessar o dataset durante a atualização. Com o Icechunk, os leitores veem o snapshot antigo ou o novo, nunca uma mistura — garantindo que as análises sejam baseadas em dados consistentes.

## Recuperando-se de erros

Uma grande vantagem do Icechunk é que erros são reversíveis. Se uma atualização ruim for commitada, é possível voltar a um snapshot anterior e restaurar o branch.

Listar o histórico de snapshots de um branch:

```python
history = list(repo.ancestry(branch="main"))
for i, snap in enumerate(history):
    print(i, snap.id, snap.message)
```

Redefinir o branch para o snapshot anterior, desfazendo efetivamente a atualização ruim:

```python
history = list(repo.ancestry(branch="main"))
prev_snapshot = history[-2].id
repo.reset_branch("main", prev_snapshot)
```

Depois, basta reabrir o dataset para confirmar que os dados originais retornaram. Isso é muito mais seguro do que sobrescrever um repositório Zarr puro, onde a recuperação normalmente depende de backups externos ou cópias manuais.

## Branches e reprodutibilidade

Branches e tags são úteis quando um dataset evolui, mas é preciso preservar uma versão estável para análise ou reprodução. Um branch como `main` pode continuar mudando, enquanto uma tag fornece um ponto de referência fixo para uma publicação, relatório ou execução operacional.

```python
# Obter o snapshot atual do branch main
snapshot = repo.lookup_branch("main")

# Criar uma tag apontando para esse snapshot
repo.create_tag("v1.0.0", snapshot)

# Abrir o dataset usando a tag
session = repo.readonly_session(tag="v1.0.0")
ds = xr.open_zarr(session.store, consolidated=False)

# Exemplo de análise
mean_sst = ds.sst.mean(dim=("latitude", "longitude")).compute()
```

Isso facilita dizer exatamente qual versão dos dados foi usada, e reabrir essa mesma versão posteriormente para verificação ou reexecuções. O fluxo de trabalho do Icechunk (branches, commits para snapshots, tags para versões importantes) é análogo ao fluxo de trabalho do Git.

## Exercícios propostos na lição (resumo do raciocínio)

- **Mapear conceitos do Git para o Icechunk**: relacionar repositório/commit/branch/tag do Git aos equivalentes do Icechunk, e discutir como a "viagem no tempo" apoia a reprodutibilidade.
- **Abrir o dataset `ocean_temperature.zarr` e adicioná-lo ao Icechunk**: abrir o repositório Zarr local, criar um repositório Icechunk no object store, importar o dataset, reabri-lo a partir do branch `main` e comparar com o Zarr local — o conteúdo é o mesmo, mas a versão do Icechunk passa a ser versionada.
- **Atualização atômica de uma variável em dois passos de tempo diferentes**: abrir o dataset do branch `main`, iniciar uma transação, atualizar pelo menos dois passos de tempo juntos (ex.: multiplicando por um fator), e confirmar que uma leitura posterior mostra a versão antiga ou a nova, nunca uma mistura.
- **Recuperar-se de uma atualização ruim**: fazer uma atualização boa e commitá-la, depois fazer uma atualização claramente ruim e commitá-la, inspecionar o dataset para confirmar os valores ruins, encontrar o snapshot anterior, redefinir o branch e reabrir o dataset para confirmar a recuperação. Em Zarr puro, essa recuperação exigiria backups externos ou cópias manuais.
- **Marcar (tag) uma versão reprodutível**: criar uma tag para a última versão do branch `main` a ser tratada como um "release", abrir o dataset usando essa tag e rodar uma pequena análise (ex.: média espacial); depois atualizar o branch `main` com um novo commit e repetir a mesma análise usando o branch e a tag, comparando os resultados — eles devem diferir, demonstrando que uma tag oferece uma referência estável para análise reprodutível, enquanto depender da "versão mais recente" pode gerar inconsistências.

## Pontos-chave (resumo final da lição)

1. O Zarr puro não possui transações, histórico ou recuperação embutidos.
2. O Icechunk adiciona repositórios, transações, snapshots, branches e tags sobre o Zarr.
3. Transações tornam atômicas as atualizações que envolvem múltiplas variáveis.
4. Branches e tags viabilizam análises reprodutíveis.
5. O histórico de versões facilita muito a recuperação de erros.

---
*Este é o Capítulo 12 de um curso de 16 capítulos. O próximo capítulo aborda Zarr Virtual com VirtualiZarr.*
