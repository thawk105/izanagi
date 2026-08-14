---
schema: izanagi-spool-v1
ledger: failures
authored: 2026-08-15
wave: dev-wave-t1092-receipt-diagnostics
seq: 3
---

## 新規

### {{F:fail-closed-instruction-reversed-published-success}}. 親の fix 指示が受入証発行後の成功を失敗へ倒した [手順漏れ]

- 事象: 診断を足す小 wave の fix 第 2 巡で、`_publish_acceptance_receipt` の
  signal mask 復元失敗を**無条件に** fail-closed (rc=70) にしたため、
  **receipt を publish し終えた後**に signal を受けた走行が成功 (rc=0) から失敗へ変わった。
  既存テスト `test_signal_after_receipt_publish_does_not_reverse_success` が回帰で赤になり検出した。
- 根本原因: 親が fix prompt に「mask 復元単独失敗も fail-closed rc=70」と書き、
  **`receipt_published` が真の場合を除外し忘れた**。子は指示どおり実装した。
  受入証はディスク上に存在し走行は実際に成功しているのに、それを失敗に倒していた。
  緑の走行を理由なく捨てるのは、この wave が無くそうとしていた事象そのものである。
- 恒久対応: {{D:acceptance-receipt-failure-diagnostics}} — 受入証を書き終えた後の失敗は
  成功を覆さない。fix prompt の制約に「緩める方向だけでなく**過剰に拒否する方向**の変更も禁止」を
  明記する (規律 2 の対称形)。fix 第 3 巡で、publish 失敗が無く**かつ**未 publish のときだけ
  fail-closed にする条件へ訂正した。
- 再発検知: `test_signal_after_receipt_publish_does_not_reverse_success` (期待値を 1 文字も
  変えずに緑へ戻すことを fix の受入条件にした)。変異 C1 が診断生成の例外で rc/stage が
  置換されないことを固定する。

### {{F:merged-new-failure-path-outside-redaction-discipline}}. 並行 wave が新設した失敗経路が非漏洩規律の外に出た [計測汚染]

- 事象: 同じ 2 ファイルを触る 2 wave の合流で、git の自動マージが競合なしで成功し、
  焦点走も 276 passed で緑だった。しかし main 側 wave が新設した waiter bytes gate の
  失敗経路は、共通の attestation 形式を使わず手組み JSON で detail を作っており、
  初期束縛失敗時に**例外メッセージ (`str(exc)`) を運用 log へ出しうる**状態だった。
  不正な SHA 文字列も原文のまま載りうる形だった。
- 根本原因: 「診断に何を載せてよいか」の規律は既存の失敗経路にしか適用されておらず、
  新設経路が規律の外側で書かれた。テストが緑なので静的にも実行前にも見えない。
  マージが競合しなかったため、合流時に中身を読む契機も無かった。
- 恒久対応: 実装面を両親のいずれとも異なる状態にする merge は Codex `role=author` が
  合成結果を監査して所有する (`docs/ai-provenance.md` の実装面 Codex author 契約が
  この監査を機械的に要求する)。本件では監査で検出し、同じ merge commit の中で
  共通形式へ統合し、型名と整数 errno だけに絞った。
- 再発検知: 例外メッセージと絶対 path が detail に出ないことの回帰テストを
  `orchestrator/tests/test_dev_wave_wait.py` へ追加した。
  `check_ai_provenance.py` が実装面 path の merge に Codex author 行を要求し、
  監査なしの通過を機械的に塞ぐ。
