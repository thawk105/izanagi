# [T-2067] oracle gate core の v2 二読 fallback を廃し、exact `LaunchValidatedFreeze` を必須にした

`authority: none` / `default_effect: no-state-change` — これは**開発 wave の記録**である。可変状態の正本
(worklog 末尾・現行 phase doc) ではない。gate の受理集合は狭まる方向にだけ変わった (§4)。

- 作業日: 2026-09-17 (JST 00:25〜03:40、記録 commit まで。最終受入と land はその後)
- 基準 commit: local main `1042a1bc95057fa03117d504cfa2b0fafaae60d0` (着手時点は `20a92f6a6`、直後に T-2630 が land したので ff で揃えた。編集面 3 file に差分なし)
- 実装 commit: `d6d3360f8` (production + 新規 test、Codex author) → `cb64c51ed` (docstring 2 箇所の fix、Codex author) → `b625a1671` (受入赤 2 件の fix: 行番号 pin と allowlist、Codex author)
- 依頼: 「`_gate_check_core` (:496 付近) の二読 fallback を廃し、exact な `LaunchValidatedFreeze` を必須にして D65 決定 (5) の
  不変条件を全分岐で成立させる (D1872、2026-09-09 裁定済み、択 (ii))。D1241 / D1313 の上限は解除しない。t080 系が
  `test_s8b_oracle_driver.py` を扱うので重なるなら test 側は触らず production + 新規 test file。Codex author + 変異事前登録。
  本題の fallback 廃止だけ。仮想リスク向けの gate・検査・台帳・一般化は scope 外。規律 2 を緩めない。」

---

## 1. 結論を先に

**閉じた。** `_gate_check_core` の v2 枝 (`floor` または `budget` が non-null) は、`launch_validated` が無ければ必ず refusal
`v2-execution: launch-validate: LaunchValidatedFreeze exact type が必要` を積み、自前で `load_ratified_freeze(root)` を
呼ばなくなった。到達経路 (`gate_check` の初回 `_load_verified_freeze` 失敗 → core の再読成功、D1831 決定 2) を
`_load_verified_freeze` の side_effect で再現し、static loader を **hash 一致の合成 `RatifiedFreeze` を返す fake** にした
負例は、旧 code では `allowed=True`、新 code では refusal 1 件で `allowed=False` になる (段 6 レンズ A が旧 code の `-` 行で
論証、変異 M1 / M3 が実測)。

| 項 | 値 |
|---|---|
| production 差分 | `orchestrator/campaign/s8b_oracle_driver.py` +18/−28 (実装) と +7/−5 (docstring fix) |
| 新規 test | `orchestrator/tests/test_s8b_gate_core_exact_launch_validated.py` 245 行、12 種 17 node |
| 既存 test file の編集 | 0 (t080 系 branch `impl-dev-wave-t080-accept-speed` が `test_s8b_oracle_driver.py` 865〜1950 行を保持、他 5 worktree でも dirty) |
| 焦点走 (計算ノード) | 新規 file 単独 17 passed (4.69 秒)、既存 consumer 28 passed / 6 skipped (skip は既存 growth hold) |
| 変異 matrix | container worktree (`b625a1671` 固定)、baseline PASSED、10 変異 = 対照 M0 SURVIVED + 9 KILLED (期待 node 完全一致、MISMATCH 0)。うち受理境界の KILL は M1〜M5・M8 の 6 件、M6 / M7 / M9 の 3 件は診断 pin (別枠) |
| 受入全走 | post-1 (tip `cb64c51ed`): child 2 failed / 24401 passed / 67 skipped — 赤 2 件は本 wave 起因 (行番号 pin・allowlist) で fix-2 `b625a1671` で閉じた。wrapper は親起因の untracked で rc=70。最終受入 final-1 は記録 commit の tip で走らせ、結果は §7 と land の受領証が持つ |

---

## 2. 何が穴だったか (現物)

旧 `_gate_check_core` (base `1042a1bc9` の 487〜505 行) の v2 枝:

```python
            active = (launch_validated.ratified
                      if launch_validated is not None else ratified)
            error = ratified_error
            if active is None and error is None:
                # 単体 gate CLI 経路: 自身で active 世代を解決する。
                try:
                    active = s8b_ratified_freeze.load_ratified_freeze(root)
                ...
            if error is not None:
                refusals.append(f"freeze-ratify: {error}")
            elif active is None or freeze_sha is None or freeze_sha != active.sha256:
                refusals.append("freeze-not-active-generation: ...")
```

`gate_check` (public) は正常経路では `load_ratified_freeze` → `launch_validate` を厳密 1 回通してから core へ入るが、初回の
`_load_verified_freeze` (旧 615 行) が失敗すると `verified` 無しで core へ入り (旧 619 行)、core は同じ path を再読 (旧 458 行)
する。再読が v2 として成功すると上の枝に入り、**launch validation を通さないまま sha256 一致だけで gate predicates へ進む**。
D65 決定 (5) 「public gate_check は v2 で必ず自己検証」がこの枝で成立していなかった (D1831 決定 2 が到達条件を併記して
記録、D1872 が「gate が 2 通りの意味を持つ状態は正しさゲートの穴 (規律 2)」として廃止を裁定)。

adapter 発火時 (`_t080_adapter_refusals` が non-None) の経路は v2 枝を飛ばすが、発火条件 `freeze_sha256 == receipt["artifacts"]["holdout"]["raw_sha256"]`
の右辺は `verify_receipt` が定数 `HOLDOUT_RAW_SHA256` (`t080_freeze_migration.py:48`、現行 v1 freeze `output/s8b-freeze/holdout_freeze.json` の
sha256 `315b1eb83d6fbdc525448c3c96c66ab6013df72487f35d8fa519c27ba34bc688`、floor/budget とも null) に固定しているので、v2 freeze は adapter
分岐に入れない (親の読解、段 3 / 段 6 の両レンズが現物で裏付け)。手作りの不整合 object まで含む保証には一般化しない。

## 3. 何をしたか (段 4 裁定の確定値)

- **P1 = core の freeze 再読は残す。** v1 と二読失敗の既存 refusal 集約に使われ、D1872 が名指すのは v2 の static self-load。
- **P2 = core の `ratified` 引数を削除** (call site 2 箇所も)。受理に寄与しない `RatifiedFreeze` の注入口を core に残すのは
  「2 通りの意味」の残骸。plan は保持を推奨したが (直接注入の負例のため)、その負例は public `gate_check(ratified=<合成>)` +
  二読 race に置き換えた (public API 越しの観測なので証拠力は上がる)。`gate_check` の public `ratified=` / `ratified_error=`
  は残す。
- **P3 = hash 一致の合成 `RatifiedFreeze` を返す fake。** AssertionError fake は旧 code も例外を捕捉して拒否するため受理境界の
  証拠にならない。
- v2 枝の順序: `ratified_error` → `freeze-ratify:` 翻訳 / `launch_validated is None` → 新 refusal / token 有り → 既存 sha256 照合。
  拒否理由の集約 (known-axes / floor-null / budget-null / manifest) は継続、early return は足さない (I1' — 段 3 レンズ B の
  B-9 と段 6 レンズ A の RA-1 で「必ず M」から「admission しない + error 優先 + 集約継続」へ限定)。
- 既存の exact type 検査 (非 None token の `type(x) is not LaunchValidatedFreeze`) は不変。

## 4. 受理集合の差分 (段 6 レンズ A の組合せ表、新 code)

adapter 非発火、receipt refusal 無し、manifest 無し。`M` = 新 refusal、`E` = `freeze-ratify:`、`X` = 型不正、`H` = `freeze-not-active-generation`、
`K` = known-axes、`F/B` = floor-null / budget-null。

| 選択 document | token | error 無し | error 有り |
|---|---|---|---|
| v1 | None / exact | v1 verifier、K、F、B → 拒否 | 同左 (core は E を追加しない) |
| v1 / v2 / None | subclass / Reverified | X で即拒否 | X で即拒否 |
| v2 | None | **M** + K + 該当 F/B → 拒否 (旧: static self-load の sha 一致で通過しえた) | E + K + 該当 F/B → 拒否 |
| v2 | exact | hash 非 None なら当該枝は通過。K・F/B 等が無ければ受理 | E + K + 該当 F/B → 拒否 |
| v2 | exact、hash None | H → 拒否 | E → 拒否 |
| None (再読も失敗) | None / exact | holdout 読取 refusal + known record 不在 + F + B → 拒否 | 同左 |

旧 → 新で allow に変わる組合せは無い (レンズ A、レンズ B とも refuted 0 件の受理拡大)。

## 5. 敵対相談・レビューの所見 (real / refuted)

- 段 3 (plan への 2 レンズ): sol 9 件 (real 6 / refuted 3)、luna 11 件 (real 5 / refuted 6)。must-fix 3 件はいずれも裁定・登録の
  文言と分類 (A-5 診断差の変異を KILL から分離、A-6 v1 不変性の正例、B-9 I1 文言) で、実装方向は不変。
- 段 6 (実装への 2 レンズ): sol 3 件 (real 2 / refuted 1)、luna 8 件 (real 2 / refuted 6)。**must-fix 0。** real は RA-1 (I1' の量化)、
  RA-2 (変異の完全集合: M6 は 4[budget-only] も、M8 は node 9 も赤)、RB-1 / RB-2 (docstring の精度) で、RB-1 / RB-2 を Codex fix
  (`cb64c51ed`、docstring のみ 7+/5−) で closed、RA-1 は本記録 §3 で限定、RA-2 は probe 走で完全集合を実測 (§6)。
- 棄却した主な所見: sha 比較を独立照合の証拠とする読み (A-1 / B-4、同一 object の自己比較)、adapter 経由の迂回 (A-4 / B-10、
  定数 pin)、負例が旧 code でも拒否される懸念 (B-5)、tmp root で exact 固定不能 (B-6)、既存 test file の編集必須 (B-11)。
- 段 6 fix 後の焦点再レビューは、fix が docstring 2 箇所 (コード行 0) だったため親の現物読解で代替した (RB-1 closed / RB-2 closed)。
- 段 3 レンズ A の A-8: D1984 (2026-09-14) の本文に「二読 fallback の択一は未裁定」と読める記述が残るが、D1872 (09-09) の後の
  不整合であり、[T-2067] 持ち越し本文 (entry 1527、09-16) と本依頼が D1872 を裁定済みとして扱う。本 wave はこれに従った。

## 6. 変異 matrix (事前登録 → probe → 本走)

事前登録は段 4 裁定 §5 (`verbatim/s4-ruling.md`)。逐語 anchor は最終 commit の現物から `build_mutation_spec.py` (job dir) が生成し、
anchor の一意性を検査した。probe 走 (container `cb64c51ed`、全件 SURVIVED 期待、`verbatim/mutation-spec-probe.json` / `mutation-probe-out.json`)
で観測 node の完全集合を採り、本走 spec (`verbatim/mutation-spec-final.json`、sha256 `44885645…`) に写した。観測集合は段 6 レンズ A
の静的予測 (RA-2 の訂正込み) と完全一致した。

本走 (container を `b625a1671` へ reset、`verbatim/mutation-final-out.json`、2026-09-17 02:20〜03:35 JST、runner = `tools/run_tests.py`
の焦点集合 = 新規 file 全 node + `test_s8b_oracle_driver.py` / `test_s1_known_axes_freeze.py` の gate 系 8 語、`--force-dispatch`):
baseline PASSED (110 秒)。`N::` = 新規 file、`T::` = `test_s8b_oracle_driver.py`。

| id | 変異 (最終 commit の位置) | 分類 | 結果 | 赤 node (完全集合) |
|---|---|---|---|---|
| M0 | v2 枝の comment 1 行を変える | 等価対照 | **SURVIVED** (期待どおり) | — |
| M1 | v2 枝に旧 code の static self-load + sha 一致受理を復活 | 受理境界 | **KILLED** | `N::test_public_reread_v2_requires_launch_validated`、`N::test_public_reread_v2_ignores_injected_ratified`、`N::test_cli_gate_check_transports_missing_token_refusal`、`N::test_core_v2_without_launch_validated_is_refused[both|floor-only|budget-only]` (6) |
| M2 | 非 None token の `type(x) is not` → `not isinstance` | 受理境界 | **KILLED** | `N::test_core_rejects_launch_validated_subclass` (1) |
| M3 | refusal `M` の append を `pass` に | 受理境界 | **KILLED** | M1 と同じ 6 node |
| M4 | core signature に `ratified` を復活 + call site 2 箇所 + v2 枝で `ratified.sha256 == freeze_sha` なら受理 | 受理境界 | **KILLED** | `N::test_public_reread_v2_ignores_injected_ratified`、`N::test_gate_core_signature_has_no_ratified_injection_port` (2) |
| M5 | token 有り枝の sha 条件 (`is None or !=`) を全削除 | 受理境界 | **KILLED** | `N::test_core_launch_validated_missing_hash_remains_refused` (1) |
| M6 | core の v2 判定 `floor is None and budget is None` → `floor is None` | 診断 pin | KILLED (別枠) | `N::test_core_v2_without_launch_validated_is_refused[budget-only]`、`N::test_core_exact_launch_validated_preserves_predicates[budget-only]` (2) |
| M7 | `ratified_error` 翻訳より `M` を優先 | 診断 pin | KILLED (別枠) | `N::test_public_ratified_load_errors_preserve_refusals[RatifiedFreezeError|RuntimeError]` (2) |
| M8 | `elif launch_validated is None or True:` (exact token があっても `M`、過剰拒否の対偶) | 受理境界 | **KILLED** | `N::test_core_exact_launch_validated_preserves_predicates[both|floor-only|budget-only]`、`N::test_core_launch_validated_missing_hash_remains_refused`、`T::test_gate_check_rebinds_each_injected_verified_manifest_axis[×4]` (8) |
| M9 | v1 枝の verify 後にも `M` を常時追加 | 診断 pin | KILLED (別枠) | `N::test_public_reread_v1_never_gets_missing_token_refusal` (1) |

- 受理境界の KILL は 6 件 (M1〜M5、M8)。M1 / M3 の片側 null fixture (`floor-only` / `budget-only`) は後段の null refusal が拒否を
  マスクするので、受理境界の証拠は `both` と public race の node から取る (レンズ A)。M8 は既存 `test_gate_check_rebinds_each_injected_verified_manifest_axis`
  4 node も赤にし、既存 consumer が過剰拒否を検出することを示した。
- 診断 pin 3 件 (M6 / M7 / M9) は拒否のまま reason・件数が変わる変異で、KILL 数に算入しない (DW-M03 / DW-M08)。
- 等価と判断して登録しなかった候補: token 有り枝の `!=` 比較だけの削除 (同一 object の自己比較)、未使用代入の増減。
- 所要は M3 / M4 / M6 / M8 が 15 分前後 (計算ノードの queue 待ち)、他は 1.5〜2 分。

## 7. 受入全走

- **post-1** (tip `cb64c51ed`、2026-09-17 01:33〜01:44 JST、計算ノード 3 shard): child **2 failed / 24401 passed / 67 skipped**。
  赤 2 件はどちらも本 wave 起因 (`verbatim/acceptance-post-1-red.md`):
  - `test_ccbench_spawn_sites.py::test_define_sink_cross_product_classifies_t2155_production_sinks_exactly` — `run_block` 内の
    `result = pipeline.evaluate(` (campaign build sink) の行番号 pin 1783 が本 wave の行シフトで 1775 へ移った。過去 wave も同 pin を
    追随更新している。
  - `test_plain_runner_coverage.py::test_every_test_file_is_self_runnable_or_allowlisted` — 新規 test file が `orchestrator/tests/README.md`
    の pytest 専用 allowlist に未登録。
  両方を Codex fix-2 (`b625a1671`、2 file 各 1 行) で閉じ、変更 test file の単独走 (計算ノード) 67 passed で確認した。
  wrapper 自体は `postrun-clean` rc=70 (受領証なし) — 親が走行中に `output/insights/` へ逐語 13 file を書いた untracked が原因 (F350 の再発として記録)。
- **final-1**: 記録 commit の tip で clean tree から投げる。結果は本 README には書かず (受入は記録の後)、land の受領証 (`acceptance-receipt-final-1.json`、job dir) と worklog が持つ。

## 8. 言ってよいこと・言ってはいけないこと

- 言ってよい: public `gate_check` は v2 freeze を full launch validation (`launch_validate` の exact token) を通らない限り受理しない。
  core は `RatifiedFreeze` を単独で受け取る口を持たない。
- 言ってはいけない: 「D1241 / D1313 の advisory / non-certifying 上限が動いた」(動かしていない)、「run-block 経路や library 経路
  (`verify_manifest` / `build_observations`) の選択強制が変わった」(触っていない)、「token 有り枝の sha 比較が requested path と
  active 世代の独立照合である」(同一 object の自己比較。独立照合は run-block の実 bytes 照合が担う)、「core 呼出の件数 (6 / 2 / 1) が
  権威ある閉包に由来する」(AST 走査)。

## 9. 一次資料

- 逐語: `verbatim/` (段 1 brief、既裁定逐語、段 2 plan、段 3 sol / luna、段 4 裁定、段 5 author、段 6 sol / luna / fix、変異 spec と結果)
- job dir (repo 外): `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2067-exact-launch-validated/` (prompt・log・receipt・受入 log)
