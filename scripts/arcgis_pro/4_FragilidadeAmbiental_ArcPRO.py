# -*- coding: utf-8 -*-
"""
4_Fragilidade Ambiental
=======================
Convertido a partir do model "4_FragilidadeAmbiental" do ModelBuilder
(toolbox "1_Ferramentas Finais da Tese.tbx"). Os parametros foram
conferidos contra o script exportado nativamente do ArcMap 10.3
("4_FragilidadeAmbiental_Arc103.py", Model > Export > To Python Script) e
contra a descricao metodologica da tese (Alex da Silva Sousa, 2024,
Cap. 6.5 "Uso e Cobertura da Terra" - Tabela 24 - e Cap. 6.6.2
"Fragilidade Ambiental", p. 78-92, DOI: 10.11606/T.8.2024.tde-18022025-121027).

Metodologia (conforme a tese):

A Fragilidade Ambiental e uma matriz de QUATRO algarismos, pixel a pixel,
obtida SOMANDO quatro rasters tematicos, cada um ja multiplicado pela
"casa decimal" que lhe cabe:

    milhar    -> Relevo   (grau de dissecacao reclassificado)   1000 a 5000
    centena   -> Solos    (campo "Frag" x 100)                   100 a  500
    dezena    -> Uso e Cobertura da Terra (MapBiomas, Tabela 24) 10 a   50
    unidade   -> Clima    (campo "Fragilidade", WorldClim)         1 a    5

Exemplos: 1111 = menor fragilidade possivel (as quatro variaveis em 1);
5555 = maior fragilidade possivel. Areas urbanas recebem o algarismo 7 e
corpos d'agua o algarismo 9 (em qualquer das variaveis), de modo que
aparecem na propria matriz (ex.: uso urbano = 70, agua = 90 na dezena).
Isso ja vem dos dados de entrada (campo "Frag" do solo, campo
"Fragilidade" do clima e a tabela de reclassificacao do uso abaixo) - o
script apenas soma.

Etapas (mesma ordem do model):

  1. Limite da area de interesse -> SIRGAS 2000 geografico + buffer de
     2 km (usado para recortar os dados de entrada com folga).
  2. Relevo: o "Grau de Dissecacao (Fragilidade)" (saida do script 3 =
     Entalhamento reclassificado + Dimensao Interfluvial reclassificada,
     valores 11 a 55) e reclassificado em fragilidade 1000-5000 (Tabela 2
     da tese / Ross 2012). No model original essa etapa partia dos rasters
     continuos de entalhamento e dimensao e refazia as reclassificacoes;
     aqui o script aproveita a saida do script 3, que e exatamente o mesmo
     raster ("rel_c_grau_dissecacao" do model).
  3. Solos: vetor pedologico -> SIRGAS 2000, recorte (buffer), conversao
     para raster pelo campo "Frag" (~30 m) e multiplicacao por 100.
  4. Clima: vetor climatico JA CLASSIFICADO (WorldClim, campo
     "Fragilidade", 1 a 5 - ver cap. 6.4 / Tabelas 13 e 22 da tese) ->
     SIRGAS 2000, recorte, conversao para raster (~30 m).
  5. a_FragilidadeFinal = Relevo + Solos + Clima  (algarismos 1, 2 e 4).
  6. Para CADA raster de Uso e Cobertura da Terra (o "Iterate Rasters" do
     model: um raster por ano do MapBiomas): reprojeta para SIRGAS 2000,
     recorta pelo buffer, reclassifica para fragilidade (Tabela 24, valores
     10 a 50, urbano 70, agua 90), soma a a_FragilidadeFinal e recorta
     pelo limite da area -> "c_<nome do raster>_FRAGILIDADE_FINAL".

Observacoes:
  * Esta versao usa APENAS o dado climatico do WorldClim (campo
    "Fragilidade" de um vetor ja classificado). A variante com as normais
    do INMET (IDW/Krigagem) e outro model e nao esta adaptada aqui.
  * Classes de uso que NAO estao na Tabela 24 (ex.: classes que nao
    ocorrem no Estado de SP) viram NoData no resultado, em vez de manter o
    codigo original (comportamento do Reclassify do model com "DATA",
    que deixaria o numero da classe somando na matriz). O script avisa se
    encontrar classes assim.
  * Como a "Fragilidade Ambiental Potencial / Emergente" (cap. 6.6.2.1 e
    6.6.2.2) parte da matriz de 4 algarismos gerada aqui, ela e uma
    ferramenta a parte (nao incluida neste script).

Requisitos: ArcGIS Pro com a extensao Spatial Analyst licenciada.

Como rodar: basta executar o script. Ele procura sozinho o Grau de
Dissecacao (saida do script 3, no local padrao); se nao encontrar,
pergunta o caminho na tela. Tambem pergunta: o vetor pedologico (campo
"Frag"), o vetor climatico (campo "Fragilidade"), o dado de uso da terra
(um raster OU uma geodatabase/pasta com varios rasters - um por ano) e o
limite vetorial da area de interesse.
"""
import os
import arcpy
from arcpy.sa import ExtractByMask, Int, Raster, Reclassify, RemapValue

# ------------------------------------------------------------------
# PARAMETROS - ajuste para o seu ambiente
# ------------------------------------------------------------------
# Geodatabase de trabalho: todas as saidas sao gravadas aqui. Se ela
# ainda nao existir, o script cria automaticamente.
WORKSPACE = r"C:\alexgeopro\FragilidadeAmbiental.gdb"

# Local padrao onde o script 3 (versao ArcGIS Pro) grava o Grau de
# Dissecacao de Fragilidade - usado automaticamente quando existir.
GRAU_DISSECACAO_PADRAO = r"C:\alexgeopro\GrauDeDissecacao.gdb\b_GrauDeDissecacao_Fragilidade"

CELL_SIZE = 0.00027777778   # ~30 m em graus (mesma resolucao do model)
EPSG_SAIDA = 4674           # SIRGAS 2000 Geografico
BUFFER_METROS = 2000        # folga usada para recortar os dados de entrada
CAMPO_SOLO = "Frag"         # campo de fragilidade (1-5, 7 urbano, 9 agua) no vetor de solos
CAMPO_CLIMA = "Fragilidade" # campo de fragilidade (1-5) no vetor climatico
TRANSFORMACAO_PADRAO = "SIRGAS_2000_To_WGS_1984_1"  # a mesma usada no model

# Filtro opcional: se o dado de uso da terra for uma pasta/geodatabase com
# varios rasters, so processa os que contem este texto no nome ("" = todos).
FILTRO_NOME_USO = ""

# False: se o resultado de um ano ja existir na geodatabase, pula esse ano
# (permite retomar uma execucao interrompida). True: refaz tudo.
SOBRESCREVER = False

# False: apaga os rasters intermediarios de cada ano de uso da terra
# (reprojetado/recortado/reclassificado) ao terminar o ano - economiza
# bastante disco quando sao 38 anos. True: mantem todos.
MANTER_INTERMEDIARIOS = False

# Reclassificacao do relevo: Grau de Dissecacao (dezena = classe do
# entalhamento, unidade = classe da dimensao interfluvial) -> fragilidade
# do relevo no milhar (Tabela 2 da tese / Ross 2012).
REMAP_RELEVO = [
    [11, 1000], [12, 2000], [13, 3000], [14, 4000], [15, 5000],
    [21, 2000], [22, 2000], [23, 3000], [24, 4000], [25, 5000],
    [31, 3000], [32, 3000], [33, 3000], [34, 4000], [35, 5000],
    [41, 4000], [42, 4000], [43, 4000], [44, 4000], [45, 5000],
    [51, 5000], [52, 5000], [53, 5000], [54, 5000], [55, 5000],
]

# Reclassificacao do uso da terra: codigo MapBiomas (colecao 8) ->
# fragilidade na dezena (Tabela 24 da tese x 10; 24 urbano = 70;
# 31/33 agua = 90; 0 sem informacao = 90, como no model).
REMAP_USO = [
    [0, 90], [3, 10], [4, 20], [5, 10], [9, 30], [11, 50], [12, 20],
    [13, 50], [15, 30], [19, 50], [20, 40], [21, 50], [23, 50], [24, 70],
    [25, 50], [29, 50], [30, 50], [31, 90], [32, 50], [33, 90], [39, 40],
    [41, 50], [46, 30], [47, 30], [48, 40], [49, 10], [50, 20], [62, 40],
]
CLASSES_USO_CONHECIDAS = {origem for origem, _ in REMAP_USO}

# Saidas fixas (as de uso da terra levam o nome do raster de origem)
LIM_A_SIRGAS = os.path.join(WORKSPACE, "lim_a_LimiteSirgas")
LIM_B_BUFFER = os.path.join(WORKSPACE, "lim_b_Limite_Buffer2Km")
REL_A_GRAU = os.path.join(WORKSPACE, "rel_a_grau_dissecacao")
REL_B_FRAGIL = os.path.join(WORKSPACE, "rel_b_RelevoFragil")
PED_A_SIRGAS = os.path.join(WORKSPACE, "ped_a_PEDOLOGICO_SIRGAS")
PED_B_CLIP = os.path.join(WORKSPACE, "ped_b_PEDOLOGICO_Clip")
PED_C_RASTER = os.path.join(WORKSPACE, "ped_c_PedRaster")
PED_D_FRAGIL = os.path.join(WORKSPACE, "ped_d_SolosFragil")
CLI_A_SIRGAS = os.path.join(WORKSPACE, "cli_a_Clima_Project")
CLI_B_CLIP = os.path.join(WORKSPACE, "cli_b_clima_clip")
CLI_C_FRAGIL = os.path.join(WORKSPACE, "cli_c_ClimaFragil")
A_FRAGILIDADE_FINAL = os.path.join(WORKSPACE, "a_FragilidadeFinal")


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


def pedir_caminho(mensagem):
    """Pergunta um caminho ao usuario e so aceita quando o dado
    realmente existir nesse caminho."""
    while True:
        caminho = input(mensagem).strip().strip('"')
        if not caminho:
            print("  -> Caminho vazio, tente novamente.")
            continue
        if arcpy.Exists(caminho):
            return caminho
        print(f"  -> Nao encontrei nada em '{caminho}'. Confira o caminho e tente de novo.")


def pedir_vetor_com_campo(mensagem, campo):
    """Pede um vetor e confere se ele tem o campo de fragilidade."""
    while True:
        caminho = pedir_caminho(mensagem)
        nomes = [f.name.lower() for f in arcpy.ListFields(caminho)]
        if campo.lower() in nomes:
            return caminho
        print(f"  -> '{caminho}' nao tem o campo '{campo}'. Campos encontrados: {nomes}")


def achar_ou_pedir_caminho(caminho_padrao, descricao):
    """Tenta usar automaticamente o caminho padrao (saida do script 3);
    se nao existir, pergunta o caminho na tela."""
    if arcpy.Exists(caminho_padrao):
        print(f"  {descricao}: encontrado automaticamente em '{caminho_padrao}'.")
        return caminho_padrao
    print(f"  {descricao}: nao encontrei em '{caminho_padrao}'.")
    return pedir_caminho(f"  Informe o caminho de {descricao}: ")


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
    """Reprojeta um raster de classes (vizinho mais proximo) para o SRC
    alvo. Mantem a resolucao nativa quando o dado ja e geografico."""
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


def apagar(*caminhos):
    for c in caminhos:
        if arcpy.Exists(c):
            arcpy.management.Delete(c)


# ------------------------------------------------------------------
# Programa principal
# ------------------------------------------------------------------
def main():
    preparar_workspace(WORKSPACE)

    arcpy.env.workspace = WORKSPACE
    arcpy.env.overwriteOutput = True
    arcpy.CheckOutExtension("Spatial")

    print()
    grau_dissecacao = achar_ou_pedir_caminho(
        GRAU_DISSECACAO_PADRAO, "Grau de Dissecacao - Fragilidade (b_GrauDeDissecacao_Fragilidade)"
    )
    pedologico = pedir_vetor_com_campo(
        f"Caminho do mapa pedologico (vetor com o campo '{CAMPO_SOLO}', "
        "ex.: C:\\dados\\GDB Final.gdb\\PEDOLOGICO_SP_ROSSI_2017_V4): ", CAMPO_SOLO
    )
    clima = pedir_vetor_com_campo(
        f"Caminho do vetor climatico ja classificado (WorldClim, campo '{CAMPO_CLIMA}', "
        "ex.: C:\\dados\\ClimaFragilidade.gdb\\wc21_Br): ", CAMPO_CLIMA
    )
    uso_terra = pedir_caminho(
        "Caminho do Uso e Cobertura da Terra (um raster OU uma geodatabase/pasta com um raster por ano, "
        "ex.: C:\\dados\\Mapbiomas8_SP.gdb): "
    )
    limite = pedir_caminho(
        "Caminho do limite vetorial da area de interesse (padrao: limite do Estado de SP, "
        "ex.: C:\\dados\\EstadoSP_2023.shp): "
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
        print("1/6 - Limite da area: SIRGAS 2000 + buffer de 2 km...")
        projetar_vetor(limite, LIM_A_SIRGAS, sr_alvo)
        # GEODESIC: o buffer e em metros sobre dado geografico (o model usava
        # PLANAR). Dissolve "ALL" evita feicoes sobrepostas no recorte.
        arcpy.analysis.Buffer(LIM_A_SIRGAS, LIM_B_BUFFER, f"{BUFFER_METROS} Meters",
                              "FULL", "ROUND", "ALL", "", "GEODESIC")

        # 2. Relevo -----------------------------------------------------------------
        print("2/6 - Relevo: Grau de Dissecacao -> fragilidade (1000 a 5000)...")
        grau = projetar_raster(grau_dissecacao, REL_A_GRAU, sr_alvo)
        Reclassify(Raster(grau), "Value", RemapValue(REMAP_RELEVO), "NODATA").save(REL_B_FRAGIL)
        # O raster de relevo e a grade de referencia de todo o resto
        celula_ref = Raster(REL_B_FRAGIL).meanCellWidth

        # Tudo abaixo e alinhado a grade do raster de relevo (vizinho mais proximo)
        with arcpy.EnvManager(snapRaster=REL_B_FRAGIL, cellSize=REL_B_FRAGIL,
                              resamplingMethod="NEAREST"):
            # 3. Solos -------------------------------------------------------------
            print("3/6 - Solos: reprojetar, recortar, rasterizar o campo 'Frag' e x 100...")
            projetar_vetor(pedologico, PED_A_SIRGAS, sr_alvo)
            arcpy.analysis.Clip(PED_A_SIRGAS, LIM_B_BUFFER, PED_B_CLIP)
            arcpy.conversion.FeatureToRaster(PED_B_CLIP, CAMPO_SOLO, PED_C_RASTER, celula_ref)
            (Raster(PED_C_RASTER) * 100).save(PED_D_FRAGIL)

            # 4. Clima -------------------------------------------------------------
            print("4/6 - Clima: reprojetar, recortar e rasterizar o campo 'Fragilidade'...")
            projetar_vetor(clima, CLI_A_SIRGAS, sr_alvo)
            arcpy.analysis.Clip(CLI_A_SIRGAS, LIM_B_BUFFER, CLI_B_CLIP)
            arcpy.conversion.FeatureToRaster(CLI_B_CLIP, CAMPO_CLIMA, CLI_C_FRAGIL, celula_ref)

            # 5. Relevo + Solos + Clima -------------------------------------------
            print("5/6 - Relevo + Solos + Clima (a_FragilidadeFinal)...")
            Int(Raster(REL_B_FRAGIL) + Raster(PED_D_FRAGIL) + Raster(CLI_C_FRAGIL)).save(A_FRAGILIDADE_FINAL)

            # 6. Uso e cobertura da terra - um resultado por raster -----------------
            print(f"6/6 - Uso e Cobertura da Terra ({len(rasters_uso)} raster(s))...")
            resultados = []
            for i, uso_original in enumerate(rasters_uso, start=1):
                nome = arcpy.ValidateTableName(
                    os.path.splitext(os.path.basename(uso_original))[0], WORKSPACE
                )
                saida = os.path.join(WORKSPACE, f"c_{nome}_FRAGILIDADE_FINAL")
                print(f"  [{i}/{len(rasters_uso)}] {nome} ...", end=" ")

                if arcpy.Exists(saida) and not SOBRESCREVER:
                    print("ja existe - pulando.")
                    resultados.append(saida)
                    continue

                uso_a = os.path.join(WORKSPACE, f"uso_a_{nome}_Project")
                uso_b = os.path.join(WORKSPACE, f"uso_b_{nome}_Extract")
                uso_c = os.path.join(WORKSPACE, f"uso_c_{nome}_UsoTerraFragil")
                soma = os.path.join(WORKSPACE, f"b_{nome}_FragFinal")

                # Project Raster -> Extract by Mask (buffer) -> Reclassify
                uso_proj = projetar_raster(uso_original, uso_a, sr_alvo)
                ExtractByMask(Raster(uso_proj), LIM_B_BUFFER).save(uso_b)

                # Aviso: classes que nao estao na Tabela 24 viram NoData
                valores = {r[0] for r in arcpy.da.SearchCursor(uso_b, ["Value"])} \
                    if Raster(uso_b).hasRAT else set()
                desconhecidas = sorted(v for v in valores if v not in CLASSES_USO_CONHECIDAS)
                if desconhecidas:
                    print(f"\n    AVISO: classes fora da Tabela 24 (viram NoData): {desconhecidas}", end=" ")

                Reclassify(Raster(uso_b), "VALUE", RemapValue(REMAP_USO), "NODATA").save(uso_c)

                # Soma com a matriz Relevo+Solo+Clima e recorta pelo limite exato
                Int(Raster(A_FRAGILIDADE_FINAL) + Raster(uso_c)).save(soma)
                ExtractByMask(Raster(soma), LIM_A_SIRGAS).save(saida)

                if not MANTER_INTERMEDIARIOS:
                    apagar(uso_a, uso_b, uso_c, soma)
                resultados.append(saida)
                print("ok.")

        print()
        print("Concluido.")
        print("a_FragilidadeFinal (Relevo + Solos + Clima, sem o uso da terra):", A_FRAGILIDADE_FINAL)
        print("Fragilidade Ambiental final (matriz de 4 algarismos), um raster por uso da terra:")
        for r in resultados:
            print("  ", r)

    finally:
        arcpy.CheckInExtension("Spatial")


if __name__ == "__main__":
    main()
