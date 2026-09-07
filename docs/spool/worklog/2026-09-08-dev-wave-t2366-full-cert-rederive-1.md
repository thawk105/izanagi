---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-09-08
wave: dev-wave-t2366-full-cert-rederive
seq: 1
title: [T-2366] full certification の materializer に acquisition からの exact 再導出を入れた — partial 側の射影で受理集合を縮小 (コード + テスト、branch worktree-dev-wave-t2366-full-cert-rederive、変異 6 件中 5 KILLED / 1 等価 SURVIVED、期待 node 完全一致)
---

## 本文

- **partial の射影で閉じた。** full (v4) 側の validator は既存の形・identity 検査を渡された evidence に
  据え置いたまま、その後ろで acquisition を読み直し、collector と同じ `_canonical_full_report` で
  report を再導出して完全一致を要求する。設計は {{D:a2-full-materializer-exact-rederivation}}。
- **段 3 の 2 レンズが独立に同じ穴を指した。** plan は既存 identity 検査を読み直した evidence へ一括で
  切り替える形だったが、それは `acquisition_path` だけ正しく他 field を改竄した dict を読み直しで
  置換して通す向き (受理集合の拡大)。据え置き + 後置へ直した。同じ 2 本が helper 冒頭の
  `_require_materializable_authority` 欠落、変異 old の partial 側との重複、brief の記述 3 点
  (manifest 無効分岐の到達性、P4 の「拒否」→「canonical 化」、production 経路では恒真) も real にした。
- **段 6 の敵対レビュー 2 本の real 所見 3 件。** (a) `return canonical_full_evidence` を
  `return evidence` へ弱めても全テストが緑のまま → P4 の意味を実体で名指しする正例を足した。
  (b) 読み直し後の receipt chain 検査が無く、partial の受領証を full の表層 field で包んだ evidence が通る →
  partial 側の同型検査を写し負例を足した。(c) `dict ==` は `True == 1` を同一視する → real だが partial 側の
  既存比較も同じ形で、ユーザー指示 (partial をそのまま射影・新しい検査層を作らない) の範囲外として
  実装せず {{T:a2-report-compare-json-typed}} へ送った。焦点再レビューは所見ゼロ。
- **正例・負例は実体を名指しした。** 負例 4 (偽 status、偽 effects、偽 driver_rcs + indeterminate report、
  partial 受領証の偽装包装)、正例 1 (受領証 bytes を差し替えても成果物は読み直した bytes)。いずれも
  変更前の実装で materialize が成功することを実装子が一時変異で確認し、親も現物で読んだ。
- **変異 6 件中 5 KILLED / 1 等価 SURVIVED、期待 node 完全一致。** 事前登録 6 件 (再導出を外す / 読み直しを外す / 常に拒否 = 過剰拒否の正例 / 等価 / 戻り値を渡された evidence へ / 読み直し後の chain 検査を外す) を probe → final の 2 段で計算ノード dispatch に流し、5 KILLED / 1 SURVIVED (等価変異 M04)、MISMATCH 0、期待 node と完全一致 (M01: 負例 3、M02: 3、M03: 正例 9、M05: 1、M06: 1)。 逐語と台帳は
  `output/insights/2026-09-08_t2366-full-cert-rederive/`。
- **受入台帳。** `test_paper_story_a2_certification.py` は 175 node 中 106 node しか登録されておらず、
  本 wave の新規 5 node を含む 69 node を正本 producer の `--add-only` で登録した (Codex author)。
  main 取り込み前の台帳に対する初回出力は捨て、取り込み後の台帳に対して取り直した。
- **main 側の欠陥を発見した (本 wave の差分ではない)。** main 先端 c12e25078 が `.codex/worktrees/*` の
  gitlink 110 本を commit しており、取り込んだ worktree で `git submodule update --init --recursive` と
  `git submodule status --recursive` が fatal、provenance 監査は同 commit を 1 違反にする。所有 session
  (T-2412) へ通知し、是正は別 session が前進修正で担当中と返答があった。
- **子の工数。** codex 子 9 本 (plan 1、consult 2、author 1、review 2、fix 3、focus 1)。fix 2 の台帳出力は
  破棄した。実装子・fix 子は自走 harness で緑を実走し、親は計算ノード dispatch で 173 → 175 passed を実測した。

## 次の一手差分

### 完了

- [T-2366] full certification の materializer に exact 再導出を入れ、変異と受入で閉じた。
  remaining: none
  base: 87b75ec9b1baa6e366e8a87271f78246c39d3d7132d1ee1b8bbc048d5bfc80c5

### 新規

- {{T:a2-report-compare-json-typed}} **P3・新規**: A-2 certification の materializer の再導出一致
  (`report == expected`) は Python の `dict ==` で `True == 1` を同一視するため、JSON 型だけ違う偽造
  report (例 `legacy_repetitions_observed: 1 → True`) が certified 成果物として通る。partial (v2) と
  full (v4) の両側を同時に `_canonical_json(report) == _canonical_json(expected)` へ変えるかを裁定する。
  production CLI では到達せず、`materialize` の直接呼出し境界だけの穴。
