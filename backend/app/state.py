from dataclasses import dataclass, field


@dataclass
class AppState:
    history: list[dict[str, str]] = field(default_factory=list)
    model: str = "deepseek/deepseek-r1-distill-qwen-32b"


app_state = AppState()
