
import os
from openai import OpenAI

client = OpenAI(
    api_key = os.environ.get("DEEPSEEK_API_KEY"),
    base_url = "https://api.deepseek.com"
)

SYSTEM_PROMPT = """
你是一个资深的 Linux 内核测试专家（Perf Test Failure Analyst Agent）。
你的任务是对专门的 perf 工具链测试失败日志进行深度的根因分析。

请遵循以下核心设计原则：
1. 可解释性第一：你必须给出完整的推理链条和证据支持（例如：引发失败的具体系统调用、日志中的关键时间戳或异常指标）。
2. 严谨性：如果判断是真实的 Kernel Bug / Regression，请给出置信度打分（0-100）。低于 80 分时提示需要人工审核。
3. 给出行动建议：如果是环境或已知问题，给出具体的排查命令。

请用以下 JSON 格式输出结果：
{
  "is_kernel_bug": true/false,
  "confidence_score": 85,
  "root_cause": "简述根本原因",
  "evidence_chain": ["证据1...", "证据2..."],
  "recommended_action": "建议工程师下一步执行的排查或修复动作"
}
"""

def analyze_failure_with_llm(log_context):
    response = client.chat.completions.create(
        model = "deepseek-v4-flash",
        messages = [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": f"Please analyze the following test failure log: \n\n{log_context}"}
        ],
        response_format = {"type": "json_object"},
        temperature = 0.2
    )
    return response.choices[0].message.content
