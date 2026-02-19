import streamlit as st
import pandas as pd
import requests
from io import StringIO
import math
from pathlib import Path

FILE_STOCK_LIST = "1nk01bicZkwvGbGTvNWYYMq4A-4dpUIbr" # 全銘柄一覧
FILE_BAIBAIDAIKIN = "1XA33JiyavO8lyNNrg2NHlsJ0EJBJeOnm" # 売買代金TOP
FILE_DEKIDAKA = "18OKlrHR1SvhgQD2RdY76wmpu8P4nUZt2" # 出来高TOP


# -----------------------------------------------------------------------------
# Declare some useful functions.

@st.cache_data
def get_gdp_data():
    """Grab GDP data from a CSV file.

    This uses caching to avoid having to read the file every time. If we were
    reading from an HTTP endpoint instead of a file, it's a good idea to set
    a maximum age to the cache with the TTL argument: @st.cache_data(ttl='1d')
    """

    # Instead of a CSV on disk, you could read from an HTTP endpoint here too.
    DATA_FILENAME = Path(__file__).parent/'data/gdp_data.csv'
    raw_gdp_df = pd.read_csv(DATA_FILENAME)

    MIN_YEAR = 1960
    MAX_YEAR = 2022

    # The data above has columns like:
    # - Country Name
    # - Country Code
    # - [Stuff I don't care about]
    # - GDP for 1960
    # - GDP for 1961
    # - GDP for 1962
    # - ...
    # - GDP for 2022
    #
    # ...but I want this instead:
    # - Country Name
    # - Country Code
    # - Year
    # - GDP
    #
    # So let's pivot all those year-columns into two: Year and GDP
    gdp_df = raw_gdp_df.melt(
        ['Country Code'],
        [str(x) for x in range(MIN_YEAR, MAX_YEAR + 1)],
        'Year',
        'GDP',
    )

    # Convert years from string to integers
    gdp_df['Year'] = pd.to_numeric(gdp_df['Year'])

    return gdp_df


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

gdp_df = get_gdp_data()

# -----------------------------------------------------------------------------
# Draw the actual page

# Set the title that appears at the top of the page.
'''
# :earth_americas: GDP dashboard

Browse GDP data from the [World Bank Open Data](https://data.worldbank.org/) website. As you'll
notice, the data only goes to 2022 right now, and datapoints for certain years are often missing.
But it's otherwise a great (and did I mention _free_?) source of data.
'''

# Add some spacing
''
''

min_value = gdp_df['Year'].min()
max_value = gdp_df['Year'].max()

from_year, to_year = st.slider(
    'Which years are you interested in?',
    min_value=min_value,
    max_value=max_value,
    value=[min_value, max_value])

countries = gdp_df['Country Code'].unique()

if not len(countries):
    st.warning("Select at least one country")

selected_countries = st.multiselect(
    'Which countries would you like to view?',
    countries,
    ['DEU', 'FRA', 'GBR', 'BRA', 'MEX', 'JPN'])

''
''
''

# Filter the data
filtered_gdp_df = gdp_df[
    (gdp_df['Country Code'].isin(selected_countries))
    & (gdp_df['Year'] <= to_year)
    & (from_year <= gdp_df['Year'])
]

st.header('GDP over time', divider='gray')

''

st.line_chart(
    filtered_gdp_df,
    x='Year',
    y='GDP',
    color='Country Code',
)

''
''


first_year = gdp_df[gdp_df['Year'] == from_year]
last_year = gdp_df[gdp_df['Year'] == to_year]

st.header(f'GDP in {to_year}', divider='gray')

''

cols = st.columns(4)

for i, country in enumerate(selected_countries):
    col = cols[i % len(cols)]

    with col:
        first_gdp = first_year[first_year['Country Code'] == country]['GDP'].iat[0] / 1000000000
        last_gdp = last_year[last_year['Country Code'] == country]['GDP'].iat[0] / 1000000000

        if math.isnan(first_gdp):
            growth = 'n/a'
            delta_color = 'off'
        else:
            growth = f'{last_gdp / first_gdp:,.2f}x'
            delta_color = 'normal'

        st.metric(
            label=f'{country} GDP',
            value=f'{last_gdp:,.0f}B',
            delta=growth,
            delta_color=delta_color
        )

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

filtered_df = df[selected_columns] # まずは列を絞った状態からスタート

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
    unique_values = df[filter_target_col].unique().tolist()
    selected_values = st.sidebar.multiselect(f"{filter_target_col} の値で絞り込み", unique_values, default=unique_values)
    
    # 選ばれた値に対応する行だけを残す
    filtered_df = filtered_df[filtered_df[filter_target_col].isin(selected_values)]

# --- 最終的な表示 ---
st.subheader("フィルタリング結果")
st.write(f"表示件数: {len(filtered_df)} 件 / 全 {len(df)} 件")
st.dataframe(filtered_df, use_container_width=True)
