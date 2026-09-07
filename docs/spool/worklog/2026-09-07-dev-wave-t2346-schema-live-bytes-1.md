---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-09-07
wave: dev-wave-t2346-schema-live-bytes
seq: 1
title: [T-2346] 受理判定が読む qualification schema の live bytes を記録 blob へ結ぶ (コード + テスト、branch worktree-dev-wave-t2346-schema-live-bytes、変異 2/2 KILLED + 帰属 probe 35 件)
---

## 本文

- 依頼は「D1512 が裁定済みの等値検査を最小の形で足す」。裁定待ちではなく実装待ちだったことを
  一次資料 (D1512 と archive worklog の次の一手) で確認してから着手した。前提は覆らなかった。
- **段 3 のレンズ A が、親 brief と段 2 plan の「path を共有すれば足りる」を崩した。** path だけ
  共有すると読み手と検査が別々に read するので、受理判定で使った bytes と検査した bytes が
  同じである保証がない。D1512 の文言は「実際に使われた」なので、path 共有では文言を満たさない。
  親は helper が bytes を返して memo する形を裁定した。同一 FD を validation stack へ通す案は、
  全 validator の署名変更を伴い D1512 が却下した bytes 級 provenance へ寄るため採らなかった。
- **段 6 のレンズ C が、その memo が作った穴を出した。** process 途中で disk の schema が
  変わっても古い bytes を使い続ける。memo は親が段 4 で足したものなので、性質 (読み手と検査が
  同じ bytes) を保ったまま塞いだ — 毎回 disk を読んで memo と比べ、不一致は fail-closed。
  差分前と同じ I/O 回数へ戻る。
- 段 3 のレンズ B が出した「6 basename の allowlist を足すな」は採用した。allowlist は D1512 が
  求めていない受理集合の縮小になる。helper の入力検査は既存 3 条件の逐語移設だけにした。
- 変異の初回走行は M12 / M13 とも自分の node に加えて登録簿の完全性 meta-test を落とした。
  変異が anchor 逐語を書き換える以上、登録簿を検査する test はどの変異でも落ちる冗長 gate である。
  単一理由にするため当該 1 件を deselect して取り直した (初回結果は erratum として insight に残す)。
- 既存 35 変異の probe を回し、M12 / M13 の node がそれらの失敗集合に現れないことを実測した。
- 段 3 で判明した既存の性質: `T126_MUTATION_REGISTRY` は parametrize された test の node を
  bare 名で持つため、登録簿から機械生成した spec は collection 照合で止まる。今回の変更とは
  無関係な既存事実であり、この wave では扱わない。

## 次の一手差分

### 完了

- [T-2346] D1512 の等値検査を実装した。受理判定が読む 6 schema の live bytes と記録 blob を
  身元検証で照合し、不一致を拒否する。設計判断は {{D:schema-bytes-shared-reader}}。
  remaining: none
  base: d4bb04aa792f018ab192c8666bb88f8fb4f2346cad185a2630df2364d09ec85b
