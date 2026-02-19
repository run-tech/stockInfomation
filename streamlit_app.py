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
    default_cols = ["銘柄コード", "銘柄名称", "現在値", "前日比", "前日比率", "出来高", "売買代金", "出来高加重平均", "時価総額", "PER", "PBR", "配当", "配当利率"]
    # 実際にCSVに含まれている列だけを抽出（エラー防止のため）
    available_default_cols = [c for c in default_cols if c in df_stcok_list.columns]
    
    # 列選択用プルダウンリスト
    selected_columns = st.multiselect(
        "表示したい列を選んでください",
        options=all_columns,
        default=available_default_cols
    )
    # 選択された列がある場合のみ表示
#    if selected_columns:
#        filtered_df = df_stcok_list[selected_columns]
#        st.dataframe(filtered_df, use_container_width=True)
#    else:
#        st.warning("表示する列を1つ以上選択してください。")

    st.divider() # 区切り線
    target_col = "現在値" # 絞り込みたい列名

    if target_col in df.columns:
        # データの型を数値に変換（エラーや空文字を考慮）
        df_stcok_list[target_col] = pd.to_numeric(df_stcok_list[target_col], errors="coerce")
        
        # スライダーで範囲を指定（あるいは st.number_input でも可）
        cols = st.columns(2)
        with cols[0]:
            start_range = st.number_input(f"{target_col} の最小値", value=1000)
        with cols[1]:
            end_range = st.number_input(f"{target_col} の最大値", value=5000.0)

        # データのフィルタリング
        filtered_df = df[
            (df[target_col] >= start_range) & 
            (df[target_col] <= end_range)
        ]
        
        # 表示する列だけを抽出
        if selected_columns:
            display_df = filtered_df[selected_columns]
        else:
            display_df = filtered_df

        # --- 3. 結果の表示 ---
        st.write(f"🔍 絞り込み結果: {len(display_df)} 件")
        st.dataframe(display_df, use_container_width=True)
    else:
        st.error(f"'{target_col}' という列が見つかりません。")

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
