# [T-529] 実装の再起票 — 裁定 E 前半と [T-615] を実装した wave

wave branch: `worktree-dev-wave-t529-impl-reraise`
基準 commit: c9990bc2 / 実装 tip: 段 7 の記録 commit (worklog fragment を参照)
受入全走: **7168 passed / 20 skipped** (merge tip `11145d19`、Pegasus dispatch job `894904.nqsv`)

## 何を実装し、何を実装しなかったか

**実装した (2 単位)。**

1. **裁定 E の前半** — 較正 artifact の検証述語 (path 封じ込め・一回読み・bytes SHA・
   `calibration/v2` schema・env_tag・clocks_per_us・effective clock policy・grandfathered v1) を
   `orchestrator/campaign/calibration_verify.py` へ抽出し、
   `env_attestation.load_verified_calibration` を型境界 wrapper にした。leaf は
   `campaign.env_contract` を直接にも間接にも import しないため、将来 `env_contract` の
   初期化中から較正検証を呼んでも循環 import にならない。
   新 leaf は実行意味論 module 閉包・env 中立 AST 閉包・T419 submission binding の 3 面へ加えた。
2. **[T-615]** — 凍結済み floor protocol の検証を historical 再検証と current admission の
   2 lane へ分けた (D `{{D:floor-protocol-two-lane}}` として記録)。

**実装しなかった (scope 外)。** bootstrap fuse の除去、後継世代の登録、
裁定 A(b) の ever-active 限定、裁定 D の世代遷移述語、activation record / receipt /
authority loader、入口 receipt。**活性化権限そのものは 1 行も入っていない。**

## この wave が確定させた事実

- **`DW-G04` の発火素材は実在する。** `calibration-94a4b79fa31bba3c.json` (accepted /
  `calibration/v2` / env_tag 一致) と計測 ID `892707.nqsv` (`calibrate_rc = 0`)。
  この較正を指す prospective 後継世代は `is_valid_successor` を True で通り
  (`contract_sha256 = 1346c20b5519be4b…`)、`load_verified_calibration` も ACCEPT する。
  D196 / D215 の理由 (b) は事実認定が古い。
- **ただし「正規 g2」ではない。** runtime loader が外部検証するのは path 封じ込め・bytes SHA・
  schema・env・clock・policy までで、publish 記録・job-result・self-comparison・final receipt は
  読まない。schema は `quality.status=rejected` 自体を許す。正確な呼称は
  「レビュー済み commit が束縛する publish 済み較正であり、後継世代の実在素材」。
- **保留の残る根拠は入口面 1 本に狭まった。** floor は Python 起動前に attempt の
  stdout / stderr / launch marker を書き、T-126 は `.git` を持たない source stage から
  driver を起動する。裁定 C(a) はこれを [T-609] へ外出ししただけで、コード上は閉じていない。
- **[T-607] の従属先は誤っていた。** freeze v2 の active pointer は env 契約の世代活性化とは
  別機構で、approval と pointer は非 merge かつ逐語 `AI-Agent: none` の commit を要求する。

## ファイル

| ファイル | 中身 |
|---|---|
| `s1-brief.md` | 段 1 brief。前提実測 9 点と provisional 裁定 (P1)〜(P4) |
| `s2-plan.md` | 段 2 プラン起草 (判定 NO。ただし 94a4 の実在を指摘して親前提を反証) |
| `s3-lensA.md` | 段 3 レンズ A — 正しさ境界と裁定整合 (NO-GO 同意、根拠を [T-609] へ限定) |
| `s3-lensB.md` | 段 3 レンズ B — scope 被覆と実装可能性 (YES。E 前半は独立に実装可能) |
| `s4-adjudication.md` | **段 4 裁定 (正本)**。親の裏取り 7 点、単位 1 の scope、変異事前登録 |
| `s5-impl.md` | 段 5 単位 1 の実装報告 |
| `s6-lensC.md` | 段 6 レンズ C — 挙動同値性 (must-fix 1: profile hash の二重正本) |
| `s6-lensD.md` | 段 6 レンズ D — 閉包網羅 (must-fix 1: T419 binding からの leaf 脱落) |
| `s6-fix.md` | 段 6 単位 1 の fix 報告 |
| `s2b-plan.md` | [T-615] の設計 (live admission との衝突を D202/D213 で立証) |
| `s4b-addendum.md` | **段 4 裁定の追補 (正本)**。[T-615] 同梱の裁定と変異事前登録 |
| `s5b-impl.md` | 段 5 単位 2 の実装報告 |
| `s6b-lensE.md` | 段 6 レンズ E — live admission (must-fix 0) |
| `s6b-lensF.md` | 段 6 レンズ F — 受理集合 (must-fix 1: `str` 派生型で 2 lane が食い違う) |
| `s6b-fix.md` | 段 6 単位 2 の fix 報告 |

## 変異台帳

| ファイル | 中身 |
|---|---|
| `mutation-ledger-run1-erratum.json` | run 1 (9 件)。**KILLED 3 / MISMATCH 6、SURVIVED 0**。登録漏れ 0 で、波及が登録より広い方向のズレ |
| `mutation-ledger.json` | run 2 (9 件)。実測どおりの期待 node で **9/9 KILLED**、baseline 緑 |
| `mutation-ledger-v3.json` | run 3 (13 件、単位 2 込み)。**13/13 赤、SURVIVED 0**。KILLED 8 / MISMATCH 5 (うち 4 件は超集合方向) |
| `mutation-ledger-v4.json` | M13 再照準。**SURVIVED** — exact `GenerationEntry` 検査は単独では load-bearing でない |
| `mutation-ledger-v5.json` | M14 両層同時。**SURVIVED** — 3 層目 (共有 leaf の広い `except Exception`) が mask していた |

**`[invalid-return]` ケースは過剰決定であり、`DW-M03` に従い単独変異の証拠から外す。**
同テストの `unknown` / `cross-env` は単一理由で M10 が kill している。
3 層目の `s8b_floor_contract.validate_protocol` は本 wave の編集範囲外のため触っていない。
テストを単一理由へ強める件は次の一手へ起票した。

## 変異 harness の運用知見

runner argv と `--runner-mode` の食い違いで 3 度 fail-closed した (詳細は failures fragment)。
**先例と同じ recipe が正解である** —
`--runner-mode dispatch` + `python3 tools/run_tests.py --force-dispatch -rf <対象 module> -p no:cacheprovider`。
`--runner-mode local` を指定しても `run_tests.py` は login node の headroom 次第で
内部 dispatch へ倒れるため、mode と実態が食い違う。
