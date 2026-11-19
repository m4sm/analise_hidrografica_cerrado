import json
from pathlib import Path
import pandas as pd

# Caminhos relativos à raiz do repositório (analise_hidrografia_cerrado)
BASE_DIR = Path(__file__).resolve().parent.parent
RAW_FILE = BASE_DIR / "data" / "raw" / "estacoes_cerrado_807.csv"
PROCESSED_DIR = BASE_DIR / "data" / "processed"
PROCESSED_DIR.mkdir(parents=True, exist_ok=True)


def executar_pipeline():
    # Lê a base bruta consolidada das 807 estações
    df = pd.read_csv(RAW_FILE)

    # Gera CSV limpo para o Mapa do Cerrado no Grafana
    colunas_mapa = [
        "CD", "NM", "X", "Y", "ANOINI", "ANOFIM",
        "MED_ANUAL", "MIN_ANUAL", "MAX_ANUAL", "DP_ANUAL",
        "MED_CDD", "MAX_CDD", "MED_RX1DAY"
    ]
    df_mapa = df[colunas_mapa].rename(columns={
        "CD": "codigo",
        "NM": "estacao",
        "X": "longitude",
        "Y": "latitude",
        "MED_ANUAL": "precipitacao_media_mm",
        "MED_CDD": "dias_secos_consecutivos"
    })
    df_mapa.to_csv(PROCESSED_DIR / "mapa_cerrado_anual.csv", index=False)

    # Gera CSV vertical de sazonalidade (Jan-Dez) para o gráfico do Alto Tocantins
    estacoes_to = df[df["CD"].isin([948000, 1247000])].set_index("CD")
    meses = [
        ("Jan", "MED_JAN"), ("Fev", "MED_FEV"), ("Mar", "MED_MAR"),
        ("Abr", "MED_ABR"), ("Mai", "MED_MAI"), ("Jun", "MED_JUN"),
        ("Jul", "MED_JUL"), ("Ago", "MED_AGO"), ("Set", "MED_SET"),
        ("Out", "MED_OUT"), ("Nov", "MED_NOV"), ("Dez", "MED_DEZ")
    ]

    linhas_mensais = []
    for idx, (nome_mes, col) in enumerate(meses, start=1):
        linhas_mensais.append({
            "ordem": idx,
            "mes": nome_mes,
            "miracema_mm": round(float(estacoes_to.loc[948000, col]), 2),
            "conceicao_mm": round(float(estacoes_to.loc[1247000, col]), 2)
        })

    df_tocantins = pd.DataFrame(linhas_mensais)
    df_tocantins.to_csv(PROCESSED_DIR / "tocantins_sazonalidade.csv", index=False)

    # Gera JSON leve para alimentar cards numéricos direto no HTML (pasta web/)
    resumo = {
        "total_estacoes_cerrado": int(len(df)),
        "media_geral_cerrado_mm": round(float(df["MED_ANUAL"].mean()), 1),
        "tocantins": {
            "miracema": {
                "codigo": "948000",
                "periodo": f"{int(estacoes_to.loc[948000, 'ANOINI'])}-{int(estacoes_to.loc[948000, 'ANOFIM'])}",
                "media_anual_mm": round(float(estacoes_to.loc[948000, "MED_ANUAL"]), 1),
                "max_dias_secos": int(estacoes_to.loc[948000, "MAX_CDD"])
            },
            "conceicao": {
                "codigo": "1247000",
                "periodo": f"{int(estacoes_to.loc[1247000, 'ANOINI'])}-{int(estacoes_to.loc[1247000, 'ANOFIM'])}",
                "media_anual_mm": round(float(estacoes_to.loc[1247000, "MED_ANUAL"]), 1),
                "max_dias_secos": int(estacoes_to.loc[1247000, "MAX_CDD"])
            }
        }
    }
    with open(PROCESSED_DIR / "resumo_indicadores.json", "w", encoding="utf-8") as f:
        json.dump(resumo, f, ensure_ascii=False, indent=2)

    print("Pipeline concluído! Arquivos gerados em:", PROCESSED_DIR)


if __name__ == "__main__":
    executar_pipeline()