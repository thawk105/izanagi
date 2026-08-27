# 2026-08-27 [T-1769] — B-4 事前登録 §5.1 (ii) の非標本 probe

B-4 事前登録 (`docs/phase3-b4-reflux-ablation-preregistration.md`) §5.1 (ii) が要求する
「next synthesis と primary / secondary outcome を生成も閲覧もしない配線調査」を行う
sanctioned CLI を新設した wave の素材。実装は
`orchestrator/campaign/p3_b4_wiring_probe.py`、検査は
`orchestrator/tests/test_p3_b4_wiring_probe.py`。

**本 wave の実走は道具の dogfood であり、§5.1 (ii) の採用証拠ではない。**
§5.1 (i) の先行 freeze (候補集合・exact command・証拠 path と hash・0 件/複数件の決定規則・
記入者・レビュー者) は人間の指名を含み未完である。§5 の欄は 1 つも埋めていない。

## 中身

|path|内容|
|---|---|
|`t1769-dogfood/`|3 driver の dogfood 証拠 JSON と detached sha256 sidecar|
|`mutation-spec.json`|本走の変異事前登録 (14 件)|
|`mutation-ledger.json`|本走の結果 (baseline PASSED、KILLED 9 / SURVIVED 5 / MISMATCH 0、14/14 一致)|
|`mutation-spec-bothlayers.json`|生存 5 件の両層同時変異の登録 (5 件)|
|`mutation-ledger-bothlayers.json`|同結果 (baseline PASSED、SURVIVED 5、5/5 一致)|
|`verbatim/`|段 1 brief、段 2 プラン、段 3 敵対相談 2 本、段 4 裁定、段 5 実装報告、段 6 レビュー 2 本・裁定・fix 2 本、親の実測|

## 変異 matrix の読み方 (正直に書く)

**発火した 9 件が覆う範囲。**

|ID|変異位置|落ちた node 数|
|---|---|---|
|MW01|`main()` から audit hook 装着を外す|4|
|MW02|`main()` から profile seal を外す|5|
|MW03|遮断集合の種 1 (certified writer authorization) を外す|9|
|MW04|遮断集合の種 2 (loop state 永続化) を外す|5|
|MW05|遮断集合の種 3 (whiteboard 射影) を外す|5|
|MW06|multi-path audit の destination 解決を落とす|3|
|MW07|目録構築の unresolved 検査を外す|1|
|MW08|publish 窓の観測を literal へ戻す|1|
|MW10|publish 前の failed check 検査を外す|1|

期待 node は観測走 (`--force-dispatch` の dispatch 走) で実観測した完全集合を使い、
本走で 14/14 完全一致した。

**生存した 5 件は到達不能な多重防御である。**

MW09 / MW11 / MW12 / MW13 / MW14 は、いずれも publish 直前または `main()` 末尾で
違反 ledger を照合する assert である。実装上、ledger へ追記する箇所は**追記の直後に必ず
例外を送出する** (`p3_b4_wiring_probe.py` の `_ProcessGuard._profile` / `_audit`)。
したがって「違反が記録されたまま publish へ到達する」状態は構造的に起こらず、
これらの assert は現在の実装では一度も発火しない。

遮蔽 (他層が同じ入力を拒否している) ではないことは、**両層同時変異で裏取りした** —
遮蔽候補 (`main()` の ledger 照合ブロック、証拠 schema の ledger 照合ブロック) を
同時に外しても 5 件とも生存した (`mutation-ledger-bothlayers.json`)。

**これらを「発火する保証」として数えない。** 将来の改修に備えた多重防御として残し、
到達不能であることをここに記録する。本 wave の保証の中核は発火した 9 件が担う。

## この wave が実測して訂正した事実

- **事前登録 §10 の「`--no-build` 経路は §3.1 の切替点を通らない」は sort driver について偽だった。**
  base と trigger では切替点が `do_build` の内側にあるが、sort では無条件である。
  probe の証拠はこれを driver 別の guard 式として機械記録する
  (`t1769-dogfood/base.json` と `trigger.json` は guard 式を持ち、`sort.json` は空)。
  sort の `--no-build` が probe にならない理由は別にある — iteration を実走して
  checkpoint と whiteboard 結果を書き、synthesis 記録を生成するためである。

## probe が閉じないこと

- **承認経路は deny-only の legacy 台帳を読む。** 迂回すると `make_critic_digest` が要求する
  exact な型を作れず、正しさゲートを緩めることになる (規律 2)。読んだ台帳の path と sha256 は
  証拠の `admission_reads` へ開示し、それ以外の実 campaign artifact を読まないことを ledger で示す。
- **遮断集合は生成器の完全目録ではない。** 3 種の権威点のいずれにも到達しない生成器は
  この層では覆わない。閲覧側は隔離層 (保護領域の read/write 拒否) が受け持つ。
- **切替点通過の証拠は composite である。** 静的到達性と probe からの実 `make_critic_digest`
  直接呼出しを併せたものであり、driver が runtime に切替点を通ったことは主張しない。
- **trigger の site 射影 identity は計測契約を発行できる site でしか測れない。**
  login site では production が拒否するため `status=not_measured` と記録する。
- **任意の native code や同権限 process による interpreter 改変は主張しない。**
