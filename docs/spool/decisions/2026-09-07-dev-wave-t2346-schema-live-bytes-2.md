---
schema: izanagi-spool-v1
ledger: decisions
authored: 2026-09-07
wave: dev-wave-t2346-schema-live-bytes
seq: 2
---

## {{D:schema-bytes-shared-reader}}. 受理判定の schema 読み取りは bytes を返す共有経路に集約する

**決定:** qualification の受理判定が使う schema は、bytes を返す 1 本の共有 helper から取る。
判定側の validator も、記録 blob との等値検査も、同じ helper が返した同じ bytes を使う。
helper は呼ばれるたびに disk を読み、schema 名ごとに保持した bytes と比べ、
一致しなければ fail-closed で拒否する。

**理由:**
- D1512 が求めたのは「受理判定に**実際に使われた** schema の live bytes」と記録 blob の等値である。
  path だけを共有して読み手と検査が別々に読むと、検証と等値検査の間で bytes を差し替える窓が残り、
  D1512 の文言を満たさない。
- 保持した bytes を無検査で使い回すと、process の途中で disk 上の schema が変わっても
  古い bytes を使い続ける。毎回読んで比べれば、この穴は塞がり、I/O 回数も集約前へ戻るだけである。
- 読み手が複数ある以上、path の解決を各所に書くと、読み手だけを別 file へ向けても
  検査が通る形になりうる。共有経路が 1 本であることが、この検査が機構を通る条件である。

**却下した選択肢:**
- 同一 FD を validation stack へ通す — 全 validator の署名変更を伴い、D1512 が却下した
  bytes 級 provenance の側へ寄る。
- path だけを共有し、読み手と検査が別々に読む — 上記のとおり D1512 の文言を満たさない。
- 共有 helper に schema 名の allowlist を新設する — D1512 が求めていない受理集合の縮小になる。
  入力検査は集約前の条件をそのまま移すに留める。
- 保持した bytes と disk の差を黙って更新する — 差は drift の証拠であり、握り潰さない。
