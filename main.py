"""Oh-my-claudeusage - Claude 사용량 대시보드"""
import sys
import io

# Windows 콘솔 인코딩 설정
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', line_buffering=True)
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', line_buffering=True)

# 출력 즉시 플러시
import functools
_original_print = print
print = functools.partial(_original_print, flush=True)

import subprocess
import threading

from gui.dashboard import DashboardWindow
from gui.login import LoginWindow
from scraper.auth import ClaudeAuth
from scraper.usage_playwright import ClaudeUsageScraperPlaywright


class App:
    """메인 애플리케이션"""

    def __init__(self):
        self.auth = ClaudeAuth()
        self.dashboard = None
        self.scraper = None  # 브라우저 인스턴스 유지
        self._stop_event = threading.Event()
        self.update_interval = 1 * 60 * 1000  # 1분 (밀리초)

    def run(self):
        """애플리케이션 실행"""
        # 대시보드 생성
        self.dashboard = DashboardWindow()

        # 저장된 세션 확인 (Playwright 사용 안함 - 파일만 체크)
        if self.auth.load_session() and self.auth.get_cookies():
            print("✓ 저장된 세션을 찾았습니다.")
            self.start_monitoring()
        else:
            print("로그인이 필요합니다.")
            self.show_login()

        # 메인 루프 시작
        self.dashboard.mainloop()

    def show_login(self):
        """로그인 창 표시"""
        LoginWindow(self.dashboard, self.on_login)

    def on_login(self) -> bool:
        """로그인 처리 (백그라운드 스레드에서 호출됨)"""
        success = self.auth.login_with_browser_manual()

        if success:
            print("✓ Login successful")
            self.dashboard.after(0, self.start_monitoring)
            return True
        else:
            print("✗ 로그인 실패")
            return False

    def start_monitoring(self):
        """모니터링 시작"""
        cookies = self.auth.get_cookies()
        if not cookies:
            self.dashboard.show_error("세션 정보를 찾을 수 없습니다.")
            return

        # 대시보드 포커스
        self.dashboard.lift()
        self.dashboard.focus_force()

        # 전용 백그라운드 스레드에서 Playwright 실행 (스레드 바인딩 유지)
        if not self.scraper:
            self.scraper = ClaudeUsageScraperPlaywright(cookies)
            thread = threading.Thread(target=self._monitoring_loop, daemon=True)
            thread.start()

    def _monitoring_loop(self):
        """전용 스레드에서 Playwright 브라우저 유지 + 주기적 조회"""
        first_fetch = True
        try:
            self.scraper.start()

            while not self._stop_event.is_set():
                print("사용량 데이터 조회 중...")
                try:
                    usage_data = self.scraper.fetch_usage_data()
                    if usage_data:
                        self.dashboard.after(0, lambda d=usage_data: self.dashboard.update_usage_data(d))
                        print("✓ 사용량 데이터 업데이트 완료")
                        first_fetch = False
                    else:
                        if first_fetch:
                            # 세션 만료 → 로그인 필요
                            print("세션이 만료되었습니다. 재로그인 필요.")
                            self.dashboard.after(0, self.show_login)
                            return
                        self.dashboard.after(0, lambda: self.dashboard.show_error("사용량 데이터를 가져올 수 없습니다."))
                        print("✗ 사용량 데이터 조회 실패")
                except Exception as e:
                    print(f"✗ 사용량 조회 오류: {e}")
                    err_msg = str(e)
                    self.dashboard.after(0, lambda m=err_msg: self.dashboard.show_error(f"오류: {m}"))

                # 1분 대기 (중간에 stop 가능)
                self._stop_event.wait(self.update_interval / 1000)

        except Exception as e:
            print(f"모니터링 루프 오류: {e}")
            import traceback
            traceback.print_exc()
        finally:
            self.scraper.stop()


def ensure_playwright_chromium():
    """Playwright Chromium 브라우저가 없으면 자동 설치"""
    try:
        from playwright.sync_api import sync_playwright
        with sync_playwright() as p:
            p.chromium.launch(headless=True).close()
    except Exception:
        print("Chromium 브라우저를 설치합니다...")
        subprocess.run(
            [sys.executable, "-m", "playwright", "install", "chromium"],
            check=True,
        )
        print("✓ Chromium 설치 완료")


def main():
    """메인 함수"""
    ensure_playwright_chromium()
    app = None
    try:
        app = App()
        app.run()
    except KeyboardInterrupt:
        print("\n프로그램 종료")
    except Exception as e:
        print(f"오류 발생: {e}")
        import traceback
        traceback.print_exc()
    finally:
        if app and app.scraper:
            app.scraper.stop()
        sys.exit(0)


if __name__ == "__main__":
    main()
