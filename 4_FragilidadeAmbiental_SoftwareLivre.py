# -*- coding: utf-8 -*-
"""
4_Fragilidade Ambiental - versao software livre SEM QGIS (Python + GDAL/OGR)
=============================================================================
Mesma metodologia do script "4_fragilidade_ambiental.py" (ArcGIS Pro /
arcpy) e do "4_fragilidade_ambiental_QGIS.py" (QGIS + Python) - ver aquele
arquivo para a descricao completa da metodologia e as fontes conferidas:
script exportado do ArcMap 10.3 ("4_FragilidadeAmbiental_Arc103.py"), a
Tabela 24 (Cap. 6.5) e o Cap. 6.6.2 da tese (Alex da Silva Sousa, 2024,
DOI: 10.11606/T.8.2024.tde-18022025-121027).

Resumo: a Fragilidade Ambiental e uma matriz de QUATRO algarismos obtida
SOMANDO, pixel a pixel, quatro rasters tematicos:

    milhar   -> Relevo (Grau de Dissecacao reclassificado)    1000 a 5000
    centena  -> Solos (campo "Frag" x 100)                     100 a  500
    dezena   -> Uso e Cobertura da Terra (MapBiomas, Tab. 24)   10 a   50
    unidade  -> Clima (campo "Fragilidade", WorldClim)           1 a    5

1111 = menor fragilidade possivel; 5555 = maior. Urbano = algarismo 7 e
agua = algarismo 9 (ja vem dos dados de entrada e da tabela de uso).
Apenas o dado climatico do WorldClim (vetor ja classificado) e usado aqui.

Diferencas em relacao a versao ArcGIS/arcpy:

  * Em vez de ferramentas separadas (Project, Buffer, Clip, Feature to
    Raster, Extract by Mask, Raster Calculator), cada dado de entrada e
    levado DIRETO para a grade do raster de relevo (o Grau de Dissecacao
    do script 3): os vetores de solo e clima sao reprojetados e
    rasterizados (gdal.Rasterize) nessa grade, e cada raster de uso da
    terra e reprojetado/reamostrado (vizinho mais proximo - dado de
    classes, nao pode interpolar) nessa mesma grade com gdal.Warp. Como a
    propria grade ja limita a area, o buffer de 2 km e o recorte
    intermediario do model deixam de ser necessarios - o resultado dentro
    do limite e equivalente. No fim, o resultado e mascarado pelo
    contorno exato do limite da area (cutline).
  * As somas sao feitas em blocos de linhas (nao carrega o Estado inteiro
    na memoria), e a reclassificacao do uso da terra e feita na hora da
    soma (o raster "uso_c ... Fragil" do model nao e gravado).
  * Classes de uso fora da Tabela 24 viram NoData (o script avisa).
  * Se o raster de uso da terra declarar o valor 0 como NoData (comum em
    GeoTIFFs do MapBiomas), o GDAL o trata como NoData, e nao como a classe
    "0 - sem informacao" (que o model reclassificava para 90).

Entradas:
  * Grau de Dissecacao - Fragilidade (saida do script 3, versao sem QGIS,
    local padrao abaixo - ou informe o caminho na tela).
  * Mapa pedologico (vetor com campo "Frag").
  * Vetor climatico ja classificado (WorldClim, campo "Fragilidade").
  * Uso e Cobertura da Terra: um raster (GeoTIFF etc.) OU uma pasta com
    varios rasters (um por ano - o "Iterate Rasters" do model). O GDAL nao
    le raster dentro de geodatabase (.gdb): se o MapBiomas esta numa .gdb,
    exporte antes cada raster para GeoTIFF (no ArcGIS Pro: Copy Raster).
  * Limite vetorial da area de interesse.
  Vetores em .gdb tambem funcionam (ex.: C:\\dados\\GDB Final.gdb\\Camada).

Requisitos (nenhum deles precisa do QGIS instalado):
    - Python 3.x com os pacotes: gdal (osgeo), numpy
    - Instalacao mais simples: usando conda -
          conda install -c conda-forge gdal numpy

Como rodar:
    python 4_fragilidade_ambiental_sem_qgis.py
"""
import glob
import os

import numpy as np
from osgeo import gdal, ogr, osr

gdal.UseExceptions()
ogr.UseExceptions()

# ------------------------------------------------------------------
# PARAMETROS - ajuste para o seu ambiente
# ------------------------------------------------------------------
WORKSPACE = r"C:\alexgeopro\FragilidadeAmbiental_SemQGIS"  # pasta - criada automaticamente

CELL_SIZE = 0.00027777778   # ~30 m em graus (usada so se o relevo precisar ser reprojetado)
EPSG_SAIDA = 4674           # SIRGAS 2000 Geografico
EPSG_USO_ENTRADA_PADRAO = 4326  # usado so se o raster de uso nao tiver SRC definido
NODATA = -9999
CAMPO_SOLO = "Frag"         # campo de fragilidade (1-5, 7 urbano, 9 agua) no vetor de solos
CAMPO_CLIMA = "Fragilidade" # campo de fragilidade (1-5) no vetor climatico
LINHAS_BLOCO = 1024         # linhas lidas de cada vez nas somas (reduza se faltar memoria)

# Local padrao onde a versao "_sem_qgis" do script 3 grava o Grau de
# Dissecacao de Fragilidade - usado automaticamente quando existir.
GRAU_DISSECACAO_PADRAO = r"C:\alexgeopro\GrauDeDissecacao_SemQGIS\b_GrauDeDissecacao_Fragilidade.tif"

# Filtro opcional: se o uso da terra for uma pasta com varios rasters, so
# processa os que contem este texto no nome ("" = todos).
FILTRO_NOME_USO = ""
EXTENSOES_RASTER_USO = ("*.tif", "*.tiff", "*.vrt", "*.img")

# False: se o resultado de um ano ja existir, pula esse ano (permite
# retomar uma execucao interrompida). True: refaz tudo.
SOBRESCREVER = False

# False: apaga o raster de uso reprojetado de cada ano ao terminar o ano.
MANTER_INTERMEDIARIOS = False

# Reclassificacao do relevo: Grau de Dissecacao (dezena = classe do
# entalhamento, unidade = classe da dimensao interfluvial) -> fragilidade
# do relevo no milhar (Tabela 2 da tese / Ross 2012).
REMAP_RELEVO = {
    11: 1000, 12: 2000, 13: 3000, 14: 4000, 15: 5000,
    21: 2000, 22: 2000, 23: 3000, 24: 4000, 25: 5000,
    31: 3000, 32: 3000, 33: 3000, 34: 4000, 35: 5000,
    41: 4000, 42: 4000, 43: 4000, 44: 4000, 45: 5000,
    51: 5000, 52: 5000, 53: 5000, 54: 5000, 55: 5000,
}

# Reclassificacao do uso da terra: codigo MapBiomas (colecao 8) ->
# fragilidade na dezena (Tabela 24 da tese x 10; 24 urbano = 70;
# 31/33 agua = 90; 0 sem informacao = 90, como no model).
REMAP_USO = {
    0: 90, 3: 10, 4: 20, 5: 10, 9: 30, 11: 50, 12: 20, 13: 50, 15: 30,
    19: 50, 20: 40, 21: 50, 23: 50, 24: 70, 25: 50, 29: 50, 30: 50,
    31: 90, 32: 50, 33: 90, 39: 40, 41: 50, 46: 30, 47: 30, 48: 40,
    49: 10, 50: 20, 62: 40,
}

# Saidas fixas (as de uso da terra levam o nome do raster de origem)
GPKG_LIMITE = os.path.join(WORKSPACE, "lim_a_LimiteSirgas.gpkg")
GPKG_SOLO = os.path.join(WORKSPACE, "ped_a_PEDOLOGICO_SIRGAS.gpkg")
GPKG_CLIMA = os.path.join(WORKSPACE, "cli_a_Clima_Project.gpkg")
NOME_CAMADA = "camada"  # nome da camada dentro de cada GPKG (um GPKG por camada)

REL_A_GRAU = os.path.join(WORKSPACE, "rel_a_grau_dissecacao.tif")      # so se precisar reprojetar
REL_B_FRAGIL = os.path.join(WORKSPACE, "rel_b_RelevoFragil.tif")
PED_C_RASTER = os.path.join(WORKSPACE, "ped_c_PedRaster.tif")
PED_D_FRAGIL = os.path.join(WORKSPACE, "ped_d_SolosFragil.tif")
CLI_C_FRAGIL = os.path.join(WORKSPACE, "cli_c_ClimaFragil.tif")
A_FRAGILIDADE_FINAL = os.path.join(WORKSPACE, "a_FragilidadeFinal.tif")

OPCOES_TIF = ["COMPRESS=LZW", "TILED=YES"]


# ------------------------------------------------------------------
# Funcoes auxiliares - GDAL/OGR puro (sem QGIS)
# ------------------------------------------------------------------
def garantir_pasta(caminho):
    if not os.path.isdir(caminho):
        print(f"Criando pasta '{caminho}'...")
        os.makedirs(caminho)


def srs_de_epsg(epsg):
    """Cria um osr.SpatialReference a partir de um codigo EPSG, forcando
    a ordem tradicional de eixos (long, lat / x, y) - evita o bug
    classico do GDAL 3+ de inverter a ordem dos eixos em SRCs
    geograficos."""
    srs = osr.SpatialReference()
    srs.ImportFromEPSG(epsg)
    srs.SetAxisMappingStrategy(osr.OAMS_TRADITIONAL_GIS_ORDER)
    return srs


def separar_gdb(caminho):
    """Permite usar camadas de uma File Geodatabase pelo caminho do
    ArcGIS (ex.: C:\\dados\\GDB Final.gdb\\Camada). Devolve
    (caminho_da_fonte, nome_da_camada_ou_None)."""
    minusculo = caminho.lower()
    pos = minusculo.find(".gdb")
    if pos == -1:
        return caminho, None
    fim = pos + len(".gdb")
    fonte = caminho[:fim]
    resto = caminho[fim:].strip("\\/")
    return fonte, (resto or None)


def abrir_camada_vetor(caminho):
    """Abre um vetor (shapefile, GPKG, camada de .gdb...) e devolve
    (datasource, camada). Mantenha a referencia ao datasource enquanto
    usar a camada."""
    fonte, nome = separar_gdb(caminho)
    ds = ogr.Open(fonte)
    if ds is None:
        raise RuntimeError(f"Nao consegui abrir '{caminho}'.")
    camada = ds.GetLayerByName(nome) if nome else ds.GetLayer(0)
    if camada is None:
        raise RuntimeError(f"Camada '{nome}' nao encontrada em '{fonte}'.")
    return ds, camada


def resolver_campo(caminho, campo):
    """Procura o campo no vetor sem diferenciar maiusculas/minusculas.
    Devolve o nome real do campo ou None."""
    ds, camada = abrir_camada_vetor(caminho)
    definicao = camada.GetLayerDefn()
    nomes = [definicao.GetFieldDefn(i).GetName() for i in range(definicao.GetFieldCount())]
    ds = None
    for nome in nomes:
        if nome.lower() == campo.lower():
            return nome
    return None


def pedir_caminho(mensagem, tipo):
    """Pergunta um caminho (raster ou vetor) e so aceita quando o GDAL/OGR
    conseguir realmente abrir o dado."""
    while True:
        caminho = input(mensagem).strip().strip('"')
        if not caminho:
            print("  -> Caminho vazio, tente novamente.")
            continue
        try:
            if tipo == "raster":
                ds = gdal.Open(caminho)
            elif tipo == "pasta_ou_raster":
                ds = True if os.path.isdir(caminho) else gdal.Open(caminho)
            else:
                ds, _ = abrir_camada_vetor(caminho)
        except (RuntimeError, ValueError):
            ds = None
        if ds is not None:
            ds = None
            return caminho
        print(f"  -> Nao consegui abrir '{caminho}' como {tipo}. Confira o caminho e tente de novo.")


def pedir_vetor_com_campo(mensagem, campo):
    """Pede um vetor e confere se ele tem o campo de fragilidade.
    Devolve (caminho, nome_real_do_campo)."""
    while True:
        caminho = pedir_caminho(mensagem, "vetor")
        nome_real = resolver_campo(caminho, campo)
        if nome_real:
            return caminho, nome_real
        print(f"  -> '{caminho}' nao tem o campo '{campo}'. Confira e tente de novo.")


def achar_ou_pedir_caminho(caminho_padrao, descricao):
    """Tenta usar automaticamente o caminho padrao (saida do script 3,
    versao "_sem_qgis"); se nao existir/abrir, pergunta o caminho."""
    try:
        ds = gdal.Open(caminho_padrao)
    except RuntimeError:
        ds = None
    if ds is not None:
        ds = None
        print(f"  {descricao}: encontrado automaticamente em '{caminho_padrao}'.")
        return caminho_padrao
    print(f"  {descricao}: nao encontrei em '{caminho_padrao}'.")
    return pedir_caminho(f"  Informe o caminho de {descricao}: ", "raster")


def listar_rasters_uso(caminho):
    """Devolve a lista de rasters de uso da terra: o proprio arquivo, ou
    todos os rasters de uma pasta (o 'Iterate Rasters' do model)."""
    if os.path.isfile(caminho):
        return [caminho]
    if caminho.lower().endswith(".gdb"):
        raise SystemExit(
            "O GDAL nao le rasters dentro de geodatabase (.gdb). Exporte cada raster "
            "de uso da terra para GeoTIFF (ArcGIS Pro: Copy Raster) e aponte para a pasta."
        )
    rasters = []
    for padrao in EXTENSOES_RASTER_USO:
        rasters += glob.glob(os.path.join(caminho, padrao))
    if FILTRO_NOME_USO:
        rasters = [r for r in rasters if FILTRO_NOME_USO in os.path.basename(r)]
    return sorted(set(rasters))


def reprojetar_vetor(caminho_entrada, srs_saida, caminho_saida_gpkg):
    """Equivalente a 'Project' do ArcGIS / 'native:reprojectlayer' do
    QGIS: reprojeta um vetor para o SRC informado usando
    gdal.VectorTranslate (mesmo motor do "ogr2ogr"). Cada camada vai para
    o seu proprio GPKG."""
    fonte, nome = separar_gdb(caminho_entrada)
    opcoes = gdal.VectorTranslateOptions(
        format="GPKG", dstSRS=srs_saida, reproject=True,
        layerName=NOME_CAMADA, accessMode="overwrite",
        layers=[nome] if nome else None,
        geometryType="PROMOTE_TO_MULTI",  # camada MULTIPOLYGON (evita o aviso de POLYGON x MULTIPOLYGON)
    )
    ds = gdal.VectorTranslate(caminho_saida_gpkg, fonte, options=opcoes)
    if ds is None:
        raise RuntimeError(f"Falha ao reprojetar '{caminho_entrada}'.")
    ds = None


def grade_do_raster(caminho):
    """Devolve (colunas, linhas, geotransform, projecao, bounds) do raster
    - 'bounds' = (xmin, ymin, xmax, ymax). E a grade de referencia."""
    ds = gdal.Open(caminho)
    colunas, linhas = ds.RasterXSize, ds.RasterYSize
    gt = ds.GetGeoTransform()
    projecao = ds.GetProjection()
    ds = None
    bounds = (gt[0], gt[3] + gt[5] * linhas, gt[0] + gt[1] * colunas, gt[3])
    return colunas, linhas, gt, projecao, bounds


def rasterizar_campo(caminho_gpkg, campo, caminho_saida, grade):
    """Equivalente a 'Feature to Raster' do ArcGIS: grava o valor do campo
    de cada poligono nos pixels cujo centro cai dentro dele, DIRETO na
    grade de referencia (gdal.Rasterize)."""
    colunas, linhas, _, _, bounds = grade
    opcoes = gdal.RasterizeOptions(
        format="GTiff", outputType=gdal.GDT_Int16, creationOptions=OPCOES_TIF,
        outputBounds=bounds, width=colunas, height=linhas,
        attribute=campo, noData=NODATA, initValues=[NODATA],
    )
    ds = gdal.Rasterize(caminho_saida, caminho_gpkg, options=opcoes)
    if ds is None:
        raise RuntimeError(f"Falha ao rasterizar '{caminho_gpkg}' (campo '{campo}').")
    ds = None


def alinhar_raster(caminho_entrada, caminho_saida, srs_saida, grade):
    """Equivalente a 'Project Raster' + 'Extract by Mask' do ArcGIS: leva
    um raster de classes para a grade de referencia (SRC, extensao,
    resolucao e origem) com vizinho mais proximo, numa unica passada."""
    colunas, linhas, _, _, bounds = grade
    ds_in = gdal.Open(caminho_entrada)
    sem_srs = not ds_in.GetProjection()
    ds_in = None
    opcoes = dict(
        dstSRS=srs_saida, outputBounds=bounds, width=colunas, height=linhas,
        resampleAlg="near", dstNodata=NODATA, outputType=gdal.GDT_Int16,
        creationOptions=OPCOES_TIF, multithread=True,
    )
    if sem_srs:
        opcoes["srcSRS"] = srs_de_epsg(EPSG_USO_ENTRADA_PADRAO)
    ds = gdal.Warp(caminho_saida, caminho_entrada, **opcoes)
    if ds is None:
        raise RuntimeError(f"Falha ao alinhar '{caminho_entrada}' a grade de referencia.")
    ds = None


def mascarar_por_limite(caminho_entrada, caminho_saida, grade, nome_camada_limite):
    """Equivalente a 'Extract by Mask' final do model: recorta pelo
    contorno exato do limite (cutline), mantendo a MESMA grade (sem
    reamostrar)."""
    colunas, linhas, _, _, bounds = grade
    ds = gdal.Warp(
        caminho_saida, caminho_entrada,
        cutlineDSName=GPKG_LIMITE, cutlineLayer=nome_camada_limite,
        outputBounds=bounds, width=colunas, height=linhas, resampleAlg="near",
        dstNodata=NODATA, outputType=gdal.GDT_Int16, creationOptions=OPCOES_TIF,
    )
    if ds is None:
        raise RuntimeError(f"Falha ao recortar '{caminho_entrada}' pelo limite.")
    ds = None


def calcular_em_blocos(caminho_saida, entradas, funcao):
    """Raster Calculator em blocos de linhas: le as mesmas linhas de todos
    os rasters de 'entradas' (todos na mesma grade), aplica
    funcao(lista_de_arrays, lista_de_nodata) -> array Int16 (com NODATA
    onde nao ha resultado) e grava no raster de saida."""
    dss = [gdal.Open(c) for c in entradas]
    bandas = [d.GetRasterBand(1) for d in dss]
    nodatas = [b.GetNoDataValue() if b.GetNoDataValue() is not None else NODATA for b in bandas]
    colunas, linhas = dss[0].RasterXSize, dss[0].RasterYSize
    for d in dss:
        if (d.RasterXSize, d.RasterYSize) != (colunas, linhas):
            raise RuntimeError("Os rasters nao estao na mesma grade - isso nao deveria acontecer.")

    driver = gdal.GetDriverByName("GTiff")
    saida = driver.Create(caminho_saida, colunas, linhas, 1, gdal.GDT_Int16, options=OPCOES_TIF)
    saida.SetGeoTransform(dss[0].GetGeoTransform())
    saida.SetProjection(dss[0].GetProjection())
    banda_saida = saida.GetRasterBand(1)
    banda_saida.SetNoDataValue(NODATA)

    for y in range(0, linhas, LINHAS_BLOCO):
        n = min(LINHAS_BLOCO, linhas - y)
        arrays = [b.ReadAsArray(0, y, colunas, n) for b in bandas]
        banda_saida.WriteArray(funcao(arrays, nodatas), 0, y)

    banda_saida.FlushCache()
    saida = None
    dss = None


def todos_validos(arrays, nodatas):
    valido = np.ones(arrays[0].shape, dtype=bool)
    for a, nd in zip(arrays, nodatas):
        valido &= (a != nd)
    return valido


# --- funcoes de calculo (uma por etapa do model) ---------------------
def f_reclassificar_relevo(arrays, nodatas):
    """Reclassify: Grau de Dissecacao (11-55) -> fragilidade do relevo (1000-5000)."""
    a = arrays[0]
    saida = np.full(a.shape, NODATA, dtype=np.int16)
    for origem, destino in REMAP_RELEVO.items():
        saida[a == origem] = destino
    return saida


def f_solos_x100(arrays, nodatas):
    """Raster Calculator: solos x 100 (algarismo das centenas)."""
    a = arrays[0]
    valido = todos_validos(arrays, nodatas)
    return np.where(valido, np.rint(a.astype(np.float64) * 100), NODATA).astype(np.int16)


def f_soma(arrays, nodatas):
    """Raster Calculator: soma de rasters (Relevo + Solos + Clima)."""
    valido = todos_validos(arrays, nodatas)
    total = np.zeros(arrays[0].shape, dtype=np.float64)
    for a in arrays:
        total += np.where(valido, a, 0)
    return np.where(valido, np.rint(total), NODATA).astype(np.int16)


def criar_f_uso(classes_desconhecidas):
    """Devolve a funcao que reclassifica o uso (Tabela 24) e soma com a
    matriz Relevo+Solo+Clima. Classes fora da tabela viram NoData e sao
    registradas em 'classes_desconhecidas'."""
    lut = np.full(256, NODATA, dtype=np.int16)
    for origem, destino in REMAP_USO.items():
        lut[origem] = destino

    def f_uso(arrays, nodatas):
        base, uso = arrays
        valido_base = (base != nodatas[0])
        valido_uso = (uso != nodatas[1])
        codigo = np.where(valido_uso, uso, 0).astype(np.int64)
        dentro_lut = valido_uso & (codigo >= 0) & (codigo < len(lut))
        uso_frag = np.where(dentro_lut, lut[np.clip(codigo, 0, len(lut) - 1)], NODATA)

        for c in np.unique(uso[valido_uso]):
            if int(c) not in REMAP_USO:
                classes_desconhecidas.add(int(c))

        valido = valido_base & (uso_frag != NODATA)
        return np.where(valido, base.astype(np.int32) + uso_frag, NODATA).astype(np.int16)

    return f_uso


# ------------------------------------------------------------------
# Programa principal
# ------------------------------------------------------------------
def main():
    garantir_pasta(WORKSPACE)

    print()
    grau_dissecacao = achar_ou_pedir_caminho(
        GRAU_DISSECACAO_PADRAO, "Grau de Dissecacao - Fragilidade (b_GrauDeDissecacao_Fragilidade)"
    )
    pedologico, campo_solo = pedir_vetor_com_campo(
        f"Caminho do mapa pedologico (vetor com o campo '{CAMPO_SOLO}', "
        "ex.: C:\\dados\\GDB Final.gdb\\PEDOLOGICO_SP_ROSSI_2017_V4): ", CAMPO_SOLO
    )
    clima, campo_clima = pedir_vetor_com_campo(
        f"Caminho do vetor climatico ja classificado (WorldClim, campo '{CAMPO_CLIMA}', "
        "ex.: C:\\dados\\ClimaFragilidade.gdb\\wc21_Br): ", CAMPO_CLIMA
    )
    uso_terra = pedir_caminho(
        "Caminho do Uso e Cobertura da Terra (um raster OU uma pasta com um GeoTIFF por ano, "
        "ex.: C:\\dados\\MapBiomas8_SP): ", "pasta_ou_raster"
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

    srs_saida = srs_de_epsg(EPSG_SAIDA)

    # 1. Limite -> SIRGAS 2000 -----------------------------------------------------
    print("1/6 - Limite da area: SIRGAS 2000...")
    reprojetar_vetor(limite, srs_saida, GPKG_LIMITE)

    # 2. Relevo: grade de referencia ------------------------------------------------
    print("2/6 - Relevo: Grau de Dissecacao -> fragilidade (1000 a 5000)...")
    ds = gdal.Open(grau_dissecacao)
    srs_grau = osr.SpatialReference(wkt=ds.GetProjection()) if ds.GetProjection() else None
    ds = None
    if srs_grau is not None:
        srs_grau.SetAxisMappingStrategy(osr.OAMS_TRADITIONAL_GIS_ORDER)
    if srs_grau is not None and srs_grau.IsSame(srs_saida):
        grau = grau_dissecacao
    else:
        # fora do SIRGAS 2000 geografico: reprojeta (vizinho mais proximo)
        print("   (Grau de Dissecacao fora do SIRGAS 2000 geografico - reprojetando...)")
        gdal.Warp(REL_A_GRAU, grau_dissecacao, dstSRS=srs_saida, xRes=CELL_SIZE, yRes=CELL_SIZE,
                  resampleAlg="near", dstNodata=NODATA, outputType=gdal.GDT_Int16,
                  creationOptions=OPCOES_TIF)
        grau = REL_A_GRAU
    calcular_em_blocos(REL_B_FRAGIL, [grau], f_reclassificar_relevo)
    grade = grade_do_raster(REL_B_FRAGIL)  # TODOS os outros rasters seguem esta grade

    # 3. Solos ------------------------------------------------------------------------
    print("3/6 - Solos: reprojetar, rasterizar o campo 'Frag' e x 100...")
    reprojetar_vetor(pedologico, srs_saida, GPKG_SOLO)
    rasterizar_campo(GPKG_SOLO, campo_solo, PED_C_RASTER, grade)
    calcular_em_blocos(PED_D_FRAGIL, [PED_C_RASTER], f_solos_x100)

    # 4. Clima ------------------------------------------------------------------------
    print("4/6 - Clima: reprojetar e rasterizar o campo 'Fragilidade'...")
    reprojetar_vetor(clima, srs_saida, GPKG_CLIMA)
    rasterizar_campo(GPKG_CLIMA, campo_clima, CLI_C_FRAGIL, grade)

    # 5. Relevo + Solos + Clima -----------------------------------------------------
    print("5/6 - Relevo + Solos + Clima (a_FragilidadeFinal)...")
    calcular_em_blocos(A_FRAGILIDADE_FINAL, [REL_B_FRAGIL, PED_D_FRAGIL, CLI_C_FRAGIL], f_soma)

    # 6. Uso e cobertura da terra - um resultado por raster -----------------------------
    print(f"6/6 - Uso e Cobertura da Terra ({len(rasters_uso)} raster(s))...")
    resultados = []
    for i, uso_original in enumerate(rasters_uso, start=1):
        nome = os.path.splitext(os.path.basename(uso_original))[0]
        saida = os.path.join(WORKSPACE, f"c_{nome}_FRAGILIDADE_FINAL.tif")
        print(f"  [{i}/{len(rasters_uso)}] {nome} ...", end=" ", flush=True)

        if os.path.exists(saida) and not SOBRESCREVER:
            print("ja existe - pulando.")
            resultados.append(saida)
            continue

        uso_b = os.path.join(WORKSPACE, f"uso_b_{nome}_Alinhado.tif")
        soma = os.path.join(WORKSPACE, f"b_{nome}_FragFinal.tif")

        # Project Raster + Extract by Mask -> grade de referencia
        alinhar_raster(uso_original, uso_b, srs_saida, grade)

        # Reclassify (Tabela 24) + soma com a_FragilidadeFinal
        desconhecidas = set()
        calcular_em_blocos(soma, [A_FRAGILIDADE_FINAL, uso_b], criar_f_uso(desconhecidas))
        if desconhecidas:
            print(f"\n    AVISO: classes fora da Tabela 24 (viraram NoData): {sorted(desconhecidas)}", end=" ")

        # Extract by Mask final (contorno exato do limite)
        mascarar_por_limite(soma, saida, grade, NOME_CAMADA)

        if not MANTER_INTERMEDIARIOS:
            for tmp in (uso_b, soma):
                if os.path.exists(tmp):
                    os.remove(tmp)
        resultados.append(saida)
        print("ok.")

    print()
    print("Concluido.")
    print("a_FragilidadeFinal (Relevo + Solos + Clima, sem o uso da terra):", A_FRAGILIDADE_FINAL)
    print("Fragilidade Ambiental final (matriz de 4 algarismos), um raster por uso da terra:")
    for r in resultados:
        print("  ", r)


if __name__ == "__main__":
    main()
