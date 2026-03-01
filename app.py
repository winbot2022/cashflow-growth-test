import streamlit as st
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.font_manager as fm
import os

# --- ページ設定 ---
st.set_page_config(page_title="資金繰り・融資シミュレーター", layout="wide")

# --- フォント設定 ---
FONT_PATH = 'NotoSansJP-Regular.ttf'
if os.path.exists(FONT_PATH):
    fp = fm.FontProperties(fname=FONT_PATH)
    plt.rcParams['font.family'] = fp.get_name()
    font_prop = fp
else:
    font_prop = None

st.title("🚀 資金繰り・成長リスク ＆ 融資シミュレーター")
st.write("「死の谷」を埋めるための融資額とタイミングをシミュレートし、最適な資金調達計画を策定します。")

# --- サイドバー：1. 既存事業（定常状態） ---
st.sidebar.header("📊 1. 既存事業の状況")
initial_cash = st.sidebar.number_input("現在の現預金 (万円)", value=1000, step=100)
base_revenue = st.sidebar.number_input("既存の月間総売上 (万円)", value=1500, step=100)
fixed_cost = st.sidebar.number_input("既存の月間固定費 (万円)", value=1000, step=50)
var_cost_rate = st.sidebar.slider("既存の変動費率 (%)", 0, 100, 40) / 100

# --- サイドバー：2. 新規取引（非定常状態） ---
st.sidebar.markdown("---")
st.sidebar.header("⚡ 2. 新規大口取引の衝撃")
new_deal_rev = st.sidebar.number_input("新規取引の月間売上 (万円)", value=700, step=100)
new_deal_var_rate = st.sidebar.slider("新規取引の変動費率 (%)", 0, 100, 40) / 100
start_month = st.sidebar.slider("プロジェクト開始月 (支出発生)", 1, 6, 3)
payment_lag = st.sidebar.slider("入金までのラグ (ヶ月)", 1, 6, 2)

# --- サイドバー：3. 融資実行シミュレーション ---
st.sidebar.markdown("---")
st.sidebar.header("💰 3. 融資実行シミュレーション")
loan_amount = st.sidebar.number_input("融資額 (万円)", value=0, step=500)
loan_month = st.sidebar.slider("融資実行月", 1, 12, 2)
repay_years = st.sidebar.slider("返済期間 (年)", 1, 10, 5)
interest_rate = st.sidebar.slider("年利 (%)", 0.0, 5.0, 2.0, step=0.1) / 100

st.sidebar.markdown("---")
trials = st.sidebar.select_slider("シミュレーション回数", options=[100, 1000, 10000], value=1000)
execute_button = st.sidebar.button("🚀 戦略的資金シミュレーションを実行")

if execute_button:
    months = 18
    results = []
    
    # 毎月の返済額（元金均等）
    monthly_repay_principal = loan_amount / (repay_years * 12) if loan_amount > 0 else 0
    
    for _ in range(trials):
        cash = initial_cash
        cash_flow = [cash]
        loan_balance = 0
        
        for m in range(1, months + 1):
            # A. 既存事業（5%変動リスク）
            current_base_sales = np.random.normal(base_revenue, base_revenue * 0.05)
            base_profit = current_base_sales * (1 - var_cost_rate) - fixed_cost
            
            # B. 新規取引
            new_inflow = 0
            new_outflow = 0
            if m >= start_month:
                new_outflow = new_deal_rev * new_deal_var_rate
                if m >= (start_month + payment_lag):
                    new_inflow = new_deal_rev
            
            # C. 融資の実行と返済
            loan_inflow = 0
            loan_outflow = 0
            
            # 融資実行
            if m == loan_month:
                loan_inflow = loan_amount
                loan_balance = loan_amount
            
            # 返済（実行の翌月から開始）
            if m > loan_month and loan_balance > 0:
                interest_payment = (loan_balance * interest_rate) / 12
                loan_outflow = monthly_repay_principal + interest_payment
                loan_balance -= monthly_repay_principal
            
            # D. キャッシュ更新
            cash = cash + base_profit + (new_inflow - new_outflow) + (loan_inflow - loan_outflow)
            cash_flow.append(cash)

        results.append(cash_flow)

    results = np.array(results)

    # --- 描画エリア ---
    col1, col2 = st.columns([2, 1])
    
    with col1:
        fig, ax = plt.subplots(figsize=(10, 6))
        is_short = np.any(results < 0, axis=1)
        time_axis = np.arange(months + 1)
        
        # 線グラフ
        ax.plot(time_axis, results[~is_short].T, color='gray', alpha=0.02)
        if np.any(is_short):
            ax.plot(time_axis, results[is_short].T, color='#d62728', alpha=0.04, linewidth=0.8)
        
        ax.plot(time_axis, np.median(results, axis=0), color='#1f77b4', linewidth=4, label='融資後シナリオ（中央値）')
        ax.axhline(0, color='black', linewidth=2.5)
        ax.set_xticks(time_axis)
        
        # 補助線
        ax.axvline(start_month, color='green', linestyle='--', alpha=0.5, label='新規取引開始')
        if loan_amount > 0:
            ax.axvline(loan_month, color='gold', linestyle='-', linewidth=3, alpha=0.6, label='★融資実行')
        
        ax.set_title("融資実行による『死の谷』の回避シミュレーション", fontproperties=font_prop, fontsize=16)
        ax.set_xlabel("月数 (Month)", fontproperties=font_prop)
        ax.set_ylabel("現預金残高 (万円)", fontproperties=font_prop)
        ax.legend(prop=font_prop, loc='upper left')
        st.pyplot(fig)

    with col2:
        short_rate = (np.sum(is_short) / trials) * 100
        st.metric("資金ショート確率（融資考慮後）", f"{short_rate:.2f} %")
        
        median_path = np.median(results, axis=0)
        min_cash = np.min(median_path)
        
        st.subheader("📝 資金調達アドバイス")
        if loan_amount == 0:
            st.info("左メニューから『融資額』を入力して、リスクがどう変化するか確認してください。")
        elif short_rate > 0:
            st.error(f"融資 {loan_amount}万円 を受けても、依然として {short_rate:.1f}% の確率でショートします。融資額を増やすか、実行月を早める必要があります。")
        else:
            st.success(f"おめでとうございます。{loan_amount}万円 の融資により、成長に伴うリスクを完全にカバーできました。")

        # 返済シミュレーション表示
        if loan_amount > 0:
            st.write("---")
            st.write("**返済計画メモ**")
            st.write(f"- 毎月の元金返済: {monthly_repay_principal:.1f}万円")
            st.write(f"- 初回利息目安: {(loan_amount * interest_rate / 12):.2f}万円")
            st.caption(f"※{repay_years}年（{repay_years*12}回）払い / 年利{interest_rate*100:.1f}%")

        # インパクト分析
        worst_drop = initial_cash - np.min(results) if np.min(results) < initial_cash else 0
        st.write("---")
        st.write(f"**最大資金需要（ワーストケース）**")
        st.write(f"約 **{worst_drop:.0f}万円**")
        st.caption("既存顧客の遅延と新規取引の先行支出が重なった場合の最大凹み額です。")
