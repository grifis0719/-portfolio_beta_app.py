#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Portfolio Beta Calculator & Risk Dashboard
포트폴리오 베타 계산기 & 리스크 대시보드

Author: Portfolio Risk Team
License: MIT
"""

import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime

# 페이지 설정
st.set_page_config(
    page_title="Portfolio Beta Calculator",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 커스텀 CSS
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: 700;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        text-align: center;
        margin-bottom: 2rem;
    }
    .metric-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 1.5rem;
        border-radius: 10px;
        color: white;
        text-align: center;
    }
    .risk-low { color: #10b981; font-weight: bold; }
    .risk-medium { color: #f59e0b; font-weight: bold; }
    .risk-high { color: #ef4444; font-weight: bold; }
</style>
""", unsafe_allow_html=True)

# 알려진 베타값 데이터베이스 (레버리지 ETF 포함)
KNOWN_BETAS = {
    # 3배 레버리지 ETF (Bulls)
    'TQQQ': 2.98,   # 3x Nasdaq-100
    'UPRO': 2.95,   # 3x S&P 500
    'TECL': 2.97,   # 3x Technology
    'SOXL': 3.15,   # 3x Semiconductors
    'FAS': 2.88,    # 3x Financial
    'TNA': 2.92,    # 3x Russell 2000
    'LABU': 3.05,   # 3x Biotech
    'NUGT': 3.20,   # 3x Gold Miners
    
    # 3배 역레버리지 ETF (Bears)
    'SQQQ': -2.98,  # -3x Nasdaq-100
    'SPXU': -2.95,  # -3x S&P 500
    'TECS': -2.97,  # -3x Technology
    'SOXS': -3.15,  # -3x Semiconductors
    'FAZ': -2.88,   # -3x Financial
    'TZA': -2.92,   # -3x Russell 2000
    
    # 2배 레버리지 ETF
    'QLD': 2.00,    # 2x Nasdaq-100
    'SSO': 1.98,    # 2x S&P 500
    'UWM': 1.95,    # 2x Russell 2000
    
    # 일반 ETF
    'QQQ': 1.05,    # Nasdaq-100
    'SPY': 1.00,    # S&P 500
    'IWM': 1.15,    # Russell 2000
    'DIA': 0.95,    # Dow Jones
    'VTI': 1.00,    # Total Market
    'VOO': 1.00,    # S&P 500
    'AGG': 0.05,    # Bonds
    'TLT': -0.15,   # Long-term Treasury
    'GLD': 0.10,    # Gold
    
    # 주요 기술주
    'NVDA': 1.68,
    'TSLA': 2.29,
    'META': 1.18,
    'AAPL': 1.24,
    'MSFT': 0.89,
    'GOOGL': 1.05,
    'AMZN': 1.15,
    'NFLX': 1.35,
    'AMD': 1.82,
    'INTC': 0.78
}

# 세션 상태 초기화
if 'portfolio' not in st.session_state:
    st.session_state.portfolio = []
if 'cash_balance' not in st.session_state:
    st.session_state.cash_balance = 0.0

def get_stock_data(ticker):
    """실시간 주식 데이터 가져오기"""
    try:
        stock = yf.Ticker(ticker)
        info = stock.info
        
        # 현재가
        price = (
            info.get('currentPrice') or 
            info.get('regularMarketPrice') or 
            info.get('previousClose') or 
            0
        )
        
        # 베타값: knownBetas 우선, 없으면 API, 마지막으로 1.0
        beta = KNOWN_BETAS.get(ticker.upper(), info.get('beta', 1.0))
        
        return {
            'ticker': ticker.upper(),
            'price': price,
            'beta': beta,
            'name': info.get('shortName', ticker),
            'sector': info.get('sector', 'Unknown')
        }
    except Exception as e:
        st.error(f"❌ {ticker} 데이터를 가져올 수 없습니다: {str(e)}")
        return None

def calculate_portfolio_beta():
    """포트폴리오 가중 베타 계산"""
    if not st.session_state.portfolio:
        return 0.0
    
    total_value = sum(stock['price'] * stock['shares'] for stock in st.session_state.portfolio)
    
    if total_value == 0:
        return 0.0
    
    weighted_beta = sum(
        (stock['price'] * stock['shares'] / total_value) * stock['beta']
        for stock in st.session_state.portfolio
    )
    
    return weighted_beta

def get_risk_level(beta):
    """베타값에 따른 리스크 레벨"""
    beta_abs = abs(beta)
    if beta_abs < 0.8:
        return "Low Risk", "risk-low"
    elif beta_abs < 1.2:
        return "Neutral Risk", "risk-medium"
    elif beta_abs < 2.0:
        return "Higher Risk", "risk-medium"
    else:
        return "High Risk", "risk-high"

def create_beta_gauge(beta):
    """베타 게이지 차트 생성"""
    fig = go.Figure(go.Indicator(
        mode = "gauge+number+delta",
        value = beta,
        domain = {'x': [0, 1], 'y': [0, 1]},
        title = {'text': "Portfolio Beta", 'font': {'size': 24}},
        delta = {'reference': 1.0},
        gauge = {
            'axis': {'range': [-3, 3], 'tickwidth': 1, 'tickcolor': "darkblue"},
            'bar': {'color': "darkblue"},
            'bgcolor': "white",
            'borderwidth': 2,
            'bordercolor': "gray",
            'steps': [
                {'range': [-3, -2], 'color': '#ef4444'},
                {'range': [-2, -1], 'color': '#f59e0b'},
                {'range': [-1, 0], 'color': '#fbbf24'},
                {'range': [0, 0.8], 'color': '#10b981'},
                {'range': [0.8, 1.2], 'color': '#fbbf24'},
                {'range': [1.2, 2], 'color': '#f59e0b'},
                {'range': [2, 3], 'color': '#ef4444'}
            ],
            'threshold': {
                'line': {'color': "red", 'width': 4},
                'thickness': 0.75,
                'value': beta
            }
        }
    ))
    
    fig.update_layout(height=300, margin=dict(l=20, r=20, t=50, b=20))
    return fig

# 헤더
st.markdown('<h1 class="main-header">📊 Portfolio Beta Calculator</h1>', unsafe_allow_html=True)
st.markdown("### 포트폴리오 리스크 분석 대시보드")

# 사이드바 - 종목 추가
with st.sidebar:
    st.header("➕ 종목 추가")
    
    with st.form("add_stock_form"):
        ticker_input = st.text_input("티커 심볼", placeholder="예: TQQQ, AAPL, TSLA").upper()
        shares_input = st.number_input("주식 수", min_value=0, value=100, step=1)
        submit_button = st.form_submit_button("📈 종목 추가", use_container_width=True)
        
        if submit_button and ticker_input:
            with st.spinner(f'{ticker_input} 데이터 가져오는 중...'):
                stock_data = get_stock_data(ticker_input)
                if stock_data:
                    stock_data['shares'] = shares_input
                    st.session_state.portfolio.append(stock_data)
                    st.success(f"✅ {ticker_input} 추가 완료!")
                    st.rerun()
    
    st.divider()
    
    # 현금 잔고
    st.header("💵 현금 잔고")
    cash_input = st.number_input(
        "현금 (USD)", 
        min_value=0.0, 
        value=st.session_state.cash_balance,
        step=100.0,
        format="%.2f"
    )
    if cash_input != st.session_state.cash_balance:
        st.session_state.cash_balance = cash_input
        st.rerun()
    
    st.divider()
    
    # 포트폴리오 초기화
    if st.button("🗑️ 포트폴리오 초기화", use_container_width=True):
        st.session_state.portfolio = []
        st.session_state.cash_balance = 0.0
        st.rerun()

# 메인 영역
if st.session_state.portfolio:
    # 포트폴리오 베타 계산
    portfolio_beta = calculate_portfolio_beta()
    risk_level, risk_class = get_risk_level(portfolio_beta)
    
    # 총 자산 계산
    stock_value = sum(stock['price'] * stock['shares'] for stock in st.session_state.portfolio)
    total_assets = stock_value + st.session_state.cash_balance
    
    # 상단 메트릭
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Portfolio Beta", f"{portfolio_beta:.2f}")
    
    with col2:
        st.metric("Risk Level", risk_level)
    
    with col3:
        st.metric("주식 가치", f"${stock_value:,.2f}")
    
    with col4:
        st.metric("총 자산", f"${total_assets:,.2f}")
    
    # 베타 게이지
    st.plotly_chart(create_beta_gauge(portfolio_beta), use_container_width=True)
    
    # 포트폴리오 테이블
    st.header("📋 보유 종목")
    
    df_data = []
    for idx, stock in enumerate(st.session_state.portfolio):
        market_value = stock['price'] * stock['shares']
        weight = (market_value / stock_value * 100) if stock_value > 0 else 0
        
        df_data.append({
            '티커': stock['ticker'],
            '종목명': stock['name'],
            '주식수': stock['shares'],
            '현재가': f"${stock['price']:.2f}",
            '평가액': f"${market_value:,.2f}",
            '비중': f"{weight:.1f}%",
            '베타': f"{stock['beta']:.2f}",
            'Sector': stock['sector']
        })
    
    df = pd.DataFrame(df_data)
    st.dataframe(df, use_container_width=True, hide_index=True)
    
    # 개별 종목 삭제 버튼
    st.subheader("종목 관리")
    cols = st.columns(min(len(st.session_state.portfolio), 4))
    for idx, stock in enumerate(st.session_state.portfolio):
        with cols[idx % 4]:
            if st.button(f"❌ {stock['ticker']} 삭제", key=f"del_{idx}"):
                st.session_state.portfolio.pop(idx)
                st.rerun()

else:
    # 빈 포트폴리오 메시지
    st.info("👈 왼쪽 사이드바에서 종목을 추가하세요!")
    
    st.markdown("""
    ### 📖 사용 방법
    
    1. **종목 추가**: 사이드바에서 티커(예: TQQQ, AAPL)와 주식 수를 입력
    2. **베타 확인**: 자동으로 포트폴리오 베타가 계산됩니다
    3. **리스크 분석**: 게이지 차트로 리스크 수준 확인
    4. **자산 관리**: 현금 잔고를 입력하여 총 자산 확인
    
    ### 💡 베타(Beta)란?
    
    - **베타 = 1.0**: 시장과 동일한 변동성
    - **베타 > 1.0**: 시장보다 높은 변동성 (공격적)
    - **베타 < 1.0**: 시장보다 낮은 변동성 (보수적)
    - **베타 < 0**: 시장과 반대 방향 (헤지)
    
    ### 🚀 레버리지 ETF 예시
    
    - **TQQQ**: β 2.98 (나스닥 3배 상승)
    - **SQQQ**: β -2.98 (나스닥 3배 하락)
    - **QQQ**: β 1.05 (나스닥 추종)
    """)

# 푸터
st.divider()
st.markdown(f"""
<div style='text-align: center; color: gray;'>
    <small>Portfolio Beta Calculator v1.0 | 마지막 업데이트: {datetime.now().strftime('%Y-%m-%d %H:%M')}</small>
</div>
""", unsafe_allow_html=True)
