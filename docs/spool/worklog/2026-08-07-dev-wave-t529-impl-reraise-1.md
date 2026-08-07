---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-08-07
wave: dev-wave-t529-impl-reraise
seq: 1
title: [T-529] 実装を再起票し、裁定 E の共有 leaf 抽出と [T-615] の歴史世代解決を入れた — 活性化権限そのものは入れていない (コード + docs、受入 7168 passed / 20 skipped、変異 13/13 KILLED + 生存 2 件の erratum、branch worktree-dev-wave-t529-impl-reraise)
---

## 本文

- **保留の根拠だった「発火正例を書けない」は反証された。** `DW-G04` は実在 artifact path か
  計測 ID を求めるが、Pegasus の登録済み較正
  `output/env/pegasus/calibration/registered/calibration-94a4b79fa31bba3c.json`
  (accepted / schema `calibration/v2` / env_tag 一致) と計測 ID `892707.nqsv`
  (`calibrate_rc = 0`) が実在する。親が実測し、この較正を指す prospective g2 は
  `is_valid_successor` を True で通り (`contract_sha256 = 1346c20b5519be4b…`)、
  `load_verified_calibration` も g1(753f)・g2(94a4) の双方を ACCEPT した。
  段 2 が先に指摘し、段 3 レンズ A が独立に裏づけた。{{D:g04-firing-material-exists}}
- **それでも活性化権限そのものは実装していない。** 保留の残る根拠は入口面であり、
  裁定 C(a) がそれを [T-609] へ外出ししただけで、コード上は閉じていないためである。
  floor は Python 起動前に attempt の stdout / stderr / launch marker を書き、
  T-126 は `.git` を持たない source stage から driver を起動する。両方とも現状のまま。
- **段 3 の 2 レンズは割れた。** レンズ A は NO-GO 同意 (根拠を [T-609] だけへ狭めよ)、
  レンズ B は「裁定 E の前半 (述語の共有 leaf 抽出) は活性化の発火から独立に実装できる」と反論。
  親はレンズ B を採り、**親自身の provisional 裁定 (P1)(P4) を誤りと裁定した**。
  親の一般化が段 3 で覆るのはこれで 4 wave 連続である。
- **裁定 A(b) と D は実装しなかった。** A(b) は registry が 1 env 1 世代のため
  受理集合を 1 要素も変えられず、無条件 pass と区別できない。D は文言に穴があり
  (下記)、穴を残したまま predicate を land すると弱い gate が台帳に残る。
- **[T-615] は wave 稼働中に同梱指定された。** 受入全走の直前に local main を再確認して
  検出した (取り込み前に見つけたので巻き戻しは発生していない)。段 4 の追補として裁定し、
  設計子 1 本・敵対レビュー 2 本・fix 1 本を追加で回した。{{D:floor-protocol-two-lane}}
- **[T-615] を素直に実装すると規律 2 を破るところだった。** 対象入口は producer・
  凍結 artifact 検証・live admission の 3 用途を兼ねており、全体を歴史解決へ倒すと
  「現在 active でない較正で新しい実測を走らせる」ことを許す。設計子と親の裏取りが
  D202 (履歴解決は read-only 入口へ限定) と D213 (resume は current 固定) を根拠に示した。
  2 lane へ分離し、historical 検証を通した document を実行権限 token にしない構成にした。
- **敵対レビューが「今日の受理集合は不変」という親の主張に反例を出した。** 記録
  `contract_sha256` に `str` の派生型を入れると current lane は受理し historical lane は
  拒否する。レンズ F が非 pytest probe で実測した。共有 core の exact 型検査 1 か所で解消した。
  実 artifact は JSON parse 由来で必ず exact `str` のため、凍結 bytes 由来の受理集合は不変。
- **T419 の submission binding に本 wave 由来の穴を作りかけた。** 同 probe は
  「提出時と同じコードで走ったか」を `env_contract.py` と `env_attestation.py` の 2 path で
  判定するが、検証の実体を新 leaf へ移したため、新 leaf だけを変えても `matched=True` に
  なりえた。レンズ D が検出し、`related` への追加と観測 SHA と leaf-only dirty 負例で塞いだ。
- **変異は 13/13 KILLED (生存 0)、baseline 緑。** ただし erratum が 2 件ある。
  (1) run 1 は 9 件中 6 件が MISMATCH だった — **登録漏れは 0 で、波及が登録より広い方向**の
  ズレ (leaf を変異させると入口経由の試験も落ちる)。実測どおりの期待 node で run 2 を回し 9/9 KILLED。
  初回台帳は `mutation-ledger-run1-erratum.json` に残す。
  (2) M10 の期待 node のうち `[invalid-return]` だけが発火しなかった。再照準した M13
  (exact `GenerationEntry` 検査の無効化) は **SURVIVED**、両層同時の M14 も **SURVIVED**。
  原因は 3 層目 — 共有 leaf `s8b_floor_contract.validate_protocol` の広い
  `except Exception` が AttributeError を `FloorContractError` へ変換する。
  よって `[invalid-return]` は**過剰決定**であり、`DW-M03` に従い単独変異の証拠から外す。
  同テストの `unknown` / `cross-env` は単一理由で M10 が kill している。
- **重複起票を 1 件回避した。** 裁定 C(a) の「certified writer 閉包の新規タスク」は
  [T-609] として既に存在し、差分 0 だった。レンズ B とレンズ A が独立に指摘した。
- **[T-607] の従属裁定の前提が誤っていた。** 塞いでいるのは env 契約の世代活性化ではなく、
  freeze v2 の candidate generation (AI が発行可) と、非 merge かつ逐語 `AI-Agent: none` を
  要求する approval / active pointer (運用上の人間手番) の chain である。
  T-529 の活性化を実装しても `no-active` は解消しない。項を訂正する。
- 変異 harness の起動で 3 度 fail-closed した。(a) runner に全走を渡すと collection が
  dispatch へ回り、端末側の中継が切り詰めて期待 node が「collection に実在しない」と判定される。
  (b) 対象を 4 module へ絞ると `--collect-only` が 1 秒未満で終わり、`run_tests.py` の
  bounded scope が cgroup を attest できず rc=16 になる (`_SCOPE_ATTEST_SECONDS = 1.0`)。
  (c) parametrize 済み test を素の関数名で登録した。いずれも harness の事前検査が
  正しく止めたものである。解は先例 ((281) の U-8 wave) と同じ
  `--runner-mode dispatch` + `--force-dispatch` + `-p no:cacheprovider` だった。{{F:mutation-collection-preflight}}
- **段 8 の改善候補 3 件のうち 2 件は failures へ、1 件は入らなかった。**
  変異 runner の recipe と `.done` 残骸は F へ送り、恒久対応は memory
  `mutation-runner-dispatch-recipe` と launcher の `rm -f` が担う。
  入らなかったのは「`DW-S01` の前提実測に、保留裁定 (D) の**解除条件を条文単位で棚卸しし、
  今回の裁定が各条件へ効くかを対応づける**義務を足す」で、本 wave の scope 判断そのものが
  これだった。dev-wave 4 文書の aggregate は 25,187 / 25,200 bytes で余地 13 bytes
  (2026-08-07 再実測、(285) と同値)。予算引き上げは提案せず [T-597] へ従属させ、
  新しい T / F を作らない。
- 一次資料 = `output/insights/2026-08-07_t529-impl-reraise/`
  (段 1 brief、段 4 裁定、段 4 追補、段 2/3/6 の逐語、変異台帳 5 本)

## 次の一手差分

### 完了

- [T-615] 凍結済み floor protocol の検証を historical 再検証と current admission の 2 lane へ
  分け、記録 hash からの歴史世代解決を配線した。凍結 bytes と `FROZEN_MANIFEST` 期待値は不変。
  registry が 1 env 1 世代のため今日の受理集合は変わらず、効くのは後継世代の活性化後である。
  remaining: none
  base: 89ec986404784b676365f4e03119b9d0a29d031c47c0d924638da855075d0659

### 更新

- [T-529] **P1・裁定 A〜E のうち E 前半のみ実装済み (2026-08-07)。残りは [T-609] 待ち**:
  契約世代の活性化権限。**実装したのは E の前半だけ** — 較正検証述語を
  `orchestrator/campaign/calibration_verify.py` へ抽出し、`env_attestation` を型境界 wrapper に
  した。これで将来 `env_contract` の初期化中から較正検証を呼んでも循環 import にならない。
  **A(b) / D / fuse 除去 / g2 登録 / activation record / receipt はいずれも未実装。**
  A(b) は registry が 1 env 1 世代のため今日は受理集合を変えられず、
  無条件 pass と区別できない。D は文言に穴がある (下記 甲)。
  **保留の残る根拠は入口面 ([T-609]) だけに狭まった** — `DW-G04` の発火素材は
  94a4 + job `892707.nqsv` として実在すると実測で確定した。
  A(b) を将来実装するときは `s8b_oracle_report.py:1640` の raw `resolve_by_contract_sha256`
  直接使用も同時に配線しないと observation 側に穴が残る (レンズ A の指摘)。
  正本 = `output/insights/2026-08-07_t529-impl-reraise/`
  base: ab076a9a52957a3790920725e2eeeb1f79b571c0eb043a8f757ba02153325ca1
- [T-607] **P1・従属先を訂正 (2026-08-07 実測)。ユーザー裁定待ち**:
  `reverify_published_freeze` の production 到達性。**[T-529] の活性化では解消しない** —
  塞いでいるのは freeze v2 側の別機構である。`load_ratified_freeze` が `no-active` で落ちるのは
  `output/s8b-freeze/` に v2 世代・approvals・active pointer が 1 件も無いためで、
  approval と active pointer は非 merge かつ逐語 `AI-Agent: none` の commit を要求する
  (`s8b_ratified_freeze.py:537-549`)。candidate generation は AI trailer 付き commit で
  発行できる (同 `:552`) が、approval / pointer は運用上の人間手番である。
  従属先を「[T-529] の活性化」から「freeze v2 の candidate 発行 + 人間 approval / pointer」へ
  改める要否をユーザーへ諮る。
  base: f0d3d04dc4481b4d2b5a498e0d51b285b0c0c1f15bcd9509cea388fd502d7309

### 新規

- {{T:floor-protocol-invalid-return-single-reason}} **P3・新規**:
  `test_public_validate_protocol_historical_failures_never_fallback_to_current[invalid-return]`
  を単一理由へ強める。現状は共有 leaf `s8b_floor_contract.validate_protocol` の広い
  `except Exception` が AttributeError を `FloorContractError` へ変換するため、
  型検査 2 層を同時に消しても赤にならない (M13 / M14 とも SURVIVED)。
  同 leaf は本 wave の編集範囲外だったため触っていない。
- {{T:d-transition-rule-wording-hole}} **P2・新規・ユーザー裁定待ち**:
  [T-529] 裁定 D の文言「各 env は据置または +1」だけでは、**全 env 据置の no-op
  activation record を拒否できない**。前 wave の段 4 表は no-op を明示的に問題としていたので、
  文言と意図に差がある。択一 = (a) 「全 env の delta ∈ {0,1} かつ少なくとも 1 env の
  delta == 1」へ条件を足す (親の推奨) / (b) 文言どおり据置も受理する。
  親は独断で条件を足さない。決めないと contract が同じまま activation serial だけが動く
  record を受理し、レポートと試行台帳の activation 参照が意味なく分岐する。
