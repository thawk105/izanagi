---
schema: izanagi-spool-v1
ledger: failures
authored: 2026-08-16
wave: dev-wave-floor-reseal-authority
seq: 3
---

## 新規

### {{F:mutation-node-space-selfconsistency}}. 変異 harness の報告 node と collection 実在検査の空間が内部で食い違い、どちらの形で登録しても一致しない [手順漏れ] [恒真ゲート]

- 事象: 変異本走が `MISMATCH` を 1 件返した。実体は変異の生存ではなく node ID の表記差である。
  probe 走が報告した失敗 node のうち real-repo serial の 2 件は
  `...::test_build_and_write_leave_repo_tree_unchanged[nested]@real-repo` の形で、
  末尾に xdist の実行グループ名が付いていた。この形をそのまま期待 node へ登録すると、
  harness の起動前検査が「期待 node が pytest collection に実在しない」で rc=2 停止する。
  グループ名を落とした素の nodeid で登録すると起動は通るが、
  比較段で報告側 (グループ名つき) と一致せず `MISMATCH` になる。
  **書き手が選べるどちらの形でも一致しない。**
- 根本原因: harness は失敗 node を pytest の**報告空間** (xdist `--dist loadgroup` が
  `@<group>` を付ける) から採り、期待 node の実在検査は**collection 空間** (グループ名なし) に対して
  行う。2 つの空間を正規化せずに突き合わせている。F224 は同じ症状を
  「書き手が非 ASCII の parametrize ID を逐語で書いた」機序で起こしたが、本件は
  **機構側の自己不整合**であり、書き手の手順では回避できない。
- 恒久対応: {{T:mutation-node-space-selfconsistency}} で harness の両空間を正規化する
  (報告 node から `@<group>` を剥がしてから照合し、期待 node も同じ正規化を通す)。
  実装までの間は、この形の `MISMATCH` を SURVIVED と数えず、
  失敗 node 数と非 serial node の完全一致を根拠に KILLED として erratum つきで記録する。
- 再発検知: 期待 node に `@` を含む変異 spec は harness が起動前に rc=2 で拒否する
  (今回それが発火した)。正規化を実装したら、real-repo serial node を期待に含む変異を
  1 本以上必ず登録し、`MISMATCH` にならないことを本走で確認する。
- 併記する実測: 本 wave の本走は baseline PASSED、KILLED 11 / MISMATCH 1 / SURVIVED 0 /
  TIMEOUT 0。MISMATCH の M01 は失敗 node 19 件のうち 17 件が完全一致し、
  差は real-repo serial 2 件のグループ名だけだった。

## 再発

### F24

- **再発: 2026-08-16** — `tools/dev_wave_wait.py producer` が
  **`.done` 不在・成果物不在・producer 生存 (pid 3178700、実行 41 秒経過) のまま
  rc=0・出力ゼロ**で返した。2026-08-12 / 08-13 の再発と同型である。本 wave の追加事実は、
  当日の local main 取り込みで `tools/dev_wave_wait.py` が 348 行規模で変更された直後に
  発生した点で、待ち手側の改修が進んでも同じ形が残ることを示す。
  既存の恒久対応 (成果物実在 + `.done` の exit code + producer 死の 3 点照合) が有効に働き、
  `ps -p` で生存を確認して誤完了を弾いた。以後の待ちは
  `.done` 出現と `kill -0` による producer 生死だけを見る条件ループへ切り替えた。

### F224

- **再発: 2026-08-16** — 同じ症状 (期待 node が collection に実在せず起動前 rc=2) を
  別機序で起こした。書き手の逐語ミスではなく、harness 自身が報告した node をそのまま
  登録したことによる。詳細と恒久対応は {{F:mutation-node-space-selfconsistency}}。
