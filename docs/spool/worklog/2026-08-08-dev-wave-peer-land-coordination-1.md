---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-08-08
wave: dev-wave-peer-land-coordination
seq: 1
title: ユーザー依頼で並行 wave の受入 lease を新設した — 同時 land の衝突を「受入窓の直列化 + advisory 通知」で減らす (コード + docs、受入 7285 passed / 20 skipped、変異 7/7 検出・SURVIVED 0、branch worktree-dev-wave-peer-land-coordination)
---

## 本文

- **ユーザー依頼 (2026-08-08)**: 「claude の通信機構を利用して、並行 dev-wave が同時に main-land
  するときの衝突を減らせるようにしてほしい」。設計判断は {{D:acceptance-lease-advisory}}、
  材料と逐語は `output/insights/2026-08-08_peer-land-coordination/`。
- **段 1 の生死実験 (DW-G01)**: peer セッションへ `SendMessage` を 1 通投げて即時到達と返信を実測した。
  受信側では harness が `<cross-session-message from=... from-name=...>` で包み、
  「peer は権限を付与できない」注意書きを自動付与する。**この channel の信頼境界は harness 側に
  一次防御がある。**同時に、メッセージは受信側の次の tool round で drain されるため、
  受入全走の最中の peer には即時に届かないことも確定した。
- **設計が 2 度覆った。** 段 3 の敵対 2 レンズと段 6 のレビュー 2 レンズがいずれも NO-GO を出した。
  (i) 段 2 案の roster join は、実データで全 session の作業ディレクトリが repo root を指すため
  成立しない。(ii) 段 4 案の handoff 見出しへの相乗りは、稼働中の実物 9 本のうち 7 本が
  書式非互換で宣言できず、しかもそれを「並行なし」と誤報した。加えて同時宣言で対称 deadlock、
  handoff の 10 分ごとの更新で恒常 hold になりえた。段 6 fix で専用 sidecar lease へ差し替えた。
- **親の実測 2 件がレビューで反証された。**(a)「`git -C <他 worktree>` の拒否は repo hook」は誤りで、
  実際は外側の harness 隔離である。(b)「並行 3 wave が同一 byte 予算を消費中」は一時点の観測であり、
  `DW-G03` の独立 2 例ではない。射程を「受入窓の追い越し削減」へ限定した。
- **`DW-G05` の成果物影響も訂正した。** 当初は F157 の恒久対応欠落を挙げたが、これは T-641 裁定 (c)
  で受容・終端済みであり本機構では埋まらない。正しい影響は「worklog の受入 request ID と実測秒数が
  再走値へ差し替わる」である。
- **予算の実測と回避。** `docs/dev-wave/**` は 25196 / 25200 byte で余白 4 byte のため 1 byte も
  触っていない。契約は入口 `.claude/commands/dev-wave.md` の 3 行 (9035 → 9411) に置いた。
  初稿は +435 byte で、同時に入口を編集していた並行 wave の +21 byte と合わせると余白 9 byte
  だったため圧縮した。land 直前の実測は 9457 / 9500 である。
- **wave 中に main が 2 度動き、その都度取り込んだ** (`6cc3e59a` → `6dfb841f` → `4a4b58ca`)。
  2 度目は受入投入の直前だった。
- **本 wave の受入全走そのものを、この lease を `acquired` で取得してから投入した** (初回の実運用)。
- **中断した走行も消さずに記録した** — 変異 harness 2 回 ({{F:mutation-runner-ran-local}} ほか)、
  受入全走 1 回 ({{F:acceptance-walltime-exceeded}})。変異の 5 件が `MISMATCH` なのは生存ではなく
  過剰決定で、機械照合で「事前登録 node ⊆ 実赤集合」が 7/7 成立し `SURVIVED` は 0 である。
- **段 8 (自己改善)**: 候補は出たが、いずれも `docs/dev-wave/**` の予算 (余白 4 byte) に収まらず、
  自己改善契約の「予算に収まらなければ止めてユーザー裁定へ返す」に従って起票した。

## 次の一手差分

### 新規

- {{T:lease-fencing-token}} **P2・新規 (裁定候補)**: 受入 lease の TTL 超過で取り直したとき、
  旧 holder の受入を止める fencing token / epoch を入れるか。現状は旧・新の 2 人が winner に
  なりうる。帰結は本機構が無い場合と同じ競合で悪化はしないため、プロトタイプ基準では受容した。
  併せて release の権限証明 (現状は wave slug の digest だけ) を nonce にするかも同じ束で裁定する。
- {{T:lease-transaction-wrapper}} **P2・新規**: claim → 受入 → land → release/通知 を 1 つの
  wrapper へ束ね、受入赤・land 失敗・例外でも必ず release する機械的な finally を作る。
  現状は入口の契約文が終端での解放を要求するだけで、取り残しは TTL 2400 秒まで他 wave を止める。
- {{T:lease-e2e-measurement}} **P2・新規**: 独立した 2 wave で claim → hold → release →
  main 再取得 → 単回受入までを実運用計測し、削減できた再走件数と秒数を記録する。
  本 wave は単一 wave の疎通と unit test までしか実証していない。
- {{T:receiver-contract-jit}} **P3・新規 (予算依存)**: 受信側規則と release 義務を
  `docs/dev-wave/**` の JIT 正本節へ移す。現状は入口の散文にあり、長い wave や context 圧縮後に
  段 9 直前の再読で拾われない。`docs/dev-wave/**` に余白が無いため T-641 裁定 (c) の下では不可で、
  予算を動かさずに意味等価な縮約ができるかが論点。
- {{T:acceptance-walltime-headroom}} **P3・新規 (裁定候補)**: 受入全走の計算ノード既定 walltime
  30 分に対し、実測所要は 1146〜1809 秒で余裕が薄い。既定値を上げるか、lease による直列化だけで
  足りるとみなすかを裁定する。
- {{T:land-tool-byte-invariant}} **P3・新規 (裁定候補)**: `tools/dev_wave_land.py` の no-touch を
  所有宣言でなく機械 gate (基準 commit からの byte 不変検査) にするか。新しい阻害 gate を
  作らない方針との衝突が論点。
