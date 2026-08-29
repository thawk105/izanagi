---
schema: izanagi-spool-v1
ledger: failures
authored: 2026-08-29
wave: dev-wave-t2005-b4-projection-registration
seq: 1
---

## 新規

### {{F:verifier-moved-check-strands-single-caller-path}}. 検査を verifier から呼び出し側へ移し、その verifier だけを通る別経路を無防備にした [恒真ゲート] [手順漏れ]

- 事象: B-4 の受理記録検証で、record が宣言する projection と事前登録文書の projection を
  照合していた 1 手を `verify_b4_admission_record` から pair 生成点へ移した。pair 経路では
  より強い検査 (文書 3 値すべてを live 値と照合) に置き換わったが、起動器の bootstrap 経路
  (`p3_b4_launcher.issue_context` → `launch_bootstrap_impl`) は同 verifier しか通らず
  pair 生成点を通らないため、**その経路の受理集合が変更前より広がった。**
  実 driver と sidecar は照合なしで起動できる状態だった。
- 根本原因: 親が段 4 の裁定で「文書 3 値が live と一致し record 値が選択 driver の live と
  一致すれば対応は導ける」と推論したが、**その 2 つの照合がどちらも走る経路 (pair) しか
  数えていなかった。** 同じ verifier を呼ぶ別の production 呼び出し側を列挙していない。
- 恒久対応: `DW-S04` の「gate の禁止は署名で書き、通る正例を 1 つ添える」に加え、
  検査を移動・削除する裁定では **移動元を呼ぶ全 caller を列挙し、移動先を通らない caller が
  無いことを実測する**。本 wave では `verify_b4_admission_record` の caller 20 箇所
  (production 3、test 17) を焦点再レビューが数え、既定値経路の不在まで確認した。
- 再発検知: bootstrap 経路の負例テスト
  `test_bootstrap_rejects_stale_or_driver_mismatched_projection_before_sidecar`
  (実 driver・sidecar・executable 探索・artifact 作成のいずれにも到達しないことを assert する)。
  変異 M1 / M4 がこの経路を単独で倒す。

### {{F:doc-implementation-mismatch-resolved-by-widening}}. 文書と実装の食い違いを、実装を緩める向きで解決した [恒真ゲート]

- 事象: 敵対レビューが「事前登録文書の `<slug>` と `<64 hex>` という記述は実装の受理集合より
  広い」と指摘した。fix 子はこれを**実装側を広げて**解決し、model の `claude-opus-` 接頭辞
  要求を落とし、hash に大文字を許した。canonical record は接頭辞と小文字のみを受理し、
  `projection_sha256` も小文字しか produce しないため、受理集合を無用に広げただけだった。
- 根本原因: 「記述と実装が食い違う」という所見が、どちらを正とするかを含んでいなかった。
  fix の指示も向きを明示していなかった。
- 恒久対応: D1283 が定めた向き — 文書の文言が実装より厳しいときは docs 側を実装へ合わせる。
  逆向き (実装が文書より厳しい) の場合は**文書を実装へ合わせる**のであって、
  受理集合を広げてはならない (絶対規律 2)。fix の指示には向きを明記する。
- 再発検知: 期待値行の字句負例
  `test_closed_critic_expectation_row_requires_claude_opus_slug_and_lowercase_ascii_hex`
  (非接頭辞 model と大文字 hash を拒否する)。変異 M5 / M6 が文法の緩和を倒す。

### {{F:background-job-notification-is-not-a-waiter-verdict}}. 背景 job の完了通知が、子の生存中に完了として届いた [手順漏れ]

- 事象: dev-wave の子 (`nohup setsid bash <launcher>`) を harness の背景 job として投入した
  段 6 で、harness が「completed exit code 0」を通知した時点で子はまだ生存し `.done` も
  存在しない、という事象が 3 回続いた (敵対レビュー 2 本と fix 1 本)。さらに
  `tools/dev_wave_wait.py producer` を同じく背景 job として張ると、待ち手自身が出力ゼロ・
  rc=0 で即座に完了扱いされ receipt file を書かなかった。前景で同じ引数を走らせると
  正しく `producer-timeout rc=70` を返し、待ち手の実装には欠陥が無いことを確認した。
- 根本原因: 背景 job の完了通知は wrapper shell の終了を見ており、`setsid` で切り離した
  本体の終了を見ていない。待ち手を同じ経路で張ると、待ち手も本体を待たずに終了扱いされる。
- 恒久対応: `DW-C00` の「完了は `.done` 非空で決める」を守る。加えて
  **待ち手を harness の背景 job として張らない — 前景で走らせる。**
  本 wave は `.done` で判定していたため誤判定には至っていない。
- 再発検知: 待ち手を張った直後に receipt file の実在を確かめる。receipt が無いまま rc=0 で
  戻ったら待ち手が走っていない。
