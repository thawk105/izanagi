単独段 dispatch: stage=fix; sandbox=workspace-write; parent=/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1851-unit-c2

必読事項の射影 (いずれも絶対パス。読めなければ即停止し、その旨を出力に書いて終わること):

- **作業 root (書込み可。編集は所有 path だけ)**: `/work/1/SFC/tanab/izanagi/.codex/worktrees/t1851-c3-fix3`
- **親の段 4 裁定**: `/home/SFC/tanab/.claude/jobs/460f7d58/tmp/t1851unitsel/s4-adjudication.md`
- **段 6 レビュー A (RA-1 / RA-2 / RA-3 の根拠)**: `/home/SFC/tanab/.claude/jobs/460f7d58/tmp/t1851unitsel/out-s6-ra.md`
- **段 6 レビュー B (RB-1 / RB-2 の根拠)**: `/home/SFC/tanab/.claude/jobs/460f7d58/tmp/t1851unitsel/out-s6-rb.md`
- 実装子の報告: `out-s5-a1.md`, `out-s5-a2.md`, `out-s5-b.md`, `out-fix1.md`, `out-fix2.md`
  (すべて `/home/SFC/tanab/.claude/jobs/460f7d58/tmp/t1851unitsel/` 配下)
- 契約の正本: `/work/1/SFC/tanab/izanagi/.codex/worktrees/t1851-c3-fix3/output/insights/2026-09-08_t1851-unit-c1b-sealed-terminal-evidence/contract-v3.1.md`
- 共通規律: `/work/1/SFC/tanab/izanagi/.codex/worktrees/t1851-c3-fix3/CLAUDE.md`

# 段 6 fix 3 — 敵対レビュー 2 本が出した real 所見 4 件を閉じる

所見が API 面と呼び手面へ同時に及ぶため、**1 単位で 4 file を所有する** (親の裁定)。

## 所有 path (編集はこの 4 つだけ)

- `orchestrator/campaign/s8b_floor_attempt_launcher.py`
- `orchestrator/campaign/s8b_floor_campaign.py`
- `orchestrator/tests/test_s8b_floor_attempt_launcher.py`
- `orchestrator/tests/test_s8b_floor_campaign.py`

**docs は編集しない。commit しない。`git add` もしない。**
`s8b_attempt_registry.py`、`s8b_terminal_evidence.py`、`s8b_holdout_admission.py`、
`attempt_registry_core.py` は**変更しない**。

## 直す所見 4 件

### F-1 (RA-2 / RB-1、重大) — competing session が実測していない probe payload を記録する

production の competing 分岐は launcher が実測した raw probe を捨て、
`{"rc": 0, "stdout": "", "stderr": "", "competing": True}` を合成して journal / session へ渡している
(`s8b_floor_campaign.py:8954-8969`)。しかし canonical classifier は `rc == 0` かつ空 stdout を
`inconsistent-output` として拒否する組合せである (`orchestrator/calibrator/runner.py:327-365`、
`s8b_floor_campaign.py:1695-1706`)。**成果物が実際には観測していない probe bytes を証拠として持つ。**

**直し方**: phase 1 の封印 pre-probe が保持している**実 raw probe** を、campaign が正直に記録できる
形にする。封印 object から raw を読み取る狭い read-only 経路 (不変な copy を返す) を launcher 側へ足し、
campaign はそれをそのまま記録する。**合成 tuple は除去する。**

- 封印の目的は competing 判定の偽造防止であって raw の秘匿ではない。既存の単段経路も
  terminal の `probe_before` に raw を載せている。**一貫させること。**
- one-shot・偽装拒否・issuer 検査を**弱めてはならない**。raw 読み取りで seal が消費されない形にする。
- test: competing 分岐で journal / session に記録された 4 field が、probe が返した実値と**等値**である
  ことを検査する正例。合成値へ戻す変異が赤になること。

### F-2 (RA-1) — cut-6 の M+A- resume 経路に blocker 1 が残る

crash で marker だけ存在し ledger row が無い状態 (M+A-) を cut-6 が replay 対象として返し
(`s8b_holdout_admission.py:5230-5311,5330-5352`)、runner が `_run_session()` に戻す
(`s8b_floor_campaign.py:6409-6436`)。resume 後の新しい pre-probe が competing だと、
**既存 marker を残したまま competing completion を書く**ため、inspector が
`attempt-ledger-coverage-mismatch` で必ず拒否する (`s8b_holdout_admission.py:6733-6741`)。

**直し方**: この経路で competing completion を書かない。**inspector は 1 bit も緩めない。**
既存 marker がある replay で pre-probe が competing になったら、
**fail-closed で明示的な理由とともに停止する** (成果物を作らない)。
理由文字列は既存の分類語と衝突しない新しい exact な語にし、test で pin する。

- test: crash cut を作って **certified 経路**を通す。既存の cut-6 test は injected `measure_fn` の
  legacy 経路なので (`test_s8b_floor_campaign.py:10674-10735`)、それとは別に新設する。
- 「marker を消す」「inspector の連言を外す」「competing を無視して launcher を呼ぶ」形は禁止。

### F-3 (RA-3) — v5 prefix 被覆 test が result producer を通っていない

`test_v5_prefix_covers_every_consumed_non_competing_session` は全 session 後に
`_capture_floor_attempt_registry_prefix()` を直接呼んで同じ registry と比べるだけで、
`assemble_result()` / 通常 finalize / `result["attempt_registry"]` を通らない
(`test_s8b_floor_campaign.py:15035-15089`)。live verifier は報告 `row_count` までの prefix 一致で
受理するため (`s8b_attempt_registry.py:1050-1086`)、**producer が古い prefix を result に載せる変異でも
この test は赤にならない。**

**直し方**: この test を、**複数 clean session の result を実際に組み立て**、
result の proof が**最後の launcher terminal 後の live 全行数・head と一致する**検査へ再照準する。
1 件目の terminal 後の古い prefix を載せる変異が赤になることを、実際に確かめて報告する。

### F-4 (RB-2) — campaign が launcher の module attribute 経由で adapter 境界を迂回している

campaign が `s8b_floor_attempt_launcher.attempt_registry` / `.profile8b` / `.attempt_registry.core` を
参照している (`s8b_floor_campaign.py:8702-8704,8785,8922-8926,9014-9017`)。
既存 guard は import 名・AST `Name`・文字列だけを見るため検出しないが、
**campaign が registry profile と core canonicalization の直接 consumer になっている。**

**直し方**: launcher 側に**狭い名前付き surface** を用意し、campaign はそれだけを呼ぶ。
`attempt_registry` / `profile8b` / `core` を module attribute 経由で辿る参照を**全て除去する**。

- 新しい surface は「module の再 export」にしない。campaign が実際に必要とする操作だけを
  名前付き関数として出す。
- **既存の境界を緩める方向 (guard を弱める、campaign に直接 import を許す) では解決しない。**
- test: campaign source に `attempt_registry` / `profile8b` / `core` への間接参照が
  1 件も無いことを検査する node を新設する (AST か source 走査)。

## 禁止

- 赤を skip・xfail・deselect・assert 緩和・期待値反転で消さない。
  実装が誤りだと判断したら**直さず報告して止まる**。
- 所有外 file を編集しない。**inspector と marker 規則を緩めない。**
- `FORMULA_ID`、凍結成果物、`attempt_registry_core.py` に触れない。
- 行番号 pin (`s8b_floor_campaign.py` の 4707 と 8636) を動かさない。
  新 helper は 8636 より後ろへ置き、前方の物理行数を保存する。
- launcher の perf 述語の新しい直接 call を作らない。
- 期待値へ揮発 payload を焼き込まない。
- 出力へ結合文字 U+0300〜U+036F を使わない。

## 検査 (自分で実走する)

**`tools/run_tests.py` は sandbox では rc=16 になるので使わない。** 自走 harness を使う。

```
cd /work/1/SFC/tanab/izanagi/.codex/worktrees/t1851-c3-fix3
PYTHONPATH=. python3 orchestrator/tests/test_s8b_floor_attempt_launcher.py
PYTHONPATH=. python3 orchestrator/tests/test_s8b_floor_campaign.py
PYTHONPATH=. python3 orchestrator/tests/test_s8b_attempt_registry.py
PYTHONPATH=. python3 orchestrator/tests/test_s8b_terminal_evidence.py
PYTHONPATH=. python3 orchestrator/tests/test_ccbench_spawn_sites.py
PYTHONPATH=. python3 orchestrator/tests/test_official_perf_closure.py
```

6 file すべての passed/failed の実数を報告する。走らせていないものを緑と書かない。

## 出力形式

```
## 総括
(3-5 行)

## F-1 の直し方と検算 (実 raw が記録されることの実測)

## F-2 の直し方と検算 (certified 経路の crash cut test)

## F-3 の再照準と検算 (古い prefix を載せる変異が赤になることの実測)

## F-4 の狭い surface (新しい関数名と、除去した間接参照の全列挙)

## 新設した test (nodeid / 正例・負例)

## 実走結果 (command と passed/failed の実数)

## 残った懸念
```
