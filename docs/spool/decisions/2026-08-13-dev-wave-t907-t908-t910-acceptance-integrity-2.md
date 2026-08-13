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

## {{D:non-attributable-acceptance-requires-pytest-failure-rc}}. 非帰属受理は「テスト失敗で落ちた走行」に限る

**決定:** 受入 command が非 0 で終わったときに receipt を発行してよいのは、
**`child_rc` がちょうど 1** であり、かつ `tools/check_acceptance_reds.py` が
**`rc == 0` かつ `status == "non-attributable-only"`** を返し、その receipt の
`log_sha256` が待ち手自身が捕獲した log の hash と一致したときだけとする。
`status == "green"`、`rc == 1`、`rc == 2`、`child_rc` が 0 でも 1 でもない非 0 は、
いずれも fail-closed とする。bypass flag と環境変数は作らない。

**理由:**
- **checker の `rc == 0` は 2 つの意味を持つ。** `status = "non-attributable-only"` は
  「赤があり、全て tested main 単独でも落ちる」、`status = "green"` は
  「log から赤 nodeid を 1 件も取り出せなかった」である。後者は非帰属の証拠ではない。
  受入が非 0 で終わったのに赤 nodeid が 0 件になる経路 (collection error、internal error、
  crash、xdist worker の異常終了) は実在するので、`rc == 0` だけを条件にすると
  **崩れた受入が受領証を得る**。
- **赤の非帰属は「走行が崩れたこと」を説明しない。** pytest が summary まで出したあとに
  wrapper が signal・後段 gate で落ちても、log 中の赤が全て非帰属なら受理されてしまう。
  `tools/run_tests.py` の main は `return subprocess.call(cmd, cwd=_REPO)` で pytest の rc を
  そのまま返すので、テストが落ちた走行は 1 である。`run_tests.py` 自身の失敗は
  `_DELETION_GATE_RC = 13` / `_PEGASUS_DISPATCH_RC = 16` など 1 以外になる。
  したがって `child_rc == 1` は「テスト失敗だけで落ちた」の機械的な言い換えである。
- **log は待ち手が所有する。** 親が渡した log を受け取る形だと、任意の過去 log を渡して
  非帰属判定を素通りできる。待ち手が child の stdout/stderr を直接ファイルへ捕獲し、
  その bytes の hash を receipt へ束縛することで、checker の入力が当該走行のものであることが
  監査可能になる。

**却下した選択肢:**
- 批准済み既知赤 nodeid の registry を置く — ユーザー裁定で不採用。registry は肥大すると
  実質的な fail-open になり、批准手順の設計と期限管理を伴う。checker による単独再走は
  同じ判断を機械化でき、人手の批准を要さない。
- checker 自身に受入走を所有させる ([T-1019] の対立案) — ユーザー裁定で不採用。
- `child_rc != 0` すべてを非帰属判定へ流す — 上記のとおり受理集合が
  「テスト失敗で落ちた走行」から「何らかの理由で落ちた走行」へ広がる。
- checker rc=2 を「判定不能だが赤は非帰属らしい」として通す — `DW-O18` が
  「rc=2 は判定不能で非帰属の根拠にしない」と定めた向きに反する。
