import streamlit as st
import pandas as pd
import requests
from io import StringIO
from datetime import datetime
import pytz

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
        # HTTPヘッダーから日時を取得
        last_modified_str = response.headers.get('Last-Modified')
        
        if last_modified_str:
            # 文字列を日時に変換
            dt = datetime.strptime(last_modified_str, '%a, %d %b %Y %H:%M:%S %Z')
            # 日本時間に変換
            dt_jst = dt.replace(tzinfo=pytz.utc).astimezone(pytz.timezone('Asia/Tokyo'))
            last_updated = dt_jst.strftime('%Y/%m/%d %H:%M')
        else:
            # ヘッダーから取れない場合は、現在の取得時刻を表示するなどの代用
            last_updated = "日時取得不可（直近の読み込み時刻: " + datetime.now(pytz.timezone('Asia/Tokyo')).strftime('%Y/%m/%d %H:%M') + ")"
            
        # 文字コードが不明な場合は utf-8 や shift_jis を試してください
        csv_data = StringIO(response.text)
        df = pd.read_csv(csv_data)
        return df, last_updated
    else:
        raise Exception(f"ファイルの取得に失敗しました。ステータスコード: {response.status_code}")

# =========================================================
# スタイル設定(赤文字表示)
# =========================================================
def color_negative_red(val):
    if isinstance(val, (int, float)) and val < 0:
        return 'color: red'
    return ''

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
    df_stcok_list, last_updated = get_gd_file(FILE_STOCK_LIST)
    st.caption(f"最終データ更新日時: {last_updated}")
    
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
        #st.dataframe(filtered_df[selected_columns], use_container_width=True)
        # スタイル設定
        config = {
            col: st.column_config.NumberColumn(format="%d")
            for col in filtered_df.columns if pd.api.types.is_numeric_dtype(filtered_df[col])
        }
        styled_df = filtered_df[selected_columns].style.map(color_negative_red).format(
            {col: "{:,}" for col in filtered_df.columns if pd.api.types.is_numeric_dtype(filtered_df[col])}
        )

        st.dataframe(styled_df, use_container_width=True, hide_index=True)

    else:
        st.info("表示する列を少なくとも1つ選択してください。")
        
except Exception as e:
    st.error(f"データの読み込みに失敗しました。設定を確認してください。")
    st.info("エラー詳細: " + str(e))

''
