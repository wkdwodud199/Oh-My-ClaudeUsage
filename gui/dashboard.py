"""메인 대시보드"""
import customtkinter as ctk
from datetime import datetime, timedelta
from typing import Optional
from scraper.usage_playwright import UsageData


# 뷰 모드 상수
VIEW_MAX = 0   # 전체 (현재 세션 + 주간 전체 + Sonnet)
VIEW_MIN = 1   # 최소 (현재 세션만)
VIEW_MID = 2   # 중간 (현재 세션 + 주간 전체)

VIEW_LABELS = {
    VIEW_MAX: "Full",
    VIEW_MIN: "Min",
    VIEW_MID: "Mid",
}

VIEW_SIZES = {
    VIEW_MAX: (380, 480),
    VIEW_MIN: (380, 190),
    VIEW_MID: (380, 340),
}


class DashboardWindow(ctk.CTk):
    """대시보드 메인 창"""

    def __init__(self):
        super().__init__()

        # 다크 모드 설정
        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("blue")

        # 창 설정
        self.title("Oh-my-claudeusage")
        self.geometry("380x480")
        self.resizable(False, False)

        # 상태
        self.usage_data: Optional[UsageData] = None
        self.view_mode = VIEW_MAX
        self.opacity = 1.0
        self.always_on_top = False

        self._create_widgets()

    def _create_widgets(self):
        """위젯 생성"""

        # ── 상단 툴바 ──
        toolbar = ctk.CTkFrame(self, fg_color="gray20", height=36, corner_radius=0)
        toolbar.pack(fill="x")
        toolbar.pack_propagate(False)

        # 뷰 토글 버튼
        self.view_button = ctk.CTkButton(
            toolbar,
            text="Full",
            command=self._toggle_view,
            width=60, height=26,
            font=ctk.CTkFont(family="Inter", size=11),
            fg_color="gray35",
            hover_color="gray45",
            corner_radius=6
        )
        self.view_button.pack(side="left", padx=(10, 0), pady=5)

        # 항상 위 고정 버튼
        self.pin_button = ctk.CTkButton(
            toolbar,
            text="Pin",
            command=self._toggle_pin,
            width=46, height=26,
            font=ctk.CTkFont(family="Inter", size=11),
            fg_color="gray35",
            hover_color="gray45",
            corner_radius=6
        )
        self.pin_button.pack(side="left", padx=(6, 0), pady=5)

        # GitHub 링크 버튼
        github_button = ctk.CTkButton(
            toolbar,
            text="GitHub",
            command=self._open_github,
            width=56, height=26,
            font=ctk.CTkFont(family="Inter", size=11),
            fg_color="gray35",
            hover_color="gray45",
            corner_radius=6
        )
        github_button.pack(side="left", padx=(6, 0), pady=5)

        # 투명도 슬라이더
        self.opacity_slider = ctk.CTkSlider(
            toolbar,
            from_=0.2, to=1.0,
            width=100, height=14,
            command=self._on_opacity_change,
            button_length=12,
            fg_color="gray40",
            progress_color="gray60"
        )
        self.opacity_slider.set(1.0)
        self.opacity_slider.pack(side="right", padx=(0, 10), pady=5)

        # ── 메인 컨텐츠 ──
        self.content_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.content_frame.pack(fill="both", expand=True, padx=16, pady=(10, 0))

        # 헤더
        self.header_label = ctk.CTkLabel(
            self.content_frame,
            text="Plan Usage Limits",
            font=ctk.CTkFont(family="Inter", size=22, weight="bold"),
            anchor="w"
        )
        self.header_label.pack(fill="x", pady=(5, 10))

        # ── 현재 세션 섹션 (항상 표시) ──
        self.session_frame = ctk.CTkFrame(self.content_frame, fg_color="transparent")
        self.session_frame.pack(fill="x")
        self._create_usage_section(self.session_frame, "Current Session", "current_session")

        # ── 주간 전체 섹션 (중간/최대에서 표시) ──
        self.weekly_all_frame = ctk.CTkFrame(self.content_frame, fg_color="transparent")
        self.weekly_all_frame.pack(fill="x")

        self.sep1 = ctk.CTkFrame(self.weekly_all_frame, height=1, fg_color="gray30")
        self.sep1.pack(fill="x", pady=(12, 8))

        weekly_header = ctk.CTkLabel(
            self.weekly_all_frame,
            text="Weekly Limits",
            font=ctk.CTkFont(family="Inter", size=16, weight="bold"),
            anchor="w"
        )
        weekly_header.pack(fill="x", pady=(0, 6))

        self._create_usage_section(self.weekly_all_frame, "All Models", "weekly_all")

        # ── Sonnet 섹션 (최대에서만 표시) ──
        self.weekly_sonnet_frame = ctk.CTkFrame(self.content_frame, fg_color="transparent")
        self.weekly_sonnet_frame.pack(fill="x")

        self.sep2 = ctk.CTkFrame(self.weekly_sonnet_frame, height=1, fg_color="gray30")
        self.sep2.pack(fill="x", pady=(10, 6))

        self._create_usage_section(self.weekly_sonnet_frame, "Sonnet Only", "weekly_sonnet")

        # ── 하단 상태바 ──
        self.status_frame = ctk.CTkFrame(self, fg_color="gray20", height=28, corner_radius=0)
        self.status_frame.pack(fill="x", side="bottom")
        self.status_frame.pack_propagate(False)

        self.status_label = ctk.CTkLabel(
            self.status_frame,
            text="Checking session...",
            font=ctk.CTkFont(family="Inter", size=10),
            text_color="gray"
        )
        self.status_label.pack(pady=4)

    def _create_usage_section(self, parent, title: str, key: str):
        """사용량 섹션 생성"""
        section = ctk.CTkFrame(parent, fg_color="transparent")
        section.pack(fill="x", pady=(4, 4))

        # 상단: 제목 + 퍼센트
        top = ctk.CTkFrame(section, fg_color="transparent")
        top.pack(fill="x")

        # 왼쪽: 제목 + 재설정 시간
        left = ctk.CTkFrame(top, fg_color="transparent")
        left.pack(side="left", fill="x", expand=True)

        title_label = ctk.CTkLabel(
            left,
            text=title,
            font=ctk.CTkFont(family="Inter", size=13, weight="bold"),
            anchor="w"
        )
        title_label.pack(anchor="w")

        reset_label = ctk.CTkLabel(
            left,
            text="",
            font=ctk.CTkFont(family="Inter", size=11),
            text_color="orange",
            anchor="w"
        )
        reset_label.pack(anchor="w")

        # 오른쪽: 퍼센트
        percent_label = ctk.CTkLabel(
            top,
            text="0%",
            font=ctk.CTkFont(family="Inter", size=12),
            text_color="gray",
            anchor="e"
        )
        percent_label.pack(side="right")

        # 진행률 바
        progress = ctk.CTkProgressBar(section, height=8, corner_radius=4)
        progress.pack(fill="x", pady=(4, 0))
        progress.set(0)

        # 참조 저장
        setattr(self, f"{key}_reset_label", reset_label)
        setattr(self, f"{key}_percent_label", percent_label)
        setattr(self, f"{key}_progress", progress)

    # ── 뷰 토글 ──

    def _toggle_view(self):
        """뷰 모드 순환: 전체 → 최소 → 중간 → 전체"""
        next_mode = {VIEW_MAX: VIEW_MIN, VIEW_MIN: VIEW_MID, VIEW_MID: VIEW_MAX}
        self.view_mode = next_mode[self.view_mode]
        self._apply_view()

    def _apply_view(self):
        """현재 뷰 모드에 따라 섹션 표시/숨기기 + 크기 조절"""
        mode = self.view_mode

        # 섹션 표시/숨기기
        if mode == VIEW_MIN:
            self.weekly_all_frame.pack_forget()
            self.weekly_sonnet_frame.pack_forget()
        elif mode == VIEW_MID:
            self.weekly_sonnet_frame.pack_forget()
            # weekly_all이 빠져있으면 다시 추가
            self.weekly_all_frame.pack(fill="x", after=self.session_frame)
        else:  # VIEW_MAX
            self.weekly_all_frame.pack(fill="x", after=self.session_frame)
            self.weekly_sonnet_frame.pack(fill="x", after=self.weekly_all_frame)

        # 버튼 텍스트 업데이트
        self.view_button.configure(text=VIEW_LABELS[mode])

        # 창 크기 조절
        w, h = VIEW_SIZES[mode]
        self.geometry(f"{w}x{h}")

    # ── 항상 위 고정 ──

    def _toggle_pin(self):
        """항상 위 고정 토글"""
        self.always_on_top = not self.always_on_top
        self.attributes('-topmost', self.always_on_top)
        if self.always_on_top:
            self.pin_button.configure(fg_color="#4299e1", text="Pin")
        else:
            self.pin_button.configure(fg_color="gray35", text="Pin")

    # ── GitHub ──

    def _open_github(self):
        """Open GitHub repo in browser"""
        import webbrowser
        webbrowser.open("https://github.com/wkdwodud199/Oh-My-ClaudeUsage")

    # ── 투명도 ──

    def _on_opacity_change(self, value: float):
        """투명도 슬라이더 변경"""
        self.opacity = value
        self.attributes('-alpha', value)

    # ── 데이터 업데이트 ──

    def update_usage_data(self, data: UsageData):
        """사용량 데이터 업데이트"""
        self.usage_data = data

        self._update_section(
            "current_session",
            data.current_session_usage,
            data.current_session_limit,
            data.current_session_reset
        )
        self._update_section(
            "weekly_all",
            data.weekly_all_usage,
            data.weekly_all_limit,
            data.weekly_all_reset
        )
        self._update_section(
            "weekly_sonnet",
            data.weekly_sonnet_usage,
            data.weekly_sonnet_limit,
            data.weekly_sonnet_reset
        )

        if data.last_updated:
            self.status_label.configure(
                text=f"Last updated: {data.last_updated.strftime('%H:%M:%S')}",
                text_color="gray"
            )

    def _update_section(self, key: str, usage: int, limit: int, reset_time: Optional[datetime]):
        """섹션 업데이트"""
        percent = (usage / limit * 100) if limit > 0 else 0

        reset_label = getattr(self, f"{key}_reset_label")
        percent_label = getattr(self, f"{key}_percent_label")
        progress = getattr(self, f"{key}_progress")

        if reset_time:
            reset_label.configure(text=self._format_reset_time(reset_time))
        else:
            reset_label.configure(text="")

        percent_label.configure(text=f"{int(percent)}%")

        # 색상 변화: 낮음=초록, 중간=노랑, 높음=빨강
        if percent < 60:
            progress.configure(progress_color="#4ade80")
        elif percent < 80:
            progress.configure(progress_color="#facc15")
        else:
            progress.configure(progress_color="#f87171")

        progress.set(percent / 100)

    def _format_reset_time(self, reset_time: datetime) -> str:
        """재설정 시간 포맷팅"""
        if reset_time.tzinfo is not None:
            from datetime import timezone
            now = datetime.now(timezone.utc)
        else:
            now = datetime.now()

        reset_naive = reset_time.replace(tzinfo=None) if reset_time.tzinfo else reset_time
        now_naive = now.replace(tzinfo=None) if now.tzinfo else now
        diff = reset_naive - now_naive

        if diff.total_seconds() < 0:
            return "Pending reset"
        elif diff.total_seconds() < 3600:
            minutes = int(diff.total_seconds() / 60)
            return f"Resets in {minutes}m"
        elif diff.total_seconds() < 86400:
            hours = int(diff.total_seconds() / 3600)
            minutes = int((diff.total_seconds() % 3600) / 60)
            return f"Resets in {hours}h {minutes}m"
        else:
            weekdays = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
            weekday = weekdays[reset_naive.weekday()]
            time_str = reset_naive.strftime("%I:%M %p")
            return f"Resets {weekday} {time_str}"

    def show_error(self, message: str):
        """에러 메시지 표시"""
        self.status_label.configure(text=f"Error: {message}", text_color="red")
