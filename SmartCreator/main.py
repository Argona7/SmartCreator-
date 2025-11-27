import re
import subprocess
from pathlib import Path

import pandas as pd
from config import *


def extract_wallet(url: str) -> str:
    """
    Достаём адрес кошелька из ссылки вида:
    https://hashdive.com/Analyze_User?user_address=0x...&source=...
    """
    if not isinstance(url, str):
        return ""
    match = re.search(r"user_address=([^&]+)", url)
    return match.group(1) if match else url


def load_all_tables(tables_dir: Path) -> pd.DataFrame:
    """
    Читает все .csv из папки tables и объединяет их в один DataFrame
    с колонками wallet и market_name.
    """
    all_rows = []

    for path in sorted(tables_dir.glob("*.csv")):
        try:
            df = pd.read_csv(path)
        except Exception as e:
            print(f"[WARN] не удалось прочитать {path.name}: {e}")
            continue

        # проверяем нужные колонки
        required_cols = [URL_COL, INVEST_COL, ROI_COL, SCORE_COL]
        missing = [c for c in required_cols if c not in df.columns]
        if missing:
            print(f"[WARN] в файле {path.name} нет колонок: {missing}, пропускаю его")
            continue

        df = df.copy()
        df["wallet"] = df[URL_COL].apply(extract_wallet)
        df["market_name"] = path.stem  # имя файла без .csv

        all_rows.append(df)

    if not all_rows:
        raise ValueError("нет валидных CSV в папке tables")

    full = pd.concat(all_rows, ignore_index=True)
    return full


def build_insiders_table(full_df: pd.DataFrame) -> pd.DataFrame:
    """
    Строит агрегированную таблицу по кошелькам с фильтрами и сортировкой.
    """

    # 1) Фильтруем по ROI и минимальному инвесту на уровне СДЕЛКИ (строки)
    filt = full_df[
        (full_df[ROI_COL] > ROI_THRESHOLD) &
        (full_df[INVEST_COL] >= MIN_INVESTED)
    ].copy()

    if filt.empty:
        print("[INFO] после фильтрации таблица пустая")
        return pd.DataFrame()

    # 2) Считаем, в скольких маркетах кошелёк победил
    counts = (
        filt.groupby("wallet")["market_name"]
        .nunique()
        .rename("markets_won")
    )

    merged = filt.merge(counts, on="wallet", how="left")

    # 3) Агрегируем по кошельку
    if PNL_COL in merged.columns:
        total_pnl_agg = (PNL_COL, "sum")
    else:
        total_pnl_agg = (ROI_COL, "sum")  # запасной вариант

    wallet_level = (
        merged
        .groupby("wallet")
        .agg(
            markets_won=("markets_won", "max"),
            avg_score=(SCORE_COL, "mean"),
            avg_roi=(ROI_COL, "mean"),
            total_pnl=total_pnl_agg,
            total_invested=(INVEST_COL, "sum"),
            markets_list=("market_name", lambda x: ", ".join(sorted(set(map(str, x)))))
        )
        .reset_index()
    )

    # 🔴 4) ЖЁСТКИЙ ФИЛЬТР УЖЕ НА УРОВНЕ КОШЕЛЬКА
    wallet_level = wallet_level[wallet_level["total_invested"] >= MIN_INVESTED]

    if wallet_level.empty:
        print("[INFO] после фильтра по total_invested на уровне кошелька никого не осталось")
        return wallet_level

    # 5) Сортировка: сначала по markets_won, потом по smart score
    wallet_level = wallet_level.sort_values(
        by=["markets_won", "avg_score"],
        ascending=[False, False]
    )

    return wallet_level


def main():
    # путь к папке tables рядом с main.py
    base_dir = Path(__file__).resolve().parent
    tables_dir = base_dir / "tables"
    output_path = base_dir / OUTPUT_FILENAME

    if not tables_dir.exists():
        raise FileNotFoundError(f"папка {tables_dir} не найдена")

    print(f"[INFO] читаю CSV из: {tables_dir}")

    full = load_all_tables(tables_dir)
    insiders = build_insiders_table(full)

    if insiders.empty:
        print("[INFO] подходящих кошельков не найдено (проверь пороги фильтра)")
        return

    insiders.to_excel(output_path, index=False)
    print(f"[OK] инсайдер-таблица сохранена в: {output_path}")

    # Открываем файл автоматически
    try:
        subprocess.run(["open", str(output_path)], check=True)
        print(f"[INFO] файл открыт в Excel")
    except Exception as e:
        print(f"[WARN] не удалось открыть файл автоматически: {e}")


if __name__ == "__main__":
    main()