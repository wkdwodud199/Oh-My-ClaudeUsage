"""Claude.ai 사용량 조회 (Playwright 버전)"""
from typing import Optional, Dict
from datetime import datetime, timedelta
from playwright.sync_api import sync_playwright, Browser, BrowserContext, Page
import json


class UsageData:
    """사용량 데이터 클래스"""

    def __init__(self):
        self.current_session_usage = 0
        self.current_session_limit = 100
        self.current_session_reset = None

        self.weekly_all_usage = 0
        self.weekly_all_limit = 100
        self.weekly_all_reset = None

        self.weekly_sonnet_usage = 0
        self.weekly_sonnet_limit = 100
        self.weekly_sonnet_reset = None

        self.last_updated = None


class ClaudeUsageScraperPlaywright:
    """Claude 사용량 스크래퍼 (Playwright 사용, 브라우저 인스턴스 유지)"""

    def __init__(self, cookies: Dict):
        self.cookies = cookies
        self.playwright = None
        self.browser = None
        self.context = None
        self.page = None
        self.org_id = None  # 캐시
        self.is_running = False

    def start(self):
        """브라우저 시작 (한 번만 호출)"""
        if self.is_running:
            return
        self.playwright = sync_playwright().start()
        self.browser = self.playwright.chromium.launch(headless=True)
        self._create_context()
        self.is_running = True
        print("✓ Playwright 브라우저 시작됨 (유지 모드)")

    def _create_context(self):
        """브라우저 컨텍스트 생성"""
        if self.context:
            try:
                self.context.close()
            except:
                pass
        self.context = self.browser.new_context(
            user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        )
        cookies_list = []
        for name, value in self.cookies.items():
            cookies_list.append({
                'name': name,
                'value': value,
                'domain': '.claude.ai',
                'path': '/',
            })
        self.context.add_cookies(cookies_list)
        self.page = self.context.new_page()

    def stop(self):
        """브라우저 종료"""
        self.is_running = False
        try:
            if self.page:
                self.page.close()
            if self.context:
                self.context.close()
            if self.browser:
                self.browser.close()
            if self.playwright:
                self.playwright.stop()
        except:
            pass
        print("✓ Playwright 브라우저 종료됨")

    def update_cookies(self, cookies: Dict):
        """쿠키 갱신 (세션 재로그인 시)"""
        self.cookies = cookies
        self._create_context()
        self.org_id = None

    # 기존 컨텍스트 매니저 호환 유지
    def __enter__(self):
        self.start()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.stop()

    def fetch_usage_data(self) -> Optional[UsageData]:
        """사용량 데이터 조회 (브라우저 재사용)"""
        try:
            # 조직 ID 캐시 활용
            if not self.org_id:
                print("조직 정보 조회 중...")
                response = self.page.request.get("https://claude.ai/api/organizations")
                if response.status != 200:
                    print(f"조직 정보 조회 실패: {response.status}")
                    return None
                orgs = response.json()
                if not orgs:
                    print("조직 정보가 없습니다")
                    return None
                self.org_id = orgs[0].get('uuid')
                print(f"✓ 조직 ID: {self.org_id}")

            # 사용량 조회
            usage_response = self.page.request.get(
                f"https://claude.ai/api/organizations/{self.org_id}/usage"
            )

            if usage_response.status == 200:
                usage_json = usage_response.json()
                print(f"✓ 사용량 데이터 조회 성공")
                return self._parse_usage_data(usage_json)
            else:
                print(f"사용량 API 응답 실패: {usage_response.status}")
                # 403/401이면 컨텍스트 재생성 시도
                if usage_response.status in (401, 403):
                    print("세션 만료 가능성 - 컨텍스트 재생성")
                    self._create_context()
                    self.org_id = None
                return None

        except Exception as e:
            print(f"사용량 조회 실패: {e}")
            import traceback
            traceback.print_exc()
            return None

    def _parse_usage_data(self, data: Dict) -> UsageData:
        """API 응답 데이터 파싱"""
        from dateutil import parser as date_parser

        usage = UsageData()

        # 현재 세션 (5시간 한도)
        if 'five_hour' in data and data['five_hour']:
            five_hour = data['five_hour']
            usage.current_session_usage = int(five_hour.get('utilization', 0))
            usage.current_session_limit = 100

            reset_str = five_hour.get('resets_at')
            if reset_str:
                usage.current_session_reset = date_parser.parse(reset_str)

        # 주간 한도 - 모든 모델
        if 'seven_day' in data and data['seven_day']:
            seven_day = data['seven_day']
            usage.weekly_all_usage = int(seven_day.get('utilization', 0))
            usage.weekly_all_limit = 100

            reset_str = seven_day.get('resets_at')
            if reset_str:
                usage.weekly_all_reset = date_parser.parse(reset_str)

        # 주간 한도 - Sonnet만
        if 'seven_day_sonnet' in data and data['seven_day_sonnet']:
            sonnet = data['seven_day_sonnet']
            usage.weekly_sonnet_usage = int(sonnet.get('utilization', 0))
            usage.weekly_sonnet_limit = 100

            reset_str = sonnet.get('resets_at')
            if reset_str:
                usage.weekly_sonnet_reset = date_parser.parse(reset_str)

        usage.last_updated = datetime.now()
        return usage
