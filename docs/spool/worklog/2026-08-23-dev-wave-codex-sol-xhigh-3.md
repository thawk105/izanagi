---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-08-23
wave: dev-wave-codex-sol-xhigh
seq: 3
title: dev-wave の codex を全段 gpt-5.6-sol / reasoning=xhigh へ張り替えた (コード + docs、branch worktree-dev-wave-codex-sol-xhigh、変異 matrix = baseline PASSED・M1〜M5 5/5 KILLED・SURVIVED 0・MISMATCH 0)
---

## 本文

- **ユーザー裁定:** 「codex のモデルを gpt5.6sol extra high にしてください。全て。研究が壊れそうな
  くらい進捗がおかしくなっている。これは私の絶対的な決定です。」D514 (全段 luna @ max) の
  supersede であり、根拠は運用選好。詳細と正直な効果評価は {{D:codex-sol-xhigh-all-stages}}。
- **effort の向きを親から明示的に申し送る。** `xhigh` は `max` の 1 段下である。D514 直前と比べると
  全段 1 段下がり、D514 より前の sol 期と比べると段 2 / 3 が 1 段下がり段 5 / 6 が 1 段上がる。
  段 2 / 3 の引き下げは D207 が A/B 装置に限定した領域だが、本 wave は手続きを経ていない
  ユーザー裁定 supersede である。**検出力への正味の影響は測っていない。**
- **本 wave 自身が新権威の実証点になった。** 段 6 の 2 レンズと焦点再レビューは sol @ xhigh で
  実走し (receipt の `recorded_model=gpt-5.6-sol` / `recorded_effort=xhigh`)、親が独立に見つけた
  2 件を再現したうえで、親が見落としていた 1 件を追加検出した。
- **棄却しなかったが scope 外にした real 所見が 1 件。** 段 6 レビュー B が
  「段 2 / 3 の effort pin は subprocess argv へ機械強制されていない」を must-fix で出した。
  親は real と認めたうえで **本 wave が作った欠陥ではない** (D207 期から同じ構造で、機械強制は
  T-1362 が author / fix にだけ入れたもの) と裁定し、launcher の新規配線を要するため scope 外として
  {{T:plan-consult-effort-argv-wiring}} へ送った。焦点再レビューもこの裁定を妥当と評価した。
- **変異の再照準と erratum (DW-M02)。** 段 4 で登録した変異 2 件は docs 側への変異だったが、
  `docs/dev-wave/{operations,workers}.md` を変異させると「working tree が authority commit と
  異なる」層が先に発火し、単一理由にならない。実効 gate である checker / launch_authority 側へ
  再照準した。初回 probe では `check_docs.py` の DW-S02 expected 値を変える形が **309 node** に
  膨れた (expected を変えると checker が実 docs を拒否し、checker を呼ぶ全テストが連鎖で赤になる)。
  DW-M03 に従い「DW-S02 の pin 登録タプルごと外す」形へ差し替えて 6 node に収束させた。
  初回登録は消さず本項に残す。
- **実測した小さな罠。** `tools/dev_wave_wait.py acceptance --help` は help を出さず
  `error: stage=cli-usage rc=2` を返す。引数一覧は `_acceptance_parser()` を読む必要がある。
  `--check-only` は `--max-wait-seconds` と併用できない。
- **親の手順ミス 1 件 (実害なし)。** 変異 harness の走行中に spool fragment を tree へ書き、
  harness が untracked file 検出で fail-closed 中止した (rc=2)。baseline は PASSED まで済んでおり
  被害はない。commit してから再走した。「変異走行中は tree へ書かない」は既知の規律である。
- **偽完了 2 回。** {{F:repin-search-misses-incoming-value}} と F24 再発を参照。いずれも
  `.done` の実体確認で捕捉し、待ち手を張り直した。実害ゼロ。
- **非帰属の赤 1 件。** `test_exploration_external_root_keeps_wave_clean` は長期の既知赤
  ([T-1079] 所有)。単独走でも 3.11s で赤になり、本 wave の差分と経路が無関係。D662 項目 4 に従い
  本 wave へ帰属させない。
- 工数: codex 子 7 本 (plan 1・review 3 (うち 1 本は evidence 不備で再走)・author 1・fix 1・focus 1)。
  親 = 裁定・docs 編集・統合 commit・全実測。

## 次の一手差分

### 新規

- {{T:plan-consult-effort-argv-wiring}} **P2・新規**: 段 2 / 段 3 の reasoning effort を
  docs pin から subprocess argv へ機械強制する。現在 `snapshot_authority()` が読む effort 節は
  `DW-S05-A` / `DW-S06-A` / `DW-S06-C` だけで、`derive_launch()` は plan / consult へ
  `effort=None` / `effort_authority="unbound"` を返す。launcher はこの 2 段でだけ caller の
  `--reasoning` を必須とし、その値をそのまま argv に入れるため、docs と checker が `xhigh` で
  一致していても `--stage plan --reasoning max` が通る。T-1362 が author / fix へ入れた強制を
  plan / consult へ広げる形になる。実装時は plan / consult の caller effort を変異させ、
  argv が docs 値から逸脱すれば KILL する subprocess 境界変異を登録する。
