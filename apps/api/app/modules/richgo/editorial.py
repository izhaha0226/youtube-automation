from __future__ import annotations

KIM_KIWON_PRINCIPLES: tuple[str, ...] = (
    "가슴 뛰는 목표가 있는 콘텐츠를 우선한다.",
    "운에 기대기보다 통제력과 영향력이 있는 해석을 선호한다.",
    "쉬운 길보다 어려운 선택을 통해 성장하는 방향을 택한다.",
    "시련과 실패도 성장과 학습의 재료로 바꾼다.",
    "독서와 축적된 지식이 판단력의 차이를 만든다고 본다.",
    "겉보다 본질 중심의 해석을 우선한다.",
)

RICHGO_EDITORIAL_RULES: tuple[str, ...] = (
    "경제 이슈는 반드시 부동산 실수요자 관점으로 번역한다.",
    "단순 뉴스 요약보다 지금 어떻게 판단해야 하는지를 우선한다.",
    "낚시성 공포 조장보다 책임 있는 표현과 체크포인트를 남긴다.",
    "겉보기 화려함보다 본질, 지속성, 실행 가능한 포인트를 중시한다.",
)


def philosophy_context() -> str:
    return "\n".join(f"- {item}" for item in KIM_KIWON_PRINCIPLES)


def editorial_rules_context() -> str:
    return "\n".join(f"- {item}" for item in RICHGO_EDITORIAL_RULES)
