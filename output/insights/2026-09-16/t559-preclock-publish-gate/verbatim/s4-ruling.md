# 段 4 裁定 — [T-559] publish 前 pre→post clock 照合

## 結論

段 2 plan を **条件付きで採用**し、下記 plan v2 を実装する。実装面は Codex `role=author` の子 1 本。
編集面は `orchestrator/calibrator/cli.py` と `orchestrator/tests/test_calibrator_certify.py` の 2 file だけ。

## 所見の裁定

| # | 出所 | 所見 | 裁定 |
|---|---|---|---|
| 1 | A-1 | 親の実測 (外側 wrapper の post 7 件) は、新 gate が読む CLI 内 `static_post` の到達性の証拠ではない。F108 の 23 は標本列数、親の 7 は attempt 数で単位が違う | **real・採用。** 記録の主張を「外側 wrapper 観測 7 件の実測」に限定し、次回 job の成功確率を推定しない。「計算ノードでは再現していない」とは書かない |
| 2 | A-2 | key 形を保ったまま expected/observed を逆転すると、pre を pre 中央値で検査して**常に通る** | **real・採用。** 変異 M02/M03 に登録。spy は「呼ばれた」だけでなく expected が凍結 dynamic pre、observed が `static_post` と**一致すること**を assert する |
| 3 | A-3 | 主要負例の中央値・帯は成立する (中央値 2101.0、帯 2058.98–2143.02、2110 は帯内、3079.456 は帯外) | **real・採用。** 親も独立に検算し一致 |
| 4 | A-4 | 末尾 append なら既存 reason を消さない。early 未評価一覧の追加は early の受理集合を変えない | **real・採用** |
| 5 | A-5 | sidecar だけでは canonical 判定を再計算できない。policy が benchmark 中に変わった場合、照合時の policy 値が残らない | **real・採用。** sidecar に**照合時 policy 値**を記録する |
| 6 | A-6 / B-1 | 「publish 前照合」は満たすが、benchmark 中の振れ・外側 `attestation-post.json`・観測者効果は保証しない | **real・採用。** 成果物に限定文を逐語で書く (下記「名乗り」) |
| 7 | B-2 | published bytes 不変は条件付きで成立。保証できるのは「同じ既存入力に対する bytes」であり、別 attempt 同士の一致ではない。sidecar は公開 bytes の外 | **real・採用。** 不変条件 2 を条件つきに書き直す |
| 8 | B-3 | D191・D218・D155 との衝突は確認できない | **refuted (衝突の主張は成り立たない)。** 整合を確認済みとして進む |
| 9 | B-4 | plan の行番号 9 箇所に重大なずれなし。brief の `env_contract.py:263–277` は 2 件目 hash の `:279` を含まない | **real・採用。** 参照を `:263–279` に訂正 |
| 10 | B-5 | canonical へ委譲する spy は「呼ばれること」を示すが「**戻り値が受理判断を支配すること**」を示さない。戻り値を捨てて `diagnostics["band_pass"]` で判定する変異が生存しうる | **real・採用。** policy 変更負例 (下記) で戻り値依存を証明し、変異 M05 に登録 |
| 11 | B-6 | early 未評価一覧の変更は `test_calibrator_certify.py:841,959,1237,1454` の完全一致 assertion に届く。共通定数 `:34–45` の 1 箇所更新で追随 | **real・採用。** 実装子へ 4 箇所を名指しで渡す |
| 12 | B-7 | **成功時**の pre→post 判定は成果物から再計算できない (plan は失敗時しか証拠を残さない) | **real だが scope 外。** 受理集合も published bytes も参照も変えないので `DW-G05` の must-fix に当たらない。**裁定パッケージ候補**としてユーザーへ返す |
| 13 | B-7 | 不変条件 2 は pin 保全に不可欠ではなく、今回の保守的な自己制約である | **real・採用。** 理由づけを「schema 改訂を避けるための本 wave の自己制約」と正直に書く |

## plan v2 (実装仕様)

### 1. 挿入位置

`orchestrator/calibrator/cli.py` の `_certify_main` 内、既存
`if not _effective_clock_self_comparison_passes(profile): ...` (`:1015–1016`) の**直後**、
`status = "accepted" if not reasons else "rejected"` (`:1017`) の**直前**。

publish transaction (`:1039` 以降) は 1 行も動かさない。
`_published_self_comparison_receipt` (`:1079`) も動かさない。拒否時に published artifact を削除しない。

### 2. 比較

```
expected = {"samples_mhz": profile["effective_clock"]["samples_mhz"],
            "tolerance_pct": profile["effective_clock"]["tolerance_pct"]}
observed = {"samples_mhz": static_post["effective_clock"]["samples_mhz"]}
```

判定は `effective_clock_comparison_passes(expected, observed)` の**戻り値だけ**で行う。
診断値 (`effective_clock_comparison_diagnostics`) を受理判断に使わない (D191 決定 6)。
帯計算を再実装しない (D191 決定 1)。canonical 述語と policy 定数を変更しない。

expected は**凍結した dynamic pre** (`profile`) とする。`static_pre` でも `static_post` でもない。

### 3. reason code

失敗時に `reasons.append("effective-clock-pre-post-comparison-failed")`。
既存 reason を消さず、統合せず、末尾へ足す。

`_EARLY_CLOCK_REJECTION_NOT_EVALUATED` (`cli.py:75–86`) へ
`"late-effective-clock-pre-post-comparison"` を、**実行順どおり**
`"late-effective-clock-self-comparison"` の直後・
`"final-artifact-assembly-and-schema-validation"` の直前に挿入する。

### 4. 失敗時 sidecar

失敗分岐内、`status` 決定より前に、既存 `_write_exclusive` で
`<staging>/effective-clock-pre-post-comparison.json` を 1 つだけ書く。内容は次に限定する。

- `schema`: 新しい固定文字列 1 本 (既存 `_PUBLISHED_SELF_COMPARISON_SCHEMA` と別)
- `passed`: `false`
- 凍結 `attestation_profile` 全体と、その SHA-256 (既存 `_canonical_json_bytes` で算出)
- `canonicalization`: 既存 `_ATTESTATION_PROFILE_CANONICALIZATION` (`cli.py:90–92`)
- canonical 述語へ渡した `expected` と `observed` の実入力
- `diagnostics`: `effective_clock_comparison_diagnostics(expected, observed)` (受理判断には使わない)
- **`policy_at_comparison`**: 照合時点の `effective_clock_policy.EFFECTIVE_CLOCK_TOLERANCE_PCT`
  (所見 5。これが無いと policy 変更時に判定を再計算できない)

新 helper・新台帳・新 schema validator・成功時 sidecar は作らない。

### 5. 名乗り (成果物へ逐語で書く限定)

> 本 gate は、CLI が benchmark 直後に取得した post clock と凍結 pre profile の canonical 照合を
> publish 前に課す。benchmark **中**に帯外へ振れて post 観測までに戻った変動は検出しない。
> CLI 終了後に外側 wrapper が撮る `attestation-post.json` は本 gate の検査対象外であり、
> その窓は残る。probe の観測者効果 (F108) は是正しない。

### 6. 不変条件 (条件つきに書き直したもの)

1. 規律 2 を緩めない。受理を狭める方向にだけ効き、既存 reason を消さない。
2. **同じ既存入力に対する accepted artifact の published bytes を変えない。** 成立条件は
   (a) 凍結 `profile` の標本・順序・型・tolerance を変えない、(b) `result_to_dict` 出力・receipt・
   genome・schema version を同一に保つ、(c) 合格時の `status="accepted"` と空 `reasons` を維持、
   (d) JSON serialization 設定と末尾改行を維持、(e) post 情報を artifact のどの field にも
   混入させない (`notes` を含む)。これは pin 保全に不可欠だからではなく、schema 改訂を避ける
   本 wave の自己制約である。
3. canonical 述語 (`execution_guard.py:324`) と `effective_clock_policy.py` を変更しない。
4. publish の位置・順序・公開後再読を変更しない。拒否時に published artifact を削除しない。

## 変異事前登録 (DW-M01)

位置はすべて `orchestrator/calibrator/cli.py` の新規ハンク内。全件 **KILLED 期待**。

| ID | 変異 | 期待する検出 |
|---|---|---|
| M01 | 新 gate のブロックごと削除 | 帯外 post 負例が accepted になる |
| M02 | `expected` と `observed` を入れ替える | 逆転 assert と帯外 post 負例 |
| M03 | `observed` の供給源を `static_post` から `profile` へ替える (自己照合へ退化) | 帯外 post 負例 |
| M04 | `expected` の供給源を `profile` から `static_pre` へ替える | static pre だけ帯外にした**正例** |
| M05 | canonical の戻り値を捨て `diagnostics["band_pass"]` で判定する | **policy 変更負例** (帯内だが policy 不一致) |
| M06 | 条件は評価するが `reasons.append` を消す | 帯外 post 負例 (accepted になる) |
| M07 | `tolerance_pct` を凍結値でなく現行 policy 定数から取る | policy 変更負例 |
| M08 | 新 gate を `status` 決定の**後ろ**へ移す | 帯外 post 負例で registered/publish が作られる |
| M09 | 条件を恒真拒否 (`if True:`) にする | **帯内 post 正例** (承認外の過剰拒否の正例。受理集合を縮小する wave の義務) |

期待 node の完全集合は実装後に確定する。`DW-M08` に従い、初回は **probe と明記して全件 SURVIVED で
登録**し、観測 node を集めてから完全集合で再登録・再走する。初回 spec と台帳は erratum として残す。

## テスト要件 (段 5 の実装子へ渡す)

既存 fixture (`_pegasus_shaped_probe` `:253`、`_expect_48_physical_cores` `:286`、
`_fake_calibrate` `:367`、`_invoke` `:379`) を**変更しない**。48 標本・3 回 profile 取得・
tolerance を持たない observed profile という形を崩さない。既存テストの期待値を変えない
(例外は `_EARLY_CLOCK_NOT_EVALUATED` `:34–45` の 1 定数のみ)。

必須の入力は次の 6 種。

1. **主要負例**: 3 行の標本を `[2101.0]*47+[2095.0]` / `[2101.0]*47+[2110.0]` / `[2101.0]*48` とし、
   post の 1 標本だけを `3079.456` にする。`outlier_index` を `[0, 24, 47]` で parametrize。
   → 新 reason ちょうど 1 件、registered 未作成、publish receipt 未作成、公開後 self receipt 未作成、
   sidecar だけから hash と判定を再計算できること。
2. **正例**: 3 行とも帯内。accepted になり、probe 呼び出しは 3 回、benchmark stub は 1 回。
3. **下側負例**: post に低側の帯外値を 1 個置く。
4. **expected 取り違え正例**: `static_pre` だけ `[2300.0]*48`、dynamic pre と post は `[2101.0]*48`。
   accepted のままであること (M04 を殺す)。
5. **post 自己照合取り違え負例**: post を `[2300.0]*48` にする。post 自身の self は通るが
   pre→post は落ちる。
6. **policy 変更負例**: benchmark 中に `EFFECTIVE_CLOCK_TOLERANCE_PCT` が変わり、post は全標本帯内。
   → canonical の戻り値が False になるので新 reason が出る。`diagnostics["band_pass"]` は True なので、
   戻り値を使わない実装ではこの reason が出ない (M05/M07 を殺す)。既存の self reason も同時に出るため、
   **両 reason の存在**を要求する。

加えて `bad_cv` との複合で `["within-run-cv-invalid", "effective-clock-pre-post-comparison-failed"]` の
順序を検証する (既存 reason の上書き検出)。

canonical への spy は「呼ばれた」だけで closed としない。expected が凍結 dynamic pre と、
observed が `static_post` と**値一致**することを assert する。

`_EARLY_CLOCK_NOT_EVALUATED` の期待値定数を 1 箇所更新すると
`test_calibrator_certify.py:841,959,1237,1454` の完全一致 assertion が追随する。4 箇所とも緑を確認する。

## scope 外として裁定パッケージへ返すもの

1. **成功時の pre→post 判定証拠** (所見 12)。成功した照合は成果物から再計算できない。
   受理集合・published bytes・参照を変えないので must-fix ではないが real。
2. 外側 wrapper `attestation-post.json` の評価と、それによる publish 取り消し。
   T-559 原文の窓のうち CLI 外の部分は残る。
3. probe の観測者効果 (F108) の是正 — D155 決定 (4) が既にユーザー再裁定へ返している。
4. 別 process verifier ([T-560]) — D218 が実装しないと定めている。
