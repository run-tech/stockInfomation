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
    page_title='StcokInfochecker',
    page_icon=':chart:', # This is an emoji shortcode. Could be a URL too.
)

# =========================================================
# GUI メイン画面
# =========================================================
st.title(":chart: StockChecker")

st.header(f"銘柄一覧", divider="gray")
try:
    # データの読み込み
    df = get_gd_file(FILE_STOCK_LIST)

    # データの表示
    st.dataframe(df) # インタラクティブな表として表示

except Exception as e:
    st.error(f"データの読み込みに失敗しました。URLや共有設定を確認してください。")
    st.info("エラー詳細: " + str(e))

''

st.header(f"出来高TOP100", divider="gray")
try:
    # データの読み込み
    df = get_gd_file(FILE_BAIBAIDAIKIN)

    # データの表示
    st.dataframe(df) # インタラクティブな表として表示

except Exception as e:
    st.error(f"データの読み込みに失敗しました。URLや共有設定を確認してください。")
    st.info("エラー詳細: " + str(e))

''

st.header(f"売買代金TOP100", divider="gray")
try:
    # データの読み込み
    df = get_gd_file(FILE_DEKIDAKA)

    # データの表示
    st.dataframe(df) # インタラクティブな表として表示

except Exception as e:
    st.error(f"データの読み込みに失敗しました。URLや共有設定を確認してください。")
    st.info("エラー詳細: " + str(e))


