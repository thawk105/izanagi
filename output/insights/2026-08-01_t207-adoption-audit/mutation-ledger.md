# [T-207] 変異台帳 — `--provider fixture` + 実 build の fail-closed 拒否

段 4 で事前登録 (`DW-M01`)、段 6 の fix 後に本走 (`DW-M07`)。harness は Codex `role=author` が
書き、親が実走した。実走後に harness は削除し、本台帳を凍結記録とする。

## 変異対象

`orchestrator/campaign/p3_autonomous_workload_trial.py` の `main()` で、
`parse_args()` 直後に置いた 4 行の fail-closed 拒否。

## 固定している 4 象限

| provider | `--no-build` | 期待 | nodeid |
|---|---:|---|---|
| fixture | なし | 拒否 | `test_main_rejects_fixture_build_before_build_preparation` |
| fixture | あり | 受理 | `test_main_accepts_fixture_no_build_at_cli_gate` |
| claude-headless | なし | 受理 | `test_main_accepts_claude_headless_build_at_cli_gate` |
| claude-headless | あり | 受理 | `test_main_accepts_claude_headless_no_build_at_cli_gate` |

いずれも `orchestrator/tests/test_p3_autonomous_workload_trial.py`。
受理側 3 本はモジュール内 sentinel `_CliGateReached` を期待し、gate の例外**文言に依存しない**。

## 事前登録と結果

各変異は元ソースから独立に作り (累積適用しない)、anchor は適用前に出現回数 1 を assert した。
復元は `read_text() == 元ソース` の内容比較で検査した (`DW-M04` / `DW-M05`)。

| # | 変異 (anchor → 置換) | 受理集合を変えるか | 期待 | 記録 node | 判定 |
|---|---|---|---|---|---|
| M1 | `if args.provider == "fixture" and not args.no_build:` → `... and args.no_build:` (条件反転) | 変える | kill / `test_main_rejects_fixture_build_before_build_preparation` + `test_main_accepts_fixture_no_build_at_cli_gate` | 期待どおり 2 本 | **AGREE** |
| M2 | 同 anchor + 次行 `raise AutonomousTrialError(` → `if not args.no_build:` (provider によらず build を拒否 = 過剰拒否) | 変える | kill / `test_main_accepts_claude_headless_build_at_cli_gate` | 期待どおり 1 本 | **AGREE** |
| M3 | `"fixture provider cannot be used with a real build"` → 別文言 (診断文言のみ) | 変えない | **SURVIVED** / node なし | node なし、rc=0 | **AGREE** |
| M4 | 同 anchor → `if (args.provider == "fixture") == (not args.no_build):` (claude-headless + no-build だけ過剰拒否) | 変える | kill / `test_main_accepts_claude_headless_no_build_at_cli_gate` | 期待どおり 1 本 | **AGREE** |

M2 と M4 が `DW-M01` の「承認外の過剰拒否を検出する正例」枠である。負例 (M1) だけでは
拒否しすぎる変異が生き残るため両方を登録した。

**M3 が SURVIVED したことが、境界テストが診断文言に依存していない (恒真化していない) 証拠**である
(`DW-M03`: 診断文字列だけの赤を kill にしない)。

## harness 自身の欠陥と erratum (`DW-M02` / `DW-M08`)

**初回の本走は 4 変異とも rc は正しかったが、記録 node が全件「なし」になった。**
原因は `tools/run_tests.py` の Pegasus dispatch が計算ノード子の stdout を行頭 `| ` 付きで
中継するのに、harness が接頭辞を剥がさず `FAILED ` 判定をしていたこと。
`DW-M08` の「赤くなった test node を毎回記録する」を満たしていなかったため、matrix は
M1 / M2 / M4 を MISMATCH と報告した (実体は kill)。

修正は 2 点。(1) 中継接頭辞を剥がしてから `FAILED` 判定し、期待側・記録側へ同じ正規化関数を
通す。(2) **kill (rc≠0) なのに node が 1 件も取れなかった場合は AGREE にせず MISMATCH 側へ倒す** —
「node が取れないから期待どおり」と読める出力を作らない。修正後の再走が上表である。

初回結果は消さず、本節を erratum として残す。
