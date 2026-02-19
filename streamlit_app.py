import streamlit as st
import pandas as pd
import requests
from io import StringIO
import math
from pathlib import Path

FILE_STOCK_LIST = "1nk01bicZkwvGbGTvNWYYMq4A-4dpUIbr" # 全銘柄一覧
FILE_BAIBAIDAIKIN = "1XA33JiyavO8lyNNrg2NHlsJ0EJBJeOnm" # 売買代金TOP
FILE_DEKIDAKA = "18OKlrHR1SvhgQD2RdY76wmpu8P4nUZt2" # 出来高TOP

# =========================================================
# GoogleDocumentからファイル取得
# =========================================================
def get_gd_file(file_id):
    # 指定したGoogleDocumentのファイルをダウンロード
    url = f"https://drive.google.com/uc?id={file_id}&export=download"
    # データを取得
    response = requests.get(url)
    
    # レスポンスが正常か確認
    if response.status_code == 200:
        # 文字コードが不明な場合は utf-8 や shift_jis を試してください
        csv_data = StringIO(response.text)
        return pd.read_csv(csv_data)
    else:
        raise Exception(f"ファイルの取得に失敗しました。ステータスコード: {response.status_code}")

# =========================================================
# GUI　ブラウザタイトル
# =========================================================
st.set_page_config(
    page_title="StcokInfochecker",
    page_icon=":chart:",
)

# =========================================================
# GUI メイン画面
# =========================================================
st.title(":chart: StockChecker")

st.header(f"銘柄一覧", divider="gray")
try:
    # データの読み込み
    df_stcok_list = get_gd_file(FILE_STOCK_LIST)
    # 全ての列名を取得
    all_columns = df_stcok_list.columns.tolist()
    
    # 最初に表示したい列名をリストで定義
    default_cols = ["銘柄コード", "銘柄名", "現在値", "前日比", "前日比率", "出来高", "売買代金", "出来高加重平均", "時価総額", "PER", "PBR", "配当", "配当利率"]

    # 実際にCSVに含まれている列だけを抽出（エラー防止のため）
    available_default_cols = [c for c in default_cols if c in df.columns]
    
    # 列洗濯用プルダウンリスト
    selected_columns = st.multiselect(
        "表示したい列を選んでください",
        options=all_columns,
        default=available_default_cols
    )
    # 選択された列がある場合のみ表示
    if selected_columns:
        filtered_df = df_stcok_list[selected_columns]
        st.dataframe(filtered_df, use_container_width=True)
    else:
        st.warning("表示する列を1つ以上選択してください。")

except Exception as e:
    st.error(f"データの読み込みに失敗しました。URLや共有設定を確認してください。")
    st.info("エラー詳細: " + str(e))

''

st.header(f"出来高TOP100", divider="gray")
try:
    # データの読み込み
    df_dekidaka = get_gd_file(FILE_BAIBAIDAIKIN)

    # データの表示
    st.dataframe(df_dekidaka) # インタラクティブな表として表示

except Exception as e:
    st.error(f"データの読み込みに失敗しました。URLや共有設定を確認してください。")
    st.info("エラー詳細: " + str(e))

''

st.header(f"売買代金TOP100", divider="gray")
try:
    # データの読み込み
    df_baibaidaikin = get_gd_file(FILE_DEKIDAKA)

    # データの表示
    st.dataframe(df_baibaidaikin) # インタラクティブな表として表示

except Exception as e:
    st.error(f"データの読み込みに失敗しました。URLや共有設定を確認してください。")
    st.info("エラー詳細: " + str(e))


# =========================================================
# GUI サイドバー
# =========================================================
# --- 行の絞り込み機能（サイドバーに配置） ---
st.sidebar.header("行のフィルタリング")

# 1. キーワードによる全体検索
search_query = st.sidebar.text_input("キーワード検索（全体）", "")

# 2. 特定の列（例：カテゴリや状態）の重複しない値で絞り込み
# ここでは例として、選択された列の中から1つ選んで絞り込むようにします
filter_target_col = st.sidebar.selectbox("絞り込み対象の列を選択", ["選択なし"] + selected_columns)

filtered_df = df_stcok_list[selected_columns] # まずは列を絞った状態からスタート

# --- フィルタリング処理 ---

# キーワード検索の適用
if search_query:
    # 全列を対象に、文字列としてキーワードを含む行を抽出
    filtered_df = filtered_df[
        filtered_df.astype(str).apply(lambda x: x.str.contains(search_query, case=False)).any(axis=1)
    ]

# 特定列の値による絞り込みの適用
if filter_target_col != "選択なし":
    # その列に含まれるユニークな値を取得
    unique_values = df_stcok_list[filter_target_col].unique().tolist()
    selected_values = st.sidebar.multiselect(f"{filter_target_col} の値で絞り込み", unique_values, default=unique_values)
    
    # 選ばれた値に対応する行だけを残す
    filtered_df = filtered_df[filtered_df[filter_target_col].isin(selected_values)]

# --- 最終的な表示 ---
st.subheader("フィルタリング結果")
st.write(f"表示件数: {len(filtered_df)} 件 / 全 {len(df)} 件")
st.dataframe(filtered_df, use_container_width=True)
