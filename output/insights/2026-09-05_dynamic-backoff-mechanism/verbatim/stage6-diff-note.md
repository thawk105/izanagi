# 段 6 レビュー用: 差分の範囲と、親が実行済みの検査 (2026-09-05)

## 差分

- base = 3b0d7a1cb (事前登録 v1 を含む)。統合 commit = `8bfa6d110` (`git diff 3b0d7a1cb 8bfa6d110`)。
  その後 local main を merge しているが main 側は docs のみ。
- 単位 A (Codex author): `patches/cicada-adaptive-dynamic.patch` (sha256 `eb6669c514628686a48e837a6fd7e7c80ec40d7d2ec45c1bd99ba5c8781f18af`)、
  `orchestrator/tests/test_dynamic_backoff_transitions.py`。fix 2 回 (variant 固有コメント、`[[maybe_unused]]` + 警告フラグ)。
- 単位 B (Codex author): probe `.py` / `.pbs`、`condition_meaning_gate.py`、`screening_driver.py`、test 3 file。fix 1 回
  (trace parser の整数符号化、ccbench build test の差し替え、sink golden / deferred 行番号)。
- 単位 C (Codex author): `tools/plotting/plot_dynamic_backoff.py`、`orchestrator/tests/test_plot_dynamic_backoff.py`。
- 親 (docs): `patches/README.md`、`tools/plotting/README.md`、`docs/README.md`、`docs/dynamic-backoff-preregistration.md`。

## 親が実行済みの検査 (結果は job dir の log)

- 焦点走 `focus-all-2.log`: 7 test file (transitions / plot / t2187 probe / condition gate / spawn sites / screening / hooks) で 750 緑・1 skip・1 赤。赤は
  `test_screening_driver.py::test_prepare_repairs_tail_before_baseline_callback` (本 wave が触らない file。`/tmp` の一時 dir を
  repo 内と誤判定した一過性で、単独再走は緑 `focus-screening-1.log`)。
- login node の生死確認 `liveness-2.log`: pin + A + B を CCBench の CMake (`-Wall -Wextra -Werror`) で build。
  tuned (既定) / cw-as-dyn (perf) / cw-as-dyn (BACKOFF_TRACE=1) の 3 build 成功。perf 2 本は `nm` の `izanagi_backoff_trace`
  0 件・`strings` の `IZANAGI_BACKOFF_TRACE` 0 件、診断は symbol 4・文字列 2。A 単独と A+B 既定の tuned binary は、
  アドレス注記を除いた `objdump -d` の命令列 60,242 行が完全一致 (差は rip 相対のデータ位置注記のみ)。
  **1 回目の生死確認は `-Werror=unused-parameter` で既定 build が落ちる実欠陥を捕まえ、A の fix 3 で直した。**
- `check_docs.py`: 違反なし。`git diff --check`: patch file の空 context 行 (`+ `) 13 件は A の commit (0185e07ca) と同じ型で許容。
- 計測 (Pegasus) はまだ投げていない。認証も未実行。**性能値は 1 つも無い。**

## レビューで前提にしてよいこと

- 事前登録 v1 は凍結済み (commit 3b0d7a1cb)。実装が事前登録と食い違えば実装側の所見。
- `patches/ledger.json` は非登録が裁定 (P7)。
- 認証は perf/診断の後に無条件で 24 request (裁定 B-MF10 refuted)。
