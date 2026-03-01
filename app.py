import streamlit as st
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.font_manager as fm
import os

# --- ページ設定 ---
st.set_page_config(page_title="資金繰り・成長リスクシミュレーター", layout="wide")

# --- フォント設定 ---
FONT_PATH = 'NotoSansJP-Regular.ttf'
if os.path.exists(FONT_PATH):
    fp = fm.FontProperties(fname=FONT_PATH)
    plt.rcParams['font.family'] = fp.get_name()
    font_prop = fp
else:
    font_prop = None

st.title("🚀 資金繰り・成長リスクシミュレーター")
st.write("「新規大口取引」の開始に伴う、先行支出と入金ラグが生む『死の谷』をシミュレートします。")

# --- サイドバー：1. 既存事業（定常状態） ---
st.sidebar.header("📊 1. 既存事業の状況")
initial_cash = st.sidebar.number_input("現在の現預金 (万円)", value=1000, step=100)
base_revenue = st.sidebar.number_input("既存の月間総売上 (万円)", value=1500, step=100)
fixed_cost = st.sidebar.number_input("既存の月間固定費 (万円)", value=1000, step=50)
var_cost_rate = st.sidebar.slider("既存の変動費率 (%)", 0, 100, 40) / 100

# --- サイドバー：2. 新規取引（非定常状態） ---
st.sidebar.markdown("---")
st.sidebar.header("⚡ 2. 新規大口取引の衝撃")
new_deal_rev = st.sidebar.number_input("新規取引の月間売上 (万円)", value=1500, step=100)
new_deal_var_rate = st.sidebar.slider("新規取引の変動費率（外注費等） (%)", 0, 100, 70) / 100
start_month = st.sidebar.slider("プロジェクト開始月 (支出発生)", 1, 6, 3)
payment_lag = st.sidebar.slider("入金までのラグ (ヶ月)", 1, 6, 2)

st.sidebar.markdown("---")
trials = st.sidebar.select_slider("シミュレーション回数", options=[100, 1000, 10000], value=1000)
execute_button = st.sidebar.button("🚀 成長リスクを分析する")

if execute_button:
    months = 18 # 安定期まで見るために1.5年スパン
    results = []
    
    for _ in range(trials):
        cash = initial_cash
        cash_flow = [cash]
        
        for m in range(1, months + 1):
            # A. 既存事業の収支（5%の変動リスク込）
            current_base_sales = np.random.normal(base_revenue, base_revenue * 0.05)
            base_profit = current_base_sales * (1 - var_cost_rate) - fixed_cost
            
            # B. 新規取引の収支（先行支出モデル）
            new_inflow = 0
            new_outflow = 0
            
            if m >= start_month:
                # 支出は開始月からフルで発生
                new_outflow = new_deal_rev * new_deal_var_rate
                # 入金はラグ期間を経てから発生
                if m >= (start_month + payment_lag):
                    new_inflow = new_deal_rev
            
            # C. キャッシュ更新
            cash = cash + base_profit + (new_inflow - new_outflow)
            cash_flow.append(cash)

        results.append(cash_flow)

    results = np.array(results)

    # --- グラフ描画 ---
    col1, col2 = st.columns([2, 1])
    
    with col1:
        fig, ax = plt.subplots(figsize=(10, 6))
        is_short = np.any(results < 0, axis=1)
        time_axis = np.arange(months + 1)
        
        # 安全/ショートルートの描画
        ax.plot(time_axis, results[~is_short].T, color='gray', alpha=0.02)
        if np.any(is_short):
            ax.plot(time_axis, results[is_short].T, color='#d62728', alpha=0.04, linewidth=0.8)
        
        # 中央値（青い太線）
        ax.plot(time_axis, np.median(results, axis=0), color='#1f77b4', linewidth=4, label='通常シナリオ')
        ax.axhline(0, color='black', linewidth=2.5)
        
        # 【改修ポイント】横軸を整数に固定
        ax.set_xticks(time_axis)
        
        # 特徴的なラインの追加
        ax.axvline(start_month, color='green', linestyle='--', alpha=0.6, label='新規取引 支出開始')
        ax.axvline(start_month + payment_lag, color='orange', linestyle='--', alpha=0.6, label='初入金')
        
        ax.set_title("成長の罠：新規取引に伴うキャッシュの『谷』", fontproperties=font_prop, fontsize=16)
        ax.set_xlabel("月数 (Month)", fontproperties=font_prop)
        ax.set_ylabel("現預金残高 (万円)", fontproperties=font_prop)
        ax.legend(prop=font_prop)
        st.pyplot(fig)

    with col2:
        short_rate = (np.sum(is_short) / trials) * 100
        st.metric("1.5年以内の資金ショート確率", f"{short_rate:.2f} %")
        
        # 谷の深さの分析
        median_path = np.median(results, axis=0)
        min_cash = np.min(median_path)
        cash_drop = initial_cash - min_cash
        
        st.subheader("💡 資金繰り診断")
        st.write(f"新規取引開始後、入金が始まるまでの間に、キャッシュは最大で **{cash_drop:.0f}万円** 減少します。")
        
        if min_cash < 0:
            required = abs(min_cash) + 300 # 300万のバッファを推奨
            st.error(f"通常シナリオでも資金が底を付きます。取引開始前に **{required:.0f}万円** 程度の融資（運転資金）が必要です。")
        elif short_rate > 5:
            st.warning("既存事業の変動リスクにより、成長の過程でショートする可能性があります。予備資金の確保を推奨します。")
        else:
            st.success("現在の余力で、新規取引の先行支出をカバー可能です。")

        # 構造の可視化
        st.write("---")
        st.write("**新規取引の月間収支構造**")
        st.info(f"月間売上: {new_deal_rev}万 / 支出: {new_deal_rev * new_deal_var_rate:.0f}万\n\n累計先行支出額: {(new_deal_rev * new_deal_var_rate) * payment_lag:.0f}万円")
