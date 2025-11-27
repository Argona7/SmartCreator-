# ================== НАСТРОЙКИ, КОТОРЫЕ МОЖНО МЕНЯТЬ ==================

# пороги фильтрации
ROI_THRESHOLD = 0.3          # минимальный ROI
MIN_INVESTED = 300.0         # минимальный total_invested_usd

# имена колонок (если у HashDive что-то изменится — просто поправишь тут)
URL_COL = "url"
INVEST_COL = "total_invested_usd"
ROI_COL = "ROI"
SCORE_COL = "Score"
PNL_COL = "realizedPnl"      # если этой колонки нет, будет использовать ROI как запасной вариант

# имя выходного файла
OUTPUT_FILENAME = "insiders_summary.xlsx"

# =====================================================================