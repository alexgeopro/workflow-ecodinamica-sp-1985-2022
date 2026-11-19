# Ferramentas Finais da Tese — scripts arcpy

Conversão dos models do ModelBuilder reunidos na toolbox
**`1_Ferramentas Finais da Tese.tbx`** para scripts Python usando `arcpy`
(ArcGIS Pro).

Cada script foi conferido tanto pelos parâmetros gravados no diagrama
original (tooltips das caixas) quanto, quando disponível, pelo script
exportado nativamente do ArcMap 10.3 (Model → Export → To Python Script).

## Ligação com a tese

Alex da Silva Sousa. *Workflow científico aplicado à modelos ambientais:
automatização das classificações ecodinâmicas e análise espaço-temporal.*
Tese (Doutorado) — Programa de Geografia Física, FFLCH-USP, 2024.
DOI: [10.11606/T.8.2024.tde-18022025-121027](https://doi.org/10.11606/T.8.2024.tde-18022025-121027)

## Pipeline

A toolbox reúne vários models. Os três primeiros
calculam o Grau de Dissecação do Relevo; o quarto combina esse resultado
com as demais camadas ambientais da tese (solos, uso e cobertura da
terra, clima) para gerar o mapa de Fragilidade Ambiental da paisagem
(metodologia de ecodinâmica de Jean Tricart, com os pesos de Ross); o
quinto gera o mapa de Vulnerabilidade Ambiental (pesos de Crepani) como
a média de cinco temas.

| # | Model (toolbox) | Script(s) | O que faz |
|---|---|---|---|
| 1 | `1_Entalhamento do Vale_FINAL_Geografica` | `scripts/arcgis_pro/1_Entalhamento do Vale_ArcPRO.py` (ArcGIS Pro), `scripts/qgis/1_Entalhamento do Vale_QGIS.py` (QGIS, software livre) e `scripts/software_livre/1_Entalhamento do Vale_SoftwareLivre.py` (Python + GDAL, sem QGIS) | Calcula a profundidade de encaixe do vale (entalhamento) a partir do DEM |
| 2 | `2_Dimensão Interfluvial Média_FINAL_Geografica` | `scripts/arcgis_pro/2_Dimensao Interfluvial_ArcPRO.py` (ArcGIS Pro), `scripts/qgis/2_Dimensao_Interfluvial_Media_QGIS.py` (QGIS, software livre) e `scripts/software_livre/2_Dimensao_Interfluvial_Media_SoftwareLivre.py` (Python + GDAL, sem QGIS) | Calcula a largura média do interflúvio a partir de um raster de subbacias (qualquer fonte, desde que já em raster) |
| 3 | `3_Grau de Dissecação` | `scripts/arcgis_pro/3_Grau de Dissecacao_ArcPRO.py` (ArcGIS Pro), `scripts/qgis/3_grau_de_dissecacao_QGIS.py` (QGIS, software livre) e `scripts/software_livre/3_grau_de_dissecacao_SoftwareLivre.py` (Python + GDAL, sem QGIS) | Combina os resultados reclassificados dos passos 1 e 2 nos índices finais de Grau de Dissecação (Fragilidade e Vulnerabilidade) |
| 4 | `4_FragilidadeAmbiental` | `scripts/arcgis_pro/4_FragilidadeAmbiental_ArcPRO.py` (ArcGIS Pro), `scripts/qgis/4_FragilidadeAmbiental_QGIS.py` (QGIS, software livre) e `scripts/software_livre/4_FragilidadeAmbiental_SoftwareLivre.py` (Python + GDAL, sem QGIS) | Soma Relevo (Grau de Dissecação) + Solos + Uso e Cobertura da Terra + Clima (WorldClim) na matriz de 4 algarismos de Fragilidade Ambiental, um raster por ano de uso da terra |
| 5 | `5_VulnerabilidadeAmbiental` | `scripts/arcgis_pro/5_VulnerabilidadeAmbiental_ArcPRO_V6_completa.py` (ArcGIS Pro), `scripts/qgis/5_VulnerabilidadeAmbiental_QGIS_V6_completa.py` (QGIS, software livre) e `scripts/software_livre/5_VulnerabilidadeAmbiental_SoftwareLivre_V6_completa.py` (Python + GDAL, sem QGIS) | Fluxo completo da Vulnerabilidade (Crepani, escala × 10): monta o Relevo (entalhamento + dimensão interfluvial + declividade do DEM), converte Geologia, Solos e Clima (vetores) em raster e tira a média (Cell Statistics, ignorando NoData) desses quatro temas com o Uso e Cobertura da Terra; três produtos, dois deles por ano de uso da terra |
| — | `Modelo Geral_Fragilidade_DissecaçãoV5` e demais models (Fragilidade com dados do INMET, Fragilidade Potencial/Emergente) | *ainda não convertidos* | Variantes e etapas posteriores dos mapas de fragilidade/vulnerabilidade ambiental |

Os 4 primeiros devem ser rodados nessa ordem (a saída de um alimenta o
próximo); o script 4 usa a saída do script 3 e, além dela, dados que vêm
de outros capítulos metodológicos da tese (pedologia, clima, uso e
cobertura da terra — ver a seção "Fragilidade Ambiental" abaixo). O
script 5 (Vulnerabilidade) não usa a saída do script 3: parte de rasters
temáticos já em escala de vulnerabilidade (ver a seção "Vulnerabilidade
Ambiental") e de uma tabela de pesos da tese ("Pesos de Fragilidade e
Vulnerabilidade", no fim desse README).

## Estrutura do repositório

- `scripts/` — os scripts convertidos, uma subpasta por programa. Escolha a
  pasta de acordo com o que você tem instalado e siga os passos 1 a 5 na
  ordem (o número no começo do nome do arquivo é o passo):
  - `scripts/arcgis_pro/` — ArcGIS Pro (`arcpy`; precisa de Spatial Analyst).
  - `scripts/qgis/` — QGIS 3.x (PyQGIS, roda também sem abrir o QGIS).
  - `scripts/software_livre/` — Python puro com GDAL/OGR, sem QGIS e sem ArcGIS.
- `modelbuilder/1_Ferramentas Finais da Tese.tbx` — a toolbox original com
  os models da tese.
- `modelbuilder/exports_arc103/` — o código Python exportado pelo próprio
  ModelBuilder (ArcMap 10.3, *Model > Export > To Python Script*) de cada
  model: é a referência contra a qual os parâmetros dos scripts foram
  conferidos. Para a Vulnerabilidade há duas, que na toolbox
  são o model **V6** e o model **V7**: `5_VulnerabilidadeAmbiental_Arc103_V6_completa.py`
  (**V6**, versão completa da tese, em que se baseiam os scripts 5) e
  `5_VulnerabilidadeAmbiental_Arc103_V7_simplificada.py` (**V7**, versão simplificada, que
  lê os quatro temas já prontos — ver a nota na seção Vulnerabilidade
  Ambiental).
  O export do passo 1 tem no nome o aviso de que sai com um erro do
  próprio exportador do ArcMap (ver a "Nota de transparência
  metodológica"): para esse model, use a toolbox ou o script de
  `scripts/arcgis_pro/`.

## As quatro versões do "Entalhamento do Vale"

Para essa ferramenta especificamente, existem quatro formas equivalentes
de rodar a mesma metodologia (Cap. 6.3 da tese), cada uma com um jeito
diferente de organizar pasta/GDB e dados de entrada:

### 1) O model original (`1_Entalhamento do Vale_FINAL_Geografica`, dentro da toolbox, ModelBuilder/ArcMap/ArcGIS Pro)

Esse é o artefato original usado na tese. Ele **não pergunta os caminhos
na hora de rodar** — os caminhos ficam gravados dentro do próprio
diagrama do model (em cada caixinha de dado). Para reutilizá-lo hoje, é
preciso:

1. Recriar, no seu computador, a mesma pasta e a mesma geodatabase que
   estavam gravadas no model original (`D:\Doutorado\Entalhamento.gdb`),
   com esse nome exato — ou abrir o model no ModelBuilder e, em cada
   caixinha de dado, clicar com o botão direito para apontar de novo
   para onde os arquivos estão hoje no seu computador.
2. Colocar dentro dessa estrutura (ou apontar o model para) o raster do
   MDT/mosaico e o shapefile/feature class do limite da área de estudo,
   com os mesmos nomes/caminhos que o model espera.
3. Rodar o model normalmente dentro do ArcMap/ArcGIS Pro (Catalog >
   Toolboxes > clique duplo no model).

Ou seja: com o model, a organização de pastas é fixa (definida pelo
diagrama) — é você quem se adapta a ela, recriando a estrutura ou
reapontando os dados.

### 2) `scripts/arcgis_pro/1_Entalhamento do Vale_ArcPRO.py` (ArcGIS Pro / arcpy)

Já vem organizado de forma automática: o script cria sozinho a pasta e a
geodatabase de trabalho, direto na unidade C:, e pergunta os dados de
entrada quando você roda — não precisa editar nada no código.

- **Pasta/GDB de trabalho (criada automaticamente):**
  `C:\alexgeopro\Entalhamento.gdb`
- **Dados de entrada (perguntados na tela ao rodar, podem estar em
  qualquer pasta):**
  - MDT / mosaico raster (ex.: `C:\dados\mosaicoRMSP.tif`)
  - shapefile/feature class da área de estudo (ex.: `C:\dados\AreaEstudo.shp`)
- **Saídas** (todas dentro da geodatabase acima): `a_` a `g_` são
  intermediárias; `h_entalhamento` é o entalhamento contínuo (metros por
  pixel) e `i_EntalhamentoRecla` é o resultado final reclassificado em 5
  classes de peso (Ross/Crepani).

### 3) `scripts/qgis/1_Entalhamento do Vale_QGIS.py` (QGIS + Python, software livre)

Mesma lógica de organização automática, adaptada para as ferramentas
livres (GeoPackage no lugar de geodatabase):

- **Pasta de trabalho (criada automaticamente):**
  `C:\alexgeopro\Entalhamento_QGIS`
- **Dentro dela:** `Entalhamento.gpkg` (camadas vetoriais intermediárias)
  e os rasters `a_` a `i_` como arquivos `.tif` soltos na mesma pasta.
- **Dados de entrada** (perguntados na tela ao rodar, podem estar em
  qualquer pasta): os mesmos dois de cima — MDT/mosaico raster e
  shapefile/feature class da área de estudo.
- **Saídas:** `h_entalhamento.tif` (entalhamento contínuo) e
  `i_EntalhamentoRecla.tif` (reclassificado em 5 classes, Ross/Crepani) —
  os mesmos dois produtos finais da versão ArcGIS Pro.

Rodar essa versão exige o QGIS instalado (com scipy e scikit-image no
Python dele — ver `Requisitos` abaixo); pode ser executada de dentro do
Console Python do QGIS, ou pelo terminal em modo "headless" (sem abrir a
janela do QGIS) — ver seção `Requisitos`.

### 4) `scripts/software_livre/1_Entalhamento do Vale_SoftwareLivre.py` (Python + GDAL/OGR, sem QGIS)

Mesma lógica de organização automática das versões acima, mas sem
NENHUMA dependência do QGIS — chama diretamente as bibliotecas
GDAL/OGR (`osgeo.gdal`/`osgeo.ogr`), que são as mesmas que o QGIS usa
por baixo dos panos, só que sem precisar do programa QGIS instalado:

- **Pasta de trabalho (criada automaticamente):**
  `C:\alexgeopro\Entalhamento_SemQGIS`
- **Dentro dela:** `Entalhamento.gpkg` (camadas vetoriais intermediárias)
  e os rasters `a_` a `i_` como arquivos `.tif` soltos na mesma pasta —
  mesma organização da versão QGIS.
- **Dados de entrada e saídas:** os mesmos da versão QGIS (item 3 acima).
- Roda com qualquer instalação comum de Python (Windows, Linux, macOS)
  que tenha os pacotes `gdal`, `numpy`, `scipy` e `scikit-image`
  instalados — o jeito mais simples é via conda:
  `conda install -c conda-forge gdal numpy scipy scikit-image`.
- Basta rodar `python "1_Entalhamento do Vale_SoftwareLivre.py"` num terminal
  comum — não precisa abrir o QGIS nem o ArcGIS Pro para nada.

## Dimensão Interfluvial Média

Três versões, mesmo padrão de organização automática do script de
entalhamento (o modelo original, dentro da toolbox, segue a mesma lógica
do "Entalhamento" — caminhos fixos gravados no diagrama, veja a seção
acima):

**Dado de entrada, em ambas as versões** (perguntado na tela ao rodar,
pode estar em qualquer pasta): um raster de subbacias (ex.:
`C:\dados\Subbacias.tif`). Por padrão, o dado usado é o das subbacias
oficiais do Estado de São Paulo (Secretaria do Meio Ambiente/CPLA, 2013,
elaborado pela FUNCATE em parceria com o Instituto Geológico — ver
`Ficha_Tecnica_Sub_bacia.pdf`), mas qualquer outra fonte de subbacias
serve, desde que já convertida para raster antes de rodar o script.

### `scripts/arcgis_pro/2_Dimensao Interfluvial_ArcPRO.py` (ArcGIS Pro)

- **Pasta/GDB de trabalho (criada automaticamente):**
  `C:\alexgeopro\DimensaoInterfluvial.gdb`
- **Saídas** (dentro da geodatabase acima): `a_` a `i_` são
  intermediárias; `j_Dimensao` é a dimensão interfluvial média contínua
  (metros) por subbacia; `l_DimensaoReclaFrag` e `l_DimensaoReclaVul` são
  os dois resultados finais reclassificados (Ross/Fragilidade e
  Crepani/Vulnerabilidade).

### `scripts/qgis/2_Dimensao_Interfluvial_Media_QGIS.py` (QGIS, software livre)

- **Pasta de trabalho (criada automaticamente):**
  `C:\alexgeopro\DimensaoInterfluvial_QGIS`, com os rasters `a_`, `d_`,
  `i_`, `j_` e `l_` como arquivos `.tif` soltos ali dentro.
- **Saídas finais:** as mesmas duas de cima — `j_Dimensao.tif`
  (contínuo) e `l_DimensaoReclaFrag.tif` / `l_DimensaoReclaVul.tif`
  (reclassificados).
- Como o raster de subbacias já traz o identificador de cada subbacia
  pixel a pixel, os passos "Raster to Polygon" e "Polygon To Line" do
  model original não são necessários — a borda de cada subbacia é
  identificada direto na matriz, comparando cada pixel aos vizinhos. Por
  esse mesmo motivo, a limpeza iterativa por Eliminate (5x no model
  original) também não é necessária aqui. Detalhes completos no
  cabeçalho do script.
- Usa a mesma constante de conversão graus→metros da tese (107015),
  sem alteração — ver a nota de transparência no cabeçalho do script.

Rodar a versão QGIS exige o QGIS instalado (com scipy e scikit-image no
Python dele — ver `Requisitos` abaixo).

### `scripts/software_livre/2_Dimensao_Interfluvial_Media_SoftwareLivre.py` (Python + GDAL, sem QGIS)

Mesma lógica da versão QGIS acima, mas sem nenhuma dependência do QGIS —
chama `gdal.Warp()` diretamente em vez do algoritmo `gdal:warpreproject`
do QGIS:

- **Pasta de trabalho (criada automaticamente):**
  `C:\alexgeopro\DimensaoInterfluvial_SemQGIS`.
- **Dados de entrada e saídas:** os mesmos da versão QGIS.
- Roda com qualquer instalação comum de Python com `gdal`, `numpy`,
  `scipy` e `scikit-image` instalados (`conda install -c conda-forge
  gdal numpy scipy scikit-image`) — basta rodar `python
  "2_Dimensao_Interfluvial_Media_SoftwareLivre.py"` num terminal comum.

## Grau de Dissecação

Combina os resultados dos dois scripts anteriores num único índice
final, por área de interesse. Três versões:

**Dado de entrada, em ambas:** os três rasters reclassificados gerados
pelos scripts 1 e 2 (o script procura sozinho nos locais padrão de cada
versão, e só pergunta o caminho na tela se não achar algum
automaticamente), e o limite vetorial da área de interesse (por padrão,
o Estado de São Paulo — mas serve qualquer área de estudo), sempre
perguntado na tela.

### Como ler o valor final: Tabelas 19, 20 e 21 da tese

O raster final é a soma da classe de Entalhamento do Vale (dezena: 10 a
50) com a classe de Dimensão Interfluvial Média (unidade: 1 a 5), então
cada pixel recebe um número de dois dígitos: **o primeiro dígito é a
linha** (Entalhamento) **e o segundo é a coluna** (Dimensão
Interfluvial) das tabelas abaixo. Por exemplo, `34` = Entalhamento de 40
a 80 m (linha) combinado com Dimensão Interfluvial de 250 a 750 m
(coluna). As colunas seguem a ordem das classes de unidade: a classe 1 é
a coluna da esquerda (dimensão interfluvial maior, relevo menos
dissecado) e a classe 5 é a da direita (dimensão menor, mais
dissecado).

Na tese, as células das Tabelas 19 e 20 são coloridas, e a Tabela 21
define o significado de cada cor (Fragilidade/Vulnerabilidade). O
esquema de cores é o mesmo nas duas tabelas:

- Verde-escuro: `11`
- Verde-claro: `12`, `21`, `22`
- Amarelo: `13`, `23`, `31`, `32`, `33`
- Laranja: `14`, `24`, `34`, `41`, `42`, `43`, `44`
- Vermelho: `15`, `25`, `35`, `45`, `51`, `52`, `53`, `54`, `55`

**Tabela 19 — Classes de Fragilidade para escalas médias e pequenas**
(adaptado de Crepani et al., 2001). Script: `b_GrauDeDissecacao_Fragilidade`.

Colunas: Densidade de Drenagem ou Dimensão Interfluvial Média (m).

| Graus de Entalhamento de Vales (m) | Fragilidade | > 3.750 (Muito Fraca) | 1.750 a 3.750 (Fraca) | 750 a 1.750 (Média) | 250 a 750 (Forte) | < 250 (Muito Forte) |
|---|---|:---:|:---:|:---:|:---:|:---:|
| < 20 | Muito Fraca | 11 | 12 | 13 | 14 | 15 |
| 20 a 40 | Fraca | 21 | 22 | 23 | 24 | 25 |
| 40 a 80 | Médio | 31 | 32 | 33 | 34 | 35 |
| 80 a 160 | Forte | 41 | 42 | 43 | 44 | 45 |
| > 160 | Muito Forte | 51 | 52 | 53 | 54 | 55 |

**Tabela 20 — Classes de Vulnerabilidade para escalas médias e
pequenas** (adaptado de Crepani et al., 2001). Script:
`b_GrauDeDissecacao_Vulnerabilidade`.

Colunas: Amplitude Interfluvial (m); o valor entre parênteses é o peso
de vulnerabilidade da coluna.

| Amplitude Altimétrica (m) | Vulnerabilidade | > 5.000 (1,0) | 2.000 a 5.000 (1,5) | 750 a 2.000 (2,0) | 250 a 750 (2,5) | < 250 (3,0) |
|---|:---:|:---:|:---:|:---:|:---:|:---:|
| < 20 | 1,0 | 11 | 12 | 13 | 14 | 15 |
| 20 a 40 | 1,5 | 21 | 22 | 23 | 24 | 25 |
| 40 a 80 | 2,0 | 31 | 32 | 33 | 34 | 35 |
| 80 a 160 | 2,5 | 41 | 42 | 43 | 44 | 45 |
| > 160 | 3,0 | 51 | 52 | 53 | 54 | 55 |

**Tabela 21 — Atribuição de pesos de Fragilidade e Vulnerabilidade
conforme as cores.** Elaborado pelo autor.

| Cor | Fragilidade/Vulnerabilidade |
|---|---|
| Verde-escuro | Muito Fraca |
| Verde-claro | Fraca |
| Amarelo | Média |
| Laranja | Forte |
| Vermelho | Muito Forte |

As faixas da Dimensão Interfluvial nas duas tabelas são as mesmas usadas
na reclassificação do script 2 (`REMAP_FRAGILIDADE` e
`REMAP_VULNERABILIDADE`), e as faixas de Entalhamento são as do script 1
(`REMAP_ENTALHAMENTO`).

### `scripts/arcgis_pro/3_Grau de Dissecacao_ArcPRO.py` (ArcGIS Pro)

- **Pasta/GDB de trabalho (criada automaticamente):**
  `C:\alexgeopro\GrauDeDissecacao.gdb`
- **Locais padrão que o script procura sozinho:**
  `C:\alexgeopro\Entalhamento.gdb\i_EntalhamentoRecla`,
  `C:\alexgeopro\DimensaoInterfluvial.gdb\l_DimensaoReclaFrag` e
  `l_DimensaoReclaVul`.
- **Saídas** (dentro da geodatabase acima): `b_GrauDeDissecacao_Fragilidade`
  e `b_GrauDeDissecacao_Vulnerabilidade`.

### `scripts/qgis/3_grau_de_dissecacao_QGIS.py` (QGIS, software livre)

- **Pasta de trabalho (criada automaticamente):**
  `C:\alexgeopro\GrauDeDissecacao_QGIS`, com os rasters `a_`/`b_` (e
  algumas grades alinhadas intermediárias, prefixo `_`) como `.tif`
  soltos ali dentro.
- **Locais padrão que o script procura sozinho:**
  `C:\alexgeopro\Entalhamento_QGIS\i_EntalhamentoRecla.tif`,
  `C:\alexgeopro\DimensaoInterfluvial_QGIS\l_DimensaoReclaFrag.tif` e
  `l_DimensaoReclaVul.tif`.
- **Saídas finais:** as mesmas duas de cima, como `.tif`.
- Diferença em relação à versão ArcGIS Pro: antes de somar, os três
  rasters são reprojetados/reamostrados (vizinho mais próximo) para uma
  mesma grade de referência (baseada no limite da área de interesse),
  já que os scripts 1 e 2 recortam por máscaras diferentes entre si e
  raramente saem com a mesma grade de pixels "de fábrica". Detalhes no
  cabeçalho do script.

### `scripts/software_livre/3_grau_de_dissecacao_SoftwareLivre.py` (Python + GDAL/OGR, sem QGIS)

Mesma lógica da versão QGIS acima, mas sem nenhuma dependência do QGIS —
chama `gdal.Warp()`/`gdal.VectorTranslate()` diretamente em vez dos
algoritmos `gdal:warpreproject`/`native:reprojectlayer`/
`gdal:cliprasterbymasklayer` do QGIS:

- **Pasta de trabalho (criada automaticamente):**
  `C:\alexgeopro\GrauDeDissecacao_SemQGIS`.
- **Locais padrão que o script procura sozinho:**
  `C:\alexgeopro\Entalhamento_SemQGIS\i_EntalhamentoRecla.tif`,
  `C:\alexgeopro\DimensaoInterfluvial_SemQGIS\l_DimensaoReclaFrag.tif` e
  `l_DimensaoReclaVul.tif` — ou seja, esta versão espera, por padrão, as
  saídas das versões "sem QGIS" dos scripts 1 e 2 (não as da versão
  QGIS). Se você rodou os scripts 1/2 na versão QGIS, só informar o
  caminho correto na tela quando perguntado.
- **Saídas finais:** as mesmas de sempre, como `.tif`.
- Roda com qualquer instalação comum de Python com `gdal` e `numpy`
  instalados (não precisa de scipy/scikit-image) — basta rodar `python
  "3_grau_de_dissecacao_SoftwareLivre.py"` num terminal comum.

Ambos os índices finais representam os dois índices de Geomorfologia
do modelo de Fragilidade/Vulnerabilidade Ambiental (Tricart).

## Fragilidade Ambiental

Gera o mapa de Fragilidade Ambiental (Cap. 6.6.2 da tese) somando, pixel
a pixel, quatro rasters temáticos — cada um já multiplicado pela "casa
decimal" que lhe cabe, de modo que o valor final é uma **matriz de quatro
algarismos**:

| Algarismo | Tema | Como é obtido | Valores |
|---|---|---|---|
| 1º (milhar) | Relevo | Grau de Dissecação (script 3) reclassificado em fragilidade | 1000 a 5000 |
| 2º (centena) | Solos | Campo `Frag` do mapa pedológico × 100 | 100 a 500 |
| 3º (dezena) | Uso e Cobertura da Terra | MapBiomas reclassificado pela Tabela 24 (abaixo) | 10 a 50 |
| 4º (unidade) | Clima | Campo `Fragilidade` do vetor climático WorldClim | 1 a 5 |

`1111` é a menor fragilidade possível e `5555` a maior. Áreas urbanas
recebem o algarismo **7** e corpos d'água o **9**, em qualquer das
variáveis (ex.: uso urbano = `70`, água = `90` na dezena). Por exemplo,
`3152` = relevo de fragilidade média (3), solo de fragilidade muito fraca
(1), uso de fragilidade muito alta (5) e clima de fragilidade fraca (2).
Esses valores de solo (7 e 9) e de clima já vêm dos dados de entrada — o
script apenas soma.

**Escopo desta versão.** Apenas o dado climático do **WorldClim** é usado
(vetor já classificado, campo `Fragilidade`, produzido pelo procedimento
do Cap. 6.4 da tese — Tabelas 13 e 22). O outro model, que permite
escolher entre sete classificações climáticas (WorldClim + normais do
INMET por IDW e krigagem) e exigia dois `Iterate` encadeados, **não foi
adaptado** aqui. A *Fragilidade Ambiental Potencial* e *Emergente*
(Cap. 6.6.2.1 e 6.6.2.2, Tabelas 25 e 26), que partem da matriz de 4
algarismos gerada por este script, também são outra ferramenta, ainda
não convertida.

**Entradas (perguntadas na tela ao rodar):**

- **Grau de Dissecação – Fragilidade** (`b_GrauDeDissecacao_Fragilidade`,
  saída do script 3): o script procura sozinho no local padrão da versão
  correspondente e só pergunta se não achar. No model original, essa
  etapa partia dos rasters *contínuos* de entalhamento e dimensão e
  refazia as duas reclassificações e a soma; como isso é exatamente o que
  o script 3 já faz, aqui o script 4 aproveita o resultado dele (e depois
  só aplica a reclassificação de 25 combinações `11`–`55` para
  fragilidade do relevo 1000–5000).
- **Mapa pedológico:** vetor (ex.: `PEDOLOGICO_SP_ROSSI_2017_V4`) com o
  campo `Frag`.
- **Vetor climático já classificado:** WorldClim (ex.: `wc21_Br`) com o
  campo `Fragilidade`.
- **Uso e Cobertura da Terra (MapBiomas):** um raster, ou uma pasta/
  geodatabase com **um raster por ano** — substitui o *Iterate Rasters*
  do model: o script gera um resultado `c_<nome do raster>_FRAGILIDADE_FINAL`
  para cada raster. Pode-se limitar quais rasters entram pela constante
  `FILTRO_NOME_USO`.
- **Limite vetorial** da área de interesse.

**Tabela 24 — pesos de Fragilidade (e Vulnerabilidade) do Uso e
Cobertura da Terra, MapBiomas coleção 8** (só as classes que ocorrem no
Estado de SP). Coluna "Valor no script" = fragilidade × 10 (dezena da
matriz):

| Código | Classe | Fragilidade | Vulnerabilidade | Valor no script |
|---:|---|:---:|:---:|:---:|
| 3 | Formação Florestal | 1 | 1,6 | 10 |
| 4 | Formação Savânica | 2 | 2,1 | 20 |
| 5 | Mangue | 1 | 1,4 | 10 |
| 49 | Restinga Arbórea | 1 | 1,4 | 10 |
| 12 | Formação Campestre | 2 | 2,7 | 20 |
| 50 | Restinga Herbácea | 2 | 2,7 | 20 |
| 11 | Campo Alagado e Área Pantanosa | 5 | 3,0 | 50 |
| 32 | Apicum | 5 | 3,0 | 50 |
| 29 | Afloramento Rochoso | 5 | 3,0 | 50 |
| 13 | Outras Formações não Florestais | 5 | 3,0 | 50 |
| 15 | Pastagem | 3 | 2,8 | 30 |
| 19 | Lavoura Temporária | 5 | 3,0 | 50 |
| 39 | Soja | 4 | 3,0 | 40 |
| 20 | Cana | 4 | 3,0 | 40 |
| 62 | Algodão | 4 | 3,0 | 40 |
| 41 | Outras Lavouras Temporárias | 5 | 3,0 | 50 |
| 46 | Café | 3 | 2,9 | 30 |
| 47 | Citrus | 3 | 2,9 | 30 |
| 48 | Outras Lavouras Perenes | 4 | 2,9 | 40 |
| 9 | Silvicultura | 3 | 2,9 | 30 |
| 21 | Mosaico de Usos | 5 | 3,0* | 50 |
| 23 | Praia e Duna | 5 | 3,0* | 50 |
| 25 | Outra Área não Vegetada | 5 | 3,0* | 50 |
| 30 | Mineração | 5 | 3,0* | 50 |
| 33 | Rio, Lago e Oceano | 5* | 3,0* | **90** (água) |
| 31 | Aquicultura | 5* | 3,0* | **90** (água) |
| 24 | Infraestrutura Urbana | — | — | **70** (urbano) |
| 0 | Sem Informação | — | — | **90** (como no model) |

\* Valor máximo atribuído pela ausência (ou indefinição) de cobertura
vegetal. Urbano (7) e água (9) não recebem peso na tabela da tese: são
marcados com esses algarismos para aparecerem destacados na matriz.
A coluna de Vulnerabilidade não é usada por este script (é a do script 5,
Vulnerabilidade Ambiental). Classes que **não** estão nesta
tabela (por exemplo as que não ocorrem em SP) viram *NoData* no resultado
— o script avisa na tela quando encontra alguma. Isso difere do
`Reclassify` do model original com a opção `DATA`, que manteria o código
original da classe (somando um número sem sentido na matriz).

**Mapa de cada tema como o script os prepara:**

- Solos e clima: vetor → SIRGAS 2000 geográfico → raster de ~30 m
  (0,00027777778°) pelo campo de fragilidade.
- Uso da terra: raster → SIRGAS 2000 geográfico → vizinho mais próximo
  para a grade do relevo → reclassificação pela Tabela 24.
- Resultado final recortado pelo contorno exato do limite da área.

**Retomar execuções longas.** Como são até 38 anos (1985–2022), se o
script for interrompido basta rodar de novo: por padrão
(`SOBRESCREVER = False`) ele pula os anos cujo resultado já existe. Os
rasters intermediários de cada ano são apagados ao fim dele
(`MANTER_INTERMEDIARIOS = False`) para economizar disco.

### `scripts/arcgis_pro/4_FragilidadeAmbiental_ArcPRO.py` (ArcGIS Pro)

- **Pasta/GDB de trabalho (criada automaticamente):**
  `C:\alexgeopro\FragilidadeAmbiental.gdb`
- **Local padrão que o script procura sozinho:**
  `C:\alexgeopro\GrauDeDissecacao.gdb\b_GrauDeDissecacao_Fragilidade`.
- **Saídas** (dentro da geodatabase): `a_FragilidadeFinal` (Relevo +
  Solos + Clima, ainda sem o uso da terra — algarismos 1, 2 e 4, com 0 na
  dezena) e um `c_<nome>_FRAGILIDADE_FINAL` por raster de uso da terra
  (a matriz completa de 4 algarismos).
- Diferenças em relação ao model: o buffer de 2 km agora usa método
  geodésico (o model usava planar, sobre dado geográfico) e é dissolvido
  numa feição só; os vetores só são reprojetados se não estiverem já em
  SIRGAS 2000; o *Iterate Rasters* aceita um raster solto, uma pasta ou
  uma geodatabase (o MapBiomas `.gdb` funciona direto aqui).
- Requer a extensão Spatial Analyst.

### `scripts/qgis/4_FragilidadeAmbiental_QGIS.py` (QGIS, software livre)

- **Pasta de trabalho (criada automaticamente):**
  `C:\alexgeopro\FragilidadeAmbiental_QGIS`, com os rasters como `.tif`
  soltos e um `.gpkg` para cada camada vetorial reprojetada.
- **Local padrão que o script procura sozinho:**
  `C:\alexgeopro\GrauDeDissecacao_QGIS\b_GrauDeDissecacao_Fragilidade.tif`.
- **Saídas:** `a_FragilidadeFinal.tif` e
  `c_<nome>_FRAGILIDADE_FINAL.tif` para cada raster de uso da terra.
- Diferença em relação à versão ArcGIS Pro: cada dado é levado direto
  para a grade do raster de relevo (vetores com `gdal.Rasterize` — chamado
  direto na biblioteca GDAL, porque o algoritmo `gdal:rasterize` do QGIS
  pode falhar sem avisar no modo *headless* —, uso da terra com
  `gdal:warpreproject` em vizinho mais próximo), então o buffer
  de 2 km e os recortes intermediários do model deixam de ser necessários;
  as somas são feitas em blocos de linhas com numpy, para não carregar o
  Estado inteiro na memória.
- O **MapBiomas precisa estar como GeoTIFF** (um por ano, numa pasta): o
  QGIS/GDAL não lê raster dentro de geodatabase `.gdb` (no ArcGIS Pro:
  *Copy Raster*).
- Segue o mesmo padrão dos demais scripts QGIS (relança-se sozinho com o
  Python do QGIS, funciona em modo *headless*, um `.gpkg` por camada).

### `scripts/software_livre/4_FragilidadeAmbiental_SoftwareLivre.py` (Python + GDAL/OGR, sem QGIS)

Mesma lógica da versão QGIS acima, mas sem nenhuma dependência do QGIS —
chama `gdal.Warp()`/`gdal.Rasterize()`/`gdal.VectorTranslate()`
diretamente:

- **Pasta de trabalho (criada automaticamente):**
  `C:\alexgeopro\FragilidadeAmbiental_SemQGIS`.
- **Local padrão que o script procura sozinho:**
  `C:\alexgeopro\GrauDeDissecacao_SemQGIS\b_GrauDeDissecacao_Fragilidade.tif`
  (saída da versão "sem QGIS" do script 3; se você rodou o script 3 em
  outra versão, informe o caminho na tela).
- **Saídas finais:** as mesmas da versão QGIS.
- Roda com qualquer instalação comum de Python com `gdal` e `numpy`
  instalados — basta rodar `python "4_FragilidadeAmbiental_SoftwareLivre.py"`
  num terminal comum. Vetores dentro de `.gdb` (ex.:
  `C:\dados\GDB Final.gdb\Camada`) são aceitos; o raster do MapBiomas,
  porém, precisa estar em GeoTIFF.

**Observação sobre o valor `0` do MapBiomas.** No ArcGIS, o valor `0`
(classe "sem informação") entra na reclassificação e vira `90`. Nas
versões QGIS e sem QGIS, se o GeoTIFF declarar `0` como *NoData* (comum),
esses pixels ficam sem valor no resultado em vez de virarem `90`. Dentro
de um limite como o do Estado de SP isso quase não afeta nada, mas vale
saber ao comparar os resultados das versões.

## Vulnerabilidade Ambiental

Gera o mapa de Vulnerabilidade Ambiental (Cap. 6.6.1 e Figura 11 da tese;
metodologia de Crepani et al., 1996 e 2001). Ao contrário da Fragilidade
(que soma algarismos), a vulnerabilidade é a **média aritmética, pixel a
pixel, de cinco temas** — cada um já expresso como grau de vulnerabilidade
de **1,0** (mais estável, pedogênese) a **3,0** (mais instável,
morfogênese):

| Tema | Como é obtido (tese) | Peso |
|---|---|---|
| Relevo | `R = (G + A + D) / 3` — G: dissecação (amplitude do interflúvio, Tabela 7), A: amplitude altimétrica (Tabela 8) e D: clinografia (Tabela 9) | Tabelas 7, 8 e 9 |
| Solos | Mapa pedológico do IAC (Rossi, 2017), 27 classes | Tabela 18 |
| Geologia | Unidades litológicas da CPRM (Peixoto, 2010); litotipo de **maior** vulnerabilidade quando há mais de um | Tabela 10 (Crepani) e Tabela 52 (anexo da tese) |
| Clima | Intensidade pluviométrica (chuva anual ÷ distribuição sazonal) | Tabela 14 |
| Uso e Cobertura da Terra | MapBiomas coleção 8, um raster por ano (1985–2022) | Tabela 24 |

**Escala dos rasters: vulnerabilidade × 10.** No model, tudo é gravado
com a vulnerabilidade multiplicada por 10 (1,6 → `16`; 3,0 → `30`): a
tabela de reclassificação do uso da terra e o *Calculate Field* dos campos
de geologia, solos e clima. O script faz essas multiplicações sozinho —
**os campos dos vetores devem estar de 1,0 a 3,0**, e o script mostra os
valores distintos (já × 10) de cada um e avisa se parecerem estar fora do
esperado (por exemplo, se o campo já estiver multiplicado por 10). No
fim ele também mostra o mínimo e o máximo de cada tema. O resultado fica
entre 10 e 30, mais os valores **70** (área urbana) e **90** (água) nos
produtos que sobrepõem essas classes.

**Três produtos** (como na tese, p. 86–87):

| Produto | Saída | O que é |
|---|---|---|
| Sem o uso da terra | `h_Vuln_CellStatisticNoDataGRSC_noLanduse` | Média de Geologia, Relevo, Solos e Clima — só os fatores naturais (GRSC = Geologia, Relevo, Solos, Clima) |
| Com o uso da terra, urbano/água fora da média | `h_Vuln_CellStatisticNoData_<nome do raster de uso>` | Média dos cinco temas; urbano e água do uso viram *NoData* (nesses pixels a média sai dos outros quatro) |
| Com o uso da terra, urbano/água como máscara | `h_Vuln_CellStatisticNoDataUrbAgua_<nome do raster de uso>` | Igual ao anterior, com urbano (`70`) e água (`90`) sobrepostos como máscara. Permite estudar, por exemplo, em que níveis de vulnerabilidade avança a área urbana |

**Por que *NoData* e não o valor do relevo.** A tese (p. 85) conta que
chegou a testar atribuir às áreas de água (geologia e pedologia) e urbanas
(pedologia) a vulnerabilidade do relevo, mas adotou *NoData*: o *Cell
Statistics* só conta na média as células com valor, o que evita pesar o
relevo em dobro ou em triplo. Exemplo da tese: onde solos e geologia são
"água", a vulnerabilidade é a média de uso, relevo e clima.

**Entradas.** O script segue o model completo da tese (Figura 11; export
`5_VulnerabilidadeAmbiental_Arc103_V6_completa.py`, que corresponde ao
*Modelo Geral_VulnerabilidadeV6*, o model **V6** da toolbox): parte dos dados brutos e constrói os
quatro temas naturais. As entradas são:

- **DEM** (`mosaico.tif`): base da declividade e **grade de referência** de
  todo o resto (SIRGAS 2000 geográfico, célula de 0,00027777778° ≈ 30 m,
  interpolação bilinear, como no model).
- **Entalhamento do Vale** (`h_entalhamento`) e **Dimensão Interfluvial
  Média** (`j_Dimensao`): saídas **contínuas, em metros, dos scripts 1 e
  2** (não os reclassificados). O script procura nos locais padrão de
  cada versão e, se não achar, pergunta.
- **Vetor de Geologia** (campo `Vulnerabil`), **vetor de Solos** (campo
  `Vulne`) e **vetor de Clima** (campo `Vulnerabilidade`), com a
  vulnerabilidade de **1,0 a 3,0** (água = 9 e urbano = 7 nos campos de
  geologia e solos, que viram 90 e 70 depois do × 10). Vetores dentro de
  `.gdb` funcionam nas três versões (ex.:
  `C:\dados\GDB Final.gdb\Vulnerabilidade_Final`). Se o campo do seu dado
  tem outro nome, ajuste `CAMPO_GEOLOGIA`, `CAMPO_SOLOS` ou `CAMPO_CLIMA`
  no topo do script. No model, a tese gera **sete** versões do clima
  (WorldClim; krigagem das normais do INMET 1961–1990, 1981–2010 e
  1991–2020; IDW dos mesmos três períodos): o script não escolhe — basta
  apontar o vetor da versão desejada (o model exportado usa
  `Vuln_wc21_30s_Brasil`, do WorldClim).
- **Uso e Cobertura da Terra:** um raster, ou uma pasta/geodatabase com
  **um raster por ano** (substitui o *Iterate Rasters* do model). Pode-se
  limitar quais rasters entram por `FILTRO_NOME_USO`.
- **Limite vetorial** da área de interesse.

**Como cada tema é construído** (Cap. 6.6.1 e model):

| Tema | Construção | Saída |
|---|---|---|
| Relevo | Entalhamento → Tabela 8; Dimensão Interfluvial → Tabela 7; declividade (%) do DEM → Tabela 9 (fator Z `0,00000956`). Cada um é reclassificado em 21 classes (10 a 30) e o Relevo é a **média dos três** — no model: classe ÷ 10, soma ÷ 3, × 10 (equivalente) | `rel_e2_Relevo` |
| Geologia | Campo `Vulnerabil` × 10 → raster na grade do relevo. Água (90) → *NoData* | `geol_d2_Rochas` |
| Solos | Campo `Vulne` × 10 → raster. Urbano (70) e água (90) → *NoData* | `ped_d2_solos` |
| Clima | Campo `Vulnerabilidade` × 10 → raster | `cli_c_clima` |

*Sobre as Tabelas 7 e 8:* o texto da seção 6.6.1 cita as tabelas na ordem
entalhamento → Tabela 7, dimensão → Tabela 8, mas pelos títulos — e pelo
model exportado — é o inverso (Tabela 7 = amplitude do interflúvio =
dimensão interfluvial; Tabela 8 = amplitude altimétrica = entalhamento).
**O Relevo da vulnerabilidade não é a saída do script 3**: aquela é o grau
de dissecação em classes de 1 a 5 (Fragilidade/Vulnerabilidade
qualitativas); aqui o relevo usa os valores contínuos de 1,0 a 3,0 das
Tabelas 7 a 9, mais a declividade.

**Faixas das Tabelas 7, 8 e 9.** As faixas do *Reclassify* estão no topo do
script (`LIMITES_ENTALHAMENTO`, `LIMITES_DIMENSAO` e
`LIMITES_DECLIVIDADE`) e foram conferidas, uma a uma, com o export do
ArcMap 10.3 — cada classe vai de `[limite anterior, limite seguinte)`.
Veja as três tabelas na seção de pesos mais abaixo.

**Observações importantes (diferenças em relação ao model exportado):**

- Classes de uso que **não** estão na Tabela 24 viram *NoData* (o script
  avisa), em vez de manter o código original (comportamento do
  `Reclassify` do model com `DATA`, que deixaria o número da classe
  entrando na média). O código `0` (sem informação) vira *NoData*, como no
  model (`0 NODATA`).
- **Aquicultura (31) = 3,0** (valor `30`, entra na média) e só a classe 33
  (rio, lago e oceano) vira água (`90`) — como no model exportado e na
  Tabela 24 da tese. No script de Fragilidade, ao contrário, 31 e 33 viram
  `90`.
- O produto "sem uso da terra" (GRSC) é recortado pelo limite exato; no
  model exportado ele ficava sem esse recorte final (os demais tinham).
- O *Mosaic To New Raster* (`FIRST`) que sobrepõe urbano/água à média é
  feito na versão ArcGIS Pro com `Con(IsNull(...))`, equivalente para esse
  caso; nas versões livres a sobreposição é feita no próprio cálculo em
  blocos.
- O resultado é *Float32* (a média não é inteira).
- **Declividade:** o model usa `Slope_3d` (extensão 3D Analyst), em
  porcentagem e com fator Z `0,00000956`. A versão ArcGIS Pro usa
  `arcpy.sa.Slope` (Spatial Analyst, mesmo cálculo, sem precisar do 3D
  Analyst) e as versões livres usam `gdal.DEMProcessing` (algoritmo de
  Horn, escala = 1 / fator Z ≈ 104.603 m por grau). O fator Z converte
  graus em metros para a latitude de São Paulo; para outra região, ajuste
  `Z_FACTOR` no topo do script.
- **Grade de referência:** é a do DEM projetado. Entalhamento e Dimensão
  Interfluvial (que vêm dos scripts 1 e 2, possivelmente com outra grade)
  e todos os demais temas são reamostrados para ela por vizinho mais
  próximo; onde falta qualquer um dos três componentes do relevo, o
  relevo fica *NoData* (como na *Raster Calculator*).
- **Faixas extremas do *Reclassify*:** nas versões livres a primeira e a
  última faixa vão até −∞ / +∞ (no model: −5000 e 5000, 200000 ou 2000);
  só muda para valores impossíveis na prática.
- **Vetores recortados:** o model recorta os vetores pelo buffer de 2 km
  antes de projetar. Nas versões livres a grade já limita a área, então
  só as feições que tocam a grade são reprojetadas (muito mais rápido
  para o clima do Brasil inteiro).

**Retomar execuções longas.** Com `SOBRESCREVER = False` o script reaproveita
o que já existe: os temas `rel_e2_Relevo`, `geol_d2_Rochas`, `ped_d2_solos`
e `cli_c_clima` (úteis para rodar de novo só a parte do uso da terra) e os
anos cujos dois resultados já estão prontos. Os temas e os três produtos
sempre ficam gravados; os demais intermediários (DEM projetado,
declividade, vetores recortados, rasters de cada ano) são apagados
(`MANTER_INTERMEDIARIOS = False`).

### Partindo dos quatro temas prontos (model V7, versão simplificada)

A toolbox tem dois models da Vulnerabilidade: o **V6** é o fluxo completo,
que parte dos dados brutos (é o que os scripts 5 implementam), e o **V7**
é a versão simplificada, que já recebe os quatro temas naturais prontos
(`rel_e2_Relevo`, `geol_d2_Rochas`, `ped_d2_solos` e `cli_c_clima`, todos
× 10, na mesma grade) e só trata o uso da terra e tira as médias. O V7 é
útil quando os temas já existem: refazer só a parte do uso da terra (por
exemplo, com outra coleção do MapBiomas) ou trocar um único tema — como o
clima, que a tese gera em sete versões — sem reconstruir o relevo.

Os scripts não têm um "modo V7" próprio, mas dá para usá-los assim:

1. Grave os quatro temas na pasta (ou geodatabase) de saída do script, com
   exatamente esses nomes (`.tif` nas versões QGIS e sem QGIS) e deixe
   `SOBRESCREVER = False`. O script encontra cada tema pronto, **não o
   refaz** e segue direto para as médias e o uso da terra. Para refazer só
   um deles, apague-o da pasta antes de rodar.
2. O script ainda **pergunta** o DEM, os rasters dos scripts 1 e 2 e os três
   vetores. Como esses dados não serão usados (os temas já existem), basta
   apontar qualquer raster ou vetor válido para cada pergunta.
3. Os temas prontos precisam estar **como o V7 espera**: vulnerabilidade
   × 10 (10 a 30); água (e urbano, nos solos) já como *NoData*; mesmo SIRGAS
   2000 geográfico. Nas versões **QGIS e sem QGIS** os quatro temas
   precisam ainda ter **exatamente a mesma grade** (extensão, tamanho e
   posição das células) — se forem de outra origem, o script interrompe
   com o aviso de que os rasters não estão na mesma grade. A versão ArcGIS
   Pro alinha pela grade do relevo, mas vale conferir.

### `scripts/arcgis_pro/5_VulnerabilidadeAmbiental_ArcPRO_V6_completa.py` (ArcGIS Pro)

- **Geodatabase de trabalho (criada automaticamente):**
  `C:\alexgeopro\VulnerabilidadeAmbiental.gdb`.
- **Pergunta na tela:** DEM, os rasters dos scripts 1 e 2 (procura em
  `C:\alexgeopro\Entalhamento.gdb\h_entalhamento` e
  `C:\alexgeopro\DimensaoInterfluvial.gdb\j_Dimensao`), os vetores de
  geologia, solos e clima, o uso da terra (raster ou geodatabase/pasta) e
  o limite.
- **Saídas:** os quatro temas (`rel_e2_Relevo`, `geol_d2_Rochas`,
  `ped_d2_solos`, `cli_c_clima`), `h_Vuln_CellStatisticNoDataGRSC_noLanduse`
  e, para cada raster de uso, `h_Vuln_CellStatisticNoData_<nome>` e
  `h_Vuln_CellStatisticNoDataUrbAgua_<nome>`.
- Como nos demais scripts ArcGIS, o buffer de 2 km (geodésico) recorta os
  vetores e o uso da terra, e os resultados são recortados pelo limite
  exato. Precisa só da extensão Spatial Analyst (não do 3D Analyst).

### `scripts/qgis/5_VulnerabilidadeAmbiental_QGIS_V6_completa.py` (QGIS, software livre)

- **Pasta de trabalho (criada automaticamente):**
  `C:\alexgeopro\VulnerabilidadeAmbiental_QGIS`.
- **Procura sozinho** `C:\alexgeopro\Entalhamento_QGIS\h_entalhamento.tif`
  e `C:\alexgeopro\DimensaoInterfluvial_QGIS\j_Dimensao.tif` (saídas dos
  scripts 1 e 2 desta versão).
- **Saídas:** as mesmas da versão ArcGIS, em GeoTIFF (`.tif`, Float32,
  *NoData* −9999).
- Todo o processamento de raster (projetar o DEM, declividade, alinhar,
  rasterizar) é chamado **direto na biblioteca GDAL** do Python do QGIS
  (não pelos algoritmos `gdal:*` do Processing, que no modo *headless*
  podem falhar sem avisar); as médias são feitas em blocos com numpy. O
  QGIS entra para recortar e reprojetar os vetores
  (`native:extractbyextent` e `native:reprojectlayer`).
- O **MapBiomas precisa estar como GeoTIFF** (um por ano, numa pasta).
- Segue o mesmo padrão dos demais scripts QGIS (relança-se sozinho com o
  Python do QGIS, funciona em modo *headless*).

### `scripts/software_livre/5_VulnerabilidadeAmbiental_SoftwareLivre_V6_completa.py` (Python + GDAL/OGR, sem QGIS)

Mesma lógica da versão QGIS, sem nenhuma dependência do QGIS:

- **Pasta de trabalho (criada automaticamente):**
  `C:\alexgeopro\VulnerabilidadeAmbiental_SemQGIS`; procura
  `C:\alexgeopro\Entalhamento_SemQGIS\h_entalhamento.tif` e
  `C:\alexgeopro\DimensaoInterfluvial_SemQGIS\j_Dimensao.tif`.
- **Saídas:** as mesmas da versão QGIS.
- Roda com qualquer instalação comum de Python com `gdal` e `numpy` —
  basta rodar `python "5_VulnerabilidadeAmbiental_SoftwareLivre_V6_completa.py"`. Vetores em
  `.gdb` são aceitos para leitura; o MapBiomas precisa estar em GeoTIFF.

**Sobre os testes.** As versões **QGIS** (QGIS 3.34 em modo *headless*) e
**sem QGIS** (GDAL 3.8) foram executadas de ponta a ponta com dados
sintéticos (DEM, entalhamento, dimensão, três vetores, dois rasters de uso
com resolução e origem diferentes e um limite), e cada pixel dos resultados
foi comparado com um cálculo independente: relevo (declividade de Horn,
faixas e média), temas vetoriais, os dois produtos de cada ano e o
produto sem uso da terra — sem diferenças. As tabelas de faixas
(Tabelas 7, 8 e 9) e a de reclassificação do uso foram comparadas
programaticamente com o export do ArcMap 10.3 nas três versões. A versão
**ArcGIS Pro não foi executada** (o ambiente em que foi escrita não tem
`arcpy`): usa as mesmas faixas e a mesma lógica das outras, mas só rodando
com seus dados para confirmar. Nenhuma das três foi executada com os dados
reais da tese.

## Pesos de Fragilidade e Vulnerabilidade (tabelas da tese)

Os pesos abaixo vêm das tabelas do Cap. 5.4 (fundamentação) e do Cap. 6
(aplicação) da tese. Fragilidade segue Ross (1994, 2012), em classes de 1
(muito fraca) a 5 (muito forte); Vulnerabilidade segue Crepani et al.
(1996, 2001), de 1,0 (estável) a 3,0 (instável). Eles já estão embutidos
nos dados de entrada (solos, geologia, clima) ou nas tabelas de
reclassificação dos scripts (relevo e uso da terra) — esta seção só
documenta de onde vêm.

### Solos — Tabela 18 (Rossi, 2017, adaptado)

Valores gravados no mapa pedológico (campos de fragilidade e de
vulnerabilidade); o script 4 lê a fragilidade (campo `Frag`) e o script 5
lê a vulnerabilidade (campo `Vulne`) e multiplica por 10 (raster `ped_d2_solos`).

| Classe | Código | Fragilidade | Vulnerabilidade |
|---|---|:---:|:---:|
| Afloramento Rochoso | AF | *5 | 3,0 |
| Argissolos | PA | 3 | 2,0 |
| Argissolos Vermelhos | PV1 a PV12 | 3 | 2,0 |
| Argissolos Vermelho-Amarelos | PVA1 a PVA44 | 3 | 2,0 |
| Cambissolos Húmicos | CH1 a CH4 | 4 | 2,5 |
| Cambissolos Háplicos | CX1 a CX24 | 4 | 2,5 |
| Chernossolos Argilúvicos | MT1 a MT6 | *1 | 2,0 |
| Espodossolos | EK | 5 | 2,0 |
| Gleissolos Tiomórficos | GJ | 5 | 3,0 |
| Gleissolos Sálicos | GZ | 5 | 3,0 |
| Gleissolos Melânicos | GM1 a GM3 | 5 | 3,0 |
| Gleissolos Háplicos | GX1 a GX12 | 5 | 3,0 |
| Latossolos Brunos | LB1 a LB3 | 1 | 1,0 |
| Latossolos Amarelos – Férricos | LA1 a LA5 | 2 | 1,0 |
| Latossolos Amarelos – Não Férricos | LA6 a LA13 | 2 | 1,0 |
| Latossolos Vermelhos – Férricos | LV1 a LV18 | 1 | 1,0 |
| Latossolos Vermelhos – Não Férricos | LV19 a LV31 | 1 | 1,0 |
| Latossolos Vermelho-Amarelos | LVA1 a LVA20 | 1 | 1,0 |
| Luvissolos Háplicos | TX1 a TX5 | *4 | 2,0 |
| Neossolos Litólicos | RL1 a RL26 | 5 | 3,0 |
| Neossolos Flúvicos | RY1 a RY3 | 5 | 3,0 |
| Neossolos Quartzarênicos | RQ1 a RQ8 | 5 | 3,0 |
| Nitossolos Vermelhos | NV1 a NV16 | 3 | 2,0 |
| Organossolos Tiomórficos | OJ1 a OJ2 | 5 | 3,0 |
| Organossolos Háplicos | OX1 a OX4 | 5 | 3,0 |
| Planossolos Háplicos | SX1 a SX4 | *4 | 2,0 |
| Plintossolos Pétricos | FF1 a FF2 | *2 | 3,0 |

\* Afloramento Rochoso: Crepani considera vulnerabilidade "Alta" (início
de formação de solo) e o mesmo critério foi adotado para a fragilidade.
Chernossolos Argilúvicos: B textural desenvolvido, adequado à
agricultura (fragilidade muito baixa). Luvissolos Háplicos: áreas com
deficiência hídrica, muita argila, pouco profundos, usados para pastagem
(fragilidade alta). Planossolos Háplicos: solo hidromórfico, usado para
pastagem e rizicultura (fragilidade alta). Plintossolos Pétricos: ruins
para a agricultura, bons para estradas, solos já enrijecidos e bem
drenados (fragilidade baixa).

As classes "Área Urbana" e "Rios, represas e lagoas" receberam, no mapa
de solos, valores à parte para não receberem peso equivocado. Na
Fragilidade elas aparecem como os algarismos 7 e 9; na Vulnerabilidade o
model as trata como *NoData* (saem da média).

### Uso e Cobertura da Terra — Tabela 24 (MapBiomas coleção 8)

Só as classes presentes no Estado de SP. "Script 4" = fragilidade × 10;
"Script 5" = vulnerabilidade × 10 (como gravado no `Reclassify` de cada
model). As classes de outras regiões do Brasil não estão nas tabelas dos
scripts e viram *NoData* (o script avisa).

| Código | Classe | Fragilidade | Vulnerabilidade | Script 4 | Script 5 |
|---:|---|:---:|:---:|:---:|:---:|
| 3 | Formação Florestal | 1 | 1,6 | 10 | 16 |
| 4 | Formação Savânica | 2 | 2,1 | 20 | 21 |
| 5 | Mangue | 1 | 1,4 | 10 | 14 |
| 49 | Restinga Arbórea | 1 | 1,4 | 10 | 14 |
| 11 | Campo Alagado e Área Pantanosa | 5 | 3,0 | 50 | 30 |
| 12 | Formação Campestre | 2 | 2,7 | 20 | 27 |
| 32 | Apicum | 5 | 3,0 | 50 | 30 |
| 29 | Afloramento Rochoso | 5 | 3,0 | 50 | 30 |
| 50 | Restinga Herbácea | 2 | 2,7 | 20 | 27 |
| 13 | Outras Formações não Florestais | 5 | 3,0 | 50 | 30 |
| 15 | Pastagem | 3 | 2,8 | 30 | 28 |
| 19 | Lavoura Temporária | 5 | 3,0 | 50 | 30 |
| 39 | Soja | 4 | 3,0 | 40 | 30 |
| 20 | Cana | 4 | 3,0 | 40 | 30 |
| 62 | Algodão | 4 | 3,0 | 40 | 30 |
| 41 | Outras Lavouras Temporárias | 5 | 3,0 | 50 | 30 |
| 46 | Café | 3 | 2,9 | 30 | 29 |
| 47 | Citrus | 3 | 2,9 | 30 | 29 |
| 48 | Outras Lavouras Perenes | 4 | 2,9 | 40 | 29 |
| 9 | Silvicultura | 3 | 2,9 | 30 | 29 |
| 21 | Mosaico de Usos | 5 | 3,0* | 50 | 30 |
| 23 | Praia e Duna | 5 | 3,0* | 50 | 30 |
| 30 | Mineração | 5 | 3,0* | 50 | 30 |
| 25 | Outra Área não Vegetada | 5 | 3,0* | 50 | 30 |
| 24 | Infraestrutura Urbana | — | — | **70** | **70** |
| 33 | Rio, Lago e Oceano | 5* | 3,0* | **90** | **90** |
| 31 | Aquicultura | 5* | 3,0* | **90** | 30 |
| 0 | Sem Informação | — | — | **90** | NoData |

\* Valor máximo atribuído pela ausência (ou indefinição) de cobertura
vegetal. Urbano e água não recebem peso na tabela da tese: os scripts os
marcam com `70` e `90` para aparecerem destacados (na matriz de
Fragilidade, e como máscara nos produtos de Vulnerabilidade). A
Aquicultura difere entre os dois scripts porque os models exportados
tratam a classe de forma diferente (no de Vulnerabilidade, só a classe 33
é água).

### Relevo — Vulnerabilidade (Tabelas 7, 8 e 9, Crepani et al., 2001)

A vulnerabilidade do relevo é `R = (G + A + D) / 3` (Equação 1 da tese),
com G, A e D buscados nas três tabelas abaixo. A fragilidade do relevo
vem do grau de dissecação (Tabelas 19 a 21 e script 3).

**Tabela 7 — Intensidade de dissecação (amplitude do interflúvio, m):**

| Amplitude do interflúvio (m) | Vuln. | Amplitude do interflúvio (m) | Vuln. | Amplitude do interflúvio (m) | Vuln. |
|---|:---:|---|:---:|---|:---:|
| > 5.000 | 1,0 | 3.250 – 3.500 | 1,7 | 1.500 – 1.750 | 2,4 |
| 4.750 – 5.000 | 1,1 | 3.000 – 3.250 | 1,8 | 1.250 – 1.500 | 2,5 |
| 4.500 – 4.750 | 1,2 | 2.750 – 3.000 | 1,9 | 1.000 – 1.250 | 2,6 |
| 4.250 – 4.500 | 1,3 | 2.500 – 2.750 | 2,0 | 750 – 1.000 | 2,7 |
| 4.000 – 4.250 | 1,4 | 2.250 – 2.500 | 2,1 | 500 – 750 | 2,8 |
| 3.750 – 4.000 | 1,5 | 2.000 – 2.250 | 2,2 | 250 – 500 | 2,9 |
| 3.500 – 3.750 | 1,6 | 1.750 – 2.000 | 2,3 | < 250 | 3,0 |

**Tabela 8 — Amplitude altimétrica (m):**

| Amplitude altimétrica (m) | Vuln. | Amplitude altimétrica (m) | Vuln. | Amplitude altimétrica (m) | Vuln. |
|---|:---:|---|:---:|---|:---:|
| < 20 | 1,0 | 77 – 84,5 | 1,7 | 141,5 – 151 | 2,4 |
| 20 – 29,5 | 1,1 | 84,5 – 94 | 1,8 | 151 – 160,5 | 2,5 |
| 29,5 – 39 | 1,2 | 94 – 103,5 | 1,9 | 160,5 – 170 | 2,6 |
| 39 – 48,5 | 1,3 | 103,5 – 113 | 2,0 | 170 – 179,5 | 2,7 |
| 48,5 – 58 | 1,4 | 113 – 122,5 | 2,1 | 179,5 – 189 | 2,8 |
| 58 – 67,5 | 1,5 | 122,5 – 132 | 2,2 | 189 – 200 | 2,9 |
| 67,5 – 77 | 1,6 | 132 – 141,5 | 2,3 | > 200 | 3,0 |

**Tabela 9 — Clinografia (declividade):**

| Em % | Em graus | Vuln. | Em % | Em graus | Vuln. | Em % | Em graus | Vuln. |
|---|---|:---:|---|---|:---:|---|---|:---:|
| < 2 | < 3,5 | 1,0 | 9,9 – 11,2 | 17,4 – 19,8 | 1,7 | 19,1 – 20,4 | 34,6 – 37,2 | 2,4 |
| 2 – 3,3 | 3,5 – 5,8 | 1,1 | 11,2 – 12,5 | 19,8 – 22,2 | 1,8 | 20,4 – 21,7 | 37,2 – 39,8 | 2,5 |
| 3,3 – 4,6 | 5,8 – 5,8 | 1,2 | 12,5 – 13,8 | 22,2 – 24,5 | 1,9 | 21,7 – 23,0 | 39,8 – 42,4 | 2,6 |
| 4,6 – 5,9 | 8,2 – 10,3 | 1,3 | 13,8 – 15,2 | 24,5 – 27,2 | 2,0 | 23,0 – 24,4 | 42,4 – 45,3 | 2,7 |
| 5,9 – 7,3 | 10,3 – 12,9 | 1,4 | 15,2 – 16,5 | 27,2 – 29,6 | 2,1 | 24,4 – 25,7 | 45,3 – 48,1 | 2,8 |
| 7,3 – 8,6 | 12,9 – 15,1 | 1,5 | 16,5 – 17,8 | 29,6 – 32,1 | 2,2 | 25,7 – 27,0 | 48,1 – 50,0 | 2,9 |
| 8,6 – 9,9 | 15,1 – 17,4 | 1,6 | 17,8 – 19,1 | 32,1 – 34,6 | 2,3 | > 27 | > 50 | 3,0 |

(Transcrita como está na tese. Na linha "3,3 – 4,6" a faixa em graus
aparece como "5,8 – 5,8", provável erro de digitação — pela sequência
deveria ser "5,8 – 8,2". Vale corrigir na tese e conferir antes de usar a
tabela como referência.)

### Geologia — Tabela 10 (Crepani et al., 1996, 2001)

A tese classifica **todos os litotipos do Estado de SP** a partir dessa
escala (lista completa na Tabela 52, no anexo). Fragilidade não usa
litologia (Ross não a considera diretamente); só a Vulnerabilidade.

| Vuln. | Rochas | Vuln. | Rochas | Vuln. | Rochas |
|:---:|---|:---:|---|:---:|---|
| 1,0 | Quartzitos ou metaquartzitos | 1,7 | Milonitos, quartzo-muscovita, biotita, clorita xisto | 2,4 | Arenitos quartzosos ou ortoquartzitos |
| 1,1 | Riólito, granito, dacito | 1,8 | Piroxenito, anfibolito, kimberlito, dunito | 2,5 | Conglomerados, subgrauvacas |
| 1,2 | Granodiorito, quartzo-diorito, granulitos | 1,9 | Hornblenda, tremolita, actinolita xisto | 2,6 | Grauvacas, arcózios |
| 1,3 | Migmatitos, gnaisses | 2,0 | Estaurolita xisto, xistos granatíferos | 2,7 | Siltitos, argilitos |
| 1,4 | Fonólito, nefelina sienito, traquito, sienito | 2,1 | Filito, metassiltito | 2,8 | Folhelhos |
| 1,5 | Andesito, diorito, basalto | 2,2 | Ardósia, metargilito | 2,9 | Calcários, dolomitos, margas, evaporitos |
| 1,6 | Anortosito, gabro, peridotito | 2,3 | Mármores | 3,0 | Sedimentos inconsolidados: aluviões, colúvios etc. |

### Clima

**Fragilidade — Tabela 22** (Pluviosidade anual × distribuição sazonal,
adaptada de Ross, 2012; valores com \* foram adaptados pela autora para
suavizar a transição entre os valores de Ross). É a matriz que gera o
campo `Fragilidade` (1 a 5) do vetor climático do script 4:

| Pluviosidade anual (mm) \ Meses de chuva | 8 | 9 | 10 | 11 | 12 |
|---|:---:|:---:|:---:|:---:|:---:|
| < 900 | 5 | 5 | 5 | 5 | 5 |
| 1000 | 5\* | 4\* | 4\* | 3\* | 3\* |
| 1300 | 4\* | 3\* | 3\* | 1 | 1 |
| 1600 | 4\* | 3 | 3 | 1\* | 1\* |
| 1800 | 4 | 4 | 3\* | 1\* | 1\* |
| 2000 | 5\* | 4\* | 3\* | 1\* | 1\* |
| 2500 | 5\* | 5\* | 4\* | 2 | 2 |
| > 2500 | 5 | 5 | 5 | 5 | 5 |

**Vulnerabilidade — Tabela 14** (intensidade pluviométrica em mm/mês =
chuva anual ÷ distribuição sazonal, Crepani et al., 2001):

| Intensidade (mm/mês) | Vuln. | Intensidade (mm/mês) | Vuln. | Intensidade (mm/mês) | Vuln. |
|---|:---:|---|:---:|---|:---:|
| < 50 | 1,0 | 200 – 225 | 1,7 | 375 – 400 | 2,4 |
| 50 – 75 | 1,1 | 225 – 250 | 1,8 | 400 – 425 | 2,5 |
| 75 – 100 | 1,2 | 250 – 275 | 1,9 | 425 – 450 | 2,6 |
| 100 – 125 | 1,3 | 275 – 300 | 2,0 | 450 – 475 | 2,7 |
| 125 – 150 | 1,4 | 300 – 325 | 2,1 | 475 – 500 | 2,8 |
| 150 – 175 | 1,5 | 325 – 350 | 2,2 | 500 – 525 | 2,9 |
| 175 – 200 | 1,6 | 350 – 375 | 2,3 | > 525 | 3,0 |

## Requisitos

**Scripts ArcGIS Pro** (pasta `scripts/arcgis_pro/`):
- ArcGIS Pro com `arcpy`
- Extensões: Spatial Analyst (todos) e 3D Analyst (script 2, por causa do
  Add Surface Information)

**Scripts QGIS** (pasta `scripts/qgis/`, versões livres):
- QGIS 3.x instalado (já traz GDAL, numpy e o framework `processing`)
- `scipy` e `scikit-image` dentro do Python do QGIS, necessários para os
  scripts 1 e 2 (os scripts 3 e 4 não precisam deles) — no Windows, abra o
  "OSGeo4W Shell" (instalado junto com o QGIS), digite `py3_env` e depois
  `python -m pip install scipy scikit-image` (uma vez só)
- Rodar de qualquer jeito, inclusive o botão "Run" de um editor comum
  (ex.: VS Code): todos os scripts QGIS detectam sozinhos se não estão rodando
  com o Python do QGIS e, se for o caso, procuram o `python-qgis.bat`
  instalado (em qualquer pasta `C:\Program Files\QGIS <versão>\bin\`,
  sem precisar saber a versão exata) e se relançam automaticamente com
  ele — nada a fazer manualmente na maioria dos casos.
- Também dá pra rodar de dentro do QGIS (Console Python > Editor de
  script > abrir o arquivo e clicar em "Executar script"), ou direto
  pelo terminal (Prompt de Comando/PowerShell) apontando o
  `python-qgis.bat` manualmente, por exemplo:

  ```
  "C:\Program Files\QGIS 3.34\bin\python-qgis.bat" "C:\caminho\para\1_Entalhamento do Vale_QGIS.py"
  ```

  Todos esses modos continuam exigindo o QGIS instalado na máquina (é
  dele que vêm o `qgis.core`/`processing` por baixo) — só não precisa
  abrir o programa. Se o script não encontrar o `python-qgis.bat`
  sozinho (instalação em local incomum), ele avisa e você pode rodar
  manualmente apontando o caminho certo, como no exemplo acima, ou
  ajustar a constante `CAMINHO_INSTALACAO_QGIS` no topo de cada script.

**Scripts sem QGIS** (pasta `scripts/software_livre/`, versões livres e 100%
independentes do QGIS):
- Nenhum programa de SIG precisa estar instalado — só os pacotes Python:
  `gdal` (`osgeo`), `numpy` e, para os scripts 1 e 2, também `scipy` e
  `scikit-image`.
- Instalação mais simples: usando conda —
  `conda install -c conda-forge gdal numpy scipy scikit-image` (uma vez
  só; o pacote `gdal` do PyPI puro costuma dar mais trabalho para
  compilar no Windows, então conda-forge é o caminho mais tranquilo).
- Rodar: `python "1_Entalhamento do Vale_SoftwareLivre.py"` (e equivalentes)
  num terminal comum, dentro do ambiente onde os pacotes acima estão
  instalados.

## Antes de rodar

Os scripts numerados de 1 a 5 das três pastas (`scripts/arcgis_pro/`,
`scripts/qgis/` e `scripts/software_livre/`) já
criam sozinhos a pasta/GDB (ou pasta comum, nas versões QGIS/sem QGIS)
de trabalho e perguntam os dados de entrada na
tela ao rodar (os scripts 3 ainda tentam achar sozinhos, nos locais
padrão, os rasters gerados pelos scripts 1 e 2, os scripts 4 o raster
gerado pelo script 3, e os scripts 5 também procuram as saídas dos scripts 1 e 2 e
pedem o DEM, os vetores de geologia, solos e clima, o uso da terra e o limite) — não é preciso editar nada neles antes de rodar.

## Nota de transparência metodológica

Ao conferir o script `1_Entalhamento do Vale_ArcPRO.py` contra a exportação
nativa do ArcMap 10.3, identificamos uma falha de tradução do próprio
exportador do ArcMap (não do model em si): a variável que a ferramenta
Eliminate usa como entrada, gerada automaticamente para a "saída
derivada" de um Select Layer By Location anterior, nunca é reatribuída
corretamente no script exportado — ela herda um valor de outro elemento
do model sem relação lógica com o fluxo real de dados. Isso é uma
limitação conhecida do exportador Model→Python do ArcMap para
ferramentas que alteram a seleção "in place" (Select Layer By Attribute,
Select Layer By Location, Add Join, etc.), não um erro de como o model
foi construído — rodado dentro do próprio ModelBuilder/ArcMap (que foi o
que gerou os resultados publicados na tese), o fluxo de dados está
correto, pois o motor de execução do ModelBuilder rastreia as conexões
reais do diagrama internamente. O script Python aqui já traz essa
correção.

Essa observação vale para a versão ArcGIS Pro (`1_Entalhamento do Vale_ArcPRO.py`).
Na versão QGIS (`1_Entalhamento do Vale_QGIS.py`), a etapa de Fill/Flow
Direction/Sink/Basin foi reescrita como uma rotina única em
numpy/scipy/scikit-image (em vez de encadear ferramentas SAGA/GRASS do
QGIS, cujos nomes e parâmetros variam entre versões) — como consequência,
a limpeza iterativa por Eliminate deixou de ser necessária: o método
usado ali (watershed) sempre atribui cada pixel a alguma zona/pico, sem
gerar fragmentos órfãos. Os detalhes dessa adaptação estão no cabeçalho
do próprio script.

Ao rodar `1_Entalhamento do Vale_QGIS.py` de fato em modo headless
(`python-qgis.bat`), apareceu mais um problema real, também corrigido:
as camadas vetoriais intermediárias (`a_limite_Proj` e
`a_limite_Proj_Buffer`) originalmente ficavam dentro de um único
GeoPackage compartilhado, endereçadas como
`Entalhamento.gpkg|layername=a_limite_Proj`. Nesse modo, o algoritmo
`processing` às vezes não interpreta essa sintaxe como "abrir o
GeoPackage existente e adicionar essa camada" — trata a string inteira
como nome literal de um datasource novo, e falha com
`sqlite3_open(...) failed: unable to open database file`. A correção
foi dar um `.gpkg` próprio para cada camada, em vez de várias camadas
dentro de um `.gpkg` compartilhado.

## Histórico

Ver o histórico de commits deste repositório para acompanhar mudanças ao
longo do tempo, em vez de duplicar arquivos com sufixos como `_v2`,
`_FINAL`, `_PRO`.
