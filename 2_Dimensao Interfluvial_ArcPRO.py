# -*- coding: utf-8 -*-
"""
2_Dimensao Interfluvial Media_FINAL_Geografica
=================================================
Convertido a partir do model do ModelBuilder de mesmo nome, dentro da
toolbox "1_Ferramentas Finais da Tese.tbx". Os parametros foram
conferidos contra o script exportado nativamente do ArcMap 10.3
("2_Dimensao_Interfluvial_Arc103.py", Model > Export > To Python Script)
e contra a descricao metodologica da propria tese (Alex da Silva Sousa,
2024, Cap. 6.3 "Geomorfologia e Hidrografia", p. 62-64,
DOI: 10.11606/T.8.2024.tde-18022025-121027).

Metodologia (conforme descrita na tese):

O objetivo desta ferramenta e obter, para cada subbacia, a "dimensao
interfluvial media": a largura media do espaco entre os canais de
drenagem (o interfluvio), estimada a partir da distancia ao ponto mais
"central" de cada subbacia.

    (a) O raster de subbacias e convertido para poligono, no sistema de
        projecao SIRGAS 2000 Geografico.
    (b) O poligono e convertido para linha (as bordas das subbacias).
    (c) A partir da linha, calcula-se a Distancia Euclidiana: quanto
        mais distante da borda, maior o valor; quanto mais proximo,
        menor o valor.
    (d) Os valores sao convertidos para numeros inteiros em metros,
        multiplicando por uma constante (107015). Essa constante foi
        obtida comparando os resultados gerados pelo dado em projecao
        UTM com o dado em coordenadas geograficas - e foi adotada assim
        para nao deixar a ferramenta limitada a um fuso UTM especifico.
    (e) Os valores inteiros sao transformados em negativos, de forma
        que o menor valor passe a representar o ponto MAIS distante das
        bordas da subbacia (ou seja, o ponto mais "central").
    (f) "Flow Direction" e aplicado sobre os valores negativos de (e),
        gerando um dado onde os valores menores representam a
        estimativa do centro matematico da subbacia.
    (g) "Sink" determina, a partir do Flow Direction (f), as areas de
        menor valor - que sao os pontos mais distantes das bordas da
        subbacia, ou seja, a estimativa do(s) ponto(s) central(is) de
        cada subbacia.
    (h) Os pontos de (g) sao convertidos para vetor. Adiciona-se um
        campo com o valor inteiro de distancia euclidiana (d) - a
        distancia desse ponto ate as bordas da subbacia - e depois um
        segundo campo ("diametro") que e esse valor multiplicado por 2:
        a dimensao do interfluvio naquele ponto central.
    (i) Os pontos (h) sao convertidos de volta para raster (valor =
        diametro) e cruzados com o limite das subbacias via "Zonal
        Statistics" (MEAN), obtendo a media dos valores de dimensao
        interfluvial dentro de cada subbacia (j).
    (j) Resultado: as subbacias, cada uma com o valor medio de dimensao
        interfluvial.
    (l) Reclassifica-se (j) em duas variantes, conforme as
        metodologias de Ross (1994, 2012) - Fragilidade - e de Crepani
        et al. (1996, 2001) - Vulnerabilidade -, com os intervalos das
        Tabelas 5 e 7 do Cap. 5.4.1 "Geomorfologia" da tese.

Sobre o dado de entrada (subbacias): a tese testou tanto subbacias
geradas automaticamente (Fill do MDT + "r.watershed" do QGIS) quanto
dados secundarios (ottobacias da ANA, e as subbacias oficiais do Estado
de Sao Paulo). Por padrao, este script usa as subbacias elaboradas pela
Secretaria do Meio Ambiente do Estado de Sao Paulo (SMA/CPLA, 2013,
executado pela FUNCATE em parceria com o Instituto Geologico - IG, a
partir de MDE derivado de cartas 1:50.000 do IBGE/IGG/Exercito, projeto
GISAT; ver "Ficha_Tecnica_Sub_bacia.pdf"), convertidas para raster.
Qualquer outra fonte de subbacias serve, desde que tambem esteja em
formato raster antes de rodar este script - a ferramenta em si nao faz
distincao entre a origem do dado.

Requisitos: ArcGIS Pro com as extensoes Spatial Analyst e 3D Analyst
licenciadas (Add Surface Information usa 3D Analyst).

Como rodar: basta executar o script. Ele pergunta, na tela, o caminho
do raster de subbacias (por padrao, "Subbacias.tif") - nao e preciso
editar o codigo para isso. A geodatabase de trabalho (workspace) e
criada automaticamente, se ainda nao existir.
"""
import os
import arcpy
from arcpy.sa import (
    EucDistance, FlowDirection, Sink, ZonalStatistics,
    Reclassify, RemapRange, Raster, Int,
)

# ------------------------------------------------------------------
# PARAMETROS - ajuste para o seu ambiente
# ------------------------------------------------------------------
# Geodatabase de trabalho: todas as saidas intermediarias e finais sao
# gravadas aqui. Se ela ainda nao existir, o script cria automaticamente
# (inclusive a pasta C:\alexgeopro, se necessario).
WORKSPACE = r"C:\alexgeopro\DimensaoInterfluvial.gdb"

# Parametros
CELL_SIZE = 0.00027777778          # ~30 m (resolucao do SRTM, igual aos demais scripts)
FATOR_GRAUS_PARA_METROS = 107015   # ver nota do passo (d) acima
N_ITERACOES_ELIMINATE = 5          # numero de rodadas de limpeza (igual ao model original)

# Field info dos Make Feature Layer (confirmado no script exportado do ArcMap 10.3)
FIELD_INFO_INICIAL = (
    "Shape Shape VISIBLE NONE;OBJECTID OBJECTID VISIBLE NONE;"
    "Shape_Length Shape_Length VISIBLE NONE;Shape_Area Shape_Area VISIBLE NONE;"
    "ID ID VISIBLE NONE;GRIDCODE GRIDCODE VISIBLE NONE"
)

# Reclassificacao final da dimensao interfluvial media (Tabela 5/Tabela 7,
# Cap. 5.4.1 da tese) - confirmadas no script exportado do ArcMap 10.3
REMAP_FRAGILIDADE = [
    [0, 250, 5], [250, 750, 4], [750, 1750, 3], [1750, 3750, 2], [3750, 100000, 1],
]
REMAP_VULNERABILIDADE = [
    [-100000, 250, 5], [250, 750, 4], [750, 2000, 3], [2000, 5000, 2], [5000, 100000, 1],
]

# Saidas (nomes iguais aos do model original)
A_SUBBACIAS_POL = os.path.join(WORKSPACE, "a_Subbacias_Pol")
B_SUBBACIAS_POLINE = os.path.join(WORKSPACE, "b_Subbacias_Poline")
C_SUBBACIAS_EUCDIST = os.path.join(WORKSPACE, "c_Subbacias_EucDist")
C_OUTPUT_DIRECTION = os.path.join(WORKSPACE, "c_Output_Direction")
D_EUCDISTINT = os.path.join(WORKSPACE, "d_Subbacias_EucDistInt")
E_EUCDISTINTINVERT = os.path.join(WORKSPACE, "e_Subbacias_EucDistIntInvert")
F_FLOWDIRECTION = os.path.join(WORKSPACE, "f_Subbacias_EucDistIntInvertFD")
F_DROP_RASTER = os.path.join(WORKSPACE, "f_drop_raster")
G_SINK = os.path.join(WORKSPACE, "g_Subbacias_EucDistIntInvertFDSink")
H_SINK_POINT = os.path.join(WORKSPACE, "h_sink_point")
I_SINKPTRASTER = os.path.join(WORKSPACE, "i_SinkPtRaster")
J_DIMENSAO = os.path.join(WORKSPACE, "j_Dimensao")
L_DIMENSAO_RECLA_FRAG = os.path.join(WORKSPACE, "l_DimensaoReclaFrag")
L_DIMENSAO_RECLA_VULN = os.path.join(WORKSPACE, "l_DimensaoReclaVul")


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
    """Pergunta um caminho ao usuario (raster) e so aceita quando o dado
    realmente existir nesse caminho."""
    while True:
        caminho = input(mensagem).strip().strip('"')
        if not caminho:
            print("  -> Caminho vazio, tente novamente.")
            continue
        if arcpy.Exists(caminho):
            return caminho
        print(f"  -> Nao encontrei nada em '{caminho}'. Confira o caminho e tente de novo.")


def limpar_poligonos_sem_ponto(poligonos, pontos_referencia, n_iteracoes, prefixo):
    """
    Reproduz o passo de limpeza do model original: poligonos de subbacia
    que nao intersectam nenhum ponto central (h) sao fundidos ao vizinho
    que intersecte (Make Feature Layer -> Select Layer By Location ->
    Eliminate), repetido ate toda subbacia ter um ponto central associado.

    NOTA sobre o script exportado do ArcMap 10.3: nele, a variavel que o
    Eliminate usa como entrada ("Output_Layer_Name") na verdade NAO e
    reatribuida apos o Select Layer By Location - ela fica presa a um
    valor de outro elemento do model (o mesmo artefato ja documentado no
    script "1_entalhamento_do_vale.py", conhecido do exportador
    Model->Python do ArcMap para ferramentas que modificam a selecao
    "in place"). Aqui, a funcao usa diretamente a variavel do layer
    (correta) em vez de seguir esse encadeamento.

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
            selection="LENGTH",
        )
        atual = saida
    return atual


def main():
    preparar_workspace(WORKSPACE)

    arcpy.env.workspace = WORKSPACE
    arcpy.env.overwriteOutput = True
    arcpy.CheckOutExtension("Spatial")
    arcpy.CheckOutExtension("3D")

    # Dado de entrada, informado pelo usuario na hora de rodar o script
    print()
    SUBBACIAS_RASTER = pedir_caminho(
        "Caminho do raster de subbacias (ex.: C:\\dados\\Subbacias.tif): "
    )
    print()

    try:
        # (a) Raster to Polygon --------------------------------------------
        print("(a) 1/13 - Raster to Polygon...")
        arcpy.conversion.RasterToPolygon(SUBBACIAS_RASTER, A_SUBBACIAS_POL, "SIMPLIFY", "Value")

        # (b) Polygon To Line -------------------------------------------------
        print("(b) 2/13 - Polygon To Line...")
        arcpy.management.PolygonToLine(A_SUBBACIAS_POL, B_SUBBACIAS_POLINE, "IDENTIFY_NEIGHBORS")

        # (c) Euclidean Distance ------------------------------------------------
        print("(c) 3/13 - Euclidean Distance...")
        EucDistance(
            in_source_data=B_SUBBACIAS_POLINE,
            cell_size=CELL_SIZE,
            out_direction_raster=C_OUTPUT_DIRECTION,
        ).save(C_SUBBACIAS_EUCDIST)

        # (d) Raster Calculator: converte para inteiro / escala -------------------
        print("(d) 4/13 - Raster Calculator (Int + escala x107015)...")
        Int(Raster(C_SUBBACIAS_EUCDIST) * FATOR_GRAUS_PARA_METROS).save(D_EUCDISTINT)

        # (e) Raster Calculator: inverte o sinal ------------------------------------
        print("(e) 5/13 - Raster Calculator (inverter sinal)...")
        (Raster(D_EUCDISTINT) * -1).save(E_EUCDISTINTINVERT)

        # (f) Flow Direction -----------------------------------------------------------
        print("(f) 6/13 - Flow Direction...")
        FlowDirection(
            in_surface_raster=E_EUCDISTINTINVERT,
            force_flow="NORMAL", out_drop_raster=F_DROP_RASTER,
        ).save(F_FLOWDIRECTION)

        # (g) Sink -----------------------------------------------------------------------
        print("(g) 7/13 - Sink (pontos centrais de cada subbacia)...")
        Sink(F_FLOWDIRECTION).save(G_SINK)

        # (h) Raster to Point + campos diametro ----------------------------------------------
        print("(h) 8/13 - Raster to Point...")
        arcpy.conversion.RasterToPoint(G_SINK, H_SINK_POINT, "VALUE")

        print("(h) 9/13 - Add Surface Information (distancia real ate a borda)...")
        arcpy.ddd.AddSurfaceInformation(
            in_feature_class=H_SINK_POINT, in_surface=D_EUCDISTINT,
            out_property="Z", method="BILINEAR", z_factor=1,
            pyramid_level_resolution=0, noise_filtering="NO_FILTER",
        )

        print("(h) 10/13 - Add Field + Calculate Field (diametro = Z * 2)...")
        arcpy.management.AddField(H_SINK_POINT, "diametro", "LONG")
        arcpy.management.CalculateField(
            in_table=H_SINK_POINT, field="diametro",
            expression="!Z! * 2", expression_type="PYTHON3",
        )

        # (i) Point to Raster ------------------------------------------------------------------
        print("(i) 11/13 - Point to Raster (diametro)...")
        arcpy.conversion.PointToRaster(
            in_features=H_SINK_POINT, value_field="diametro",
            out_rasterdataset=I_SINKPTRASTER,
            cell_assignment_type="MOST_FREQUENT", priority_field="NONE",
            cellsize=CELL_SIZE,
        )

        # Limpeza iterativa das subbacias sem ponto central associado (Select Layer By Location + Eliminate x5)
        print("- 12/13 - Limpeza iterativa das subbacias (%dx)..." % N_ITERACOES_ELIMINATE)
        subbacias_pol_final = limpar_poligonos_sem_ponto(
            poligonos=A_SUBBACIAS_POL, pontos_referencia=H_SINK_POINT,
            n_iteracoes=N_ITERACOES_ELIMINATE, prefixo="i_eliminate",
        )

        # (i)/(j) Zonal Statistics (MEAN) --------------------------------------------------------
        print("(i)/(j) 13/13 - Zonal Statistics (MEAN) - dimensao interfluvial media por subbacia...")
        ZonalStatistics(
            in_zone_data=subbacias_pol_final, zone_field="ID",
            in_value_raster=I_SINKPTRASTER,
            statistics_type="MEAN", ignore_nodata="DATA",
        ).save(J_DIMENSAO)

        # (l) Reclassifica em 2 variantes (Fragilidade/Vulnerabilidade) -------------------------
        print("(l) Reclassify (Fragilidade - Ross)...")
        Reclassify(
            in_raster=J_DIMENSAO, reclass_field="VALUE",
            remap=RemapRange(REMAP_FRAGILIDADE), missing_values="DATA",
        ).save(L_DIMENSAO_RECLA_FRAG)

        print("(l) Reclassify (Vulnerabilidade - Crepani)...")
        Reclassify(
            in_raster=J_DIMENSAO, reclass_field="VALUE",
            remap=RemapRange(REMAP_VULNERABILIDADE), missing_values="DATA",
        ).save(L_DIMENSAO_RECLA_VULN)

        print()
        print("Concluido.")
        print("j_ (dimensao interfluvial media por subbacia, valor continuo em metros):", J_DIMENSAO)
        print("l_DimensaoReclaFrag (reclassificado, metodologia Ross - Fragilidade):", L_DIMENSAO_RECLA_FRAG)
        print("l_DimensaoReclaVul (reclassificado, metodologia Crepani - Vulnerabilidade):", L_DIMENSAO_RECLA_VULN)

    finally:
        arcpy.CheckInExtension("Spatial")
        arcpy.CheckInExtension("3D")


if __name__ == "__main__":
    main()
