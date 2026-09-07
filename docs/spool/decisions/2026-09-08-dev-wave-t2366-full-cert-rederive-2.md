---
schema: izanagi-spool-v1
ledger: decisions
authored: 2026-09-08
wave: dev-wave-t2366-full-cert-rederive
seq: 2
---

## {{D:a2-full-materializer-exact-rederivation}}. A-2 full certification の materializer は partial と同じく acquisition から report 全体を再導出して完全一致を要求する

**決定:** `paper-story-a2-certification-result/v4` (full) の materialize は、既存の形・identity・schema chain・
request ID・固定 field・cells 検査を**渡された evidence に対して据え置いた後**、`acquisition_path` から
`validate_acquisition_bundle` で evidence を読み直し、読み直した receipt chain が full (v3 acquisition /
v3 completion) であることを検査し、collector と同じ関数 `_canonical_full_report` で report を再導出して
`report == expected` を要求する。不一致は `certification result differs from evidence re-derivation`。
戻り値は読み直した canonical evidence とし、materialize が書く receipt bytes はそこから取る (渡された
bytes は authority にせず、拒否もしない)。`_collect_command` の full 側 else 枝は同関数へ逐語で切り出し、
collector と validator が同じ経路で report を導く。legacy v3 full / v1 partial / v2 partial の枝、
materialize 本体、schema 識別子、report と成果物の形は変えない。

**理由:**
- D1259 が partial 側に入れた「materialize 時に acquisition / completion / manifest から authority・cells・
  effects・status を再導出して report 全体と比較する」防壁が full 側に無く、正の evidence に対する偽 status・
  偽 effects・偽 driver_rcs と整合する indeterminate report を tracked 成果物として公開できた (D1692 が別項へ
  送った既存の非対称)。production CLI は同じ evidence から report を作るので到達しないが、`materialize` を
  直接呼ぶ API 境界 (tests・将来の呼び手) と二回読みの間の disk 整合性がこの検査の射程である。
- 既存 identity 検査を読み直した evidence へ一括で切り替えると、`acquisition_path` だけ正しく他 field を
  改竄した evidence dict が読み直しで置換されて通り、入力受理集合が広がる (段 3 の 2 レンズが独立に指摘)。
  据え置き + 後置の再導出なら縮小のみになる。
- 読み直し後の receipt chain 検査が無いと、partial の受領証を full の表層 field で包んだ evidence が
  indeterminate report と一致して通る (段 6 レビュー B)。partial 側の同型検査 (v4 chain 要求) を写した。
- 渡された receipt bytes と disk の不一致を「拒否」する要件は新設しない。canonical bytes への置換で
  成果物の bytes 集合は縮み、拒否要件は partial にも無い。

**却下した選択肢:**
- `report == expected` を canonical JSON bytes 比較にする — `dict ==` は `True == 1` を同一視するので
  JSON 型だけ違う偽造が通る (段 6 レビュー A、real)。しかし partial 側の既存比較も同じ `==` で、本 wave は
  「partial をそのまま射影し新しい検査層を作らない」指示の範囲内に留めた。両側を同時に変える案として
  別項へ送る。
- legacy v3 full にも再導出を入れる — 既存完走 artifact の受理集合を変える。D1259 が legacy v1 partial を
  identity-only に据え置いたのと同じ理由で採らない。
- partial の raw manifest schema chain の全拒否まで写す — full の「manifest 無効 = indeterminate」の
  既存判定と衝突する。
