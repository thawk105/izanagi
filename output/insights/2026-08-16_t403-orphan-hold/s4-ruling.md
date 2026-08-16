# 段 4 裁定 — [T-403] 孤児 job の後始末 (plan v2)

裁定時刻 2026-08-16 14:52 JST / base = 478a4138 (local main 取り込み後)

## 所見の裁定表

| 出所 | 所見 | 裁定 | 採否 | 根拠 |
|---|---|---|---|---|
| A-1 | `request_present=False` は不在証明でない (P1 に false negative) | **real** | 採用 | qsub 受理直後に qstat 未反映でも `success-request-absent` になる。既存テスト `:1724` が同経路で `job_may_remain=True` を固定している |
| A-1b | `terminal-history-conflict` も permissive parser 由来で不確実 | **real** | 採用 | `_scheduler_state` は対象束縛でない (`dispatch_compute.py:1594-1622`) |
| A-2 / B-2 | qsub 受理〜`active=True` の間 hold が武装されない | **real** | 採用 | `active=True` は qsub の return 観測後 (`:1493`)。その前の signal は `active=False` の例外経路へ落ちる |
| A-3 | harness の 5 秒 SIGKILL が 90 秒 cleanup を殺し、hold が書かれないまま `TIMEOUT` が受理されうる | **real** | 採用 | `_stop_process` (`mutation_harness.py:1328`) と `DEFAULT_CLEANUP_BUDGET_S` の差。`TIMEOUT` は正規 status で次変異へ進める |
| A-4 | hold 書込み失敗が通常 INFRA に埋没し再ラッチされない | **real** | 採用 (層で塞ぐ) | `claim_cleanup_once` は再入で既存 record を返すだけ |
| A-5 / B-3 | hold file は同期原語でなく TOCTOU を閉じない | **real** | **部分採用** | 下記「TOCTOU の裁定」 |
| A-6 | 署名は false positive も持つ (自然終了直後の qdel 失敗など) | **real** | 採用 (署名は緩めない) | D142 の非対称性より、止め過ぎは回復可能・殺し過ぎは回復不能 |
| A-7 / B-7 | 提案テストは主要欠陥を殺せない | **real** | 採用 | テスト集合を下記へ差し替える |
| A-8 | 「計算 job は独立 copy を読む」反論 | **refuted** | — | 親 brief の因果前提は確認された (`:439,467,502`, `_job_run:573,594`, `run_tests.py:53,1898`) |
| A-9 | 実 receipt 135 件は保存成功条件付き標本 (survivorship bias) | **real** | 採用 | root 直下の `receipt-setup-*.json` を親の glob が落としていた (実数 136)。field 欠落を安全証拠にしない |
| B-1 | 受入赤再走が孤児の probe worktree を `worktree remove --force` する | **real** | 採用 | `check_acceptance_reds.py:815-835` を親が実測確認 |
| B-4 | plan-only の例外 fallback が teardown gate を迂回する | **real** | 採用 | `mutation_worktree.py:1167-1199` |
| B-6 | 回復手順が RUN / qdel 副作用 / path を扱えない | **real** | 採用 | hold と停止記録に状態別手順を書く |
| B-8 | 並行 wave の root 巻き込み | **refuted** | — | dispatch root は `repo_root` ごと (`:1319-1326`) |
| B-9 | F47 / fanout 契約 / task_run との直接衝突 | **refuted** | — | 別 file・別検査 |
| B-候補1 | `submit_*.sh` と `patchharness.py` の未防護 qsub / 復元 / worktree 強制削除 | **real** | **scope 外 → 裁定パッケージ** | 別 producer 族。本 wave の主張範囲を明示する |
| B-候補2 | local (非 dispatch) 実行経路を停止対象に含めるか | **real** | **scope 外 → 裁定パッケージ** | local 実行は計算ノード job を作らないが、孤児が居る間の tree 書換えは同じ危険 |

## TOCTOU の裁定 (A-5 / B-3)

- **完全な排他 (共有 lifecycle lock) は scope 外。** 裁定パッケージへ送る。
- **本 wave で閉じる範囲を実測で確定した**: harness の復元は `_run_tests` の finally が
  `_stop_process` で dispatcher process group を**回収しきった後**に走る
  (`mutation_harness.py:1430-1431` → `_apply_mutation:1602`)。したがって「dispatcher が hold を書く」と
  「harness が復元する」は同一 checkout では逐次であり、この対に race は無い。
  さらに harness 同士は `flock` (`:2090-2110`) で 1 checkout 1 本に直列化される。
- 残る窓は「同一 checkout で harness を経由しない別 dispatch invocation が同時に走る」場合だけで、
  これは運用上作らない構成である。**hold は latch であって mutual exclusion ではない**ことを
  docstring・decisions に明記し、残余窓を隠さない。

## plan v2 (実装する形)

### 層 1 — `tools/pegasus/dispatch_compute.py`

- **L1.1 署名を単純化する。** `H(qdel) := qdel.job_may_remain is True`。**例外条項を置かない。**
  段 2 プランの `request_present is False` / `terminal-history-conflict` 免除は A-1/A-1b により**撤回**。
  `gate.reason` は判定に使わず、人間の解除判断のため hold record へ**記録だけ**する。
  - 通る正例: 通常完走経路 (`:1466-1779`) は `claim_cleanup_once` を呼ばないので `qdel` は
    receipt 初期値のまま = `job_may_remain` 不在 → hold は立たず、次回投入は従来どおり `qstat -Q` → `qsub` へ進む。
    gate 許可 + qdel rc=0 (`job_may_remain=False`) も hold を立てない。
- **L1.2 投入結果不明の窓を塞ぐ。** qsub を起動する**前**に「投入結果不明」状態へ入り、
  qsub の return を観測して初めて確定 (rc=0 → active / rc≠0 → 不明を解除) する。
  結果不明のまま例外・signal で抜ける場合は、
  **read-only の request ID discovery (`_discover_request_id`) だけを行い、qdel を試みずに hold を立てる。**
  - **この wave は qdel 経路を 1 本も増やさない** (ユーザー裁定)。L1.2 の新経路は qstat のみを打つ。
  - qsub が rc≠0 を返したことを観測できた場合は hold を立てない (投入されていない実証)。
- **L1.3 投入前検査。** 既存 F47 ラッチ検査 (`:1350-1354`) の**直後**、nonce directory 作成と
  `qstat -Q` preflight より**前**に hold を検査し、成立なら scheduler command を 1 本も打たずに `INFRA_RC`。
  存在判定は `exists() or is_symlink()`。読めない・壊れている・directory でも成立側 (fail-closed)。
  F47 と両方あるときは F47 の文言を先に出す (既存 F47 の受理集合と文言を変えない)。
- **L1.4 hold 書込み失敗を握り潰さない。** `FileExistsError` は既存 record 保持で正常。
  それ以外の `OSError` は receipt へ `qdel.hold_error` を残し stderr へ明示する。
  成功したことにしない。層 2 が独立に塞ぐ。
- hold record は create-only、上書き・削除・自動解除を実装しない。
  `gate.reason` / `request_id` / `job_name` / `submission_dir` / `attempted` / `returncode` /
  `exception` と、**状態別の回復手順**を持つ。
  回復手順には「手動 qdel は F47 ラッチを武装させ、その解除もユーザー手番になる」を明記する (B-6)。

### 層 2 — `tools/mutation_harness.py`

- **L2.1 dispatcher の生存に依存しない独立判定。** `runner_mode == "dispatch"` の試行について、
  次のいずれかが成立したら孤児条件とする。
  1. hold file が存在する (層 1 が立てた、または過去に立った)。
  2. その試行が `timed_out is True` である。**dispatcher を自分で殺した以上、計算ノードの job は
     残っていると仮定する** (A-3)。
  - 2 が成立して hold file が無い場合、**harness 自身が hold を create-only で立てる**。
    これで dispatcher が SIGKILL された経路 (A-3) と hold 書込み失敗 (A-4) を塞ぐ。
  - `timed_out` でない `PARSE_ERROR` は孤児条件に**含めない**。dispatcher が正常 rc を返した以上、
    job の lifecycle は閉じている。過剰拒否を避ける (DW-M01 の正例側)。
  - 副作用: `hang_risk` 変異の期待 `TIMEOUT` も dispatch mode では孤児条件になる。
    これは隠さず記録する。DW-M06 の「timeout を fail-open の証拠として記録する」は行い、
    そのうえで停止する。
- **L2.2 復元と前進を止める。** 孤児条件成立時は `_restore_targets` を呼ばず、
  変異 bytes を tree に残したまま停止する。次の変異へ進まない。
  `_purge_pycache` / `_verify_originals` も呼ばない。`_assert_head` は行ってよい。
- **L2.3 検査点。** collection / baseline / 各 mutation の runner 起動**前**と、
  `_apply_mutation` の `finally`。finally の判定を復元可否の権威とする。
- **L2.4 停止記録。** 通常 ledger schema (`izanagi-dev-wave-mutation/v4`) は変えない。
  専用の非終端停止記録を `--out` へ書き、`reason.code="orphan-hold"`、`phase`、`mutation_id`、
  `hold_path`、`source_state`、`dirty_paths` (touched を sort)、`recovery` を持たせる。
  fan-out merge へは渡さない。
- **L2.5 rc。** 専用例外を `HarnessError` 系として扱い rc=2 (既存の「harness aborted」) で終える。
  stderr に「変異を残した」「dirty path」「hold path」「復旧順序」を必ず出す。
  signal unwind 中に孤児条件を見つけた場合は、復元を見送った事実を明示してから signal を再送出する。
  既存の「active mutation restore attempted」文言は孤児条件が無い場合だけ維持する。

### 層 3 — `tools/mutation_worktree.py`

- `_should_teardown` に `orphan_hold: bool` を足し、`not orphan_hold and (...)` とする。
- **通常経路と plan-only / 例外 fallback の両方**に適用する (B-4)。判定不能も保全側へ倒す。
- 検査対象は container 内 `<checkout>/output/pegasus-dispatch/orphan-hold.json`
  (`_dispatch_root(preflight)` 直下)。退避後の evidence path ではない。
- wrapper receipt は schema を変えず `failure="orphan-hold"`、`container_preserved=true`、
  `teardown_attempted=false`、`teardown_completed=false`、`dispatch_evidence.relocated=false` を書く。
  `terminal_ledger` と `child_rc` は実測値を改竄しない。
- 既に `child_rc in {0,1}` 要件が rc=2 停止を弾くが、**それに依存しない明示 gate**を置く
  (rc 意味変更への耐性、および plan-only 経路のため)。

### 層 4 — `tools/check_acceptance_reds.py`

- `_cleanup_probe` (`:815-835`) と `_cleanup_dispatch_artifacts` (`:383-400`) は、
  対象 dispatch root 直下に hold があるとき **`git worktree remove --force` も `rmtree` も `rmdir` も行わず**、
  probe worktree と成果物を保全して構造化 `InvalidInput` を上げる (判定不能 = 非帰属の根拠にしない)。
- hold を隠すために検査から除外する変更はしない。

## scope 外 (裁定パッケージとしてユーザーへ返す)

1. dispatch / 復元 / teardown を跨ぐ共有 lifecycle lock (完全排他)。本 wave の hold は latch であり、
   「同一 checkout で harness を経由しない並行 dispatch」は運用上作らない前提で残余窓を明記する。
2. `tools/pegasus/submit_floor.sh` / `submit_certify.sh` / `submit_silo_ladder_rung1.sh` の直接 qsub と、
   `orchestrator/campaign/patchharness.py` の checkout 復元・worktree 強制削除。
   → **本 wave の主張は「`dispatch_compute` 経由の dispatch と変異 harness 系」に限る**と明記し、
   「全 job が fail-closed になった」とは報告しない。
3. local (非 dispatch) 実行経路を hold の停止対象に含めるか。
4. hold の自動解除・claim tombstone による解決証拠 (A-2/A-4 の恒久形)。

## 不変条件 (実装子への拘束)

- **qdel を実行する経路を 1 本も増やさない。** L1.2 の新経路は qstat のみ。
- 既存 F47 ラッチの発火条件・payload・文言・優先順位を変えない。
- 既存テストの期待値を変更しない。変更が必要に見えたら実装を疑い、報告して止める。
- 新しい scheduler state 語彙を作らない。
- hold は create-only。削除・上書き・自動解除を実装しない。
- 通常 ledger v4 / wrapper receipt v1 / dispatch receipt v2 の schema を変えない。

## 変異事前登録 (DW-M01、B-057)

各変異は「wave 前の実コードの形」を含む。位置は fix 後の最終 commit で anchor を再検証する (DW-M07)。

| id | 層 | 変異 (wave 前の形へ戻す) | 期待 | 単一理由性の根拠 |
|---|---|---|---|---|
| M1 | 1 | hold 署名を常に不成立へ固定 | KILLED | 前後に同判定を行う層は無い。hold 発行はここだけ |
| M2 | 1 | 投入前 hold 検査を削除 (wave 前の形) | KILLED | F47 検査は別 file を見るので先取りしない |
| M3 | 1 | 「投入結果不明」を qsub の return 後に立てる (wave 前の形) | KILLED | qsub 中 signal のテストはこの 1 点だけに依存 |
| M4 | 2 | `finally` を無条件 `_restore_targets` へ戻す (wave 前の形) | KILLED | 復元はこの 1 箇所 |
| M5 | 2 | 孤児条件から `timed_out` 項を落とし hold file 存在だけにする | KILLED | SIGKILL 経路は他層が拒否しない |
| M6 | 2 | 停止後に次変異へ進むよう戻す | KILLED | 進行停止はこの 1 箇所 |
| M7 | 3 | `_should_teardown` から `not orphan_hold and` を削除 (wave 前の形) | KILLED | rc=2 に依存しない gate を殺す。テストは plan-only + child_rc=0 で単一理由化する |
| M8 | 3 | 例外 fallback 経路の gate を削除 | KILLED | 通常経路の gate は fallback を先取りしない |
| M9 | 4 | `_cleanup_probe` の保全を削除 (wave 前の形) | KILLED | 保全判定はこの 1 箇所 |
| P1 | 全 | hold 判定を常に成立へ固定 (過剰拒否) | KILLED | **正例側**。hold 不在時に従来どおり投入・復元・teardown する経路が赤くなることを固定する (DW-M01) |

**新設 gate の先取り注意 (memory `new-gate-mutations-count-preempted-checks`):** M2 / M4 / M7 / M9 は
gate が発火すると後段が走らないため、期待 node は「gate 由来の 1 件」ではなく
**後段検査も含む完全集合**を fix 後に `--junitxml` から再導出する (DW-M08、F33)。

## 段 5 の分割

編集面は 4 file + それぞれの test。依存は 層 1 の hold record 形式 → 層 2/3/4 の一方向。
**Codex `role=author` 1 単位の直列**とし、所有 path を次に限定する。

- `tools/pegasus/dispatch_compute.py`
- `tools/mutation_harness.py`
- `tools/mutation_worktree.py`
- `tools/check_acceptance_reds.py`
- `orchestrator/tests/test_pegasus_dispatch_compute.py`
- `orchestrator/tests/test_mutation_harness.py`
- `orchestrator/tests/test_mutation_worktree.py`
- `orchestrator/tests/test_check_acceptance_reds.py`
