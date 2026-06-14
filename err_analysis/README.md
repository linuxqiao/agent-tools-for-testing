# Perf 测试失败分析 Pipeline

一套两阶段（规则引擎 + LLM 深度分析）的自动化 **perf 工具链测试失败日志分析系统**，能够快速分类故障根因并给出修复建议。

## 架构概览

```
┌─────────────────────────────────────────────────────────────┐
│                run_analysis_pipeline(fail_log)              │
│                       main_pipeline.py                      │
└──────────────────────────┬──────────────────────────────────┘
                           │
                           ▼
              ┌─────────────────────────┐
              │  Phase 1: 规则引擎      │
              │  quick_classify()        │  ← classifier.py
              │  正则匹配 PATTERN_DB     │
              └───────────┬─────────────┘
                          │
              是否匹配且置信度 ≥ 80%？
                    │           │
                  是的         否
                    │           │
                    ▼           ▼
              ┌──────────┐  ┌──────────────────────────────┐
              │ 直接返回  │  │ Phase 2: DeepSeek LLM 深度分析│
              │ 规则结果   │  │ analyze_failure_with_llm()   │  ← analyst_agent.py
              └──────────┘  │ 调用 deepseek-v4-flash 模型   │
                            └──────────────┬───────────────┘
                                           ▼
                              ┌──────────────────────────┐
                              │ 置信度 < 80 分？          │
                              │  → 标记为「需要人工审核」  │
                              └──────────────────────────┘
```

### 工作流程

1. **接收失败日志** → `run_analysis_pipeline(fail_log)`
2. **Phase 1 — 规则引擎快检**：用预定义的正则规则快速匹配已知问题模式。若匹配且置信度 ≥ 80%，直接返回结果，**不调用 LLM**，节省时间和费用。
3. **Phase 2 — LLM 深度分析**：规则引擎无法高置信度判定时，调用 DeepSeek 模型进行深度根因分析，输出结构化 JSON 报告。
4. **置信度检查**：LLM 返回的置信度低于 80 分时，自动标记为需要人工专家介入。

## 模块说明

### `main_pipeline.py` — 主流程入口

负责编排整个分析流程：

- `run_analysis_pipeline(fail_log)` — 接收原始失败日志字符串，依次执行两阶段分析
- 命令行入口：直接运行时使用内置的示例日志进行测试

### `classifier.py` — 规则引擎（Phase 1）

基于正则表达式匹配的轻量级快速分类器。

**预置规则（`PATTERN_DB`）：**

| 匹配关键词 | 分类 | 置信度 | 建议动作 |
|-----------|------|--------|---------|
| `Operation not permitted` | 权限 / 配置 | 90% | 检查 perf_event_paranoid、capability |
| `Command not found` | 脚本 / 环境 | 90% | 检查工具依赖与路径 |
| `Killed` | 资源 / OOM | 70% | 检查内存使用，考虑增加 buffer |

- `quick_classify(log_exit)` — 对日志进行模式匹配，返回匹配到的规则或 `None`

> **扩展规则**：只需在 `PATTERN_DB` 列表中追加新的规则字典即可。

### `analyst_agent.py` — LLM 深度分析代理（Phase 2）

基于 DeepSeek API 的智能分析代理：

- 调用 `deepseek-v4-flash` 模型
- 使用结构化输出 (`response_format = json_object`)
- 系统提示词要求：可解释性优先、严谨置信度评分、给出具体排查命令
- 输出 JSON 格式：`is_kernel_bug`, `confidence_score`, `root_cause`, `evidence_chain`, `recommended_action`

**环境要求：** 需设置环境变量 `DEEPSEEK_API_KEY`。

## 快速开始

### 1. 安装依赖

```bash
pip install openai
```

### 2. 设置 API Key

```bash
export DEEPSEEK_API_KEY="your_api_key_here"
```

### 3. 运行

```bash
python main_pipeline.py
```

或者在自己的代码中导入使用：

```python
from main_pipeline import run_analysis_pipeline

log = "perf stat: Operation not permitted"
result = run_analysis_pipeline(log)
print(result)
```

## 输出示例

### Phase 1 命中规则（置信度 ≥ 80%）

```
=== Step 1: running Phase 1 quick pattern matching ===
Successfully intercepted by the rules engine! category: Script / Environment (confidence: 90%)
Suggestion action: Check the tools dependency and path if it is right.
```

### Phase 2 LLM 分析

```
=== Step 1: running Phase 1 quick pattern matching ===
The rules engine is unable to resolve the issue with high confidence, and is activating the Phase 2 DeepSeek deep inference agent...

=== Step 2: DeepSeek analyse report ===
{
  "is_kernel_bug": false,
  "confidence_score": 75,
  "root_cause": "简述根本原因",
  "evidence_chain": ["证据1...", "证据2..."],
  "recommended_action": "建议工程师下一步执行的排查或修复动作"
}

[Need Manual Review] Agent confidence level is less than 80 points, and it has been assigned to a human expert!
```

## 设计原则

- **可解释性第一**：LLM 输出必须包含完整的推理链条和证据支持
- **成本优化**：常见问题由轻量级规则引擎拦截，无需调用 LLM
- **分级处理**：低置信度结果自动升级到人工审核，避免误判
- **扩展友好**：规则库和 LLM Prompt 均可独立扩展

## 自定义扩展

### 添加新规则

在 `classifier.py` 的 `PATTERN_DB` 中追加规则：

```python
{
    "pattern": r"新的匹配模式",
    "category": "分类名称",
    "confidence": 85,
    "suggestion": "建议修复动作"
}
```

### 调整 LLM 分析逻辑

修改 `analyst_agent.py` 中的 `SYSTEM_PROMPT` 即可改变分析行为、输出格式或语言风格。

## 系统要求

- Python 3.8+
- `openai` Python 包
- DeepSeek API Key（或兼容 OpenAI 接口的其他 LLM 服务）
