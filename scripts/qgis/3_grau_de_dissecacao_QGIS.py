# -*- coding: utf-8 -*-
"""
3_Grau de Dissecacao - versao software livre (QGIS + Python)
================================================================
Mesma metodologia do script "3_grau_de_dissecacao.py" (ArcGIS Pro /
arcpy), reescrita usando apenas ferramentas livres: QGIS (framework
"processing") + GDAL + numpy, que ja vem dentro do Python do proprio
QGIS.

Baseado no model "3_Grau de Dissecacao" da toolbox "1_Ferramentas Finais
da Tese.tbx", conferido contra o script exportado nativamente do ArcMap
10.3 ("3_Grau_de_Dissecacao_Arc103.py") e contra a descricao
metodologica da tese (Alex da Silva Sousa, 2024, Cap. 6.3 "Geomorfologia
e Hidrografia", p. 64-65, DOI: 10.11606/T.8.2024.tde-18022025-121027).

Metodologia (identica a versao ArcGIS): soma o raster reclassificado de
Entalhamento do Vale (classes de dezena: 10 a 50) com os rasters
reclassificados de Dimensao Interfluvial Media (classes de unidade: 1 a
5 - uma para Fragilidade/Ross, outra para Vulnerabilidade/Crepani), e
recorta o resultado pelo limite da area de interesse. O resultado e um
numero de dois digitos: a dezena e a classe de Entalhamento, a unidade e
a classe de Dimensao Interfluvial (ex.: 11 = fragilidade/vulnerabilidade
baixa nas duas variaveis; 55 = alta nas duas). Como a Dimensao
Interfluvial tem duas variantes, este script gera as DUAS combinacoes
automaticamente:

    - Grau de Dissecacao (Fragilidade) = Entalhamento_Recla + DimensaoReclaFrag
    - Grau de Dissecacao (Vulnerabilidade) = Entalhamento_Recla + DimensaoReclaVul

Diferenca em relacao a versao ArcGIS/arcpy: antes de somar, os tres
rasters de entrada sao reprojetados/reamostrados (vizinho mais proximo -
sao rasters de classes, nao pode interpolar) para uma MESMA grade
(mesma extensao, resolucao e origem), usando como referencia a extensao
do limite da area de interesse. Isso e necessario porque os scripts 1 e
2 recortam por mascaras diferentes (buffer da area de estudo, no caso do
Entalhamento; as proprias subbacias, no caso da Dimensao Interfluvial),
entao os dois rasters raramente vem com a mesma grade de pixels "de
fabrica" - somar rasters em grades diferentes pixel a pixel exigiria
esse alinhamento de qualquer forma, entao a ferramenta ja faz isso
automaticamente.

Requisitos:
    - QGIS 3.x instalado (traz GDAL, numpy e o "processing" prontos).
    - Nao precisa de scipy/scikit-image (diferente dos scripts 1 e 2).

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
    4. O script procura sozinho, nos locais padrao onde as versoes QGIS
       dos scripts 1 e 2 gravam suas saidas, os tres rasters
       reclassificados de que precisa; se algum nao for encontrado ali,
       pergunta o caminho na tela. O limite vetorial da area de
       interesse (por padrao, o limite do Estado de Sao Paulo, mas pode
       ser qualquer area de estudo) e sempre perguntado na tela.

    Opcao 2 - pelo terminal, sem abrir o QGIS (modo "headless"):
    1. Abra o Prompt de Comando/PowerShell.
    2. Rode (ajuste o caminho do QGIS para a sua instalacao):
           "C:\\Program Files\\QGIS 3.34\\bin\\python-qgis.bat" "C:\\caminho\\para\\3_grau_de_dissecacao_QGIS.py"
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
#   "C:\Program Files\QGIS 3.34\bin\python-qgis.bat" "C:\caminho\para\3_grau_de_dissecacao_QGIS.py"
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
WORKSPACE = r"C:\alexgeopro\GrauDeDissecacao_QGIS"  # pasta - criada automaticamente

CELL_SIZE = 0.00027777778   # ~30 m em graus (mesma resolucao dos demais scripts)
EPSG_SAIDA = 4674           # SIRGAS 2000 Geografico
NODATA_PADRAO = -9999.0

# Locais padrao onde as versoes QGIS dos scripts 1 e 2 gravam suas
# saidas reclassificadas - usados automaticamente quando existirem.
ENTALHAMENTO_RECLA_PADRAO = r"C:\alexgeopro\Entalhamento_QGIS\i_EntalhamentoRecla.tif"
DIMENSAO_RECLA_FRAG_PADRAO = r"C:\alexgeopro\DimensaoInterfluvial_QGIS\l_DimensaoReclaFrag.tif"
DIMENSAO_RECLA_VULN_PADRAO = r"C:\alexgeopro\DimensaoInterfluvial_QGIS\l_DimensaoReclaVul.tif"

# Saidas (grades intermediarias alinhadas + resultados finais)
ENTALHAMENTO_ALINHADO = os.path.join(WORKSPACE, "_entalhamento_alinhado.tif")
DIMENSAO_FRAG_ALINHADO = os.path.join(WORKSPACE, "_dimensao_frag_alinhado.tif")
DIMENSAO_VULN_ALINHADO = os.path.join(WORKSPACE, "_dimensao_vuln_alinhado.tif")
A_SOMA_FRAGILIDADE = os.path.join(WORKSPACE, "a_Soma_Fragilidade.tif")
A_SOMA_VULNERABILIDADE = os.path.join(WORKSPACE, "a_Soma_Vulnerabilidade.tif")
B_GRAU_DISSECACAO_FRAGILIDADE = os.path.join(WORKSPACE, "b_GrauDeDissecacao_Fragilidade.tif")
B_GRAU_DISSECACAO_VULNERABILIDADE = os.path.join(WORKSPACE, "b_GrauDeDissecacao_Vulnerabilidade.tif")


# ------------------------------------------------------------------
# Funcoes auxiliares
# ------------------------------------------------------------------
def garantir_pasta(caminho):
    if not os.path.isdir(caminho):
        print(f"Criando pasta '{caminho}'...")
        os.makedirs(caminho)


def pedir_caminho(mensagem, tipo):
    while True:
        caminho = input(mensagem).strip().strip('"')
        if not caminho:
            print("  -> Caminho vazio, tente novamente.")
            continue
        camada = QgsRasterLayer(caminho, "teste") if tipo == "raster" else QgsVectorLayer(caminho, "teste", "ogr")
        if camada.isValid():
            return caminho
        print(f"  -> Nao consegui abrir '{caminho}' como {tipo}. Confira o caminho e tente de novo.")


def achar_ou_pedir_caminho(caminho_padrao, descricao):
    """Tenta usar automaticamente o caminho padrao (saida dos scripts
    1/2, versao QGIS); se nao existir/abrir, pergunta o caminho na tela."""
    if QgsRasterLayer(caminho_padrao, "teste").isValid():
        print(f"  {descricao}: encontrado automaticamente em '{caminho_padrao}'.")
        return caminho_padrao
    print(f"  {descricao}: nao encontrei em '{caminho_padrao}'.")
    return pedir_caminho(f"  Informe o caminho de {descricao}: ", "raster")


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


def alinhar_raster(caminho_entrada, caminho_saida, extensao_str, sr_saida):
    """Reprojeta/reamostra um raster de classes para uma grade comum
    (mesma extensao, resolucao e origem) - vizinho mais proximo, para
    nao interpolar valores de classe."""
    processing.run("gdal:warpreproject", {
        "INPUT": caminho_entrada,
        "TARGET_CRS": sr_saida,
        "RESAMPLING": 0,  # nearest neighbour - obrigatorio para dados de classe
        "TARGET_RESOLUTION": CELL_SIZE,
        "TARGET_EXTENT": extensao_str,
        "TARGET_EXTENT_CRS": sr_saida,
        "NODATA": NODATA_PADRAO,
        "DATA_TYPE": 6,  # Float32
        "OUTPUT": caminho_saida,
    })


# ------------------------------------------------------------------
# Programa principal
# ------------------------------------------------------------------
def main():
    garantir_pasta(WORKSPACE)

    print()
    print("Localizando os rasters reclassificados dos scripts 1 e 2 (versao QGIS)...")
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

    sr_saida = QgsCoordinateReferenceSystem(f"EPSG:{EPSG_SAIDA}")

    # Reprojeta o limite e usa a extensao dele como referencia para alinhar os rasters
    print("1/5 - Reprojetando o limite da area e definindo a grade de referencia...")
    limite_proj = processing.run("native:reprojectlayer", {
        "INPUT": LIMITE_AREA, "TARGET_CRS": sr_saida, "OUTPUT": "memory:",
    })["OUTPUT"]
    extensao = limite_proj.extent()
    extensao_str = f"{extensao.xMinimum()},{extensao.xMaximum()},{extensao.yMinimum()},{extensao.yMaximum()} [EPSG:{EPSG_SAIDA}]"

    print("2/5 - Alinhando os tres rasters reclassificados a uma grade comum...")
    alinhar_raster(entalhamento_recla, ENTALHAMENTO_ALINHADO, extensao_str, sr_saida)
    alinhar_raster(dimensao_recla_frag, DIMENSAO_FRAG_ALINHADO, extensao_str, sr_saida)
    alinhar_raster(dimensao_recla_vuln, DIMENSAO_VULN_ALINHADO, extensao_str, sr_saida)

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
    print("5/5 - Recortando pelo limite da area (Extract by Mask)...")
    processing.run("gdal:cliprasterbymasklayer", {
        "INPUT": A_SOMA_FRAGILIDADE, "MASK": limite_proj,
        "NODATA": nodata, "CROP_TO_CUTLINE": True, "KEEP_RESOLUTION": True,
        "OUTPUT": B_GRAU_DISSECACAO_FRAGILIDADE,
    })
    processing.run("gdal:cliprasterbymasklayer", {
        "INPUT": A_SOMA_VULNERABILIDADE, "MASK": limite_proj,
        "NODATA": nodata, "CROP_TO_CUTLINE": True, "KEEP_RESOLUTION": True,
        "OUTPUT": B_GRAU_DISSECACAO_VULNERABILIDADE,
    })

    print()
    print("Concluido.")
    print("b_GrauDeDissecacao_Fragilidade (Ross - Entalhamento + Dimensao Interfluvial):", B_GRAU_DISSECACAO_FRAGILIDADE)
    print("b_GrauDeDissecacao_Vulnerabilidade (Crepani - Entalhamento + Dimensao Interfluvial):", B_GRAU_DISSECACAO_VULNERABILIDADE)


if __name__ == "__main__":
    _qgs = iniciar_qgis_headless()
    try:
        main()
    finally:
        encerrar_qgis_headless(_qgs)
