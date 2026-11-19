# -*- coding: utf-8 -*-
"""
5_Vulnerabilidade Ambiental - versao software livre (QGIS + Python)
====================================================================
Mesma metodologia do script "5_vulnerabilidade_ambiental.py" (ArcGIS Pro /
arcpy) - ver aquele arquivo para a descricao completa e as fontes
conferidas: o script exportado do ArcMap 10.3
("5_VulnerabilidadeAmbiental_Arc103_v2.py"), a Figura 11 e o Cap. 6.6.1 da
tese (Alex da Silva Sousa, 2024, DOI: 10.11606/T.8.2024.tde-18022025-121027).

Este e o fluxo COMPLETO da tese: parte dos dados brutos (DEM, rasters dos
scripts 1 e 2, vetores de geologia, solos e clima, MapBiomas e o limite) e
chega aos tres produtos finais.

Resumo: a Vulnerabilidade Ambiental (Crepani) e a MEDIA ARITMETICA, pixel a
pixel, de cinco temas ja expressos em vulnerabilidade x 10 (10 a 30):
Relevo ((G+A+D)/3), Geologia, Solos, Clima e Uso e Cobertura da Terra
(Tabela 24). Pixels sem dado (NoData) ficam fora da media daquele pixel
(como o "Cell Statistics" do ArcGIS com "ignorar NoData"): por exemplo,
agua/urbano no mapa de solos e agua no de geologia. Os temas:

  * Relevo   = (Entalhamento + Dimensao Interfluvial + Declividade) / 3
               Entalhamento -> Tabela 8; Dimensao -> Tabela 7;
               Declividade (%) do DEM -> Tabela 9 (fator Z 0,00000956)
  * Geologia, Solos, Clima = campo de vulnerabilidade do vetor x 10
               (geologia: agua 90 -> NoData; solos: urbano 70 e agua 90 ->
               NoData), rasterizados na grade do relevo
  * Uso da terra = MapBiomas reclassificado pela Tabela 24 (x 10)

Tres produtos finais:

  * h_Vuln_CellStatisticNoDataGRSC_noLanduse.tif
        media de Geologia, Relevo, Solos e Clima (sem o uso da terra)
  * h_Vuln_CellStatisticNoData_<nome do raster de uso>.tif
        media dos cinco temas; urbano e agua do uso viram NoData (saem da media)
  * h_Vuln_CellStatisticNoDataUrbAgua_<nome do raster de uso>.tif
        igual ao anterior, com urbano (70) e agua (90) SOBREPOSTOS como mascara

Os resultados sao Float32 (NoData = -9999), recortados pelo contorno exato
do limite. Aquicultura (31) = 3,0 e so a classe 33 vira agua (90), como no
model (diferente do script de Fragilidade).

Diferencas em relacao a versao ArcGIS/arcpy:

  * Tudo e levado DIRETO para a grade do DEM projetado: entalhamento,
    dimensao, vetores e uso da terra seguem essa mesma grade. Como a
    propria grade ja limita a area, o buffer de 2 km e o Clip do model
    deixam de ser necessarios. O limite e rasterizado na grade e usado
    como mascara. Todo o processamento de raster (projetar o DEM,
    declividade, alinhar, rasterizar) e chamado direto na biblioteca GDAL
    do Python do QGIS - nao usa os algoritmos "gdal:*" do Processing, que
    no modo headless podem falhar sem avisar. O QGIS entra para
    recortar/reprojetar os vetores ("native:extractbyextent" e
    "native:reprojectlayer").
  * Declividade: gdal.DEMProcessing (porcentagem, algoritmo de Horn), com
    escala = 1 / fator Z (0,00000956). Nao precisa da extensao 3D Analyst.
  * Reclassify do relevo: mesma regra de faixas do ArcGIS, [limite
    anterior, limite seguinte) - a primeira e a ultima faixa vao ate
    -infinito / +infinito (no model, -5000 e 5000, 200000 ou 2000).
  * As medias sao feitas em blocos de linhas com numpy (nao carrega o
    Estado inteiro na memoria), e a reclassificacao do uso da terra e a
    sobreposicao de urbano/agua sao feitas na hora do calculo (os rasters
    uso_c, uso_c2, uso_c3 e f_ do model nao sao gravados).
  * Classes de uso fora da Tabela 24 viram NoData (o script avisa).
  * Se o raster de uso da terra declarar o valor 0 como NoData (comum em
    GeoTIFFs do MapBiomas), ele e tratado como NoData - o mesmo destino que
    o model da a classe 0 ("0 NODATA").

Entradas (as mesmas do model completo):
  * DEM (mosaico.tif) - qualquer SRC (se nao tiver, assume WGS 84).
  * Entalhamento do Vale (h_entalhamento) e Dimensao Interfluvial Media
    (j_Dimensao): saidas dos scripts 1 e 2 (versao QGIS) - o script
    procura nos locais padrao e, se nao achar, pergunta.
  * Vetores de GEOLOGIA (campo "Vulnerabil"), SOLOS (campo "Vulne") e CLIMA
    (campo "Vulnerabilidade"), com a vulnerabilidade de 1,0 a 3,0 (agua = 9
    e urbano = 7 nos campos de geologia e solos). Vetores em .gdb tambem
    funcionam, ex.: C:\\dados\\GDB Final.gdb\\Camada. O script multiplica o
    campo por 10 (o "Calculate Field" do model) e mostra os valores
    distintos.
  * Uso e Cobertura da Terra: um raster (GeoTIFF etc.) OU uma pasta com
    varios rasters (um por ano - o "Iterate Rasters" do model). O QGIS/GDAL nao
    le raster dentro de geodatabase (.gdb): se o MapBiomas esta numa .gdb,
    exporte antes cada raster para GeoTIFF (no ArcGIS Pro: Copy Raster).
  * Limite vetorial da area de interesse.

Requisitos:
    - QGIS 3.x instalado (traz GDAL, numpy e o "processing" prontos).

Como rodar (tres opcoes - o resultado e identico):

    Opcao 0 - qualquer Python, incluindo o botao "Run" do seu editor:
    O script detecta sozinho se nao esta rodando com o Python do QGIS e,
    se for o caso, procura o "python-qgis.bat" instalado e se relanca
    automaticamente com ele - nao precisa fazer nada manual. So nao
    funciona se o QGIS nao estiver instalado na maquina, ou estiver
    instalado num local que o script nao consegue encontrar sozinho
    (nesse caso, use a Opcao 2 abaixo, apontando o caminho certo).

    Opcao 1 - dentro do QGIS (Console Python):
    1. Abra o QGIS.
    2. Menu Complementos/Plugins > Console Python.
    3. No console, abra o "Editor de script", abra este arquivo .py e
       clique em "Executar script" - ou cole o conteudo direto no
       console.
    4. O script pergunta na tela o DEM, os rasters dos scripts 1 e 2 (se
       nao os achar sozinho), os tres vetores, o uso da terra e o limite.

    Opcao 2 - pelo terminal, sem abrir o QGIS (modo "headless"):
    1. Abra o Prompt de Comando/PowerShell.
    2. Rode (ajuste o caminho do QGIS para a sua instalacao):
           "C:\\Program Files\\QGIS 3.34\\bin\\python-qgis.bat" "C:\\caminho\\para\\5_vulnerabilidade_ambiental_QGIS.py"
    3. Se o comando acima nao existir na sua instalacao, veja dentro da
       pasta "bin" do QGIS por um arquivo parecido (ex.:
       "python-qgis-ltr.bat"), e ajuste tambem a constante
       CAMINHO_INSTALACAO_QGIS no topo deste script se sua instalacao
       estiver em outra pasta/versao.
    Ainda exige o QGIS instalado na maquina (e dele que vem o
    qgis.core/processing por baixo) - so nao precisa mais abrir a janela
    do programa.
"""
import os
import sys
import glob
import subprocess


def relancar_com_python_do_qgis():
    """Se este script for rodado com qualquer Python que nao seja o do
    QGIS (botao "Run" do editor de outro programa, Python do sistema,
    de outro software como o ArcGIS Pro), o "import qgis.core" mais
    abaixo falharia com "ModuleNotFoundError: No module named 'qgis'".
    Esta funcao detecta isso ANTES de importar qualquer coisa que
    dependa do QGIS (ou mesmo numpy) e, se necessario, procura o
    "python-qgis.bat" (instalado junto com o QGIS) e relanca este mesmo
    arquivo com ele - sem precisar que o usuario va procurar o caminho
    certo manualmente."""
    try:
        import qgis.core  # noqa: F401
        return  # ja estamos rodando com o Python do QGIS - nada a fazer
    except ImportError:
        pass

    candidatos = sorted(
        glob.glob(r"C:\Program Files\QGIS *\bin\python-qgis.bat")
        + glob.glob(r"C:\Program Files\QGIS *\bin\python-qgis-ltr.bat")
    )
    if not candidatos:
        sys.exit(
            "Nao encontrei o Python do QGIS (python-qgis.bat) automaticamente.\n"
            "Rode este script com o Python do proprio QGIS - veja a secao "
            "'Como rodar' no cabecalho deste arquivo."
        )

    python_qgis = candidatos[0]  # se houver mais de uma instalacao, usa a primeira encontrada
    print(f"(Este script precisa do Python do QGIS - relancando com '{python_qgis}'...)")
    resultado = subprocess.run([python_qgis, os.path.abspath(__file__)] + sys.argv[1:])
    sys.exit(resultado.returncode)


relancar_com_python_do_qgis()

import numpy as np
from osgeo import gdal, ogr, osr

# No modo headless (python-qgis.bat), o proprio .bat define PYTHONPATH
# apontando so para "<QGIS>/apps/qgis/python", mas o pacote "processing"
# (plugin nativo do QGIS) fica em
# "<QGIS>/apps/qgis/python/plugins/processing" - uma pasta que esse .bat
# nao adiciona ao path. Rodando de dentro do Console Python do QGIS (a
# outra forma de uso), isso nao acontece, pois o QGIS ja adiciona essa
# pasta de plugins ao sys.path sozinho ao iniciar.
try:
    import processing
except ImportError:
    _prefixo_qgis = os.environ.get("QGIS_PREFIX_PATH")
    _pasta_plugins_qgis = (
        os.path.join(_prefixo_qgis, "python", "plugins") if _prefixo_qgis else None
    )
    if _pasta_plugins_qgis and os.path.isdir(_pasta_plugins_qgis):
        sys.path.append(_pasta_plugins_qgis)
        import processing
    else:
        raise
from qgis.core import (
    QgsCoordinateReferenceSystem, QgsRasterLayer, QgsVectorLayer,
)

gdal.UseExceptions()
ogr.UseExceptions()

# ------------------------------------------------------------------
# EXECUCAO "HEADLESS" - roda pelo terminal, sem abrir a janela do QGIS
# ------------------------------------------------------------------
# Continua exigindo o QGIS instalado na maquina (e dele que vem o
# qgis.core/processing por baixo) - so nao precisa mais abrir o programa
# e colar no Console Python. Basta rodar pelo terminal usando o
# "python-qgis.bat" que vem dentro da pasta "bin" da instalacao do QGIS,
# por exemplo:
#
#   "C:\Program Files\QGIS 3.34\bin\python-qgis.bat" "C:\caminho\para\5_vulnerabilidade_ambiental_QGIS.py"
#
# Se o QGIS estiver instalado em outra pasta/versao, ajuste
# CAMINHO_INSTALACAO_QGIS abaixo (ou defina a variavel de ambiente
# QGIS_PREFIX_PATH antes de rodar). Se este script for executado de
# dentro do proprio Console Python do QGIS (como antes), nada muda -
# ele detecta que o QGIS ja esta aberto e pula esta inicializacao.
CAMINHO_INSTALACAO_QGIS = r"C:\Program Files\QGIS 3.34"


def iniciar_qgis_headless():
    """Inicializa o QGIS sem abrir a interface grafica. Se o script ja
    estiver rodando dentro do Console Python do QGIS, nao faz nada
    (retorna None) - so e usada quando se roda pelo terminal/atalho."""
    from qgis.core import QgsApplication

    if QgsApplication.instance() is not None:
        return None

    caminho_instalacao = os.environ.get("QGIS_PREFIX_PATH", CAMINHO_INSTALACAO_QGIS)
    QgsApplication.setPrefixPath(caminho_instalacao, True)
    qgs = QgsApplication([], False)
    qgs.initQgis()

    from processing.core.Processing import Processing
    Processing.initialize()

    return qgs


def encerrar_qgis_headless(qgs):
    """Fecha a instancia headless do QGIS, se uma foi aberta por
    iniciar_qgis_headless() (nao faz nada se o script rodou dentro do
    Console Python do QGIS)."""
    if qgs is not None:
        qgs.exitQgis()


# ------------------------------------------------------------------
# PARAMETROS - ajuste para o seu ambiente
# ------------------------------------------------------------------
WORKSPACE = r"C:\alexgeopro\VulnerabilidadeAmbiental_QGIS"  # pasta - criada automaticamente

# Saidas dos scripts 1 e 2 (procuradas automaticamente; se nao existirem,
# o script pergunta o caminho na tela).
ENTALHAMENTO_PADRAO = r"C:\alexgeopro\Entalhamento_QGIS\h_entalhamento.tif"
DIMENSAO_PADRAO = r"C:\alexgeopro\DimensaoInterfluvial_QGIS\j_Dimensao.tif"

CELL_SIZE = 0.00027777778   # ~30 m em graus (a mesma do model: "0,00027777778")
EPSG_SAIDA = 4674           # SIRGAS 2000 Geografico
EPSG_DEM_PADRAO = 4326      # usado so se o DEM nao tiver SRC definido
EPSG_USO_ENTRADA_PADRAO = 4326  # usado so se o raster de uso nao tiver SRC definido
NODATA = -9999
LINHAS_BLOCO = 256          # linhas lidas de cada vez nos calculos (reduza se faltar memoria)

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

# Filtro opcional: se o uso da terra for uma pasta com varios rasters, so
# processa os que contem este texto no nome ("" = todos).
FILTRO_NOME_USO = ""
EXTENSOES_RASTER_USO = ("*.tif", "*.tiff", "*.vrt", "*.img")

# False: se os resultados ja existirem, pula essa etapa (permite retomar
# uma execucao interrompida e reaproveitar o Relevo, Solos, Geologia e
# Clima ja calculados). True: refaz tudo.
SOBRESCREVER = False

# False: apaga os rasters intermediarios (DEM projetado, declividade,
# rasters alinhados, vetores reprojetados) ao terminar. Os quatro temas
# (rel_e2_Relevo, geol_d2_Rochas, ped_d2_solos, cli_c_clima) e os tres
# produtos finais sao sempre mantidos.
MANTER_INTERMEDIARIOS = False

# Reclassificacao do uso da terra: codigo MapBiomas (colecao 8) ->
# vulnerabilidade x 10 (Tabela 24 da tese; 24 urbano = 70; 33 agua = 90),
# exatamente como no model exportado. O codigo 0 (sem informacao) NAO esta
# aqui de proposito: no model ele vira NoData ("0 NODATA").
REMAP_USO = {
    3: 16, 4: 21, 5: 14, 9: 29, 11: 30, 12: 27, 13: 30, 15: 28, 19: 30,
    20: 30, 21: 30, 23: 30, 24: 70, 25: 30, 29: 30, 30: 30, 31: 30, 32: 30,
    33: 90, 39: 30, 41: 30, 46: 29, 47: 29, 48: 29, 49: 14, 50: 27, 62: 30,
}
URBANO = 70
AGUA = 90

# Saidas fixas (as de uso da terra levam o nome do raster de origem).
# Os quatro temas levam os mesmos nomes do model.
REL_E2_RELEVO = os.path.join(WORKSPACE, "rel_e2_Relevo.tif")
GEOL_D2_ROCHAS = os.path.join(WORKSPACE, "geol_d2_Rochas.tif")
PED_D2_SOLOS = os.path.join(WORKSPACE, "ped_d2_solos.tif")
CLI_C_CLIMA = os.path.join(WORKSPACE, "cli_c_clima.tif")
H_SEM_USO = os.path.join(WORKSPACE, "h_Vuln_CellStatisticNoDataGRSC_noLanduse.tif")

# Intermediarios (apagados ao final, a menos que MANTER_INTERMEDIARIOS = True)
GPKG_LIMITE = os.path.join(WORKSPACE, "lim_a_LimiteSirgas.gpkg")
MASCARA_LIMITE = os.path.join(WORKSPACE, "lim_b_MascaraLimite.tif")
REL_A_MOSAICO = os.path.join(WORKSPACE, "rel_a_mosaico.tif")                 # DEM projetado
REL_B_SLOPE = os.path.join(WORKSPACE, "rel_b_slope.tif")                     # declividade (%)
REL_C_ENTALHAMENTO = os.path.join(WORKSPACE, "rel_c_entalhamento.tif")       # alinhado ao DEM
REL_C_DIMENSAO = os.path.join(WORKSPACE, "rel_c_Dimensao.tif")               # alinhado ao DEM
GEOL_A_GPKG = os.path.join(WORKSPACE, "geol_a_Geologico_Sirgas.gpkg")
GEOL_C_RASTER = os.path.join(WORKSPACE, "geol_c_Geologico_Raster.tif")
PED_A_GPKG = os.path.join(WORKSPACE, "ped_a_solos_Sirgas.gpkg")
PED_C_RASTER = os.path.join(WORKSPACE, "ped_c_solos_Raster.tif")
CLI_A_GPKG = os.path.join(WORKSPACE, "cli_a_clima_Sirgas.gpkg")
CLI_C_RASTER = os.path.join(WORKSPACE, "cli_c_clima_Raster.tif")

OPCOES_TIF = ["COMPRESS=LZW", "TILED=YES"]
SRC_SAIDA = f"EPSG:{EPSG_SAIDA}"

# ------------------------------------------------------------------
# Funcoes auxiliares - vetor e entrada de caminhos (QGIS)
# ------------------------------------------------------------------
def uri_vetor(caminho):
    """Permite usar camadas de uma File Geodatabase pelo caminho do
    ArcGIS (ex.: C:\\dados\\GDB Final.gdb\\Camada) - converte para o
    formato do QGIS ("C:\\dados\\GDB Final.gdb|layername=Camada")."""
    pos = caminho.lower().find(".gdb")
    if pos == -1:
        return caminho
    fim = pos + len(".gdb")
    fonte, resto = caminho[:fim], caminho[fim:].strip("\\/")
    return f"{fonte}|layername={resto}" if resto else fonte


def abre_como(caminho, tipo):
    """True se o QGIS conseguir abrir o dado como 'tipo' (raster,
    pasta_ou_raster ou vetor)."""
    if tipo == "raster":
        return QgsRasterLayer(caminho, "teste").isValid()
    if tipo == "pasta_ou_raster":
        return os.path.isdir(caminho) or QgsRasterLayer(caminho, "teste").isValid()
    return QgsVectorLayer(uri_vetor(caminho), "teste", "ogr").isValid()


def reprojetar_vetor(caminho_entrada, caminho_saida_gpkg, bounds=None):
    """Equivalente a 'Clip' + 'Project' do ArcGIS: reprojeta o vetor para
    SIRGAS 2000 geografico ('native:reprojectlayer'). Se 'bounds' (xmin,
    ymin, xmax, ymax, em SIRGAS 2000) for dado, antes disso so as feicoes
    que tocam essa extensao sao extraidas ('native:extractbyextent') -
    muito mais rapido para vetores grandes (ex.: clima do Brasil)."""
    apagar_arquivo(caminho_saida_gpkg)
    entrada = uri_vetor(caminho_entrada)
    if bounds is not None:
        xmin, ymin, xmax, ymax = bounds
        entrada = processing.run("native:extractbyextent", {
            "INPUT": entrada,
            "EXTENT": f"{xmin},{xmax},{ymin},{ymax} [{SRC_SAIDA}]",
            "CLIP": False,
            "OUTPUT": "TEMPORARY_OUTPUT",
        })["OUTPUT"]
    processing.run("native:reprojectlayer", {
        "INPUT": entrada,
        "TARGET_CRS": QgsCoordinateReferenceSystem(SRC_SAIDA),
        "OUTPUT": caminho_saida_gpkg,
    })


# ------------------------------------------------------------------
# Funcoes auxiliares
# ------------------------------------------------------------------
def garantir_pasta(caminho):
    if not os.path.isdir(caminho):
        print(f"Criando pasta '{caminho}'...")
        os.makedirs(caminho)


def pedir_caminho(mensagem, tipo):
    """Pergunta um caminho ao usuario e so aceita quando o dado puder
    realmente ser aberto como 'tipo' (raster, pasta_ou_raster, vetor)."""
    while True:
        caminho = input(mensagem).strip().strip('"')
        if not caminho:
            print("  -> Caminho vazio, tente novamente.")
            continue
        if abre_como(caminho, tipo):
            return caminho
        print(f"  -> Nao consegui abrir '{caminho}' como {tipo}. Confira o caminho e tente de novo.")


def achar_ou_pedir_caminho(caminho_padrao, descricao, tipo):
    """Tenta usar automaticamente o caminho padrao (saida dos scripts 1/2);
    se nao existir/abrir, pergunta o caminho na tela."""
    if abre_como(caminho_padrao, tipo):
        print(f"  {descricao}: encontrado automaticamente em '{caminho_padrao}'.")
        return caminho_padrao
    print(f"  {descricao}: nao encontrei em '{caminho_padrao}'.")
    return pedir_caminho(f"  Informe o caminho de {descricao}: ", tipo)


def srs_de_epsg(epsg):
    """Cria um osr.SpatialReference a partir de um codigo EPSG, forcando
    a ordem tradicional de eixos (long, lat / x, y) - evita o bug
    classico do GDAL 3+ de inverter a ordem dos eixos em SRCs
    geograficos."""
    srs = osr.SpatialReference()
    srs.ImportFromEPSG(epsg)
    srs.SetAxisMappingStrategy(osr.OAMS_TRADITIONAL_GIS_ORDER)
    return srs


def apagar_arquivo(caminho):
    """Apaga um raster/vetor (e os arquivos auxiliares) se existir."""
    if os.path.exists(caminho):
        os.remove(caminho)
    for extra in (caminho + ".aux.xml", caminho + "-wal", caminho + "-shm"):
        if os.path.exists(extra):
            os.remove(extra)


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


def grade_do_raster(caminho):
    """Devolve (colunas, linhas, geotransform, bounds) do raster - 'bounds'
    = (xmin, ymin, xmax, ymax). E a grade de referencia de todo o resto."""
    ds = gdal.Open(caminho)
    colunas, linhas = ds.RasterXSize, ds.RasterYSize
    gt = ds.GetGeoTransform()
    ds = None
    bounds = (gt[0], gt[3] + gt[5] * linhas, gt[0] + gt[1] * colunas, gt[3])
    return colunas, linhas, gt, bounds


def raster_sem_srs(caminho):
    ds = gdal.Open(caminho)
    sem_srs = not ds.GetProjection()
    ds = None
    return sem_srs


def projetar_dem(caminho_entrada, caminho_saida):
    """'Project Raster' do model: DEM -> SIRGAS 2000 geografico, celula de
    CELL_SIZE graus, interpolacao BILINEAR (como no model - o DEM e um
    dado continuo)."""
    opcoes = dict(
        dstSRS=SRC_SAIDA, xRes=CELL_SIZE, yRes=CELL_SIZE, resampleAlg="bilinear",
        dstNodata=NODATA, outputType=gdal.GDT_Float32, creationOptions=OPCOES_TIF,
        multithread=True,
    )
    if raster_sem_srs(caminho_entrada):
        opcoes["srcSRS"] = f"EPSG:{EPSG_DEM_PADRAO}"
    ds = gdal.Warp(caminho_saida, caminho_entrada, **opcoes)
    if ds is None:
        raise RuntimeError("Falha ao reprojetar o DEM.")
    ds = None


def calcular_declividade(caminho_dem, caminho_saida):
    """'Slope' do model: declividade em PORCENTAGEM (PERCENT_RISE) com
    fator Z = Z_FACTOR. No GDAL a escala e a razao entre a unidade
    horizontal (graus) e a vertical (m), ou seja, 1 / fator Z."""
    ds = gdal.DEMProcessing(
        caminho_saida, caminho_dem, "slope", slopeFormat="percent",
        scale=1.0 / Z_FACTOR, computeEdges=True, creationOptions=OPCOES_TIF,
    )
    if ds is None:
        raise RuntimeError("Falha ao calcular a declividade.")
    ds = None


def alinhar_raster(caminho_entrada, caminho_saida, grade, tipo, epsg_se_sem_srs):
    """Equivalente a 'Project Raster' + 'Extract by Mask' do ArcGIS: leva
    um raster para a grade de referencia (SRC, extensao, resolucao e
    origem) com vizinho mais proximo, numa unica passada (gdal.Warp).
    Chamado direto na biblioteca GDAL: qualquer erro aparece na tela."""
    colunas, linhas, _, bounds = grade
    opcoes = dict(
        dstSRS=SRC_SAIDA, outputBounds=bounds, width=colunas, height=linhas,
        resampleAlg="near", dstNodata=NODATA, outputType=tipo,
        creationOptions=OPCOES_TIF, multithread=True,
    )
    if raster_sem_srs(caminho_entrada):
        opcoes["srcSRS"] = f"EPSG:{epsg_se_sem_srs}"
    ds = gdal.Warp(caminho_saida, caminho_entrada, **opcoes)
    if ds is None:
        raise RuntimeError(f"Falha ao alinhar '{caminho_entrada}' a grade de referencia.")
    ds = None


def nome_camada(caminho_gpkg):
    """Nome da (primeira) camada de um GPKG - o gdal.Rasterize precisa
    dele."""
    ds = ogr.Open(caminho_gpkg)
    nome = ds.GetLayer(0).GetName()
    ds = None
    return nome


def rasterizar_mascara(caminho_gpkg, caminho_saida, grade):
    """Equivalente ao 'Extract by Mask' final do model: rasteriza o limite
    (1 dentro, 0 fora; pixels cujo centro cai dentro do poligono) na grade
    de referencia. Os resultados sao mascarados por este raster."""
    colunas, linhas, _, bounds = grade
    apagar_arquivo(caminho_saida)
    opcoes = gdal.RasterizeOptions(
        format="GTiff", outputType=gdal.GDT_Byte, creationOptions=OPCOES_TIF,
        outputBounds=bounds, width=colunas, height=linhas,
        burnValues=[1], initValues=[0], layers=[nome_camada(caminho_gpkg)],
    )
    ds = gdal.Rasterize(caminho_saida, caminho_gpkg, options=opcoes)
    if ds is None:
        raise RuntimeError(f"Falha ao rasterizar o limite '{caminho_gpkg}'.")
    ds = None


def conferir_campo(rotulo, caminho_gpkg, campo):
    """Confere o campo de vulnerabilidade do vetor (ja reprojetado):
    devolve o nome real do campo (sem diferenciar maiusculas), mostra os
    valores distintos ja multiplicados por 10 e avisa se parecerem fora
    do esperado (10 a 30, mais 70/90). Interrompe se o campo nao existir."""
    ds = ogr.Open(caminho_gpkg)
    camada = ds.GetLayer(0)
    definicao = camada.GetLayerDefn()
    nomes = [definicao.GetFieldDefn(i).GetName() for i in range(definicao.GetFieldCount())]
    real = next((n for n in nomes if n.lower() == campo.lower()), None)
    if real is None:
        ds = None
        raise SystemExit(
            f"O vetor de {rotulo} nao tem o campo '{campo}'. Campos encontrados: {nomes}. "
            "Ajuste CAMPO_GEOLOGIA / CAMPO_SOLOS / CAMPO_CLIMA no topo do script."
        )
    valores = set()
    for feicao in camada:
        v = feicao.GetField(real)
        if v is not None:
            try:
                valores.add(round(float(v) * 10, 4))
            except (TypeError, ValueError):
                pass
    ds = None
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
        ds = gdal.Open(caminho)   # manter a referencia: sem ela o GDAL fecha a banda
        minimo, maximo = ds.GetRasterBand(1).ComputeRasterMinMax(False)
        ds = None
    except Exception:
        print(f"  {rotulo}: nao consegui calcular minimo/maximo.")
        return
    print(f"  {rotulo}: minimo {minimo:g}, maximo {maximo:g}")
    if maximo > 30.5 or minimo < 9.5:
        print(f"    AVISO: '{rotulo}' deveria ficar entre 10 e 30 - confira o dado de entrada.")


def ler_bloco(banda, nodata, y, n, colunas):
    """Le 'n' linhas a partir de 'y' como float32 e devolve
    (valores, mascara_de_pixels_validos)."""
    a = banda.ReadAsArray(0, y, colunas, n).astype(np.float32)
    valido = np.isfinite(a)
    if nodata is not None:
        valido &= (a != np.float32(nodata))
    return a, valido


def calcular_em_blocos(caminhos_saida, entradas, funcao):
    """Raster Calculator / Cell Statistics em blocos de linhas: le as
    mesmas linhas de todos os rasters de 'entradas' (todos na mesma grade),
    aplica funcao(lista_de_(valores, validos)) -> lista de arrays float32
    (NODATA onde nao ha resultado) e grava cada um no seu raster de saida."""
    dss = [gdal.Open(c) for c in entradas]
    bandas = [d.GetRasterBand(1) for d in dss]
    nodatas = [b.GetNoDataValue() for b in bandas]
    colunas, linhas = dss[0].RasterXSize, dss[0].RasterYSize
    for d in dss:
        if (d.RasterXSize, d.RasterYSize) != (colunas, linhas):
            raise RuntimeError("Os rasters nao estao na mesma grade - isso nao deveria acontecer.")

    driver = gdal.GetDriverByName("GTiff")
    saidas, bandas_saida = [], []
    for caminho in caminhos_saida:
        apagar_arquivo(caminho)
        s = driver.Create(caminho, colunas, linhas, 1, gdal.GDT_Float32, options=OPCOES_TIF)
        s.SetGeoTransform(dss[0].GetGeoTransform())
        s.SetProjection(dss[0].GetProjection())
        b = s.GetRasterBand(1)
        b.SetNoDataValue(NODATA)
        saidas.append(s)
        bandas_saida.append(b)

    for y in range(0, linhas, LINHAS_BLOCO):
        n = min(LINHAS_BLOCO, linhas - y)
        dados = [ler_bloco(b, nd, y, n, colunas) for b, nd in zip(bandas, nodatas)]
        for banda_saida, resultado in zip(bandas_saida, funcao(dados)):
            banda_saida.WriteArray(resultado, 0, y)

    for b in bandas_saida:
        b.FlushCache()
    saidas = None
    bandas_saida = None
    dss = None


# --- funcoes de calculo (uma por etapa do model) ---------------------
def classe_por_limites(valores, limites, crescente):
    """'Reclassify' por faixas: [limite anterior, limite seguinte) - a
    mesma regra do ArcGIS. 21 classes de 10 a 30; 'crescente' = a classe
    sobe com o valor (Entalhamento, Declividade); falso = desce com o
    valor (Dimensao Interfluvial)."""
    indice = np.digitize(np.asarray(valores, dtype=np.float64), limites)
    return (10 + indice) if crescente else (30 - indice)


def f_relevo(dados):
    """Vulnerabilidade do Relevo = (G + A + D) / 3, x10:
    dados = [Entalhamento (m), Dimensao Interfluvial (m), Declividade (%)].
    Cada um e reclassificado (Tabelas 8, 7 e 9), e a media aritmetica das
    tres classes (10 a 30) e o tema Relevo (rel_e2_Relevo). Onde falta
    qualquer um dos tres, o resultado e NoData (como na Raster Calculator)."""
    (ent, v_ent), (dim, v_dim), (decl, v_decl) = dados
    ok = v_ent & v_dim & v_decl
    a = classe_por_limites(ent, LIMITES_ENTALHAMENTO, True)
    g = classe_por_limites(dim, LIMITES_DIMENSAO, False)
    d = classe_por_limites(decl, LIMITES_DECLIVIDADE, True)
    relevo = (a + g + d) / 3.0
    return [np.where(ok, relevo, NODATA).astype(np.float32)]


def criar_f_tema_vetor(valores_excluidos):
    """Tema vindo de vetor (geologia, solos, clima): campo x 10 (o
    'Calculate Field' do model) e os valores de 'valores_excluidos' (agua
    = 90 na geologia; urbano = 70 e agua = 90 nos solos) viram NoData, para
    sairem da media (os 'Reclassify' do model)."""
    def f_tema(dados):
        bruto, valido = dados[0]
        v = np.round(bruto.astype(np.float64) * 10, 4)
        ok = valido.copy()
        for excluido in valores_excluidos:
            ok &= ~np.isclose(v, excluido)
        return [np.where(ok, v, NODATA).astype(np.float32)]
    return f_tema


def media_ignorando_nodata(lista):
    """Cell Statistics MEAN com 'ignorar NoData' (DATA): media apenas dos
    temas que tem valor em cada pixel. Devolve (media, tem_resultado)."""
    soma = np.zeros(lista[0][0].shape, dtype=np.float32)
    quantos = np.zeros(soma.shape, dtype=np.int16)
    for valores, valido in lista:
        soma += np.where(valido, valores, 0)
        quantos += valido
    media = soma / np.maximum(quantos, 1)
    return media, quantos > 0


def dentro_do_limite(dado_mascara):
    valores, valido = dado_mascara
    return valido & (valores == 1)


def f_sem_uso(dados):
    """Vulnerabilidade sem o uso da terra: media de Relevo, Geologia, Solos
    e Clima (GRSC), recortada pelo limite."""
    media, ok = media_ignorando_nodata(dados[:4])
    ok &= dentro_do_limite(dados[4])
    return [np.where(ok, media, NODATA).astype(np.float32)]


def criar_f_uso(classes_desconhecidas):
    """Devolve a funcao que reclassifica o uso (Tabela 24 x 10) e calcula
    os dois produtos do ano: [media sem urbano/agua, media com urbano e
    agua sobrepostos]. Classes fora da tabela viram NoData e sao
    registradas em 'classes_desconhecidas'."""
    lut = np.full(256, np.nan, dtype=np.float32)
    for origem, destino in REMAP_USO.items():
        lut[origem] = destino

    def f_uso(dados):
        temas = dados[:4]
        uso, valido_uso = dados[5]

        codigo = np.where(valido_uso, uso, 0).astype(np.int64)
        dentro_lut = valido_uso & (codigo >= 0) & (codigo < len(lut))
        uso_c = np.where(dentro_lut, lut[np.clip(codigo, 0, len(lut) - 1)], np.nan)

        for c in np.unique(uso[valido_uso]):
            if int(c) != 0 and int(c) not in REMAP_USO:
                classes_desconhecidas.add(int(c))

        tem_uso_c = np.isfinite(uso_c)
        urbano_agua = tem_uso_c & ((uso_c == URBANO) | (uso_c == AGUA))
        so_vegetacao = tem_uso_c & ~urbano_agua   # uso_c2: urbano/agua = NoData

        media, ok = media_ignorando_nodata(temas + [(uso_c, so_vegetacao)])
        no_limite = dentro_do_limite(dados[4])

        sem_mascara = np.where(ok & no_limite, media, NODATA)
        # Mosaic To New Raster (FIRST): urbano/agua por cima da media
        com_mascara = np.where(urbano_agua, uso_c, media)
        com_mascara = np.where((ok | urbano_agua) & no_limite, com_mascara, NODATA)
        return [sem_mascara.astype(np.float32), com_mascara.astype(np.float32)]

    return f_uso


# --- etapas maiores ---------------------------------------------------
def rasterizar_campo(caminho_gpkg, campo, caminho_saida, grade):
    """'Feature to Raster' do model: rasteriza o campo de vulnerabilidade
    (pixels cujo centro cai dentro do poligono) na grade de referencia."""
    colunas, linhas, _, bounds = grade
    apagar_arquivo(caminho_saida)
    opcoes = gdal.RasterizeOptions(
        format="GTiff", outputType=gdal.GDT_Float32, creationOptions=OPCOES_TIF,
        outputBounds=bounds, width=colunas, height=linhas, attribute=campo,
        initValues=[NODATA], noData=NODATA, layers=[nome_camada(caminho_gpkg)],
    )
    ds = gdal.Rasterize(caminho_saida, caminho_gpkg, options=opcoes)
    if ds is None:
        raise RuntimeError(f"Falha ao rasterizar o campo '{campo}' de '{caminho_gpkg}'.")
    ds = None


def construir_relevo(dem, entalhamento, dimensao):
    """Tema RELEVO: (Entalhamento + Dimensao Interfluvial + Declividade) / 3,
    x10 -> rel_e2_Relevo. A grade do DEM projetado e a referencia."""
    print("   DEM -> SIRGAS 2000 (bilinear) e declividade em %...")
    projetar_dem(dem, REL_A_MOSAICO)
    calcular_declividade(REL_A_MOSAICO, REL_B_SLOPE)
    grade = grade_do_raster(REL_A_MOSAICO)
    print("   Entalhamento e Dimensao Interfluvial: alinhar a grade do DEM...")
    alinhar_raster(entalhamento, REL_C_ENTALHAMENTO, grade, gdal.GDT_Float32, EPSG_SAIDA)
    alinhar_raster(dimensao, REL_C_DIMENSAO, grade, gdal.GDT_Float32, EPSG_SAIDA)
    print("   Reclassificar (Tabelas 8, 7 e 9) e tirar a media...")
    calcular_em_blocos([REL_E2_RELEVO], [REL_C_ENTALHAMENTO, REL_C_DIMENSAO, REL_B_SLOPE], f_relevo)
    if not MANTER_INTERMEDIARIOS:
        for tmp in (REL_A_MOSAICO, REL_B_SLOPE, REL_C_ENTALHAMENTO, REL_C_DIMENSAO):
            apagar_arquivo(tmp)


def construir_tema_vetor(rotulo, vetor, campo, valores_excluidos, gpkg, raster_bruto, saida, grade):
    """Tema vindo de vetor (geologia, solos ou clima): reprojeta (so a
    parte que cai na grade) -> confere o campo -> rasteriza -> x10 e
    reclassifica."""
    reprojetar_vetor(vetor, gpkg, grade[3])
    campo_real = conferir_campo(rotulo, gpkg, campo)
    rasterizar_campo(gpkg, campo_real, raster_bruto, grade)
    calcular_em_blocos([saida], [raster_bruto], criar_f_tema_vetor(valores_excluidos))
    if not MANTER_INTERMEDIARIOS:
        apagar_arquivo(gpkg)
        apagar_arquivo(raster_bruto)


# ------------------------------------------------------------------
# Programa principal
# ------------------------------------------------------------------
def main():
    garantir_pasta(WORKSPACE)

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

    # 1. Limite -> SIRGAS 2000 -----------------------------------------------------
    print("1/5 - Limite da area: SIRGAS 2000...")
    reprojetar_vetor(limite, GPKG_LIMITE)

    # 2. Relevo --------------------------------------------------------------------
    print("2/5 - Tema RELEVO: (entalhamento + dimensao interfluvial + declividade) / 3 ...")
    if os.path.exists(REL_E2_RELEVO) and not SOBRESCREVER:
        print("   rel_e2_Relevo ja existe - usando o existente (SOBRESCREVER = True refaz).")
    else:
        construir_relevo(dem, entalhamento, dimensao)
    grade = grade_do_raster(REL_E2_RELEVO)  # TODOS os outros rasters seguem esta grade

    # 3. Geologia, solos e clima (vetores) -------------------------------------------
    print("3/5 - Temas GEOLOGIA, SOLOS e CLIMA: vetor -> raster na grade do relevo...")
    temas_vetor = (
        ("Geologia", geologia, CAMPO_GEOLOGIA, (AGUA,), GEOL_A_GPKG, GEOL_C_RASTER, GEOL_D2_ROCHAS),
        ("Solos", solos, CAMPO_SOLOS, (URBANO, AGUA), PED_A_GPKG, PED_C_RASTER, PED_D2_SOLOS),
        ("Clima", clima, CAMPO_CLIMA, (), CLI_A_GPKG, CLI_C_RASTER, CLI_C_CLIMA),
    )
    for rotulo, vetor, campo, excluidos, gpkg, bruto, saida in temas_vetor:
        if os.path.exists(saida) and not SOBRESCREVER:
            print(f"   {rotulo}: {os.path.basename(saida)} ja existe - usando o existente.")
            continue
        construir_tema_vetor(rotulo, vetor, campo, excluidos, gpkg, bruto, saida, grade)
    rasterizar_mascara(GPKG_LIMITE, MASCARA_LIMITE, grade)
    print("   Conferencia dos quatro temas (devem ficar entre 10 e 30):")
    for rotulo, caminho in (("Relevo", REL_E2_RELEVO), ("Geologia", GEOL_D2_ROCHAS),
                            ("Solos", PED_D2_SOLOS), ("Clima", CLI_C_CLIMA)):
        resumo_tema(rotulo, caminho)
    temas = [REL_E2_RELEVO, GEOL_D2_ROCHAS, PED_D2_SOLOS, CLI_C_CLIMA]   # ordem do Cell Statistics do model

    # 4. Vulnerabilidade SEM o uso da terra ------------------------------------------
    print("4/5 - Vulnerabilidade sem o uso da terra (media de Relevo, Geologia, Solos e Clima)...")
    calcular_em_blocos([H_SEM_USO], temas + [MASCARA_LIMITE], f_sem_uso)

    # 5. Uso e cobertura da terra - um resultado por raster -----------------------------
    print(f"5/5 - Uso e Cobertura da Terra ({len(rasters_uso)} raster(s))...")
    resultados = []
    for i, uso_original in enumerate(rasters_uso, start=1):
        nome = os.path.splitext(os.path.basename(uso_original))[0]
        saida_nodata = os.path.join(WORKSPACE, f"h_Vuln_CellStatisticNoData_{nome}.tif")
        saida_mascara = os.path.join(WORKSPACE, f"h_Vuln_CellStatisticNoDataUrbAgua_{nome}.tif")
        print(f"  [{i}/{len(rasters_uso)}] {nome} ...", end=" ", flush=True)

        if os.path.exists(saida_nodata) and os.path.exists(saida_mascara) and not SOBRESCREVER:
            print("ja existem - pulando.")
            resultados.append((saida_nodata, saida_mascara))
            continue

        uso_b = os.path.join(WORKSPACE, f"uso_b_{nome}_Alinhado.tif")

        # Project Raster + Extract by Mask -> grade de referencia
        alinhar_raster(uso_original, uso_b, grade, gdal.GDT_Int16, EPSG_USO_ENTRADA_PADRAO)

        # Reclassify (Tabela 24 x 10) + Cell Statistics + mascara urbano/agua
        desconhecidas = set()
        calcular_em_blocos([saida_nodata, saida_mascara], temas + [MASCARA_LIMITE, uso_b],
                           criar_f_uso(desconhecidas))
        if desconhecidas:
            print(f"\n    AVISO: classes fora da Tabela 24 (viraram NoData): {sorted(desconhecidas)}", end=" ")

        if not MANTER_INTERMEDIARIOS:
            apagar_arquivo(uso_b)
        resultados.append((saida_nodata, saida_mascara))
        print("ok.")

    if not MANTER_INTERMEDIARIOS:
        apagar_arquivo(MASCARA_LIMITE)
        apagar_arquivo(GPKG_LIMITE)

    print()
    print("Concluido.")
    print("Temas (vulnerabilidade x 10):")
    for caminho in temas:
        print("  ", caminho)
    print("Vulnerabilidade sem o uso da terra (Relevo, Geologia, Solos, Clima):", H_SEM_USO)
    print("Vulnerabilidade Ambiental por uso da terra (NoData = urbano/agua fora da media | UrbAgua = urbano 70 e agua 90 por cima):")
    for sem_mascara, com_mascara in resultados:
        print("  ", sem_mascara)
        print("  ", com_mascara)


if __name__ == "__main__":
    _qgs = iniciar_qgis_headless()
    try:
        main()
    finally:
        encerrar_qgis_headless(_qgs)
