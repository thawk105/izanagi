---
schema: izanagi-spool-v1
ledger: decisions
authored: 2026-08-26
wave: dev-wave-t1726-freeze-rederive
seq: 1
---

## {{D:receipt-freeze-rederivation-authority}}. 受入 receipt verifier の権威 root は verifier 自身の checkout とする

**決定:** `orchestrator/campaign/s8c_acceptance_receipt.py` が v2/v3 receipt を検証するとき、
ratified legacy freeze は **verifier 自身の checkout** から `s8b_ratified_freeze.load_legacy_freeze()`
の既定 root で読む。検証対象 repository (`repository_root`) に凍結 artifact の複製を要求しない。
検証対象から読むのは、`measurement_head` に紐づく historical off artifact だけとする。

**理由:**
- ratified legacy freeze は「検証者が持つ信頼の起点」であって、検証される側が供給するものではない。
  bytes は `V1_FREEZE_SHA256` 定数で束縛されており、供給元を検証対象に委ねると信頼の向きが逆転する。
- 検証対象 root から読む設計は、凍結 artifact を複製しない正当な receipt 生成経路をすべて
  `legacy-read` で拒否する。段 3 の敵対相談が実在の正例を名指しして実証した。
- 既存の producer 側 preflight (`p3_autonomous_workload_trial`) が同じ形を採っており、整合する。

**却下した選択肢:**
- 検証対象 root から読む — 上記のとおり正当な正例を拒否する。
- 凍結 artifact の複製を receipt 生成側へ義務づける — 受理条件を artifact 配置へ広げ、
  条件の正しさと無関係な理由で受理集合が変わる。

## {{D:receipt-legacy-generation-conditions}}. 旧 v2/v3 receipt は固定 V1 authority の legacy として読み続ける

**決定:** 受入 receipt の schema を v4 へ上げず、旧 v2/v3 artifact を明示的に失効させない。
固定された第 1 世代 freeze を権威として読み続ける。ただし次の 3 条件を伴う。

1. `V1_FREEZE_SHA256` を差し替えない。
2. `s8b_holdout_freeze.HOLDOUTS` / `DERANGEMENT` を改訂しない。
3. 1 または 2 を行う前に、freeze の path・hash・generation を serialized binding へ載せる
   schema 世代交代 (v4) を先に入れる。

**理由:**
- 条件の再導出に要る値 (arm、holdout、measurement head、content digest) は v2/v3 receipt に既にある。
  権威が単一固定である限り、freeze 識別子を receipt へ載せる純増は provenance 記録に留まる。
- v4 は receipt の保存 bytes と exact key 集合を変え、receipt の key 集合を不透明 blob で pin する
  互換 baseline と、並行 wave が所有する台帳系 test を巻き込む。
  条件検査の昇格はこれらを一切変えずに成立する。
- 一方 authority が複数世代化した瞬間、freeze 識別子は provenance ではなく受理判定そのものになる。
  旧 receipt は黙って緑 (別世代を同じ権威と誤認) か黙って赤 (再導出不能) のどちらかに倒れる。
  条件 3 はこの分岐を先回りして塞ぐためにある。

**却下した選択肢:**
- 本 wave で v4 へ上げる — 条件検査の昇格に不要であり、並行 wave の編集面と保存 bytes を巻き込む。
- 旧 artifact を明示的に失効させる — 監査 artifact を偶発的な digest 不一致で捨てることになる。
  失効させるなら versioned policy と明示理由で行うべきで、本件はその条件を満たさない。

## {{D:receipt-gate-no-tautological-assert}}. 既存 gate から恒真に従う照合は追加しない

**決定:** 条件再導出 gate では expected content digest だけを照合し、
expected arm binding digest の照合は追加しない。省いた理由をコード comment に残す。

**理由:**
- 既存 gate が `binding_digest == hash(holdout, arm, receipt_content_digest)` を要求済みのため、
  `receipt_content_digest == expected_content_digest` を足せば
  `binding_digest == hash(holdout, arm, expected_content_digest)` は決定論的に従う。
  追加照合は受理集合を 1 bit も狭めない。
- 謳うだけで発火しない assert は防壁の見かけを増やし、変異検査で偽の KILLED を生む。

**却下した選択肢:**
- 多重防御として両方を照合する — 独立でない冗長は多重防御ではなく、検出力の水増しである。
