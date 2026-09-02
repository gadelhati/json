# Resumo: Arquitetura e Boas Práticas

**Fonte:** [Cloud-Native Geoscience Data Workflows – Capítulo 16: Architecture and Best Practices](https://noc-oi.github.io/cloud-native-geoscience-course/16-best-practices.html)

Este é o **capítulo final** do curso "Cloud-Native Geoscience Data Workflows". Em vez de introduzir uma nova ferramenta, ele é uma lição reflexiva que conecta todos os conceitos vistos anteriormente, discutindo como combiná-los em arquiteturas coerentes e quais boas práticas adotar.

## Objetivos da aula

- Refletir sobre como as diferentes ferramentas e formatos se encaixam em arquiteturas de ponta a ponta (end-to-end).
- Identificar trade-offs entre simplicidade, performance, custo e manutenibilidade.
- Discutir boas práticas para projetar workflows cloud-native com Zarr, STAC, Icechunk, Virtualizarr e GeoZarr.

## Por que arquitetura e prática importam

Ao longo do curso, foram apresentados diversos blocos de construção:

- **Formatos:** NetCDF, Zarr.
- **Metadados:** convenções CF.
- **Armazenamento de objetos** (object storage).
- **Virtualização:** Virtualizarr.
- **Versionamento:** Icechunk.
- **Catalogação:** STAC.
- **Visualização:** GeoZarr, pirâmides multiscale.

Cada peça resolve um problema específico, mas só entrega valor real quando **combinada em uma arquitetura coerente**.

Uma boa arquitetura:
- Facilita a descoberta dos dados.
- Permite acesso eficiente aos dados.
- Permite atualizações seguras.
- Possibilita visualização interativa.
- Continua compreensível e sustentável pela equipe ao longo do tempo.

**Boas práticas** são os hábitos e padrões que mantêm essas arquiteturas saudáveis com o tempo: metadados claros, chunking sensato, decisões documentadas e automação de tarefas repetitivas.

## Exercício 1 — Esboçar uma arquitetura de ponta a ponta

Proposta de exercício (individual ou em grupo) para esboçar a arquitetura de um projeto hipotético (ex.: uma reanálise global, um sistema de previsão por ensemble, ou um produto de satélite), definindo:

- Onde os dados brutos residem (formatos, armazenamento).
- Como tratar os metadados.
- Como e quando converter para Zarr ou Zarr virtual.
- Como aplicar versionamento (Icechunk) e catalogação (STAC).
- Como os usuários descobrem, analisam e visualizam os dados (ex.: GeoZarr, ferramentas de navegador).

Perguntas de discussão: onde a simplicidade foi priorizada? Onde investir em ferramentas mais complexas para performance ou governança?

## Exercício 2 — Checklist pessoal de boas práticas

Proposta de exercício para elaborar um checklist curto para projetos futuros. Exemplos sugeridos no capítulo:

- "Sempre definir metadados e vocabulários claros para novos datasets."
- "Planejar o chunking e o layout multiscale com base nos padrões de acesso esperados, não apenas em valores padrão."
- "Usar STAC para descoberta e Zarr para análise. Mantê-los sincronizados."
- "Adotar versionamento (Icechunk ou similar) para qualquer dataset atualizado regularmente."
- "Preferir virtualização (Virtualizarr, kerchunk) quando a conversão completa for impraticável."
- "Documentar decisões arquiteturais e revisitá-las periodicamente."

A sugestão é comparar o checklist com o de um colega e refiná-lo em algo realmente aplicável no dia a dia de trabalho.

## Pontos-chave (Key Points)

- Workflows cloud-native são mais fortes quando formatos, metadados, armazenamento e operações são projetados juntos, como uma única arquitetura.
- Não existe uma "pilha" única e melhor: a escolha entre Zarr físico, Zarr virtual, STAC, Icechunk e GeoZarr depende da carga de trabalho, governança e recursos disponíveis.
- Trade-offs práticos entre simplicidade, performance, custo e manutenibilidade devem ser documentados e revisitados ao longo do tempo.
- Chunking, qualidade dos metadados e descobribilidade são decisões fundamentais que afetam fortemente a usabilidade e a sustentabilidade de longo prazo.
- Um checklist de boas práticas curto e explícito ajuda as equipes a aplicar os conceitos do curso de forma consistente em projetos reais.
