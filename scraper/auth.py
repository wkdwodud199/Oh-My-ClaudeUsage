"""Claude.ai 인증 및 세션 관리"""
import json
import os
from pathlib import Path
from typing import Optional, Dict
from playwright.sync_api import sync_playwright, Page, Browser


class ClaudeAuth:
    """Claude.ai 인증 관리 클래스"""

    def __init__(self):
        self.session_file = Path("config/session.json")
        self.session_data: Optional[Dict] = None
        self.cookies: Optional[Dict] = None

    def load_session(self) -> bool:
        """저장된 세션 로드"""
        if not self.session_file.exists():
            return False

        try:
            with open(self.session_file, 'r', encoding='utf-8') as f:
                self.session_data = json.load(f)
                self.cookies = self.session_data.get('cookies', {})
            return True
        except Exception as e:
            print(f"세션 로드 실패: {e}")
            return False

    def save_session(self, cookies: Dict) -> bool:
        """세션 저장"""
        try:
            self.session_file.parent.mkdir(parents=True, exist_ok=True)

            session_data = {
                'cookies': cookies
            }

            with open(self.session_file, 'w', encoding='utf-8') as f:
                json.dump(session_data, f, indent=2)

            self.session_data = session_data
            self.cookies = cookies
            return True
        except Exception as e:
            print(f"세션 저장 실패: {e}")
            return False

    def login_with_browser_manual(self) -> bool:
        """브라우저를 열어서 사용자가 직접 로그인 (GUI 안전 버전)"""
        try:
            print("=" * 80)
            print("브라우저 로그인")
            print("=" * 80)
            print()
            print("브라우저가 열립니다. Claude.ai에 로그인하세요.")
            print()

            with sync_playwright() as p:
                # 브라우저 설정
                browser = p.chromium.launch(
                    headless=False,
                    args=[
                        '--disable-blink-features=AutomationControlled',
                    ]
                )

                context = browser.new_context(
                    viewport={'width': 1280, 'height': 720},
                    user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
                )

                page = context.new_page()

                # Claude.ai로 이동
                print("브라우저에서 https://claude.ai 를 여는 중...")
                page.goto("https://claude.ai", wait_until="networkidle")

                print("✓ Browser opened")
                print("Please sign in. Login will be detected automatically...")

                # 로그인 완료 대기 - 쿠키 모니터링 + API 확인
                print("로그인 완료 대기 중 (최대 5분)...")
                import time
                login_success = False
                start_time = time.time()
                initial_cookie_count = len(context.cookies())
                print(f"초기 쿠키 수: {initial_cookie_count}")

                while True:
                    current_time = time.time()
                    elapsed = int(current_time - start_time)
                    if elapsed > 300:  # 5분 타임아웃
                        print("⚠ 타임아웃: 5분이 경과했습니다")
                        break

                    try:
                        # 쿠키 변화 모니터링
                        current_cookies = context.cookies()
                        cookie_count = len(current_cookies)
                        cookie_names = {c['name'] for c in current_cookies}

                        # 세션 쿠키 확인
                        has_session = bool(cookie_names & {'sessionKey', '__ssid', 'lastActiveOrg'})
                        print(f"[{elapsed}s] 쿠키: {cookie_count}개, 세션쿠키: {has_session}")

                        if has_session or cookie_count > initial_cookie_count + 3:
                            # 기존 페이지의 request API로 테스트 (새 탭 없음)
                            print(f"[{elapsed}s] Session detected. Verifying API...")
                            try:
                                test_response = page.request.get(
                                    "https://claude.ai/api/organizations",
                                    timeout=10000
                                )
                                status = test_response.status
                                print(f"[{elapsed}s] API response: {status}")
                                if status == 200:
                                    print("✓ Login complete")
                                    login_success = True
                                    break
                            except Exception as e:
                                print(f"[{elapsed}s] API test error: {e}")

                        time.sleep(3)
                    except Exception as e:
                        print(f"[{elapsed}s] 확인 중 오류: {e}")
                        time.sleep(3)

                if not login_success:
                    print("✗ 로그인이 완료되지 않았습니다")
                    browser.close()
                    return False

                print("쿠키를 추출하는 중...")

                # 쿠키 추출
                cookies = context.cookies()
                cookie_dict = {cookie['name']: cookie['value'] for cookie in cookies}

                print(f"✓ {len(cookie_dict)}개의 쿠키를 추출했습니다")
                print("✓ 세션이 검증되었습니다")

                browser.close()

                # 세션 저장
                if self.save_session(cookie_dict):
                    print("✓ 세션이 저장되었습니다")
                    return True
                else:
                    print("✗ 세션 저장 실패")
                    return False

        except Exception as e:
            print(f"오류 발생: {e}")
            import traceback
            traceback.print_exc()
            return False

    def verify_session(self) -> bool:
        """세션 유효성 검증 (Playwright 사용)"""
        if not self.cookies:
            print("쿠키가 없습니다")
            return False

        try:
            print("API 검증 중 (Playwright): https://claude.ai/api/organizations")

            with sync_playwright() as p:
                browser = p.chromium.launch(headless=True)
                context = browser.new_context(
                    user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
                )

                # 쿠키를 Playwright 형식으로 변환하여 추가
                cookies_list = []
                for name, value in self.cookies.items():
                    cookies_list.append({
                        'name': name,
                        'value': value,
                        'domain': '.claude.ai',
                        'path': '/',
                    })
                context.add_cookies(cookies_list)

                page = context.new_page()

                # API 호출
                response = page.request.get("https://claude.ai/api/organizations")

                print(f"API 응답 상태: {response.status}")

                if response.status != 200:
                    print(f"API 응답 내용: {response.text()[:200]}")

                browser.close()
                return response.status == 200

        except Exception as e:
            print(f"API 호출 오류: {e}")
            import traceback
            traceback.print_exc()
            return False

    def get_cookies(self) -> Optional[Dict]:
        """현재 쿠키 반환"""
        return self.cookies
