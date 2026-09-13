---
schema: izanagi-spool-v1
ledger: failures
authored: 2026-09-14
wave: dev-wave-t2566-tail-formal-driver
seq: 3
---

## 新規

### {{F:scheduler-format-assumed-from-another-batch-system}}. 別方式のジョブ管理系の出力形式を前提にした問い合わせが、実機では説明文を返して rc=0 で終わる [恒真ゲート] [テスト代表性]

- 事象: 本走 driver の初版が、ジョブ開始時刻と予約時間を
  `qstat -f -F json <id>` の JSON から読む前提で書かれていた。これは別方式 (OpenPBS) の形式である。
  **この計算機の方式では `-F` は項目選択の flag であり、JSON ではなく項目一覧の説明を出して
  rc=0 で終わる。** 放置すれば本走は 1 cell も測らずに `run_workload` の冒頭で止まる。
- 根本原因: 環境の実形式を確かめず、広く知られた別方式の慣行を実装した。
  既存の投入 script が同じ問い合わせを text で解析している事実 (と保存済みの実出力) を参照しなかった。
  試験も新しい問い合わせを 1 度も通していなかったので、静的レビューまで検出されなかった。
- 恒久対応: {{D:static-tail-cohort-identity-and-refusal-reporting}} と同じ wave で、
  既存投入 script の text 解析を正本として合わせ、ジョブ識別子の接頭辞の扱いも揃えた。
  保存された実出力を入力にした検査を追加した。
- 再発検知: 保存済みの実出力に対する解析検査。説明文・識別子不一致・予約欠損を拒否する負例も置いた。

### {{F:codex-sandbox-lacks-scheduler-binary}}. 実装子の sandbox にジョブ管理系の実行 file が無く、共通テスト runner が 1 件も走らずに終わる [手順漏れ] [テスト代表性]

- 事象: 段 5 の実装子 2 名がともに `tools/run_tests.py` を叩き、
  投入 preflight (`qstat -Q`) が rc=1 になって `rc=16` で停止した。**両名とも実走 0 件**で
  「実装済み・未実走」を報告して終わった。親が同じ木で自走 harness を叩くと普通に走り、
  39 passed / 8 failed が出た。
- 根本原因: 子の sandbox には PATH にジョブ管理系の実行 file が無い (親からは rc=0 で通る)。
  親が実装子の prompt に自走 harness の叩き方を書いていなかった。
  さらに両名とも、runner が生成した `output/pegasus-dispatch/**/receipt.json` を
  「所有外 file を編集した」と判断して作業を止めた。これは runner の生成物であって子の編集ではない。
- 恒久対応: 実装子・fix 子の prompt に、`tools/run_tests.py` を使わず
  `PYTHONPATH=. python3 <test file>` の自走 harness を使うこと、runner の生成物は所有違反でないことを
  明記する。以後の fix 子 4 本はこの指示で実走できた。
- 再発検知: 子の完了報告に実走 nodeid が 1 件も無いときは、投入経路の失敗を疑って
  親が同じ木で自走 harness を叩き直す。
