# [T-2067] 段 4 裁定 (親)

基準: wave branch `worktree-dev-wave-t2067-bcd-population`、着手時 local main `cc9bba523`。
入力: 親 brief、段 2 プラン (`s2-plan.md`)、段 3 レンズ A (`s3-lensA.md`) / レンズ B (`s3-lensB.md`)、
親の独立実測。裁定 inbox を段 4 直前に再走査した — [T-2067] に関する新規項目は無い。

## 1. 母集合 (b) の確定 — real

批准床値 (`RatifiedFreeze`) を静的 loader で得る production callsite は **9 箇所 / 9 関数 / 7 module**。
親の AST 走査、段 2、レンズ A の 3 者が独立に同じ 9 件へ到達した。

| callsite | 強制状況 |
|---|---|
| `s8b_oracle_manifest.py:1205` | `:1206` 狭い選択 API |
| `s8b_oracle_report.py:2547` | `:2548` 狭い選択 API |
| `s8b_oracle_judge.py:749` | `:750` 狭い選択 API |
| `s8b_verdict.py:828` | `:829` 狭い選択 API |
| `s8c_result_judge.py:2076` | `:2078` 狭い選択 API |
| `s8b_oracle_driver.py:644` (`gate_check`) | `:664` full launch validation |
| `s8b_oracle_driver.py:1335` (`run_block`) | `:1351` full launch validation |
| `p3_autonomous_workload_trial.py:4957` (`run_trial`) | **未強制** — C06 予算群 |
| `s8b_oracle_driver.py:496` (`_gate_check_core`) | **未強制** — standalone gate の二読 fallback |

**強制済み 7 / 未強制 2。** `RatifiedFreeze` の構築点は loader 内 1 箇所だけで、
`RatifiedFreeze(` の直接構築を禁じる負例が `test_s8b_ratified_freeze.py:2501` に実在する。

**この数の母集合と除外:** 母集合は `orchestrator/**` + `tools/**` の Python における
「直接呼出しと通常の alias」。除外は test、docs、output、定義・docstring・annotation。
**全動的 Python 実行の閉包ではない** — `getattr` / `importlib` / `partial` / 三重引用符内 script /
entry point の各盲点はレンズ A が個別に検査し、target への production 呼出しは 0 件だった。

**権威ある閉包の在否:** `load_ratified_freeze` の caller を exact 一致で固定するメタテストは
**repo に実在しない** (レンズ A が切らない検索で確認)。したがって 9 件の正本は今回の AST 走査である。
対照的に `build_observations` は `test_s8b_oracle_report.py:5812` で caller = `main` の 1 本に、
`_gate_check_validated` は `test_s8b_oracle_driver.py:5517` で caller = `run_block` の 1 本に、
`verify_manifest` は `test_s8b_oracle_manifest_contract.py:31/99` で exact 4 file に固定されている。

## 2. 未強制 2 群の帰属

**(2-1) C06 予算群 (`p3_autonomous_workload_trial.py:4957`)** — D1371 が「現時点では実装しない」と
裁定済み。再評価の発火条件 (C05 schedule authority の着地) は**未成立**である。
レンズ B が現物で確認した機序: `p3_autonomous_workload_trial.py:2074` の schedule authority resolver が
無条件に `AutonomousTrialError` を送出するため `reserve_all_cells:4964` へ到達しない。
[T-2159] の台帳も「裁定済み (D1567) → 上流待ち」のままである。
**したがって D1371 の前提 (gate を置いても成果物の値・受理集合・参照は変わらない) は今日も成立する。**
本 wave では触らない。

**(2-2) standalone gate の二読 fallback (`s8b_oracle_driver.py:496`)** — 1236 は「private core の
self-load であり public v2 wrapper はこの形で到達させない」として母集合から外していた。
**この除外は本 wave の独立検算で破れた。** ただし到達条件は限定される。

- `gate_check:615` と `_gate_check_core:459` は同じ `_load_verified_freeze` を同じ引数で呼ぶ。
  loader (`s8b_freeze_io.py:41-68`) は file の bytes だけで結果が決まる純関数で、
  driver 内に両読の間で書き換える処理は無い (親が実物で確認)。
- よって発火には「初回 read が失敗し、直後の再 read が成功する」外部要因の状態変化が要る。
  レンズ A の具体 trace: `:615` が ENOENT で失敗 → 別 process が active 世代と**完全に同じ bytes** を
  その path へ配置 → `:459` が成功 → `:487` の v2 枝 → `:496` の loader → `:503` の sha256 一致で
  拒否されず → `:589` から allowed を返しうる。公開入口は CLI `main:2055`。
- **受理されうる freeze は active 世代そのものに限られる** (`:503` の sha256 完全一致要求)。
  別の freeze が混入する経路ではない。欠けているのは active 世代自身の選択 identity 検査である。

## 3. (c) — 元の内容は閉鎖、library 非対称は production 到達 0 件

1236 が閉じた内容 (public builder/writer の private 化) は今日も成立する
(`s8b_oracle_manifest.py:818` の private 定義、負例 `test_s8b_oracle_manifest.py:1248`)。
1345 が挙げた library 経路 (`verify_manifest` → `build_observations` / `judge_oracle` /
`verify_oracle_verdict` → `judge_combined`) は、**repo 内の production 到達経路が 0 件**である。
official artifact を生む continuation は report / judge / verdict の 3 CLI だけで、いずれも
先に選択強制を通す。`verify_manifest` の caller は権威ある閉包テストが exact 4 file に固定している。
**ユーザーの scope 制約 (仮想リスク向けの gate・検査の追加は scope 外) により実装しない。**
閉じていない範囲として明記する (絶対規律 7)。

## 4. (d) — 閉鎖を維持

genuine 正例・負例 4 node (`test_s8b_ratified_verify.py:1031/1046/1060/1075`) は今日も実在し、
**stub を使わず**実 admission 台帳を設置し、実 `load_ratified_freeze` で取り直し、
launch 経路と狭い API の両方へ通している。D1504 が却下した「loader と選択 assert の両方 stub」の形では
ない (旧 stub 版 2 本は別 node として併存)。再実装しない。

## 5. 段 2 の実装案は不採用 — 裁定パッケージへ送る

段 2 は `_gate_check_core` の v2 authority を exact `LaunchValidatedFreeze` に限定し、
`:496` の self-load と raw 注入を authority から外すことを推奨した。**本 wave では実装しない。**

- **DW-G04:** 発火条件を満たす既存 artifact path も計測 ID も brief に書けない (二読 race でしか
  発火しない)。同節はこの場合「設計メモに留める」と定める。
- **DW-G05:** 放置時に成果物 (certified 選択・レポート・台帳) の値・受理集合・参照が
  安定入力でどう変わるかを示せない。示せない must-fix は nit / backlog とする。
- **ユーザーの scope 制約:** 仮想リスク向けの gate・検査・台帳・一般化の追加は scope 外。
  レンズ B も独立に同じ判定を出した (MF-1)。段 2 が併せて提案した「初回失敗→二回目成功」の
  regression node は、既存入力の回帰ではなく mock による仮想遷移の新設に当たる。
- **ただし新事実がある。** D65 決定 (5) は「public gate_check は v2 で必ず自己検証」と裁定しており、
  この分岐ではその不変条件が成立していない。承認済み裁定に対する新事実なので、DW-S04 に従い
  親が不採用で閉じず、**裁定パッケージとしてユーザーへ返す**。

**ユーザーへ返す択一:** `_gate_check_core` の v2 fallback を (i) 現状維持のまま台帳へ記録する、
(ii) exact `LaunchValidatedFreeze` 必須へ縮めて D65 決定 (5) の不変条件を全分岐で成立させる。
(ii) を採る場合は実装面のため Codex `role=author` と変異事前登録が要る。

## 6. carry の訂正

carry の (b)「load-only consumer 3 群」は 1202 当時の値であり stale。1236 が 4 群へ訂正済みで、
(a) 着地後の現況は「未強制 2 群」である。letter の指す内容も drift している —
(c) は 1202 の旧 public builder → 1236 で private 化完了 → 1345 で別内容の library 経路、と
同じ letter に別の主題が載っている。
**「1345 が母集合の再監査を意図して (b) を再開した」可能性は否定できない** (レンズ B) ので、
意図は断定せず「数は stale・letter の意味が drift」と書く。

## 7. 変異と受入

実装面の差分ゼロにつき **DW-S04 により変異 matrix を免除**する。**受入全走は免除しない。**
記録 commit の後に受入を投入する (DW-O12)。

## 8. 所見の採否一覧

| 出所 | 所見 | 裁定 |
|---|---|---|
| 段 2 | 母集合 9 callsite / 未強制 2 | **real・採用** |
| 段 2 | `:496` は公開 CLI から到達する | **real (条件付き)・採用** — 到達条件を明記する |
| 段 2 | core を token-only 化する実装 | **不採用** — DW-G04 / DW-G05 / scope 制約。裁定パッケージへ |
| 段 2 | 新規 regression node の追加 | **不採用** — 仮想遷移の新設 |
| レンズ A | `:496` の二読 TOCTOU trace (must-fix) | **real・分類訂正として採用**、実装は不採用 |
| レンズ A | 注入 seam に production caller 無し (nit) | **real・採用** — 独立群として数えない |
| レンズ A | loader の権威ある caller 閉包は不在 (nit) | **real・採用** — 件数の出所を AST と明記する |
| レンズ A | AST 走査の盲点に実在 target 無し (nit) | **real・採用** — 母集合の射程を限定して書く |
| レンズ B | MF-1 コード変更案の撤回 | **採用** |
| レンズ B | MF-2 母集合を「実在未強制 C06 1 群 + fallback 別記」へ訂正 | **採用 (表現を調整)** — 2 群と数え、到達条件を併記する |
| レンズ B | (c) library 到達は production では refuted (nit) | **real・採用** |
| レンズ B | (d) の genuine 4 node は real (nit) | **real・採用** |
| レンズ B | D1371 射程内・C05 未着地 (nit) | **real・採用** |

## 9. 段の遷移

実装しないと裁定したので `4 → 7 → 8 → 9` とする。成果物は insight 1 本と spool fragment
(worklog / decisions)。docs 編集は local main を取り込んだ後に当てる。
