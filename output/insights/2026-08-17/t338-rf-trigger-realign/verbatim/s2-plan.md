## 前提の実測

基準は `HEAD=699c9caedec83402d633f86342429bedf86f82a9`、worktree は clean、残 handoff は README のみだった。

- **M1 — 不一致。ただし計画は厳密化すれば成立する。** 公表層への実質的依存は D291 `addendum_p_freeze_precondition` の末文にあるが、禁止状態そのものは `pilot_submission = forbidden` にも明記され、解除権限は D292 が canonical decision に限定している。したがって新 decision は「末文だけを失効」「禁止状態は維持」「解除ではない」の3点を分けて書く必要がある。`docs/decisions.md:13470-13478,13581-13588`

- **M2 — 一致。** D291 は固定 commit の `docs/decisions.md` blob から読み出され、`operational_state_on_fold` を含む各節に SHA-256 がある。`orchestrator/publication/approval_d291.py:21-29,124-145,452-487`

- **M3 — 一致。** `rg -n 'D162' orchestrator tools --glob '*.py'` は 0 hit、終了コード 1。D162 を番号で機械参照する Python consumer はない。

- **M4 — 一致。** `env_tag: "pegasus"` と `attestation_mode: "required"` は同じ exact 環境契約にあり、D162 の自然言語発火条件とは別の受理面である。`orchestrator/qualification/contract.py:150-159`

- **M5 — 一致。ただし「この追記で意味が変わる production consumer」に限定する。** `report.py` は HEAD の D291 後続節を走査する唯一の D291 supersession consumer。純粋 scan の実測は `possible_supersession / D292,D305,D313,D316`。`orchestrator/campaign/s8c_preregistration.py` にも decisions 見出し検査はあるが、世代導入 commit の ruling 存在確認であり、本 docs-only 追記の D291 意味は消費しない。`orchestrator/publication/report.py:75-111,114-190`

- **M6 — 一致。** report test は D292 membership と数値順・重複なしだけを要求し、ID 列全体を固定していない。`orchestrator/tests/test_t793_report.py:33-50,65-77`

- **M7 — 一致。** D292 は解除主体だけを canonical decision に限定し、解除条件の中身を意図的に未定義としている。`docs/decisions.md:13581-13596`

- **M8 — 一致。** D229 決定 (6) は `producer → pilot → validator/consumer → 本走` の順序と、pilot を発火条件 (i)(ii) の充足計測にする設計を固定している。`docs/decisions.md:10750-10758`

- **M9 — 一致。** `docs/decisions.md` は living-doc byte budget の対象外。ただし D 見出し、spool 構造、placeholder などの検査対象から外れるわけではない。`tools/check_docs.py:43-47`

- **P1 — 一致。** D291 の末文だけを D322 型の文限定 supersession とし、前2文の追補 P 凍結条件は維持できる。D282 の `forward_supersedes` / `preserved` も射程限定の先例になる。`docs/decisions.md:12884-12891,14600-14603`

- **P2 — 一致。** D162 (10)(ii) の前向き改訂だけで足りる。Python consumer はなく、環境契約は別面なのでコード変更は不要。

- **P3 — 一致。** 実装差分はゼロでよい。段 5 / 6 の省略確定は段 4 の親裁定事項だが、段 2 の実測上、コード変更を必要とする consumer はない。

- **P4 — 一致。ただし action は `見送り` が必要。** `[T-339]` を `完了` にすると未実装残件ゼロを偽る。`更新` では active ID が二重に残る。したがって `[T-338]` を `更新`、独立 task としての `[T-339]` を `研究・計測系` へ `見送り` とし、残作業の所有を `[T-338]` へ移す。所有移動を見送り台帳へ置く先例は `docs/phase3.md:806-807` にある。

- **P5 — 一致。** 公表層依存を外した後の pilot readiness は、RF producer + attempt registry、pilot 記録項目の単独 gate、環境契約下の実走の3点。これとは別に、D292 による将来の canonical 解除 decision と D162 (iii) の実 hook は残る。

## decision fragment の設計

対象は `docs/spool/decisions/2026-08-17-dev-wave-t338-rf-trigger-realign-1.md`。placeholder slug は `rf-trigger-pilot-realignment` とする。

`file:line` 配置は次のとおり。

- `:1-7` — frontmatter 全体。

```yaml
---
schema: izanagi-spool-v1
ledger: decisions
authored: 2026-08-17
wave: dev-wave-t338-rf-trigger-realign
seq: 1
---
```

- `:9` — H2。

```markdown
## {{D:rf-trigger-pilot-realignment}}. RF validator の発火条件と pilot の公表層依存を前向きに改訂し、producer から consumer までを 1 scope に戻す
```

- `:11-17` — **決定 (1): D162 (10)(ii) の前向き改訂**
  - 旧4項から `attestation` だけを落とす。
  - 新しい exact 列を「環境タグ・測定 checkout・pin」の3項とする。
  - 条件 (i) と (iii) は不変と明記する。

- `:19-25` — **決定 (2): 受理集合との境界**
  - `orchestrator/qualification/contract.py` の `env_tag` と `attestation_mode` は変更しない。
  - attestation の削除は D162 の機械化発火条件だけであり、qualification/admission の受理条件を緩めない。
  - 環境タグを残す理由を、D320 が測定の公正と環境契約タグを対象外としたことに結び付ける。

- `:27-37` — **決定 (3): D291 末文だけの前向き失効**
  - `addendum_p_freeze_precondition` の末文「pilot もそれまで投入しない」だけを前向きに失効させる。
  - 公表台帳の実体確定を追補 P 凍結の前提とする前2文は維持する。
  - pilot 投入の可否を、公表層実装と追補 P 凍結の双方から切り離す。
  - D291 本文、payload、承認済み三つ組、値射影、exact closure は編集・再承認しない。

- `:39-48` — **決定 (4): 本 decision は解禁ではない**
  - `pilot_submission = forbidden` と `main_submission = forbidden` を維持する。
  - D292 の解除権限をそのまま維持し、future canonical decision が別途必要と書く。
  - 本 decision、worklog、実装完了報告のいずれも投入権限を付与しない。
  - `report.py` の deny-only literal は変更しない。

- `:50-58` — **決定 (5): 残る実質条件**
  - RF producer と attempt registry の実体。
  - pilot が記録する項目の確定。D229 決定 (6) の単独 gate と位置付ける。
  - exact 環境契約下の pilot 実走。
  - D162 (iii) の実 hook は validator/consumer 段で満たす残件として別記する。

- `:60-68` — **決定 (6): scope と順序**
  - `producer → pilot → validator/consumer` を同一 task scope に戻す。
  - これは原子的実装や並列実装を意味しない。
  - D229 決定 (6) の全順序 `producer → pilot → validator/consumer → 本走` は supersede しない。
  - 本走は引き続き validator/consumer より後であり、投入禁止も維持する。

- `:70-76` — **理由**
  - attestation 証跡と環境タグでは D320 上の扱いが異なる。
  - 公表層の実装待ちを pilot へ伝播させる必要はないというユーザー裁定。
  - D291 の bytes を遡及変更せず、後続 decision で射程を限定する理由。

- `:78-86` — **却下した選択肢**
  - 環境タグも落とす。
  - `attestation_mode` を optional にする。
  - D291 を直接書き換える。
  - 本 decision を pilot 解禁として扱う。
  - validator を pilot より先に置く。
  - D229 の順序を2段階へ縮める。

- `:88-93` — **研究状態への影響**
  - certified 選択、材料レポート、proof chain、凍結 bytes、既存 gate、受理集合は不変。
  - producer、pilot artifact、validator/consumer のいずれも本変更では生成しない。
  - 変わるのは発火条件の証拠水準、公表層との依存辺、task ownership の3点だけ。

decision 本文には `[T-338]` / `[T-339]` を書かず、task ID の移動は worklog だけに置く。

## worklog fragment の設計

対象は `docs/spool/worklog/2026-08-17-dev-wave-t338-rf-trigger-realign-1.md`。

- `:1-8` — frontmatter 全体。

```yaml
---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-08-17
wave: dev-wave-t338-rf-trigger-realign
seq: 1
title: RF validator 発火条件と pilot 条件を前向きに改訂し、[T-339] を [T-338] へ統合する (docs のみ、branch worktree-dev-wave-t338-rf-trigger-realign)
---
```

- `:10-20` — `## 本文`
  - 2026-08-16 ユーザー裁定 D1 + D2 → B、C 不採用を記録。
  - canonical 判断を `{{D:rf-trigger-pilot-realignment}}` で参照。
  - D291 bytes、コード、schema、凍結 artifact、研究成果物が不変であることを記録。
  - 親が実走した検査だけを rc、件数、request ID 付きで記録する。未実走を緑と書かない。

- `:22` — `## 次の一手差分`

- `:24-31` — `### 更新`、対象 `[T-338]`
  - 状態を「docs 条文化済み、producer から validator/consumer までの実装待ち」へ更新。
  - 同一 scope 内の順序、非解禁、残る3条件、D162 (iii) を簡潔に持たせる。
  - decision は同 wave placeholder で参照する。
  - 現在の substantive item digest:

```text
base: 93be2837da1554cb3740dbf10da165cd17354ab000869fa5ae890d0ad85e8f6e
```

- `:33-41` — `### 見送り` → `#### 研究・計測系`、対象 `[T-339]`
  - 「独立 task としては `[T-338]` へ統合」と書く。
  - `理由:` に、未実装残件は `[T-338]` が保持し、active のまま残すと同一 scope が二重在籍するため、と書く。
  - 「完了」や `remaining: none` は書かない。
  - 再訪条件は「後続裁定が `[T-338]` から独立 ownership を再分離したとき」。
  - 現在の substantive item digest:

```text
base: 971cc45405f6b7d599b9238b7d5b9ed69e7aebeb3a45de5541e97c04f35bda6e
```

`carry`、`完了`、`新規` は置かない。`見送り` のため、fold 後は `[T-339]` が active 集合から外れ、`docs/phase3.md` の研究・計測系へ ownership 移動記録が生成される。

## 影響と検査

コード変更は不要。変更しないことで壊れる consumer もない。

- D162 の Python 参照は 0 件。
- D291 resolver は固定 commit blobを読むため、新 decision の追記で payload は変わらない。
- HEAD report は新 D を `possible_supersession` の ID 列へ追加するが、現在すでに同状態であり、`pilot_submission = forbidden` も維持される。
- report test は ID 列の exact pin を持たない。

親が実行すべき検査は次のとおり。

1. `python3 tools/check_docs.py`
   - 赤条件: frontmatter、ファイル名、H2、placeholder、worklog action 構造、未知 field、D 番号直書き。
   - stale `base` は検出しない。

2. `python3 tools/spool_fold.py --dry-run --show-diff`
   - 赤条件: 上記 base digest が並行 land で stale、`研究・計測系` が非一意、placeholder 未解決、active 集合保存則違反。
   - diff で `[T-338]` だけが active に残り、`[T-339]` が見送り台帳へ1回だけ移ること、D291 既存行に変更がないことを確認する。

3. 焦点テストは必ず `tools/run_tests.py` 経由で行う。

```bash
python3 tools/run_tests.py \
  orchestrator/tests/test_t793_report.py \
  orchestrator/tests/test_t793_approval_d291.py \
  orchestrator/tests/test_spool_fold.py::test_all_mutating_operation_blocks_resolve_placeholders \
  orchestrator/tests/test_spool_fold.py::test_n10_stale_base_digest_is_rejected \
  orchestrator/tests/test_spool_fold.py::test_completion_update_and_defer_form_explicit_sinks
```

   - 赤条件: D291 pin 解決失敗、後続 D291 参照の scan 漏れ、deny-only literal の変化、cross-ledger placeholder 不解決、更新と見送りの sink 不成立。
   - fold 前の pytest は新 decision が canonical HEAD にまだ無いため、新 D の実 ID追加自体までは検査しない。

4. 受入全走: repo root から `python3 tools/run_tests.py`
   - docs-only でも親 brief により免除しない。
   - 任意の赤、infra 判定、未完走を緑へ読み替えない。

5. repo 共通検査:
   - `python3 tools/check_codex_agents.py`
   - commit 後に `python3 tools/check_ai_provenance.py`

6. fold 後の read-only 確認:
   - `python3 -m orchestrator.publication.report .`
   - 新 D が `decision_ids` に追加され、`possible_supersession`、`submission_authority=not_granted`、両 submission の `forbidden` が維持されることを確認する。

本 read-only 環境では pytest と受入全走は完了していない。書込可能 tmp 不在のため pytest 初期化前に停止し、緑は主張しない。純粋な HEAD supersession scan だけは成功し、`D292,D305,D313,D316` を得た。

## 残る risk

- pilot の解除条件は依然として未定義。D292 に従う別 canonical decision が必要。
- producer、attempt registry、記録項目 gate、pilot 実走、validator/consumer hook は未実装。
- `attestation` は D162 発火条件からだけ外れる。exact 環境契約の `attestation_mode: required` は残るため、契約を満たさない pilot が受理されるわけではない。
- 公表台帳の実体確定と追補 P 凍結の依存は残る。解消するのは pilot への依存辺だけ。
- `[T-339]` の `見送り` は fold 時に `docs/phase3.md` も生成更新する。 authored file は指定2本だけだが、canonical post-fold bytes まで「2ファイルだけ」と解釈するなら P4 と spool action 文法が両立しない。
- 並行 land が `[T-338]` または `[T-339]` を先に更新すれば base は stale になり、fragment の再起草が必要。
- report の新 D ID は canonical fold 後にしか現れないため、pre-land acceptance だけでは実 ID を使った出力を実測できない。

## 総括

新 decision は D162 (10)(ii) と D291 末文だけを前向きに改訂し、D292 の禁止状態と解除権限、D229 の順序、環境契約、受理集合を維持する。worklog は `[T-338]` を更新し、未完了の `[T-339]` を `完了` ではなく `見送り` で吸収する。実装差分はゼロでよい。