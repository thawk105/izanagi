---
schema: izanagi-spool-v1
ledger: decisions
authored: 2026-08-31
wave: dev-wave-t1985-ratification-terminal
seq: 2
---

## {{D:ratification-bypass-terminal}}. 批准 gate の素通りを塞ぐ作業は実装せずに終端する

**決定:** D1039 が命じた「既存 lock からの resume で批准を再検査する」実装と、D1070 が命じた
「批准検査を artifact 受入と dispatch へ広げる」実装は、**着手せずに終端する**。D1139 が批准
突き合わせを廃止し、両裁定の実効を明示的に奪っているためである。批准機構の再建も行わない。

**理由:**

- D1139 (ユーザー裁定) は、実効を奪う既裁定として D905 / D1039 / D1070 / D1071 を名指しし、
  D1039 と D1070 について「批准 verifier が無くなるため**実装不能**になり、実効を失う」と
  書いている。実装は既裁定の否認になる。
- 判定器 `orchestrator/campaign/enforcement_source_ratification.py` と対応する試験は commit
  `b4ff38f6b` で main から削除されている。T-1629 が作った署名 receipt 版 (`ed25519_verify.py`、
  `enforcement_source_ratification_receipt.py`、`tools/ratification_broker.py`) も `c986c1459` で
  撤去され、その救出候補 7 file は D1308 が全件破棄と裁定した。**main に consumer はゼロであり、
  素通りを塞ぐべき署名 gate が存在しない。**
- `hooks/enforcement-source-closure-ratifications.v1.jsonl` は 1 行の歴史証拠として残るだけで、
  production の消費経路を持たない。台帳の実在を機構の実在と読み替えてはならない。
- D1308 が同じ主題で「破棄は既裁定の適用であって新しい設計判断ではない」と定めており、本決定は
  その先例に従う。新しい設計判断を作るものではなく、既裁定の射程を記録するものである。

**成果物影響:** 実装した場合、campaign 初期化と artifact 受入の受理集合を、再び批准集合との
照合へ依存させる方向へ引き戻す。D1139 が構造的に解消不能と判定した blockage (closure の版が
動くたびに批准行が陳腐化し、一定時刻以降は誰も certified campaign を新規初期化できなくなる)
が再発し、certified な選択結果が 1 件も生成できなくなる。終端はこの引き戻しを起こさず、受理
集合を変えない。規律 2 の中核 (anomaly を検出した variant の即 reject) は本決定に一切触れられない。

**却下した選択肢:**

- **批准機構を再建したうえで穴を塞ぐ** — D1139 が「却下した選択肢」として名指しした
  「批准行の発行を署名 broker で機械化する」の再提出になる。同裁定は、逐語が不要としているのが
  blockage だけでなく**束縛の粒度そのもの**だからこれを採らない、と理由まで書いている。
- **持ち越し本文を無変更のまま残す** — 同じ調査を次の担当が繰り返す。実際、本 wave は上書き裁定の
  着地後も更新されなかった持ち越し本文から起動された。終端を記録しなければ同型の起動が続く。
- **別の生きた署名 gate へ読み替えて実装する** — D1039 / D1070 の対象は enforcement source closure の
  批准検査であり、別機構への読み替えは裁定の射程を書き換えることになる。射程を変える必要が
  生じたなら、それは新しいユーザー裁定の対象である。
