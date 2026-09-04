# 段 4 裁定 + 変異事前登録 — [T-2067] oracle manifest 群への床値選択強制

## 親の実測の撤回 (最重要)

親 brief の「`reverify_published_freeze` が `_launch_validate` を通るので
s8b_oracle_report / s8b_verdict / s8b_oracle_judge は被覆済み」は **誤りである。撤回する。**

親が自分で行を読んで確認した事実:
`s8b_ratified_freeze.py:3303` の選択 identity 検査は `if result_type is LaunchValidatedFreeze:`
で囲まれている。`reverify_published_freeze` (3657) は `result_type=ReverifiedFreeze` を渡すので、
historical reverify 経路では選択 identity は**実行されない**。
`test_s8b_ratified_verify.py:975` はこの挙動を既存 test として明示的に固定している。

したがって上記 3 consumer は選択未検査である。段 3 の 2 レンズが独立に同じ反証を出し、
親が一次資料で追認した。

## 各所見の裁定

| # | 出所 | 所見 | 裁定 |
|---|---|---|---|
| A1 / B1 | 両レンズ | reverify 被覆は偽。report / verdict / judge が未被覆 | **real・採用・ただし scope 外** → 裁定パッケージ (下記) |
| A2 | レンズ A | genuine g1 正例が `no-approved-spec` で終わり manifest 生成に到達しない | **real・採用**。ただし解法は plan と異なる (下記 (2)) |
| B3 | レンズ B | 既存 4 test の g2 化は g1 成功被覆を消し、実 loader では成立しない fixture を作る | **real・採用**。g2 化を**却下**する (下記 (2)) |
| B2 | レンズ B | `build_manifest` / `write_manifest` が公開で loader/gate を迂回できる | **real・scope 外** → 裁定パッケージ。repo 内 caller は test helper だけ |
| A4 | レンズ A | root 省略変異と `ROOT` 置換変異は KILL 経路が別 | **real・採用**。変異を 2 件に分割して登録 |
| A3 | レンズ A | genuine g1 正例の選択述語部分は構成上恒真 | **real・nit**。記述の是正のみ。コード変更なし |
| A5 | レンズ A | `floor-selection-eligibility-underivable` の潰し変異を殺す test が無い | **real・nit・不採用**。レンズ A 自身が「受理集合と成果物 bytes は変わらない」と評価しており `DW-G05` の成果物影響を示せない |
| B5 | レンズ B | driver:496 は private core、public v2 経路は launch_validate を通る | **real・nit**。親の独立実測 (644→664、1335→1351) と一致。実装しない |
| B6 | レンズ B | W-d 所有は将来計画であって現行 lock ではない | **real・nit**。着手を止めない |
| B4 | レンズ B | 提案 gate 自体は D1370 / D1325 / D1313 の境界内 | **real・nit**。境界維持を確認 |

## (1) A1 / B1 を本 wave で実装しない理由

`DW-S04` に従い、scope 外の real 所見は実装せず裁定パッケージでユーザーへ返す。

- 依頼が名指ししたのは「oracle manifest 群」であり、report / verdict / judge は別 module である。
- `s8b_oracle_report.py` と `s8b_oracle_judge.py` は `_GENERATOR_SOURCES`
  (s8b_oracle_manifest.py:65) に含まれる。両 file を編集すると manifest の
  `generator_versions` の byte hash が変わり、**凍結成果物の bytes が変わる**。
  `DW-O09` / `DW-O10` の pin 閉包と golden 追随が必要になり、依頼の
  「本題の実装だけ」を明確に超える。
- 先行 wave (worklog 1122/1123) の「3 群」という母集合の数え方自体が、
  本 wave が反証したのと同じ前提の上で作られた可能性がある。母集合の再確定は
  ユーザー裁定に属する。

本 wave の実装対象は `build_approved_manifest` の 1 箇所に据え置く。

## (2) 既存 test の追随方針 — plan の g2 化を却下する

plan は既存 4 test (1328 / 1369 / 1395 / 1410) の合成 freeze を
`generation_number=2` にすると提案したが、**採らない。** 理由は B3 のとおり:

- 合成 document は v1 文書に floor と budget を足しただけで、実 loader が要求する
  v2 exact schema・本文世代番号・世代連鎖・approval pairing を通らない。
  dataclass の数字だけを 2 にすると、実 loader では絶対に成立しない受理集合を test 上に作る。
- 4 本すべてが g1 を通らなくなり、g1 が gate 通過後に manifest を最後まで構築して
  `holdout_freeze.v2.g1.json` を参照し `verify_manifest` されるという成功被覆が**ゼロになる**。
- `build_manifest_from_ratified` (849) は `generation_number` から
  `holdout_freeze.v2.g{n}.json` を組み立てて manifest へ焼き込むため、g2 化は
  成果物の参照文字列そのものを変える。

**採る方針:** 既存 4 test は合成 g1 のまま残し、選択 assert だけを
「呼出しを記録して何もしない stub」に差し替える。stub は
`(ratified, root)` を記録し、各 test が **呼出し回数と引数を assert する**。
これらの test の主題 (pin の一点性・単一 snapshot・cell product) は変わらない。
これで A2 が指摘した「g1 が manifest を最後まで作れる成功被覆」は既存 4 test が保持し続ける。

機構そのものの証明は、実 loader・実 callee を通す genuine g1 の正例と負例で担う。
正例は gate を通過して `no-approved-spec` へ到達することで**過剰拒否がない**ことを示す
(`DW-M01` が受理集合を縮小する wave に要求する正例)。
これは gate の直後・spec 読込の前という順序が保証するので、budget が null でも成立する。

## (3) 実装内容 (plan から採る部分)

`s8b_oracle_manifest.py` の `build_approved_manifest` で、
`load_ratified_freeze(root)` の直後・同じ `try` 内に
`s8b_ratified_freeze.assert_g1_floor_selection_identity(ratified, root)` を置く。
既存の `except RatifiedFreezeError` がそのまま受け、`no-active` だけを
`no-active-ratified-freeze` へ写す既存写像を維持したまま、
選択系 3 理由は reason を素通しで `ManifestCliError` にする。新しい理由は作らない。
`launch_validate` は呼ばない。helper も互換層も作らない。

## (4) 変異事前登録 (実装前・DW-M01)

anchor は段 5 の統合 commit。各変異は単一理由性を実装後に親が確認する。

| ID | 変異 | 期待 KILL |
|---|---|---|
| M1 | gate 呼出しを削除 (`pass` へ置換) | 既存 4 test の呼出し回数 assert、および genuine g1 負例 |
| M2 | 第 1 引数を `ratified` から `ratified.document` へ | genuine g1 正例 (`floor-artifact-invalid` が先に出て `no-approved-spec` に到達しない) |
| M3 | 第 2 引数を `root` から module `ROOT` へ | genuine g1 正例 (実 callee が tmp でなく実 repository を探索して落ちる) |
| M4 | 第 2 引数 `root` を省略 (既定値へ) | 既存 4 test。**訂正 (段 6 レビュー A 所見 3)**: assert には到達せず、記録 stub の `lambda candidate, candidate_root` が第 2 引数必須のため呼出し地点で `TypeError` になり 4 本が ERROR になる |
| M5 | gate を `load_approved_spec` の後へ移動 | pin test の呼出し回数 assert (無 pin 経路が 0、pin 経路が 1 になる)。**訂正 (段 6 レビュー A 所見 3)**: genuine g1 正例は同じ `no-approved-spec` のままなので KILL しない |
| M6 | `exc.reason` の素通しを定数 `"floor-selection-unverifiable"` へ潰す | genuine g1 負例 (`floor-selection-rule-mismatch` と不一致) |

登録しないもの: `ManifestCliError` の detail 文言だけを変える変異 (reason と
fail-closed 挙動を変えない)。fixture 未追随のままの 1369 / 1395 は正しい gate 自体で
赤になるので baseline として無効。

## (5) ユーザーへ返す裁定パッケージ (実装しない)

1. **report / verdict / judge の選択未被覆。** historical reverify は選択 identity を
   実行しない。この 3 consumer へ同種の強制を広げるか。広げる場合、report と judge は
   `_GENERATOR_SOURCES` に含まれるため凍結成果物の bytes が変わる。
2. **`build_manifest` / `write_manifest` の公開迂回口。** 現在の repo 内 caller は
   test helper だけ。「supported な production 生成面は `build_approved_manifest` だけ」と
   境界を文書で固定するか、別 API を設けるか。
3. **「load-only consumer 3 群」という母集合の再確定。** 1 の事実により、
   先行 wave が数えた 3 群は過少である可能性がある。
4. **床値選択 eligibility 導出の被覆の穴 (段 6 レビュー A 所見 2)。**
   `_derive_floor_selection_eligibility` を実際に走らせて rule-mismatch を出す test は
   repo に存在しない。既に landed している API 自身の test
   (`test_s8b_ratified_verify.py` の `test_g1_selection_helper_rejects_rule_mismatch`、
   `test_launch_validate_rejects_floor_selection_rule_mismatch`) も同じ関数を stub している。
   したがって「実導出が常に False を返す」変異は launch 経路でも本 consumer 経路でも生存する。
   **これは本 wave が作った穴ではなく、変更前後で同一の既存状態である。**
   閉じるには実 manifest / journal / admission evidence を備えた genuine earlier run の
   fixture が要り、`s8b_holdout_freeze` 側の一般的な強化になる。本 wave の scope 外。

## 段 6 レビューの裁定

| # | 出所 | 所見 | 裁定 |
|---|---|---|---|
| RA1 | レビュー A | genuine g1 正例が `no-approved-spec` の出所を識別しない。gate が同 reason を出す変異が全 test を通る | **real・採用・must-fix**。正例へ `__cause__` が `ReviewedSpecError` である assert を足す |
| RA2 | レビュー A | 負例が eligibility 導出を stub しており実導出の変異を殺せない | **real・must-fix 不採用**。既存 API test も同じ stub を使っており、本差分の前後で被覆は同一。`DW-G05` の成果物影響を本差分へ帰属できない → 裁定パッケージ 4 |
| RA3 | レビュー A | M4 / M5 の KILL 帰属記録が現物と不一致 | **real・採用**。上の変異表を訂正した。コード変更なし |
| RA4 | レビュー A | `eligibility_calls == [earlier_rel]` は恒真ではないが探索 topology の確認に留まる | **real・nit**。記述の精度のみ |
| RA5 | レビュー A | 既存 assert の削除・緩和・揮発 payload は無し。patch と現物は一致 | **確認事項**。所見ではない |
| RB1〜RB6 | レビュー B | must-fix 0。受理集合の縮小は選択違反 g1 に限定。新理由の増設なし。import の collection 障害なし。共有 helper の前提不変。D1370 / D1313 の境界内 | **確認事項**。RB6 (generic builder の迂回口) は裁定パッケージ 2 と同一 |
