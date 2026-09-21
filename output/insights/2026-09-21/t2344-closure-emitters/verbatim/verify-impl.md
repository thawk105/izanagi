# 親が repo 外で実行した script の逐語 (`verify_impl.py`)

```python
"""親の検算: 実装が裁定 §3・§4 どおりか (production を import せず AST と bytes で確かめる)。

1. 現行 tuple が closure-head.json の proposed と全順序一致 (96)。
2. T2344_EXACT85_… が変更前の現行 85 と全順序一致し、独立 literal (slice/連結でない) であること。
3. 歴史 scope 2 定数が「変更前の現行 2 定数」と UTF-8 bytes で一致すること。
4. 現行 scope 2 定数が裁定の確定文字列であること。
5. test 側の固定値 4 値が裁定 §4 と一致すること。
6. exact-63 / 62 / 24 の literal・validator が変更前と bytes 一致すること。
"""
import ast
import json
import subprocess
import sys

W = "/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2344-source-bound-emitters"
J = "/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2344-source-bound-emitters"
BASE = "71e572b3cbb46ab6427512c3edafe91c2a746f37"
head = json.load(open(J + "/closure-head.json"))
oracle = json.load(open(J + "/oracle-fixed-values.json"))
out = {}


def show(commit, rel):
    return subprocess.run(["git", "show", f"{commit}:{rel}"], cwd=W, capture_output=True, text=True, check=True).stdout


def module_consts(src, names):
    mod = ast.parse(src)
    found = {}
    for node in mod.body:
        if isinstance(node, ast.Assign):
            for t in node.targets:
                if isinstance(t, ast.Name) and t.id in names:
                    found[t.id] = node.value
    return found


now_lock = open(W + "/orchestrator/campaign/campaign_lock.py", encoding="utf-8").read()
old_lock = show(BASE, "orchestrator/campaign/campaign_lock.py")
names = ("CONTRACT_LOADER_RELATIVE_PATHS", "T2344_EXACT85_CONTRACT_LOADER_RELATIVE_PATHS",
         "T2429_EXACT63_CONTRACT_LOADER_RELATIVE_PATHS", "T733_EXACT62_CONTRACT_LOADER_RELATIVE_PATHS",
         "PRE_T733_CONTRACT_LOADER_RELATIVE_PATHS")
new_c = module_consts(now_lock, names)
old_c = module_consts(old_lock, names)

cur = [ast.literal_eval(e) for e in new_c["CONTRACT_LOADER_RELATIVE_PATHS"].elts]
out["current_tuple_len"] = len(cur)
out["current_equals_proposed"] = cur == head["proposed"]
ex85 = [ast.literal_eval(e) for e in new_c["T2344_EXACT85_CONTRACT_LOADER_RELATIVE_PATHS"].elts]
old_cur = [ast.literal_eval(e) for e in old_c["CONTRACT_LOADER_RELATIVE_PATHS"].elts]
out["exact85_len"] = len(ex85)
out["exact85_equals_previous_current"] = ex85 == old_cur
out["exact85_is_plain_tuple_literal"] = isinstance(new_c["T2344_EXACT85_CONTRACT_LOADER_RELATIVE_PATHS"], ast.Tuple) and all(
    isinstance(e, ast.Constant) for e in new_c["T2344_EXACT85_CONTRACT_LOADER_RELATIVE_PATHS"].elts)
for n in ("T2429_EXACT63_CONTRACT_LOADER_RELATIVE_PATHS", "T733_EXACT62_CONTRACT_LOADER_RELATIVE_PATHS",
          "PRE_T733_CONTRACT_LOADER_RELATIVE_PATHS"):
    out[f"{n}_unchanged"] = ([ast.literal_eval(e) for e in new_c[n].elts]
                             == [ast.literal_eval(e) for e in old_c[n].elts])

now_adm = open(W + "/orchestrator/campaign/artifact_admission.py", encoding="utf-8").read()
old_adm = show(BASE, "orchestrator/campaign/artifact_admission.py")
snames = ("CAMPAIGN_VERIFIER_EPOCH_SCOPE", "CAMPAIGN_VERIFIER_EPOCH_EXCLUDED_SCOPE",
          "T2344_EXACT85_CAMPAIGN_VERIFIER_EPOCH_SCOPE", "T2344_EXACT85_CAMPAIGN_VERIFIER_EPOCH_EXCLUDED_SCOPE",
          "T2429_EXACT63_CAMPAIGN_VERIFIER_EPOCH_SCOPE", "T2429_EXACT63_CAMPAIGN_VERIFIER_EPOCH_EXCLUDED_SCOPE",
          "T733_EXACT62_CAMPAIGN_VERIFIER_EPOCH_SCOPE", "PRE_T733_CAMPAIGN_VERIFIER_EPOCH_SCOPE")
new_s = {k: ast.literal_eval(v) for k, v in module_consts(now_adm, snames).items()}
old_s = {k: ast.literal_eval(v) for k, v in module_consts(old_adm, snames).items()}
out["exact85_scope_bytes_equal_previous_current"] = (
    new_s["T2344_EXACT85_CAMPAIGN_VERIFIER_EPOCH_SCOPE"].encode() == old_s["CAMPAIGN_VERIFIER_EPOCH_SCOPE"].encode()
    and new_s["T2344_EXACT85_CAMPAIGN_VERIFIER_EPOCH_EXCLUDED_SCOPE"].encode()
    == old_s["CAMPAIGN_VERIFIER_EPOCH_EXCLUDED_SCOPE"].encode())
out["exact63_scope_unchanged"] = (new_s["T2429_EXACT63_CAMPAIGN_VERIFIER_EPOCH_SCOPE"]
                                  == old_s["T2429_EXACT63_CAMPAIGN_VERIFIER_EPOCH_SCOPE"])
out["current_scope"] = new_s["CAMPAIGN_VERIFIER_EPOCH_SCOPE"]
out["current_excluded_scope_head"] = new_s["CAMPAIGN_VERIFIER_EPOCH_EXCLUDED_SCOPE"][:40]
EXPECT_SCOPE = (
    "enforcement source closure (curated exact 96 path; source-import 推移閉包ではない; "
    "発見集合は収載 tuple を起点に静的 import と package 初期化を辿った集合であり、"
    "2026-09-21 (5efd69367 の source 木、本版の 96 path を起点) の実測では 173 module、うち収載 96)")
out["current_scope_matches_ruling"] = new_s["CAMPAIGN_VERIFIER_EPOCH_SCOPE"] == EXPECT_SCOPE
out["current_excluded_starts_with_77"] = new_s["CAMPAIGN_VERIFIER_EPOCH_EXCLUDED_SCOPE"].startswith("同実測の発見集合の未収載 77 module、")
out["excluded_tail_unchanged"] = (new_s["CAMPAIGN_VERIFIER_EPOCH_EXCLUDED_SCOPE"].split("、", 1)[1]
                                  == old_s["CAMPAIGN_VERIFIER_EPOCH_EXCLUDED_SCOPE"].split("、", 1)[1])

test_src = open(W + "/orchestrator/tests/test_artifact_admission.py", encoding="utf-8").read()
for label, value in (("fixed_synthetic_e1_epoch_96", oracle["fixed_synthetic_e1_epoch_96"]),
                     ("fixed_ordered_closure_paths_sha256_96", oracle["fixed_ordered_closure_paths_sha256_96"]),
                     ("exact85_fixed_epoch", oracle["exact85_fixed_epoch"]),
                     ("exact85_ordered_sha256", oracle["exact85_ordered_sha256"])):
    out[f"test_has_{label}"] = value in test_src
out["test_has_stale_85_count_assert"] = "== 85" in test_src
out["t671_has_960"] = "960" in open(W + "/orchestrator/tests/test_t671_source_binding.py", encoding="utf-8").read()
out["t671_has_850"] = "850" in open(W + "/orchestrator/tests/test_t671_source_binding.py", encoding="utf-8").read()

json.dump(out, open(J + "/verify-impl.json", "w"), indent=2, ensure_ascii=False)
bad = [k for k, v in out.items() if isinstance(v, bool) and v is not (k not in ("test_has_stale_85_count_assert", "t671_has_850"))]
print(json.dumps(out, indent=2, ensure_ascii=False))
print("SUSPECT:", bad)
sys.exit(0)
```
