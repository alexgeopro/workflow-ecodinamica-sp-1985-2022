# -*- coding: utf-8 -*-
"""
1_Entalhamento do Vale - versao software livre (QGIS + Python)
=================================================================
Mesma metodologia do script "1_entalhamento_do_vale.py" (ArcGIS Pro /
arcpy), reescrita usando apenas ferramentas livres: QGIS (framework
"processing") + GDAL + numpy/scipy/scikit-image, que ja vem dentro do
Python do proprio QGIS.

Baseado no model "1_Entalhamento do Vale_FINAL_Geografica" da toolbox
"1_Ferramentas Finais da Tese.tbx", conferido contra a descricao
metodologica da tese (Alex da Silva Sousa, 2024, Cap. 6.3 "Geomorfologia
e Hidrografia", p. 59-61, DOI: 10.11606/T.8.2024.tde-18022025-121027).

Metodologia (identica a versao ArcGIS - o "pulo do gato" e usar o MDT
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

Diferencas em relacao a versao ArcGIS/arcpy (nota de transparencia
metodologica):
    - Geodatabase (.gdb) -> pasta comum com GeoPackage (.gpkg) para os
      vetores e GeoTIFF (.tif) para os rasters. E o equivalente aberto
      mais direto a uma geodatabase.
    - As quatro ferramentas hidrologicas do ArcGIS usadas no "pulo do
      gato" (Fill, Flow Direction, Sink, Basin) foram reunidas em uma
      unica rotina Python (numpy/scipy/scikit-image), em vez de usar as
      ferramentas de hidrologia do SAGA/GRASS disponiveis dentro do
      QGIS. Motivo: os nomes e parametros dessas ferramentas SAGA/GRASS
      mudam entre versoes do QGIS (o que tornaria o script fragil e
      dependente da instalacao especifica de cada computador); a
      rotina em numpy/scipy reproduz a MESMA logica matematica descrita
      acima (preencher depressoes -> inverter -> achar os pontos mais
      altos -> delimitar a zona de cada um), com resultado equivalente.
    - Como consequencia dessa rotina trabalhar direto na matriz
      (raster), a limpeza iterativa de poligonos sem pico associado
      ("Eliminate" repetido 5x no model original, necessaria porque a
      conversao para poligono podia gerar fragmentos sem nenhum ponto
      de pico dentro) deixa de ser necessaria: o metodo usado aqui
      ("watershed") sempre atribui cada pixel a alguma zona/pico,
      sem gerar fragmentos orfaos.
    - As demais etapas (reprojecao, buffer, recorte por mascara,
      reclassificacao) usam o framework "processing" do proprio QGIS
      (algoritmos "native" e "gdal"), que sao estaveis entre versoes.

Requisitos:
    - QGIS 3.x instalado (traz GDAL, numpy e o "processing" prontos).
    - scipy e scikit-image dentro do Python do QGIS. Para conferir/
      instalar (Windows): abra o "OSGeo4W Shell" (vem junto com o QGIS,
      procure no menu Iniciar), digite:
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
    2. Menu Complementos/Plugins > Console Python (ou "Python Console").
    3. No console, clique no icone de "Editor de script" (folha com um
       lapis), abra este arquivo .py e clique em "Executar script"
       (triangulo verde) - ou cole o conteudo direto no console.
    4. O script vai perguntar, na propria janela do console, o caminho
       do MDT (raster) e o caminho do shapefile/feature class da area
       de estudo.

    Opcao 2 - pelo terminal, sem abrir o QGIS (modo "headless"):
    1. Abra o Prompt de Comando/PowerShell.
    2. Rode (ajuste o caminho do QGIS para a sua instalacao):
           "C:\\Program Files\\QGIS 3.34\\bin\\python-qgis.bat" "C:\\caminho\\para\\1_entalhamento_do_vale_QGIS.py"
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
from osgeo import gdal, osr
from scipy import ndimage as ndi
from skimage.morphology import reconstruction, local_minima
from skimage.segmentation import watershed

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
from qgis.core import QgsCoordinateReferenceSystem, QgsVectorLayer, QgsRasterLayer

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
#   "C:\Program Files\QGIS 3.34\bin\python-qgis.bat" "C:\caminho\para\1_entalhamento_do_vale_QGIS.py"
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
# Pasta de trabalho (equivalente livre da geodatabase). E criada
# automaticamente se ainda nao existir.
WORKSPACE = r"C:\alexgeopro\Entalhamento_QGIS"

BUFFER_DISTANCIA_M = 2000            # 2 km (ver nota sobre CRS abaixo)
CELL_SIZE = 0.00027777778            # ~30 m em graus (resolucao do SRTM, igual a versao ArcGIS)
EPSG_SAIDA = 4674                    # SIRGAS 2000 Geografico
EPSG_DEM_ENTRADA = 4326              # WGS 84 (SRC original do mosaico, conforme o model)
EPSG_METRICO_BR = 5880               # SIRGAS 2000 / Brazil Polyconic - usado so
                                      # internamente para o buffer (precisa de
                                      # metros; a saida final volta pra graus)
NODATA_PADRAO = -9999.0

# Nota sobre a transformacao geografica: no ArcGIS, a reprojecao usou a
# transformacao "SIRGAS_To_WGS_1984_1". SIRGAS 2000 e WGS 84 sao, na
# pratica, coincidentes (diferenca de poucos cm a ~1 m), entao a
# reprojecao abaixo (feita pelo GDAL/QGIS) e equivalente ao resultado
# pratico dessa transformacao.

# Reclassificacao final do entalhamento (Tabela 5/Tabela 7, Cap. 5.4.1 da tese)
# (valor_min, valor_max, classe_de_peso)
REMAP_ENTALHAMENTO = [
    (-1500, 20, 10),   # < 20 m: Muito Fraco
    (20, 40, 20),      # 20-40 m: Fraco
    (40, 80, 30),      # 40-80 m: Medio
    (80, 160, 40),     # 80-160 m: Forte
    (160, 5000, 50),   # > 160 m: Muito Forte
]

# Saidas raster (nomes equivalentes aos do model original)
A_MOSAICO_PROJ = os.path.join(WORKSPACE, "a_mosaico_Reproj.tif")
B_MOSAICO_LIMITE = os.path.join(WORKSPACE, "b_Mosaico_Limite.tif")
C_MOSAICO_FILL = os.path.join(WORKSPACE, "c_mosaico_fill.tif")           # (c) MDT preenchido
C_MOSAICO_FILL_NEG = os.path.join(WORKSPACE, "c_mosaico_fill_neg.tif")   # (c1) MDT invertido
E_BASIN = os.path.join(WORKSPACE, "e_mosaico_basin.tif")                # (e) zonas de influencia
G_SINK_BASIN = os.path.join(WORKSPACE, "g_sink_basin.tif")              # (g) cota do pico espalhada pela zona
H_ENTALHAMENTO = os.path.join(WORKSPACE, "h_entalhamento.tif")          # (h)
I_ENTALHAMENTO_RECLA = os.path.join(WORKSPACE, "i_EntalhamentoRecla.tif")  # (i)

# Camadas vetoriais - um .gpkg PROPRIO para cada uma (em vez de varias
# camadas dentro de um unico .gpkg compartilhado, endereçadas por
# "arquivo.gpkg|layername=X"): essa sintaxe de camada-dentro-de-gpkg-
# compartilhado fez o algoritmo "processing" falhar em modo headless com
# "sqlite3_open(...) failed: unable to open database file" - o
# "OUTPUT" as vezes nao e interpretado como "abrir o gpkg existente e
# adicionar a camada X", e sim como nome literal de um datasource novo
# (acabava tentando criar um arquivo ".gpkg|layername=X.gpkg", invalido).
A_LIMITE_PROJ = os.path.join(WORKSPACE, "a_limite_Proj.gpkg")
A_LIMITE_PROJ_BUFFER = os.path.join(WORKSPACE, "a_limite_Proj_Buffer.gpkg")


# ------------------------------------------------------------------
# Funcoes auxiliares
# ------------------------------------------------------------------
def garantir_pasta(caminho):
    if not os.path.isdir(caminho):
        print(f"Criando pasta '{caminho}'...")
        os.makedirs(caminho)


def pedir_caminho(mensagem, tipo):
    """Pergunta um caminho (raster ou vetor) e so aceita quando o QGIS
    conseguir realmente abrir o dado."""
    while True:
        caminho = input(mensagem).strip().strip('"')
        if not caminho:
            print("  -> Caminho vazio, tente novamente.")
            continue
        if tipo == "raster":
            camada = QgsRasterLayer(caminho, "teste")
        else:
            camada = QgsVectorLayer(caminho, "teste", "ogr")
        if camada.isValid():
            return caminho
        print(f"  -> Nao consegui abrir '{caminho}' como {tipo}. Confira o caminho e tente de novo.")


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

    sr_saida = QgsCoordinateReferenceSystem(f"EPSG:{EPSG_SAIDA}")
    sr_metrica = QgsCoordinateReferenceSystem(f"EPSG:{EPSG_METRICO_BR}")

    # (a) Reprojeta a area de estudo e o MDT para SIRGAS 2000 Geografico ---
    print("(a) 1/9 - Reprojetando area de estudo...")
    processing.run("native:reprojectlayer", {
        "INPUT": AreaEstudo,
        "TARGET_CRS": sr_saida,
        "OUTPUT": A_LIMITE_PROJ,
    })

    print("(a) 2/9 - Reprojetando MDT (gdal:warpreproject)...")
    processing.run("gdal:warpreproject", {
        "INPUT": MOSAICO_DEM,
        "SOURCE_CRS": QgsCoordinateReferenceSystem(f"EPSG:{EPSG_DEM_ENTRADA}"),
        "TARGET_CRS": sr_saida,
        "RESAMPLING": 0,  # nearest neighbour, igual a versao ArcGIS
        "TARGET_RESOLUTION": CELL_SIZE,
        "NODATA": NODATA_PADRAO,
        "DATA_TYPE": 6,  # Float32
        "OUTPUT": A_MOSAICO_PROJ,
    })

    # (b) Buffer de 2 km (feito num CRS metrico) + recorte do MDT --------
    print("(b) 3/9 - Buffer de 2 km...")
    buffer_metrico = processing.run("native:reprojectlayer", {
        "INPUT": A_LIMITE_PROJ, "TARGET_CRS": sr_metrica, "OUTPUT": "memory:",
    })["OUTPUT"]
    buffer_metrico = processing.run("native:buffer", {
        "INPUT": buffer_metrico,
        "DISTANCE": BUFFER_DISTANCIA_M,
        "SEGMENTS": 8,
        "DISSOLVE": False,
        "OUTPUT": "memory:",
    })["OUTPUT"]
    processing.run("native:reprojectlayer", {
        "INPUT": buffer_metrico, "TARGET_CRS": sr_saida, "OUTPUT": A_LIMITE_PROJ_BUFFER,
    })

    print("(b) - Recortando o MDT pelo buffer (ExtractByMask)...")
    processing.run("gdal:cliprasterbymasklayer", {
        "INPUT": A_MOSAICO_PROJ,
        "MASK": A_LIMITE_PROJ_BUFFER,
        "NODATA": NODATA_PADRAO,
        "CROP_TO_CUTLINE": True,
        "KEEP_RESOLUTION": True,
        "OUTPUT": B_MOSAICO_LIMITE,
    })

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
    _qgs = iniciar_qgis_headless()
    try:
        main()
    finally:
        encerrar_qgis_headless(_qgs)
