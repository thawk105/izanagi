---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-08-18
wave: dev-wave-t1333-t1310-workload-profile
seq: 1
title: workload 表 entry を scale の単一権威にした — 新しい検査が repo の受入 fixture に埋まっていた矛盾を捕まえた (コード + テスト + 記録、branch worktree-dev-wave-t1333-t1310-workload-profile、変異 matrix = PLACEHOLDER)
---

## 本文

- **本 wave の主要な収穫は、実装より先に既存の矛盾を暴いたことである。**
  新設した検査が、wave 前から `orchestrator/tests/test_trial_registry.py` に埋まっていた
  scale の矛盾を捕まえた。同じ registered holdout 試行の fixture が、descriptor では
  `{records: 1000000, threads: 48}` (封印された arm 権威)、campaign `search_config` では
  `records: 100000, threads: 4` (探索 scale) という 2 つの矛盾する scale を持ち、
  **それが受入を通っていた。** [T-1349] が警告した「descriptor と実 benchmark が食い違ったまま
  両方緑になる」状態の実物である。
- **Layer-3 は descriptor について自己整合しか見ていなかった。** `descriptor_schema` と
  `descriptor_sha256` を照合するだけで、`scale` を producer entry から再投影していなかった。
  さらに `_perf_for` が実際に構築した `PerfConfig` は**どの artifact にも残らず**、
  perf sink 単独の scale 変異は cell から不可視ですらなかった。段 3 レンズ B の所見である。
  本 wave は実 `PerfConfig` の scale を cell へ残し、descriptor・cell perf・campaign・entry の
  四者を Layer-3 が独立再投影して照合する形にした。
- **裁定の前提が 2 点崩れたので、実装せずユーザー再裁定へ返した。** 詳細は下記 [T-1310] の
  更新本文と正本に置く。(1) 正式 run は今日いかなる経路でも起動できない
  (`admit_registered_launch` が要求する `EffectivePreregistration` は 12 predicate 全部が
  SATISFIED であることを要求し、現 snapshot の SATISFIED は 0 件)。
  (2) 正式 run は自分が書く `campaign.lock` で repo scan の 0-hit を壊す (未記録の新事実)。
- **したがって正式専用の Layer-3 受理枝を実装しない形 (形 A) を採った。** 起動できない以上
  置いても発火せず、`DW-G04` と [T-822] 第 6 回裁定の「空振りする検査を置いて保証があるように
  見せる方が悪い」に反する。正式 selector は fail-closed で明示的に止める。
  この判断で段 2 プランが予測した 40 件超の波及が大幅に縮んだ。
- **段 6 の敵対レビュー 2 本が独立に同じ根本原因を指し、親の焦点走とも一致した。**
  段 5 実装が正式 entry を `WORKLOADS` へ入れたため、正式 selector を**渡さなければ**
  fail-closed を迂回でき、裁定で実装しないと決めた正式 Layer-3 受理枝が暗黙にできていた。
  実装自身の fixture がそれを実証していた。正式 entry を `FORMAL_WORKLOADS` へ分離して閉じた。
- **段 5 実装に恒真な照合が入っていた。** `_ = (records, threads) == (1_000_000, 48)` と
  比較結果を捨てる形で、C01 が sink 内の整数 literal の存在しか見ないことを利用して
  検査を通すだけのものだった。実際に `raise` する形へ差し戻した。
- **変異の事前登録を焦点再レビューの帰属判定で削った。** 当初 12 件を登録したが、
  レンズ B と焦点再レビューが独立に「M9 は等価変異、M11 は `u4-holdout-workload` に mask、
  consumer call-edge は未 pin」と判定した。そのまま走らせていれば
  **偽の KILLED を台帳へ記録していた。**
- **赤は 4 → 1 → 18 → 13 → 0 と単調に収束し、既存テストの期待値を 1 つも緩めずに閉じた。**
  production 側の検査も弱めていない。fix 4 巡目で更新したのは fixture の scale と
  それに伴う campaign ID の再計算だけである。`DW-O16` の 3 巡上限を 1 巡超えた理由は、
  巡が敵対レビューの NO-GO 反復ではなく親の実測による収束であり、原因が毎巡 1 つに
  絞れていたためである。
- **C01 は `workload-projection-mismatch` から `ratified-generation-reference-absent` へ遷移した。**
  status は `UNSATISFIED` のままで、満たしたふりにはなっていない。他 11 条件は不変。
  更新した snapshot は実 repo の 1 箇所だけで、負の control は更新していない。
- **`dev_wave_wait.py producer` が出力ゼロで rc=0 早期終了する事象を 2 回観測した**
  (fix4 / fix5)。いずれも producer は生存しており `.done` も成果物も無かった。
  `DW-O01` の「完了は `.done` と exit code だけで判定」が既に覆っており誤進行は防げた。
- **`--lane` は consult 段専用**という制約で、段 6 review の起動が rc=2 で 2 本とも即死した。
- **エージェント工数**: codex 子 10 本 (plan 1・consult 2・author 1・review 2・fix 5・focus 1)。
  段 5 と fix は `gpt-5.6-sol` @ high、段 2・3 は `gpt-5.6-sol` @ max。
  codex 子は本 wave でも pytest を 1 件も実走できず (全巡 `qstat -Q rc=1` / 子 rc=16)、
  測定は親が 10 回の焦点走で引き受けた。
- 正本 = `output/insights/2026-08-18_t1333-t1310-workload-profile/README.md`

## 次の一手差分

### 完了

- [T-1333] 形 1 を実装した。workload 表 entry が `{ycsb, records, threads}` を持ち、
  producer の 3 sink と Layer-3 の campaign-chain 検査が同じ entry から scale を導出する。
  正式 entry は `FORMAL_WORKLOADS` に分離し、単一 resolver を通す。
  探索側の cell bytes・campaign identity preimage は不変
  (canonical sha256 3 件と campaign ID `4b75e24e` / `136086b0` / `4ac6e6a4` で pin)。
  remaining: none
  base: f2789f5726bbd09d1bde949e65d43e3f1c9a0b00efea8c25e4beaedc90a2c5b7

- [T-1349] module 表 `s8b_holdout_freeze.HOLDOUTS` / legacy freeze 文書 / producer entry の
  四 key を canonical bytes で比較し、producer entry を `_descriptor_for` へ通した
  content digest が arm resolver の封印 digest と一致することを要求する形で閉じた。
  正式 entry の `ycsb` は deep copy し、module 表との可変 alias を断った。
  remaining: none
  base: c1f6760625cb9ee97705bf7a6fc276e1155f2d00364de84f7bc775d68f99b896

### 更新

- [T-1310] **P2・択 (β) の源の受理は実装済み → 起動可能化はユーザー再裁定待ち**:
  `load_legacy_freeze` の `legacy-v1` 源を暫定源として受理し、consumer が独立に再ロードして
  path / sha256 / 四 key を再導出して照合する形を実装した。`load_ratified_freeze` は呼ばず、
  non-certifying の新 flag も作らない (既存の強制連鎖を使う)。
  **しかし「正式 scale の実測を開始できるようにする」という択 (β) の目的は達成していない。**
  `admit_registered_launch` が要求する `EffectivePreregistration` は
  12 predicate 全部が SATISFIED であることを要求し、現 snapshot の SATISFIED は 0 件である。
  未登録の探索経路は holdout workload を `u4-holdout-workload` で明示的に拒否する。
  正本の塞ぐ点 (3) は「manifest が無い」までを記録していたが、
  **全 predicate SATISFIED という形の要求は未記録だった。**
  **択 = (a) 正式 non-certifying 専用の launch admission mode を新設する。
  (b) 8c registered 経路を通さず oracle driver 側または手動で測る
  (ただし oracle も `LaunchValidatedFreeze` → `RatifiedFreeze` を要求し v2 未発効で塞がる)。
  (c) 択 (α) へ戻る。** 親の推奨は (a) — (β) を選んだ意図を実際に実現するのは (a) だけである。
  正本 = `output/insights/2026-08-18_t1333-t1310-workload-profile/README.md`
  base: d49049d9cd0be5e52c126e3ee6d1e81f7f5773e72425ac21bb4f5d3a652fe61a

### 新規

- {{T:formal-run-writes-conjunction-hit}} **P1・新規・ユーザー裁定要**:
  正式 rr80 / rr20 run が書く `campaign.lock` は compact canonical JSON で
  `ycsb_rratio` / `ycsb_zipf_skew` / `ycsb_rmw` を**同一ファイルに**並べるため、
  run 自身が守るべき repo scan の 0-hit を壊す。凍結文書自身の positive control が
  既存 campaign.lock を conjunction hit として記録しており実証済みの形である。
  `output/exploration/` は `.gitignore` に無く、repo scan は untracked 非 ignore file も列挙する。
  前 wave の敵対レンズは source / test / fixture / golden / docs までしか見ておらず、
  **run 自身の生成物は射程外だった。** 即時の赤にはならない
  (live の全 repo scan `launch_validate` は `RatifiedFreeze` を要求し v2 未発効で到達不能) が、
  v2 発効時に起動を塞ぐ。**択 = (a) 正式 run の run root / campaign root を repo 外へ強制する。
  (b) 凍結の unknownness 主張を「凍結時点の歴史的記録」と明示して事後 scan を要求しない。
  (c) 明示的な exempt path を裁定する。** 親の推奨は (a)。

- {{T:oracle-holdout-scale-unbound}} **P2・新規**:
  `s8b_oracle_driver._perf_for_holdout` は freeze **文書**から `PerfConfig` を作り、
  module 表とも producer entry とも束縛されていない。schema-valid な `records=2000000` を
  入れると通過する。`DW-G03` は producer + oracle の独立 2 例で満たすが、
  oracle は本 wave の編集面外であり scope 拡張の裁定が要る。
