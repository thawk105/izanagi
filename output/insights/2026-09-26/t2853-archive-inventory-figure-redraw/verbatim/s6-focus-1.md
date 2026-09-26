## 対応表

| 対象 | 判定 | 根拠 |
|---|---|---|
| A-M1・B-M1 | partial | HEAD と patch hash のずれは `failed` にする。ただし短縮 pin を使う通常経路も HEAD 照合で失敗する。[pipeline.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/t2853-archive-inventory-figure-redraw/orchestrator/campaign/pipeline.py:2737) |
| A-S2 | closed | fixture が Silo proof source を commit する。[test_t2853_trace_preservation.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/t2853-archive-inventory-figure-redraw/orchestrator/tests/test_t2853_trace_preservation.py:64) |
| A-S3 | closed | evidence と保存 patch の hash を実 diff から照合する。[test_t2853_trace_preservation.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/t2853-archive-inventory-figure-redraw/orchestrator/tests/test_t2853_trace_preservation.py:85) |
| B-S2 | closed | 実 HEAD に checkout し、復元 patch を適用して内容を比べる。[test_t2853_trace_preservation.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/t2853-archive-inventory-figure-redraw/orchestrator/tests/test_t2853_trace_preservation.py:126) |
| B-N3 | not-addressed | 広い `subprocess.run`・`Path.read_bytes` 差し替えは残る。段6裁定どおりの nit。[test_t2853_trace_preservation.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/t2853-archive-inventory-figure-redraw/orchestrator/tests/test_t2853_trace_preservation.py:320) |
| 焦点走の赤: `test_archive_before_cleanup`、`test_unset_env_unchanged`、`test_failure_retains_original` 4 ケース、`test_preservation_error_does_not_replace_result`、`test_inventory_records_r1_inputs` | closed（静的判定） | 共通 fixture に proof source を追加し、env 未設定テストでは監視開始前に metadata を取得する。[test_t2853_trace_preservation.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/t2853-archive-inventory-figure-redraw/orchestrator/tests/test_t2853_trace_preservation.py:70)、[同:295](/work/1/SFC/tanab/izanagi/.claude/worktrees/t2853-archive-inventory-figure-redraw/orchestrator/tests/test_t2853_trace_preservation.py:295) |
| 焦点走の赤: 起動箇所検査 2 件 | closed（静的判定） | Git 起動は `_archive_git` の 1 箇所となり、共通登録簿に 1 件追加された。[pipeline.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/t2853-archive-inventory-figure-redraw/orchestrator/campaign/pipeline.py:2633)、[test_ccbench_spawn_sites.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/t2853-archive-inventory-figure-redraw/orchestrator/tests/test_ccbench_spawn_sites.py:99) |

## 新規所見

1. **must-fix** — 短縮 pin の通常入力で HEAD 照合が恒常的に失敗する。`pin.CURRENT_PIN = "6810666"` を使う driver があり、`resolve_evidence` はその文字列を `ccbench_commit` に保持する。一方 `git rev-parse HEAD` は完全 SHA を返し、文字列比較する。[pin.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/t2853-archive-inventory-figure-redraw/orchestrator/campaign/pin.py:32)、[source_digest.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/t2853-archive-inventory-figure-redraw/orchestrator/campaign/source_digest.py:2453)、[pipeline.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/t2853-archive-inventory-figure-redraw/orchestrator/campaign/pipeline.py:2737)。**影響:** その標準経路の inventory は source が変わらなくても `failed` となり、正常な R1 入力が得られない。**代案:** evidence の pin を `rev-parse --verify <pin>^{commit}` で完全 SHA に解決して HEAD と比べ、短縮 pin と tag の回帰テストを加える。

patch hash は `_tracked_diff_sha256` と同じ Git argv・sanitized env・source root を使う。[source_digest.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/t2853-archive-inventory-figure-redraw/orchestrator/campaign/source_digest.py:2377)、[pipeline.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/t2853-archive-inventory-figure-redraw/orchestrator/campaign/pipeline.py:2633)。`source_root` も evidence 生成時に realpath 化される。[source_digest.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/t2853-archive-inventory-figure-redraw/orchestrator/campaign/source_digest.py:2430)。patch 保存後の照合失敗では patch を残して `failed` を記録し、`complete` には進まないため、段6裁定と status 規則に合う。[pipeline.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/t2853-archive-inventory-figure-redraw/orchestrator/campaign/pipeline.py:2736)。env 未設定時の追加処理も保全分岐の内側に留まり、保全例外は caller が受けて元の評価結果を保つ。[pipeline.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/t2853-archive-inventory-figure-redraw/orchestrator/campaign/pipeline.py:2204)。

## 変異 kill 点の判定

静的な判定であり、probe は未実走。

| ID | 判定 | 名指し test の kill 点 |
|---|---|---|
| M1・M2 | 成立 | argv 全体の 1 assert。[test_t2853_trace_preservation.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/t2853-archive-inventory-figure-redraw/orchestrator/tests/test_t2853_trace_preservation.py:117) |
| M3 | 成立 | witness 無しの null assert。[同:145](/work/1/SFC/tanab/izanagi/.claude/worktrees/t2853-archive-inventory-figure-redraw/orchestrator/tests/test_t2853_trace_preservation.py:145) |
| M4 | 成立 | source と repo の HEAD が異なり、`repo_head` assert で赤。[同:111](/work/1/SFC/tanab/izanagi/.claude/worktrees/t2853-archive-inventory-figure-redraw/orchestrator/tests/test_t2853_trace_preservation.py:111)、[同:118](/work/1/SFC/tanab/izanagi/.claude/worktrees/t2853-archive-inventory-figure-redraw/orchestrator/tests/test_t2853_trace_preservation.py:118) |
| M5 | 成立 | pin assert。[同:119](/work/1/SFC/tanab/izanagi/.claude/worktrees/t2853-archive-inventory-figure-redraw/orchestrator/tests/test_t2853_trace_preservation.py:119) |
| M6 | 成立 | 復元 patch・hash の組 assert。[同:122](/work/1/SFC/tanab/izanagi/.claude/worktrees/t2853-archive-inventory-figure-redraw/orchestrator/tests/test_t2853_trace_preservation.py:122) |
| M7 | 成立 | module hash 辞書 assert。[同:134](/work/1/SFC/tanab/izanagi/.claude/worktrees/t2853-archive-inventory-figure-redraw/orchestrator/tests/test_t2853_trace_preservation.py:134) |
| M8 | 成立 | env 未設定時の verifier 読取回数 assert。[同:328](/work/1/SFC/tanab/izanagi/.claude/worktrees/t2853-archive-inventory-figure-redraw/orchestrator/tests/test_t2853_trace_preservation.py:328) |
| M9 | 成立 | 非 Git root の取得失敗が漏れれば結果比較 assert で赤。[同:168](/work/1/SFC/tanab/izanagi/.claude/worktrees/t2853-archive-inventory-figure-redraw/orchestrator/tests/test_t2853_trace_preservation.py:168) |
| M10・M11 | 成立 | 各 test は evidence の該当 1 field のみを変え、`failed` の組 assert で赤。[同:187](/work/1/SFC/tanab/izanagi/.claude/worktrees/t2853-archive-inventory-figure-redraw/orchestrator/tests/test_t2853_trace_preservation.py:187)、[同:193](/work/1/SFC/tanab/izanagi/.claude/worktrees/t2853-archive-inventory-figure-redraw/orchestrator/tests/test_t2853_trace_preservation.py:193) |
| C0 | 成立 | docstring のみの変更で判定経路に影響しない。[pipeline.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/t2853-archive-inventory-figure-redraw/orchestrator/campaign/pipeline.py:2653) |

## 総括

**NO-GO。** must-fix は短縮 pin と完全 SHA の照合を正規化する 1 件。焦点走 1 回目の赤 10 件は静的には解消されたが、焦点走 2 回目・変異 probe の結果は本レビュー時点で未確認。