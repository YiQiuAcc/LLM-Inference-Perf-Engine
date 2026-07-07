DEFAULT_BASE_URL = "http://localhost:11434"
DEFAULT_MODEL = "deepseek-r1:7b"
DEFAULT_CONCURRENCY = 50
DEFAULT_DURATION = 120
DEFAULT_TIMEOUT = 600
DEFAULT_STREAM = False
DEFAULT_GRADIENT = False

LONG_TEXT_PROMPT = (
    "请详细解释人工智能大语言模型的工作原理"
    "包括 Transformer 架构、注意力机制和训练过程。"
)

SHORT_TEXT_PROMPT = "你好, 请做一下自我介绍。"

TECHNICAL_PROMPT = (
    "请详细解释量子计算的基本原理, "
    "包括量子比特、量子纠缠、量子叠加以及量子门操作, "
    "不少于500字。"
)

GRADIENT_CONCURRENCY_LEVELS = "10,30,50,80,100"
