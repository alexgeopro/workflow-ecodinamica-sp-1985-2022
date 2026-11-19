# -*- coding: utf-8 -*-
"""
1_Entalhamento do Vale_FINAL_Geografica
=========================================
Convertido a partir do model do ModelBuilder de mesmo nome, dentro da
toolbox "1_Ferramentas Finais da Tese.tbx". Os parametros foram
conferidos contra tres fontes: os tooltips do diagrama original, o
script exportado nativamente do ArcMap 10.3 (Model > Export > To Python
Script), e a descricao metodologica da propria tese (Alex da Silva
Sousa, 2024, Cap. 6.3 "Geomorfologia e Hidrografia", p. 59-61,
DOI: 10.11606/T.8.2024.tde-18022025-121027).

Metodologia (conforme descrita na tese, adaptada de Guimaraes et al.,
2017, para automatizar o calculo do grau de dissecacao do relevo de
Ross e de Crepani):

O objetivo desta ferramenta e obter, pixel a pixel, o "entalhamento do
vale": o quanto cada ponto do terreno esta rebaixado em relacao ao
divisor de aguas (linha de crista) mais proximo. Isso e feito de forma
indireta, usando o MDT invertido para que as ferramentas hidrologicas
do ArcGIS (que naturalmente buscam pontos baixos) passem a identificar
os pontos ALTOS do relevo original:

    (a) Reprojeta-se o MDT (SRTM) e o limite da area de interesse para
        SIRGAS 2000 Geografico.
    (b) Gera-se um buffer de 2 km do limite, para recortar o SRTM com
        margem de seguranca.
    (c) Usa-se "Fill" para preencher imperfeicoes do MDT (ex.: areas de
        reservatorios). Esse dado (MDT preenchido) e usado em 3 pontos
        do fluxo; primeiro ele e multiplicado por -1 (c1), invertendo o
        relevo.
    (d) "Flow Direction" roda sobre o MDT invertido (c1).
    (e) A partir de (d), "Sink" busca os pontos mais baixos do relevo
        invertido - que, por estar invertido, correspondem aos pontos
        MAIS ALTOS do relevo original (picos/divisores). Esses pontos
        sao convertidos para vetor e recebem a cota original (de c).
        Em paralelo, a partir de (d) tambem se geram "bacias" via
        "Basin" (bacias do relevo invertido, ou seja, zonas de
        influencia de cada pico) - convertidas para poligono. Poligonos
        que nao intersectam nenhum ponto de pico sao fundidos a um
        vizinho que intersecte, via "Eliminate", garantindo que toda
        zona tenha um pico associado.
    (f) Os pontos de pico (com cota original) sao convertidos para
        raster.
    (g) "Zonal Statistics" (MAXIMUM) cruza as zonas de (e) com o raster
        de cotas de pico (f), espalhando a cota do pico por toda a sua
        zona de influencia.
    (h) Entalhamento = (g) cota do pico da zona) - (c) cota real do
        terreno = o quanto cada pixel esta abaixo do divisor mais
        proximo.
    (i) Reclassifica-se (h) conforme as Tabelas 5 e 7 (Cap. 5.4.1
        Geomorfologia da tese), em 5 classes de peso (10 a 50).

Requisitos: ArcGIS Pro com as extensoes Spatial Analyst e 3D Analyst
licenciadas (Add Surface Information usa 3D Analyst).

Como rodar: basta executar o script. Ele pergunta, na tela, o caminho
do MDT (raster) e o caminho do shapefile/feature class da area de
estudo - nao e preciso editar o codigo para isso. A geodatabase de
trabalho (workspace) e criada automaticamente, se ainda nao existir.
"""
import os
import arcpy
from arcpy.sa import (
    ExtractByMask, Fill, FlowDirection, Sink, Basin,
    ZonalStatistics, Reclassify, RemapRange, Raster,
)

# ------------------------------------------------------------------
# PARAMETROS - ajuste para o seu ambiente
# ------------------------------------------------------------------
# Geodatabase de trabalho: todas as saidas intermediarias e finais sao
# gravadas aqui. Se ela ainda nao existir, o script cria automaticamente
# (inclusive a pasta C:\alexgeopro, se necessario).
WORKSPACE = r"C:\alexgeopro\Entalhamento.gdb"

# Parametros
BUFFER_DISTANCIA = "2 Kilometers"
CELL_SIZE = 0.00027777778                      # ~30 m (resolucao do SRTM)
SISTEMA_COORD_SAIDA = "GCS_SIRGAS_2000"
SISTEMA_COORD_DEM_ENTRADA = "GCS_WGS_1984"     # usado so se o raster de entrada nao tiver SR definido (ver obter_sr_raster_entrada)
N_ITERACOES_ELIMINATE = 5                      # numero de rodadas de limpeza (igual ao model original)

# Field info do primeiro Make Feature Layer (confirmado no script exportado do ArcMap 10.3)
FIELD_INFO_INICIAL = (
    "Shape Shape VISIBLE NONE;OBJECTID OBJECTID VISIBLE NONE;"
    "Shape_Length Shape_Length VISIBLE NONE;Shape_Area Shape_Area VISIBLE NONE;"
    "ID ID VISIBLE NONE;GRIDCODE GRIDCODE VISIBLE NONE"
)

# Reclassificacao final do entalhamento (Tabela 5/Tabela 7, Cap. 5.4.1 da tese)
# Value: cota do pico da zona - cota real do terreno (m) | classe de peso
REMAP_ENTALHAMENTO = [
    [-1500, 20, 10],   # < 20 m: Muito Fraco
    [20, 40, 20],      # 20-40 m: Fraco
    [40, 80, 30],      # 40-80 m: Medio
    [80, 160, 40],     # 80-160 m: Forte
    [160, 5000, 50],   # > 160 m: Muito Forte
]

# Saidas (nomes iguais aos do model original)
A_LIMITE_PROJ = os.path.join(WORKSPACE, "a_limite_Proj")
A_LIMITE_PROJ_BUFFER = os.path.join(WORKSPACE, "a_limite_Proj_Buffer")
A_MOSAICO_PROJ = os.path.join(WORKSPACE, "a_mosaico_Reproj")
B_MOSAICO_LIMITE = os.path.join(WORKSPACE, "b_Mosaico_Limite")
C_MOSAICO_FILL = os.path.join(WORKSPACE, "c_mosaico_fill")               # (c) MDT preenchido
C_MOSAICO_FILL_NEG = os.path.join(WORKSPACE, "c_mosaico_fill_neg")       # (c1) MDT invertido
D_FLOW_DIRECTION = os.path.join(WORKSPACE, "d_mosaico_flow_direction")   # (d)
D_DROP_RASTER = os.path.join(WORKSPACE, "d_drop_raster_extra")
E_SINK = os.path.join(WORKSPACE, "e_mosaico_sink")                      # (e) picos, ainda em raster
E_SINK_PT = os.path.join(WORKSPACE, "e_mosaico_sink_pt")                # (e) picos em ponto, com cota
E_BASIN = os.path.join(WORKSPACE, "e_mosaico_basin")                    # (e) zonas de influencia (raster)
E_BASIN_POL = os.path.join(WORKSPACE, "e_mosaico_basin_pol")            # (e) zonas de influencia (poligono)
F_SINK_COTA = os.path.join(WORKSPACE, "f_mosaico_Sink_Cota")            # (f)
G_SINK_BASIN = os.path.join(WORKSPACE, "g_sink_basin")                  # (g)
H_ENTALHAMENTO = os.path.join(WORKSPACE, "h_entalhamento")              # (h)
I_ENTALHAMENTO_RECLA = os.path.join(WORKSPACE, "i_EntalhamentoRecla")   # (i)


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
    """Pergunta um caminho ao usuario (raster ou feature class/shapefile)
    e so aceita quando o dado realmente existir nesse caminho."""
    while True:
        caminho = input(mensagem).strip().strip('"')
        if not caminho:
            print("  -> Caminho vazio, tente novamente.")
            continue
        if arcpy.Exists(caminho):
            return caminho
        print(f"  -> Nao encontrei nada em '{caminho}'. Confira o caminho e tente de novo.")


def obter_sr_raster_entrada(caminho_raster, sr_padrao):
    """Usa o sistema de referencia (SR) ja gravado no raster de entrada,
    se houver um definido - so usa o SR padrao (SISTEMA_COORD_DEM_ENTRADA)
    quando o raster nao tiver nenhum SR definido. Evita forcar um SR
    errado sobre um raster que ja tem o seu proprio definido (o que pode
    fazer o ProjectRaster pedir uma transformacao invalida)."""
    sr_raster = arcpy.Describe(caminho_raster).spatialReference
    if sr_raster and sr_raster.name not in ("Unknown", ""):
        print(f"  SR do MDT detectado automaticamente: {sr_raster.name}")
        return sr_raster
    print(f"  MDT sem SR definido - assumindo {sr_padrao.name}.")
    return sr_padrao


def obter_transformacao_geografica(sr_entrada, sr_saida):
    """Tenta achar, entre as transformacoes geograficas instaladas neste
    computador, uma que converta de sr_entrada para sr_saida. Retorna
    None se os dois SR forem o mesmo ou se nenhuma transformacao for
    necessaria/encontrada (comum entre SIRGAS 2000 e WGS 84, que sao
    datums muito proximos - nesse caso o ArcGIS reprojeta direto, sem
    transformacao de datum). Isso evita depender de um nome de
    transformacao fixo, que pode nao existir ou ter outro nome em cada
    instalacao do ArcGIS Pro."""
    if sr_entrada.name == sr_saida.name:
        return None
    transformacoes = arcpy.ListTransformations(sr_entrada, sr_saida)
    if transformacoes:
        print(f"  Transformacao geografica encontrada: {transformacoes[0]}")
        return transformacoes[0]
    print("  Nenhuma transformacao geografica necessaria/encontrada - reprojetando direto.")
    return None


def limpar_poligonos_sem_ponto(poligonos, pontos_referencia, campo_zona, n_iteracoes, prefixo):
    """
    Reproduz o passo (e) da tese: poligonos de zona de influencia que nao
    intersectam nenhum ponto de pico sao fundidos ao vizinho que
    intersecte (Make Feature Layer -> Select Layer By Location -> Eliminate),
    repetido ate toda zona ter um pico associado.

    NOTA sobre o script exportado do ArcMap 10.3: nele, a variavel que o
    Eliminate usa como entrada ("Output_Layer_Name") na verdade NAO e
    reatribuida apos o Select Layer By Location - ela fica presa a um
    valor de outro elemento do model (um artefato conhecido do
    exportador Model->Python do ArcMap para ferramentas que modificam a
    selecao "in place"). Aqui, a funcao usa diretamente a variavel do
    layer (correta) em vez de seguir esse encadeamento.

    Retorna o caminho do feature class final, ja limpo.
    """
    atual = poligonos
    for i in range(1, n_iteracoes + 1):
        layer = f"{prefixo}_lyr_{i}"
        arcpy.management.MakeFeatureLayer(
            atual, layer,
            field_info=FIELD_INFO_INICIAL if i == 1 else None,
        )
        arcpy.management.SelectLayerByLocation(
            in_layer=layer,
            overlap_type="INTERSECT",
            select_features=pontos_referencia,
            search_distance=None,
            selection_type="NEW_SELECTION",
            invert_spatial_relationship="INVERT",
        )
        saida = os.path.join(WORKSPACE, f"{prefixo}_elim{i:02d}")
        arcpy.management.Eliminate(
            in_features=layer,  # o layer com a selecao aplicada - nao "Output_Layer_Name"
            out_feature_class=saida,
            selection="LENGTH",  # "Eliminating polygon by border" no model original
        )
        atual = saida
    return atual


def main():
    preparar_workspace(WORKSPACE)

    arcpy.env.workspace = WORKSPACE
    arcpy.env.overwriteOutput = True
    arcpy.CheckOutExtension("Spatial")
    arcpy.CheckOutExtension("3D")

    # Dados de entrada, informados pelo usuario na hora de rodar o script
    print()
    MOSAICO_DEM = pedir_caminho("Caminho do MDT / mosaico raster (ex.: C:\\dados\\mosaicoRMSP.tif): ")
    AreaEstudo = pedir_caminho("Caminho do shapefile/feature class da area de estudo (ex.: C:\\dados\\AreaEstudo.shp): ")
    print()

    try:
        # (a) Reprojeta o limite e o MDT para SIRGAS 2000 Geografico -----
        print("(a) 1/9 - Project (area de estudo)...")
        out_sr = arcpy.SpatialReference(SISTEMA_COORD_SAIDA)
        arcpy.management.Project(
            in_dataset=AreaEstudo,
            out_dataset=A_LIMITE_PROJ,
            out_coor_system=out_sr,
            preserve_shape="NO_PRESERVE_SHAPE",
        )

        print("(a) 2/9 - Project Raster (MDT)...")
        sr_dem_entrada = obter_sr_raster_entrada(MOSAICO_DEM, arcpy.SpatialReference(SISTEMA_COORD_DEM_ENTRADA))
        transformacao = obter_transformacao_geografica(sr_dem_entrada, out_sr)
        arcpy.management.ProjectRaster(
            in_raster=MOSAICO_DEM,
            out_raster=A_MOSAICO_PROJ,
            out_coor_system=out_sr,
            resampling_type="NEAREST",
            cell_size=f"{CELL_SIZE} {CELL_SIZE}",
            geographic_transform=[transformacao] if transformacao else None,
            in_coor_system=sr_dem_entrada,
        )

        # (b) Buffer de 2 km para recortar o SRTM com margem de seguranca --
        print("(b) 3/9 - Buffer 2 km...")
        arcpy.analysis.Buffer(
            in_features=A_LIMITE_PROJ,
            out_feature_class=A_LIMITE_PROJ_BUFFER,
            buffer_distance_or_field=BUFFER_DISTANCIA,
            line_side="FULL", line_end_type="ROUND",
            dissolve_option="NONE", method="PLANAR",
        )
        ExtractByMask(A_MOSAICO_PROJ, A_LIMITE_PROJ_BUFFER).save(B_MOSAICO_LIMITE)

        # (c) Fill (preenche imperfeicoes do MDT) + inverte (c1) -----------
        print("(c) 4/9 - Fill + inverter relevo...")
        Fill(B_MOSAICO_LIMITE).save(C_MOSAICO_FILL)
        (Raster(C_MOSAICO_FILL) * -1).save(C_MOSAICO_FILL_NEG)

        # (d) Flow Direction sobre o MDT invertido --------------------------
        print("(d) 5/9 - Flow Direction (relevo invertido)...")
        FlowDirection(
            in_surface_raster=C_MOSAICO_FILL_NEG,
            force_flow="NORMAL",
            out_drop_raster=D_DROP_RASTER,
        ).save(D_FLOW_DIRECTION)

        # (e) Basin (zonas de influencia dos picos) + Sink (picos) ----------
        print("(e) 6/9 - Basin (zonas de influencia)...")
        Basin(D_FLOW_DIRECTION).save(E_BASIN)
        arcpy.conversion.RasterToPolygon(E_BASIN, E_BASIN_POL, "SIMPLIFY", "VALUE")

        print("(e) 7/9 - Sink (picos do relevo original) + cota original...")
        Sink(D_FLOW_DIRECTION).save(E_SINK)
        arcpy.conversion.RasterToPoint(E_SINK, E_SINK_PT, "VALUE")
        arcpy.ddd.AddSurfaceInformation(
            in_feature_class=E_SINK_PT,
            in_surface=C_MOSAICO_FILL,   # cota real (MDT nao invertido)
            out_property="Z",
            method="BILINEAR",
            z_factor=1,
            pyramid_level_resolution=0,
            noise_filtering="NO_FILTER",
        )

        print("(e) - Limpeza iterativa das zonas sem pico associado (%dx)..." % N_ITERACOES_ELIMINATE)
        zonas_final = limpar_poligonos_sem_ponto(
            poligonos=E_BASIN_POL,
            pontos_referencia=E_SINK_PT,
            campo_zona="ID",
            n_iteracoes=N_ITERACOES_ELIMINATE,
            prefixo="e_mosaico_basin_pol",
        )

        # (f) Cota dos picos em raster ---------------------------------------
        print("(f) 8/9 - Point to Raster (cota dos picos)...")
        arcpy.conversion.PointToRaster(
            in_features=E_SINK_PT, value_field="Z",
            out_rasterdataset=F_SINK_COTA,
            cell_assignment_type="MOST_FREQUENT", priority_field="NONE",
            cellsize=CELL_SIZE,
        )

        # (g) Zonal Statistics (MAXIMUM): espalha a cota do pico pela zona ---
        print("(g) 9/9 - Zonal Statistics (MAXIMUM)...")
        ZonalStatistics(
            in_zone_data=zonas_final, zone_field="ID",
            in_value_raster=F_SINK_COTA,
            statistics_type="MAXIMUM", ignore_nodata="DATA",
        ).save(G_SINK_BASIN)

        # (h) Entalhamento = cota do pico da zona - cota real do terreno -----
        print("(h) Raster Calculator (entalhamento)...")
        (Raster(G_SINK_BASIN) - Raster(C_MOSAICO_FILL)).save(H_ENTALHAMENTO)

        # (i) Reclassifica em 5 classes de peso (Tabela 5/7, Cap. 5.4.1) ------
        print("(i) Reclassify...")
        Reclassify(
            in_raster=H_ENTALHAMENTO, reclass_field="Value",
            remap=RemapRange(REMAP_ENTALHAMENTO),
            missing_values="DATA",  # "Change missing values to NoData: false" no model
        ).save(I_ENTALHAMENTO_RECLA)

        print("Concluido.")
        print("h_ (entalhamento, valor continuo em metros por pixel):", H_ENTALHAMENTO)
        print("i_ (entalhamento reclassificado em 5 classes de peso, conforme Ross/Crepani):", I_ENTALHAMENTO_RECLA)

    finally:
        arcpy.CheckInExtension("Spatial")
        arcpy.CheckInExtension("3D")


if __name__ == "__main__":
    main()
