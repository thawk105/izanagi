---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-08-03
wave: dev-wave-t342-344-provenance
seq: 1
title: [T-342/T-343/T-344] build provenance を source 由来 capability へ移し、cache/replay identity へ束縛し、旧成果物を overlay で既定除外する — 3 件を一体で塞いだ (コード + docs、branch worktree-dev-wave-t342-344-provenance)
---

## 本文

- ユーザー裁定 3 件 ((126) 参照) を**一体で**実装した。分割すると片方が迂回路になるという
  ユーザーの明示に従い、capability 化・4 identity 面への束縛・overlay を同じ変更集合に入れた。
  設計判断は {{D:provenance-capability}}、scope 外へ返した 8 件は同 D の末尾に列挙した。
- **段 1 の前提実測で親の不変条件が 1 つ誤っていた。** `s1_known_axes_freeze.py` の sha pin を
  「3 箇所」と書いたが、段 3 レンズ B の反証で **4 ファイル・7 field** と判明した。うち live file を
  照合するのは freeze verifier だけで、T080 は `migration_basis_commit` の blob を見る。
  編集禁止という結論は変わらない。凍結 doc の source pin も 63 record / 31 distinct path /
  15 mismatch record / 4 distinct mismatch path であり、親が書いた「63 source」は record 数だった。
- **親の provisional 裁定 6 件のうち 3 件がレンズに反証され、段 4 で撤回した。**
  - (P3) legacy cache key で stock を例外にする案 → **不採用**。receipt を持たない旧 stock cache が
    受理され続け、「旧 entry は拒否」というユーザー裁定と両立しない。stock を含む全 class で変える。
  - (P5) campaign ID を保ったまま lock へ policy を焼く案 → **撤回**。親は
    `_verify_screening_policy` を「ID に入らない policy 照合」の先例と読んだが、screening policy は
    `search_config` の一部で ID にも入っており、先例の読み違いだった。さらにレンズ B が
    「旧 3 campaign は `output/campaigns/`、現行 driver は D123 で `output/exploration/campaigns/` へ
    前向き移行済み」と実測し、**ID を保っても通常 resume で踏む実物は 0/3** と判明した。
    可聴な拒否は overlay + consumer 側が担う。
  - (P6) 3 件 denylist だけで既定除外する案 → **fail-open として補強**。未掲載の receiptless artifact が
    通るため、positive receipt 要求を足した。ただし射程は新 schema 以後の成果物に限る。
- **段 6 の敵対レビュー 2 本が Critical 2 件を出し、いずれも T-344 の中核だった。** (a) overlay が
  campaign ID と path でしか照合せず、同じ lock/WAL bytes を別 directory へ置くだけで迂回できた。
  (b) 「新 schema 以後か」を成果物自身の申告 (lock の key 有無) で決めていたため、receipt を欠く
  新成果物ほど歴史成果物として通る循環定義だった。前者は lock SHA・WAL SHA・件数の不変 tuple 照合、
  後者は pre-policy snapshot の exact path と bytes による歴史性証明で閉じた。
- **レビュー 2 がテスト弱体化を 2 件摘発した。** S6/S8a の exact class 検査と T126 の意味的 negative が、
  裁定 §1-E の許可列挙外で「context object の存在検査」「引数欠落の TypeError 検査」へ置き換えられて
  いた。いずれも復元した。
- **`silo_ladder_rung1.py` への変更は親裁定で取り消した。** 実装子が non-admissible 分類を
  committed evidence の schema へ埋め込んだが、これは exact-key schema と driver sha 束縛を壊し、
  修復に `output/` 配下の再 pin が要る。registry 自体が閉包を担うため埋め込みは不要と裁定し、
  registry の docstring を実態へ訂正した。レビュー 2 はこれを所見として再提出したが、
  親裁定済みとして却下した。
- **fix は 5 巡かかった。** 段 5 の実装子は互いの変更を見ないため、統合時に 194 failed / 96 errors が
  出た。1 巡目で 18 件まで下げ、2 巡目で敵対レビューの所見を閉じたが、新設した historicity gate が
  合成 fixture を弾いて 61 件へ増えた。**gate を緩めず fixture を post-policy 形へ直す**方向で裁定し、
  3 巡目で 4 件、4 巡目で 0 件になった。5 巡目は焦点再レビューの partial 2 件へ充てたが、
  実装子は「no-build の成功形が既存の受理集合に無い」として**受理集合を広げずに停止した** — 正しい判断で、
  この設計判断は裁定パッケージへ返した。
- 受入全走 = Pegasus gen_S 計算ノードで **5343 passed / 19 skipped / 0 failed**。
  赤の推移は 290 → 18 → 61 → 4 → 0。`python3 tools/check_docs.py` は違反なし、
  `python3 tools/check_ai_provenance.py` は 809 件で違反なし。
- 変異は 12 件を事前登録した。段 6 レビュー 2 が M3/M7/M9/M10/M11 を「別例外・別検査・広すぎる
  mutation surface により帰属しない」と判定したため、5 件を coherent な変異へ再照準した。

## 次の一手差分

### 完了

- [T-342] provenance を source 由来 capability へ移した。class は caller が選ばず、repo 正本 pin 付き
  clean stock / source 束縛 review receipt / run 束縛 generator receipt / parser 発行 token の順で
  導出する。CLI opt-in は plain bool を廃した。
  remaining: none
  base: 177519f7bca374a4957ed87540ea8baccc7dea8599cfee994cafb494ccc73328

- [T-343] admission を 4 つの identity 面すべてへ束縛した。legacy cache key は stock を含む全 class で
  receipt digest を織り込み exact-schema sidecar を必須化、v2 は preimage と completion manifest の
  両方、campaign は canonical preimage へ policy を入れ、replay は attempt ID 単位で receipt を照合する。
  receipt 欠落の旧 entry は拒否し、明示 migration は作っていない。
  remaining: none
  base: fd6d751ad79ee455cb48a74c5c419c82eb6498c6d834e79936764aa61228c35d

- [T-344] 旧 loop campaign 3 件を deny-only overlay で `legacy-unclassified` と宣言し、
  admission-aware な選択・材料レポート・certified 判定から既定除外した。`verification_status` と
  `admission_status` を別次元にし、歴史的 verifier 判定は否定していない。凍結 bytes は 1 byte も
  変えていない。
  remaining: none
  base: 9805d7175add2acfd7effcd228e3c6ab08e35421caa0e95234717c6b880736b1

### 新規

- {{T:admission-issuer-trust-boundary}} **P2・新規**: capability の発行器が同一 process 内 caller から
  隔離されていない。sealed 型と closed registry は偽 object を拒むが、正規 factory の無権限利用は
  拒めない。別 process / OS capability / 署名鍵への移設を検討する。本 wave では信頼境界を
  「trusted orchestrator code」と docstring に明記するに留めた。
- {{T:materializer-closure-shell}} **P2・新規**: Python materializer は registry で閉じたが、
  `tools/pegasus/*.sh` の 3 本と calibrator の任意 binary path、S8b content-addressed store の
  resume 取得が閉じていない。
- {{T:transitive-provenance-freeze}} **P2・新規**: 旧 campaign 値を内包する freeze を経由した
  laundering が閉じていない。`s1_known_axes_freeze.py` が編集禁止 (sha が 4 ファイル 7 field に pin)
  のため本 wave では閉じられなかった。
- {{T:historical-artifact-reclassification}} **P2・新規**: 全 receiptless 歴史成果物の遡及再分類。
  本 wave は 3 campaign を明示 deny し、positive receipt 要求を新 schema 以後に限定した。
  全 artifact と全 consumer の inventory は別 wave が要る。
- {{T:t126-control-remeasurement}} **P2・新規**: T126 の control が receiptless な旧 P2-2 campaign を
  pin している。新しい admitted source の実測と新 protocol/pin が要る。本 wave では series identity と
  control pin に触れず、live member build にだけ新 capability を要求した。
- {{T:s8b-refreeze-receipt-chain}} **P3・新規**: `eligible_for_refreeze` が receipt chain でなく
  `mode == "official"` から決まる。本 wave では official mode への materializer 注入を core で
  拒否する最小閉包に留めた。
- {{T:immutable-source-snapshot}} **P3・新規**: evidence 発行と build の間に working tree が動いて
  戻る ABA / 混在 snapshot が閉じていない。本 wave は evidence と build の source root を同一に
  束縛して記録するに留めた。
- {{T:no-build-attempt-canonical-form}} **P2・新規**: 成功する no-build 試行を表す正規形が無い。
  `guided.py` は receiptless な `BUILD_START → VERIFY_DONE → BENCH_DONE → COMMIT` を書くが、
  共有 topology が受理するのは receiptful な `BUILD_START → BUILD_DONE → COMMIT` と
  receiptless な pre-build `ABORT` だけである。実測では `p2_5` が `trial_result()` で直接読むため
  admission-aware consumer を経由せず、実害のある断線ではない。受理集合を広げる判断になるため
  裁定へ返す。あわせて孤児 `VERIFY_DONE` / `BENCH_DONE` の variant identity が束縛されない残余も
  同じ裁定で扱う。
