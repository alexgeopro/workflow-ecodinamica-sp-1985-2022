# -*- coding: utf-8 -*-
"""
1_Entalhamento do Vale - versao software livre SEM QGIS (Python + GDAL/OGR)
=============================================================================
Mesma metodologia do script "1_entalhamento_do_vale.py" (ArcGIS Pro /
arcpy) e do "1_entalhamento_do_vale_QGIS.py" (QGIS + Python) - ver
aqueles arquivos para a descricao completa dos passos (a)-(i) e as
fontes conferidas: tooltips do model original, script exportado do
ArcMap 10.3, e a tese - Alex da Silva Sousa, 2024, Cap. 6.3
"Geomorfologia e Hidrografia", p. 59-61,
DOI: 10.11606/T.8.2024.tde-18022025-121027.

Diferenca em relacao a "1_entalhamento_do_vale_QGIS.py": aquela versao
usa o framework "processing" do QGIS (algoritmos "native:reprojectlayer",
"native:buffer", "gdal:warpreproject", "gdal:cliprasterbymasklayer") -
e, por isso, so roda com o QGIS instalado (seja dentro do proprio QGIS,
seja no modo "headless" via python-qgis.bat). Este script faz a MESMA
coisa chamando diretamente as bibliotecas GDAL/OGR (osgeo.gdal/osgeo.ogr)
que o QGIS usa por baixo dos panos - sem nenhuma dependencia do QGIS.
Roda em QUALQUER instalacao comum de Python (Windows, Linux, macOS,
Anaconda, venv, etc.), bastando instalar os pacotes abaixo.

Equivalencias usadas (o algoritmo do QGIS, e a chamada GDAL/OGR direta
que faz a mesma coisa aqui):
    - "native:reprojectlayer"        -> gdal.VectorTranslate(...)
    - "native:buffer"                -> ogr Geometry.Buffer(...) (em CRS metrico)
    - "gdal:warpreproject"           -> gdal.Warp(...)
    - "gdal:cliprasterbymasklayer"   -> gdal.Warp(..., cutlineDSName=..., cropToCutline=True)

A partir da etapa (c) (Fill/inverter/Flow Direction/Sink/Basin), o
script e identico ao "_QGIS.py": tudo e feito com numpy/scipy/
scikit-image direto na matriz do raster, sem chamar nenhuma ferramenta
de geoprocessamento (nem do ArcGIS, nem do QGIS/GDAL) - por isso essa
parte nunca dependeu do QGIS, so a etapa de preparo (a)/(b) dependia.

Metodologia (identica as outras versoes - o "pulo do gato" e usar o MDT
invertido para que operacoes hidrologicas, que buscam pontos baixos,
passem a encontrar os pontos ALTOS do relevo original):

    (a) Reprojeta-se o MDT (SRTM) e o limite da area de estudo para
        SIRGAS 2000 Geografico.
    (b) Gera-se um buffer de 2 km do limite, para recortar o SRTM com
        margem de seguranca.
    (c) "Fill" preenche imperfeicoes do MDT (depressoes fechadas, ex.:
        reservatorios). O resultado (MDT preenchido) e multiplicado por
        -1 (c1), invertendo o relevo.
    (d)-(g) No relevo invertido, os pontos mais baixos ("Sink") sao, na
        verdade, os pontos MAIS ALTOS do relevo original (picos/
        divisores de agua). Para cada pico, delimita-se sua "zona de
        influencia" (equivalente ao "Basin" do ArcGIS) e atribui-se a
        toda a zona a cota (altitude) do seu pico.
    (h) Entalhamento = (cota do pico da zona) - (cota real do terreno) =
        o quanto cada pixel esta abaixo do divisor mais proximo.
    (i) Reclassifica-se (h) conforme as Tabelas 5 e 7 (Cap. 5.4.1
        Geomorfologia da tese), em 5 classes de peso (10 a 50).

Requisitos (nenhum deles precisa do QGIS instalado):
    - Python 3.x com os pacotes: gdal (osgeo), numpy, scipy, scikit-image
    - Instalacao mais simples: usando conda -
          conda install -c conda-forge gdal numpy scipy scikit-image
      (o pacote "gdal" do PyPI puro costuma dar mais trabalho para
      compilar no Windows - conda-forge e o caminho mais tranquilo).

Como rodar: basta rodar este arquivo com o Python onde os pacotes acima
estao instalados (ex.: no Prompt de Comando/PowerShell, dentro do
ambiente conda certo):

    python 1_entalhamento_do_vale_sem_qgis.py

O script pergunta, na propria tela, o caminho do MDT (raster) e o
caminho do shapefile/feature class da area de estudo.
"""
import os

import numpy as np
from osgeo import gdal, ogr, osr
from scipy import ndimage as ndi
from skimage.morphology import reconstruction, local_minima
from skimage.segmentation import watershed

gdal.UseExceptions()
ogr.UseExceptions()

# ------------------------------------------------------------------
# PARAMETROS - ajuste para o seu ambiente
# ------------------------------------------------------------------
# Pasta de trabalho (equivalente livre da geodatabase). E criada
# automaticamente se ainda nao existir.
WORKSPACE = r"C:\alexgeopro\Entalhamento_SemQGIS"
GPKG = os.path.join(WORKSPACE, "Entalhamento.gpkg")  # vetores intermediarios

BUFFER_DISTANCIA_M = 2000            # 2 km (ver nota sobre CRS abaixo)
BUFFER_SEGMENTOS = 8                 # segmentos por 1/4 de circulo (igual ao "SEGMENTS" do QGIS)
CELL_SIZE = 0.00027777778            # ~30 m em graus (resolucao do SRTM, igual as outras versoes)
EPSG_SAIDA = 4674                    # SIRGAS 2000 Geografico
EPSG_DEM_ENTRADA_PADRAO = 4326       # usado so se o raster de entrada nao tiver SRC definido
EPSG_METRICO_BR = 5880               # SIRGAS 2000 / Brazil Polyconic - usado so
                                      # internamente para o buffer (precisa de
                                      # metros; a saida final volta pra graus)
NODATA_PADRAO = -9999.0

# Nota sobre a transformacao geografica: assim como na versao QGIS,
# SIRGAS 2000 e WGS 84 sao, na pratica, coincidentes (diferenca de
# poucos cm a ~1 m), entao a reprojecao abaixo (feita direto pelo GDAL)
# e equivalente ao resultado pratico da transformacao "SIRGAS_To_WGS_1984_1"
# usada na versao ArcGIS.

# Reclassificacao final do entalhamento (Tabela 5/Tabela 7, Cap. 5.4.1 da tese)
# (valor_min, valor_max, classe_de_peso)
REMAP_ENTALHAMENTO = [
    (-1500, 20, 10),   # < 20 m: Muito Fraco
    (20, 40, 20),      # 20-40 m: Fraco
    (40, 80, 30),      # 40-80 m: Medio
    (80, 160, 40),     # 80-160 m: Forte
    (160, 5000, 50),   # > 160 m: Muito Forte
]

# Saidas raster (nomes equivalentes aos das outras versoes)
A_MOSAICO_PROJ = os.path.join(WORKSPACE, "a_mosaico_Reproj.tif")
B_MOSAICO_LIMITE = os.path.join(WORKSPACE, "b_Mosaico_Limite.tif")
C_MOSAICO_FILL = os.path.join(WORKSPACE, "c_mosaico_fill.tif")           # (c) MDT preenchido
C_MOSAICO_FILL_NEG = os.path.join(WORKSPACE, "c_mosaico_fill_neg.tif")   # (c1) MDT invertido
E_BASIN = os.path.join(WORKSPACE, "e_mosaico_basin.tif")                # (e) zonas de influencia
G_SINK_BASIN = os.path.join(WORKSPACE, "g_sink_basin.tif")              # (g) cota do pico espalhada pela zona
H_ENTALHAMENTO = os.path.join(WORKSPACE, "h_entalhamento.tif")          # (h)
I_ENTALHAMENTO_RECLA = os.path.join(WORKSPACE, "i_EntalhamentoRecla.tif")  # (i)

# Nomes das camadas vetoriais (dentro do GPKG)
NOME_LIMITE_PROJ = "a_limite_Proj"
NOME_LIMITE_PROJ_BUFFER = "a_limite_Proj_Buffer"


# ------------------------------------------------------------------
# Funcoes auxiliares - GDAL/OGR puro (sem QGIS)
# ------------------------------------------------------------------
def garantir_pasta(caminho):
    if not os.path.isdir(caminho):
        print(f"Criando pasta '{caminho}'...")
        os.makedirs(caminho)


def srs_de_epsg(epsg):
    """Cria um osr.SpatialReference a partir de um codigo EPSG, forcando
    a ordem tradicional de eixos (long, lat / x, y). Sem isso, o GDAL 3+
    pode inverter a ordem dos eixos para alguns SRCs geograficos (bug
    classico de reprojecao com coordenadas trocadas)."""
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


def reprojetar_vetor(caminho_entrada, srs_saida, caminho_saida_gpkg, nome_camada):
    """Equivalente a 'native:reprojectlayer' do QGIS: reprojeta um vetor
    (shapefile, GPKG etc.) para o SRC informado, usando
    gdal.VectorTranslate - o mesmo motor por tras do "ogr2ogr", sem
    precisar do QGIS."""
    opcoes = gdal.VectorTranslateOptions(
        format="GPKG", dstSRS=srs_saida, reproject=True,
        layerName=nome_camada, accessMode="overwrite",
    )
    ds = gdal.VectorTranslate(caminho_saida_gpkg, caminho_entrada, options=opcoes)
    if ds is None:
        raise RuntimeError(f"Falha ao reprojetar '{caminho_entrada}' (camada '{nome_camada}').")
    ds = None


def bufferizar_vetor(caminho_gpkg, nome_camada_entrada, distancia_m, segmentos,
                      srs_metrica, srs_saida, nome_camada_saida):
    """Equivalente a 'native:buffer' do QGIS: cria um buffer (em metros)
    ao redor de feicoes que estao num SRC geografico (graus) -
    reprojeta cada geometria para um SRC metrico, aplica
    Geometry.Buffer() (osgeo.ogr) e reprojeta de volta, sem QGIS."""
    ds_entrada = ogr.Open(caminho_gpkg)
    camada_entrada = ds_entrada.GetLayerByName(nome_camada_entrada)
    srs_entrada = camada_entrada.GetSpatialRef()

    para_metrico = osr.CoordinateTransformation(srs_entrada, srs_metrica)
    de_metrico = osr.CoordinateTransformation(srs_metrica, srs_saida)

    # calcula todos os buffers e fecha a conexao de leitura antes de abrir
    # uma nova conexao de escrita no MESMO arquivo .gpkg (evita conflito
    # de acesso simultaneo ao mesmo banco SQLite por baixo do GeoPackage)
    geometrias_buffer = []
    for feicao in camada_entrada:
        geom = feicao.GetGeometryRef().Clone()
        geom.Transform(para_metrico)
        geom_buffer = geom.Buffer(distancia_m, segmentos)
        geom_buffer.Transform(de_metrico)
        geometrias_buffer.append(geom_buffer)
    ds_entrada = None

    ds_saida = ogr.Open(caminho_gpkg, update=1)
    if ds_saida.GetLayerByName(nome_camada_saida) is not None:
        ds_saida.DeleteLayer(nome_camada_saida)
    # geom_type=wkbUnknown (em vez de wkbPolygon) para aceitar tanto
    # Polygon quanto MultiPolygon sem erro de tipo, ja que o resultado de
    # Buffer() pode ser um ou outro dependendo da geometria de entrada.
    camada_saida = ds_saida.CreateLayer(nome_camada_saida, srs=srs_saida, geom_type=ogr.wkbUnknown)

    for geom_buffer in geometrias_buffer:
        nova = ogr.Feature(camada_saida.GetLayerDefn())
        nova.SetGeometry(geom_buffer)
        camada_saida.CreateFeature(nova)
        nova = None

    ds_saida = None


def reprojetar_raster(caminho_entrada, srs_saida, caminho_saida, cell_size, nodata,
                       srs_entrada_padrao=None):
    """Equivalente a 'gdal:warpreproject' do QGIS / 'ProjectRaster' do
    ArcGIS: reprojeta um raster usando gdal.Warp. Se o raster de entrada
    ja tiver um SRC definido, usa esse; so cai no SRC padrao
    (srs_entrada_padrao) se o raster nao tiver nenhum definido - mesmo
    ajuste feito no script ArcGIS Pro para evitar o erro
    'ERROR 000151: geotransformation is not valid' quando o SRC de
    entrada era assumido errado."""
    ds_entrada = gdal.Open(caminho_entrada)
    projecao_entrada = ds_entrada.GetProjection()
    ds_entrada = None

    kwargs = dict(
        dstSRS=srs_saida, xRes=cell_size, yRes=cell_size,
        resampleAlg="near", dstNodata=nodata, outputType=gdal.GDT_Float32,
    )
    if not projecao_entrada:
        if srs_entrada_padrao is None:
            raise RuntimeError(
                f"'{caminho_entrada}' nao tem SRC definido e nenhum SRC padrao foi informado."
            )
        print("  MDT sem SRC definido - assumindo o padrao informado.")
        kwargs["srcSRS"] = srs_entrada_padrao
    else:
        print("  SRC do MDT detectado automaticamente a partir do proprio arquivo.")

    gdal.Warp(caminho_saida, caminho_entrada, **kwargs)


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
    """Le um raster com GDAL e devolve (array, nodata, geotransform, projecao)."""
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


def preencher_depressoes(dem, nodata):
    """
    Equivalente ao "Fill" do ArcGIS: preenche depressoes fechadas do MDT
    (pontos mais baixos que todos os vizinhos, sem saida) por reconstrucao
    morfologica (Vincent, 1993) - tecnica classica e bem documentada para
    esse fim.
    """
    dem_trabalho = np.where(dem == nodata, np.nan, dem)
    maximo = np.nanmax(dem_trabalho)
    marcador = dem_trabalho.copy()
    interior = np.zeros_like(dem_trabalho, dtype=bool)
    interior[1:-1, 1:-1] = True
    marcador[interior & ~np.isnan(dem_trabalho)] = maximo
    marcador = np.where(np.isnan(dem_trabalho), maximo, marcador)
    base = np.where(np.isnan(dem_trabalho), maximo, dem_trabalho)
    preenchido = reconstruction(marcador, base, method="erosion")
    preenchido = np.where(np.isnan(dem_trabalho), nodata, preenchido)
    return preenchido


def achar_picos_e_zonas(dem_preenchido, nodata):
    """
    Equivalente a Flow Direction + Sink + Basin do ArcGIS, feito direto
    sobre a matriz:
      1. Inverte o MDT preenchido.
      2. Acha os minimos locais do MDT invertido (= os pontos mais ALTOS
         do MDT original) - equivalente ao "Sink".
      3. Usa "watershed" (bacias hidrograficas de imagem) a partir desses
         pontos para delimitar a zona de influencia de cada pico -
         equivalente ao "Basin". Diferente da versao ArcGIS, aqui todo
         pixel sempre cai em alguma zona (sem precisar de limpeza
         iterativa de poligonos orfaos).

    Retorna (zonas, cota_do_pico_por_pixel) - dois arrays do mesmo
    tamanho do MDT.
    """
    mascara_valida = dem_preenchido != nodata
    invertido = np.where(mascara_valida, -dem_preenchido, np.nan)

    minimos = local_minima(np.where(mascara_valida, invertido, np.inf), connectivity=2)
    minimos &= mascara_valida

    rotulos, n_rotulos = ndi.label(minimos, structure=np.ones((3, 3)))
    if n_rotulos == 0:
        raise RuntimeError(
            "Nao foi encontrado nenhum pico/divisor no MDT invertido - "
            "confira se o MDT de entrada e o recorte estao corretos."
        )
    print(f"  {n_rotulos} picos/divisores identificados.")

    # cota (altitude real) de cada pico = valor maximo do MDT preenchido
    # dentro da regiao correspondente ao minimo local
    cota_por_rotulo = ndi.maximum(dem_preenchido, labels=rotulos, index=np.arange(1, n_rotulos + 1))
    tabela_cota = np.zeros(n_rotulos + 1, dtype=np.float64)
    tabela_cota[1:] = cota_por_rotulo

    invertido_para_watershed = np.where(mascara_valida, invertido, np.nanmax(invertido[mascara_valida]) + 1)
    zonas = watershed(invertido_para_watershed, markers=rotulos, mask=mascara_valida)

    cota_por_pixel = tabela_cota[zonas]
    cota_por_pixel = np.where(mascara_valida, cota_por_pixel, nodata)
    zonas = np.where(mascara_valida, zonas, 0)
    return zonas, cota_por_pixel


def reclassificar(array, nodata, faixas):
    resultado = np.full(array.shape, nodata, dtype=np.float64)
    valido = array != nodata
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
    MOSAICO_DEM = pedir_caminho("Caminho do MDT / mosaico raster (ex.: C:\\dados\\mosaicoRMSP.tif): ", "raster")
    AreaEstudo = pedir_caminho("Caminho do shapefile/feature class da area de estudo (ex.: C:\\dados\\AreaEstudo.shp): ", "vetor")
    print()

    srs_saida = srs_de_epsg(EPSG_SAIDA)
    srs_metrica = srs_de_epsg(EPSG_METRICO_BR)
    srs_dem_entrada_padrao = srs_de_epsg(EPSG_DEM_ENTRADA_PADRAO)

    # (a) Reprojeta a area de estudo e o MDT para SIRGAS 2000 Geografico ---
    print("(a) 1/9 - Reprojetando area de estudo (gdal.VectorTranslate)...")
    reprojetar_vetor(AreaEstudo, srs_saida, GPKG, NOME_LIMITE_PROJ)

    print("(a) 2/9 - Reprojetando MDT (gdal.Warp)...")
    reprojetar_raster(MOSAICO_DEM, srs_saida, A_MOSAICO_PROJ, CELL_SIZE, NODATA_PADRAO,
                       srs_entrada_padrao=srs_dem_entrada_padrao)

    # (b) Buffer de 2 km (feito num CRS metrico) + recorte do MDT --------
    print("(b) 3/9 - Buffer de 2 km (osgeo.ogr)...")
    bufferizar_vetor(GPKG, NOME_LIMITE_PROJ, BUFFER_DISTANCIA_M, BUFFER_SEGMENTOS,
                      srs_metrica, srs_saida, NOME_LIMITE_PROJ_BUFFER)

    print("(b) - Recortando o MDT pelo buffer (gdal.Warp com cutline)...")
    recortar_raster_por_mascara(A_MOSAICO_PROJ, GPKG, NOME_LIMITE_PROJ_BUFFER,
                                 B_MOSAICO_LIMITE, NODATA_PADRAO)

    # A partir daqui, trabalha-se direto com as matrizes (numpy) ----------
    dem, nodata, geotransform, projecao = ler_raster(B_MOSAICO_LIMITE)

    # (c) Fill + inverte (c1) ---------------------------------------------
    print("(c) 4/9 - Fill (preencher depressoes) + inverter relevo...")
    preenchido = preencher_depressoes(dem, nodata)
    gravar_raster(C_MOSAICO_FILL, preenchido, nodata, geotransform, projecao)
    gravar_raster(C_MOSAICO_FILL_NEG, np.where(preenchido == nodata, nodata, -preenchido),
                  nodata, geotransform, projecao)

    # (d)-(g) Flow Direction + Sink + Basin + Zonal Statistics (MAXIMUM) ---
    print("(d)-(g) 5/9 a 8/9 - Achando picos/divisores e suas zonas de influencia...")
    zonas, cota_por_zona = achar_picos_e_zonas(preenchido, nodata)
    gravar_raster(E_BASIN, zonas.astype(np.float64), 0, geotransform, projecao)
    gravar_raster(G_SINK_BASIN, cota_por_zona, nodata, geotransform, projecao)

    # (h) Entalhamento = cota do pico da zona - cota real do terreno ------
    print("(h) 9/9 - Calculando entalhamento (cota do pico - cota do terreno)...")
    valido = (preenchido != nodata) & (cota_por_zona != nodata)
    entalhamento = np.where(valido, cota_por_zona - preenchido, nodata)
    gravar_raster(H_ENTALHAMENTO, entalhamento, nodata, geotransform, projecao)

    # (i) Reclassifica em 5 classes de peso (Tabela 5/7, Cap. 5.4.1) ------
    print("(i) Reclassificando (Tabelas 5/7, Cap. 5.4.1 da tese)...")
    reclassificado = reclassificar(entalhamento, nodata, REMAP_ENTALHAMENTO)
    gravar_raster(I_ENTALHAMENTO_RECLA, reclassificado, nodata, geotransform, projecao)

    print()
    print("Concluido.")
    print("h_ (entalhamento, valor continuo em metros por pixel):", H_ENTALHAMENTO)
    print("i_ (entalhamento reclassificado em 5 classes de peso, conforme Ross/Crepani):", I_ENTALHAMENTO_RECLA)


if __name__ == "__main__":
    main()
