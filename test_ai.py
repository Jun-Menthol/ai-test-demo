import requests
import json
import re
import time
from datetime import datetime

# ===== 配置 =====
API_KEY = "sk-xsrclpqmirlnvtywpcqdbyrucsaubdudqajhwqcewcpjxdny"  # 替换成你的密钥
MODEL = "Qwen/Qwen2.5-7B-Instruct"
# ================

def call_ai(prompt):
    url = "https://api.siliconflow.cn/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json"
    }
    data = {
        "model": MODEL,
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0.7
    }
    try:
        response = requests.post(url, headers=headers, json=data, timeout=30)
        if response.status_code == 200:
            result = response.json()
            return result["choices"][0]["message"]["content"]
        else:
            return f"[ERROR] 状态码: {response.status_code}"
    except Exception as e:
        return f"[ERROR] {str(e)}"

def test_case(prompt, expected_keywords=None, min_length=5):
    print(f"\n📝 测试: {prompt[:30]}...")
    reply = call_ai(prompt)
    time.sleep(0.5)
    
    # 保留中文、英文、数字
    clean_reply = re.sub(r'[^\u4e00-\u9fa5a-zA-Z0-9，。！？、：；""\'\n]', '', reply)
    
    passed = True
    reasons = []
    
    if len(clean_reply.strip()) < min_length:
        passed = False
        reasons.append(f"回复过短(仅{len(clean_reply.strip())}字)")
    
    # 关键词检查：包含任一即通过
    if expected_keywords:
        has_any = any(kw in clean_reply for kw in expected_keywords)
        if not has_any:
            passed = False
            reasons.append(f"未包含任一关键词: {expected_keywords}")
    
    if "[ERROR]" in reply:
        passed = False
        reasons.append("API调用报错")
    
    status = "✅ PASS" if passed else "❌ FAIL"
    print(f"  结果: {status}")
    print(f"  回复预览: {clean_reply[:50] if clean_reply else '(空)'}...")
    if not passed:
        print(f"  原因: {', '.join(reasons)}")
    
    return {
        "prompt": prompt,
        "reply": clean_reply,
        "passed": passed,
        "reasons": reasons
    }

print("=" * 50)
print(f"🤖 AI测试执行开始 - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
print("=" * 50)

# 预热
print("\n[预热] 测试API连通性...")
test_reply = call_ai("你好")
if "[ERROR]" in test_reply:
    print(f"[预热失败] {test_reply}")
    exit()
else:
    print(f"[预热成功] 回复: {test_reply[:50]}...")

# 测试用例（关键词支持多个备选）
test_prompts = [
   {"prompt": "你好，请用一句话介绍自己", "keywords": ["模型", "语言", "大型"], "min_length": 5},
    {"prompt": "1+1等于几？", "min_length": 2},  # 只要回复不少于2个字就算通过
    {"prompt": "写一句关于深圳的诗", "min_length": 5},
    {"prompt": "你的名字是什么？", "keywords": ["Qwen", "助手"], "min_length": 5},
    {"prompt": "请用中文回答：Hello", "keywords": ["你好", "您好"], "min_length": 3},
]

results = []
for case in test_prompts:
    result = test_case(
        case["prompt"],
        expected_keywords=case.get("keywords"),
        min_length=case.get("min_length", 5)
    )
    results.append(result)

# 报告
print("\n" + "=" * 50)
print("📊 测试报告")
print("=" * 50)

total = len(results)
passed = sum(1 for r in results if r["passed"])
failed = total - passed
pass_rate = (passed / total) * 100 if total > 0 else 0

print(f"总用例数: {total}")
print(f"✅ 通过: {passed}")
print(f"❌ 失败: {failed}")
print(f"通过率: {pass_rate:.1f}%")

if failed > 0:
    print("\n失败用例详情:")
    for r in results:
        if not r["passed"]:
            print(f"  ❌ {r['prompt'][:30]}... -> {', '.join(r['reasons'])}")

report_file = f"test_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
with open(report_file, "w", encoding="utf-8") as f:
    f.write(f"AI测试报告 - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
    f.write("=" * 50 + "\n")
    f.write(f"总用例: {total} | 通过: {passed} | 失败: {failed} | 通过率: {pass_rate:.1f}%\n\n")
    for r in results:
        f.write(f"用例: {r['prompt']}\n")
        f.write(f"回复: {r['reply'][:100]}\n")
        f.write(f"结果: {'✅ PASS' if r['passed'] else '❌ FAIL'}\n")
        if not r['passed']:
            f.write(f"原因: {', '.join(r['reasons'])}\n")
        f.write("-" * 30 + "\n")

print(f"\n📄 详细报告已保存至: {report_file}")
print("=" * 50)