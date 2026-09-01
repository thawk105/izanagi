---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-09-01
wave: dev-wave-t1806-prereg-c10-fieldpaths
seq: 1
title: [T-1806] 事前登録契約 C10 の証拠 field を広げ、判定器版 v7 と条件凍結 g12 を発行した
---

## 本文

D967 の確定裁定を実装した。契約 C10 の `field_paths` は 12 件、実装の
`S8C_CROSS_BINDING_FIELDS` は 13 件で、差分はちょうど `proposal_build_source_bindings` の
1 件だった。T-1749 (commit 1e10a081) が足した arm から source への因果束縛の証拠を、
契約が要求していなかったものである。

**契約 JSON だけを広げても正式 gate の検知力は 1 mm も増えない。** `_evaluate_c10` が照合するのは
契約ではなく Python 定数 `_C10_FIELDS` だからである。D967 が理由に挙げた「後から実装を弱めても
正式 gate が検知できない」を実際に解消するため、判定器側も同時に広げた。詳細は
{{D:c10-field-paths-single-binding-table}}。

### D967 の前提が後発裁定で成立しなくなっていた

D967 は「既存 campaign が `E1-stale` になることを正直な migration として記録する」と定めるが、
**D967 の翌日に下されたユーザー裁定 D1163 (絶対規律 7 の新設) が、その拒否経路そのものを
名指しで撤去していた。** 親は段 1 brief でこれを見落とし、段 3 の敵対レンズが独立に反証した。
親が D1163 の本文、`artifact_admission._require_verifier_epoch_for_purpose` の現行実装、
tracked `campaign.lock` 32 件のうち閉包 hash を持つもの 0 件を実測して確認した。
**本件で新たに失効する campaign は 0 件である。** D967 の 3 行動はすべて実行し、記録だけを
事実へ合わせた。詳細は {{D:d967-e1-stale-premise-superseded}}、経緯は F67 の再発項。

親が brief で (P1) の補強に使った「D967 が E1-stale を明言している以上、閉包内 .py の変更を
意図している」という推論は取り下げた。D1163 下ではどちらでも E1-stale は起きないため成立しない。
(P1) は「判定器が読むのは `_C10_FIELDS`」という一次根拠だけで立つ。

### 段 3 と段 6 が独立に同じ欠陥へ到達した

段 2 の plan は drift 検査を片方向の包含 `all(x in y)` で書き、それを C06 の既存 idiom だと
引用した。**実際の C06 の `field_paths` idiom は完全一致比較で、片方向の `all` は
`reachable_from` 用の別 idiom である。** 段 3 の 2 レンズが独立にこれを指摘し、段 6 の
レビュー 2 本も独立に同じ結論へ達した。裁定で plan の形を却下し、
`(実装 literal, 契約 field path)` の単一対応表から両側を導出して完全一致で比較する形へ
差し替えた。

段 6 のレビュー 2 本は、事前登録した変異の対のうち**条件版 (生存側) が実装されていない**ことも
独立に指摘した。親の段 5 prompt の抜けである。fix で、値照合を実際に持つ source と
literal を残したまま照合だけを恒真化した source を対で作り、両者が同じ終端になることを
通常の緑のテストとして記録した。

### 変異が pin の射程を機械で露出させた

**同一の変異が、見る層によって結果が変わることを実測で示した。**

| 変異 | C10 の gate で見る | producer の functional test で見る |
|---|---|---|
| `M01-COND-E2` (literal を残し E2 digest 等式だけ恒真化) | **SURVIVED** (0 node) | **KILLED** (2 node) |

走 B が落とした 2 node の 1 つは
`test_verify_s8c_cross_binding_rejects_each_reference_mutation[proposal_build_source_bindings]`
で、今回追加した field そのものの参照変異テストである。値束縛は producer 側が守っており、
C10 の gate は literal の実在までしか見ていないことが、同じ 1 つの変異で両側から確定した。

matrix 全体は KILLED 3・SURVIVED 1・MISMATCH 0、baseline はいずれも PASSED、
`repo_head=3bd9b5d3a`。`M04` (完全一致を片方向の包含へ戻す) が KILLED になったことは、
段 3・段 6 が出した must-fix の修正に実際の検出力があることの直接の証拠である。

### 変異設計で親が 2 回間違えた (erratum、初回結果は消さない)

1. **過剰決定。** 初回の probe で `M01-UNCOND` と `M04` が 55〜60 node を落とした。
   `s8c_preregistration_evidence.py` が契約 loader 閉包の中にあるため、変異すると
   `capture_contract_loader_binding()` が壊れて campaign chain 系まで連鎖する。
   runner を C10 の述語 node へ絞って単一理由性を回復した。
2. **条件版の照合点が無検査だった。** 最初に選んだ
   `expected_path != path or proposal_sha256 in source_artifacts` を恒真化しても、
   producer 側 `test_autonomous_trial_completeness.py` を全部走らせて **0 node しか落ちなかった**。
   実際に検査されている E2 digest 等式 (`preimage_sha256 != source.source_bytes_sha256`、
   `test_t1749_m03` が kill する) へ再照準した。
   **この照合点に負の対照が無いことは実測された事実**であり、本 wave の scope 外の所見として残す。

### 実測した検査

計算ノードへ dispatch した焦点走。login node は pytest が hook で拒否され、
cgroup も headroom ゼロだった。

| 対象 | 結果 |
|---|---|
| `test_s8c_preregistration_predicates.py -k c10` | 5 passed (4.06s) |
| `test_s8c_preregistration_core.py` + `_invariant.py` | 403 passed, 5 skipped (24.60s) |
| `test_autonomous_trial_completeness.py -k cross_binding` | 18 passed (10.29s) |
| `test_acceptance_schedule_order.py` + `test_real_repo_serialization.py` | 135 passed, 1 skipped (50.45s) |

**5 skipped の中身は `test_s8c_preregistration_invariant.py` の candidate-fixture node 5 本で、
まさに g12 と v7 を実 repository に対して検証する node である。** 2026-08-29 の T-1434
ユーザー裁定で growth hold にかかっており、解除条件は明示のユーザー指示のみ。既存の hold で
あって本 wave が作った状態ではなく、迂回もしていない。したがって g12/v7 の正しさは、
これらのテストではなく次の実測に支えられている。

- `prepare_revision` の `spurious-revision` guard を通過した (契約が実際に変わった機械的証拠)
- 親が g12 の全 field を g11 と 1 件ずつ比較し、`section6_condition_hashes` 12 件が
  不変であることを確認した (規範文書を変える必要がなかったことの実測)
- 契約 hash `26f7bd47…` を親と段 3 レンズ B が独立に再計算して一致した
- g11 の raw hash `8fb7802e…` が g12 の `supersedes_sha256` と一致することをレンズ B が独立確認した

### 段 8 の候補は予算に入らず実施しなかった

実測した候補が 1 件あった。`DW-O09` の pin 閉包検索を repo root で走らせると submodule と
別 wave の worktree を舐めるため 120 秒で返らない。本 wave で 2 回踏み、いずれも背景送りになった。
探索根を絞れば即座に返る。

該当 leaf 節へ 1 文 (約 125 bytes) を統合しようとしたが、`DW-O09` は L2 単節予算 1000 bytes の
上限ぎりぎりで、追加すると 1125 bytes になり `check_docs` が赤になった。D730 / D782 の手順を
適用した。**既存記述の削減では 125 bytes を安全に空けられず** (残る記述はいずれも
F30 / F39 / F78 由来の義務)、**独立 3 例には達していない** (本件は 1 例) ため、
上限は引き上げず「実施しない」へ落とした。予算のために安全義務を削る選択は採らない。
同型を別 wave が独立に 2 例目として実測したら、そのとき例外収容を検討できる。

### 並行 wave との統合で、merge 前に静的特定した相互破断

同じ条件 10 を扱う別 wave と同一 file を別方向から書き換えたため、land 前に相手の差分を読んだ。
**merge して赤を見る前に 3 件を特定した。**

1. 相手が新設した述語 (`pass` だけの reader を拒否する) に、本 wave の新設 fixture 2 つが掛かる。
2. 本 wave が契約を締めた結果、相手の「充足する」fixture が包含不成立で落ちる。
   **これは回帰ではなく意図した検出力である。** 直す場所は契約側でなく fixture 側で、
   裁定により相手が land 前に自分で修正した。
3. 本 wave の対照 fixture が `str.replace` の byte 一致で導出されており、
   元 fixture の編集でアンカーが静かに不発になりうる。`str.replace` は一致しなくても
   例外を出さず元をそのまま返す。

**総括すると、静的検査の限界は検査の質ではなく軸の列挙にある。** 3 件はいずれも差分を読めば
出るものだったが、実際には探そうとした軸だけが見つかった。相手の子は「個数を pin する test」を
探して `replace` の軸を探さず、本 wave の親も指摘を受けるまで自分の `.replace()` を見なかった。
一晩で観測された 6 軸を、発火する走の種類つきで
`output/insights/2026-09-01_t1806-prereg-c10-fieldpaths/parallel-wave-static-check-axes.md`
へ残した。新規の失敗型としては立てない — 6 軸のうち複数は既存の型の再発であり、
新規で立てると台帳が重複する。

### 子の工数

plan・consult 2 本・author・review 2 本・fix の 7 子はすべて `gpt-5.6-sol` / xhigh。
実装子と fix 子はいずれも pytest を実走できず「実装済み・未実走」と正直に申告した
(codex sandbox 内で `qstat -Q` が uid 認証に失敗し rc=16、local も cgroup headroom ゼロ)。
**同じ `qstat -Q` は親からは rc=0 で通る。** 子の sandbox 固有の制約であって
クラスタ側の不調ではない。実テストはすべて親が dispatch して走らせた。

## 次の一手差分

### 完了

- [T-1806] 事前登録契約 C10 の `field_paths` を新 field まで広げ、判定器の照合集合と
  契約整合検査を追随させ、判定器版を v7 へ上げ、条件凍結を g12 として再発行した。
  D967 が想定した E1-stale は後発の D1163 により発生しないことを実測して記録した。
  remaining: none
  base: 49eee7f7628d47044c8b51eb7ffb26d8373e7e8e140b6beb8947a6b13b5050ed

### 新規

- {{T:cross-binding-source-artifact-path-check-uncovered}} **P3・新規**:
  `_cross_binding_source_bindings` の
  `expected_path != path or proposal_sha256 in source_artifacts` を恒真化しても、
  `test_autonomous_trial_completeness.py` の全 node が緑のままだった (本 wave の変異 probe で実測)。
  この照合点に負の対照が無い。等価変異なのか本当に無検査なのかの切り分けと、
  必要なら負の対照の追加を別 wave で扱う。本 wave では scope 外として実測だけ残した。
