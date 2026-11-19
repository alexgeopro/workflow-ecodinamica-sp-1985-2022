# -*- coding: utf-8 -*-
"""
2_Dimensao Interfluvial Media - versao software livre SEM QGIS (Python + GDAL)
=================================================================================
Mesma metodologia do script "2_dimensao_interfluvial_media.py" (ArcGIS
Pro / arcpy) e do "2_dimensao_interfluvial_media_QGIS.py" (QGIS +
Python) - ver aqueles arquivos para a descricao completa dos passos
(a)-(l) e as fontes conferidas: script exportado do ArcMap 10.3 e a
tese (Alex da Silva Sousa, 2024, Cap. 6.3 "Geomorfologia e
Hidrografia", p. 62-64, DOI: 10.11606/T.8.2024.tde-18022025-121027).

Diferenca em relacao a "2_dimensao_interfluvial_media_QGIS.py": aquela
versao usa o framework "processing" do QGIS (algoritmo
"gdal:warpreproject") - e, por isso, so roda com o QGIS instalado (seja
dentro do proprio QGIS, seja no modo "headless" via python-qgis.bat).
Este script faz a MESMA coisa chamando diretamente gdal.Warp()
(osgeo.gdal) - a mesma biblioteca que o QGIS usa por baixo dos panos -
sem nenhuma dependencia do QGIS. Roda em QUALQUER instalacao comum de
Python, bastando instalar os pacotes abaixo.

Toda a etapa (b) em diante (distancia ate a borda, centro de cada
subbacia, media zonal, reclassificacao) e identica ao "_QGIS.py": feita
com numpy/scipy/scikit-image direto na matriz do raster, sem chamar
nenhuma ferramenta de geoprocessamento - por isso essa parte nunca
dependeu do QGIS, so a etapa (a) (reprojetar o raster de entrada)
dependia.

Nota sobre a constante 107015: no texto da tese, esse valor foi obtido
comparando os resultados gerados pelo dado em projecao UTM com o dado
em coordenadas geograficas, para nao deixar a ferramenta limitada a um
fuso especifico. E uma aproximacao (o fator graus->metros varia um
pouco com a latitude), mas foi mantida EXATAMENTE como na tese - por
opcao explicita da autora, para manter esta versao fiel ao metodo
publicado. Uma correcao mais rigorosa (reprojetar para uma projecao
metrica equidistante antes de calcular a distancia) fica para uma
eventual modernizacao futura do script.

Requisitos (nenhum deles precisa do QGIS instalado):
    - Python 3.x com os pacotes: gdal (osgeo), numpy, scipy, scikit-image
    - Instalacao mais simples: usando conda -
          conda install -c conda-forge gdal numpy scipy scikit-image

Como rodar:
    python 2_dimensao_interfluvial_media_sem_qgis.py

O script pergunta, na propria tela, o caminho do raster de subbacias
(ex.: "Subbacias.tif").
"""
import os

import numpy as np
from osgeo import gdal, osr
from scipy import ndimage as ndi
from skimage.morphology import local_maxima

gdal.UseExceptions()

# ------------------------------------------------------------------
# PARAMETROS - ajuste para o seu ambiente
# ------------------------------------------------------------------
WORKSPACE = r"C:\alexgeopro\DimensaoInterfluvial_SemQGIS"  # pasta - criada automaticamente

CELL_SIZE = 0.00027777778           # ~30 m em graus (mesma resolucao das outras versoes)
EPSG_SAIDA = 4674                   # SIRGAS 2000 Geografico
FATOR_GRAUS_PARA_METROS = 107015    # MESMA constante da tese - ver nota no cabecalho
NODATA_PADRAO = -9999.0

# Reclassificacao final da dimensao interfluvial media (Tabela 5/Tabela 7,
# Cap. 5.4.1 da tese) - os mesmos remaps confirmados no script ArcGIS
REMAP_FRAGILIDADE = [
    (0, 250, 5), (250, 750, 4), (750, 1750, 3), (1750, 3750, 2), (3750, 100000, 1),
]
REMAP_VULNERABILIDADE = [
    (-100000, 250, 5), (250, 750, 4), (750, 2000, 3), (2000, 5000, 2), (5000, 100000, 1),
]

# Saidas raster (nomes equivalentes aos das outras versoes)
A_SUBBACIAS_PROJ = os.path.join(WORKSPACE, "a_Subbacias_Reproj.tif")
D_DISTANCIA_M = os.path.join(WORKSPACE, "d_Subbacias_EucDistInt.tif")     # (c)+(d)
I_DIAMETRO = os.path.join(WORKSPACE, "i_SinkPtRaster.tif")                # (h)/(i) - diametro nos centros
J_DIMENSAO = os.path.join(WORKSPACE, "j_Dimensao.tif")                    # (i)/(j) - media zonal
L_DIMENSAO_RECLA_FRAG = os.path.join(WORKSPACE, "l_DimensaoReclaFrag.tif")
L_DIMENSAO_RECLA_VULN = os.path.join(WORKSPACE, "l_DimensaoReclaVul.tif")


# ------------------------------------------------------------------
# Funcoes auxiliares - GDAL puro (sem QGIS)
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


def pedir_caminho(mensagem):
    """Pergunta o caminho do raster de subbacias e so aceita quando o
    GDAL conseguir realmente abrir o dado."""
    while True:
        caminho = input(mensagem).strip().strip('"')
        if not caminho:
            print("  -> Caminho vazio, tente novamente.")
            continue
        try:
            ds = gdal.Open(caminho)
        except RuntimeError:
            ds = None
        if ds is not None:
            ds = None
            return caminho
        print(f"  -> Nao consegui abrir '{caminho}' como raster. Confira o caminho e tente de novo.")


def reprojetar_raster_categorico(caminho_entrada, srs_saida, caminho_saida, cell_size, nodata):
    """Equivalente a 'gdal:warpreproject' do QGIS: reprojeta o raster de
    subbacias usando gdal.Warp com reamostragem "nearest neighbour"
    (obrigatoria aqui - qualquer outro metodo de interpolacao corrompe
    os codigos/ID de cada subbacia) e saida em inteiro (GDT_Int32,
    igual ao DATA_TYPE=5 usado na versao QGIS)."""
    gdal.Warp(
        caminho_saida, caminho_entrada,
        dstSRS=srs_saida, xRes=cell_size, yRes=cell_size,
        resampleAlg="near", dstNodata=nodata, outputType=gdal.GDT_Int32,
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


def mascara_de_borda(zonas, valido):
    """
    Equivalente a "Polygon To Line": marca como borda todo pixel valido
    que tenha ao menos um vizinho (dos 8 ao redor) de uma subbacia
    diferente, ou fora da area valida (nodata) - reproduz, na matriz, o
    conjunto combinado de todas as linhas de borda entre subbacias e o
    limite externo da area de estudo.
    """
    borda = np.zeros_like(zonas, dtype=bool)
    deslocamentos = [(-1, 0), (1, 0), (0, -1), (0, 1), (-1, -1), (-1, 1), (1, -1), (1, 1)]
    for dy, dx in deslocamentos:
        vizinho_zona = np.roll(np.roll(zonas, dy, axis=0), dx, axis=1)
        vizinho_valido = np.roll(np.roll(valido, dy, axis=0), dx, axis=1)
        diferente = (vizinho_zona != zonas) | (~vizinho_valido)
        borda |= diferente
    # as bordas do proprio array tambem contam como limite externo
    borda[0, :] = borda[-1, :] = borda[:, 0] = borda[:, -1] = True
    return borda & valido


def calcular_dimensao_interfluvial(zonas, nodata_zonas):
    """
    Equivalente aos passos (b) a (j) da tese, feito direto sobre a
    matriz de subbacias. Retorna (distancia_m, diametro, dimensao_por_zona).
    """
    valido = zonas != nodata_zonas

    print("  Calculando distancia ate a borda mais proxima (equivalente a Euclidean Distance)...")
    borda = mascara_de_borda(zonas, valido)
    distancia_px = ndi.distance_transform_edt(~borda)
    distancia_m = distancia_px * CELL_SIZE * FATOR_GRAUS_PARA_METROS
    distancia_m = np.where(valido, distancia_m, np.nan)

    print("  Identificando o(s) ponto(s) mais central(is) de cada subbacia...")
    referencia = np.where(valido, distancia_m, -np.inf)
    maximos = local_maxima(referencia, connectivity=2) & valido

    diametro = np.full(zonas.shape, np.nan)
    diametro[maximos] = distancia_m[maximos] * 2

    ids_zona = np.unique(zonas[valido]).astype(np.int64)
    dimensao_por_zona = {}
    for zona_id in ids_zona:
        pixels_zona = zonas == zona_id
        pixels_centrais = pixels_zona & maximos
        if pixels_centrais.any():
            dimensao_por_zona[zona_id] = float(np.nanmean(diametro[pixels_centrais]))
        else:
            # salvaguarda: nenhum maximo local caiu nessa subbacia
            # (equivalente ao papel do Eliminate no model original) -
            # usa diretamente 2x a maior distancia-ate-a-borda da zona.
            dimensao_por_zona[zona_id] = float(2 * np.nanmax(distancia_m[pixels_zona]))

    dimensao_raster = np.full(zonas.shape, np.nan)
    for zona_id, valor in dimensao_por_zona.items():
        dimensao_raster[zonas == zona_id] = valor
    dimensao_raster = np.where(valido, dimensao_raster, np.nan)

    return distancia_m, diametro, dimensao_raster


def reclassificar(array, faixas):
    resultado = np.full(array.shape, np.nan)
    valido = ~np.isnan(array)
    for minimo, maximo, classe in faixas:
        alvo = valido & (array >= minimo) & (array < maximo)
        resultado[alvo] = classe
    return resultado


# ------------------------------------------------------------------
# Programa principal
# ------------------------------------------------------------------
def main():
    garantir_pasta(WORKSPACE)

    print()
    SUBBACIAS_RASTER = pedir_caminho(
        "Caminho do raster de subbacias (ex.: C:\\dados\\Subbacias.tif): "
    )
    print()

    srs_saida = srs_de_epsg(EPSG_SAIDA)

    # (a) Reprojeta o raster de subbacias para SIRGAS 2000 Geografico -----
    print("(a) 1/4 - Reprojetando raster de subbacias (gdal.Warp, nearest)...")
    reprojetar_raster_categorico(SUBBACIAS_RASTER, srs_saida, A_SUBBACIAS_PROJ, CELL_SIZE, NODATA_PADRAO)

    zonas, nodata_zonas, geotransform, projecao = ler_raster(A_SUBBACIAS_PROJ)
    zonas = np.round(zonas).astype(np.int64)
    nodata_zonas = int(round(nodata_zonas))

    # (b)-(j) Distancia ate a borda + centro de cada subbacia + media zonal ---
    print("(b)-(j) 2/4 - Calculando dimensao interfluvial media por subbacia...")
    distancia_m, diametro, dimensao_raster = calcular_dimensao_interfluvial(zonas, nodata_zonas)

    gravar_raster(D_DISTANCIA_M, distancia_m, NODATA_PADRAO, geotransform, projecao)
    gravar_raster(I_DIAMETRO, diametro, NODATA_PADRAO, geotransform, projecao)
    gravar_raster(J_DIMENSAO, dimensao_raster, NODATA_PADRAO, geotransform, projecao)

    # (l) Reclassifica em 2 variantes (Fragilidade/Vulnerabilidade) --------
    print("(l) 3/4 - Reclassify (Fragilidade - Ross)...")
    recla_frag = reclassificar(dimensao_raster, REMAP_FRAGILIDADE)
    gravar_raster(L_DIMENSAO_RECLA_FRAG, recla_frag, NODATA_PADRAO, geotransform, projecao)

    print("(l) 4/4 - Reclassify (Vulnerabilidade - Crepani)...")
    recla_vuln = reclassificar(dimensao_raster, REMAP_VULNERABILIDADE)
    gravar_raster(L_DIMENSAO_RECLA_VULN, recla_vuln, NODATA_PADRAO, geotransform, projecao)

    print()
    print("Concluido.")
    print("j_ (dimensao interfluvial media por subbacia, valor continuo em metros):", J_DIMENSAO)
    print("l_DimensaoReclaFrag (reclassificado, metodologia Ross - Fragilidade):", L_DIMENSAO_RECLA_FRAG)
    print("l_DimensaoReclaVul (reclassificado, metodologia Crepani - Vulnerabilidade):", L_DIMENSAO_RECLA_VULN)


if __name__ == "__main__":
    main()
