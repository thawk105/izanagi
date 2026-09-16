---
schema: izanagi-spool-v1
ledger: decisions
authored: 2026-09-16
wave: dev-wave-fig5-a2-identity-reissue
seq: 1
---

## {{D:legacy-figure-condition-description-default-corrected}}. 凍結図の caption は prefix 列挙で例外にし、legacy 権威から作る図の条件記述は既定で訂正後にする

**決定:** A-2 図生成器の legacy profile について、caption・x 軸目盛・`tracked_inputs` の
**既定を訂正後の条件記述**とし、`FROZEN_LEGACY_CAPTION_PREFIXES` に列挙した出力 prefix の
ときだけ凍結済みの旧文言・旧目盛・旧 2 行 provenance を返す。列挙は現在
`fig5_a2_certification_reject` の 1 件だけである。

- 列挙は機能の台帳ではなく、「この 1 成果物の caption は訂正前の文言で凍結されている」という
  **凍結の記録**である。新しい gate・検査層は足さない。
- caller は「どの成果物か」だけを選び、caption 文字列を注入できない (D1752 / D1753 の形を踏襲)。
- 訂正側の図は `tracked_inputs` へ `kind: "caption_source"` の 1 行を足し、
  `authority_scope` を `condition description only; not measurement values or protocol status`
  と限定する。権威 bytes (certification / raw_manifest) の 2 行は保持する。

**理由:**

- 着地 closure が `provenance["caption"] == _caption(provenance, prefix)` を要求するため、
  生成器の legacy caption 文言を**一律に**直すと凍結図を再生成しない限り検査が赤になる。
  出力 prefix で分岐すれば、凍結 bytes の保持と条件記述の訂正が両立する。
- **既定を訂正側に置く向きを採ったのは、allow-list だと将来 legacy 権威から別の図を作った人が
  黙って誤った条件記述を得るからである。** 既定を正しい側にすれば、誤りを持つのは明示的に
  凍結した 1 件だけになる。列挙の長さは同じで費用も変わらない。
- 条件記述の訂正は caption だけでは足りない。x 軸の目盛が要求 genome の名
  (`fixed 10 us`) を表示している限り、**絵そのものが誤った条件を述べ続ける。**
  PDF を論文へ貼った時点で、別 file にある erratum は付いてこない。
- 段 3 の 2 レンズが独立に、in-place の上書きは現在の授権では実施できないと判定した
  (絶対規律 7、D1645、D1753、および `figures/README.md` の追補が bytes 保持を明記)。

**却下した選択肢:**

- **凍結図を in-place で作り直す** — 4 つの現行裁定と正面衝突する。訂正は追記でのみ行う。
- **allow-list (新 prefix のときだけ訂正版を返す)** — 既定が誤った側に残る。段 2 プランの初版。
- **caption だけ訂正し目盛は保持する** — 絵が誤った条件を述べ続け、依頼を満たさない。
  段 2 プランはこれを「scope と最小差分」を理由に採ったが、両レンズが real な不履行と判定した。
- **改訂稿で権威 bytes 2 行を置換する** — 実際に使った測定権威の出所記録を落とす。
  機構上は可能だが採らない。
