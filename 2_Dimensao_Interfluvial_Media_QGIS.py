# -*- coding: utf-8 -*-
"""
2_Dimensao Interfluvial Media - versao software livre (QGIS + Python)
=========================================================================
Mesma metodologia do script "2_dimensao_interfluvial_media.py" (ArcGIS
Pro / arcpy), reescrita usando apenas ferramentas livres: QGIS
(framework "processing") + GDAL + numpy/scipy/scikit-image, que ja vem
dentro do Python do proprio QGIS.

Baseado no model "2_Dimensao Interfluvial Media_FINAL_Geografica" da
toolbox "1_Ferramentas Finais da Tese.tbx", conferido contra o script
exportado nativamente do ArcMap 10.3 e contra a descricao metodologica
da tese (Alex da Silva Sousa, 2024, Cap. 6.3 "Geomorfologia e
Hidrografia", p. 62-64, DOI: 10.11606/T.8.2024.tde-18022025-121027).

Metodologia (identica, em espirito, a versao ArcGIS - obter, para cada
subbacia, a "dimensao interfluvial media": o dobro da distancia entre o
ponto mais "central" da subbacia e a borda mais proxima):

    (a) O raster de subbacias e reprojetado para SIRGAS 2000 Geografico.
    (b)+(c) Calcula-se, para cada pixel, a distancia ate a borda mais
        proxima entre subbacias (ou o limite externo da area de
        estudo) - equivalente a converter os poligonos em linhas e
        calcular a Distancia Euclidiana a partir delas.
    (d) Os valores de distancia (em graus) sao convertidos para metros
        multiplicando pela mesma constante do script ArcGIS (107015) -
        ver nota abaixo.
    (e)-(g) O(s) ponto(s) mais distante(s) de qualquer borda dentro de
        cada subbacia (o "centro" da subbacia) sao identificados
        diretamente (maximos locais da distancia).
    (h) A cada um desses pontos, atribui-se "diametro" = 2x a distancia
        encontrada em (d)-(e).
    (i)/(j) Calcula-se a media do "diametro" dentro de cada subbacia -
        a dimensao interfluvial media daquela subbacia.
    (l) Reclassifica-se o resultado em duas variantes, conforme as
        metodologias de Ross (1994, 2012) - Fragilidade - e de Crepani
        et al. (1996, 2001) - Vulnerabilidade -, com os intervalos das
        Tabelas 5 e 7 do Cap. 5.4.1 "Geomorfologia" da tese (os mesmos
        remaps confirmados no script ArcGIS/export nativo do ArcMap).

Diferencas em relacao a versao ArcGIS/arcpy (nota de transparencia
metodologica):
    - Como o dado de entrada ja e um raster de subbacias (cada subbacia
      com um codigo/ID unico por pixel), os passos (a) "Raster to
      Polygon" e (b) "Polygon To Line" do model original deixam de ser
      necessarios: a "borda" de cada subbacia e identificada
      diretamente comparando cada pixel aos seus 8 vizinhos (pixel de
      borda = tem ao menos um vizinho de outra subbacia, ou fora da
      area valida). O resultado e o mesmo conjunto de linhas de borda,
      so que obtido direto na matriz.
    - As etapas (c) Distancia Euclidiana + (d) escala para metros + (e)
      inversao de sinal viram uma unica transformada de distancia
      (scipy.ndimage.distance_transform_edt) a partir dessa mascara de
      borda, multiplicada pela MESMA constante 107015 usada na tese -
      esse valor foi mantido sem alteracao (ver nota abaixo).
    - (f) Flow Direction + (g) Sink viram a busca direta pelos maximos
      locais da distancia-ate-a-borda (skimage.morphology.local_maxima)
      - o "centro" de cada subbacia e, por definicao, o ponto mais
      distante de qualquer borda.
    - Como ja se trabalha com os rotulos de subbacia originais do
      raster de entrada (em vez de reconstruir poligonos e ter que
      "adivinhar" a qual subbacia cada ponto central pertence), a
      limpeza iterativa por Eliminate (5x no model original, necessaria
      la para garantir que toda subbacia tivesse um ponto central
      associado) deixa de ser necessaria. Como salvaguarda equivalente,
      se por algum motivo uma subbacia nao tiver nenhum maximo local
      identificado dentro dela (caso raro), o script usa diretamente 2x
      a maior distancia-ate-a-borda encontrada naquela subbacia.

Nota sobre a constante 107015: no texto da tese, esse valor foi obtido
comparando os resultados gerados pelo dado em projecao UTM com o dado
em coordenadas geograficas, para nao deixar a ferramenta limitada a um
fuso especifico. E uma aproximacao (o fator graus->metros varia um
pouco com a latitude), mas foi mantida EXATAMENTE como na tese - por
opcao explicita da autora, para manter esta versao fiel ao metodo
publicado. Uma correcao mais rigorosa (reprojetar para uma projecao
metrica equidistante antes de calcular a distancia) fica para uma
eventual modernizacao futura do script.

Requisitos:
    - QGIS 3.x instalado (traz GDAL, numpy e o "processing" prontos).
    - scipy e scikit-image dentro do Python do QGIS. Para conferir/
      instalar (Windows): abra o "OSGeo4W Shell" (vem junto com o QGIS),
      digite:
          py3_env
          python -m pip install scipy scikit-image
      Isso so precisa ser feito uma vez.

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
    4. O script vai perguntar, na propria janela do console, o caminho
       do raster de subbacias (ex.: "Subbacias.tif").

    Opcao 2 - pelo terminal, sem abrir o QGIS (modo "headless"):
    1. Abra o Prompt de Comando/PowerShell.
    2. Rode (ajuste o caminho do QGIS para a sua instalacao):
           "C:\\Program Files\\QGIS 3.34\\bin\\python-qgis.bat" "C:\\caminho\\para\\2_dimensao_interfluvial_media_QGIS.py"
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
    dependa do QGIS (ou mesmo numpy/scipy/skimage) e, se necessario,
    procura o "python-qgis.bat" (instalado junto com o QGIS) e relanca
    este mesmo arquivo com ele - sem precisar que o usuario va procurar
    o caminho certo manualmente."""
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
from scipy import ndimage as ndi
from skimage.morphology import local_maxima

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
from qgis.core import QgsCoordinateReferenceSystem, QgsRasterLayer

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
#   "C:\Program Files\QGIS 3.34\bin\python-qgis.bat" "C:\caminho\para\2_dimensao_interfluvial_media_QGIS.py"
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
WORKSPACE = r"C:\alexgeopro\DimensaoInterfluvial_QGIS"  # pasta - criada automaticamente

CELL_SIZE = 0.00027777778           # ~30 m em graus (mesma resolucao do script ArcGIS)
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

# Saidas raster (nomes equivalentes aos do model original)
A_SUBBACIAS_PROJ = os.path.join(WORKSPACE, "a_Subbacias_Reproj.tif")
D_DISTANCIA_M = os.path.join(WORKSPACE, "d_Subbacias_EucDistInt.tif")     # (c)+(d)
I_DIAMETRO = os.path.join(WORKSPACE, "i_SinkPtRaster.tif")                # (h)/(i) - diametro nos centros
J_DIMENSAO = os.path.join(WORKSPACE, "j_Dimensao.tif")                    # (i)/(j) - media zonal
L_DIMENSAO_RECLA_FRAG = os.path.join(WORKSPACE, "l_DimensaoReclaFrag.tif")
L_DIMENSAO_RECLA_VULN = os.path.join(WORKSPACE, "l_DimensaoReclaVul.tif")


# ------------------------------------------------------------------
# Funcoes auxiliares
# ------------------------------------------------------------------
def garantir_pasta(caminho):
    if not os.path.isdir(caminho):
        print(f"Criando pasta '{caminho}'...")
        os.makedirs(caminho)


def pedir_caminho(mensagem):
    """Pergunta o caminho do raster de subbacias e so aceita quando o
    QGIS conseguir realmente abrir o dado."""
    while True:
        caminho = input(mensagem).strip().strip('"')
        if not caminho:
            print("  -> Caminho vazio, tente novamente.")
            continue
        camada = QgsRasterLayer(caminho, "teste")
        if camada.isValid():
            return caminho
        print(f"  -> Nao consegui abrir '{caminho}' como raster. Confira o caminho e tente de novo.")


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

    sr_saida = QgsCoordinateReferenceSystem(f"EPSG:{EPSG_SAIDA}")

    # (a) Reprojeta o raster de subbacias para SIRGAS 2000 Geografico -----
    print("(a) 1/4 - Reprojetando raster de subbacias (gdal:warpreproject, nearest)...")
    processing.run("gdal:warpreproject", {
        "INPUT": SUBBACIAS_RASTER,
        "TARGET_CRS": sr_saida,
        "RESAMPLING": 0,  # nearest neighbour - obrigatorio para nao corromper os IDs de zona
        "TARGET_RESOLUTION": CELL_SIZE,
        "NODATA": NODATA_PADRAO,
        "DATA_TYPE": 5,  # Int32
        "OUTPUT": A_SUBBACIAS_PROJ,
    })

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
    _qgs = iniciar_qgis_headless()
    try:
        main()
    finally:
        encerrar_qgis_headless(_qgs)
