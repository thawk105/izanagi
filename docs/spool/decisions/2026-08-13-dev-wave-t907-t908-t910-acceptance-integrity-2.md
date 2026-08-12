---
schema: izanagi-spool-v1
ledger: decisions
authored: 2026-08-13
wave: dev-wave-t907-t908-t910-acceptance-integrity
seq: 2
---

## {{D:acceptance-authority-threat-model}}. 受入権威の防御対象は事故であって偽造ではない

**決定:** dev-wave の受入 receipt が防ぐ対象は、**待ち手を経由しない直接走の結果を権威ある受入
として記録してしまう事故**である。同一 Unix user による意図的な偽造は防御範囲外と明記し、
偽造対策にしか効かない機構 (interpreter attestation、暗号署名、実行 bytes の attest、
残存子孫の reap 保証) は receipt の要件に含めない。

**理由:**
- receipt の producer と consumer は同じ user 権限で走るので、その user は receipt を
  直接書ける。防御を謳っても成立しない保証を並べることは、恒真な assert を増やすのと同じである。
- 起票理由になった実例は、待ち手の deadlock を迂回して直接走した運用上の事故だった。
  安価に閉じられるのはこの経路であり、費用対効果もここに集中している。
- 範囲を明記しないと、後続レビューが偽造耐性の不足を blocker として繰り返し起票し、
  実装が青天井に膨らむ。

**却下した選択肢:**
- 偽造耐性まで要件に含める — 同一 user 前提では達成不能で、達成したふりになる。
- 範囲を書かずに実装だけ最小にする — 何が守られていないかが台帳から読めなくなる。

## {{D:land-requires-waiter-acceptance-receipt}}. land は待ち手 receipt を必須入力にする

**決定:** `tools/dev_wave_land.py` は `--acceptance-wave` / `--acceptance-receipt` を必須引数とし、
待ち手が発行した receipt を lock 内で検証してからでなければ main を 1 bit も進めず、
`landed` / `already-landed` のいずれの成功も返さない。欠落・不正・予約 temp 名前空間・
束縛不一致は `RC_AUDIT` = 23 で拒否する。CLI flag・環境変数・警告化の逃がし道を作らない。
検証の位置は provenance 監査と lock 再検証の後でよいが、fold-recovery の `already-landed`、
`locked_main == tested_tip` の `already-landed`、ff-only merge の**すべてより前**に置く。

**理由:**
- receipt を出すだけで誰も読まなければ「直接走の結果は記録不可」は機械で担保されない。
  consumer を持たない証跡は規律ではなく飾りである。
- 守るべき不変条件は「有効な receipt なしに main を進めず成功も返さない」ことだけで、
  provenance 監査との前後関係は要求ではない。前に置くと、tools/ を symlink として commit する
  既存の provenance 検査と rc 期待が両立しない。
- receipt の発行は temp へ書いて fsync し、holder / main SHA / TTL 残量を再確認してから
  `os.rename` する二段階とする。final path の存在だけが「待ち手が成功終端まで到達した」
  証拠になり、fsync 済みの temp が残っても land が予約名前空間として拒否できる。

**却下した選択肢:**
- `tools/run_tests.py` 側に同等 gate を足す — 稼働中の全 wave の受入へ即座に効くため
  ユーザー裁定で不採用。
- receipt があるときだけ検証する fail-open — 検証意味論を弱める方向であり規律 2 に反する。
- 互換 bypass flag を置いて旧待ち手の受入を通す — 逃がし道は必ず既定経路になる。
  旧待ち手で受入済み・未 land の wave には受入 1 走の再実行を求める。
