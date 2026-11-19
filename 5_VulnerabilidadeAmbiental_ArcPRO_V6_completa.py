# -*- coding: utf-8 -*-
"""
5_Vulnerabilidade Ambiental
===========================
Convertido a partir do model completo "Modelo Geral_VulnerabilidadeV6" do
ModelBuilder (toolbox "1_Ferramentas Finais da Tese.tbx"; Figura 11 da
tese). Os parametros foram conferidos contra o script exportado
nativamente do ArcMap 10.3 ("5_VulnerabilidadeAmbiental_Arc103_v2.py",
Model > Export > To Python Script) e contra a descricao metodologica da
propria tese (Alex da Silva Sousa, 2024, Cap. 6.6.1 "Vulnerabilidade
Ambiental", p. 83-87; Tabelas 7 a 9, 14, 18 e 24; DOI:
10.11606/T.8.2024.tde-18022025-121027).

Este e o fluxo COMPLETO da tese: parte dos dados brutos (DEM, rasters dos
scripts 1 e 2, vetores de geologia, solos e clima, MapBiomas e o limite) e
chega aos tres produtos finais.

Metodologia (conforme a tese):

A Vulnerabilidade Ambiental (Crepani et al., 2001) e a MEDIA ARITMETICA,
pixel a pixel, de CINCO temas, cada um expresso como grau de
vulnerabilidade de 1,0 (mais estavel, pedogenese) a 3,0 (mais instavel,
morfogenese) - no model, MULTIPLICADO POR 10 (10 a 30):

    Relevo        (G + A + D) / 3: dissecacao = dimensao interfluvial
                  (Tab. 7), amplitude altimetrica = entalhamento do vale
                  (Tab. 8) e clinografia = declividade em % (Tab. 9)
    Geologia      mapa litologico com a vulnerabilidade de cada litotipo
                  (Tab. 10 / Tab. 52 da tese)
    Solos         mapa pedologico com a vulnerabilidade de cada classe
                  (Tab. 18)
    Clima         intensidade pluviometrica (Tab. 14) - WorldClim
    Uso da Terra  MapBiomas colecao 8, reclassificado pela Tabela 24

O resultado fica entre 10 e 30, mais os valores 70 (area urbana) e 90
(agua) nos produtos que sobrepoem essas classes.

Entradas (as mesmas do model completo):

  * DEM (mosaico.tif) - qualquer SRC; e a base do Relevo (declividade) e a
    GRADE DE REFERENCIA de todo o resto (SIRGAS 2000 geografico, ~30 m,
    interpolacao bilinear).
  * Entalhamento do Vale (h_entalhamento) e Dimensao Interfluvial Media
    (j_Dimensao): saidas dos scripts 1 e 2 (rasters CONTINUOS, em metros -
    nao os reclassificados). O script procura nos locais padrao e, se nao
    achar, pergunta.
  * Vetores de GEOLOGIA (campo "Vulnerabil"), SOLOS (campo "Vulne") e CLIMA
    (campo "Vulnerabilidade"), com a vulnerabilidade de 1,0 a 3,0 (agua = 9
    e urbano = 7 nos campos de geologia e solos). O script multiplica o
    campo por 10 (o "Calculate Field" do model) e mostra os valores
    distintos para voce conferir.
  * Uso e Cobertura da Terra (MapBiomas): um raster OU uma geodatabase/
    pasta com varios rasters (um por ano - o "Iterate Rasters" do model).
  * Limite vetorial da area de interesse (padrao: Estado de SP).

Etapas (mesma ordem do model):

  1. Limite -> SIRGAS 2000 geografico + buffer de 2 km (usado para recortar
     os vetores e o uso da terra, como no model).
  2. RELEVO: DEM -> SIRGAS 2000 (bilinear, 0,00027777778 graus) e
     declividade em % (Slope, PERCENT_RISE, fator Z 0,00000956). Entalhamento
     (Tab. 8), Dimensao Interfluvial (Tab. 7) e Declividade (Tab. 9) sao
     reclassificados em 21 classes (10 a 30) e o tema Relevo e a media dos
     tres -> rel_e2_Relevo. (No model: /10, media, x10 - equivalente.)
  3. GEOLOGIA, SOLOS e CLIMA: recorta pelo buffer, projeta, multiplica o
     campo por 10 e rasteriza na grade do relevo (Feature to Raster) ->
     geol_d2_Rochas, ped_d2_solos, cli_c_clima. Valores que saem da media
     viram NoData: agua (90) na geologia; urbano (70) e agua (90) nos solos
     (a tese, p. 85, explica o motivo).
  4. Vulnerabilidade SEM o uso da terra (so fatores naturais):
     Cell Statistics MEAN de Relevo, Geologia, Solos e Clima, ignorando
     NoData -> h_Vuln_CellStatisticNoDataGRSC_noLanduse (GRSC = Geologia,
     Relevo, Solos, Clima).
  5. Para CADA raster de Uso e Cobertura da Terra (um por ano):
       a) reprojeta para SIRGAS 2000, recorta pelo buffer e reclassifica
          para vulnerabilidade (Tabela 24 x 10; urbano = 70; agua = 90;
          0 sem informacao = NoData);
       b) versao "NoData": urbano e agua viram NoData no uso e a media
          (Cell Statistics MEAN, ignorando NoData) dos cinco temas e feita
          -> h_Vuln_CellStatisticNoData_<nome>. Onde o uso e urbano/agua
          a media sai so dos outros quatro temas;
       c) versao "mascara": urbano (70) e agua (90) sao SOBREPOSTOS ao
          resultado anterior (era o Mosaic To New Raster, FIRST) ->
          h_Vuln_CellStatisticNoDataUrbAgua_<nome>. Permite estudar, por
          exemplo, em que niveis de vulnerabilidade avanca a area urbana.
     Os dois resultados de cada ano sao recortados pelo limite exato.

Observacoes:
  * Reclassify do relevo: as faixas (Tabelas 7, 8 e 9) sao identicas as do
    model exportado - cada faixa vai de [limite anterior, limite seguinte).
  * Declividade: usa arcpy.sa.Slope (Spatial Analyst) em vez do
    Slope_3d do model - mesmo calculo, sem precisar da extensao 3D Analyst.
  * Classes de uso que NAO estao na Tabela 24 viram NoData (o script
    avisa), em vez de manter o codigo original (comportamento do
    Reclassify do model com "DATA", que deixaria o numero da classe
    entrando na media).
  * Aquicultura (31) recebe 3,0 (30) como na Tabela 24 e no model - ao
    contrario do script de Fragilidade, onde 31 = agua (90). Apenas a
    classe 33 (rio, lago e oceano) vira 90 aqui.
  * O produto "sem uso da terra" (GRSC) e recortado pelo limite exato; no
    model exportado esse recorte final nao existia (so os demais).
  * A grade de referencia e a do DEM projetado; o Entalhamento e a
    Dimensao Interfluvial (que vem dos scripts 1 e 2) sao reamostrados
    para ela por vizinho mais proximo.

Requisitos: ArcGIS Pro com a extensao Spatial Analyst licenciada.

Como rodar: basta executar o script. Ele pergunta na tela o DEM, os
rasters dos scripts 1 e 2 (se nao os achar sozinho), os tres vetores, o
uso da terra (raster ou geodatabase/pasta) e o limite da area de
interesse.
"""
import os
import arcpy
from arcpy.sa import (Abs, CellStatistics, Con, ExtractByMask, Float, IsNull,
                      Raster, Reclassify, RemapRange, RemapValue, SetNull, Slope)

# ------------------------------------------------------------------
# PARAMETROS - ajuste para o seu ambiente
# ------------------------------------------------------------------
# Geodatabase de trabalho: todas as saidas sao gravadas aqui. Se ela
# ainda nao existir, o script cria automaticamente.
WORKSPACE = r"C:\alexgeopro\VulnerabilidadeAmbiental.gdb"

# Saidas dos scripts 1 e 2 (procuradas automaticamente; se nao existirem,
# o script pergunta o caminho na tela).
ENTALHAMENTO_PADRAO = r"C:\alexgeopro\Entalhamento.gdb\h_entalhamento"
DIMENSAO_PADRAO = r"C:\alexgeopro\DimensaoInterfluvial.gdb\j_Dimensao"

CELL_SIZE = 0.00027777778   # ~30 m em graus (a mesma do model: "0,00027777778")
EPSG_SAIDA = 4674           # SIRGAS 2000 Geografico
BUFFER_METROS = 2000        # folga usada para recortar vetores e uso da terra
TRANSFORMACAO_PADRAO = "SIRGAS_2000_To_WGS_1984_1"  # a mesma usada no model

# Declividade: fator Z do model (Slope, PERCENT_RISE, "0,00000956"). Como o
# DEM esta em graus e a altitude em metros, 1 / 0,00000956 = 104.603 m por
# grau (valor proximo do comprimento de 1 grau de latitude/longitude na
# latitude de Sao Paulo).
Z_FACTOR = 0.00000956

# Campos de vulnerabilidade (1,0 a 3,0; agua = 9, urbano = 7) dos vetores
# de geologia, solos e clima - o script multiplica por 10 (o "Calculate
# Field" do model). Se o campo do seu dado tem outro nome, ajuste aqui.
CAMPO_GEOLOGIA = "Vulnerabil"
CAMPO_SOLOS = "Vulne"
CAMPO_CLIMA = "Vulnerabilidade"

# Limites das classes (Tabelas 8, 7 e 9 da tese), exatamente como nos
# "Reclassify" do model: cada classe vai de [limite anterior, limite
# seguinte). Sao 21 classes de vulnerabilidade, de 10 (1,0) a 30 (3,0).
#   Entalhamento do Vale (m)  -> Tabela 8 - quanto maior, mais vulneravel
LIMITES_ENTALHAMENTO = [
    20, 29.5, 39, 48.5, 58, 67.5, 77, 84.5, 94, 103.5, 113, 122.5, 132,
    141.5, 151, 160.5, 170, 179.5, 189, 200,
]
#   Dimensao Interfluvial Media (m) -> Tabela 7 - quanto MENOR, mais vulneravel
LIMITES_DIMENSAO = [
    250, 500, 750, 1000, 1250, 1500, 1750, 2000, 2250, 2500, 2750, 3000,
    3250, 3500, 3750, 4000, 4250, 4500, 4750, 5000,
]
#   Declividade (%)           -> Tabela 9 - quanto maior, mais vulneravel
LIMITES_DECLIVIDADE = [
    2, 3.3, 4.6, 5.9, 7.3, 8.6, 9.9, 11.2, 12.5, 13.8, 15.2, 16.5, 17.8,
    19.1, 20.4, 21.7, 23, 24.4, 25.7, 27,
]


def montar_faixas(limites, inicio, fim, crescente):
    """Tabela de faixas do Reclassify: [[de, ate, classe], ...] com 21
    classes (10 a 30). 'inicio' e 'fim' sao os extremos usados no model."""
    bordas = [inicio] + limites + [fim]
    classes = range(10, 31) if crescente else range(30, 9, -1)
    return [[bordas[i], bordas[i + 1], c] for i, c in enumerate(classes)]


REMAP_ENTALHAMENTO = montar_faixas(LIMITES_ENTALHAMENTO, -5000, 5000, True)
REMAP_DIMENSAO = montar_faixas(LIMITES_DIMENSAO, -5000, 200000, False)
REMAP_DECLIVIDADE = montar_faixas(LIMITES_DECLIVIDADE, -5000, 2000, True)

# Filtro opcional: se o dado de uso da terra for uma pasta/geodatabase com
# varios rasters, so processa os que contem este texto no nome ("" = todos).
FILTRO_NOME_USO = ""

# False: se os resultados ja existirem na geodatabase, pula essa etapa
# (permite retomar uma execucao interrompida e reaproveitar o Relevo,
# Solos, Geologia e Clima ja calculados). True: refaz tudo.
SOBRESCREVER = False

# False: apaga os intermediarios (DEM projetado, declividade, vetores
# recortados/projetados, rasters de cada ano de uso da terra) ao terminar.
# Os quatro temas (rel_e2_Relevo, geol_d2_Rochas, ped_d2_solos,
# cli_c_clima) e os tres produtos finais sao sempre mantidos.
MANTER_INTERMEDIARIOS = False

# Reclassificacao do uso da terra: codigo MapBiomas (colecao 8) ->
# vulnerabilidade x 10 (Tabela 24 da tese; 24 urbano = 70; 33 agua = 90;
# 0 sem informacao = NoData), exatamente como no model exportado.
REMAP_USO = [
    [0, "NODATA"], [3, 16], [4, 21], [5, 14], [9, 29], [11, 30], [12, 27],
    [13, 30], [15, 28], [19, 30], [20, 30], [21, 30], [23, 30], [24, 70],
    [25, 30], [29, 30], [30, 30], [31, 30], [32, 30], [33, 90], [39, 30],
    [41, 30], [46, 29], [47, 29], [48, 29], [49, 14], [50, 27], [62, 30],
]
CLASSES_USO_CONHECIDAS = {origem for origem, _ in REMAP_USO}
URBANO = 70
AGUA = 90

# Urbano/agua saem da media (viram NoData) e voltam como mascara depois.
REMAP_SO_VEGETACAO = [
    [14, 14], [16, 16], [21, 21], [27, 27], [28, 28], [29, 29], [30, 30],
    [70, "NODATA"], [90, "NODATA"],
]
REMAP_SO_URBANO_AGUA = [[70, 70], [90, 90]]

# Saidas fixas (as de uso da terra levam o nome do raster de origem).
# Os nomes seguem os do model.
LIM_A_SIRGAS = os.path.join(WORKSPACE, "lim_a_LimiteSirgas")
LIM_B_BUFFER = os.path.join(WORKSPACE, "lim_b_Limite_Buffer2Km")
REL_A_MOSAICO = os.path.join(WORKSPACE, "rel_a_mosaico")               # DEM projetado
REL_B_SLOPE = os.path.join(WORKSPACE, "rel_b_slope")                   # declividade (%)
REL_E2_RELEVO = os.path.join(WORKSPACE, "rel_e2_Relevo")               # tema Relevo (x10)
GEOL_D2_ROCHAS = os.path.join(WORKSPACE, "geol_d2_Rochas")             # tema Geologia (x10)
PED_D2_SOLOS = os.path.join(WORKSPACE, "ped_d2_solos")                 # tema Solos (x10)
CLI_C_CLIMA = os.path.join(WORKSPACE, "cli_c_clima")                   # tema Clima (x10)
H_SEM_USO = os.path.join(WORKSPACE, "h_Vuln_CellStatisticNoDataGRSC_noLanduse")

# Intermediarios de cada tema vetorial: (recorte, projetado, raster bruto)
INTERMEDIARIOS_GEOL = tuple(os.path.join(WORKSPACE, n) for n in
                            ("geol_a_Geologico", "geol_b_Geologico_Project", "geol_c_Geologico_Project"))
INTERMEDIARIOS_SOLOS = tuple(os.path.join(WORKSPACE, n) for n in
                             ("ped_a_solos", "ped_b_solos", "ped_c_solos"))
INTERMEDIARIOS_CLIMA = tuple(os.path.join(WORKSPACE, n) for n in
                             ("cli_a_clima", "cli_b_clima", "cli_c_clima_raster"))


# ------------------------------------------------------------------
# Funcoes auxiliares
# ------------------------------------------------------------------
def preparar_workspace(caminho_gdb):
    """Cria a geodatabase de trabalho (e a pasta que a contem, se
    necessario), caso ainda nao existam."""
    pasta = os.path.dirname(caminho_gdb)
    nome_gdb = os.path.basename(caminho_gdb)

    if pasta and not os.path.isdir(pasta):
        print(f"Criando pasta '{pasta}'...")
        os.makedirs(pasta)

    if not arcpy.Exists(caminho_gdb):
        print(f"Geodatabase '{caminho_gdb}' nao encontrada - criando...")
        arcpy.management.CreateFileGDB(pasta, nome_gdb)
    else:
        print(f"Geodatabase '{caminho_gdb}' ja existe - usando a existente.")


def abre_como(caminho, tipo):
    """True se o dado existir e for do tipo esperado (raster,
    pasta_ou_raster ou vetor)."""
    if not arcpy.Exists(caminho):
        return False
    if tipo == "pasta_ou_raster":
        return True
    tipo_dado = arcpy.Describe(caminho).dataType
    if tipo == "raster":
        return tipo_dado in ("RasterDataset", "RasterLayer")
    return tipo_dado in ("FeatureClass", "ShapeFile", "FeatureLayer")


def pedir_caminho(mensagem, tipo):
    """Pergunta um caminho ao usuario e so aceita quando o dado existir
    nesse caminho e for do tipo esperado."""
    while True:
        caminho = input(mensagem).strip().strip('"')
        if not caminho:
            print("  -> Caminho vazio, tente novamente.")
            continue
        if abre_como(caminho, tipo):
            return caminho
        print(f"  -> Nao encontrei '{caminho}' como {tipo}. Confira o caminho e tente de novo.")


def achar_ou_pedir_caminho(caminho_padrao, descricao, tipo):
    """Tenta usar automaticamente o caminho padrao (saida dos scripts 1/2);
    se nao existir, pergunta o caminho na tela."""
    if abre_como(caminho_padrao, tipo):
        print(f"  {descricao}: encontrado automaticamente em '{caminho_padrao}'.")
        return caminho_padrao
    print(f"  {descricao}: nao encontrei em '{caminho_padrao}'.")
    return pedir_caminho(f"  Informe o caminho de {descricao}: ", tipo)


def escolher_transformacao(sr_origem, sr_destino):
    """Escolhe a transformacao geografica entre dois sistemas: a mesma do
    model (SIRGAS_2000_To_WGS_1984_1) quando ela se aplica, senao a
    primeira que o ArcGIS recomendar (ou nenhuma)."""
    try:
        lista = arcpy.ListTransformations(sr_origem, sr_destino)
    except Exception:
        lista = []
    if TRANSFORMACAO_PADRAO in lista:
        return TRANSFORMACAO_PADRAO
    return lista[0] if lista else ""


def projetar_vetor(entrada, saida, sr_alvo):
    """Reprojeta um vetor para o SRC alvo (SIRGAS 2000 geografico). Se ele
    ja estiver nesse SRC, so copia."""
    sr_in = arcpy.Describe(entrada).spatialReference
    if sr_in.factoryCode == sr_alvo.factoryCode:
        arcpy.management.CopyFeatures(entrada, saida)
    else:
        arcpy.management.Project(entrada, saida, sr_alvo, escolher_transformacao(sr_in, sr_alvo))


def projetar_raster(entrada, saida, sr_alvo):
    """Reprojeta um raster de classes/valores (vizinho mais proximo) para o
    SRC alvo. Mantem a resolucao nativa quando o dado ja e geografico. Se o
    raster ja estiver no SRC alvo, devolve o proprio raster."""
    desc = arcpy.Describe(entrada)
    sr_in = desc.spatialReference
    if sr_in.factoryCode == sr_alvo.factoryCode:
        return entrada
    celula = desc.meanCellWidth if sr_in.type == "Geographic" else CELL_SIZE
    arcpy.management.ProjectRaster(
        entrada, saida, sr_alvo, "NEAREST", celula, escolher_transformacao(sr_in, sr_alvo)
    )
    return saida


def listar_rasters_uso(caminho):
    """Devolve a lista de rasters de uso da terra: o proprio dado, se for
    um raster; ou todos os rasters de uma geodatabase/pasta (o 'Iterate
    Rasters' do model)."""
    tipo = arcpy.Describe(caminho).dataType
    if tipo in ("RasterDataset", "RasterLayer"):
        return [caminho]
    rasters = []
    for pasta, _, nomes in arcpy.da.Walk(caminho, datatype="RasterDataset"):
        for nome in nomes:
            if FILTRO_NOME_USO and FILTRO_NOME_USO not in nome:
                continue
            rasters.append(os.path.join(pasta, nome))
    return sorted(rasters)


def conferir_campo(rotulo, fc, campo):
    """Confere o campo de vulnerabilidade do vetor: devolve o nome real do
    campo (sem diferenciar maiusculas), mostra os valores distintos ja
    multiplicados por 10 e avisa se parecerem fora do esperado (10 a 30,
    mais 70/90). Interrompe se o campo nao existir."""
    nomes = [f.name for f in arcpy.ListFields(fc)]
    real = next((n for n in nomes if n.lower() == campo.lower()), None)
    if real is None:
        raise SystemExit(
            f"O vetor de {rotulo} nao tem o campo '{campo}'. Campos encontrados: {nomes}. "
            "Ajuste CAMPO_GEOLOGIA / CAMPO_SOLOS / CAMPO_CLIMA no topo do script."
        )
    valores = set()
    with arcpy.da.SearchCursor(fc, [real]) as cursor:
        for (v,) in cursor:
            if v is not None:
                try:
                    valores.add(round(float(v) * 10, 4))
                except (TypeError, ValueError):
                    pass
    valores = sorted(valores)
    print(f"  {rotulo}: campo '{real}', valores distintos (x10): "
          f"{[int(v) if v == int(v) else v for v in valores][:30]}")
    estranhos = [v for v in valores if not (10 <= v <= 30) and v not in (URBANO, AGUA)]
    if estranhos:
        print(f"    AVISO: valores fora de 10 a 30 (e de 70/90) em '{rotulo}': {estranhos[:10]}. "
              "O model espera a vulnerabilidade de 1,0 a 3,0 no campo (o script multiplica por 10) - "
              "se o campo ja estiver multiplicado por 10, divida-o por 10 antes.")
    return real


def resumo_tema(rotulo, caminho):
    """Mostra minimo/maximo do raster tematico e avisa se estiver fora do
    esperado (10 a 30)."""
    try:
        minimo = float(arcpy.management.GetRasterProperties(caminho, "MINIMUM").getOutput(0).replace(",", "."))
        maximo = float(arcpy.management.GetRasterProperties(caminho, "MAXIMUM").getOutput(0).replace(",", "."))
    except Exception:
        print(f"  {rotulo}: nao consegui calcular minimo/maximo.")
        return
    print(f"  {rotulo}: minimo {minimo:g}, maximo {maximo:g}")
    if maximo > 30.5 or minimo < 9.5:
        print(f"    AVISO: '{rotulo}' deveria ficar entre 10 e 30 - confira o dado de entrada.")


def apagar(*caminhos):
    for c in caminhos:
        if arcpy.Exists(c):
            arcpy.management.Delete(c)



def construir_relevo(dem, entalhamento, dimensao, sr_alvo):
    """Tema RELEVO: (Entalhamento + Dimensao Interfluvial + Declividade) / 3,
    x10 -> rel_e2_Relevo. A grade do DEM projetado e a referencia."""
    print("   DEM -> SIRGAS 2000 (bilinear) e declividade em %...")
    sr_dem = arcpy.Describe(dem).spatialReference
    arcpy.management.ProjectRaster(
        dem, REL_A_MOSAICO, sr_alvo, "BILINEAR", CELL_SIZE, escolher_transformacao(sr_dem, sr_alvo)
    )
    with arcpy.EnvManager(snapRaster=REL_A_MOSAICO, cellSize=REL_A_MOSAICO, resamplingMethod="NEAREST"):
        # Slope (PERCENT_RISE, fator Z) - Spatial Analyst, sem 3D Analyst
        Slope(REL_A_MOSAICO, "PERCENT_RISE", Z_FACTOR).save(REL_B_SLOPE)

        print("   Reclassificar entalhamento, dimensao e declividade (Tabelas 8, 7 e 9)...")
        c_ent = Reclassify(Raster(entalhamento), "VALUE", RemapRange(REMAP_ENTALHAMENTO), "DATA")
        c_dim = Reclassify(Raster(dimensao), "VALUE", RemapRange(REMAP_DIMENSAO), "DATA")
        c_decl = Reclassify(Raster(REL_B_SLOPE), "VALUE", RemapRange(REMAP_DECLIVIDADE), "DATA")

        # (G + A + D) / 3 - no model: cada classe /10, media, x10 (equivalente)
        ((Float(c_ent) + Float(c_dim) + Float(c_decl)) / 3).save(REL_E2_RELEVO)

    if not MANTER_INTERMEDIARIOS:
        apagar(REL_A_MOSAICO, REL_B_SLOPE)


def construir_tema_vetor(rotulo, vetor, campo, valores_excluidos, intermediarios, saida, sr_alvo):
    """Tema vindo de vetor (geologia, solos ou clima): recorta pelo buffer
    -> projeta -> campo x10 -> Feature to Raster na grade do relevo ->
    valores de 'valores_excluidos' viram NoData."""
    a_recorte, b_projetado, c_raster = intermediarios
    arcpy.analysis.Clip(vetor, LIM_B_BUFFER, a_recorte)
    projetar_vetor(a_recorte, b_projetado, sr_alvo)
    campo_real = conferir_campo(rotulo, b_projetado, campo)
    # Calculate Field: vulnerabilidade x 10
    arcpy.management.CalculateField(b_projetado, campo_real, f"!{campo_real}! * 10", "PYTHON3")
    extensao = arcpy.Describe(REL_E2_RELEVO).extent
    with arcpy.EnvManager(snapRaster=REL_E2_RELEVO, extent=extensao, cellSize=REL_E2_RELEVO):
        arcpy.conversion.FeatureToRaster(b_projetado, campo_real, c_raster, CELL_SIZE)
        bruto = Raster(c_raster)
        if valores_excluidos:
            # Reclassify do model: esses valores -> NoData; os demais ficam iguais
            condicao = Abs(bruto - valores_excluidos[0]) < 0.01
            for excluido in valores_excluidos[1:]:
                condicao = condicao | (Abs(bruto - excluido) < 0.01)
            SetNull(condicao, bruto).save(saida)
        else:
            bruto.save(saida)
    if not MANTER_INTERMEDIARIOS:
        apagar(a_recorte, b_projetado, c_raster)


# ------------------------------------------------------------------
# Programa principal
# ------------------------------------------------------------------
def main():
    preparar_workspace(WORKSPACE)

    arcpy.env.workspace = WORKSPACE
    arcpy.env.overwriteOutput = True
    arcpy.CheckOutExtension("Spatial")

    print()
    print("Informe os dados de entrada (os mesmos do model completo da tese).")
    dem = pedir_caminho("Caminho do DEM (ex.: C:\\dados\\mosaico.tif): ", "raster")
    entalhamento = achar_ou_pedir_caminho(
        ENTALHAMENTO_PADRAO, "Entalhamento do Vale (h_entalhamento, saida do script 1)", "raster")
    dimensao = achar_ou_pedir_caminho(
        DIMENSAO_PADRAO, "Dimensao Interfluvial Media (j_Dimensao, saida do script 2)", "raster")
    geologia = pedir_caminho(
        "Caminho do vetor de GEOLOGIA com a vulnerabilidade (campo 'Vulnerabil', ex.: "
        "C:\\dados\\GDB Final.gdb\\Vulnerabilidade_Final): ", "vetor")
    solos = pedir_caminho(
        "Caminho do vetor de SOLOS com a vulnerabilidade (campo 'Vulne', ex.: "
        "C:\\dados\\GDB Final.gdb\\PEDOLOGICO_SP_ROSSI_2017_V4): ", "vetor")
    clima = pedir_caminho(
        "Caminho do vetor de CLIMA com a vulnerabilidade (campo 'Vulnerabilidade', ex.: "
        "C:\\dados\\Final.gdb\\Vuln_wc21_30s_Brasil): ", "vetor")
    uso_terra = pedir_caminho(
        "Caminho do Uso e Cobertura da Terra (um raster OU uma geodatabase/pasta com um raster por ano, "
        "ex.: C:\\dados\\Mapbiomas8_SP.gdb): ", "pasta_ou_raster"
    )
    limite = pedir_caminho(
        "Caminho do limite vetorial da area de interesse (padrao: limite do Estado de SP, "
        "ex.: C:\\dados\\EstadoSP_2023.shp): ", "vetor"
    )
    print()

    rasters_uso = listar_rasters_uso(uso_terra)
    if not rasters_uso:
        raise SystemExit(f"Nenhum raster de uso da terra encontrado em '{uso_terra}'.")
    print(f"{len(rasters_uso)} raster(s) de uso da terra a processar.")
    print()

    sr_alvo = arcpy.SpatialReference(EPSG_SAIDA)

    try:
        # 1. Limite -> SIRGAS 2000 + buffer ---------------------------------------
        print("1/5 - Limite da area: SIRGAS 2000 + buffer de 2 km...")
        projetar_vetor(limite, LIM_A_SIRGAS, sr_alvo)
        # GEODESIC: o buffer e em metros sobre dado geografico (o model usava
        # PLANAR). Dissolve "ALL" evita feicoes sobrepostas no recorte.
        arcpy.analysis.Buffer(LIM_A_SIRGAS, LIM_B_BUFFER, f"{BUFFER_METROS} Meters",
                              "FULL", "ROUND", "ALL", "", "GEODESIC")

        # 2. Relevo ----------------------------------------------------------------
        print("2/5 - Tema RELEVO: (entalhamento + dimensao interfluvial + declividade) / 3 ...")
        if arcpy.Exists(REL_E2_RELEVO) and not SOBRESCREVER:
            print("   rel_e2_Relevo ja existe - usando o existente (SOBRESCREVER = True refaz).")
        else:
            construir_relevo(dem, entalhamento, dimensao, sr_alvo)

        # 3. Geologia, solos e clima (vetores) ----------------------------------------
        print("3/5 - Temas GEOLOGIA, SOLOS e CLIMA: vetor -> raster na grade do relevo...")
        temas_vetor = (
            ("Geologia", geologia, CAMPO_GEOLOGIA, [AGUA], INTERMEDIARIOS_GEOL, GEOL_D2_ROCHAS),
            ("Solos", solos, CAMPO_SOLOS, [URBANO, AGUA], INTERMEDIARIOS_SOLOS, PED_D2_SOLOS),
            ("Clima", clima, CAMPO_CLIMA, [], INTERMEDIARIOS_CLIMA, CLI_C_CLIMA),
        )
        for rotulo, vetor, campo, excluidos, intermediarios, saida in temas_vetor:
            if arcpy.Exists(saida) and not SOBRESCREVER:
                print(f"   {rotulo}: {os.path.basename(saida)} ja existe - usando o existente.")
                continue
            construir_tema_vetor(rotulo, vetor, campo, excluidos, intermediarios, saida, sr_alvo)
        print("   Conferencia dos quatro temas (devem ficar entre 10 e 30):")
        for rotulo, caminho in (("Relevo", REL_E2_RELEVO), ("Geologia", GEOL_D2_ROCHAS),
                                ("Solos", PED_D2_SOLOS), ("Clima", CLI_C_CLIMA)):
            resumo_tema(rotulo, caminho)
        temas = [REL_E2_RELEVO, GEOL_D2_ROCHAS, PED_D2_SOLOS, CLI_C_CLIMA]

        # Tudo abaixo e alinhado a grade do raster de relevo (vizinho mais proximo)
        with arcpy.EnvManager(snapRaster=REL_E2_RELEVO, cellSize=REL_E2_RELEVO, resamplingMethod="NEAREST"):
            # 4. Vulnerabilidade SEM o uso da terra -----------------------------------
            print("4/5 - Vulnerabilidade sem o uso da terra (media de Relevo, Geologia, Solos e Clima)...")
            media_natural = CellStatistics(temas, "MEAN", "DATA")
            ExtractByMask(media_natural, LIM_A_SIRGAS).save(H_SEM_USO)

            # 5. Uso e cobertura da terra - um resultado por raster ---------------------
            print(f"5/5 - Uso e Cobertura da Terra ({len(rasters_uso)} raster(s))...")
            resultados = []
            for i, uso_original in enumerate(rasters_uso, start=1):
                nome = arcpy.ValidateTableName(
                    os.path.splitext(os.path.basename(uso_original))[0], WORKSPACE
                )
                saida_nodata = os.path.join(WORKSPACE, f"h_Vuln_CellStatisticNoData_{nome}")
                saida_mascara = os.path.join(WORKSPACE, f"h_Vuln_CellStatisticNoDataUrbAgua_{nome}")
                print(f"  [{i}/{len(rasters_uso)}] {nome} ...", end=" ")

                if arcpy.Exists(saida_nodata) and arcpy.Exists(saida_mascara) and not SOBRESCREVER:
                    print("ja existem - pulando.")
                    resultados.append((saida_nodata, saida_mascara))
                    continue

                uso_a = os.path.join(WORKSPACE, f"uso_a_{nome}_Project")
                uso_b = os.path.join(WORKSPACE, f"uso_b_{nome}_Extract")
                uso_c = os.path.join(WORKSPACE, f"uso_c_{nome}_UsoSoloVulne")
                uso_c2 = os.path.join(WORKSPACE, f"uso_c2_{nome}_UsoSoloVulne")
                uso_c3 = os.path.join(WORKSPACE, f"uso_c3_{nome}_UsoSoloVulne_UrbAgua")
                f_media = os.path.join(WORKSPACE, f"f_{nome}_Vuln_CellStatisticNoData")
                g_mosaico = os.path.join(WORKSPACE, f"G_{nome}_Vuln_UrbAgua")

                # Project Raster -> Extract by Mask (buffer)
                uso_proj = projetar_raster(uso_original, uso_a, sr_alvo)
                ExtractByMask(Raster(uso_proj), LIM_B_BUFFER).save(uso_b)

                # Aviso: classes que nao estao na Tabela 24 viram NoData
                valores = {r[0] for r in arcpy.da.SearchCursor(uso_b, ["Value"])} \
                    if Raster(uso_b).hasRAT else set()
                desconhecidas = sorted(v for v in valores if v not in CLASSES_USO_CONHECIDAS)
                if desconhecidas:
                    print(f"\n    AVISO: classes fora da Tabela 24 (viram NoData): {desconhecidas}", end=" ")

                # Reclassify (5): MapBiomas -> vulnerabilidade x 10
                Reclassify(Raster(uso_b), "VALUE", RemapValue(REMAP_USO), "NODATA").save(uso_c)
                # Reclassify (8): urbano e agua -> NoData (saem da media)
                Reclassify(Raster(uso_c), "VALUE", RemapValue(REMAP_SO_VEGETACAO), "DATA").save(uso_c2)
                # Reclassify (6): so urbano e agua (a "mascara")
                Reclassify(Raster(uso_c), "VALUE", RemapValue(REMAP_SO_URBANO_AGUA), "NODATA").save(uso_c3)

                # Cell Statistics (2): media dos cinco temas, ignorando NoData
                CellStatistics([uso_c2] + temas, "MEAN", "DATA").save(f_media)
                ExtractByMask(Raster(f_media), LIM_A_SIRGAS).save(saida_nodata)

                # Mosaic To New Raster (FIRST): urbano/agua por cima da media
                Con(IsNull(Raster(uso_c3)), Raster(f_media), Raster(uso_c3)).save(g_mosaico)
                ExtractByMask(Raster(g_mosaico), LIM_A_SIRGAS).save(saida_mascara)

                if not MANTER_INTERMEDIARIOS:
                    apagar(uso_a, uso_b, uso_c, uso_c2, uso_c3, f_media, g_mosaico)
                resultados.append((saida_nodata, saida_mascara))
                print("ok.")

        print()
        print("Concluido.")
        print("Temas (vulnerabilidade x 10):")
        for caminho in temas:
            print("  ", caminho)
        print("Vulnerabilidade sem o uso da terra (Relevo, Geologia, Solos, Clima):", H_SEM_USO)
        print("Vulnerabilidade Ambiental por uso da terra (NoData = urbano/agua fora da media | MASCARA = urbano 70 e agua 90 por cima):")
        for sem_mascara, com_mascara in resultados:
            print("  ", sem_mascara)
            print("  ", com_mascara)

    finally:
        arcpy.CheckInExtension("Spatial")


if __name__ == "__main__":
    main()
