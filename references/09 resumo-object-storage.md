# Resumo: Object Storage e Organização de Dados na Nuvem (Cloud-Native Geoscience Course)

**Fonte:** [noc-oi.github.io/cloud-native-geoscience-course/09-object_store.html](https://noc-oi.github.io/cloud-native-geoscience-course/09-object_store.html)
Capítulo 9 do curso "Cloud-Native Geoscience Data Workflows".

## Objetivo do capítulo

Explicar o que é object storage e como difere do armazenamento em sistema de arquivos tradicional, por que é adequado ao compartilhamento de dados em larga escala e à ciência cloud-native, como suporta acesso seguro, concorrente e paralelo, e como acessar object storage na nuvem (e soluções self-hosted como o MinIO) a partir do Python.

## O que é object storage?

Object storage armazena dados como **objetos** em um espaço de endereçamento plano, geralmente dentro de **buckets**. Cada objeto contém dados binários e metadados (como tipo de conteúdo ou tags personalizadas) e é identificado por uma chave única dentro do bucket, em vez de um caminho em uma árvore de diretórios aninhada.

Diferente de sistemas tradicionais:

- **Armazenamento em arquivos** (sistemas de arquivos POSIX) organiza dados em diretórios e arquivos.
- **Armazenamento em blocos** apresenta blocos de tamanho fixo a um sistema operacional; geralmente é a base de sistemas de arquivos, discos virtuais e bancos de dados, em vez de ser acessado diretamente pelos usuários.

O object storage é projetado para armazenar grandes coleções de objetos independentes, acessados via APIs como HTTP ou S3. Essa arquitetura permite escalar através de muitos discos e nós, com alta durabilidade.

### Object storage vs. servidores tradicionais

Fluxos de trabalho científicos tradicionais costumam armazenar dados em sistemas de arquivos locais ou em rede: dados ficam em diretórios de um servidor ou pequeno cluster, o acesso é feito via SSH, NFS ou discos montados, e a capacidade de armazenamento e a largura de banda dependem do hardware e da rede subjacentes.

O object storage adota uma abordagem diferente:

- Dentro de uma implantação, objetos e fragmentos redundantes podem ser distribuídos por muitos discos, nós e zonas de disponibilidade; replicação entre regiões ou data centers separados também pode ser configurada para recuperação de desastres, dependendo do provedor.
- As aplicações acessam os dados por meio de APIs padrão, como Amazon S3, Google Cloud Storage (GCS) ou Azure Blob Storage.
- Os sistemas de armazenamento podem crescer incrementalmente, adicionando novos nós em vez de substituir hardware existente.

Tanto o armazenamento em arquivos quanto o em objetos dependem, em última instância, de capacidade finita de hardware e rede — mas o object storage distribuído facilita expandir esses limites, agrupando muitos nós e adicionando capacidade incrementalmente.

Para datasets científicos, isso torna prático armazenar milhões de objetos independentes, como arquivos NetCDF, tiles de imagem ou chunks de Zarr. Como cada objeto pode ser acessado independentemente, aplicações rodando em sistemas HPC, plataformas de nuvem ou infraestrutura local podem processar dados em paralelo enquanto acessam o mesmo dataset compartilhado.

## Vantagens do object storage

### Compartilhamento e durabilidade

O object storage é bem adequado para compartilhamento e preservação de longo prazo, oferecendo:

- Acesso global por URLs ou endpoints de API.
- Controle de acesso granular via políticas de bucket, listas de controle de acesso (ACLs), gestão de identidade ou URLs assinadas.
- Alta durabilidade via replicação ou codificação por eliminação (*erasure coding*) entre múltiplos discos e nós.
- Suporte a metadados por objeto, versionamento e buckets públicos ou privados.

### Segurança e controle de acesso

Object stores oferecem várias camadas de segurança:

- **Autenticação**: verifica a identidade de usuários ou serviços por meio de chaves de acesso, tokens OAuth ou identidades de serviço.
- **Autorização**: controla quem pode ler, escrever, listar ou gerenciar objetos, usando políticas, papéis (roles) e ACLs.
- **Criptografia**: protege dados em trânsito e em repouso; alguns sistemas também suportam criptografia do lado do cliente.

### Acesso paralelo e concorrente

Cada objeto em um object store pode ser acessado independentemente. Como resultado:

- Vários clientes podem ler e escrever objetos diferentes simultaneamente.
- Grandes datasets compostos por muitos objetos (como chunks de Zarr) podem ser processados em paralelo.
- As requisições são distribuídas entre muitos servidores e discos, aumentando a taxa de transferência agregada.

Frameworks como Dask, Spark e Apache Beam aproveitam esse modelo, atribuindo objetos ou chunks diferentes a workers diferentes — uma das razões pelas quais formatos cloud-native como o Zarr costumam ser combinados com object storage.

### Custo e classes de armazenamento

Provedores de nuvem geralmente oferecem múltiplas classes de armazenamento para diferentes padrões de acesso:

- **Acesso frequente**: maior desempenho para dados acessados regularmente.
- **Acesso infrequente**: menor custo de armazenamento, com taxas de recuperação mais altas.
- **Arquivo (armazenamento frio)**: menor custo de armazenamento, mas maior latência e taxas de recuperação.

Escolher a classe de armazenamento adequada ajuda a equilibrar custo e desempenho conforme a frequência de uso dos dados.

### Trade-offs de implantação

Há várias formas de implantar object storage:

- **Armazenamento de arquivos tradicional ou compartilhado**: pode oferecer acesso muito rápido quando próximo à computação e geralmente não tem cobranças de transferência de dados medidas, mas capacidade, compartilhamento remoto e resiliência dependem da infraestrutura local.
- **Object storage em nuvem**: oferece escalonamento gerenciado e tipicamente alta durabilidade, mas o desempenho depende da localização de rede e dos padrões de acesso, e podem se aplicar cobranças de requisição, recuperação e transferência de dados.
- **Object storage self-hosted**: oferece acesso estilo S3, controle local e potencialmente acesso rápido a partir de computação on-premise, sem taxas de transferência de dados na nuvem, mas redundância, backups, monitoramento e manutenção de hardware permanecem sob responsabilidade da instituição.

A melhor escolha depende de fatores como tamanho do dataset, padrões de acesso, proximidade da computação, desempenho necessário, requisitos de durabilidade e recuperação de desastres, largura de banda de rede, cobranças de transferência de dados, expertise operacional e orçamento. Para grandes arquivos científicos, a pergunta-chave não é apenas "o que é mais barato por terabyte?", mas também "o que é mais barato e seguro ao longo de toda a vida útil dos dados?".

Todas essas vantagens tornam o object storage adequado a fluxos de trabalho de dados científicos, especialmente combinado com formatos fragmentados como o Zarr — a capacidade de armazenar muitos objetos independentes, acessá-los em paralelo e gerenciá-los via APIs permite construir sistemas de dados escaláveis, reprodutíveis e compartilháveis.

## Acessando object storage na nuvem a partir do Python

Object stores comuns incluem AWS S3, Google Cloud Storage (GCS), Azure Blob Storage e serviços compatíveis com S3, como Cloudflare e JASMIN. Bibliotecas Python comuns:

- **`boto3`** — para AWS S3 e serviços compatíveis com S3.
- **`fsspec` / `s3fs`** — para abrir sistemas de arquivos remotos a partir do Python e do xarray.
- **`gcsfs`** ou bibliotecas específicas do provedor — para Google Cloud Storage.
- **`azure-storage-blob`** — para Azure Blob.

A lição foca em acesso estilo S3, por ser amplamente suportado e funcionar bem com Zarr e xarray — o mesmo tipo usado pelo JASMIN e outras plataformas HPC/nuvem.

### Listando objetos

Exemplo de listagem de objetos em um bucket público (bucket do satélite GOES-18 da NOAA), usando `boto3` sem credenciais:

```python
import boto3
from botocore import UNSIGNED
from botocore.config import Config

s3 = boto3.client("s3", config=Config(signature_version=UNSIGNED))

response = s3.list_objects_v2(
    Bucket="noaa-goes18",
    Prefix="ABI-L2-CMIPF/",
    MaxKeys=10,
)
for obj in response.get("Contents", []):
    print(obj["Key"])
```

Para acessar um bucket protegido (ex.: o bucket do curso, hospedado no JASMIN), é necessário fornecer credenciais e o `endpoint_url` do serviço compatível com S3:

```python
import boto3

s3 = boto3.client(
    "s3",
    endpoint_url="https://atlantis-vis-o.s3-ext.jc.rl.ac.uk",
    aws_access_key_id="your-access-key",
    aws_secret_access_key="your-secret-key",
)

bucket_name = "cloud-native-geoscience-course"
response = s3.list_objects_v2(Bucket=bucket_name, MaxKeys=10)
for obj in response.get("Contents", []):
    print(obj["Key"], obj["Size"])
```

> **Política de bucket**: o bucket do curso permite leitura pública dos objetos (então arquivos podem ser abertos sem credenciais AWS se o caminho já for conhecido), mas fornece credenciais somente-leitura para permitir a listagem/descoberta do conteúdo do bucket sem permitir modificações. Isso é feito com uma política JSON que concede `s3:GetObject` e `s3:ListBucket` ao princípio `"*"` (qualquer um) para os recursos do bucket — uma forma simples e segura de compartilhar datasets com um grupo de usuários.

### Usando xarray com um bucket

Com as credenciais definidas, é possível abrir um repositório Zarr diretamente com o xarray, informando as `storage_options`:

```python
import os
import xarray as xr

storage_options = {
    "key": os.environ["AWS_ACCESS_KEY_ID"],
    "secret": os.environ["AWS_SECRET_ACCESS_KEY"],
    "client_kwargs": {"endpoint_url": "https://atlantis-vis-o.s3-ext.jc.rl.ac.uk"},
    "config_kwargs": {
        "request_checksum_calculation": "when_required",
        "response_checksum_validation": "when_required",
    },
}

ds = xr.open_zarr(
    "s3://cloud-native-geoscience-course/ocean_temperature.zarr",
    storage_options=storage_options,
)
```

Como o bucket do exemplo é público, também é possível abrir o repositório Zarr sem credenciais, usando o endpoint público diretamente:

```python
ds = xr.open_zarr("https://atlantis-vis-o.s3-ext.jc.rl.ac.uk/cloud-native-geoscience-course/ocean_temperature.zarr")
```

A listagem do conteúdo do bucket, porém, ainda exige as credenciais somente-leitura. Um ponto-chave destacado na lição: a descoberta do object storage e a análise do dataset são etapas separadas — primeiro encontra-se o repositório (store), depois ele é aberto com o xarray.

## Object storage self-hosted

Algumas instituições não podem ou não querem colocar todos os dados em uma nuvem comercial, por razões como soberania de dados, regras de licitação/compras, requisitos de segurança local, limitações de largura de banda de rede, ou o desejo de manter datasets muito grandes próximos à computação on-premise.

Nesses casos, o object storage self-hosted pode ser uma boa opção: oferece a API estilo S3 que as ferramentas científicas modernas esperam, mantendo os dados dentro da própria infraestrutura da instituição — útil para universidades, institutos de pesquisa e órgãos governamentais que já operam seus próprios servidores, armazenamento e clusters.

### Infraestrutura local necessária

Um object store pronto para produção é mais do que "apenas um servidor com um disco". Para uma implantação rápida e confiável, as instituições geralmente precisam de:

- Múltiplos nós de armazenamento, não apenas uma máquina.
- Rede rápida, idealmente 10/25/100 GbE, dependendo da escala.
- Discos redundantes, tipicamente SSD ou NVMe para maior throughput, ou camadas de HDD cuidadosamente planejadas para dados mais frios.
- Memória e CPU suficientes para suportar codificação por eliminação, gerenciamento de metadados e muitas requisições concorrentes.
- Sistemas separados de backup e monitoramento.
- Energia estável, refrigeração e segurança física.
- Um plano para gestão de identidade, controle de acesso e certificados.

### Implantação mínima do MinIO com Docker Compose

A lição mostra, como demonstração (sem exigir execução em aula), como implantar um serviço compatível com S3 self-hosted (**MinIO**) dentro da infraestrutura de uma instituição, usando um `docker-compose.yml` com a imagem `minio/minio:latest`, expondo a porta 9000 (API S3) e 9001 (console web), definindo usuário/senha root via variáveis de ambiente e montando um volume `/data:/data`.

Após subir o contêiner (`docker compose up -d`), é possível acessar o console web, fazer login, criar um bucket e enviar um arquivo de teste. A partir daí, ferramentas S3 padrão (AWS CLI, `boto3`, cliente `mc` do MinIO) podem ser usadas apontando para o endpoint do MinIO (`http://localhost:9000`), como se fosse um object store na nuvem.

## Organizando dados em buckets e objetos

Seja usando object storage na nuvem ou self-hosted, é necessário um esquema de organização sensato. Padrões típicos incluem:

- **Um bucket por projeto ou produto** (ex.: `era5-reanalysis`, `spotter-archive`, `ifs-ens-forecast`).
- **Prefixos hierárquicos nas chaves dos objetos**, representando uma estrutura lógica, por exemplo:
  - `variable/time/region/chunk.zarr`
  - `year/month/day/file.nc`
  - `model/experiment/member/store.zarr`

Considerações de design:

- Facilitar a listagem de todos os dados de uma dada variável ou intervalo de tempo.
- Alinhar os prefixos com consultas comuns (ex.: `model/experiment` para o CMIP6; `instrument/trajectory` para boias de deriva).
- Evitar nomenclatura excessivamente profunda ou inconsistente — object storage não exige diretórios, mas os prefixos os imitam.

Para repositórios Zarr:

- Cada repositório normalmente reside sob um único prefixo (`path/to/store.zarr`), contendo metadados JSON aninhados e objetos de chunk de dados.
- É possível criar repositórios separados para variáveis, domínios ou intervalos de tempo diferentes, dependendo do volume de dados e dos fluxos de trabalho.

### Exemplo de layout de bucket (do exercício da lição)

Para um cenário com reanálise global em grade, uma rede de trajetórias de boias de deriva (arrays irregulares/*ragged arrays*) e um sistema de previsão por ensemble (com dimensão `member`), um layout proposto seria:

- `reanalysis/<variable>/<year>/<month>/store.zarr` — para dados em grade.
- `drifters/<platform>/<trajectory>/data.zarr` — para dados irregulares (ragged).
- `ens/<model>/<run>/<member>/store.zarr` — para dados de ensemble.

## Pontos-chave (resumo final da lição)

1. Object storage armazena dados como objetos com chaves e metadados em buckets, acessados via APIs estilo HTTP/S3, em vez de sistemas de arquivos locais.
2. Object stores em nuvem (S3, GCS, Azure Blob, serviços compatíveis com S3) oferecem armazenamento durável, escalável e seguro, bem adequado a grandes datasets científicos.
3. Acesso paralelo e concorrente é natural em object storage, o que o torna adequado a formatos fragmentados e frameworks de processamento distribuído.
4. Soluções self-hosted como o MinIO oferecem APIs compatíveis com S3 e podem ser implantadas com Docker nos próprios servidores da instituição.
5. Uma organização cuidadosa de buckets e chaves é essencial para descoberta eficiente de dados e design de fluxos de trabalho na nuvem.

---
*Este é o Capítulo 9 de um curso de 16 capítulos. O próximo capítulo aborda a Conversão de Formatos Tradicionais para Zarr.*
