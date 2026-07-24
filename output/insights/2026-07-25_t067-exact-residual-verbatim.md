# [T-067] exact 化残余 — codex 逐語 (2026-07-25)

構成: codex exec, model=gpt-5.6-sol, sandbox=read-only(段2/3/6)/workspace-write(段5), cwd=worktree (基準 0c03609)。
reasoning: 段2/3/6=max(実効 xhigh)、段5=high。三軸語 conjunction 機械検査=clean。

---

## 段 2 — プラン起草 (read-only, xhigh)

静的解析のみの起草結果です。書込・commit・test 実行は行っていません。

結論は、同一 test file 内で 6 面を harden し、contract SHA の 1 面は意図的 partial のまま残す案です。production／凍結成果物／guard／calibration は変更対象に含めません。

## 1. store missing

- **loc**: `orchestrator/tests/test_s8b_oracle_driver.py:3543-3561`  
  `test_v2_store_missing_is_refused`、アンカー `assert _v2_refusal_reason(result) == "store-missing"`

- **現状**: `_v2_refusal_reason` (`:3093-3099`) が `status == "refused"`、件数 1、`v2-execution: [` prefix、角括弧内の code だけを固定する。`]` 以後の説明・store path・cell は未固定。

- **volatility 判定**: **hermetic**。生成元は `_build_v2_repo(tmp_path)` (`:3049-3070`)。production の文字列生成は `s8b_oracle_driver.py:824-829`。tail は次の形で、tmp path・PID・actual/expected SHA は出ない。

  ```text
  v2-execution: [store-missing] floor 計測 binary の store 実体が無い: <store_path> (cell=<tuple>)
  ```

  `<store_path>` は content-addressed SHA を含むが、実 working tree の揮発実測値ではなく fixture の `victim` record に束縛された値。literal SHA を焼かず `victim["store_path"]` から期待値を構成できる。

- **提案**: `_assert_exact_refusals`。`victim` 選択直後に次を導出し、旧 parser assert を置換する。

  ```python
  victim_cell = (victim["holdout_id"], victim["configuration_id"])
  assert result["status"] == "refused", result
  _assert_exact_refusals(result["refusals"], {
      "v2-execution: [store-missing] floor 計測 binary の store 実体が無い: "
      f"{victim['store_path']} (cell={victim_cell})",
  })
  ```

- **事前登録変異**:

  - refusal 末尾へ `" [unexpected-tail]"` を追加する件数保存変異。旧 parser は `"store-missing"` を返して通る。新 helper は **集合層のみ**で落ちる。
  - `cell=...` を別 tuple へ置換する件数保存変異。code は維持され旧 parser は通る。新 helper は **集合層のみ**で落ちる。

  旧 parser が既に `len == 1` を固定しているため、新 assertion だけが排他的に検出する件数層変異は存在しない。上記は `allowed=False` を変えない diagnostic sensitivity pin であり、dev-wave kill 集計外。

## 2. store hash mismatch

- **loc**: `orchestrator/tests/test_s8b_oracle_driver.py:3568-3585`  
  `test_v2_store_hash_mismatch_is_refused`、アンカー `== "store-hash-mismatch"`

- **現状**: 件数 1 と角括弧内 code だけを固定。説明・store path・cell は未固定。

- **volatility 判定**: **hermetic**。文字列生成は `s8b_oracle_driver.py:830-834`。実文字列は次の形。

  ```text
  v2-execution: [store-hash-mismatch] store binary sha256 が floor receipt と不一致: <store_path> (cell=<tuple>)
  ```

  actual/expected hash 値自体は診断へ出ない。

- **提案**: `_assert_exact_refusals`。missing と同じ `victim_cell` を使う。

  ```python
  assert result["status"] == "refused", result
  _assert_exact_refusals(result["refusals"], {
      "v2-execution: [store-hash-mismatch] "
      "store binary sha256 が floor receipt と不一致: "
      f"{victim['store_path']} (cell={victim_cell})",
  })
  ```

  2 テストを変換後、caller がなくなる `_v2_refusal_reason` (`:3093-3099`) は削除候補。

- **事前登録変異**:

  - refusal に余分な tail を追加する件数保存変異。**集合層のみ**。
  - store path を別の relative path に置換し、code と件数を維持する変異。**集合層のみ**。

  ここも旧 parser が件数を固定済みなので、排他的な件数層変異は登録しない。

## 3. contract SHA mismatch

- **loc**: `orchestrator/tests/test_s8b_oracle_driver.py:3592-3610`  
  `test_v2_contract_sha256_mismatch_is_refused`、アンカー `assert result["status"] == "refused", result`

- **現状**: status だけを固定し、件数・理由を全く固定しない。

- **volatility 判定**: **非決定（複数 catch 契約）**。ただし、同じ bytes に対する実行時ランダム分岐ではない。

  現 fixture は `run_contract.contract_sha256` と `manifest_id` だけを更新し、`campaign_config_preimages` を更新しない。このため現行コードでは `s8b_oracle_manifest.py:678-685` に決定的に捕捉され、静的導出される refusal は:

  ```text
  manifest-verify: ManifestError: campaign config preimage/hash が manifest 実行契約と不一致
  ```

  preimage も正しく再封した場合は manifest 検証を通り、`s8b_oracle_driver.py:766-769,1160-1164` の:

  ```text
  v2-execution: run_contract.contract_sha256 が env 契約 lookup 結果と不一致
  ```

  へ到達する。

- **提案**: **実装しない（裁定パッケージ候補）**。コメント `:3608-3609` は捕捉層を契約にしない意図を明示している。既知 2 理由を `_assert_exact_refusals` の expected set に同時指定すると「2 件とも出る」という誤契約になる。`_assert_refusal_reasons` も one-of を表現できない。

  将来この意図を変更するなら、同じ node 内で「stale preimage」と「preimage 再封済み」を別々に構成し、各結果を exact 化する案が適切。今回は対象外。

- **事前登録変異**: 実装しないため本 wave では登録なし。裁定材料として、将来 one-of assertion を導入する場合は次が分離可能。

  - 第三の未知理由への件数保存置換: **理由集合層のみ**。
  - 許容理由 1 件の重複: set/membership は不変、**件数層のみ**。

## 4. extime launch refusal helper

- **loc**: `orchestrator/tests/test_s8b_oracle_driver.py:3121-3127`  
  `_assert_extime_launch_refusal`。call site は `:3176` と `:3193`、test は `test_v2_standalone_gate_check_requires_full_floor_validation`。

- **現状**: `allowed=False`、件数 1、driver prefix、`protocol.extime_s`、受領値 3、承認値 5 を固定する。一方、構造化 reason code と全文同一性は未固定。

- **volatility 判定**: **hermetic**。`floor_extime_s=3` の tmp Git fixture。`s8b_floor_contract.py:95-100,188-190`、`s8b_ratified_freeze.py:2877-2886`、driver `:504-510` から静的導出される全文は:

  ```text
  v2-execution: launch-validate: [floor-artifact-invalid] [floor-artifact-invalid] floor protocol full validation 失敗: protocol.extime_s が承認凍結値と不一致 (受領 3 != 承認 5)
  ```

  tmp path・SHA・PID は含まれない。

- **提案**: helper 名と call site を維持し、内部を `_assert_exact_refusals` に置換する。

  ```python
  assert not decision.allowed
  _assert_exact_refusals(decision.refusals, {
      "v2-execution: launch-validate: "
      "[floor-artifact-invalid] [floor-artifact-invalid] "
      "floor protocol full validation 失敗: "
      "protocol.extime_s が承認凍結値と不一致 (受領 3 != 承認 5)",
  })
  ```

  P3 には反対。現 assertion は `[wrong-reason]` でも既存 substring を含めば通るため、構造化理由の誤翻訳を検出する追加価値がある。D73(9) の over-determination は変異帰属の問題であり、hermetic な全文期待値自体を避ける根拠にはならない。

- **事前登録変異**:

  - reason code を `[wrong-reason]` に置換し、prefix・`protocol.extime_s`・`受領 3`・`承認 5` を維持。旧 helper は通り、新 helper は **集合層のみ**で落ちる。
  - refusal 末尾へ余分な文言を追加。旧 helper は通り、新 helperは **集合層のみ**で落ちる。

  旧 helper が件数 1 を既に固定するため、排他的な件数層変異は登録しない。

## 5. PID 変動の既存 claim

- **loc**: `orchestrator/tests/test_s8b_oracle_driver.py:1572-1591`  
  `test_required_existing_claim_refuses_production_entry_without_new_side_effects`

- **現状**: `_assert_refusal_reasons` で件数 1 と PID 直前までを固定済み。

- **volatility 判定**: **非決定（PID）**。`s8b_oracle_driver.py:852-858` が `os.getpid()` を記録し、`campaign_claim.py:197-201` が所有 PID を本文へ埋める。

- **提案**: **実装しない（確認済み除外）**。現在の prefix:

  ```text
  v2-execution: G12 campaign claim 取得失敗: campaign claim は既に 
  ```

  は揮発部分の直前で正しく切れており、件数も固定している。full exact 化は D73(8)/(10) 違反。

- **事前登録変異**: 新 assertion がないため登録なし。

## 6. 漏れ: real-repo run_block refusal

- **loc**: `orchestrator/tests/test_s8b_oracle_driver.py:1454-1471`  
  `test_run_block_refusal_writes_no_campaign_or_budget_and_calls_nothing`、アンカー `:1469`

- **現状**: status、allowed、無副作用のみ。理由集合は未固定。D73 がいう「status-only 2 件」のもう 1 件。

- **volatility 判定**: **payload-volatile（厳密には real-repo state dependent）**。現 repository には live active pointer がなく、`s8b_ratified_freeze.py:1237-1240` と driver `:1043-1051` から現在の理由は:

  ```text
  freeze-ratify: [no-active] [no-active] live active pointer が無い (v2 未発効)
  ```

  実 repo の activation 状態に依存するため full literal より理由 code の prefix 固定が適切。

- **提案**: `_assert_refusal_reasons`。

  ```python
  _assert_refusal_reasons(result["refusals"], [
      "freeze-ratify: [no-active] ",
  ])
  ```

- **事前登録変異**:

  - 件数 1 のまま別 reason code へ置換。旧 assertion は通り、新 helper は **理由対応層のみ**で落ちる。
  - 同一 refusal を重複。旧 assertion は通り、新 helper は **件数層のみ**で落ちる。

## 7. 漏れ: subprocess claim race の loser

- **loc**: `orchestrator/tests/test_s8b_oracle_driver.py:1638-1748`  
  `test_two_real_subprocess_oracle_submissions_only_one_acquires_g12_claim`、アンカー `sorted(...status...) == ["claim-won", "refused"]`

- **現状**: loser が refused であることだけを固定し、`refusals` は未検査。

- **volatility 判定**: **非決定（PID）**。勝者は非決定で、loser の本文には勝者 PID が入る。ただし拒否理由の prefix と件数は一意。

- **提案**: refused result を status から選び、`_assert_refusal_reasons` を追加する。

  ```python
  refused = next(result for result in results if result["status"] == "refused")
  _assert_refusal_reasons(refused["refusals"], [
      "v2-execution: G12 campaign claim 取得失敗: "
      "campaign claim は既に ",
  ])
  ```

- **事前登録変異**:

  - 件数保存で別理由へ置換: **理由対応層のみ**。
  - PID 付き同一理由を重複: **件数層のみ**。

## 8. 漏れ: CLI rc=2 面

- **loc**: `orchestrator/tests/test_s8b_oracle_driver.py:2441-2467`  
  `test_cli_subprocess_returns_rc_2_on_gate_refused`、アンカー `assert proc.returncode == 2`

- **現状**: rc=2 と無副作用だけを固定。CLI が出力した JSON の status／refusals は未検査。

- **volatility 判定**: **payload-volatile（real-repo state dependent）**。現在は項 6 と同じ `no-active` 経路。

- **提案**: `proc.stdout` の JSON を読み、status と prefix 集合を固定する。

  ```python
  payload = json.loads(proc.stdout)
  assert payload["status"] == "refused", payload
  _assert_refusal_reasons(payload["refusals"], [
      "freeze-ratify: [no-active] ",
  ])
  ```

- **事前登録変異**:

  - refusal を別 reason code へ件数保存置換: **理由対応層のみ**。
  -同一 refusal を重複: **件数層のみ**。

## 漏れ列挙と除外結果

全 `refused`／`refusals` 参照を関数単位で確認した結果:

- 実装候補の漏れは `:1469`、`:1747`、`:2466` の 3 面。
- `:3610` は status-only だが、複数 catch 層を許す明示契約のため裁定候補として残す。
- `:424-427` の subprocess 内部分検査は、同じ fixture を親側 `:463` が `_assert_exact_refusals` で再検査しており、新しい排他的検出力がない。
- `:2250-2261` は件数 4、known reason 1 件の prefix、残り 3 件の完全一致を既に固定しており、working-tree SHA だけを意図的に外した compliant な mixed check。
- `:534-539`、`:648-651`、`:682-684` は T-080 migration receipt 自体の検査で、oracle `GateDecision`／run-block refusal 集合ではない。
- `binding-refused` event、`_exit_code("refused")`、production AST の status 分類は拒否理由集合の対象外。

## 不変条件・P# への裁定

- **P1**: 採用。ただし store path に content SHA は含まれる。literal を焼かず fixture の `victim` record から exact expected を構成する。
- **P2**: 一部反論。現 fixture の経路はランダムではなく manifest preimage mismatch に決定的。ただしテスト契約は捕捉層を意図的に非固定としているため、実装しない結論は維持。
- **P3**: 反対。extime exact 化には reason code 誤翻訳を検出する排他的価値があり、payload も揮発しない。
- **P4**: 確認。さらに subprocess race (`:1747`) も同じ PID prefix 除外が必要。
- node 名はすべて維持。特に変更候補の real-repo 3 node は `conftest.py:96,100-101` と `test_real_repo_serialization.py:68,72-73` に literal 固定されている。
- 全変異候補は refusal 診断だけを変え、`allowed=False`／受理集合を変えないため、すべて dev-wave kill ではなく diagnostic sensitivity pin。

---

## 段 3 レンズ A — 正しさ/volatility (read-only, xhigh)

結論は **プラン現状のまま NO-GO** です。store/extime の exact 化自体は成立しますが、store の共有 hash 前提と、項6/8の real-repo `no-active` 固定を修正すべきです。書込・commit・test 実行はしていません。

1. **[real] A3 — 項6/8の `freeze-ratify: [no-active]` 固定は activation による false-red を再導入する**

loc: [s8b_oracle_driver.py:1043 `load_ratified_freeze`](</home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-e2e-real-seal/orchestrator/campaign/s8b_oracle_driver.py:1043>)、[同:1074 requested freeze 照合](</home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-e2e-real-seal/orchestrator/campaign/s8b_oracle_driver.py:1074>)、[s8b_ratified_freeze.py:1237 `live` 解決](</home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-e2e-real-seal/orchestrator/campaign/s8b_ratified_freeze.py:1237>)、[test:1454](</home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-e2e-real-seal/orchestrator/tests/test_s8b_oracle_driver.py:1454>)、[test:2441](</home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-e2e-real-seal/orchestrator/tests/test_s8b_oracle_driver.py:2441>)

根拠:

- resolver は現在 `if not live: raise RatifiedFreezeError("no-active", ...)`。
- `run_block` は requested `REAL_FREEZE` を評価する前に `load_ratified_freeze(root)` を実行する。
- activation 後は `no-active` ではなく、launch validation の理由か、成功後の `freeze-not-active-generation` に進む。
- 項8の docstring は「real freeze の floor/budget null」と書くが、現在の実発火理由はその前段の `no-active`。prefix 追加はこの食い違いを契約化する。
- `no-active` 自体は [test:1751 `test_nonnull_floor_without_active_generation...`](</home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-e2e-real-seal/orchestrator/tests/test_s8b_oracle_driver.py:1751>) が既に明示的に exact characterization している。

影響: 正当な v2 activation で、副作用ゼロ契約と CLI rc=2 契約が維持されても項6/8が赤くなる。D73(8) 型の状態依存 false-red。

推奨: 項6は `status/allowed` に加えて `refusals` が非空であることまで。項8は stdout JSON を parse し、`status=="refused"`、`allowed is False`、`refusals` 非空を検査するが、`no-active` prefix は固定しない。reason identity が必要なら real repo ではなく、loader 失敗を固定した hermetic test を別途使う。

2. **[refuted] A1 — `victim` に cell field が無い／tuple repr が初回不一致、という親の懸念は誤り**

loc: [s8b_ratified_freeze.py:181 `_PORTABLE_BINARY_KEYS`](</home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-e2e-real-seal/orchestrator/campaign/s8b_ratified_freeze.py:181>)、[同:1624 `_validate_portable_binaries`](</home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-e2e-real-seal/orchestrator/campaign/s8b_ratified_freeze.py:1624>)、[同:3032 binaries equality](</home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-e2e-real-seal/orchestrator/campaign/s8b_ratified_freeze.py:3032>)、[driver:816](</home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-e2e-real-seal/orchestrator/campaign/s8b_oracle_driver.py:816>)

根拠:

- portable record の exact keys に `"holdout_id", "configuration_id", "store_path"` が必須。
- validator は `rec[key] != cell[key]` を拒否する。
- `result.binaries != manifest.binaries` も拒否される。
- driver は同じ文字列値から `cell = (row["holdout_id"], row["configuration_id"])` を作る。manifest validator も両 ID を非空 `str` に限定する。

影響: `victim_cell=(victim["holdout_id"], victim["configuration_id"])` の tuple repr は、現在の production 表示と厳密一致する。

推奨: rec の2 fieldを使う。親案の `cell_id.split("::")` は採らない。identifier 契約は `::` を禁止しておらず、split は新たな曖昧性を作る。

3. **[refuted] P1 — fixture は厳密な意味では hermetic ではない。ただし同一 checkout 内の store SHA は決定的**

loc: [test_s8b_ratified_freeze.py:422 `_prepare_emitter_base`](</home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-e2e-real-seal/orchestrator/tests/test_s8b_ratified_freeze.py:422>)、[同:343 fake build](</home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-e2e-real-seal/orchestrator/tests/test_s8b_ratified_freeze.py:343>)、[s8b_floor_campaign.py:1759 `store_binaries`](</home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-e2e-real-seal/orchestrator/campaign/s8b_floor_campaign.py:1759>)、[同:1153 portable `store_path`](</home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-e2e-real-seal/orchestrator/campaign/s8b_floor_campaign.py:1153>)

根拠:

- fixture は `_REAL_V1.read_bytes()`、実 calibration、known-axes、selector source を現 repo からコピーする。
- binary bytes は `fixture-binary::{genome.canonical()}::{src_token}` の UTF-8。tmp path、PID、時刻は含まれない。
- store は `store_root / sha`。PID は一時名 `.{sha}.tmp.{pid}` にしか入らず、最終 `store_path` は `out_root` 相対へ変換される。

影響:

- 同一 checkout の再実行・xdist・対応 POSIX platform では決定的。
- real freeze の binding entry を正当に編集すると entry token、binary SHA、store path は変わり得る。したがって「固定 SHA の hermetic fixture」ではなく「repo-seeded deterministic fixture」。
- 提案は SHA を literal 化せず `victim["store_path"]` から組むため、その変化自体では false-red しない。

推奨: dynamic な exact を維持し、SHA literal は焼かない。

4. **[real] A1 — content-address 共有時には `victim_cell` が報告 cell と一致しない隠れ前提がある**

loc: [s8b_floor_campaign.py:1769](</home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-e2e-real-seal/orchestrator/campaign/s8b_floor_campaign.py:1769>)、[holdout_freeze.json:268](</home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-e2e-real-seal/output/s8b-freeze/holdout_freeze.json:268>)、[同:550](</home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-e2e-real-seal/output/s8b-freeze/holdout_freeze.json:550>)、[test:3553](</home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-e2e-real-seal/orchestrator/tests/test_s8b_oracle_driver.py:3553>)

根拠:

- store は `dest = store_root / sha` であり、同一内容の複数 cell は同じ実体を共有する設計。
- 現 freeze でも rr20/rr80 の `stock_common` entry は同一。静的な canonical preimage 計算では両者が同一 store SHAになった。
- 現在の `next(iter(binaries.values()))` は、sorted result mapping の先頭 `rr20::backoff_fixed_best` で、この cell は一意 SHA。したがって初回失敗はしない。
- しかし共有 path を victim に選ぶと、driver は schedule 上で最初にその pathへ遭遇した cellを表示するため、選択した `victim_cell` と一致する保証がない。

影響: 正当な fixture entry/order 変更で、production が正しく共有 store 欠落を報告しても exact が赤くなる。

推奨: exact は採用してよいが、期待 cell は「block schedule 上、victim store_path を参照する最初の cell」から導出する。簡略化するなら store_path が一意な victim を選び、その一意性を明示 assert する。

5. **[real] A2 — 二重 `[floor-artifact-invalid]` は実在し、同一 reason の二重レンダリングである**

loc: [s8b_floor_contract.py:95 `_pinned`](</home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-e2e-real-seal/orchestrator/campaign/s8b_floor_contract.py:95>)、[同:188 extime](</home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-e2e-real-seal/orchestrator/campaign/s8b_floor_contract.py:188>)、[s8b_ratified_freeze.py:269 exception renderer](</home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-e2e-real-seal/orchestrator/campaign/s8b_ratified_freeze.py:269>)、[同:2877 wrapper](</home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-e2e-real-seal/orchestrator/campaign/s8b_ratified_freeze.py:2877>)、[driver:504](</home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-e2e-real-seal/orchestrator/campaign/s8b_oracle_driver.py:504>)

根拠:

- `_pinned` は tag なしの detail を生成。
- wrapper が `RatifiedFreezeError("floor-artifact-invalid", detail)` にする。
- `RatifiedFreezeError.__init__` 自身が `"[{reason}] {detail}"` を文字列化。
- driver がさらに `f"[{exc.reason}] {exc}"` を付ける。

したがって静的に導出される全文は提案どおりです。

```text
v2-execution: launch-validate: [floor-artifact-invalid] [floor-artifact-invalid] floor protocol full validation 失敗: protocol.extime_s が承認凍結値と不一致 (受領 3 != 承認 5)
```

影響: 二重 tag は別々の意味を持つ二層タグではなく、同じ `exc.reason` の冗長表示で、production 欠陥候補。exact は将来の重複除去で赤くなる。

推奨: 現 T-067 の「観測文字列を exact contract にする」という目的には exact が正しい。二重 tag 解消は別 production task として扱い、その修正時に期待値も同時更新する。なお [test:3502](</home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-e2e-real-seal/orchestrator/tests/test_s8b_oracle_driver.py:3502>) が既に別 reason の二重 tag を exact pin しており、extime exact が初めて欠陥を固定するわけではない。

6. **[refuted] P3/A4 — extime/store の正当な文言変更による赤は D73(8) の「無関係な編集」ではない**

loc: [D73(8) decisions.md:2905](</home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-e2e-real-seal/docs/decisions.md:2905>)、[extime helper test:3121](</home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-e2e-real-seal/orchestrator/tests/test_s8b_oracle_driver.py:3121>)

根拠:

- D73(8) が禁止したのは、実 working-tree SHAのように「別 doc の正当編集」で変わる payload。
- store path は record から動的導出するため、SHA変化を焼かない。
- extime の `3` は明示 fixture、`5` は承認 authority。変更時は正例・負例 fixture自体の更新が必要。
- 既存 helper は `protocol.extime_s`、`受領 3`、`承認 5` があれば、構造化 reason が別物でも通す。exact には排他的な追加検出力がある。
- error wording変更や二重 tag修正は、拒否診断そのものへの関連編集であり、赤は契約更新要求として正当。

影響: P3の「volatility のため full exact は over-determination」という理由は成立しない。ただし人間向け detail を契約扱いしない方針なら、T-067 の exact 方針そのものを再裁定する必要がある。

推奨: store は共有-path対策後に exact、extime も exact。文言リワード許容のため prefix に後退させない。

7. **[real] P4 — PID prefix の意図的 partial は正しい**

loc: [driver:842 `_execution_identity`](</home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-e2e-real-seal/orchestrator/campaign/s8b_oracle_driver.py:842>)、[campaign_claim.py:197](</home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-e2e-real-seal/orchestrator/campaign/campaign_claim.py:197>)、[test:1587](</home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-e2e-real-seal/orchestrator/tests/test_s8b_oracle_driver.py:1587>)

根拠: identity は `os.getpid()`、衝突 detail は `campaign claim は既に {existing.pid} が所有している`。現 prefix は数値直前で止まる。

影響: full exact は単独走／xdist／subprocess で false-red。

推奨: 現状の prefix のまま触らない。

最終裁定:

- store-missing / hash-mismatch: **exact 採用。ただし共有 store を考慮して expected cell を schedule から導出**
- extime: **exact 採用。二重 tag は production debtとして明記**
- real-repo run_block 項6: **`no-active` prefix は実装しない**
- CLI 項8: **stdout JSON parse は採用、`no-active` prefix は実装しない**
- PID: **prefix 維持**

---

## 段 3 レンズ B — 整合/完全性/over-det (read-only, xhigh)

結論は **NO-GO**。主な問題は、項3が wrong-layer masking を残すこと、項6/8で揮発しない理由に prefix helper を使うこと、項7の競合理由が単一 prefix に決定できないことです。

1. **[real] B2 — 項3の「実装しない」は T-067 の負債を温存する**

   loc: [test_s8b_oracle_driver.py:3592](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-e2e-real-seal/orchestrator/tests/test_s8b_oracle_driver.py:3592), [s8b_oracle_manifest.py:678](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-e2e-real-seal/orchestrator/campaign/s8b_oracle_manifest.py:678), [s8b_oracle_driver.py:1102](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-e2e-real-seal/orchestrator/campaign/s8b_oracle_driver.py:1102)

   根拠:

   - テストは `run_contract.contract_sha256` と `manifest_id` だけを更新し、`campaign_config_preimages` は更新していない。
   - manifest verifier は `value != expected` なら必ず `"campaign config preimage/hash が manifest 実行契約と不一致"` を送出する。
   - 検査順も preimage 検査が `manifest_id` 照合より先。
   - 最初の `verify_manifest` 例外は握り潰されるが、`verified_manifest=None` が `_gate_check_core` に渡り、[s8b_oracle_driver.py:428](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-e2e-real-seal/orchestrator/campaign/s8b_oracle_driver.py:428) で再検証される。現在の singleton reason は決定的に次になる。

   ```text
   manifest-verify: ManifestError: campaign config preimage/hash が manifest 実行契約と不一致
   ```

   一方、テストの docstring は「env 契約 lookup 結果との不一致」を対象と明記し、実際の env guard は [s8b_oracle_driver.py:766](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-e2e-real-seal/orchestrator/campaign/s8b_oracle_driver.py:766) にあるが到達不能。既存 insight 自身もこれを「wrong-layer refusal でも緑になる masking」と記録している（[insight:735](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-e2e-real-seal/output/insights/2026-07-21_t067-exact-refusal-and-s1-repackage.md:735)）。

   影響: status-only のままなら、テスト名と異なる前段 gate で落ちても永久に緑。これは T-067 が除去するはずの masking そのもの。

   推奨: `campaign_config_preimages` を変更後の契約から今ここで再封し、env guard まで到達させ、次を `_assert_exact_refusals` で固定する。

   ```text
   v2-execution: run_contract.contract_sha256 が env 契約 lookup 結果と不一致
   ```

   現在の manifest reason を exact pin する案は「実装しない」より良いが、wrong layer を仕様化してしまう。manifest seal のテストにするなら別テストとして明示すべき。「二経路のどちらでもよい」が本当に契約なら singleton + exact one-of を直接書けるため、helper が one-of 非対応なのは省略理由にならない。

2. **[refuted] B1 — store 2件の exact 化は単なる churn ではない**

   loc: [test_s8b_oracle_driver.py:3093](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-e2e-real-seal/orchestrator/tests/test_s8b_oracle_driver.py:3093), [s8b_oracle_driver.py:824](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-e2e-real-seal/orchestrator/campaign/s8b_oracle_driver.py:824)

   根拠: 旧 parser は

   > `return refusal[len(prefix):].split("]", 1)[0]`

   で `]` 以後を完全に捨てる。production は store path と `(cell=...)` を理由へ載せる。victim record から期待値を組み立てるなら、path 値を hard-code せず「実際に壊した victim と診断の帰属が一致するか」を検査できる。

   影響: exact 化は件数検出を増やさないが、誤った store path、誤 cell、説明の欠落・破損を新たに検出する。規律3の診断帰属 pin として実効価値がある。ただし `allowed` は変わらないため kill ではなく diagnostic sensitivity のまま。

   推奨: victim 構成の `_assert_exact_refusals` を採用する。code だけの `_assert_refusal_reasons` は旧 parser とほぼ等価で負債返済にならない。prose まで含む prefix でも wrong-victim を見逃す。

3. **[real] 項1/2の変換後は `_v2_refusal_reason` を削除しないと残骸になる**

   loc: [test_s8b_oracle_driver.py:3093](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-e2e-real-seal/orchestrator/tests/test_s8b_oracle_driver.py:3093), calls [3561](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-e2e-real-seal/orchestrator/tests/test_s8b_oracle_driver.py:3561), [3585](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-e2e-real-seal/orchestrator/tests/test_s8b_oracle_driver.py:3585)

   根拠: 定義以外の caller はこの2件だけ。

   影響: 呼出しだけ置換すると、T-067 が問題視した partial parser が未使用のまま残り、将来再利用され得る。

   推奨: 2 caller の変換と同時に helper 自体を削除することをプランへ明記する。

4. **[refuted] B4/P3 — extime exact 化は over-determination ではない**

   loc: [test_s8b_oracle_driver.py:3121](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-e2e-real-seal/orchestrator/tests/test_s8b_oracle_driver.py:3121), [s8b_oracle_driver.py:504](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-e2e-real-seal/orchestrator/campaign/s8b_oracle_driver.py:504), [s8b_ratified_freeze.py:2883](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-e2e-real-seal/orchestrator/campaign/s8b_ratified_freeze.py:2883)

   根拠: 現 helper は件数、`launch-validate:`、`protocol.extime_s`、値だけを検査し、`[floor-artifact-invalid]` の reason code と余分な suffix を検査しない。driver wrapper の `[{exc.reason}]` を `[wrong-reason]` に置換すれば、件数は1のまま、旧 helper は緑、新 exact 集合層だけが赤になる。

   影響: exact 化には独立した排他価値がある。

   推奨: `_assert_exact_refusals` 化する。変異 anchor は driver の wrapper 側 `[{exc.reason}]` と明記すること。ratified verifier 本体の共通 reason code を変える変異は他テストも赤くし、当該強化への帰属にならない。

5. **[real] 項6/8の no-active reason に prefix helper を使う理由がない**

   loc: [s8b_oracle_driver.py:1043](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-e2e-real-seal/orchestrator/campaign/s8b_oracle_driver.py:1043), [s8b_ratified_freeze.py:1237](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-e2e-real-seal/orchestrator/campaign/s8b_ratified_freeze.py:1237), existing exact pins [test:1771](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-e2e-real-seal/orchestrator/tests/test_s8b_oracle_driver.py:1771), [test:1801](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-e2e-real-seal/orchestrator/tests/test_s8b_oracle_driver.py:1801)

   根拠: reason は literal の

   ```text
   freeze-ratify: [no-active] [no-active] live active pointer が無い (v2 未発効)
   ```

   で、SHA、path、PIDなどの揮発 payload を含まない。同じ `ROOT` 経路を既存2テストが既に全文 exact 固定している。

   影響: `"freeze-ratify: [no-active] "` だけの prefix は、後半破損や不正 suffix を通す。D73(8)の「揮発 payload を焼かない」を、単に「real repo は全部 prefix」と誤適用している。

   推奨: 項6とCLI項8は `_assert_exact_refusals` を使う。必要なら `_NO_ACTIVE_REFUSAL` 定数へまとめる。

6. **[real] B4 — 項6の duplicate 変異は現プランの helper では件数層単独にならない**

   loc: [_assert_refusal_reasons:106](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-e2e-real-seal/orchestrator/tests/test_s8b_oracle_driver.py:106)

   根拠: duplicate `[x, x]` に対し、`len` を除去しても1件目が prefix を `remaining` から削除し、2件目は `match=[]` となって line 110 で赤になる。したがって duplicate は件数層と1:1理由対応層の双方に歯が当たる。

   さらに natural production anchor の no-active return を変えると、既存の exact テスト [1771](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-e2e-real-seal/orchestrator/tests/test_s8b_oracle_driver.py:1771) と [1801](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-e2e-real-seal/orchestrator/tests/test_s8b_oracle_driver.py:1801) が既に検出する。新 assertion 固有の sensitivity とも言えない。

   影響: D73(9)の単一層性にも、DW-M08の「新テストだけが検出」にも違反する。

   推奨:

   - 項6を exact helper に変えれば duplicate は `set` が重複を潰すため件数層だけになる。
   - それでも sibling 既存テストが検出するため、新規検出力としては数えず「当該 node の契約完備」と記録する。
   - CLI項8で新規検出力を示すなら、reason generator ではなく「CLI JSONから refusals を欠落・置換する」transport-layer 変異へ照準する。

   一方、store の「同一要素内 tail 追加」「cell 表示置換」と extime wrapper の reason 置換は、要素数を維持する限り集合層だけなので妥当。`refusals.append(...)` と混同しないよう変異逐語を固定すべき。

7. **[real] 項7の claim loser reason は単一 prefix に決定できない**

   loc: [test_s8b_oracle_driver.py:1729](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-e2e-real-seal/orchestrator/tests/test_s8b_oracle_driver.py:1729), [campaign_claim.py:153](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-e2e-real-seal/orchestrator/campaign/campaign_claim.py:153), [campaign_claim.py:195](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-e2e-real-seal/orchestrator/campaign/campaign_claim.py:195)

   根拠: production コメント自身が

   > `O_EXCL の directory entry は winner の write より先に見える`

   と認め、loser は1ms×50回だけ既存 record を再読する。winner が open 後に50ms超 deschedule/fsync 遅延すれば、`campaign claim は既に <PID>` ではなく「既存 claim record を構造化して読めない」等が再送出され得る。

   影響: status は正しく `refused` でも、提案 prefix が CI 負荷依存で false red になる。PIDだけが揮発するという前提は不十分。

   推奨: winner の claim record が完全に書かれたことを IPC/barrier で確認してから loser を衝突させ、その後 prefixまたは claim recordから構成した exact reasonを検査する。真の同時競合を維持するなら、singleton + 許容される exact reason class の one-of にする。現 fixtureのまま単一 prefixを強制しない。

8. **[refuted] B3 — 既知残余以外の追加漏れは1469・1747・2466の3件で尽きる**

   全参照を関数単位で再スイープした結果、top-level gate refusal を status/rcだけで終えている node は次の4件。そのうち3610は既に項3なので、追加漏れは指定の3件だけ。

   | node | 未 pin 箇所 |
   |---|---:|
   | `test_run_block_refusal_writes_no_campaign_or_budget_and_calls_nothing` | [1469](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-e2e-real-seal/orchestrator/tests/test_s8b_oracle_driver.py:1469) |
   | `test_two_real_subprocess_oracle_submissions_only_one_acquires_g12_claim` | [1747](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-e2e-real-seal/orchestrator/tests/test_s8b_oracle_driver.py:1747) |
   | `test_cli_subprocess_returns_rc_2_on_gate_refused` | [2466](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-e2e-real-seal/orchestrator/tests/test_s8b_oracle_driver.py:2466) |
   | `test_v2_contract_sha256_mismatch_is_refused` | [3610](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-e2e-real-seal/orchestrator/tests/test_s8b_oracle_driver.py:3610) |

   既知 partial は extime、store 2件、PID prefixだけ。その他の rejection fixture は exact/list equality または理由+件数を既に pin している。

   除外判断も妥当:

   - [424–427](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-e2e-real-seal/orchestrator/tests/test_s8b_oracle_driver.py:424) は同じ生成 repo を親テストの [463](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-e2e-real-seal/orchestrator/tests/test_s8b_oracle_driver.py:463) が exact 再検査する。
   - [2250–2261](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-e2e-real-seal/orchestrator/tests/test_s8b_oracle_driver.py:2250) は総数4、known prefix 1件、残り3件の exact set を固定している。
   - [534–539](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-e2e-real-seal/orchestrator/tests/test_s8b_oracle_driver.py:534) と [648–651](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-e2e-real-seal/orchestrator/tests/test_s8b_oracle_driver.py:648) は T-080 verifier の `ReceiptResolution` で、かつ件数1と `[expected_reason]` を固定済み。[682–684](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-e2e-real-seal/orchestrator/tests/test_s8b_oracle_driver.py:682) は refusal list ではなく `MigrationError` JSON。
   - `_assert_required_refusal_has_zero_side_effects` は status-only helperだが、全4 callerが直後に exact refusal 検査を行う。
   - ASTの `"refused"`、`_exit_code("refused")`、row-level `binding-refused`、`protocol_violation` は refusal集合を生成・観測するfixtureではない。

9. **[refuted] B5 — node名維持の前提は確認できた**

   loc: [conftest.py:96](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-e2e-real-seal/orchestrator/tests/conftest.py:96), [conftest.py:100](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-e2e-real-seal/orchestrator/tests/conftest.py:100), [test_real_repo_serialization.py:68](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-e2e-real-seal/orchestrator/tests/test_real_repo_serialization.py:68)

   2面に literal 固定される3 nodeは以下で一致する。

   - `test_run_block_refusal_writes_no_campaign_or_budget_and_calls_nothing`
   - `test_cli_subprocess_returns_rc_2_on_gate_refused`
   - `test_v2_standalone_gate_check_requires_full_floor_validation`

   提案は assertion/helper 本文だけの変更で、def 名を変える必要はない。claim race nodeはこの golden集合には含まれない。

10. **[refuted] 単一実装子・1ファイル所有という分割自体には問題なし**

    B2のpreimage再封、helper削除、全assertion修正を含めても編集は `test_s8b_oracle_driver.py` 内で閉じる。golden 2面はnode名を維持すれば変更不要。したがって所有衝突回避として単一実装子は妥当。ただし、単一所有は誤った変異帰属や競合fixtureの非決定性を解消しない。

静的解析のみで、書込・commit・test実行は行っていません。

---

## 段 5 — 実装 (workspace-write, high)

実装完了です。変更は [test_s8b_oracle_driver.py](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-e2e-real-seal/orchestrator/tests/test_s8b_oracle_driver.py:66) のみで、commit は作成していません。

項3は Level 2 を採用しました。manifest の `campaign_config_preimages` と `manifest_id` を再封して env-guard まで到達し、実 refusal は次でした。

`v2-execution: run_contract.contract_sha256 が env 契約 lookup 結果と不一致`

項4の二重 tag、項6/8の no-active も実走で確認済みです。

- 項4: `v2-execution: launch-validate: [floor-artifact-invalid] [floor-artifact-invalid] floor protocol full validation 失敗: protocol.extime_s が承認凍結値と不一致 (受領 3 != 承認 5)`
- 項6/8: `freeze-ratify: [no-active] [no-active] live active pointer が無い (v2 未発効)`

実行結果:

- 以下9 node: `9 passed in 84.70s`

  - `test_run_block_refusal_writes_no_campaign_or_budget_and_calls_nothing`
  - `test_two_real_subprocess_oracle_submissions_only_one_acquires_g12_claim`
  - `test_nonnull_floor_without_active_generation_is_refused`
  - `test_active_resolution_and_manifest_structure_refusals_are_aggregated`
  - `test_cli_subprocess_returns_rc_2_on_gate_refused`
  - `test_v2_standalone_gate_check_requires_full_floor_validation`
  - `test_v2_store_missing_is_refused`
  - `test_v2_store_hash_mismatch_is_refused`
  - `test_v2_contract_sha256_mismatch_is_refused`

- emitter `src_token` を実行時に変更し、binary SHA/store path を変化させた再検証: store 2 nodeとも緑、`2 passed`
- golden consumer `test_real_repo_group_collection_exactly_matches_canonical_nodes`: 緑
- `py_compile`、`git diff --check`、`check_codex_agents.py`、`check_docs.py`: 緑
- submodule/real-repo 起因の赤なし

最初の既定 `pytest` は Python 3.9 のため collection 時に `dataclass(kw_only=...)` で1エラーになりました。対応する Python 3.10 で上記全検査を再実行しています。

所有外への波及確認:

- `_NO_ACTIVE_REFUSAL` は項6/8と既存no-active 2 testの計4箇所を集約。
- store victim helperは項1/2だけで共有。
- extime helperの既存2 call siteは維持。
- `conftest.py:96,100-101`、`test_real_repo_serialization.py:68,72-73` のliteral node名はすべて不変。
- production、他テスト、docsは未変更。既存の未追跡handoffも触れていません。

受理集合（allowed/refused/tie）は変更しておらず、全変更は診断アサーション強化のみです。

---

## 段 6 レビュー X — 正しさ/弱体化/項3 (read-only, xhigh)

判定: **ブロッキングな [real] 所見はありません。項3は Level 2 sound、F27 弱体化もなし。GO** です。既知の二重 tag は非ブロッキングな production 診断欠陥として残ります。静的解析のみで、test は実行していません。

1. **[refuted] 項3が manifest-preimage 層を検査するだけ／恒真である懸念**  
   loc: [test_s8b_oracle_driver.py:3616](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-e2e-real-seal/orchestrator/tests/test_s8b_oracle_driver.py:3616), [s8b_oracle_manifest.py:377](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-e2e-real-seal/orchestrator/campaign/s8b_oracle_manifest.py:377), [s8b_oracle_driver.py:747](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-e2e-real-seal/orchestrator/campaign/s8b_oracle_driver.py:747)  
   **根拠:** manifest verifier は contract hash を「`ここでは形式のみ 64hex 検査`」し、preimage は `run_contract` から `_campaign_config_preimages(...)` で再計算、最後に `manifest_id` を再計算します。test はその二つを双方再封しているため、`s8b_oracle_manifest.py:678-685,898-901` を通る構成です。その後 `config_for_block` は manifest の `run_contract` をそのまま渡しますが、driver の比較相手は独立 registry の `contract = _env_contract.lookup(env_tag)` であり、`run_contract.get("contract_sha256") != contract.contract_sha256` が catcher です。期待全文の production 出現箇所も `s8b_oracle_driver.py:768` の一箇所だけなので、別 gate の refusal で偶然緑にはなりません。  
   **成果物影響:** この guard の退行を旧 masking が見逃すと、manifest/preimage の contract hash と execution receipt の registry hash が分裂した campaign を受理し得ます。現差分はそれを赤にします。  
   **推奨:** 現在の再封＋単一 exact reason を維持し、one-of refusal へ戻さない。

2. **[refuted] `_v2_refusal_reason` 置換による F27 弱体化**  
   loc: [test_s8b_oracle_driver.py:92](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-e2e-real-seal/orchestrator/tests/test_s8b_oracle_driver.py:92), [test_s8b_oracle_driver.py:3557](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-e2e-real-seal/orchestrator/tests/test_s8b_oracle_driver.py:3557)  
   **根拠:** 旧 helper (`HEAD:...:3093-3099`) は `len == 1` と `v2-execution: [` prefix の後の reason code だけを検査し、tail を捨てていました。新 helper は `len(actual) == len(expected)` と `set(actual) == expected`、各 store test はさらに `status == "refused"` と `allowed is False` を要求します。wrong path、wrong cell、tail 欠落、重複 refusal は旧検査を通れても新検査を通れません。extime と CLI の変更も部分一致／rc のみから全文＋payload 検査への強化です。  
   **成果物影響:** certified 選択の受理集合は不変ですが、誤った refusal report や CLI JSON が緑になる集合は狭まります。  
   **推奨:** 変更どおり exact を維持。

3. **[refuted] `_unique_store_victim` が victim 不在や共有 store を誤選択する懸念**  
   loc: [test_s8b_oracle_driver.py:3099](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-e2e-real-seal/orchestrator/tests/test_s8b_oracle_driver.py:3099), [s8b_ratified_freeze.py:1624](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-e2e-real-seal/orchestrator/campaign/s8b_ratified_freeze.py:1624)  
   **根拠:** 選択条件は各 record について `sum(candidate["store_path"] == rec["store_path"]) == 1`、不在時は `assert victims, binaries`、選択後にも同じ一意性を再検査しています。ratified validator は binaries の cell 集合を expected cells と exact 照合し、record の `holdout_id/configuration_id` も cell と一致させます。oracle schedule は全 holdout×configuration を含むため victim は必ず消費対象です。現 fixture では build payload が `genome + src_token` に依存し、rr20/rr80 の `BACKOFF_FIXED=10/2` などから一意 SHA/store も実在します。  
   **成果物影響:** production 成果物への影響なし。共有 store を選んだ場合に起きる schedule-first cell との test false-red を防いでいます。  
   **推奨:** helper を維持。`victims[0]` の選択順も期待値と mutation が同じ record を使うため問題ありません。

4. **[refuted] exact 文字列の誤り／D73(8) false-red**  
   loc: `test_s8b_oracle_driver.py:66-69,3135-3141,3575-3580,3604-3609,3642-3645`  
   **根拠:** 全期待値が production 組立てと一致します。

   - no-active: `RatifiedFreezeError("no-active", ...)` と driver の `freeze-ratify: [{exc.reason}] {exc}` の合成。
   - extime: floor validator の `受領 {value!r} != 承認 {expected!r}`、ratified wrapper、driver wrapper の合成。
   - store: `s8b_oracle_driver.py:827-834` の path/cell と `v2-execution:` prefix の合成。
   - contract: `s8b_oracle_driver.py:766-769` の固定文言と prefix の合成。

   Store の SHA/path/cell は literal 焼込みでなく `victim` から動的構成され、contract reason は実 hash を含みません。extime は test が明示した 3 と承認値 5、no-active にも PID・tmp path・hash はありません。  
   **成果物影響:** 無関係な source bytes の編集では赤になりません。診断文言や active-generation 状態の変更では赤になりますが、いずれも当該 gate 契約に直接関係する変更です。  
   **推奨:** exact を維持。

5. **[real・既知・非ブロッキング] reason tag の二重描画**  
   loc: [s8b_ratified_freeze.py:269](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-e2e-real-seal/orchestrator/campaign/s8b_ratified_freeze.py:269), [s8b_oracle_driver.py:504](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-e2e-real-seal/orchestrator/campaign/s8b_oracle_driver.py:504), `s8b_oracle_driver.py:1043-1046`  
   **根拠:** `RatifiedFreezeError.__init__` 自身が `"[{reason}] {detail}"` を生成し、driver がさらに `"[{exc.reason}] {exc}"` を付けます。したがって `[floor-artifact-invalid]` だけでなく `[no-active]` も二重です。test の期待値は現 production を正しく characterize しています。  
   **成果物影響:** `GateDecision.refusals` と CLI JSON の診断文字列だけが冗長になります。certified 選択・WAL の受理値は変わりません。  
   **推奨:** 本 test-only wave では exact pin を許容。別 production task で重複を除去し、同じ変更で期待値を更新する。その際の赤は D73(8) の false-red ではなく関連変更の検知です。

6. **[refuted] 受理集合を変更している懸念**  
   loc: 指定 diff 全体  
   **根拠:** tracked diff は test ファイルのみです。manifest 再封と store mutation は `tmp_path` fixture 内、race 部分はコメント追加のみ。production の allowed/refused/tie 判定コードには変更がありません。  
   **成果物影響:** runtime の certified 選択・report・台帳値は不変。test が受理する診断出力だけが厳密化されます。  
   **推奨:** 変更不要。

---

## 段 6 レビュー Y — 変異帰属/完全性 (read-only, xhigh)

結論: DW-G05 の must-fix は 0 件です。静的裁定は M1/M2/M3/M8＝排他的 diagnostic pin、M4＝実受理集合を変える kill、項6＝suite 全体の新規検出力なし／node 契約完備です。

- [refuted] 項1 store-missing exact は churn ではありません。  
  loc: [test:3577](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-e2e-real-seal/orchestrator/tests/test_s8b_oracle_driver.py:3577)、production anchor [driver:827](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-e2e-real-seal/orchestrator/campaign/s8b_oracle_driver.py:827)。old 逐語は `f"[store-missing] floor 計測 binary の store 実体が無い: "` + `f"{rec['store_path']} (cell={cell})"`。後者へ文字追加、または `cell` 表示だけを誤らせる件数保存変異なら、新 exact は赤、HEAD の `_v2_refusal_reason()` は先頭 reason code しか見ないため緑です。  
  成果物影響: refused/allowed は不変で、certified 選択・report・台帳は変わらないため diagnostic pin。  
  推奨: M1 を kill でなく DW-M08 diagnostic sensitivity として記録。

- [refuted] 項2 store-hash exact も同様に排他検出力があります。  
  loc: [test:3606](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-e2e-real-seal/orchestrator/tests/test_s8b_oracle_driver.py:3606)、production anchor [driver:832](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-e2e-real-seal/orchestrator/campaign/s8b_oracle_driver.py:832)。old 逐語は `f"[store-hash-mismatch] store binary sha256 が floor receipt と不一致: "` + `f"{rec['store_path']} (cell={cell})"`。tail/cell のみの変異で新 exact の set 層だけが赤、HEAD parser は緑です。  
  成果物影響: 診断文字列だけなので nit/diagnostic。  
  推奨: M2 も kill 集計外。

- [refuted] 項4 extime の正しい anchor は ratified verifier 本体ではなく driver wrapper です。  
  loc: [test:3137](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-e2e-real-seal/orchestrator/tests/test_s8b_oracle_driver.py:3137)、production anchor [driver:509](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-e2e-real-seal/orchestrator/campaign/s8b_oracle_driver.py:509)。old 逐語は `refusals=[f"v2-execution: launch-validate: [{exc.reason}] {exc}"],`。外側だけを `[wrong-reason]` にすると、HEAD helper の prefix・`protocol.extime_s`・受領/承認値検査は全て通り、新 exact だけ赤です。  
  [ratified verifier:2883](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-e2e-real-seal/orchestrator/campaign/s8b_ratified_freeze.py:2883) の共通 `"floor-artifact-invalid"` を変えると、既存 ratified tests の reason pin も多数赤くなり、T-067 への帰属になりません。  
  成果物影響: acceptance 不変の diagnostic pin。  
  推奨: M3 は wrapper anchor に固定。

- [real] 項3 env-guard no-op は mask されず、静的予測では `refused → completed/allowed=True` に反転します。  
  loc: fixture 再封 [test:3623](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-e2e-real-seal/orchestrator/tests/test_s8b_oracle_driver.py:3623)、production anchor [driver:766](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-e2e-real-seal/orchestrator/campaign/s8b_oracle_driver.py:766)。old 逐語は `if run_contract.get("contract_sha256") != contract.contract_sha256:`。これを `if False:` 相当にするのが M4 です。  
  HEAD 版は `campaign_config_preimages` を再計算しないため、[manifest verifier:681](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-e2e-real-seal/orchestrator/campaign/s8b_oracle_manifest.py:681) で先に拒否され、M4 下でも緑です。新 fixture は preimage と manifest ID を再封するので guard へ到達します。guard 後は receipt の [driver:790](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-e2e-real-seal/orchestrator/campaign/s8b_oracle_driver.py:790)、途中検査の [driver:933](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-e2e-real-seal/orchestrator/campaign/s8b_oracle_driver.py:933)、BuildResult の [driver:948](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-e2e-real-seal/orchestrator/campaign/s8b_oracle_driver.py:948) はいずれも lookup 済み `plan.contract` 同士を比較し、manifest の改変 SHA へ戻りません。fake evaluator も build_v2 を呼ばないため mask しません。  
  成果物影響: 不整合 manifest が実走を許可され、marker・WAL・budget/trial ledger を生成し得るため、DW-G05 上も実効 gate の kill。  
  推奨: 再照準不要。M4 を唯一の kill として維持。

- [real] ただし M4 を `_assert_exact_refusals` の排他 kill と記録するのは誤帰属です。  
  loc: [test:3642](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-e2e-real-seal/orchestrator/tests/test_s8b_oracle_driver.py:3642)。M4 では先行する `status/allowed` assert が最初に落ち、exact helper へ到達しません。kill を買ったのは「preimage 再封による実効 gate 到達」です。exact assertion 自体の排他変異は [driver:768](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-e2e-real-seal/orchestrator/campaign/s8b_oracle_driver.py:768) の old 逐語 `"run_contract.contract_sha256 が env 契約 lookup 結果と不一致"` を別文言へ置換する診断変異です。  
  成果物影響: mutation ledger の帰属精度だけで、DW-G05 成果物影響は書けないため nit。  
  推奨: M4＝fixture reachability/status kill、別変異＝exact reason diagnostic と分記。

- [real] 項6 run_block no-active は非排他的です。  
  loc: 新規 [test:1474](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-e2e-real-seal/orchestrator/tests/test_s8b_oracle_driver.py:1474)、既存 siblings [test:1777](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-e2e-real-seal/orchestrator/tests/test_s8b_oracle_driver.py:1777)、[test:1804](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-e2e-real-seal/orchestrator/tests/test_s8b_oracle_driver.py:1804)。production old anchor は [s8b_ratified_freeze.py:1240](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-e2e-real-seal/orchestrator/campaign/s8b_ratified_freeze.py:1240) の `raise RatifiedFreezeError("no-active", "live active pointer が無い (v2 未発効)")`。この reason/detail を壊すと変更前 HEAD の siblings も赤です。  
  成果物影響: suite 全体の検出力は増えず、DW-G05 影響なし。  
  推奨: mutation gain としては churn/0 件、実装分類はプランどおり「当該 node の契約完備」。kill/diagnostic matrix には加えない。

- [refuted] 項8 CLI exact には transport 固有の排他検出力があります。  
  loc: [test:2469](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-e2e-real-seal/orchestrator/tests/test_s8b_oracle_driver.py:2469)、production anchor [driver:1568](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-e2e-real-seal/orchestrator/campaign/s8b_oracle_driver.py:1568)。old 逐語は `print(json.dumps(result, ensure_ascii=False, sort_keys=True))`。これを `{**result, "refusals": []}` の JSON 出力へ置換すれば、[driver:1569](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-e2e-real-seal/orchestrator/campaign/s8b_oracle_driver.py:1569) の rc 射影は元の `result` を使うため rc=2 のままです。HEAD 版は緑、新 exact の refusals set 層だけ赤になります。  
  成果物影響: underlying acceptance/台帳は不変。stdout 診断 transport の pin なので kill ではない。  
  推奨: M8 を独立 diagnostic pin として採用。

- [refuted] プラン v2 の実装漏れ・やり過ぎはありません。  
  loc: store×2、contract、extime、run_block、CLI は上記の通り実装済み。項5 PID は [test:1592](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-e2e-real-seal/orchestrator/tests/test_s8b_oracle_driver.py:1592) の可変 PID 手前までの prefix を維持。項7 は [test:1752](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-e2e-real-seal/orchestrator/tests/test_s8b_oracle_driver.py:1752) の説明コメントだけです。`_v2_refusal_reason` は残存 caller ごと削除されています。  
  成果物影響: test-only 1 ファイルで production/凍結成果物への変更なし。  
  推奨: scope はこのまま維持。

- [refuted] 波及懸念。  
  `_NO_ACTIVE_REFUSAL` は旧 sibling の連結 literal と文字列同値です。`_unique_store_victim` の caller は [test:3567](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-e2e-real-seal/orchestrator/tests/test_s8b_oracle_driver.py:3567) と [test:3596](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-e2e-real-seal/orchestrator/tests/test_s8b_oracle_driver.py:3596) の2件だけです。ratified verifier は [s8b_ratified_freeze.py:1637](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-e2e-real-seal/orchestrator/campaign/s8b_ratified_freeze.py:1637) で record の cell fields を束縛するため、選んだ unique store と期待 cell は一致します。node 名は [conftest.py:96](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-e2e-real-seal/orchestrator/tests/conftest.py:96) と [test_real_repo_serialization.py:68](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-e2e-real-seal/orchestrator/tests/test_real_repo_serialization.py:68) の golden と不変です。  
  成果物影響: なし。  
  推奨: 追加変更不要。

- [real] CLI テストの docstring だけは実際の pin と不一致です。  
  loc: [test:2444](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-e2e-real-seal/orchestrator/tests/test_s8b_oracle_driver.py:2444)。`floor/budget null` と説明していますが、production は先に active generation を解決し、新 assertion は `no-active` を固定しています。  
  成果物影響: なし、nit。  
  推奨: docstring を「active generation 不在の refusal を CLI JSON/rc へ transport」に合わせる。

指定どおり、書込・commit・test 実行はしていません。