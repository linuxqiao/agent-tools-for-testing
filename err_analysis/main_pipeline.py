
from classifier import quick_classify
from analyst_agent import analyze_failure_with_llm
import json

def run_analysis_pipeline(fail_log):
    print("=== Step 1: running Phase 1 quick pattern matching ===")
    fast_result = quick_classify(fail_log)

    if fast_result and fast_result["confidence"] >= 80:
        print(f"Successfully intercepted by the rules engine! category: {fast_result['category']} (confidence: {fast_result['confidence']}%)")
        print(f"Suggestion action: {fast_result['suggestion']}")
        return fast_result

    print("The rules engine is unable to resolve the issue with high confidence, and is activating the Phase 2 DeepSeek deep interencde agent...")
    llm_raw_result = analyze_failure_with_llm(fail_log)
    llm_result = json.loads(llm_raw_result)

    print("\n=== Step 2: DeepSeek analyse report ===")
    print(json.dumps(llm_result, indent = 2, ensure_ascii = False))

    if llm_result.get("confidence_score", 0) < 80:
        print("\n[Need Manual Review] Agent confidence level is less than 80 points, and it has been assigned to a human expert!")

    return llm_result

if __name__ == "__main__":
    #sample_log = "perf interrupt: caught segfault at 0000000000000020 ip 00007f9c12a3b4c5 error 4 in perf[7f9c12a00000+40000]"
    sample_log = "perf c2c --unknown: Command not found"
    run_analysis_pipeline(sample_log)
