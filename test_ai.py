"""
AI 自动化测试框架 - 最终完整版
作者：你的名字
功能：对大语言模型 API 进行自动化测试，支持批量用例执行、质量评估、报告生成
技术栈：Python 3.12 + Requests
"""

import requests
import json
import re
import time
from datetime import datetime

# ============================================================
# 配置区（使用前请修改）
# ============================================================
API_KEY = "你的硅基流动API密钥"
MODEL = "Qwen/Qwen2.5-7B-Instruct"  # 被测模型
TIMEOUT = 30  # API 超时时间（秒）
DELAY = 0.5  # 用例间延时（防止限流）
# ============================================================


def call_ai(prompt):
    """
    调用大模型 API，返回回复内容
    参数：
        prompt: 用户输入的提示词
    返回：
        模型回复的文本内容，或错误信息
    """
    url = "https://api.siliconflow.cn/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json; charset=utf-8"
    }
    data = {
        "model": MODEL,
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0.7
    }

    try:
        # 手动编码确保 UTF-8
        json_data = json.dumps(data, ensure_ascii=False).encode('utf-8')
        response = requests.post(url, headers=headers, data=json_data, timeout=TIMEOUT)

        if response.status_code == 200:
            result = response.json()
            return result["choices"][0]["message"]["content"]
        else:
            return f"[ERROR] HTTP状态码: {response.status_code}"

    except requests.exceptions.Timeout:
        return "[ERROR] 请求超时"
    except requests.exceptions.ConnectionError:
        return "[ERROR] 网络连接失败"
    except Exception as e:
        return f"[ERROR] {str(e)}"


def clean_text(text):
    """
    清洗文本，保留中文、英文、数字和常见标点
    参数：
        text: 原始文本
    返回：
        清洗后的文本
    """
    # 保留中文、英文、数字、常见标点
    pattern = r'[^\u4e00-\u9fa5a-zA-Z0-9，。！？、：；""\'\n]'
    return re.sub(pattern, '', text)


def test_case(prompt, expected_keywords=None, min_length=5):
    """
    执行单个测试用例
    参数：
        prompt: 测试提示词
        expected_keywords: 期望包含的关键词列表（含任一即可）
        min_length: 最小回复字数
    返回：
        测试结果字典
    """
    print(f"\n📝 用例: {prompt[:35]}...")

    # 调用 API
    reply = call_ai(prompt)

    # 延时防止限流
    time.sleep(DELAY)

    # 清洗回复
    clean_reply = clean_text(reply)

    # 判断结果
    passed = True
    reasons = []

    # 检查1：是否 API 报错
    if "[ERROR]" in reply:
        passed = False
        reasons.append("API调用失败")

    # 检查2：字数是否达标
    word_count = len(clean_reply.strip())
    if word_count < min_length:
        passed = False
        reasons.append(f"回复过短（仅{word_count}字，需≥{min_length}字）")

    # 检查3：是否包含预期关键词（含任一即可）
    if expected_keywords and passed:  # 如果已经失败就不用重复检查了
        has_any = any(kw in clean_reply for kw in expected_keywords)
        if not has_any:
            passed = False
            reasons.append(f"未包含任一关键词：{expected_keywords}")

    # 输出结果
    status = "✅ PASS" if passed else "❌ FAIL"
    print(f"  结果: {status}")
    print(f"  回复预览: {clean_reply[:60] if clean_reply else '(空)'}")
    if not passed:
        print(f"  原因: {'；'.join(reasons)}")

    return {
        "prompt": prompt,
        "reply": clean_reply,
        "passed": passed,
        "reasons": reasons,
        "word_count": word_count
    }


def generate_report(results, start_time):
    """
    生成测试报告（控制台输出 + 文件保存）
    参数：
        results: 测试结果列表
        start_time: 测试开始时间
    """
    total = len(results)
    passed_count = sum(1 for r in results if r["passed"])
    failed_count = total - passed_count
    pass_rate = round((passed_count / total) * 100, 1) if total > 0 else 0

    # ===== 控制台输出 =====
    print("\n" + "=" * 60)
    print("📊 测试报告")
    print("=" * 60)
    print(f"  总用例数: {total}")
    print(f"  ✅ 通过: {passed_count}")
    print(f"  ❌ 失败: {failed_count}")
    print(f"  通过率: {pass_rate}%")

    if failed_count > 0:
        print("\n  失败详情:")
        for r in results:
            if not r["passed"]:
                print(f"    ❌ {r['prompt'][:30]}... → {'；'.join(r['reasons'])}")

    # ===== 保存文件 =====
    filename = f"test_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
    with open(filename, "w", encoding="utf-8") as f:
        f.write("=" * 60 + "\n")
        f.write("AI 自动化测试报告\n")
        f.write(f"生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"被测模型: {MODEL}\n")
        f.write("=" * 60 + "\n\n")

        f.write(f"总用例数: {total}\n")
        f.write(f"通过数: {passed_count}\n")
        f.write(f"失败数: {failed_count}\n")
        f.write(f"通过率: {pass_rate}%\n\n")

        f.write("-" * 60 + "\n")
        f.write("详细结果:\n")
        f.write("-" * 60 + "\n")
        for i, r in enumerate(results, 1):
            f.write(f"\n[{i}] 用例: {r['prompt']}\n")
            f.write(f"    回复: {r['reply'][:100]}\n")
            f.write(f"    字数: {r['word_count']}\n")
            f.write(f"    结果: {'✅ PASS' if r['passed'] else '❌ FAIL'}\n")
            if not r['passed']:
                f.write(f"    原因: {'；'.join(r['reasons'])}\n")

    print(f"\n📄 详细报告已保存至: {filename}")
    print("=" * 60)

    return {"total": total, "passed": passed_count, "failed": failed_count, "pass_rate": pass_rate}


def run_tests():
    """
    执行所有测试用例
    """
    print("=" * 60)
    print("🤖 AI 自动化测试框架")
    print(f"  启动时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"  被测模型: {MODEL}")
    print("=" * 60)

    # ===== 预热测试 =====
    print("\n[预热] 检查 API 连通性...")
    warmup_reply = call_ai("你好")
    if "[ERROR]" in warmup_reply:
        print(f"[预热失败] {warmup_reply}")
        print("请检查: 1. API密钥是否正确 2. 网络是否正常")
        return
    print(f"[预热成功] 回复: {warmup_reply[:40]}...")

    # ===== 测试用例集 =====
    test_cases = [
      {"prompt": "你好，请用一句话介绍自己", "min_length": 5},  # 只检查字数，不检查关键词
        {"prompt": "1+1等于几？", "keywords": ["2", "二", "等于"], "min_length": 2},
        {"prompt": "写一句关于深圳的诗", "min_length": 5},
        {"prompt": "你的名字是什么？", "keywords": ["Qwen", "通义"], "min_length": 3},
        {"prompt": "请用中文回答：Hello", "keywords": ["你好", "您好"], "min_length": 3},
    ]

    # ===== 执行测试 =====
    results = []
    for case in test_cases:
        result = test_case(
            prompt=case["prompt"],
            expected_keywords=case.get("keywords"),
            min_length=case.get("min_length", 5)
        )
        results.append(result)

    # ===== 生成报告 =====
    generate_report(results, datetime.now())

    print("\n🎉 测试执行完成！")
    print("GitHub: https://github.com/你的用户名/ai-test-demo")


# ============================================================
# 程序入口
# ============================================================
if __name__ == "__main__":
    run_tests()
