# -*- coding: utf-8 -*-
"""
3_Grau de Dissecacao - versao software livre SEM QGIS (Python + GDAL/OGR)
============================================================================
Mesma metodologia do script "3_grau_de_dissecacao.py" (ArcGIS Pro /
arcpy) e do "3_grau_de_dissecacao_QGIS.py" (QGIS + Python) - ver
aqueles arquivos para a descricao completa da metodologia e as fontes
conferidas: script exportado do ArcMap 10.3 e a tese (Alex da Silva
Sousa, 2024, Cap. 6.3 "Geomorfologia e Hidrografia", p. 64-65,
DOI: 10.11606/T.8.2024.tde-18022025-121027).

Metodologia (identica as outras versoes): soma o raster reclassificado
de Entalhamento do Vale (classes de dezena: 10 a 50) com os rasters
reclassificados de Dimensao Interfluvial Media (classes de unidade: 1 a
5 - uma para Fragilidade/Ross, outra para Vulnerabilidade/Crepani), e
recorta o resultado pelo limite da area de interesse. Gera as DUAS
combinacoes automaticamente:

    - Grau de Dissecacao (Fragilidade) = Entalhamento_Recla + DimensaoReclaFrag
    - Grau de Dissecacao (Vulnerabilidade) = Entalhamento_Recla + DimensaoReclaVul

Diferenca em relacao a "3_grau_de_dissecacao_QGIS.py": aquela versao usa
o framework "processing" do QGIS (algoritmos "native:reprojectlayer",
"gdal:warpreproject", "gdal:cliprasterbymasklayer") - e, por isso, so
roda com o QGIS instalado. Este script faz a MESMA coisa chamando
diretamente gdal.Warp()/gdal.VectorTranslate() (osgeo.gdal/osgeo.ogr) -
as mesmas bibliotecas que o QGIS usa por baixo dos panos - sem nenhuma
dependencia do QGIS.

Antes de somar, os tres rasters de entrada sao reprojetados/reamostrados
(vizinho mais proximo - sao rasters de classes, nao pode interpolar)
para uma MESMA grade (mesma extensao, resolucao e origem), usando como
referencia a extensao do limite da area de interesse - necessario
porque os scripts 1 e 2 recortam por mascaras diferentes entre si e
raramente saem com a mesma grade de pixels "de fabrica".

Este script procura automaticamente, nos locais padrao onde a versao
"_sem_qgis" dos scripts 1 e 2 gravam suas saidas, os tres rasters
reclassificados de que precisa. Se voce rodou os scripts 1/2 na versao
QGIS (nao a "_sem_qgis"), ou moveu os arquivos, so informar o caminho
correto na tela quando perguntado.

Requisitos (nenhum deles precisa do QGIS instalado):
    - Python 3.x com os pacotes: gdal (osgeo), numpy
    - Instalacao mais simples: usando conda -
          conda install -c conda-forge gdal numpy

Como rodar:
    python 3_grau_de_dissecacao_sem_qgis.py
"""
import os

import numpy as np
from osgeo import gdal, ogr, osr

gdal.UseExceptions()
ogr.UseExceptions()

# ------------------------------------------------------------------
# PARAMETROS - ajuste para o seu ambiente
# ------------------------------------------------------------------
WORKSPACE = r"C:\alexgeopro\GrauDeDissecacao_SemQGIS"  # pasta - criada automaticamente
GPKG = os.path.join(WORKSPACE, "GrauDeDissecacao.gpkg")  # vetor intermediario (limite reprojetado)

CELL_SIZE = 0.00027777778   # ~30 m em graus (mesma resolucao dos demais scripts)
EPSG_SAIDA = 4674           # SIRGAS 2000 Geografico
NODATA_PADRAO = -9999.0

# Locais padrao onde a versao "_sem_qgis" dos scripts 1 e 2 gravam suas
# saidas reclassificadas - usados automaticamente quando existirem.
ENTALHAMENTO_RECLA_PADRAO = r"C:\alexgeopro\Entalhamento_SemQGIS\i_EntalhamentoRecla.tif"
DIMENSAO_RECLA_FRAG_PADRAO = r"C:\alexgeopro\DimensaoInterfluvial_SemQGIS\l_DimensaoReclaFrag.tif"
DIMENSAO_RECLA_VULN_PADRAO = r"C:\alexgeopro\DimensaoInterfluvial_SemQGIS\l_DimensaoReclaVul.tif"

# Nome da camada vetorial (dentro do GPKG)
NOME_LIMITE_PROJ = "limite_proj"

# Saidas (grades intermediarias alinhadas + resultados finais)
ENTALHAMENTO_ALINHADO = os.path.join(WORKSPACE, "_entalhamento_alinhado.tif")
DIMENSAO_FRAG_ALINHADO = os.path.join(WORKSPACE, "_dimensao_frag_alinhado.tif")
DIMENSAO_VULN_ALINHADO = os.path.join(WORKSPACE, "_dimensao_vuln_alinhado.tif")
A_SOMA_FRAGILIDADE = os.path.join(WORKSPACE, "a_Soma_Fragilidade.tif")
A_SOMA_VULNERABILIDADE = os.path.join(WORKSPACE, "a_Soma_Vulnerabilidade.tif")
B_GRAU_DISSECACAO_FRAGILIDADE = os.path.join(WORKSPACE, "b_GrauDeDissecacao_Fragilidade.tif")
B_GRAU_DISSECACAO_VULNERABILIDADE = os.path.join(WORKSPACE, "b_GrauDeDissecacao_Vulnerabilidade.tif")


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


def pedir_caminho(mensagem, tipo):
    """Pergunta um caminho (raster ou vetor) e so aceita quando o GDAL/OGR
    conseguir realmente abrir o dado."""
    while True:
        caminho = input(mensagem).strip().strip('"')
        if not caminho:
            print("  -> Caminho vazio, tente novamente.")
            continue
        try:
            ds = gdal.Open(caminho) if tipo == "raster" else ogr.Open(caminho)
        except RuntimeError:
            ds = None
        if ds is not None:
            ds = None
            return caminho
        print(f"  -> Nao consegui abrir '{caminho}' como {tipo}. Confira o caminho e tente de novo.")


def achar_ou_pedir_caminho(caminho_padrao, descricao):
    """Tenta usar automaticamente o caminho padrao (saida dos scripts
    1/2, versao "_sem_qgis"); se nao existir/abrir, pergunta o caminho
    na tela."""
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


def reprojetar_vetor(caminho_entrada, srs_saida, caminho_saida_gpkg, nome_camada):
    """Equivalente a 'native:reprojectlayer' do QGIS: reprojeta um vetor
    para o SRC informado usando gdal.VectorTranslate (mesmo motor do
    "ogr2ogr"), sem precisar do QGIS."""
    opcoes = gdal.VectorTranslateOptions(
        format="GPKG", dstSRS=srs_saida, reproject=True,
        layerName=nome_camada, accessMode="overwrite",
    )
    ds = gdal.VectorTranslate(caminho_saida_gpkg, caminho_entrada, options=opcoes)
    if ds is None:
        raise RuntimeError(f"Falha ao reprojetar '{caminho_entrada}' (camada '{nome_camada}').")
    ds = None


def calcular_extensao(caminho_gpkg, nome_camada):
    """Le a extensao (bounding box) de uma camada ja reprojetada -
    equivalente ao 'extent()' usado no algoritmo QGIS para definir a
    grade de referencia. Retorna (xmin, ymin, xmax, ymax)."""
    ds = ogr.Open(caminho_gpkg)
    camada = ds.GetLayerByName(nome_camada)
    xmin, xmax, ymin, ymax = camada.GetExtent()
    ds = None
    return xmin, ymin, xmax, ymax


def alinhar_raster(caminho_entrada, caminho_saida, srs_saida, bounds):
    """Equivalente a 'gdal:warpreproject' (com TARGET_EXTENT) do QGIS:
    reprojeta/reamostra um raster de classes para uma grade comum (mesma
    extensao, resolucao e origem) usando gdal.Warp - vizinho mais
    proximo, para nao interpolar valores de classe."""
    gdal.Warp(
        caminho_saida, caminho_entrada,
        dstSRS=srs_saida, xRes=CELL_SIZE, yRes=CELL_SIZE,
        outputBounds=bounds, resampleAlg="near",
        dstNodata=NODATA_PADRAO, outputType=gdal.GDT_Float32,
    )


def recortar_raster_por_mascara(caminho_entrada, caminho_mascara_gpkg, nome_camada_mascara,
                                 caminho_saida, nodata):
    """Equivalente a 'gdal:cliprasterbymasklayer' do QGIS / 'ExtractByMask'
    do ArcGIS: recorta um raster pelo contorno exato de um poligono (nao
    so pelo retangulo envolvente), usando gdal.Warp com cutline."""
    gdal.Warp(
        caminho_saida, caminho_entrada,
        cutlineDSName=caminho_mascara_gpkg, cutlineLayer=nome_camada_mascara,
        cropToCutline=True, dstNodata=nodata,
    )


def ler_raster(caminho):
    ds = gdal.Open(caminho)
    banda = ds.GetRasterBand(1)
    nodata = banda.GetNoDataValue()
    if nodata is None:
        nodata = NODATA_PADRAO
    array = banda.ReadAsArray().astype(np.float64)
    geotransform = ds.GetGeoTransform()
    projecao = ds.GetProjection()
    ds = None
    return array, nodata, geotransform, projecao


def gravar_raster(caminho, array, nodata, geotransform, projecao):
    driver = gdal.GetDriverByName("GTiff")
    linhas, colunas = array.shape
    ds = driver.Create(caminho, colunas, linhas, 1, gdal.GDT_Float32,
                        options=["COMPRESS=LZW"])
    ds.SetGeoTransform(geotransform)
    ds.SetProjection(projecao)
    banda = ds.GetRasterBand(1)
    banda.SetNoDataValue(nodata)
    banda.WriteArray(np.where(np.isnan(array), nodata, array))
    banda.FlushCache()
    ds = None


# ------------------------------------------------------------------
# Programa principal
# ------------------------------------------------------------------
def main():
    garantir_pasta(WORKSPACE)

    print()
    print("Localizando os rasters reclassificados dos scripts 1 e 2 (versao sem QGIS)...")
    entalhamento_recla = achar_ou_pedir_caminho(
        ENTALHAMENTO_RECLA_PADRAO, "Entalhamento do Vale reclassificado (i_EntalhamentoRecla)"
    )
    dimensao_recla_frag = achar_ou_pedir_caminho(
        DIMENSAO_RECLA_FRAG_PADRAO, "Dimensao Interfluvial reclassificada - Fragilidade (l_DimensaoReclaFrag)"
    )
    dimensao_recla_vuln = achar_ou_pedir_caminho(
        DIMENSAO_RECLA_VULN_PADRAO, "Dimensao Interfluvial reclassificada - Vulnerabilidade (l_DimensaoReclaVul)"
    )
    print()
    LIMITE_AREA = pedir_caminho(
        "Caminho do limite vetorial da area de interesse (padrao: limite do Estado de SP, "
        "ex.: C:\\dados\\EstadoSP_2023.shp): ",
        "vetor",
    )
    print()

    srs_saida = srs_de_epsg(EPSG_SAIDA)

    # Reprojeta o limite e usa a extensao dele como referencia para alinhar os rasters
    print("1/5 - Reprojetando o limite da area e definindo a grade de referencia...")
    reprojetar_vetor(LIMITE_AREA, srs_saida, GPKG, NOME_LIMITE_PROJ)
    bounds = calcular_extensao(GPKG, NOME_LIMITE_PROJ)

    print("2/5 - Alinhando os tres rasters reclassificados a uma grade comum (gdal.Warp)...")
    alinhar_raster(entalhamento_recla, ENTALHAMENTO_ALINHADO, srs_saida, bounds)
    alinhar_raster(dimensao_recla_frag, DIMENSAO_FRAG_ALINHADO, srs_saida, bounds)
    alinhar_raster(dimensao_recla_vuln, DIMENSAO_VULN_ALINHADO, srs_saida, bounds)

    entalhamento_arr, nodata, geotransform, projecao = ler_raster(ENTALHAMENTO_ALINHADO)
    dimensao_frag_arr, _, _, _ = ler_raster(DIMENSAO_FRAG_ALINHADO)
    dimensao_vuln_arr, _, _, _ = ler_raster(DIMENSAO_VULN_ALINHADO)

    valido_frag = (entalhamento_arr != nodata) & (dimensao_frag_arr != nodata)
    valido_vuln = (entalhamento_arr != nodata) & (dimensao_vuln_arr != nodata)

    # Grau de Dissecacao - Fragilidade (Ross) --------------------------------
    print("3/5 - Raster Calculator (Entalhamento + Dimensao/Fragilidade)...")
    soma_frag = np.where(valido_frag, entalhamento_arr + dimensao_frag_arr, nodata)
    gravar_raster(A_SOMA_FRAGILIDADE, soma_frag, nodata, geotransform, projecao)

    # Grau de Dissecacao - Vulnerabilidade (Crepani) -------------------------
    print("4/5 - Raster Calculator (Entalhamento + Dimensao/Vulnerabilidade)...")
    soma_vuln = np.where(valido_vuln, entalhamento_arr + dimensao_vuln_arr, nodata)
    gravar_raster(A_SOMA_VULNERABILIDADE, soma_vuln, nodata, geotransform, projecao)

    # Recorta as duas somas pelo limite exato da area (nao so a extensao/bbox) ----
    print("5/5 - Recortando pelo limite da area (gdal.Warp com cutline)...")
    recortar_raster_por_mascara(A_SOMA_FRAGILIDADE, GPKG, NOME_LIMITE_PROJ,
                                 B_GRAU_DISSECACAO_FRAGILIDADE, nodata)
    recortar_raster_por_mascara(A_SOMA_VULNERABILIDADE, GPKG, NOME_LIMITE_PROJ,
                                 B_GRAU_DISSECACAO_VULNERABILIDADE, nodata)

    print()
    print("Concluido.")
    print("b_GrauDeDissecacao_Fragilidade (Ross - Entalhamento + Dimensao Interfluvial):", B_GRAU_DISSECACAO_FRAGILIDADE)
    print("b_GrauDeDissecacao_Vulnerabilidade (Crepani - Entalhamento + Dimensao Interfluvial):", B_GRAU_DISSECACAO_VULNERABILIDADE)


if __name__ == "__main__":
    main()
