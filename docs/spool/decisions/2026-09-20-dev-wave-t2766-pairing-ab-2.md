---
schema: izanagi-spool-v1
ledger: decisions
authored: 2026-09-20
wave: dev-wave-t2766-pairing-ab
seq: 2
---

## {{D:t2766-pairing-ab-measurement}}. 受入順序変更の効果測定は同一 SHA からの直接投入で行い、opt-in 実装は impl branch に置いて main に入れず、採否は実受入の隣接対の結果で諮る

**決定:**

1. **同一 tip 反復の測定走は待ち手 (`tools/dev_wave_wait.py acceptance`) を使わない。** 待ち手は claim 直後に local main を取り込むため
   隣接 2 走でも tip が変わる。測定は wave worktree を測定 SHA に固定し `IZANAGI_ACCEPTANCE_SHARDS=3 python3 tools/run_tests.py`
   (空 argv の受入形、Pegasus LOGIN の明示 shard mode) を直接投入する。dispatch・shard child・`tools.acceptance_shards`・session dir は
   受入と同一経路で、lease / merge / receipt / launcher の main blob 実行だけが無い。測定対象は shard の JUnit wall と worker 占有であり、
   待ち手経由の受入総経過時間ではない。投入直前と終了後に HEAD と clean を照合し、集計器が測定 SHA の一致・投入時刻の逐次性・複製成果物の
   実在を fail-closed で検算する。land 用の最終受入だけ待ち手を使う。
2. **pairing の実装は既定 off の opt-in (env の exact token) とし、発火の witness を junit の property に残す。** production の `report.json` は順序を
   証言しない (records / selected の digest は sort 済み) ため、opt-in 時だけ全 item の `user_properties` に scope / rank / partner / 実行 worker を
   付け、集計器が `selected` + 台帳から tie-break 非依存の多重集合で独立に検算する。A (opt-in off) は現行と同一順序・同一 property を固定 literal
   の負例と変異で固定する。
3. **効果の有無にかかわらず本 wave は実装を main に入れない。** 実装 commit は branch `impl-t2766-pairing-optin` に保存し、landing は insight と
   fragment だけとする。採否 (既定 on への変更) は測定結果を添えてユーザー裁定へ返す (起票文の「採用は効果実証を条件」と D104 決定 3 の「効果を示せない機構は
   land しない」に、示せた場合も採用は別裁定という読みを重ねた)。
4. **判定規則は結果を見る前に固定する。** 有効対 = 隣接 2 走がともに緑・同一 SHA・B は witness 一致、無効対は同順序で追加 (slot を消費しない)、
   有効 3 対で固定終了、測定走上限 12。指標は最遅 shard の JUnit wall の対差と対率、3 種の中央値 (対差・対率・条件別中央値差) を別量として併記。
   判定は (i) 全対同方向かつ対率中央値 ≥ 10 % → 採否を諮る、(ii) 同方向だが < 10 % → 見送りとして諮る、(iii) それ以外 → 効果未確立。
   10 % は本 wave の保守基準で D357 の 1 走比較の規則とは別に置く。

**理由:**

- 段 3 相談が「非 docs 木の一致」を反証した (real-repo test が `output/` を走査し docs も読む) ため、同一 SHA 以外に同一条件を保証する手段が無く、
  待ち手の post-claim merge を避けるには直接投入しかない。
- 効果は実受入の隣接対 3 組で 3 対とも B が 101.7 / 112.9 / 144.3 秒短く (対率中央値 24.2 %)、B の発火は 12 shard の witness で一致した。
  一方で機序は未同定 (A の律速 worker の中身は未観測) で、隣接対は同 allocation でない。採用は受理集合に触れない順序変更だが、既定 on への変更と
  再確認は別 wave に置くのが「実装を採用済みとして本番に入れない」依頼に沿う。
- 独立 clone (D1009) と probe → final の 2 段で変異 6 件を期待 node 完全一致で kill し、A 不変・受理集合不変を実測で固定した。

**却下した選択肢:**

- 待ち手経由で隣接対を取り「非 docs 木の一致」で有効対とする — 相談 A1 で反証。
- 2 worktree からの同時投入 (同時刻の対照) — D357 が測定中の自 job の並走を禁じる。
- 既定 off の opt-in をそのまま main に入れて再現性を main に置く — 効果未実証の保守面を増やし、依頼の読みに反する。impl branch と逐語で足りる。
- tracked flag file を B 用 commit で切り替える — tip が変わり同一 tip を破る。
- 実装を Claude 親が直接書く — D95 (実装面は Codex author)。
