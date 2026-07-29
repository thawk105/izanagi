authority: none
default_effect: no-state-change

# [T-126] 逐次停止 v2 — 実装 preflight の新事実と再裁定 package (2026-07-29)

## 結論

2026-07-27 に採用された逐次停止 設計 v2 は、実装 preflight で formal source eligibility、
qualification hold、promotion authority の未見 blocker が判明したため、本 wave では実装しない。
採用裁定を AI が取り消すのではなく、追加情報を添えて再裁定へ返す。plan・敵対相談・親裁定の逐語は
`output/insights/2026-07-29_t126-sequential-stopping-verbatim/`。

## 独立に確認した事実

1. tracked S8a pair `41b196c96428` → `e932c4502198` は、現 `compare()` で
   faster +3.417%、`p=0.0121858`、`near_floor=True`。入力 seam と near-floor 発火自体は実在する。
2. ただし pair の出所は D47 の 8a 軸提案 sweep で、formal headline 対象外。SPRT reproduced
   だけでは headline eligible にならない。
3. 設計 §8 が要求する既知非再現 pair は floor 内で、通常の near-floor admission を通らない。
   qualification-only series と、それを formal output から構造隔離する規約は未裁定。
4. planner の sidecar promotion gate は現 formal Layer3/headline producer に接続されず、
   machine-readable qualification hold もない。このままでは未配線 gate になる。
5. 現 host は Pegasus login node。Pegasus は `allow_resume=false`、S8a は linux-baremetal 固定で、
   live positive control を planner の 1 round / process 案で取得できない。

## なぜ実装を止めるか

- 現 tracked pair を production positive input にすると D47 の formal source boundary を破る。
- known non-repro pair を通すために admission を広げると、承認済み T-126 を超えて受理集合を変える。
- code landing と activation を prose だけで分けても、qualification 前に formal consumer が
  gate を迂回できる。停止条件は機械的でなければならない。
- source、qualification、authority、Pegasus execution を同じ wave で補うと、D96 の新判断、
  Layer3 authority 改訂、run lifecycle の追加が必要になり、採用済みの保守形 1 本を超える。

## 再裁定が必要な択

### (a) qualification-first amendment を承認する — 親推奨

formal headline へ絶対に昇格しない専用 qualification series を先に定義し、既知非再現 pair の
live positive control を取得する。qualification receipt は machine-readable hold の解除条件とし、
production gate / authoritative consumer は証拠取得後の別 wave で実装する。

### (b) headline-eligible artifact を待つ

8b など formal source boundary を満たす near-floor pair が自然発生するまで T-126 を保留する。
新しい admission や authority を導入しない最小案だが、再開時期は未定となる。

### (c) source eligibility と formal authority まで同時に拡張する

D47 の境界、Layer3/headline producer、Pegasus execution を同時に裁定・実装する。T-126 の当初
scope を大きく超え、D96 の受理集合変更手続も要るため非推奨。

## 本 wave の射程

コード・テスト変更なし。したがって mutation matrix と実装後の受入全走は対象外。
実装前 baseline は関連 3 suite の 64 passed で、実装受入や live qualification の証拠には数えない。
