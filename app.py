import streamlit as st
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.font_manager as fm
import os

np.random.seed(42)

# --- ページ設定 ---
st.set_page_config(page_title="戦略的資金繰りシミュレーター", layout="wide")

# --- フォント設定 ---
FONT_PATH = 'NotoSansJP-Regular.ttf'
if os.path.exists(FONT_PATH):
    fp = fm.FontProperties(fname=FONT_PATH)
    plt.rcParams['font.family'] = fp.get_name()
    font_prop = fp
else:
    font_prop = None

st.title("🛡️ 経営戦略・資金調達シミュレーター")
st.write("「最悪の事態」を想定した資金需要を算出し、倒産リスクをゼロにするためのロードマップを可視化します。")

# --- サイドバー設定 ---
st.sidebar.header("📊 1. 既存事業（ベースライン）")
initial_cash = st.sidebar.number_input("現在の現預金 (万円)", value=1000, step=100)

# ★変更①：最小・最大売上入力
min_revenue = st.sidebar.number_input("最小月間売上 (万円)", value=1200, step=100)
max_revenue = st.sidebar.number_input("最大月間売上 (万円)", value=1800, step=100)

fixed_cost = st.sidebar.number_input("既存の月間固定費 (万円)", value=1000, step=50)
var_cost_rate = st.sidebar.slider("既存の変動費率 (%)", 0, 100, 40) / 100

# ★変更②：平均・標準偏差の計算
mean_revenue = (min_revenue + max_revenue) / 2
std_revenue = (max_revenue - min_revenue) / 6 if max_revenue > min_revenue else 1e-6

st.sidebar.markdown("---")
st.sidebar.header("⚡ 2. 新規取引（成長の罠）")
new_deal_rev = st.sidebar.number_input("新規取引の月間売上 (万円)", value=700, step=100)
new_deal_var_rate = st.sidebar.slider("新規取引の変動費率 (%)", 0, 100, 40) / 100
start_month = st.sidebar.slider("プロジェクト開始月 (支出発生)", 1, 6, 3)
payment_lag = st.sidebar.slider("入金までのラグ (ヶ月)", 1, 6, 2)

st.sidebar.markdown("---")
st.sidebar.header("💰 3. 資金調達（融資計画）")
loan_amount = st.sidebar.number_input("融資実行額 (万円)", value=0, step=100)
loan_month = st.sidebar.slider("融資実行月", 1, 12, 2)
repay_years = st.sidebar.slider("返済期間 (年)", 1, 10, 5)
interest_rate = st.sidebar.slider("年利 (%)", 0.0, 5.0, 2.0, step=0.1) / 100

st.sidebar.markdown("---")
trials = st.sidebar.select_slider("シミュレーション回数", options=[100, 1000, 10000], value=1000)
execute_button = st.sidebar.button("🚀 戦略シミュレーションを実行")

if execute_button:
    months = 8
    results_with_loan = []
    results_no_loan = []
    
    monthly_repay_principal = loan_amount / (repay_years * 12) if loan_amount > 0 else 0
    
    for _ in range(trials):
        cash_with = initial_cash
        cash_no = initial_cash
        path_with = [cash_with]
        path_no = [cash_no]
        
        loan_balance = 0
        
        for m in range(1, months + 1):
            # ★変更③：売上生成（レンジベース＋クリップ）
            current_base_sales = np.random.normal(mean_revenue, std_revenue)
            current_base_sales = np.clip(current_base_sales, min_revenue, max_revenue)

            base_profit = current_base_sales * (1 - var_cost_rate) - fixed_cost
            
            # 新規取引
            new_in = new_deal_rev if m >= (start_month + payment_lag) else 0
            new_out = (new_deal_rev * new_deal_var_rate) if m >= start_month else 0
            
            # 融資なし
            cash_no = cash_no + base_profit + (new_in - new_out)
            path_no.append(cash_no)
            
            # 融資あり
            l_in = loan_amount if m == loan_month else 0
            l_out = 0
            if m == loan_month:
                loan_balance = loan_amount
            
            if m > loan_month and loan_balance > 0:
                interest_payment = (loan_balance * interest_rate) / 12
                l_out = monthly_repay_principal + interest_payment
                loan_balance -= monthly_repay_principal
            
            cash_with = cash_with + base_profit + (new_in - new_out) + (l_in - l_out)
            path_with.append(cash_with)

        results_with_loan.append(path_with)
        results_no_loan.append(path_no)

    results_with = np.array(results_with_loan)
    results_no = np.array(results_no_loan)
    time_axis = np.arange(months + 1)

    # --- 描画 ---
    col1, col2 = st.columns([2, 1])
    
    with col1:
        fig, ax = plt.subplots(figsize=(10, 6))
        is_short = np.any(results_with < 0, axis=1)
        
        ax.plot(time_axis, results_with[~is_short].T, color='gray', alpha=0.02)
        if np.any(is_short):
            ax.plot(time_axis, results_with[is_short].T, color='#d62728', alpha=0.04)
        
        ax.plot(time_axis, np.median(results_with, axis=0), color='#1f77b4', linewidth=4)
        ax.axhline(0, color='black', linewidth=2.5)
        ax.set_xticks(time_axis)

        ax.axvline(start_month, color='green', linestyle='--', alpha=0.6)
        ax.axvline(start_month + payment_lag, color='orange', linestyle='--', alpha=0.6)
        if loan_amount > 0:
            ax.axvline(loan_month, color='gold', linewidth=3, alpha=0.5)

        ax.set_title("戦略的資金調達シミュレーション", fontproperties=font_prop)
        ax.set_xlabel("月数", fontproperties=font_prop)
        ax.set_ylabel("現預金残高 (万円)", fontproperties=font_prop)
        st.pyplot(fig)

    with col2:
        absolute_worst_no_loan = np.min(results_no)
        true_max_demand = initial_cash - absolute_worst_no_loan if absolute_worst_no_loan < initial_cash else 0
        
        short_rate = (np.sum(is_short) / trials) * 100
        absolute_worst_with_loan = np.min(results_with)

        st.metric("真の最大資金需要", f"{true_max_demand:.0f} 万円")
        st.metric("最悪時残高", f"{absolute_worst_with_loan:.0f} 万円")
        st.metric("資金ショート確率", f"{short_rate:.2f} %")

        if absolute_worst_with_loan < 0:
            st.error(f"{abs(absolute_worst_with_loan):.0f}万円不足")
        elif absolute_worst_with_loan < 300:
            st.warning(f"余力 {absolute_worst_with_loan:.0f}万円")
        else:
            st.success("安全圏です")
