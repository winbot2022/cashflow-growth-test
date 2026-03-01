import streamlit as st
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.font_manager as fm
import os

# --- ページ設定 ---
st.set_page_config(page_title="経営戦略・資金調達シミュレーター", layout="wide")

# --- フォント設定 ---
FONT_PATH = 'NotoSansJP-Regular.ttf'
if os.path.exists(FONT_PATH):
    fp = fm.FontProperties(fname=FONT_PATH)
    plt.rcParams['font.family'] = fp.get_name()
    font_prop = fp
else:
    font_prop = None

st.title("🚀 経営戦略・資金調達シミュレーター")
st.write("「新規大口取引」の先行支出を正確に反映。必要な資金額を逆算します。")

# --- サイドバー設定 ---
st.sidebar.header("📊 1. 既存事業（ベースライン）")
initial_cash = st.sidebar.number_input("現在の現預金 (万円)", value=1000, step=100)
base_revenue = st.sidebar.number_input("既存の月間総売上 (万円)", value=1500, step=100)
fixed_cost = st.sidebar.number_input("既存の月間固定費 (万円)", value=1000, step=50)
var_cost_rate = st.sidebar.slider("既存の変動費率 (%)", 0, 100, 40) / 100

st.sidebar.markdown("---")
st.sidebar.header("⚡ 2. 新規取引（成長の罠）")
new_deal_rev = st.sidebar.number_input("新規取引の月間売上 (万円)", value=700, step=100)
new_deal_var_rate = st.sidebar.slider("新規取引の変動費率 (%)", 0, 100, 40) / 100
start_month = st.sidebar.slider("取引開始月 (支出発生)", 1, 6, 3)
payment_lag = st.sidebar.slider("入金までのラグ (ヶ月)", 1, 6, 2)

st.sidebar.markdown("---")
st.sidebar.header("💰 3. 資金調達（融資計画）")
loan_amount = st.sidebar.number_input("融資実行額 (万円)", value=0, step=100)
loan_month = st.sidebar.slider("融資実行月", 1, 12, 2)
repay_years = st.sidebar.slider("返済期間 (年)", 1, 10, 5)

st.sidebar.markdown("---")
trials = st.sidebar.select_slider("シミュレーション回数", options=[100, 1000, 10000], value=1000)
execute_button = st.sidebar.button("🚀 戦略シミュレーションを実行")

if execute_button:
    months = 18
    results_with_loan = []
    results_no_loan = []
    
    monthly_repay = loan_amount / (repay_years * 12) if loan_amount > 0 else 0
    
    for _ in range(trials):
        cash_with = initial_cash
        cash_no = initial_cash
        path_with = [cash_with]
        path_no = [cash_no]
        
        loan_balance = 0
        
        for m in range(1, months + 1):
            # A. 既存事業（5%変動リスク）
            current_base_sales = np.random.normal(base_revenue, base_revenue * 0.05)
            base_profit = current_base_sales * (1 - var_cost_rate) - fixed_cost
            
            # B. 新規取引（修正ポイント：変数を正しく使用）
            new_in = new_deal_rev if m >= (start_month + payment_lag) else 0
            new_out = (new_deal_rev * new_deal_var_rate) if m >= start_month else 0
            
            # 融資なしパス
            cash_no = cash_no + base_profit + (new_in - new_out)
            path_no.append(cash_no)
            
            # C. 融資ありパス
            l_in = loan_amount if m == loan_month else 0
            l_out = monthly_repay if (m > loan_month and loan_balance > 0) else 0
            if m == loan_month: loan_balance = loan_amount
            if l_out > 0: loan_balance -= l_out
            
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
        
        ax.plot(time_axis, np.median(results_with, axis=0), color='#1f77b4', linewidth=4, label='融資後の資金推移')
        ax.axhline(0, color='black', linewidth=2)
        ax.set_xticks(time_axis)
        
        ax.set_title("戦略的資金調達シミュレーション", fontproperties=font_prop, fontsize=16)
        ax.set_ylabel("現預金残高 (万円)", fontproperties=font_prop)
        ax.legend(prop=font_prop)
        st.pyplot(fig)

    # --- 評価指標の計算部分を以下に修正 ---

if execute_button:
    # ...（シミュレーション実行部分は同じ）

    with col2:
        # 【修正ポイント】中央値ではなく「全試行の最小値」から需要を算出
        # 1. 本来の最大資金需要（全1000回の中で、最も深く沈んだ瞬間の凹み幅）
        min_path_no_loan = np.min(results_no, axis=1) # 各試行の最低点を抽出
        absolute_worst_no_loan = np.min(min_path_no_loan) # その中の世界最悪の1点を特定
        
        # 初期キャッシュからどれだけ持ち出したか（需要）
        true_max_demand = initial_cash - absolute_worst_no_loan if absolute_worst_no_loan < initial_cash else 0
        
        # 2. 融資後の結果
        short_rate = (np.sum(is_short) / trials) * 100
        # 融資ありの中での最悪点
        min_path_with_loan = np.min(results_with, axis=1)
        absolute_worst_with_loan = np.min(min_path_with_loan)

        st.metric("真の最大資金需要 (Worst Case)", f"{true_max_demand:.0f} 万円")
        st.caption(f"※{trials}回の試行中、最も運が悪かったシナリオでの必要額です。")
        
        st.write("---")
        
        # 融資後の「最悪のシナリオでの残高」を表示
        st.metric("最悪時の残高 (Worst Case Net)", f"{absolute_worst_with_loan:.0f} 万円", delta=f"{loan_amount}万 調達後")
        st.metric("最終的な資金ショート確率", f"{short_rate:.2f} %")

        st.write("---")
        if absolute_worst_with_loan < 0:
            st.error(f"【結論】最悪の事態（不運の重なり）を想定すると、あと {abs(absolute_worst_with_loan):.0f} 万円の資金が不足します。")
        else:
            st.success("【結論】1000回のシミュレーション上、すべての不運が重なっても耐えきれる計画です。")
