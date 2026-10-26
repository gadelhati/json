# Resumo: Estudos de Caso (Cloud-Native Geoscience Course)

**Fonte:** [noc-oi.github.io/cloud-native-geoscience-course/11-case-studies.html](https://noc-oi.github.io/cloud-native-geoscience-course/11-case-studies.html)
Capítulo 11 do curso "Cloud-Native Geoscience Data Workflows".

## Objetivo do capítulo

Diferente dos capítulos técnicos anteriores, este é um capítulo de **sessão aberta com palestrantes convidados**, voltado a ouvir experiências reais de profissionais que aplicam fluxos de trabalho de dados cloud-native, entender como diferentes organizações abordam conversão de dados, catalogação, versionamento e visualização, e refletir sobre como esses exemplos informam decisões arquiteturais e de boas práticas nos projetos dos próprios participantes.

## Formato da sessão

Nesta sessão aberta, palestrantes convidados apresentam brevemente suas experiências (cerca de 10–12 minutos cada), cobrindo:

- Onde trabalham e com quais tipos de dados e aplicações atuam.
- Como estão convertendo e organizando dados (NetCDF → Zarr, Zarr virtual, STAC, GeoZarr, Icechunk, etc.).
- As principais aplicações, usuários e restrições de desempenho para os quais projetam suas soluções.
- Decisões arquiteturais-chave, trade-offs e suas implicações (governança, custo, reprodutibilidade, operação).

Após cada palestra, há uma breve sessão de perguntas e respostas, seguida de uma discussão conjunta ao final da sessão.

## Pontos-chave (resumo final da lição)

1. Estudos de caso do mundo real mostram que arquiteturas cloud-native variam conforme a missão, as necessidades dos usuários, a escala e as restrições operacionais de cada organização.
2. Equipes bem-sucedidas fazem trade-offs explícitos entre desempenho, custo, governança, reprodutibilidade e manutenibilidade.
3. Blocos de construção comuns incluem Zarr (físico ou virtual), STAC para descoberta, e abordagens de versionamento para atualizações controladas.
4. Decisões arquiteturais devem ser guiadas por cargas de trabalho concretas e padrões de acesso dos usuários, não apenas pela popularidade das ferramentas.
5. O compartilhamento de lições de implementação entre equipes ajuda a evitar erros repetidos e acelera a adoção de fluxos de trabalho robustos.

---
*Este é o Capítulo 11 de um curso de 16 capítulos. O próximo capítulo aborda Versionamento de Dados com Icechunk.*
