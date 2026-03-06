import streamlit as st
import secrets
import pandas as pd
from supabase import create_client, Client
import plotly.express as px

# --- Supabase 설정 (st.secrets 사용) ---
# GitHub에 키가 노출되지 않도록 Streamlit secrets에서 값을 가져옵니다.
SUPABASE_URL = st.secrets["SUPABASE_URL"]
SUPABASE_KEY = st.secrets["SUPABASE_KEY"]
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# --- 스타일 설정 (CSS 추가) ---
st.markdown("""
    <style>
    .door-box {
        border: 2px solid #555;
        border-radius: 10px;
        padding: 20px;
        text-align: center;
        background-color: #f0f2f6;
        transition: 0.3s;
    }
    .selected-door {
        border: 4px solid #FF4B4B !important;
        background-color: #ffe8e8 !important;
    }
    .opened-door {
        background-color: #333 !important;
        color: white !important;
        border: 2px dashed #999;
    }
    /* 선택을 변경했을 때 이전 선택을 옅게 표시하는 스타일 */
    .prev-door {
        border: 2px dashed #ff9999 !important;
        background-color: #fff0f0 !important;
        opacity: 0.5; 
    }
    /* 결과 공개 시 당첨 문 스타일 */
    .winner-door {
        border: 4px solid #00CC66 !important;
        background-color: #e6ffec !important;
    }
    </style>
    """, unsafe_allow_html=True)

# --- 데이터 처리 함수 ---
def save_to_supabase(data):
    supabase.table("monty_hall_results").insert(data).execute()

def fetch_statistics():
    response = supabase.table("monty_hall_results").select("*").execute()
    return pd.DataFrame(response.data)

# --- 세션 상태 초기화 ---
if 'step' not in st.session_state:
    st.session_state.step = 'menu'
if 'game_data' not in st.session_state:
    st.session_state.game_data = {}

# --- 메인 로직 ---
st.title("🚪 몬티홀 챌린지: 당신의 선택은?")

# 1. 메뉴 선택
if st.session_state.step == 'menu':
    st.subheader("원하시는 메뉴를 선택하세요")
    col1, col2 = st.columns(2)
    if col1.button("🧠 추론 게임 시작", use_container_width=True):
        st.session_state.step = 'login'
        st.rerun()
    if col2.button("📊 데이터 통계 보기", use_container_width=True):
        st.session_state.step = 'stats'
        st.rerun()

# 2. 추론 페이지
elif st.session_state.step in ['login', 'first_choice', 'switch_decision', 'result']:
    if st.button("⬅ 메인 메뉴로"):
        st.session_state.step = 'menu'
        st.rerun()

    if st.session_state.step == 'login':
        user_name = st.text_input("사용자 명을 입력하세요.")
        if st.button("다음"):
            if user_name:
                st.session_state.user_name = user_name
                st.session_state.game_data = {
                    "winning_door": secrets.choice([0, 1, 2]),
                    "doors": [0, 1, 2]
                }
                st.session_state.step = 'first_choice'
                st.rerun()

    else:
        st.write(f"### {st.session_state.user_name}님의 게임 진행 중")
        cols = st.columns(3)
        
        # 문 3개 렌더링
        for i in range(3):
            with cols[i]:
                # --- [결과 화면] 일 때의 렌더링 ---
                if st.session_state.step == 'result':
                    win_door = st.session_state.game_data['winning_door']
                    initial = st.session_state.game_data['initial_choice']
                    final = st.session_state.game_data['final_choice']
                    switched = st.session_state.game_data['switched']
                    
                    is_winner_door = (i == win_door)
                    is_final_choice = (i == final)
                    is_prev_choice = (switched and i == initial)
                    
                    # 문 내용 공개
                    content = "🚗<br>당첨 (자동차)" if is_winner_door else "📦<br>빈 박스 (꽝)"
                    
                    # CSS 클래스 적용
                    css_class = "door-box "
                    if is_final_choice and is_winner_door:
                        css_class += "winner-door"
                    elif is_final_choice:
                        css_class += "selected-door"
                    elif is_prev_choice:
                        css_class += "prev-door"
                        
                    st.markdown(f'<div class="{css_class}">{content}</div>', unsafe_allow_html=True)
                    
                    # 하단 라벨 추가
                    if is_final_choice:
                        st.caption("🎯 최종 선택")
                    elif is_prev_choice:
                        st.caption("⏪ 이전 선택")

                # --- [선택 진행 중] 일 때의 렌더링 ---
                else:
                    is_selected = (st.session_state.game_data.get('initial_choice') == i)
                    is_opened = (st.session_state.game_data.get('opened_door') == i)
                    
                    if is_opened:
                        st.markdown(f'<div class="door-box opened-door">📦<br>빈 박스(꽝)</div>', unsafe_allow_html=True)
                        st.button("공개됨", key=f"btn_{i}", disabled=True, use_container_width=True)
                    else:
                        highlight = "selected-door" if is_selected else ""
                        st.markdown(f'<div class="door-box {highlight}">🚪<br>{i+1}번 문</div>', unsafe_allow_html=True)
                        
                        # 버튼 로직
                        if st.session_state.step == 'first_choice':
                            if st.button(f"{i+1}번 선택", key=f"sel_{i}", use_container_width=True):
                                st.session_state.game_data['initial_choice'] = i
                                rem_goats = [d for d in [0,1,2] if d != i and d != st.session_state.game_data['winning_door']]
                                st.session_state.game_data['opened_door'] = secrets.choice(rem_goats) # secrets 모듈 적용
                                st.session_state.step = 'switch_decision'
                                st.rerun()
                        
                        elif st.session_state.step == 'switch_decision':
                            if st.button(f"{i+1}번으로 확정", key=f"re_{i}", use_container_width=True):
                                st.session_state.game_data['final_choice'] = i
                                st.session_state.game_data['switched'] = (i != st.session_state.game_data['initial_choice'])
                                st.session_state.step = 'result'
                                st.rerun()

        # 결과 텍스트 및 DB 저장 로직
        if st.session_state.step == 'switch_decision':
            st.warning("사회자가 꽝 문을 비웠습니다. 기존 선택을 유지하거나 남은 문으로 변경하세요!")

        elif st.session_state.step == 'result':
            win_door = st.session_state.game_data['winning_door']
            final = st.session_state.game_data['final_choice']
            is_winner = (win_door == final)
            
            st.write("---")
            if is_winner:
                st.success("당첨입니다! 축하합니다.") # 화려한 효과 제거, 심플한 텍스트
            else:
                st.error("꽝입니다. 아쉽네요!")
            
            # DB 중복 저장 방지
            if 'saved' not in st.session_state:
                save_data = {
                    "user_name": st.session_state.user_name,
                    "winning_door": win_door,
                    "initial_choice": st.session_state.game_data['initial_choice'],
                    "opened_door": st.session_state.game_data['opened_door'],
                    "switched": st.session_state.game_data['switched'],
                    "is_winner": is_winner
                }
                save_to_supabase(save_data)
                st.session_state.saved = True
            
            if st.button("다시 하기"):
                # 게임 데이터 초기화
                del st.session_state.saved
                st.session_state.step = 'login'
                st.rerun()

# 3. 통계 페이지
elif st.session_state.step == 'stats':
    if st.button("⬅ 메인 메뉴로"):
        st.session_state.step = 'menu'
        st.rerun()
        
    df = fetch_statistics()
    if not df.empty:
        st.subheader("📊 전체 통계")
        
        total = len(df)
        switched_df = df[df['switched'] == True]
        stayed_df = df[df['switched'] == False]
        
        c1, c2, c3 = st.columns(3)
        c1.metric("총 게임 횟수", f"{total}회")
        c2.metric("변경 시 당첨 확률", f"{(switched_df['is_winner'].mean()*100):.1f}%" if not switched_df.empty else "0%")
        c3.metric("유지 시 당첨 확률", f"{(stayed_df['is_winner'].mean()*100):.1f}%" if not stayed_df.empty else "0%")
        
        st.write("---")
        st.write("#### 🚪 각 문 별 확률")
        
        door_stats = []
        for i in range(3):
            door_total = len(df[df['winning_door'] == i])
            win_prob = (door_total / total * 100) if total > 0 else 0
            loss_prob = 100 - win_prob
            door_stats.append({
                "문 번호": f"{i+1}번", 
                "당첨 확률": f"{win_prob:.1f}%", 
                "꽝 확률": f"{loss_prob:.1f}%"
            })
        
        st.write("---")
        st.write("#### 🎲 난수 공정성 검증 (정답 비율)")
        st.write("각 문에 자동차가 배치된 비율입니다. 데이터가 누적될수록 각각 33.3%에 수렴합니다.")
        
        # 1. winning_door(0, 1, 2)의 발생 횟수를 집계하여 데이터프레임으로 변환
        win_counts = df['winning_door'].value_counts().reset_index()
        win_counts.columns = ['door', 'count']
        
        # 2. 인덱스 이름을 보기 좋게 변경 (예: 0 -> 1번 문)
        win_counts['door'] = win_counts['door'].apply(lambda x: f"{int(x)+1}번 문")
        
        # 3. Plotly를 사용한 도넛형 파이 차트 생성 (hole 속성으로 가운데를 뚫어줍니다)
        fig = px.pie(
            win_counts, 
            values='count', 
            names='door', 
            hole=0.4, 
            color_discrete_sequence=px.colors.qualitative.Pastel # 파스텔 톤 색상 적용
        )
        
        # 4. Streamlit에 차트 출력
        st.plotly_chart(fig, use_container_width=True)
        st.table(pd.DataFrame(door_stats))
        
        with st.expander("전체 원본 데이터 보기"):
            st.dataframe(df.sort_values(by='created_at', ascending=False))
    else:
        st.info("데이터가 아직 없습니다. 게임을 먼저 진행해 주세요!")