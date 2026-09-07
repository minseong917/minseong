import streamlit as st
import time
import json
import os
import requests

GOOGLE_CLIENT_ID = "674825074081-uom4bfj9uq03prjqmmkdcu4qla46so97.apps.googleusercontent.com"
GOOGLE_CLIENT_SECRET = "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"
REDIRECT_URI = "https://smartjobandusefullkeys.streamlit.app/"

# 네이버 OAuth 설정 추가
NAVER_CLIENT_ID = "xgUzDPclDitKJPQC1w4z"
NAVER_CLIENT_SECRET = "sZ5DrBZ7XO"

# -------------------------------
# 0-1. 브라우저 탭 설정 (제목 및 아이콘)
# -------------------------------
ICON_FILE = "app_icon.png" if os.path.exists("app_icon.png") else "💡"

st.set_page_config(
    page_title="스마트 직업 치트시트 & 단축키 도감",
    page_icon=ICON_FILE,
    layout="centered"
)


# -------------------------------
# 사용자 데이터 파일 관리 (JSON 저장소)
# -------------------------------
DATA_FILE = "user_data.json"

def load_data():
    if not os.path.exists(DATA_FILE):
        return {}
    try:
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}

def save_data(data):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

user_data = load_data()

# -------------------------------
# 세션 상태 초기화 & 소셜 로그인 콜백 처리
# -------------------------------
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
if "user_id" not in st.session_state:
    st.session_state.user_id = None
if "yourjob" not in st.session_state:
    st.session_state.yourjob = None
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
    if saved_user in user_data:
        st.session_state.logged_in = True
        st.session_state.user_id = saved_user
        st.session_state.yourjob = user_data[saved_user].get("job", None)
        st.session_state.my_notes = user_data[saved_user].get("notes", [])

# 2) 네이버 로그인 리다이렉트 콜백 처리 (state 파라미터가 포함되어 있을 때)
if "code" in st.query_params and "state" in st.query_params and not st.session_state.logged_in:
    code = st.query_params["code"]
    state = st.query_params["state"]
    
    token_url = "https://nid.naver.com/oauth2.0/token"
    payload = {
        "grant_type": "authorization_code",
        "client_id": NAVER_CLIENT_ID,
        "client_secret": NAVER_CLIENT_SECRET,
        "code": code,
        "state": state
    }
    try:
        token_res = requests.post(token_url, data=payload)
        token_json = token_res.json()
        access_token = token_json.get("access_token")
        
        if access_token:
            user_info_res = requests.get(
                "https://openapi.naver.com/v1/nid/me",
                headers={"Authorization": f"Bearer {access_token}"}
            )
            user_info = user_info_res.json()
            response_obj = user_info.get("response", {})
            email = response_obj.get("email")
            
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
        st.error(f"네이버 로그인 인증 중 오류가 발생했습니다: {e}")

# -------------------------------
# 단축키 데이터 (Windows 키, Mac 키, 기능 설명)
# -------------------------------
SHORTCUTS_DATA = {
    "학생": [
        ("Ctrl + C", "Cmd + C", "복사"),
        ("Ctrl + V", "Cmd + V", "붙여넣기"),
        ("Ctrl + X", "Cmd + X", "잘라내기"),
        ("Ctrl + Z", "Cmd + Z", "실행 취소 (실수 되돌리기)"),
        ("Ctrl + Y", "Cmd + Shift + Z", "다시 실행 (되돌린 작업 복구)"),
        ("Ctrl + F", "Cmd + F", "문서 및 웹페이지 내 검색"),
        ("Ctrl + A", "Cmd + A", "전체 선택"),
        ("Alt + Tab", "Cmd + Tab", "창 전환 (인강과 필기창 빠르게 이동)"),
        ("Win + Shift + S", "Cmd + Shift + 4", "화면 부분 캡처 (강의 자료 캡처)"),
        ("Win + . (마침표)", "Cmd + Ctrl + Space", "이모지 및 특수문자 창 열기"),
    ],
    "교사": [
        ("Ctrl + C", "Cmd + C", "복사"),
        ("Ctrl + V", "Cmd + V", "붙여넣기"),
        ("Ctrl + Shift + V", "Cmd + Shift + Option + V", "서식 없이 붙여넣기 (폰트 깨짐 방지)"),
        ("Ctrl + F", "Cmd + F", "문서 내 검색"),
        ("Ctrl + P", "Cmd + P", "인쇄 창 열기"),
        ("Alt + Tab", "Cmd + Tab", "창 전환"),
        ("Win + Shift + S", "Cmd + Shift + 4", "문제 및 그림 자료 캡처"),
        ("Win + V", "클립보드 기록 앱", "클립보드 검색 기록 (여러 개 복사 후 선택)"),
        ("F5", "Cmd + Shift + Return", "파워포인트 슬라이드 쇼 시작"),
        ("Shift + F5", "Cmd + Return", "현재 슬라이드부터 쇼 시작"),
    ],
    "직장인": [
        ("Alt + Tab", "Cmd + Tab", "작업 창 전환"),
        ("Win + D", "F11 (또는 Cmd + F3)", "모든 창 최소화하고 바탕화면 보기"),
        ("Win + L", "Cmd + Ctrl + Q", "자리 비울 때 컴퓨터 즉시 잠금 (보안 필수!)"),
        ("Ctrl + C", "Cmd + C", "복사"),
        ("Ctrl + V", "Cmd + V", "붙여넣기"),
        ("Ctrl + Shift + V", "Cmd + Shift + Option + V", "서식 없이 텍스트만 붙여넣기"),
        ("Ctrl + S", "Cmd + S", "수시로 파일 저장 (문서 유실 방지)"),
        ("Ctrl + Z", "Cmd + Z", "실행 취소"),
        ("Ctrl + F", "Cmd + F", "찾기 및 검색"),
        ("Win + V", "클립보드 매니저", "클립보드 기록 검색"),
    ],
    "개발자": [
        ("Ctrl + /", "Cmd + /", "코드 주석 처리 / 해제"),
        ("Ctrl + D", "Cmd + D", "같은 단어 연속 선택 (동시 수정)"),
        ("Ctrl + F", "Cmd + F", "코드 내 검색"),
        ("Ctrl + H", "Cmd + Option + F", "찾기 및 바꾸기 (Replace)"),
        ("Ctrl + P", "Cmd + P", "파일 이름으로 빠른 검색 및 열기"),
        ("Ctrl + Shift + P", "Cmd + Shift + P", "명령 팔레트 (모든 VS Code 기능 실행)"),
        ("Ctrl + `", "Cmd + `", "내장 터미널 열기 / 닫기"),
        ("Alt + 위/아래", "Option + 위/아래", "현재 줄(코드) 위/아래로 이동"),
        ("Ctrl + S", "Cmd + S", "파일 저장"),
        ("Ctrl + Shift + F", "Cmd + Shift + F", "프로젝트 전체 파일에서 검색"),
    ],
    "디자이너": [
        ("Ctrl + Z", "Cmd + Z", "실행 취소"),
        ("Ctrl + Shift + Z", "Cmd + Shift + Z", "다시 실행"),
        ("Ctrl + C", "Cmd + C", "복사"),
        ("Ctrl + V", "Cmd + V", "붙여넣기"),
        ("Ctrl + D", "Cmd + D", "복제하기 (Duplicate)"),
        ("Ctrl + G", "Cmd + G", "선택 레이어 그룹화"),
        ("Ctrl + Shift + G", "Cmd + Shift + G", "그룹 해제"),
        ("Ctrl + S", "Cmd + S", "저장"),
        ("Ctrl + Shift + S", "Cmd + Shift + S", "다른 이름으로 저장 / 내보내기"),
        ("Space + 드래그", "Space + 드래그", "캔버스 자유 이동 (핸드 툴)"),
    ],
    "콘텐츠 제작자": [
        ("Ctrl + C", "Cmd + C", "복사"),
        ("Ctrl + V", "Cmd + V", "붙여넣기"),
        ("Ctrl + Z", "Cmd + Z", "실행 취소"),
        ("Ctrl + S", "Cmd + S", "수시 저장"),
        ("Ctrl + F", "Cmd + F", "키워드 검색"),
        ("Alt + Tab", "Cmd + Tab", "참고 자료와 작업 창 전환"),
        ("Win + Shift + S", "Cmd + Shift + 4", "고화질 화면 부분 캡처"),
        ("Win + V", "클립보드 매니저", "클립보드 히스토리"),
        ("Win + . (마침표)", "Cmd + Ctrl + Space", "SNS 감성 이모지 입력창"),
    ],
    "영상 편집자": [
        ("Space", "Space", "타임라인 재생 / 일시정지"),
        ("C", "C", "자르기 도구 (Razor Tool)"),
        ("V", "V", "기본 선택 도구 (Selection Tool)"),
        ("Q", "Q", "재생헤드 앞부분 자르고 당기기 (Ripple Trim In)"),
        ("W", "W", "재생헤드 뒷부분 자르고 당기기 (Ripple Trim Out)"),
        ("Ctrl + K", "Cmd + K", "현재 위치 컷 자르기"),
        ("Ctrl + S", "Cmd + S", "틈틈이 저장 (렌더링 튕김 대비 필수!)"),
        ("Ctrl + Z", "Cmd + Z", "실행 취소"),
        ("Ctrl + M", "Cmd + M", "최종 영상 내보내기 (Export)"),
        ("Win + Shift + S", "Cmd + Shift + 4", "레퍼런스 영상 화면 캡처"),
    ],
    "기타 사용자(일반 사용자)": [
        ("Ctrl + C", "Cmd + C", "복사"),
        ("Ctrl + V", "Cmd + V", "붙여넣기"),
        ("Ctrl + Z", "Cmd + Z", "실행 취소"),
        ("Ctrl + F", "Cmd + F", "웹페이지나 문서에서 단어 찾기"),
        ("Ctrl + A", "Cmd + A", "전체 선택"),
        ("Alt + Tab", "Cmd + Tab", "실행 중인 창 빠르게 전환"),
        ("Win + E", "Cmd + N (Finder)", "파일 탐색기 열기"),
        ("Win + D", "F11", "바탕화면 바로 보기"),
        ("Win + L", "Cmd + Ctrl + Q", "컴퓨터 화면 즉시 잠금"),
        ("Ctrl + Shift + Esc", "Cmd + Option + Esc", "작업 관리자 (프로그램 강제 종료)"),
    ]
}


# -------------------------------
# 직업별 추천 사이트 데이터
# -------------------------------
SITES_DATA = {
    "학생": [
        ("노션 (Notion)", "https://www.notion.so", "강의 노트 필기, 시험 일정, 과제 체크리스트 관리 올인원 툴"),
        ("미리캔버스 (MiriCanvas)", "https://www.miricanvas.com", "깔끔한 PPT 발표 자료, 보고서 표지, 카드뉴스 무료 제작"),
        ("DeepL 번역기", "https://www.deepl.com", "과제 및 외국 논문 번역에 특화된 고성능 자연어 AI"),
        ("뤼튼 (Wrtn)", "https://wrtn.ai", "한국어 특화 무료 생성형 AI (과제 아이디어 브레인스토밍, 글 초안 작성)")
    ],
    "교사": [
        ("캔바 (Canva) 교육용", "https://www.canva.com", "교사와 학생을 위한 고품질 수업 프레젠테이션 및 학습지 제작"),
        ("카훗 (Kahoot!)", "https://kahoot.com", "학생들이 스마트폰으로 참여할 수 있는 실시간 퀴즈 도구"),
        ("패들렛 (Padlet)", "https://ko.padlet.com", "학급 온라인 게시판, 브레인스토밍 및 모둠 과제 취합"),
        ("에듀넷 티-클리어", "https://www.edunet.net", "국가 교육과정 기반의 공식 교수학습 자료 및 교육 연구 포털")
    ],
    "직장인": [
        ("ChatGPT", "https://chatgpt.com", "기획서 초안 작성, 비즈니스 이메일 검토, 데이터 요약 및 번역 보조"),
        ("Smallpdf", "https://smallpdf.com", "PDF 파일 압축, Word/Excel 변환, 페이지 합치기 및 분할"),
        ("트렐로 (Trello)", "https://trello.com", "칸반 보드 형태로 업무 진행 상태(할 일, 진행 중, 완료) 한눈에 관리"),
        ("DeepL", "https://www.deepl.com", "해외 바이어 이메일 및 외국 비즈니스 문서를 자연스럽게 번역")
    ],
    "개발자": [
        ("깃허브 (GitHub)", "https://github.com", "전 세계 최대의 소스코드 호스팅 및 버전 관리(Git), 협업 플랫폼"),
        ("스택 오버플로우 (Stack Overflow)", "https://stackoverflow.com", "개발 중 마주치는 에러와 문제 해결 팁을 모아놓은 글로벌 Q&A"),
        ("MDN Web Docs", "https://developer.mozilla.org", "웹 개발(HTML, CSS, JavaScript) 표준을 가장 정확하게 설명하는 문서"),
        ("Claude AI", "https://claude.ai", "코드 리뷰, 리팩토링, 알고리즘 구현 및 에러 디버깅 특화 AI")
    ],
    "디자이너": [
        ("피그마 (Figma)", "https://www.figma.com", "웹 브라우저에서 협업하는 UI/UX 웹, 앱 디자인 필수 툴"),
        ("핀터레스트 (Pinterest)", "https://www.pinterest.com", "시각적 영감, 디자인 트렌드 및 레퍼런스를 수집하고 정리하는 무드보드"),
        ("플래티콘 (Flaticon)", "https://www.flaticon.com", "수백만 개의 고품질 벡터 아이콘과 스티커 무료 다운로드"),
        ("눈누 (Noonnu)", "https://noonnu.cc", "상업용으로 무료 사용 가능한 예쁜 한글 폰트 모음 및 테스트")
    ],
    "콘텐츠 제작자": [
        ("썸트렌드 (SomeTrend)", "https://some.co.kr", "소셜 빅데이터 기반 실시간 검색어 트렌드 및 연관 키워드 분석"),
        ("브루 (Vrew)", "https://vrew.ai", "AI 음성인식으로 자동 자막을 생성하고 빠른 컷편집을 돕는 영상 툴"),
        ("언스플래시 (Unsplash)", "https://unsplash.com", "저작권 걱정 없는 상업용 초고화질 무료 이미지 사이트"),
        ("미리캔버스 (MiriCanvas)", "https://www.miricanvas.com", "유튜브 썸네일, 인스타그램 카드뉴스, 블로그 배너 템플릿 제작")
    ],
    "영상 편집자": [
        ("공유마당 (Gongu)", "https://gongu.copyright.or.kr", "한국저작권위원회가 제공하는 국가 공인 무료 BGM, 효과음, 폰트 아카이브"),
        ("효과음 연구소", "https://soundeffect-lab.info", "유튜브 영상 편집 시 많이 쓰이는 다양한 무료 효과음(SE) 다운로드"),
        ("프리픽 (Freepik)", "https://www.freepik.com", "영상에 삽입할 모션 그래픽 소스, 비디오 클립, 일러스트 모음"),
        ("캡컷 웹 (CapCut)", "https://www.capcut.com", "웹 브라우저에서 바로 사용 가능한 트렌디한 숏폼/릴스/틱톡 편집 툴")
    ],
    "기타 사용자(일반 사용자)": [
        ("정부24", "https://www.gov.kr", "주민등록등본 등 각종 민원 서류를 집에서 무료로 즉시 발급받는 포털"),
        ("누끼따기 (remove.bg)", "https://www.remove.bg/ko", "사진을 올리기만 하면 5초 만에 배경을 자동으로 지워주는 AI 사이트"),
        ("네이버 지도 (Naver Map)", "https://map.naver.com", "빠른 길찾기, 대중교통 경로, 거리뷰, 주변 시설 확인 필수 서비스"),
        ("ChatGPT", "https://chatgpt.com", "일상 궁금증 해결, 추천, 편지 및 글 작성을 도와주는 대화형 AI 비서")
    ]
}


# -------------------------------
# AI 단축키 추천 엔진 (자연어 질의 분석)
# -------------------------------
def get_ai_shortcut_recommendation(query, os_type):
    q = query.lower().strip()
    is_mac = (os_type == "Mac 🍎")

    def k(win, mac):
        return mac if is_mac else win

    if any(w in q for w in [
        "ctrl c", "ctrl+c", "ctrl v", "ctrl+v", "ctrl x", "ctrl+x", "cmd c", "cmd+c", "cmd v", "cmd+v", "cmd x", "cmd+x",
        "복사", "붙여넣기", "복붙", "복사 붙여넣기", "잘라내기", "카피", "복사하기", "붙여넣는", "텍스트 복사",
        "서식 없이 붙여넣기", "서식없이", "컨트롤 c", "컨트롤 v", "커맨드 c", "커맨드 v", "복사 단축키"
    ]):
        return {
            "message": "복사와 붙여넣기 단축키를 찾으셨군요! 가장 기본이 되는 단축키와 함께, 원본을 지우는 '잘라내기'와 서식 없이 텍스트만 붙여넣는 단축키도 함께 챙겨드립니다.",
            "shortcuts": [
                {"key": k("Ctrl + C", "Cmd + C"), "desc": "선택 항목 복사"},
                {"key": k("Ctrl + V", "Cmd + V"), "desc": "복사한 항목 붙여넣기"},
                {"key": k("Ctrl + X", "Cmd + X"), "desc": "잘라내기 (옮기면서 원본 삭제)"},
                {"key": k("Ctrl + Shift + V", "Cmd + Shift + Option + V"), "desc": "서식 없이 깔끔하게 텍스트만 붙여넣기"}
            ]
        }
    elif any(w in q for w in [
        "alt tab", "alt+tab", "cmd tab", "cmd+tab", "win d", "win+d", "창 전환", "작업창 전환",
        "화면 전환", "창 바꾸기", "화면 바꾸기", "창 넘기기", "작업창", "앱 전환", "프로그램 전환",
        "바탕화면 보기", "바탕화면 바로가기", "알트탭", "알트 탭", "커맨드 탭", "멀티태스킹", "다른 창으로", "화면 넘기기", "창 변경"
    ]):
        return {
            "message": "여러 프로그램을 넘나들며 작업할 때 속도를 높여주는 창 전환 단축키입니다!",
            "shortcuts": [
                {"key": k("Alt + Tab", "Cmd + Tab"), "desc": "실행 중인 작업 창 빠르게 전환"},
                {"key": k("Win + D", "F11"), "desc": "모든 창 최소화하고 바탕화면 즉시 보기"}
            ]
        }
    elif any(w in q for w in [
        "ctrl shift t", "ctrl+shift+t", "cmd shift t", "cmd+shift+t", "ctrl w", "ctrl+w", "ctrl t", "ctrl+t",
        "닫은 창", "닫힌 창", "닫은 탭", "닫힌 탭", "창 다시 열기", "탭 다시 열기", "창 다시", "탭 다시",
        "창 복구", "탭 복구", "실수로 닫", "창 닫힘", "탭 닫힘", "창 끔", "탭 끔", "창 살리기", "탭 살리기", "방금 닫은", "닫았던"
    ]):
        return {
            "message": "인터넷 하다가 실수로 닫은 탭은 복구 단축키가 있습니다! 새 탭 열기와 탭 닫기 단축키도 함께 추천해 드립니다.",
            "shortcuts": [
                {"key": k("Ctrl + Shift + T", "Cmd + Shift + T"), "desc": "방금 닫은 인터넷 탭 즉시 다시 열기 (실수 복구)"},
                {"key": k("Ctrl + W", "Cmd + W"), "desc": "현재 보고 있는 탭 닫기"},
                {"key": k("Ctrl + T", "Cmd + T"), "desc": "새로운 인터넷 탭 열기"}
            ]
        }
    elif any(w in q for w in [
        "win shift s", "win+shift+s", "cmd shift 4", "cmd+shift+4", "cmd shift 3", "cmd+shift+3",
        "prtscn", "print screen", "캡처", "캡쳐", "스크린샷", "스샷", "화면 캡처", "화면 캡쳐",
        "화면 저장", "부분 캡처", "영역 캡처", "캡처 도구", "윈도우 캡처", "맥 캡처", "화면 찍기", "캡쳐 단축키", "화면 복사"
    ]):
        return {
            "message": "화면을 캡처할 때 가장 편한 단축키입니다! 원하는 영역만 드래그해서 캡처하는 단축키를 추천해 드려요.",
            "shortcuts": [
                {"key": k("Win + Shift + S", "Cmd + Shift + 4"), "desc": "원하는 영역만 마우스 드래그로 부분 캡처"},
                {"key": k("PrtScn", "Cmd + Shift + 3"), "desc": "화면 전체 캡처"},
                {"key": k("Alt + PrtScn", "Cmd + Shift + 4 후 Space"), "desc": "현재 열린 창 하나만 캡처"}
            ]
        }
    elif any(w in q for w in [
        "ctrl z", "ctrl+z", "ctrl y", "ctrl+y", "cmd z", "cmd+z", "cmd shift z", "cmd+shift+z",
        "실행 취소", "실행취소", "되돌리기", "되돌려", "되돌리고", "다시 실행", "다시실행", "실수 되돌리기",
        "언두", "리두", "undo", "redo", "원래대로", "작업 취소", "컨트롤 z", "커맨드 z", "실행 취소 단축키"
    ]):
        return {
            "message": "실수했을 때 시간을 되돌려주는 단축키입니다! 너무 많이 되돌렸을 때 다시 앞으로 복원하는 단축키도 세트로 추천합니다.",
            "shortcuts": [
                {"key": k("Ctrl + Z", "Cmd + Z"), "desc": "실행 취소 (방금 한 실수 되돌리기)"},
                {"key": k("Ctrl + Y", "Cmd + Shift + Z"), "desc": "다시 실행 (취소한 작업 다시 복구)"}
            ]
        }
    elif any(w in q for w in [
        "ctrl /", "ctrl+/", "ctrl slash", "cmd /", "cmd+/", "cmd slash",
        "ctrl d", "ctrl+d", "cmd d", "cmd+d", "alt 위", "alt 아래", "option 위", "option 아래",
        "주석", "코드 주석", "주석 처리", "주석 달기", "주석 해제", "주석 토글", "주석 단축키",
        "코딩 주석", "한 줄 주석", "여러 줄 주석", "주석 어떻게", "코드 설명", "코드 메모",
        "코딩", "코드", "개발", "프로그래밍", "개발자 단축키", "코딩 단축키", "코딩할 때", "코드 수정",
        "동시 선택", "같은 단어 선택", "동일 단어", "멀티 커서", "단어 동시 수정",
        "줄 이동", "코드 이동", "줄 바꾸기", "줄 올리기", "줄 내리기",
        "comment", "comments", "uncomment", "vs code", "vscode", "visual studio code",
        "컨트롤 슬래시", "컨트롤 /", "커맨드 슬래시", "커맨드 /", "컨트롤 d", "커맨드 d"
    ]):
        return {
            "message": "개발자라면 매일 누르는 주석 처리와 코드 편집 단축키입니다! 줄을 통째로 이동시키는 단축키도 추천합니다.",
            "shortcuts": [
                {"key": k("Ctrl + /", "Cmd + /"), "desc": "코드 한 줄 주석 토글 (지정 / 해제)"},
                {"key": k("Ctrl + D", "Cmd + D"), "desc": "같은 단어 연속 다중 선택 (동시 수정)"},
                {"key": k("Alt + 위/아래", "Option + 위/아래"), "desc": "현재 코드 줄 위/아래로 이동"}
            ]
        }
    elif any(w in q for w in [
        "ctrl f", "ctrl+f", "ctrl h", "ctrl+h", "cmd f", "cmd+f", "cmd option f", "cmd+option+f",
        "검색", "단어 찾기", "글자 찾기", "찾기", "바꾸기", "단어 바꾸기", "문서 검색", "코드 검색",
        "replace", "find", "파인드", "리플레이스", "컨트롤 f", "컨트롤 h", "커맨드 f", "단어 변경", "일괄 변경"
    ]):
        return {
            "message": "문서나 웹페이지에서 단어를 빠르게 찾거나 바꿀 때 쓰는 단축키입니다!",
            "shortcuts": [
                {"key": k("Ctrl + F", "Cmd + F"), "desc": "문서 및 웹페이지 내 키워드 검색"},
                {"key": k("Ctrl + H", "Cmd + Option + F"), "desc": "찾기 및 다른 단어로 일괄 바꾸기"}
            ]
        }
    elif any(w in q for w in [
        "ctrl shift esc", "ctrl+shift+esc", "alt f4", "alt+f4", "win l", "win+l", "cmd option esc",
        "cmd ctrl q", "작업 관리자", "작업관리자", "강제 종료", "강제종료", "프로그램 강제", "컴퓨터 멈춤",
        "화면 멈춤", "렉 걸렸을", "렉 걸림", "안 꺼져", "화면 잠금", "컴퓨터 잠금", "pc 잠금", "응답 없음", "프로그램 끄기"
    ]):
        return {
            "message": "프로그램이 멈춰서 안 꺼질 때 쓰는 응급 단축키와 화면 잠금 단축키입니다.",
            "shortcuts": [
                {"key": k("Ctrl + Shift + Esc", "Cmd + Option + Esc"), "desc": "작업 관리자 / 강제 종료 창 열기"},
                {"key": k("Alt + F4", "Cmd + Q"), "desc": "현재 프로그램 강제 종료"},
                {"key": k("Win + L", "Cmd + Ctrl + Q"), "desc": "컴퓨터 화면 즉시 잠금 (보안 필수)"}
            ]
        }
    else:
        matched = []
        for j, s_list in SHORTCUTS_DATA.items():
            for w_k, m_k, d in s_list:
                if q in d.lower() or any(term in d.lower() for term in q.split()):
                    key_str = m_k if is_mac else w_k
                    if not any(item["key"] == key_str for item in matched):
                        matched.append({"key": key_str, "desc": f"[{j}] {d}"})
        if matched:
            return {
                "message": f"'{query}' 관련 단축키를 데이터베이스에서 찾아냈습니다!",
                "shortcuts": matched[:4]
            }
        else:
            return {
                "message": f"'{query}'에 대한 정확한 단축키를 찾지 못했습니다. 필수 기본 단축키를 추천해 드립니다!",
                "shortcuts": [
                    {"key": k("Ctrl + C", "Cmd + C"), "desc": "복사"},
                    {"key": k("Ctrl + V", "Cmd + V"), "desc": "붙여넣기"},
                    {"key": k("Ctrl + Z", "Cmd + Z"), "desc": "실행 취소"},
                    {"key": k("Win + Shift + S", "Cmd + Shift + 4"), "desc": "화면 캡처"}
                ]
            }


# -------------------------------
# 사이드바 (깔끔하고 슬림하게 조절)
# -------------------------------
with st.sidebar:
    if os.path.exists("app_icon.png"):
        st.image("app_icon.png", width=70)

    # 1. 로그인 상태 / 접이식 폼
    if st.session_state.logged_in:
        st.success(f"👤 **{st.session_state.user_id}**님 접속 중\n\n📝 등록 메모: **{len(st.session_state.my_notes)}개**")
        if st.button("로그아웃", use_container_width=True):
            user_data["__auto_login__"] = None
            save_data(user_data)
            st.session_state.logged_in = False
            st.session_state.user_id = None
            st.session_state.yourjob = None
            st.session_state.my_notes = []
            st.rerun()
    else:
        with st.expander("🔐 로그인 / 회원가입", expanded=False):
            tab_l, tab_r = st.tabs(["로그인", "가입"])
            with tab_l:
                uid = st.text_input("아이디", key="l_id")
                upw = st.text_input("비밀번호", type="password", key="l_pw")
                remember = st.checkbox("자동 로그인 (로그인 유지)", value=True, key="chk_auto")
                if st.button("로그인", key="btn_l", use_container_width=True):
                    if uid in user_data and user_data[uid]["password"] == upw:
                        st.session_state.logged_in = True
                        st.session_state.user_id = uid
                        st.session_state.yourjob = user_data[uid].get("job", None)
                        st.session_state.my_notes = user_data[uid].get("notes", [])
                        if remember:
                            user_data["__auto_login__"] = uid
                        else:
                            user_data["__auto_login__"] = None
                        save_data(user_data)
                        st.rerun()
                    else:
                        st.error("아이디나 비밀번호가 다릅니다.")
            with tab_r:
                rid = st.text_input("새 아이디", key="r_id")
                rpw = st.text_input("새 비밀번호", type="password", key="r_pw")
                if st.button("가입하기", key="btn_r", use_container_width=True):
                    if not rid or not rpw:
                        st.warning("모두 입력해주세요.")
                    elif rid in user_data:
                        st.error("이미 있는 아이디입니다.")
                    else:
                        user_data[rid] = {"password": rpw, "job": None, "notes": []}
                        save_data(user_data)
                        st.success("가입 완료! 로그인해주세요.")

            # 구글 계정으로 로그인 (실제 OAuth 연동)
            st.write("---")
            st.caption(" G 구글 계정 간편 로그인")
            google_auth_url = (
                f"https://accounts.google.com/o/oauth2/v2/auth?response_type=code"
                f"&client_id={GOOGLE_CLIENT_ID}&redirect_uri={REDIRECT_URI}"
                f"&scope=openid%20email%20profile"
            )
            st.link_button("구글 계정으로 로그인 ↗", google_auth_url, use_container_width=True)

    st.write("---")


    # 네이버 로그인 버튼
            st.write("---")
            st.caption(" N 네이버 계정 간편 로그인")
            naver_auth_url = (
                f"https://nid.naver.com/oauth2.0/authorize?response_type=code"
                f"&client_id={NAVER_CLIENT_ID}&redirect_uri={urllib.parse.quote(REDIRECT_URI)}"
                f"&state=smartjob_naver_login"
            )
            st.link_button("네이버 계정으로 로그인 ↗", naver_auth_url, use_container_width=True)

    # 2. OS 선택
    os_type = st.radio("💻 OS 선택", ["Windows 💻", "Mac 🍎"], horizontal=True)

    # 3. 네비게이션 메뉴
    menu = st.radio(
        "📌 메뉴",
        ["직업 선택하기", "유용한 단축키", "유용한 사이트", "나만의 단축키 메모", "치트시트 다운로드"]
    )

    st.write("---")
    if st.session_state.yourjob:
        st.info(f"선택 직업: **{st.session_state.yourjob}**")
    else:
        st.info("직업을 먼저 선택해주세요!")


# -------------------------------
# 1. 직업 선택하기
# -------------------------------
if menu == "직업 선택하기":
    st.title("🎯 직업 선택하기")

    if st.session_state.yourjob is None:
        st.write("본인의 직업 또는 역할을 선택하시면 맞춤 단축키와 추천 사이트를 안내해 드립니다.")
        job = st.selectbox(
            "당신의 직업은 무엇인가요?",
            ["학생", "교사", "직장인", "개발자", "디자이너", "콘텐츠 제작자", "영상 편집자", "기타 사용자(일반 사용자)"]
        )

        if st.button("직업 선택 완료"):
            st.session_state.yourjob = job
            if st.session_state.logged_in:
                user_data[st.session_state.user_id]["job"] = job
                save_data(user_data)
            st.balloons()
            st.success(f"'{job}'(으)로 선택되었습니다!")
            time.sleep(1)
            st.rerun()

    else:
        st.subheader(f"현재 선택된 직업 : **{st.session_state.yourjob}**")
        st.write("왼쪽 사이드바 메뉴에서 **'유용한 단축키'** 및 **'유용한 사이트'**를 확인해보세요.")
        if st.button("직업 다시 선택하기"):
            st.session_state.yourjob = None
            if st.session_state.logged_in:
                user_data[st.session_state.user_id]["job"] = None
                save_data(user_data)
            st.rerun()


# -------------------------------
# 2. 유용한 단축키
# -------------------------------
elif menu == "유용한 단축키":
    st.title("⚡ 유용한 단축키")

    if st.session_state.yourjob is None:
        st.warning("먼저 '직업 선택하기' 메뉴에서 직업을 선택해주세요.")
    else:
        current_job = st.session_state.yourjob
        st.caption(f"현재 운영체제: **{os_type}** (사이드바에서 변경 가능)")

        search_query = st.text_input("🔍 단축키 실시간 검색", placeholder="기능이나 단축키를 검색하세요 (예: 복사, 캡처, Cmd, Shift)")
        shortcuts = SHORTCUTS_DATA.get(current_job, [])

        st.subheader(f"💼 {current_job} 맞춤 단축키")

        matched_count = 0
        for win_key, mac_key, desc in shortcuts:
            key_to_display = mac_key if os_type == "Mac 🍎" else win_key

            if search_query.strip():
                if (search_query.lower() not in key_to_display.lower()) and (search_query.lower() not in desc.lower()):
                    continue

            matched_count += 1
            st.write(f"- **`{key_to_display}`** — {desc}")

        if matched_count == 0:
            st.info("검색 조건과 일치하는 단축키가 없습니다.")


# -------------------------------
# 3. 유용한 사이트
# -------------------------------
elif menu == "유용한 사이트":
    st.title("🌐 유용한 사이트")

    if st.session_state.yourjob is None:
        st.warning("먼저 '직업 선택하기' 메뉴에서 직업을 선택해주세요.")
    else:
        current_job = st.session_state.yourjob
        st.subheader(f"🎓 {current_job}에게 유용한 추천 사이트 & 도구")

        sites = SITES_DATA.get(current_job, [])
        for title, url, desc in sites:
            st.write(f"#### {title}")
            st.write(f"• {desc}")
            st.link_button(f"{title.split()[0]} 바로가기 ↗", url)
            st.write("")


# -------------------------------
# 4. 나만의 단축키 메모
# -------------------------------
elif menu == "나만의 단축키 메모":
    st.title("📝 나만의 단축키 메모")

    if not st.session_state.logged_in:
        st.info("💡 사이드바에서 **로그인**하시면 나만의 단축키 메모가 파일에 안전하게 영구 저장됩니다!")
    else:
        st.success(f"**{st.session_state.user_id}**님의 개인 메모 공간입니다. (저장된 메모: {len(st.session_state.my_notes)}개)")

    tab_ai, tab_manual = st.tabs(["🤖 AI 단축키 추천 비서", "✏️ 직접 입력 등록"])

    with tab_ai:
        st.subheader("💬 AI에게 단축키 물어보기")
        st.write("자연어로 편하게 물어보세요! 연관된 단축키까지 함께 추천해 드립니다.")

        st.caption("💡 빠른 질문 버튼을 눌러보세요:")
        c1, c2, c3, c4 = st.columns(4)
        if c1.button("📋 복붙 단축키"):
            st.session_state.input_ai_query = "복붙하는 단축키 알려줘"
            st.rerun()
        if c2.button("❌ 닫은 창 복구"):
            st.session_state.input_ai_query = "실수로 닫은 창 다시 열기"
            st.rerun()
        if c3.button("✂️ 화면 캡처"):
            st.session_state.input_ai_query = "화면 캡처하는 법"
            st.rerun()
        if c4.button("💻 코드 주석"):
            st.session_state.input_ai_query = "코드 주석 처리 단축키"
            st.rerun()

        user_ai_input = st.text_input(
            "궁금한 기능이나 상황을 물어보세요",
            placeholder="예: 복붙하는 단축키 없어? / 닫힌 창 다시 여는 법 / 컴퓨터 멈췄을 때",
            key="input_ai_query"
        )

        if user_ai_input.strip():
            result = get_ai_shortcut_recommendation(user_ai_input, os_type)
            st.info(f"🤖 **AI 비서의 답변:**\n\n{result['message']}")
            st.write("#### 💡 추천 단축키 목록 (원클릭 등록)")

            for i, item in enumerate(result["shortcuts"]):
                col_info, col_btn = st.columns([3, 1])
                col_info.markdown(f"**`{item['key']}`** — {item['desc']}")

                already_registered = any(note["key"] == item["key"] for note in st.session_state.my_notes)
                if already_registered:
                    col_btn.write("✅ 등록 완료")
                else:
                    if col_btn.button("➕ 내 메모에 추가", key=f"ai_add_{i}"):
                        st.session_state.my_notes.append({
                            "key": item["key"],
                            "desc": item["desc"]
                        })
                        if st.session_state.logged_in:
                            user_data[st.session_state.user_id]["notes"] = st.session_state.my_notes
                            save_data(user_data)
                        st.success(f"'{item['key']}' 단축키가 추가되었습니다!")
                        time.sleep(0.5)
                        st.rerun()

    with tab_manual:
        st.subheader("✏️ 직접 단축키 등록")
        with st.form("manual_note_form", clear_on_submit=True):
            col1, col2 = st.columns([1, 2])
            new_key = col1.text_input("단축키", placeholder="예: Ctrl + Shift + T")
            new_desc = col2.text_input("기능 설명", placeholder="예: 닫은 인터넷 창 다시 열기")
            submitted = st.form_submit_button("단축키 메모 추가")

            if submitted:
                if new_key.strip() and new_desc.strip():
                    st.session_state.my_notes.append({"key": new_key.strip(), "desc": new_desc.strip()})
                    if st.session_state.logged_in:
                        user_data[st.session_state.user_id]["notes"] = st.session_state.my_notes
                        save_data(user_data)
                    st.success("새로운 단축키가 메모에 추가되었습니다!")
                    time.sleep(0.5)
                    st.rerun()
                else:
                    st.warning("단축키와 설명을 모두 입력해주세요.")

    st.write("---")
    st.subheader("📋 내가 등록한 단축키 목록")

    if not st.session_state.my_notes:
        st.write("아직 등록된 나만의 단축키가 없습니다. 위 탭에서 단축키를 추가해보세요!")
    else:
        for index, note in enumerate(st.session_state.my_notes):
            c1, c2, c3 = st.columns([2, 4, 1])
            c1.markdown(f"**`{note['key']}`**")
            c2.write(note["desc"])
            if c3.button("삭제", key=f"del_note_{index}"):
                st.session_state.my_notes.pop(index)
                if st.session_state.logged_in:
                    user_data[st.session_state.user_id]["notes"] = st.session_state.my_notes
                    save_data(user_data)
                st.rerun()


# -------------------------------
# 5. 치트시트 다운로드
# -------------------------------
elif menu == "치트시트 다운로드":
    st.title("📥 치트시트 다운로드")

    if st.session_state.yourjob is None:
        st.warning("먼저 '직업 선택하기' 메뉴에서 직업을 선택해주세요.")
    else:
        current_job = st.session_state.yourjob
        st.write(f"선택된 직업인 **'{current_job}'**의 맞춤 단축키({os_type})와 추천 사이트, 나만의 메모를 텍스트 파일로 다운로드합니다.")

        cheatsheet_text = f"=== [{current_job}] 맞춤 치트시트 ({os_type}) ===\n\n"
        cheatsheet_text += f"■ {current_job} 추천 단축키\n"

        for win_key, mac_key, desc in SHORTCUTS_DATA.get(current_job, []):
            key_str = mac_key if os_type == "Mac 🍎" else win_key
            cheatsheet_text += f"- {key_str} : {desc}\n"

        if st.session_state.my_notes:
            cheatsheet_text += "\n■ 나만의 등록 단축키 메모\n"
            for note in st.session_state.my_notes:
                cheatsheet_text += f"- {note['key']} : {note['desc']}\n"

        cheatsheet_text += "\n■ 추천 사이트 모음\n"
        for title, url, desc in SITES_DATA.get(current_job, []):
            cheatsheet_text += f"- {title} ({url}) : {desc}\n"

        st.code(cheatsheet_text, language="text")

        st.download_button(
            label="💾 치트시트 파일(.txt) 다운로드",
            data=cheatsheet_text,
            file_name=f"{current_job}_치트시트_{os_type.split()[0]}.txt",
            mime="text/plain"
        )
