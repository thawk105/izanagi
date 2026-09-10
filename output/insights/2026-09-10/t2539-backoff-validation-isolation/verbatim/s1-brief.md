# 段 1 brief — [T-2539] backoff patch と Silo validation 経路の素性を機械検査にする

## 研究前進

`docs/decisions.md:403` (D2) は「純 timing は abort-path タイミングのみで lock/validation 論理に
触れず正しさ攻撃面が構造的に最小」と**散文で**主張し、この主張の上に backoff 軸の認証射程が乗っている。
機械検査は存在しない。worklog entry 1406 は 24 threads 1 group を認証した一方、policy 2 の 24 threads
全 12 seed と policy 0 の全条件を未認証のまま残し、「次に正しさへ資源を使うならサンプルを増やす方向
ではなく [T-2539] を勧める」と記録した。本 wave が成れば、認証の射程を「標本数」ではなく
「変異族が正しさ論理に触れないこと」で支えられる。**完了判定** = 正例 (`patches/silo-backoff-fixed.patch`)
で緑、負例 2 本で赤、かつ負例が閉包の深さ 0 と深さ 1 の両方を突く。計算 job は使わない。

## scope

`patches/silo-backoff-fixed.patch` の編集面が Silo の validation 経路と素であることを判定する
checker 1 本と、その test 1 本。負例は同じ checker を同じ引数形で通す。これ以外は作らない —
gate 新設・台帳追加・他 patch への一般化・既存 checker の改訂は scope 外 (ユーザー明示)。

## 確定済みユーザー裁定

計算 job 不要。判定は機械検査。負例を同じ単位に置き恒真でないことを示す。Codex author = D95。
規律 2 は緩めない。仮想リスク向けの gate・検査・台帳・一般化を足さない。

## 不変条件

- `patches/*.patch` の bytes を変えない (B-10 事前登録が pin、`docs/decisions.md:53130`)。
- `orchestrator/campaign/condition_meaning_gate.py` と `source_digest.py` を触らない
  (前者は並行 wave `dev-wave-t2449-s4loop-gate-evidence` の編集面)。
- 検査の入力は submodule 現物 `external/ccbench/` とする。
  `orchestrator/tests/fixtures/silo_ladder_rung1/stock/cc/silo/transaction.cc` は現物と
  byte 不一致 (古い snapshot) なので入力にしない。submodule 未初期化は fail-closed。
- 既存テストの期待値を変えない。受理集合を広げない。

## 段 1 の実測 (子はこれを前提にしてよいが、自分で確かめ直してよい)

- patch が触る file: `cmake/Options.cmake`、`include/backoff.hh` の 2 本のみ。
- 定義が変わる関数は `Backoff::backoff(size_t)` 1 本。他は file scope の
  `#ifndef BACKOFF_FIXED` / `#error` guard と `#if BACKOFF_NOINLINE` 属性行。
  `update_backoff` と `leaderBackoffWork` は非改変。
- `external/ccbench/cc/silo/transaction.cc`: `validationPhase()` = 383 行、
  `commit()` = 706 行 (`validationPhase()` → `writePhase()`)、
  `Backoff::backoff` 呼び出しは 47 行 (`TxExecutor::abort()` 内) の 1 箇所のみ、
  `leaderBackoffWork` 呼び出しは 720 行 (`TxExecutor::leaderWork()`) のみ。
- `BACKOFF_FIXED` / `BACKOFF_NOINLINE` は CCBench の .cc/.hh/.h に出現 0 件 (patch 未適用時)。
- 負例: `patches/broken-silo-norw-validation.patch` は `validationPhase` 本体 (深さ 0)、
  `patches/broken-silo-lockskip-validation.patch` は推移的呼び先 `lockWriteSet()` (深さ 1)。
- 既存策不足: `condition_meaning_gate.py` は docstring で「branch body の意味・動的到達可能性・
  正しさは証明しない」と明記。`source_digest.ALLOWLIST` は `cc/silo/transaction.cc` を含む
  file 単位許可集合で本主張を与えない。

## 割れうる前提 (親の provisional 裁定・段 3 の攻撃対象)

- **(P1-a) 「validation 経路」の定義** = `TxExecutor::validationPhase` から到達する呼び先の
  推移閉包 (CCBench source 内)。`commit()` は呼び手なので含めない、`writePhase()` は
  validation 成立**後**なので含めない、と親は暫定裁定する。sort の comparator (`operator<`) は
  閉包に含める。この境界が広すぎ/狭すぎないかを攻撃せよ。
- **(P1-b) 判定単位** = patch の hunk が写す post-image の source region。**preprocess 出力単位に
  しない** — 負例は `#if IZANAGI_BREAK_*` guard 付きで既定 OFF のため、preprocess 出力だけで
  判定すると負例が「無害」と通り検査が恒真になる。この罠を別の形で踏んでいないか攻撃せよ。
- **(P1-c) CMake leg** = `cmake/Options.cmake` は関数境界を持たないので、patch が導入する新 define が
  validation 閉包から参照されないことを別立てで検査する。text 走査で足りるか、preprocess で
  示すべきかは未裁定。
- **(P1-d) 非恒真性の witness** = 負例 2 本 (深さ 0 / 深さ 1)。2 本で足りるか、
  また正例側が「常に PASS を返す」構造になっていないかを攻撃せよ。

## 成果物の形

- checker: patch path を引数に取り、閉包との交差を verdict + 根拠 (交差した region、閉包の導出) で
  返す。判定不能は fail-closed。
- test: 正例 1・負例 2 を同じ引数形で通し、verdict の向きを固定する。閉包導出そのものの
  正例・負例も置く (実体を名指しし、stub しない)。
- 新規 test file なので自走 harness と受入所要台帳の両方が要る。

## 並列分割方針

実装面は checker + test の一枚岩に近く、段 5 は Codex 実装子 1 単位。段 3 は 2 レンズ並列、
段 6 は敵対レビュー 2 本並列。
