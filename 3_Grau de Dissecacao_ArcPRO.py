# -*- coding: utf-8 -*-
"""
3_Grau de Dissecacao
=======================
Convertido a partir do model do ModelBuilder de mesmo nome, dentro da
toolbox "1_Ferramentas Finais da Tese.tbx". Os parametros foram
conferidos contra o script exportado nativamente do ArcMap 10.3
("3_Grau_de_Dissecacao_Arc103.py", Model > Export > To Python Script) e
contra a descricao metodologica da propria tese (Alex da Silva Sousa,
2024, Cap. 6.3 "Geomorfologia e Hidrografia", p. 64-65,
DOI: 10.11606/T.8.2024.tde-18022025-121027).

Metodologia (conforme descrita na tese):

Este e o model final da parte de Geomorfologia: soma o raster
reclassificado de Entalhamento do Vale (script 1, classes de dezena:
10 a 50) com os rasters reclassificados de Dimensao Interfluvial Media
(script 2, classes de unidade: 1 a 5 - uma para Fragilidade/Ross, outra
para Vulnerabilidade/Crepani), e recorta o resultado pelo limite da area
de interesse.

O resultado da soma e um numero de dois digitos: o primeiro (dezena) e a
classe de Fragilidade/Vulnerabilidade do Entalhamento do Vale, o segundo
(unidade) e a classe da Dimensao Interfluvial Media. Por exemplo, valor
11 = fragilidade/vulnerabilidade baixa nas duas variaveis; valor 55 =
fragilidade/vulnerabilidade alta nas duas. Como a Dimensao Interfluvial
tem duas variantes (Fragilidade e Vulnerabilidade), este script gera as
DUAS combinacoes automaticamente:

    - Grau de Dissecacao (Fragilidade) = Entalhamento_Recla + DimensaoReclaFrag
    - Grau de Dissecacao (Vulnerabilidade) = Entalhamento_Recla + DimensaoReclaVul

Requisitos: ArcGIS Pro com a extensao Spatial Analyst licenciada.

Como rodar: basta executar o script. Ele procura sozinho, nos locais
padrao onde os scripts 1 e 2 gravam suas saidas
(C:\\alexgeopro\\Entalhamento.gdb e
C:\\alexgeopro\\DimensaoInterfluvial.gdb), os tres rasters reclassificados
de que precisa; se algum nao for encontrado ali, pergunta o caminho na
tela. O limite vetorial da area de interesse (por padrao, o limite do
Estado de Sao Paulo, mas pode ser qualquer area de estudo) e sempre
perguntado na tela.
"""
import os
import arcpy
from arcpy.sa import ExtractByMask, Raster

# ------------------------------------------------------------------
# PARAMETROS - ajuste para o seu ambiente
# ------------------------------------------------------------------
# Geodatabase de trabalho: todas as saidas sao gravadas aqui. Se ela
# ainda nao existir, o script cria automaticamente.
WORKSPACE = r"C:\alexgeopro\GrauDeDissecacao.gdb"

# Locais padrao onde os scripts 1 e 2 (versao ArcGIS Pro) gravam suas
# saidas reclassificadas - usados automaticamente quando existirem.
ENTALHAMENTO_RECLA_PADRAO = r"C:\alexgeopro\Entalhamento.gdb\i_EntalhamentoRecla"
DIMENSAO_RECLA_FRAG_PADRAO = r"C:\alexgeopro\DimensaoInterfluvial.gdb\l_DimensaoReclaFrag"
DIMENSAO_RECLA_VULN_PADRAO = r"C:\alexgeopro\DimensaoInterfluvial.gdb\l_DimensaoReclaVul"

# Saidas (nomes equivalentes aos do model original, um par por variante)
A_SOMA_FRAGILIDADE = os.path.join(WORKSPACE, "a_Soma_Fragilidade")
A_SOMA_VULNERABILIDADE = os.path.join(WORKSPACE, "a_Soma_Vulnerabilidade")
B_GRAU_DISSECACAO_FRAGILIDADE = os.path.join(WORKSPACE, "b_GrauDeDissecacao_Fragilidade")
B_GRAU_DISSECACAO_VULNERABILIDADE = os.path.join(WORKSPACE, "b_GrauDeDissecacao_Vulnerabilidade")


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


def achar_ou_pedir_caminho(caminho_padrao, descricao):
    """Tenta usar automaticamente o caminho padrao (saida dos scripts
    1/2); se nao existir, pergunta o caminho na tela."""
    if arcpy.Exists(caminho_padrao):
        print(f"  {descricao}: encontrado automaticamente em '{caminho_padrao}'.")
        return caminho_padrao
    print(f"  {descricao}: nao encontrei em '{caminho_padrao}'.")
    return pedir_caminho(f"  Informe o caminho de {descricao}: ")


def main():
    preparar_workspace(WORKSPACE)

    arcpy.env.workspace = WORKSPACE
    arcpy.env.overwriteOutput = True
    arcpy.CheckOutExtension("Spatial")

    print()
    print("Localizando os rasters reclassificados dos scripts 1 e 2...")
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
        "ex.: C:\\dados\\EstadoSP_2023.shp): "
    )
    print()

    try:
        # Grau de Dissecacao - Fragilidade (Ross) --------------------------------
        print("1/4 - Raster Calculator (Entalhamento + Dimensao/Fragilidade)...")
        (Raster(entalhamento_recla) + Raster(dimensao_recla_frag)).save(A_SOMA_FRAGILIDADE)

        print("2/4 - Extract by Mask (Fragilidade)...")
        snap_anterior = arcpy.env.snapRaster
        arcpy.env.snapRaster = A_SOMA_FRAGILIDADE
        ExtractByMask(A_SOMA_FRAGILIDADE, LIMITE_AREA).save(B_GRAU_DISSECACAO_FRAGILIDADE)
        arcpy.env.snapRaster = snap_anterior

        # Grau de Dissecacao - Vulnerabilidade (Crepani) -------------------------
        print("3/4 - Raster Calculator (Entalhamento + Dimensao/Vulnerabilidade)...")
        (Raster(entalhamento_recla) + Raster(dimensao_recla_vuln)).save(A_SOMA_VULNERABILIDADE)

        print("4/4 - Extract by Mask (Vulnerabilidade)...")
        snap_anterior = arcpy.env.snapRaster
        arcpy.env.snapRaster = A_SOMA_VULNERABILIDADE
        ExtractByMask(A_SOMA_VULNERABILIDADE, LIMITE_AREA).save(B_GRAU_DISSECACAO_VULNERABILIDADE)
        arcpy.env.snapRaster = snap_anterior

        print()
        print("Concluido.")
        print("b_GrauDeDissecacao_Fragilidade (Ross - Entalhamento + Dimensao Interfluvial):", B_GRAU_DISSECACAO_FRAGILIDADE)
        print("b_GrauDeDissecacao_Vulnerabilidade (Crepani - Entalhamento + Dimensao Interfluvial):", B_GRAU_DISSECACAO_VULNERABILIDADE)

    finally:
        arcpy.CheckInExtension("Spatial")


if __name__ == "__main__":
    main()
