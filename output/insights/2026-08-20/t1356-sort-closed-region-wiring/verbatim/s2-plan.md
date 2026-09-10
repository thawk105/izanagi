## 総括

推奨は、5項目を単一の gallery 型17へ集約する案です。`auditor.md` の追記、schema 上限17、auditor gate の受理集合、3つの review pin、生成 adapter、境界テストを1実装単位として扱います。

`coder-v4-autonomous-sort.md` は変更しません。CC variant の受理集合にも変更を加えません。

## 1. pin 閉包の独立検算

| file:line | 検算結果・提案 |
|---|---|
| [.claude/agents/auditor.md:58](/work/1/SFC/tanab/izanagi/.claude/worktrees/t1356-sort-closed-region-wiring/.claude/agents/auditor.md:58) | 型13〜16、入力節、checklist 11〜13を確認。型17を型16の直後、checklist 14を項目13の直後へ追加。 |
| [orchestrator/codex_roles/manifest.json:122](/work/1/SFC/tanab/izanagi/.claude/worktrees/t1356-sort-closed-region-wiring/orchestrator/codex_roles/manifest.json:122) | `violations.items.properties.type.maximum` は16。17へ変更。 |
| [orchestrator/codex_roles/review_ledger.py:16](/work/1/SFC/tanab/izanagi/.claude/worktrees/t1356-sort-closed-region-wiring/orchestrator/codex_roles/review_ledger.py:16) | auditor.md の byte SHA pin。auditor.md 編集後に更新。 |
| [orchestrator/codex_roles/review_ledger.py:38](/work/1/SFC/tanab/izanagi/.claude/worktrees/t1356-sort-closed-region-wiring/orchestrator/codex_roles/review_ledger.py:38) | `roles.auditor` 全体の canonical SHA pin。manifest 編集後に更新。 |
| [orchestrator/codex_roles/review_ledger.py:83](/work/1/SFC/tanab/izanagi/.claude/worktrees/t1356-sort-closed-region-wiring/orchestrator/codex_roles/review_ledger.py:83) | auditor output schema の canonical SHA pin。manifest 編集後に更新。 |
| [orchestrator/campaign/auditor_gate.py:29](/work/1/SFC/tanab/izanagi/.claude/worktrees/t1356-sort-closed-region-wiring/orchestrator/campaign/auditor_gate.py:29) | `_AUDITOR_VIOLATION_TYPES` を `frozenset(range(1, 18))` へ変更。 |
| [.codex/role-adapters/auditor.json:159](/work/1/SFC/tanab/izanagi/.claude/worktrees/t1356-sort-closed-region-wiring/.codex/role-adapters/auditor.json:159) | renderer 生成物にも `maximum: 16` がある。親が再生成。`source.sha256` は235行付近。 |
| [orchestrator/tests/test_p3_s4_loop_trigger_gating.py:1719](/work/1/SFC/tanab/izanagi/.claude/worktrees/t1356-sort-closed-region-wiring/orchestrator/tests/test_p3_s4_loop_trigger_gating.py:1719) | shared auditor gate の全コード検査なので `range(1, 18)` へ追随。 |
| [orchestrator/campaign/p3_autonomous_workload_trial.py:298](/work/1/SFC/tanab/izanagi/.claude/worktrees/t1356-sort-closed-region-wiring/orchestrator/campaign/p3_autonomous_workload_trial.py:298) | trigger-gating 専用 prompt。sort 専用型17をtrigger軸へ露出させないため、今回は変更しない。 |

追加検索で見つかったものは以下です。

- `tools/ruleops.py:2095` の `maximum=16` は mutation status 文字列長の汎用上限で、auditor 型の pin ではない。
- `axis_trigger_gating.py:89`、trigger runbook、過去の decisions/worklog は trigger 軸の型16を説明する文書参照であり、型17のschema pinではない。
- `test_codex_agents.py` の auditor SHA/schema 操作は動的な drift-test で、固定値の追加更新は不要。
- `_AUDITOR_VIOLATION_TYPES` の定義は `auditor_gate.py:29` の1箇所だけで、使用は同ファイル65行付近です。
- auditor.md の独立 byte 検査は review ledger と、生成 adapter の `source.sha256` に閉じています。`spec.py:583-589` がledgerを検証し、`render_adapter()` は `spec.py:803-873` でsource/schema/pinをadapterへ埋め込みます。

## 2. auditor.md の追記案

| file:line | 変更内容 |
|---|---|
| [.claude/agents/auditor.md:65](/work/1/SFC/tanab/izanagi/.claude/worktrees/t1356-sort-closed-region-wiring/.claude/agents/auditor.md:65) | 型16の直後、checklist節の前に型17を追加。 |
| [.claude/agents/auditor.md:81](/work/1/SFC/tanab/izanagi/.claude/worktrees/t1356-sort-closed-region-wiring/.claude/agents/auditor.md:81) | 既存checklist 13の直後に項目14を追加。 |

追記文面案:

```text
17. **sort closed-region 禁止事項の残余** — sort comparator の closed-region 契約に反して、
新しい型/関数を追加する、非決定ビルトインを使う、副作用のある呼び出しを行う、ループを置く、
または例外を送出する変異。型/関数の追加は機械 gate が検査せず、非決定ビルトイン・副作用の
ある呼び出し・ループ・例外送出も検査が部分的なため、機械 gate/verifier の構造判定だけでは
この契約違反を分類できない。→ designated diff を行単位で確認し、該当時は型17として場所・
正しさへの影響・verifier が見逃す機序を返す。検査しない/部分的であることは許可を意味しない。
```

```text
14. **sort closed-region の残余5項目 (型17、段5以降):** `silo-writeset-sort` の
implementation を行単位で確認し、次を別々に確認する。(a) 新しい型/関数 — 機械 gate の検査外で、
通過は不在の証拠にならない。(b) 非決定ビルトイン — 検査が部分的で、決定性の契約を完結に
判定しない。(c) 副作用のある呼び出し — 検査が部分的で、副作用なしの契約を完結に判定しない。
(d) ループ — 検査が部分的で、straight-line の契約を完結に判定しない。(e) 例外送出 —
検査が部分的で、例外なしの契約を完結に判定しない。該当箇所は型17として場所・正しさへの
影響・verifier が見逃す機序を報告する。
```

これは D511 の「境界条件を書かない」「非検査は許可ではない」を満たし、具体的な回避形や oracle の観測限界は記述していません。

型番号は5分割せず17へ集約します。5項目は同じ sort closed-region 契約の残余であり、既存の `location`、`correctness_impact`、`verifier_blind_spot`、`note` で内訳を記録できます。schema/gate/test の変更量も最小です。

[coder-v4-autonomous-sort.md:87](/work/1/SFC/tanab/izanagi/.claude/worktrees/t1356-sort-closed-region-wiring/.claude/agents/coder-v4-autonomous-sort.md:87)〜91は変更しません。禁止文は既に5項目を正しく含み、T-1356は執行側の結線が目的です。変更するとcoder source pin、adapter、T-396の別択一まで再開するため、今回のscopeから外します。

## 3. schema・gate・review ledger

| file:line | 変更内容 |
|---|---|
| [orchestrator/codex_roles/manifest.json:122](/work/1/SFC/tanab/izanagi/.claude/worktrees/t1356-sort-closed-region-wiring/orchestrator/codex_roles/manifest.json:122) | `"maximum": 16` → `"maximum": 17`。 |
| [orchestrator/campaign/auditor_gate.py:29](/work/1/SFC/tanab/izanagi/.claude/worktrees/t1356-sort-closed-region-wiring/orchestrator/campaign/auditor_gate.py:29) | `frozenset(range(1, 17))` → `frozenset(range(1, 18))`。 |
| [review_ledger.py:16](/work/1/SFC/tanab/izanagi/.claude/worktrees/t1356-sort-closed-region-wiring/orchestrator/codex_roles/review_ledger.py:16) | auditor.md 編集後の SHA256。 |
| [review_ledger.py:38](/work/1/SFC/tanab/izanagi/.claude/worktrees/t1356-sort-closed-region-wiring/orchestrator/codex_roles/review_ledger.py:38) | manifest の `roles.auditor` 全体SHA256。 |
| [review_ledger.py:83](/work/1/SFC/tanab/izanagi/.claude/worktrees/t1356-sort-closed-region-wiring/orchestrator/codex_roles/review_ledger.py:83) | output schema SHA256。 |

更新順序:

1. auditor.md 編集後に、source pinを再計算する。

```bash
sha256sum .claude/agents/auditor.md | awk '{print $1}'
```

2. manifest の上限を17へ変更後、以下のcanonical JSONをSHA256化する。

```python
import hashlib, json
from pathlib import Path

m = json.loads(Path("orchestrator/codex_roles/manifest.json").read_text())
canonical = lambda x: json.dumps(
    x, ensure_ascii=False, sort_keys=True,
    separators=(",", ":"), allow_nan=False
).encode("utf-8")

print("role_manifest", hashlib.sha256(canonical(m["roles"]["auditor"])).hexdigest())
print("output_schema", hashlib.sha256(
    canonical(m["roles"]["auditor"]["output_schema"])
).hexdigest())
```

3. 近傍のコメント規約に合わせて、例えば次を追加する。

```python
# Reviewed 2026-08-19: T-1356; auditor sort closed-region residual wiring.
```

`ROLE_MANIFEST_SHA256` には「output violation type upper bound 17」、`SCHEMA_SHA256` には「auditor violation type 17 boundary」と理由を明記します。

## 4. `.codex/role-adapters/auditor.json` と waiver

| file:line | 変更内容 |
|---|---|
| [orchestrator/codex_roles/spec.py:725](/work/1/SFC/tanab/izanagi/.claude/worktrees/t1356-sort-closed-region-wiring/orchestrator/codex_roles/spec.py:725) | `get_role_spec()` はmanifest/sourceを読み、ledger driftを検証する。 |
| [orchestrator/codex_roles/spec.py:803](/work/1/SFC/tanab/izanagi/.claude/worktrees/t1356-sort-closed-region-wiring/orchestrator/codex_roles/spec.py:803) | `render_adapter()` がsource SHA、schema、ledger pin、role bodyを生成する。 |
| [tools/check_codex_agents.py:223](/work/1/SFC/tanab/izanagi/.claude/worktrees/t1356-sort-closed-region-wiring/tools/check_codex_agents.py:223) | `expected_adapters()` と実ファイルをbyte比較する。 |
| [.codex/role-adapters/auditor.json:159](/work/1/SFC/tanab/izanagi/.claude/worktrees/t1356-sort-closed-region-wiring/.codex/role-adapters/auditor.json:159) | 親がrenderer出力へ再生成する。段5のCodex authorには触らせない。 |

段5はauditor.md、manifest、ledger、gate、テストを実装するが、`.codex/` は変更しません。親がledger更新後にrenderer出力を適用し、T-396の前例どおり実装commitとadapter再生成commitを分離します。

D105とcheckerの確認結果:

- `WAIVER_VALUE` は `reason=<IDENT>; ratified=<YYYY-MM-DD>` の形式だけを検査します。
- `reason` の許可リストやratified日付の鮮度検査はありません。
- `_waiver_audit()` は物理1行、canonical 1件、最終trailer block、`role=author` を検査します。
- `validate_implementation_author()` はCodex authorが存在しない場合に、exact waiverなら免除を実際に発火させます。
- よって `reason=codex-sandbox-readonly-dotcodex` の再利用は、2026-08-18のユーザー承認に基づく限り可能です。
- 同じ承認を再利用するため、`ratified=2026-08-18` を保持します。当日の日付へ更新するのは、新たな承認を意味するため適切ではありません。

adapter専用commitの最終blockには、次の形を使います。

```text
AI-Agent: product=claude; model=<model>; reasoning=<reasoning>; role=author
AI-Agent-Waiver: reason=codex-sandbox-readonly-dotcodex; ratified=2026-08-18
```

## 5. 境界テストとP2

| file:line | 変更案 |
|---|---|
| [orchestrator/tests/test_auditor_gate.py:132](/work/1/SFC/tanab/izanagi/.claude/worktrees/t1356-sort-closed-region-wiring/orchestrator/tests/test_auditor_gate.py:132) | type17受理、type18拒否の2テストを追加。 |
| [test_p3_s4_loop_trigger_gating.py:1719](/work/1/SFC/tanab/izanagi/.claude/worktrees/t1356-sort-closed-region-wiring/orchestrator/tests/test_p3_s4_loop_trigger_gating.py:1719) | `range(1, 17)` → `range(1, 18)`。shared gateの全コード検査なので追随させる。 |
| [p3_autonomous_workload_trial.py:298](/work/1/SFC/tanab/izanagi/.claude/worktrees/t1356-sort-closed-region-wiring/orchestrator/campaign/p3_autonomous_workload_trial.py:298) | 推奨は変更なし。trigger-gating軸でsort専用型17を出力対象にしない。 |

テスト文面案:

```python
def test_parse_auditor_dict_accepts_sort_closed_region_type_17():
    parsed = parse_auditor_dict({
        "verdict": "reject",
        "diff_digest": "a" * 64,
        "violations": [{"type": 17}],
    })
    assert parsed.violations == [{"type": 17}]


def test_parse_auditor_dict_rejects_violation_type_18():
    try:
        parse_auditor_dict({
            "verdict": "reject",
            "diff_digest": "a" * 64,
            "violations": [{"type": 18}],
        })
        raise AssertionError("gallery code 18 を素通しした")
    except AuditorGateFailure:
        pass
```

trigger-gating testはコメントどおり共有部品の契約を確認しており、sort専用driverのテストではありません。そのため17を含めるのが適切です。

## 6. 規律2の自己検査

| file:line | 判定 |
|---|---|
| [coder_effect_gate.py:58](/work/1/SFC/tanab/izanagi/.claude/worktrees/t1356-sort-closed-region-wiring/orchestrator/campaign/coder_effect_gate.py:58) | `DENY_TABLE` は変更しない。 |
| [coder_effect_gate.py:576](/work/1/SFC/tanab/izanagi/.claude/worktrees/t1356-sort-closed-region-wiring/orchestrator/campaign/coder_effect_gate.py:576) | `scan_host_effects` は変更しない。 |
| [sort_swo_oracle.py:486](/work/1/SFC/tanab/izanagi/.claude/worktrees/t1356-sort-closed-region-wiring/orchestrator/campaign/sort_swo_oracle.py:486) | `_validate_single_sort_statement` は変更しない。 |
| [sort_swo_oracle.py:1450](/work/1/SFC/tanab/izanagi/.claude/worktrees/t1356-sort-closed-region-wiring/orchestrator/campaign/sort_swo_oracle.py:1450) | SWO oracleの受理フローは変更しない。 |

今回の変更はauditorの指摘語彙を広げるだけです。CC variant側の受理集合、DENY_TABLE、host-effect scan、sort statement/SWO oracleは不変です。

## 7. decisions.md の新設計判断

新しいDエントリが必要です。

[D96]( /work/1/SFC/tanab/izanagi/.claude/worktrees/t1356-sort-closed-region-wiring/docs/decisions.md:4269 ) は受理集合を変更する場合、新設計判断と境界テストを同一変更単位に置くよう要求しています。今回のschema/gate変更は auditor output の受理集合を16から17へ広げるため、D511/D95/D344だけでは記録として不足します。

親が段7で、`docs/decisions.md` の現行末尾22999行以降へ新Dのspool fragmentを追加し、以下を記録するのが適切です。

- 型17へ5項目を集約した理由。
- manifest上限17、gate受理集合、境界テスト。
- coder契約本文とCC受理集合を変更しないこと。
- adapterをD105 waiver付き別commitで再生成すること。

静的検査のみ実施し、pytest・書き込みは行っていません。作業ツリーはcleanでした。