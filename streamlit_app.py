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
        "１．表示する列の設定",
        options=all_columns,
        default=available_default_cols
    )

    # 絞り込みの対象にする列を選択
    if selected_columns:
        st.divider()
        # 絞り込みの対象にする列を選択
        filter_cols = st.multiselect("２．絞り込み条件の設定", all_columns)
        # フィルタリング前の準備
        filtered_df = df_stcok_list.copy()

        # ETFは最初に除く
        show_all = st.checkbox("ETFも表示する", value=False)
        if not show_all and '33業種区分' in filtered_df.columns:
            filtered_df = filtered_df[filtered_df["33業種区分"] != "-"]

        # 選ばれた各列に対して、動的にフィルタUIを生成
        for col in filter_cols:
            with st.expander(f"📌 {col} の条件設定"):
                # 数値列の場合
                if pd.api.types.is_numeric_dtype(df_stcok_list[col]):
                    col_min = float(df_stcok_list[col].min())
                    col_max = float(df_stcok_list[col].max())                    
                    # 範囲スライダー
                    r = st.slider(f"{col} の範囲", col_min, col_max, (col_min, col_max), key=f"slider_{col}")
                    # フィルタ適用
                    filtered_df = filtered_df[(filtered_df[col] >= r[0]) & (filtered_df[col] <= r[1])]
                
                # 文字列列の場合
                else:
                    search_txt = st.text_input(f"{col} に含まれるキーワード", key=f"input_{col}")
                    if search_txt:
                        filtered_df = filtered_df[filtered_df[col].astype(str).str.contains(search_txt, case=False, na=False)]
                        
        # --- 結果の表示 ---
        st.divider()
        st.write(f"📊 該当件数: {len(filtered_df)}件 / 全{len(df_stcok_list)}件")
        st.dataframe(filtered_df[selected_columns], use_container_width=True)

    else:
        st.info("表示する列を少なくとも1つ選択してください。")
        
except Exception as e:
    st.error(f"データの読み込みに失敗しました。設定を確認してください。")
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
