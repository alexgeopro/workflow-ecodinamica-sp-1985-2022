# -*- coding: utf-8 -*-
"""
4_Fragilidade Ambiental - versao software livre (QGIS + Python)
================================================================
Mesma metodologia do script "4_fragilidade_ambiental.py" (ArcGIS Pro /
arcpy), reescrita usando apenas ferramentas livres: QGIS (framework
"processing") + GDAL + numpy, que ja vem dentro do Python do proprio
QGIS.

Baseado no model "4_FragilidadeAmbiental" da toolbox "1_Ferramentas Finais
da Tese.tbx", conferido contra o script exportado nativamente do ArcMap
10.3 ("4_FragilidadeAmbiental_Arc103.py"), a Tabela 24 (Cap. 6.5) e o
Cap. 6.6.2 da tese (Alex da Silva Sousa, 2024,
DOI: 10.11606/T.8.2024.tde-18022025-121027).

Metodologia (identica a versao ArcGIS): a Fragilidade Ambiental e uma
matriz de QUATRO algarismos obtida SOMANDO, pixel a pixel, quatro rasters
tematicos:

    milhar   -> Relevo (Grau de Dissecacao reclassificado)    1000 a 5000
    centena  -> Solos (campo "Frag" x 100)                     100 a  500
    dezena   -> Uso e Cobertura da Terra (MapBiomas, Tab. 24)   10 a   50
    unidade  -> Clima (campo "Fragilidade", WorldClim)           1 a    5

1111 = menor fragilidade possivel; 5555 = maior. Urbano = algarismo 7 e
agua = algarismo 9 (ja vem dos dados de entrada e da tabela de uso).
Apenas o dado climatico do WorldClim (vetor ja classificado) e usado aqui.

Diferencas em relacao a versao ArcGIS/arcpy:

  * Cada dado de entrada e levado DIRETO para a grade do raster de relevo
    (o Grau de Dissecacao do script 3): os vetores de solo e clima sao
    reprojetados ("native:reprojectlayer") e rasterizados
    ("gdal:rasterize") nessa grade, e cada raster de uso da terra e
    reprojetado/reamostrado ("gdal:warpreproject", vizinho mais proximo -
    dado de classes, nao pode interpolar) nela. Como a propria grade ja
    limita a area, o buffer de 2 km e o recorte intermediario do model
    deixam de ser necessarios - o resultado dentro do limite e
    equivalente. No fim, o resultado e mascarado pelo contorno exato do
    limite ("gdal:cliprasterbymasklayer").
  * As somas sao feitas com numpy em blocos de linhas (nao carrega o
    Estado inteiro na memoria), e a reclassificacao do uso da terra e feita
    na hora da soma (o raster "uso_c ... Fragil" do model nao e gravado).
  * Classes de uso fora da Tabela 24 viram NoData (o script avisa).
  * Se o raster de uso da terra declarar o valor 0 como NoData (comum em
    GeoTIFFs do MapBiomas), ele e tratado como NoData, e nao como a classe
    "0 - sem informacao" (que o model reclassificava para 90).

Entradas:
  * Grau de Dissecacao - Fragilidade (saida do script 3, versao QGIS, local
    padrao abaixo - ou informe o caminho na tela).
  * Mapa pedologico (vetor com campo "Frag").
  * Vetor climatico ja classificado (WorldClim, campo "Fragilidade").
  * Uso e Cobertura da Terra: um raster (GeoTIFF etc.) OU uma pasta com
    varios rasters (um por ano - o "Iterate Rasters" do model). O QGIS/GDAL
    nao le raster dentro de geodatabase (.gdb): se o MapBiomas esta numa
    .gdb, exporte antes cada raster para GeoTIFF (no ArcGIS Pro: Copy
    Raster).
  * Limite vetorial da area de interesse.
  Vetores em .gdb tambem funcionam (ex.: C:\\dados\\GDB Final.gdb\\Camada).

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
    4. O script procura sozinho o Grau de Dissecacao (saida do script 3,
       versao QGIS); se nao encontrar, pergunta o caminho na tela. Tambem
       pergunta: solos, clima, uso da terra e limite da area de interesse.

    Opcao 2 - pelo terminal, sem abrir o QGIS (modo "headless"):
    1. Abra o Prompt de Comando/PowerShell.
    2. Rode (ajuste o caminho do QGIS para a sua instalacao):
           "C:\\Program Files\\QGIS 3.34\\bin\\python-qgis.bat" "C:\\caminho\\para\\4_fragilidade_ambiental_QGIS.py"
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
from osgeo import gdal

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

# ------------------------------------------------------------------
# EXECUCAO "HEADLESS" - roda pelo terminal, sem abrir a janela do QGIS
# ------------------------------------------------------------------
# Continua exigindo o QGIS instalado na maquina (e dele que vem o
# qgis.core/processing por baixo) - so nao precisa mais abrir o programa
# e colar no Console Python. Basta rodar pelo terminal usando o
# "python-qgis.bat" que vem dentro da pasta "bin" da instalacao do QGIS,
# por exemplo:
#
#   "C:\Program Files\QGIS 3.34\bin\python-qgis.bat" "C:\caminho\para\4_fragilidade_ambiental_QGIS.py"
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
WORKSPACE = r"C:\alexgeopro\FragilidadeAmbiental_QGIS"  # pasta - criada automaticamente

CELL_SIZE = 0.00027777778   # ~30 m em graus (usada so se o relevo precisar ser reprojetado)
EPSG_SAIDA = 4674           # SIRGAS 2000 Geografico
EPSG_USO_ENTRADA_PADRAO = 4326  # usado so se o raster de uso nao tiver SRC definido
NODATA = -9999
CAMPO_SOLO = "Frag"         # campo de fragilidade (1-5, 7 urbano, 9 agua) no vetor de solos
CAMPO_CLIMA = "Fragilidade" # campo de fragilidade (1-5) no vetor climatico
LINHAS_BLOCO = 1024         # linhas lidas de cada vez nas somas (reduza se faltar memoria)

# Local padrao onde a versao QGIS do script 3 grava o Grau de Dissecacao
# de Fragilidade - usado automaticamente quando existir.
GRAU_DISSECACAO_PADRAO = r"C:\alexgeopro\GrauDeDissecacao_QGIS\b_GrauDeDissecacao_Fragilidade.tif"

# Filtro opcional: se o uso da terra for uma pasta com varios rasters, so
# processa os que contem este texto no nome ("" = todos).
FILTRO_NOME_USO = ""
EXTENSOES_RASTER_USO = ("*.tif", "*.tiff", "*.vrt", "*.img")

# False: se o resultado de um ano ja existir, pula esse ano (permite
# retomar uma execucao interrompida). True: refaz tudo.
SOBRESCREVER = False

# False: apaga os rasters intermediarios de cada ano de uso da terra.
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

# Saidas fixas (as de uso da terra levam o nome do raster de origem).
# Um GeoPackage por camada vetorial (evita o erro "unable to open database
# file" ao misturar varias camadas num so .gpkg com "|layername=").
GPKG_LIMITE = os.path.join(WORKSPACE, "lim_a_LimiteSirgas.gpkg")
GPKG_SOLO = os.path.join(WORKSPACE, "ped_a_PEDOLOGICO_SIRGAS.gpkg")
GPKG_CLIMA = os.path.join(WORKSPACE, "cli_a_Clima_Project.gpkg")

REL_A_GRAU = os.path.join(WORKSPACE, "rel_a_grau_dissecacao.tif")      # so se precisar reprojetar
REL_B_FRAGIL = os.path.join(WORKSPACE, "rel_b_RelevoFragil.tif")
PED_C_RASTER = os.path.join(WORKSPACE, "ped_c_PedRaster.tif")
PED_D_FRAGIL = os.path.join(WORKSPACE, "ped_d_SolosFragil.tif")
CLI_C_FRAGIL = os.path.join(WORKSPACE, "cli_c_ClimaFragil.tif")
A_FRAGILIDADE_FINAL = os.path.join(WORKSPACE, "a_FragilidadeFinal.tif")

OPCOES_TIF = ["COMPRESS=LZW", "TILED=YES"]


# ------------------------------------------------------------------
# Funcoes auxiliares
# ------------------------------------------------------------------
def garantir_pasta(caminho):
    if not os.path.isdir(caminho):
        print(f"Criando pasta '{caminho}'...")
        os.makedirs(caminho)


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


def abrir_vetor(caminho):
    camada = QgsVectorLayer(uri_vetor(caminho), "teste", "ogr")
    return camada if camada.isValid() else None


def pedir_caminho(mensagem, tipo):
    while True:
        caminho = input(mensagem).strip().strip('"')
        if not caminho:
            print("  -> Caminho vazio, tente novamente.")
            continue
        if tipo == "raster":
            ok = QgsRasterLayer(caminho, "teste").isValid()
        elif tipo == "pasta_ou_raster":
            ok = os.path.isdir(caminho) or QgsRasterLayer(caminho, "teste").isValid()
        else:
            ok = abrir_vetor(caminho) is not None
        if ok:
            return caminho
        print(f"  -> Nao consegui abrir '{caminho}' como {tipo}. Confira o caminho e tente de novo.")


def pedir_vetor_com_campo(mensagem, campo):
    """Pede um vetor e confere se ele tem o campo de fragilidade (sem
    diferenciar maiusculas/minusculas). Devolve (caminho, nome_real)."""
    while True:
        caminho = pedir_caminho(mensagem, "vetor")
        for nome in abrir_vetor(caminho).fields().names():
            if nome.lower() == campo.lower():
                return caminho, nome
        print(f"  -> '{caminho}' nao tem o campo '{campo}'. Confira e tente de novo.")


def achar_ou_pedir_caminho(caminho_padrao, descricao):
    """Tenta usar automaticamente o caminho padrao (saida do script 3,
    versao QGIS); se nao existir/abrir, pergunta o caminho na tela."""
    if QgsRasterLayer(caminho_padrao, "teste").isValid():
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
            "O QGIS/GDAL nao le rasters dentro de geodatabase (.gdb). Exporte cada raster "
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


def extensao_qgis(bounds):
    """Converte (xmin, ymin, xmax, ymax) para o texto de extensao que os
    algoritmos do QGIS esperam: 'xmin,xmax,ymin,ymax [EPSG:xxxx]'."""
    xmin, ymin, xmax, ymax = bounds
    return f"{xmin!r},{xmax!r},{ymin!r},{ymax!r} [EPSG:{EPSG_SAIDA}]"


def reprojetar_vetor(caminho_entrada, sr_saida, caminho_saida_gpkg):
    """Equivalente a 'Project' do ArcGIS: 'native:reprojectlayer'."""
    processing.run("native:reprojectlayer", {
        "INPUT": uri_vetor(caminho_entrada), "TARGET_CRS": sr_saida,
        "OUTPUT": caminho_saida_gpkg,
    })


def rasterizar_campo(caminho_gpkg, campo, caminho_saida, grade):
    """Equivalente a 'Feature to Raster' do ArcGIS: 'gdal:rasterize' DIRETO
    na grade de referencia (pixels cujo centro cai dentro do poligono).
    Feito com gdal.Rasterize dentro do proprio Python (e nao pelo
    'gdal:rasterize' do Processing, que roda o gdal_rasterize externo e,
    quando falha, nao avisa - o arquivo simplesmente nao e criado)."""
    colunas, linhas, gt, _ = grade
    if os.path.exists(caminho_saida):
        gdal.GetDriverByName("GTiff").Delete(caminho_saida)
    saida = gdal.GetDriverByName("GTiff").Create(
        caminho_saida, colunas, linhas, 1, gdal.GDT_Int16, options=OPCOES_TIF)
    saida.SetGeoTransform(gt)
    sr = QgsCoordinateReferenceSystem(f"EPSG:{EPSG_SAIDA}")
    saida.SetProjection(sr.toWkt())
    banda = saida.GetRasterBand(1)
    banda.SetNoDataValue(NODATA)
    banda.Fill(NODATA)
    gdal.Rasterize(saida, caminho_gpkg, attribute=campo)
    banda.FlushCache()
    saida = None
    if not os.path.exists(caminho_saida):
        raise RuntimeError(f"Falha ao rasterizar '{caminho_gpkg}' (campo '{campo}').")


def alinhar_raster(caminho_entrada, caminho_saida, sr_saida, grade):
    """Equivalente a 'Project Raster' + 'Extract by Mask' do ArcGIS:
    'gdal:warpreproject' leva um raster de classes para a grade de
    referencia (SRC, extensao, resolucao e origem), vizinho mais proximo."""
    colunas, linhas, _, bounds = grade
    parametros = {
        "INPUT": caminho_entrada, "TARGET_CRS": sr_saida,
        "RESAMPLING": 0,  # nearest neighbour - obrigatorio para dado de classe
        "NODATA": NODATA, "DATA_TYPE": 2,  # Int16
        "TARGET_EXTENT": extensao_qgis(bounds),
        "TARGET_EXTENT_CRS": sr_saida,
        "OPTIONS": "COMPRESS=LZW|TILED=YES",
        "EXTRA": f"-ts {colunas} {linhas}",  # tamanho exato da grade de referencia
        "OUTPUT": caminho_saida,
    }
    if not QgsRasterLayer(caminho_entrada, "teste").crs().isValid():
        parametros["SOURCE_CRS"] = QgsCoordinateReferenceSystem(f"EPSG:{EPSG_USO_ENTRADA_PADRAO}")
    processing.run("gdal:warpreproject", parametros)


def mascarar_por_limite(caminho_entrada, caminho_saida):
    """Equivalente a 'Extract by Mask' final do model: recorta pelo
    contorno exato do limite, mantendo a MESMA grade (sem cortar a
    extensao nem reamostrar)."""
    processing.run("gdal:cliprasterbymasklayer", {
        "INPUT": caminho_entrada, "MASK": GPKG_LIMITE,
        "NODATA": NODATA, "CROP_TO_CUTLINE": False, "KEEP_RESOLUTION": True,
        "DATA_TYPE": 0,  # mesmo tipo da entrada (Int16)
        "OPTIONS": "COMPRESS=LZW|TILED=YES",
        "OUTPUT": caminho_saida,
    })


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

    sr_saida = QgsCoordinateReferenceSystem(f"EPSG:{EPSG_SAIDA}")

    # 1. Limite -> SIRGAS 2000 -----------------------------------------------------
    print("1/6 - Limite da area: SIRGAS 2000...")
    reprojetar_vetor(limite, sr_saida, GPKG_LIMITE)

    # 2. Relevo: grade de referencia ------------------------------------------------
    print("2/6 - Relevo: Grau de Dissecacao -> fragilidade (1000 a 5000)...")
    if QgsRasterLayer(grau_dissecacao, "teste").crs() == sr_saida:
        grau = grau_dissecacao
    else:
        # fora do SIRGAS 2000 geografico: reprojeta (vizinho mais proximo)
        print("   (Grau de Dissecacao fora do SIRGAS 2000 geografico - reprojetando...)")
        processing.run("gdal:warpreproject", {
            "INPUT": grau_dissecacao, "TARGET_CRS": sr_saida, "RESAMPLING": 0,
            "TARGET_RESOLUTION": CELL_SIZE, "NODATA": NODATA, "DATA_TYPE": 2,
            "OUTPUT": REL_A_GRAU,
        })
        grau = REL_A_GRAU
    calcular_em_blocos(REL_B_FRAGIL, [grau], f_reclassificar_relevo)
    grade = grade_do_raster(REL_B_FRAGIL)  # TODOS os outros rasters seguem esta grade

    # 3. Solos ------------------------------------------------------------------------
    print("3/6 - Solos: reprojetar, rasterizar o campo 'Frag' e x 100...")
    reprojetar_vetor(pedologico, sr_saida, GPKG_SOLO)
    rasterizar_campo(GPKG_SOLO, campo_solo, PED_C_RASTER, grade)
    calcular_em_blocos(PED_D_FRAGIL, [PED_C_RASTER], f_solos_x100)

    # 4. Clima ------------------------------------------------------------------------
    print("4/6 - Clima: reprojetar e rasterizar o campo 'Fragilidade'...")
    reprojetar_vetor(clima, sr_saida, GPKG_CLIMA)
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
        alinhar_raster(uso_original, uso_b, sr_saida, grade)

        # Reclassify (Tabela 24) + soma com a_FragilidadeFinal
        desconhecidas = set()
        calcular_em_blocos(soma, [A_FRAGILIDADE_FINAL, uso_b], criar_f_uso(desconhecidas))
        if desconhecidas:
            print(f"\n    AVISO: classes fora da Tabela 24 (viraram NoData): {sorted(desconhecidas)}", end=" ")

        # Extract by Mask final (contorno exato do limite)
        mascarar_por_limite(soma, saida)

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
    _qgs = iniciar_qgis_headless()
    try:
        main()
    finally:
        encerrar_qgis_headless(_qgs)
