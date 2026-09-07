---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-09-08
wave: dev-wave-t1396-c04-reject-started
seq: 1
title: [T-1396] 判定器 C04 の到達対象へ reject_started_trial を足した — 恒真だった関門が変異 2 件を殺すようになった (コード + テスト + insight、branch worktree-dev-wave-t1396-c04-reject-started、変異 2/2 KILLED + 等価 1 SURVIVED)
---

## 本文

- 契約 JSON の condition 4 は到達経路を 3 件要求していたが、判定器 `_evaluate_c04` は 2 件しか
  見ていなかった。D1292 に従い 3 件目 (`run_trial preflight -> reject_started_trial`) を足した。
  詳細と実測は `output/insights/2026-09-08_t1396-c04-reject-started/README.md`。
- **契約側の exact-set は既に正しかった。** `test_s8c_preregistration_invariant.py` の
  `MACHINE_CONTRACT_FUNCTION_CHECKS` は C04 の 5 symbol を pin しており
  `reject_started_trial` を含む。欠けていたのは判定器だけだったので、同 file は変更していない。
- **brief 前の read-only probe で「実装しても現行 main の C04 判定は変わらない」ことを先に測った。**
  判定器を変えずに `_declared_call` を process 内で包んで 3 件目を問い合わせ、
  `EVIDENCE_UNDEFINED / completion-proof-not-machine-checkable` が保たれることを確認した。
  この結論は同一 commit・実 resolver に限定する。token-only fixture・過去 commit・
  将来の production source へ一般化しない (段 3 レンズ B の指摘)。
- **段 3 の相談 2 本が独立に、当初案の冗長な存在検査を退けた。** 段 2 プランは
  `_functions(registry)` 側にも `reject_started_trial` の存在検査を足す案だったが、
  「先行する `_declared_call` が真なら後段は必ず真、定義欠落は先行層で先に return する」ため
  効果がゼロで、負例の単一理由性を壊す。判定器の変更は 1 行だけにした ({{D:c04-no-redundant-registry-check}})。
- **段 6 の敵対レビュー 2 本とも must-fix ゼロ。** 出た nit は 3 件で、いずれも受理集合を
  広げないと確認して不採用にした。うち焦点走の取り残し 2 file
  (`test_s8c_cli_entrypoints.py` / `test_s8c_gate_report.py`) だけは安価なので実走した (25 passed)。
- **変異の帰属が例外的にきれいに立った。** 判定器は contract loader 束縛 file なので
  drift mask に埋もれることを警戒したが、probe の観測では MU-1 / MU-2 が赤にした node は
  新しい負例 2 本だけで、mask の混入はゼロだった。owner の 2 本は `evaluate_all` を直接呼び
  `capture_contract_loader_binding` を通らないためである。
- 段 5 の実装子は Pegasus dispatch 障害で pytest を起動できず「実装済み・未実走」と申告した。
  テストの実測はすべて親が行った。
- 段 1 で `--reasoning` を author 段へ渡して rc=2 で 1 回落とした (DW-C01 の argv 制約)。
  launcher は起動前に落ちるので receipt は残らず、同じ prompt のまま再投入できた。

## 次の一手差分

### 完了

- [T-1396] 判定器 C04 の到達対象へ `reject_started_trial` を足し、変異 2 件で恒真でなくなった
  ことを示した。契約側 exact-set は既に正しく変更不要だった。
  remaining: none
  base: c725cd0f67b7b0218ec5c74bd0d16eaec5a2e07240ef42d766fc5daba3e72201

### 新規

- {{T:c04-call-site-position}} **P3・ユーザー裁定待ち**: 判定器 C04 が契約の書く呼出し**位置**を
  検査していない件を裁定する。`_ReachabilityExplorer` は `main` からの may-reach 集合だけを見るので、
  `reject_started_trial()` を preflight から重複拒否の後ろへ移しても、短絡死コードにしても
  target は残る。既存の 2 件 (`mark_experiment_indeterminate` / `forbid_trial_restart` が
  crash handler の中にあること) も同じく未検査である。争点は「C04 の machine-checkable claim を
  到達可能性に限定するのか、呼出し位置・支配関係まで含むのか」。位置・支配関係の検査は
  新しい解析機構になるため T-1396 では実装していない。根拠は
  `output/insights/2026-09-08_t1396-c04-reject-started/verbatim/s4-adjudication.md` と
  同 `verbatim/s3-consult-lensA.md`。
- {{T:c04-callee-body-and-field-paths}} **P3・ユーザー裁定待ち**: 同じ軸の残り 2 点を裁定する。
  (a) C04 は callee 本体を検査しないので、`trial_registry.reject_started_trial` の本体を
  `pass` にしても判定器・正例・負例はすべて同じ結果になる。(b) 契約 condition 4 の
  `field_paths` (`trial_lifecycle.started_once` / `trial_lifecycle.restart_forbidden`) を
  判定器が一切読まない。実体は `trial_registry.py` の state 定義と更新に存在するので、
  架空の懸念ではなく現行の契約不一致である。{{T:c04-call-site-position}} と同じ争点軸なので
  併せて裁定するのが安い。
