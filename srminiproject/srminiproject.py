import time
import json
import os
import requests
import urllib.parse

GOOGLE_CLIENT_ID = st.secrets["GOOGLE_CLIENT_ID"]
GOOGLE_CLIENT_SECRET = st.secrets["GOOGLE_CLIENT_SECRET"]
REDIRECT_URI = "https://smartjobandusefullkeys.streamlit.app/"
# -------------------------------
# 0-1. 브라우저 탭 설정 (제목 및 아이콘)
# 0. 브라우저 탭 설정 (제목 및 아이콘)
# -------------------------------
ICON_FILE = "app_icon.png" if os.path.exists("app_icon.png") else "💡"

user_data = load_data()


# -------------------------------
# 세션 상태 초기화 & 소셜 로그인 콜백 처리
# 세션 상태 초기화 & 자동 로그인
# -------------------------------
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False

if "my_notes" not in st.session_state:
    st.session_state.my_notes = []

# 1) 구글 로그인 리다이렉트 콜백 처리 (state 파라미터가 없을 때만 구글로 판별)
if "code" in st.query_params and "state" not in st.query_params and not st.session_state.logged_in:
    code = st.query_params["code"]
    token_url = "https://oauth2.googleapis.com/token"
    payload = {
        "code": code,
        "client_id": GOOGLE_CLIENT_ID,
        "client_secret": GOOGLE_CLIENT_SECRET,
        "redirect_uri": REDIRECT_URI,
        "grant_type": "authorization_code"
    }
    try:
        token_res = requests.post(token_url, data=payload)
        token_json = token_res.json()
        access_token = token_json.get("access_token")
        
        if access_token:
            user_info_res = requests.get(
                "https://www.googleapis.com/oauth2/v3/userinfo",
                headers={"Authorization": f"Bearer {access_token}"}
            )
            user_info = user_info_res.json()
            email = user_info.get("email")
            
            if email:
                if email not in user_data:
                    user_data[email] = {"password": "", "job": None, "notes": []}
                user_data["__auto_login__"] = email
                save_data(user_data)
                
                st.session_state.logged_in = True
                st.session_state.user_id = email
                st.session_state.yourjob = user_data[email].get("job", None)
                st.session_state.my_notes = user_data[email].get("notes", [])
                
                st.query_params.clear()
                st.rerun()
    except Exception as e:
        st.error(f"구글 로그인 인증 중 오류가 발생했습니다: {e}")

# 이전에 자동 로그인을 켜둔 계정이 있으면 자동 로그인 복원
if not st.session_state.logged_in and user_data.get("__auto_login__"):
    saved_user = user_data["__auto_login__"]
    st.session_state.user_id = saved_user
    st.session_state.yourjob = user_data[saved_user].get("job", None)
    st.session_state.my_notes = user_data[saved_user].get("notes", [])


# -------------------------------
# 단축키 데이터 (Windows 키, Mac 키, 기능 설명)
# -------------------------------
def get_ai_shortcut_recommendation(query, os_type):
    def k(win, mac):
        return mac if is_mac else win

    q = query.lower()

    # 1. 복사, 붙여넣기, 잘라내기
    if any(w in q for w in [
        "ctrl c", "ctrl+c", "ctrl v", "ctrl+v", "ctrl x", "ctrl+x", "cmd c", "cmd+c", "cmd v", "cmd+v", "cmd x", "cmd+x",
        "복사", "붙여넣기", "복붙", "복사 붙여넣기", "잘라내기", "카피", "복사하기", "붙여넣는", "텍스트 복사",
        "서식 없이 붙여넣기", "서식없이", "컨트롤 c", "컨트롤 v", "커맨드 c", "커맨드 v", "복사 단축키"
    ]):
        return {
            "message": "복사와 붙여넣기 단축키를 찾으셨군요! 가장 기본이 되는 단축키와 함께, **한술 더 떠서** 원본을 지우는 '잘라내기'와 서식 없이 텍스트만 붙여넣는 꿀단축키도 함께 챙겨드립니다.",
            "shortcuts": [
                {"key": k("Ctrl + C", "Cmd + C"), "desc": "선택 항목 복사"},
                {"key": k("Ctrl + V", "Cmd + V"), "desc": "복사한 항목 붙여넣기"},
                {"key": k("Ctrl + X", "Cmd + X"), "desc": "잘라내기 (옮기면서 원본 삭제)"},
                {"key": k("Ctrl + Shift + V", "Cmd + Shift + Option + V"), "desc": "서식 없이 깔끔하게 텍스트만 붙여넣기"},
                {"key": k("Ctrl + X", "Cmd + X"), "desc": "💡 한술 더 떠서: 잘라내기 (옮기면서 원본 삭제)"},
                {"key": k("Ctrl + Shift + V", "Cmd + Shift + Option + V"), "desc": "💡 한술 더 떠서: 서식 없이 깔끔하게 텍스트만 붙여넣기"}
            ]
        }

    # 2. 창 전환, 화면 전환, 작업창
    elif any(w in q for w in [
        "alt tab", "alt+tab", "cmd tab", "cmd+tab", "win d", "win+d", "창 전환", "작업창 전환",
        "화면 전환", "창 바꾸기", "화면 바꾸기", "창 넘기기", "작업창", "앱 전환", "프로그램 전환",
        "바탕화면 보기", "바탕화면 바로가기", "알트탭", "알트 탭", "커맨드 탭", "멀티태스킹", "다른 창으로", "화면 넘기기", "창 변경"
    ]):
        return {
            "message": "여러 프로그램을 넘나들며 작업할 때 속도를 3배 빠르게 해주는 창 전환 단축키입니다!",
            "shortcuts": [
                {"key": k("Alt + Tab", "Cmd + Tab"), "desc": "실행 중인 작업 창 빠르게 전환"},
                {"key": k("Win + D", "F11"), "desc": "모든 창 최소화하고 바탕화면 즉시 보기"},
                {"key": k("Win + D", "F11"), "desc": "💡 한술 더 떠서: 모든 창 최소화하고 바탕화면 즉시 보기"}
            ]
        }

    # 3. 실수로 닫은 탭 / 창 복구
    elif any(w in q for w in [
        "ctrl shift t", "ctrl+shift+t", "cmd shift t", "cmd+shift+t", "ctrl w", "ctrl+w", "ctrl t", "ctrl+t",
        "닫은 창", "닫힌 창", "닫은 탭", "닫힌 탭", "창 다시 열기", "탭 다시 열기", "창 다시", "탭 다시"
    ]):
        return {
            "message": "인터넷이나 문서 작업 중 실수로 닫은 탭을 되살리는 유용한 단축키입니다!",
            "shortcuts": [
                {"key": k("Ctrl + Shift + T", "Cmd + Shift + T"), "desc": "방금 닫은 인터넷 탭 즉시 다시 열기 (실수 복구)"},
                {"key": k("Ctrl + W", "Cmd + W"), "desc": "현재 보고 있는 탭 닫기"},
                {"key": k("Ctrl + T", "Cmd + T"), "desc": "새로운 인터넷 탭 열기"},
                {"key": k("Ctrl + T", "Cmd + T"), "desc": "💡 한술 더 떠서: 새로운 인터넷 탭 열기"}
            ]
        }

    # 4. 화면 캡처 / 스크린샷
    elif any(w in q for w in [
        "win shift s", "win+shift+s", "cmd shift 4", "cmd+shift+4", "cmd shift 3", "cmd+shift+3",
        "prtscn", "print screen", "캡처", "캡쳐", "스크린샷", "스샷", "화면 캡처", "화면 캡쳐"
    ]):
        return {
            "message": "원하는 화면을 즉시 저장하고 공유할 수 있는 캡처 단축키 모음입니다!",
            "shortcuts": [
                {"key": k("Win + Shift + S", "Cmd + Shift + 4"), "desc": "원하는 영역만 마우스 드래그로 부분 캡처"},
                {"key": k("PrtScn", "Cmd + Shift + 3"), "desc": "화면 전체 캡처"},
                {"key": k("Alt + PrtScn", "Cmd + Shift + 4 후 Space"), "desc": "현재 열린 창 하나만 캡처"},
                {"key": k("Alt + PrtScn", "Cmd + Shift + 4 후 Space"), "desc": "💡 한술 더 떠서: 현재 열린 창 하나만 캡처"}
            ]
        }

    # 5. 실행 취소 / 되돌리기
    elif any(w in q for w in [
        "ctrl z", "ctrl+z", "ctrl y", "ctrl+y", "cmd z", "cmd+z", "cmd shift z", "cmd+shift+z",
        "실행 취소", "실행취소", "되돌리기", "되돌려", "되돌리고", "다시 실행", "다시실행", "실수 되돌리기"
    ]):
        return {
            "message": "실수했을 때 시간을 되돌려주는 단축키입니다! 너무 많이 되돌렸을 때 다시 앞으로 복원하는 단축키도 세트로 추천합니다.",
            "shortcuts": [
                {"key": k("Ctrl + Z", "Cmd + Z"), "desc": "실행 취소 (방금 한 실수 되돌리기)"},
                {"key": k("Ctrl + Y", "Cmd + Shift + Z"), "desc": "다시 실행 (취소한 작업 다시 복구)"},
                {"key": k("Ctrl + Y", "Cmd + Shift + Z"), "desc": "💡 한술 더 떠서: 다시 실행 (취소한 작업 다시 복구)"}
            ]
        }

    # 6. 코드 주석 / 코딩
    elif any(w in q for w in [
        "ctrl /", "ctrl+/", "ctrl slash", "cmd /", "cmd+/", "cmd slash",
        "ctrl d", "ctrl+d", "cmd d", "cmd+d", "alt 위", "alt 아래", "option 위", "option 아래"
    ]):
        return {
            "message": "코딩 작업 속도를 대폭 높여주는 핵심 편집 단축키입니다!",
            "shortcuts": [
                {"key": k("Ctrl + /", "Cmd + /"), "desc": "코드 한 줄 주석 토글 (지정 / 해제)"},
                {"key": k("Ctrl + D", "Cmd + D"), "desc": "같은 단어 연속 다중 선택 (동시 수정)"},
                {"key": k("Alt + 위/아래", "Option + 위/아래"), "desc": "현재 코드 줄 위/아래로 이동"},
                {"key": k("Alt + 위/아래", "Option + 위/아래"), "desc": "💡 한술 더 떠서: 현재 코드 줄 위/아래로 이동"}
            ]
        }

    # 7. 검색 / 찾기 / 바꾸기
    elif any(w in q for w in [
        "ctrl f", "ctrl+f", "ctrl h", "ctrl+h", "cmd f", "cmd+f", "cmd option f", "cmd+option+f",
        "검색", "단어 찾기", "글자 찾기", "찾기", "바꾸기", "단어 바꾸기", "문서 검색", "코드 검색"
    ]):
        return {
            "message": "문서나 웹페이지에서 단어를 빠르게 찾거나 바꿀 때 쓰는 단축키입니다!",
            "shortcuts": [
                {"key": k("Ctrl + F", "Cmd + F"), "desc": "문서 및 웹페이지 내 키워드 검색"},
                {"key": k("Ctrl + H", "Cmd + Option + F"), "desc": "찾기 및 다른 단어로 일괄 바꾸기"},
                {"key": k("Ctrl + H", "Cmd + Option + F"), "desc": "💡 한술 더 떠서: 찾기 및 다른 단어로 일괄 바꾸기"}
            ]
        }

    # 8. 멈춤 / 렉 / 강제 종료 / 화면 잠금
    elif any(w in q for w in [
        "ctrl shift esc", "ctrl+shift+esc", "alt f4", "alt+f4", "win l", "win+l", "cmd option esc",
        "cmd ctrl q", "작업 관리자", "작업관리자", "강제 종료", "강제종료", "프로그램 강제", "컴퓨터 멈춤"
    ]):
        return {
            "message": "컴퓨터가 멈췄거나 보안이 필요할 때 유용한 긴급 단축키입니다!",
            "shortcuts": [
                {"key": k("Ctrl + Shift + Esc", "Cmd + Option + Esc"), "desc": "작업 관리자 / 강제 종료 창 열기"},
                {"key": k("Alt + F4", "Cmd + Q"), "desc": "현재 프로그램 강제 종료"},
                {"key": k("Win + L", "Cmd + Ctrl + Q"), "desc": "컴퓨터 화면 즉시 잠금 (보안 필수)"},
                {"key": k("Win + L", "Cmd + Ctrl + Q"), "desc": "💡 한술 더 떠서: 컴퓨터 화면 즉시 잠금 (보안 필수)"}
            ]
        }
    else:
        return None

            # 구글 계정으로 로그인 (실제 OAuth 연동)
            # 1초 간편 소셜 로그인 (구글)
            st.write("---")
            st.caption(" G 구글 계정 간편 로그인")
            google_auth_url = (
                f"https://accounts.google.com/o/oauth2/v2/auth?response_type=code"
                f"&client_id={GOOGLE_CLIENT_ID}&redirect_uri={REDIRECT_URI}"
                f"&scope=openid%20email%20profile"
            )
            st.link_button("구글 계정으로 로그인 ↗", google_auth_url, use_container_width=True)
            st.caption("🚀 1초 간편 소셜 로그인")
            cg, cn, ck = st.columns(3)
            if cg.button("구글", key="btn_google", use_container_width=True):
                sid = "Google_사용자"
                if sid not in user_data:
                    user_data[sid] = {"password": "", "job": None, "notes": []}
                user_data["__auto_login__"] = sid
                save_data(user_data)
                st.session_state.logged_in = True
                st.session_state.user_id = sid
                st.session_state.yourjob = user_data[sid].get("job", None)
                st.session_state.my_notes = user_data[sid].get("notes", [])
                st.rerun()
    st.write("---")

    # 2. OS 선택
    os_type = st.radio("💻 OS 선택", ["Windows 💻", "Mac 🍎"], horizontal=True)

    if st.session_state.yourjob:
        st.info(f"선택 직업: **{st.session_state.yourjob}**")
    else:
        st.info("직업을 먼저 선택해주세요!")
        st.caption("직업을 먼저 선택해주세요!")


# -------------------------------

                    continue

            matched_count += 1
            # 키보드 키 느낌을 주는 백틱 서식 적용
            st.write(f"- **`{key_to_display}`** — {desc}")

        if matched_count == 0:
            st.info("검색 조건과 일치하는 단축키가 없습니다.")


# -------------------------------
# 3. 유용한 사이트
# 3. 유용한 사이트 (간결한 반복문으로 압축)
# -------------------------------
elif menu == "유용한 사이트":
    st.title("🌐 유용한 사이트")



# -------------------------------
# 4. 나만의 단축키 메모
# 4. 나만의 단축키 메모 (AI 비서 & 자동 초기화 폼)
# -------------------------------
elif menu == "나만의 단축키 메모":
    st.title("📝 나만의 단축키 메모")


    tab_ai, tab_manual = st.tabs(["🤖 AI 단축키 추천 비서", "✏️ 직접 입력 등록"])

    # TAB 1: AI 비서
    with tab_ai:
        st.subheader("💬 AI에게 단축키 물어보기")
        st.write("자연어로 편하게 물어보세요! 연관된 단축키까지 함께 추천해 드립니다.")
        st.write("자연어로 편하게 물어보세요! 연관된 **한술 더 뜬 단축키**까지 함께 추천해 드립니다.")

        st.caption("💡 빠른 질문 버튼을 눌러보세요:")
        c1, c2, c3, c4 = st.columns(4)

                    if col_btn.button("➕ 내 메모에 추가", key=f"ai_add_{i}"):
                        st.session_state.my_notes.append({
                            "key": item["key"],
                            "desc": item["desc"]
                            "desc": item["desc"].replace("💡 한술 더 떠서: ", "")
                        })
                        if st.session_state.logged_in:
                            user_data[st.session_state.user_id]["notes"] = st.session_state.my_notes

                        time.sleep(0.5)
                        st.rerun()

    # TAB 2: 직접 등록 (입력 후 자동 비워지는 st.form 사용)
    with tab_manual:
        st.subheader("✏️ 직접 단축키 등록")
        with st.form("manual_note_form", clear_on_submit=True):

                else:
                    st.warning("단축키와 설명을 모두 입력해주세요.")

    # 등록된 메모 목록
    st.write("---")
    st.subheader("📋 내가 등록한 단축키 목록")




# -------------------------------
# 5. 치트시트 다운로드
# 5. 치트시트 다운로드 (간결한 반복문 생성)
# -------------------------------
elif menu == "치트시트 다운로드":
    st.title("📥 치트시트 다운로드")

        current_job = st.session_state.yourjob
        st.write(f"선택된 직업인 **'{current_job}'**의 맞춤 단축키({os_type})와 추천 사이트, 나만의 메모를 텍스트 파일로 다운로드합니다.")

        # 요약 텍스트 간결하게 생성
        cheatsheet_text = f"=== [{current_job}] 맞춤 치트시트 ({os_type}) ===\n\n"
        cheatsheet_text += f"■ {current_job} 추천 단축키\n"
