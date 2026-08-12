---
schema: izanagi-spool-v1
ledger: failures
authored: 2026-08-12
wave: dev-wave-t930-hold-no-bypass
seq: 3
---

## 新規

### {{F:waiter-premature-zero}}. 待ち手が producer 生存中に rc=0 で即時返却した [手順漏れ]

- 事象: `tools/dev_wave_wait.py producer` が、`.done` も成果物も存在せず producer が生きている
  状態で **rc=0・出力空**のまま返った。本 wave で 2 回 (段 6 焦点再レビュー、変異 harvest 走)。
  いずれも producer 起動の 2〜3 秒後に待ち手を張った直後で、実際の完了はその 7〜12 分後だった。
- 根本原因: 未特定。`.done` 不在での早期返却経路がある。再現条件は producer 起動直後の待機開始と
  相関して見えるが、本 wave では原因追跡まで行っていない (実測 2 例のみ)。
- 恒久対応: **待ち手の rc=0 を完了判定に使わない。** 完了は「成果物実在 + `.done` の存在 +
  producer の死」の 3 点照合で判定し、揃っていなければ待ち手を張り直す。
  待ち手を落とすときも producer を殺さない。
- 再発検知: 3 点照合を通らない完了申告は、その場で偽完了として扱う。本 wave では 2 回とも
  この照合が偽完了を捕まえ、張り直した待ち手が正しい完了時刻を拾った。

### {{F:octopus-merge-breaks-s8c-history}}. 4 親の merge が受入全走を恒久的に赤にした [手順漏れ]

- 事象: 2026-08-13 00:45:56 に main へ入った merge `d1de13ad`「Merge 3 rulings branches into
  land wave」が**親 4 つの octopus merge** だったため、
  `test_s8c_preregistration_invariant.py::test_candidate_freeze_matches_contract_and_generation_chain`
  が恒久的に赤になった。単独再走でも再現し、複数の並行 wave が同時に踏んだ。
- 根本原因: `orchestrator/campaign/s8c_preregistration.py:1305` の `_assert_history_transition`
  は親 0 / 1 / 2 の遷移だけを定義し、3 親以上を `PreregistrationError("octopus-merge")` で
  拒否する。**この契約が「repo 履歴に octopus merge を作ってはいけない」という運用制約を
  含意していることが、merge を作る側の手順のどこにも書かれていなかった。**
- 恒久対応: branch を束ねるときは 2 親の merge を繰り返す。3 親以上の merge を作らない。
  既に入った分は当座 (a) 既知赤運用とし、履歴契約の拡張可否は未裁定として rulings へ残した
  (一次控え `rulings-inbox/2026-08-13-known-red-octopus-merge.md`)。
- 再発検知: 受入全走。ただし**発生から検知まで全 wave が赤を踏む**ため、merge を作る手前で
  親数を見るのが本筋である。既知赤の機械可読な登録機構は repo に存在しない (実測) ので、
  当面は台帳の記録と周知で運用する。
