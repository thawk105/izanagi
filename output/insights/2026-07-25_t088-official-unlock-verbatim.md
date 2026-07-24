# [T-088] official mode 解禁 設計 wave — codex 逐語 (2026-07-25)

裁定・設計の正本は `2026-07-25_t088-official-unlock-design.md`。本ファイルは子の出力の逐語保存である
(failures F20: 相談全文を job tmp にだけ置かない)。

- 実行環境: `codex exec -m gpt-5.6-sol -c model_reasoning_effort="max" -s read-only`、
  `-C <worktree root>`。3 本とも exit 0。
- 子は read-only sandbox のため pytest を実行していない。**子の非実走を緑と記録しない** (DW-O05)。
- 親の裁定 (real/refuted・採否) は設計パッケージ §2 を正本とする。ここに書かれた子の主張は
  **裁定前の生の出力**であり、親が否定した主張も原文のまま残す。

収録:
1. 段 2 プラン起草 (`plan_out.md`)
2. 段 3 敵対相談 レンズ A = 正しさ境界・防壁の破れ (`consult_a_out.md`) — 判定 NO-GO
3. 段 3 敵対相談 レンズ B = 実在性・scope 肥大・[T-083] freeze 整合 (`consult_b_out.md`) — 判定 NO-GO

---

## 1. 段 2 プラン起草 (逐語)

## A. 現状認識の訂正

- `_assert_official_permitted` の位置・内容は記載どおり `orchestrator/campaign/s8b_floor_campaign.py:193-203`。ただし guard は裁定前の残骸ではなく、裁定後にも意図して残された dormant 防壁である。`output/insights/2026-07-24_e2e-real-seal.md:11-14` もこの訂正を明記する。したがって P2 は「文言は古いが、防壁自体は誤記ではない」と補正する。

- public wrapper の 13 seam 拒否は `s8b_floor_campaign.py:2648-2667`、guard 呼出しはその次の `:2668`。現行の二重拒否は「CLI + public wrapper」であり、private core は拒否しない (`:2682-2698`)。CLI コメント `:3434` の「core も二重に拒否」は厳密には誤記。

- `_verify_resume_journal` の official/pilot 非対称は `:3243` 一行ではなく、pilot `:3243-3253`、official `:3254-3328`。

- `docs/phase3.md:53` の「承認束縛の §8 裁定まで一律拒否」は、直後の裁定完了記録 `:54-60` と矛盾する。拒否理由は修正対象。

- `§8` は少なくとも `docs/phase3-8b-descriptor-design.md:255`、`docs/freeze-permanent-design.md:303`、`output/insights/2026-07-18_s8b-c22-consultations.md:709` で別義。`F6` も `docs/failures.md:63-64` と `output/insights/2026-07-16_s8b-floor-protocol-package.md:379-390` で衝突する。新しい診断文には使わない。

- 「official テストは `_official_test_seam` によりすべて clean scan stub」という記述は現行ツリーでは不正確。確かに helper は guard と scan を差し替える (`test_s8b_floor_campaign.py:612-620`) が、real-seal E2E は private core を直接呼び (`:3373-3382`)、production preflight、二重 clean scan、durable policy を spy 委譲で通す (`:3282-3339`, `:3384-3403`)。ただし build・throughput は fake (`:3355-3372`) で、物理 Pegasus attestation でもない (`:3005-3019`)。よって「guard 削除後の public production 経路を実測できていない」という親の限定は正しい。

- `test_run_campaign_core_rejects_official_with_zero_side_effects` は名前に反し、private core でなく public `run_campaign` を呼ぶ (`test_s8b_floor_campaign.py:1057-1071`)。

- official 解禁前 MUST は D79 `docs/decisions.md:3286-3287`。D80 で、未知 file/symlink/phantom 拒否、path→SHA を含む clean-scan digest v3、独立二回 scan、strict certificate 束縛まで実装済み (`:3337-3346`)。ここは新 gate から必ず再利用する。

- 落ちている実運用制約は PBS wrapper と実行 revision 束縛。現状の `ReservationBinding.script_sha256` は実在する (`orchestrator/campaign/reservation.py:27-54`) が、予約検査は形式・job/boot/time のみで、承認済み wrapper hash との比較がない (`:218-270`)。専用 floor wrapper 自体も未実装と明記される (`tools/pegasus/README.md:128-139`)。

## B. 解禁条件の設計 (中核)

推奨述語を次とする。

```text
PermitOfficial =
  DefaultProductionSurface
  ∧ VerifiedUpstreamBundle
  ∧ HumanLaunchAuthorization
  ∧ RuntimeLaunchPreflight
```

これは「拒否削除」ではなく、無条件拒否を四項の conjunction に置換する設計である。前二項と人間 receipt は副作用前、runtime 項は launch certificate 発行前までに fail-closed で検査する。

- **production surface が既定値であること。** `mode` は閉集合検査 (`s8b_floor_campaign.py:186-190`) を通り、official では既存 13 seam がすべて default (`:2648-2667`)。この順序は変えず、receipt の読取りより前に拒否する。

- **protocol 実成果物が正当であること。** 実在成果物は `output/s8b-freeze/floor_protocol.json:1`。`schema/formula/env_tag/ccbench_pin/freeze/contract_sha256` 等の exact 18 fields は `s8b_floor_contract.py:34-41`、full validation は `:104-226`、canonical SHA は `:229-241`。固定 path の実 bytes SHA との一致は既存 preflight `s8b_floor_campaign.py:1318-1353` を用いる。

- **v1 freeze bytes が protocol と trust root の双方へ一致すること。** `protocol.freeze.{path,sha256}` は `s8b_floor_contract.py:158-165`、実 bytes と定数・protocol の三者一致は `s8b_floor_campaign.py:1343-1349`。下流 active generation は要求しない。

- **prediction seal が完全検証済みであること。** 実在 field は `selector_predictions.json:2-33` の `schema_version/pre_oracle_head/sources/execution_policy` と、例えば agent row の `input_payload_sha256/raw_sha256/raw_response_path` (`:43-67`)。文書 schema/body/basis は `s8b_selector_freeze.py:667-703`、commit・source・raw 再 parse を含む full verifier は `:879-905`、floor preflight からの呼出しは `s8b_floor_campaign.py:1355-1372`。

- **journal・prediction・歴史 anchor が相互束縛されること。** 実 journal の header は `selector-runs/journal.jsonl:1`、claim/envelope/invocation/static records は `:2-15`。既存 preflight は `prediction.pre_oracle_head`、protocol blob、parser blob、header 5 fields を照合する (`s8b_floor_campaign.py:1374-1407`)。宣言 path と filesystem の双方向 exact/hash 検査は `s8b_prediction_runner.py:1298-1370`。

  ただし現行 `resolve_journal_for_launch` は header 5 fields と順序、claim の `decision_method` 等までで (`s8b_prediction_runner.py:552-660`)、claim payload SHA や invocation の全 row fields の直接一致までは強制しない。直接一致の既存実装は下流 helper `s8b_ratified_freeze.py:2455-2700`、特に claim `:2645-2653`、invocation `:2655-2677`、envelope `:2683-2699` にある。推奨案ではこの active-generation 非依存部分を中立 helper へ抽出し、上流 bundle 検証にも追加する。これは F の裁定事項とする。

- **人間の launch authorization があること。** downstream generation approval は流用せず、新規 receipt を設ける。

  推奨 path は `output/s8b-floor-authorizations/<artifact_bundle_sha256>.json`。`output/s8b-freeze` 内に置くと現在の有界 path 検査 (`s8b_floor_campaign.py:1493-1516`) で chain record 以外の未知 file になる (`:1560-1568`) ため、namespace を分ける。

  新規 exact schema は次とする。これは現状非実在の、意図的に新設する field である。

  ```text
  {
    schema,
    scope,                         // exact "s8b-floor-official-launch"
    authorization_basis_commit,    // H
    pre_oracle_head,
    artifacts: [{path, sha256}, ...],
    artifact_bundle_sha256,
    pbs_wrapper: {path, sha256},
    authorized_by,
    authorized_at
  }
  ```

  `artifacts` は `_floor_preflight_freeze_allowlist` が返す実在 path→SHA (`s8b_floor_campaign.py:1418-1452`) の canonical sorted 射影。`pre_oracle_head` は実 prediction field、wrapper SHA は runtime `ReservationBinding.script_sha256` と比較する。PBS wrapper は現在不存在なので、wrapper 実装・commit 後でなければ receipt を発行できず、述語も成立しない。

  receipt commit A は、唯一の親が `authorization_basis_commit=H`、差分が receipt 一個の追加だけ、100644 regular blob、`AI-Agent: none` 逐語、worktree/submodule clean、かつ実行時 `HEAD==A` を要求する。検証アルゴリズムの先例は T-080 の clean tree 検査 (`t080_freeze_migration.py:1356-1424`) と introduction topology (`:853-868`)。

- **実環境 gate が成立すること。** protocol の `env_tag/contract_sha256` は registry と一致 (`s8b_floor_contract.py:138-151`)。calibration・実機 attestation・execution receipt は `s8b_floor_campaign.py:2714-2747`、reservation は `:2771-2791`、durable root は `:2805-2811`、claim は `:2821-2854`。加えて `reservation_binding.script_sha256 == permit.pbs_wrapper.sha256` を claim より前に新設する。

- **D80 certificate gate が成立すること。** freeze allowlist の再計算、独立二回 clean scan、strict certificate は既存 `s8b_floor_campaign.py:1597-1639`, `:1693-1718` をそのまま必須化する。authorization receipt の path/SHA/bundle/commit も launch certificate に直接束縛する。現行 certificate exact fields は `s8b_launch_cert.py:14-23` なので schema bump が必要。

- **postcondition。** `eligible_for_refreeze` は `mode=="official"` だけから導出せず、有効な private permit を保持した official 完走からのみ `True` にする。現状の設定箇所は `s8b_floor_campaign.py:3042-3048`, `:3091-3095`、pilot の True 拒否は `:2327-2330`。二相 finalize 後のみ publish する説明 `:2409-2416` は維持する。

既存成果物について「実在未確認」の field はない。PBS wrapper と launch authorization receipt は未確認ではなく、現状不存在であり、実装段で新設してからでなければ gate を開けない。

### 循環への回答

active ratified freeze を条件にしてはならない。v2 generation は `floor_source` を含む (`s8b_ratified_freeze.py:96-104`, `:914-985`) 一方、その floor result は `mode=="official"` と `eligible_for_refreeze is True` を要求する (`:2228-2251`)。active 解決はさらに approval/pointer を要する (`:1173-1240`)。したがって、

```text
official floor → floor result → v2 generation → approval/active → official floor
```

という実循環になる。解禁条件は上流 sealed bundle と実行 revision、人間 launch receipt に置く。

既存 generation approval の path は generation SHA から導出される (`2026-07-16_s8b-floor-protocol-package.md:387-395`) ため、floor 前には作れない。流用するのは「hash 導出 path・exact record・none commit・履歴検証」という方式だけで、schema・namespace・意味は分離する。

### 自動実行の是非

条件成立は「実行可能」を意味するだけで、自動起動させない。実行には既存の明示 `--mode official` と人間による PBS submit が必要で、receipt 作成・存在を trigger にする scheduler は設けない。追加の `--allow-official`、環境変数、production flag は禁止する。

## C. 実装形 (file:line 粒度)

- `orchestrator/campaign/s8b_selector_launch_evidence.py:1` を新設し、`s8b_ratified_freeze.py:2455-2700` の active-chain 非依存な selector exact 検証を共有 leaf 化する。ratified 側と floor admission 側の双方が同じ関数を呼ぶ。

- `orchestrator/campaign/s8b_floor_authorization.py:1` を新設する。strict canonical receipt parser、bundle SHA 導出、HEAD/worktree、sole-add topology、`AI-Agent: none`、historical verifier、immutable `VerifiedFloorLaunchAuthorization` を実装する。生成用 flag は guard に追加しない。

- `s8b_floor_campaign.py:178-203`:

  ```python
  class OfficialPermissionError(FloorCampaignError):
      reason_code: str

  def _assert_official_permitted(
      mode: str, *, protocol: Mapping, freeze_doc: VerifiedFreeze
  ) -> _OfficialPermit | None:
  ```

  pilot は直ちに `None`。official は protocol/freeze、上流 bundle、selector exact verifier、人間 receipt、clean HEAD を検証し、immutable `_OfficialPermit` を返す。拒否文は例として `official mode を拒否: launch authorization が成立しない [official-authorization-missing]` とし、番号参照を廃止する。

- `s8b_floor_campaign.py:2639-2679` は、順序を

  ```text
  mode validate
  → official seam 13 個の default 検査
  → permit = _assert_official_permitted(...)
  → _run_campaign_core(..., _official_permit=permit)
  ```

  とする。public signature には bypass 引数を追加しない。

- `s8b_floor_campaign.py:2682-2698` の private core signature に内部 proof object だけを追加する。

  ```python
  def _run_campaign_core(..., _official_permit: _OfficialPermit | None = None):
  ```

  `_validate_mode` 直後、official で permit がない・型不正なら、env lookup や時計取得より前に拒否する。pilot に permit が混入しても拒否する。これは bool/flag ではなく、検証結果を運ぶ private 型である。production での constructor/発行 callsite は wrapper だけと静的 AST test で固定する。任意 Python に対する偽造不能までは主張しない点は、既存 `RatifiedFreeze` の境界定義 (`s8b_ratified_freeze.py:726-733`) と同じ。

- `s8b_floor_campaign.py:2712-2791` で、再検証した protocol/freeze SHA と permit を比較し、reservation 取得後に `script_sha256` と承認 wrapper SHA を比較する。

- fresh official `s8b_floor_campaign.py:2862-2880` では `_floor_preflight_freeze_allowlist` を再実行し、permit 内の mapping と exact 一致させてから既存二重 scan へ進む。claim が scan より先に永続化される現行順序 `:2821-2854` は at-most-once 契約なので、別裁定なしに動かさない。

- `s8b_launch_cert.py:14-144` は certificate v2 とし、exact nested `launch_authorization {path, sha256, artifact_bundle_sha256, commit}` を追加する。`build_launch_certificate`、strict validator、発行後再検証 (`s8b_floor_campaign.py:1642-1752`) へ expected authorization を渡す。

- resume は `_verify_resume_journal` `s8b_floor_campaign.py:3205-3328` に permit を渡し、certificate が同じ authorization を参照する場合だけ official resume を許す。現行 Pegasus は `allow_resume=False` なので `:2748-2752` で先に閉じるが、journal schema の整合は維持する。

- `eligible_for_refreeze` の二箇所 `:3047`, `:3095` は `mode=="official"` ではなく「検証済み permit を持つ official execution」から導出する。

- `s8b_ratified_freeze.py:144-179`, `:2787-2916`, `:2937-2986` は、authorization record raw SHA → certificate field の辺と、A の履歴・receipt bundle を検証する。これを行わないと後段では「人間 receipt を通った run」を再構成できない。

- CLI `s8b_floor_campaign.py:3416-3460` は `:3434-3441` の固定拒否を削除する。protocol/freeze load 後に同じ `_assert_official_permitted` を一度 read-only で呼び、public wrapper でも再度呼ぶ。`OfficialPermissionError` は `status=refused`, `reason_code`, rc=2、その他の campaign error は従来どおり rc=1。

- テスト変更:

  - `test_main_official_mode_always_refused` (`test_s8b_floor_campaign.py:1047-1054`) は、`test_main_official_without_authorization_is_structured_refusal` に変更。`{}` ではなく valid protocol/freeze を使い、rc=2 と stable reason code を検査する。valid receipt の positive dispatch も追加する。
  - `test_run_campaign_core_rejects_official_with_zero_side_effects` (`:1057-1071`) は public wrapper のテストへ正しく改名し、別途、実 private core に permit なしで入って副作用 0 を検査する。
  - `test_public_official_rejects_each_nondefault_seam_before_side_effects` (`:1074-1099`) は順序を変えず残し、authorization verifier すら呼ばれないことを追加 assert する。
  - `_official_test_seam` (`:612-620`) は「permit fixture」と「clean-scan stub」に分割する。real-seal E2E では scan stub を使わない。
  - real-seal E2E (`:3005-3505`) は tmp git に実 topology の authorization commit を作り、少なくとも一ケースは public wrapper を通す。guard、receipt verifier、real preflight、二重 scan、durable policyを同時に通す。
  - receipt の全 field、bundle path/hash、HEAD、sole diff、none trailer、dirty worktree、wrapper hash、private-core permit の各一辺変異を negative matrix にする。
  - pilot は authorization fileを一切読まず、certificateなし・eligible false (`:4362-4379`) を維持する。

- 文書は `docs/phase3.md:53`、`docs/worklog.md:915`、`docs/decisions.md:3677+` を新しい正本ポインタと「裁定済み・authorization 未成立なら拒否」に更新する。実装・receipt 発効前に完了扱いにしない。

## D. 段階化 (何を先に、何を後に)

一度に恒久解禁しない。

1. **本 wave — 設計のみ。** 完了条件は本案のユーザー裁定。コード・receipt・guard は不変。

2. **前提実装 wave。** ユーザー再確認後、PBS floor wrapper、共有 selector verifier、authorization verifier、certificate/ratified 対応を実装する。guard はまだ無条件拒否。完了条件は negative matrix、pilot 非対称、ratified consumer、文書 check の実走結果を親が確認すること。

3. **条件付き guard 配線 wave。** `_assert_official_permitted` と private permit を結線するが、実 repo に receipt は置かない。したがって production は引き続き fail-closed。完了条件は tmp git の valid receipt だけが public E2E を通り、実 repo は `official-authorization-missing` で拒否されること。

4. **人間 activation。** 全コードと PBS wrapper を commit H に固定後、ユーザーが receipt だけを commit A (`A^=H`, `AI-Agent: none`)。同じ commit に AI 生成物やコード変更を混ぜない。実機 readiness が失敗したら修正 commit により receipt は自動失効し、再発行する。

5. **明示 official run。** A 上で人間が PBS submit。終了後に certificate/result 等を通常の後段へ渡す。v2 candidate/approval はこの後であり、解禁条件へ逆流させない。

## E. 解禁時に初めて production 化する面のリスク棚卸し

最大の正しさリスクは、private core が raw `mode="official"` と注入 seam だけで `eligible_for_refreeze=True` を生成できる現状 (`s8b_floor_campaign.py:2682-2698`, `:3047`, `:3095`)。guard 解除前に private permit 化を必須とする。

最大の未実測運用リスクは、物理 Pegasus 上の PBS wrapper、実 attestation、reservation、claim、12 個の trace-disabled build、96 session の実計測である。real-seal E2E は preflight/durable/certificate は実物だが、build・measure と物理 probe は模擬 (`test_s8b_floor_campaign.py:3005-3019`, `:3355-3372`)。

解禁前の最小実測は次とする。

- tmp git の public-path E2E: 実 receipt commit topology、guard、実 seal、production preflight、二重 scan、durable policyを通し、build/measure だけを test dependency に差し替える。既存 private-core E2E の不足分を閉じる。

- 実 Pegasus allocation 上の read-only readiness job: receipt/HEAD/worktree、wrapper SHA、実 calibration/attestation、PBS reservation、durable root、CCBench HEAD、二重 clean scanまでを、production と共有する関数で実測する。`run_campaign` に `--dry-run` bypass は加えない。

- 同 allocation で実 `build_cells` の12 trace-disabled buildと contract provenanceを integration harness で確認する (`s8b_floor_campaign.py:962-1019`)。floor 数値としては採用しない。

- その後の最初の official campaign を canary とし、certificate、journal、result、claim、frozen bytes 不変を独立照合する。

なお scan 失敗時にも claim が残るのは現行の意図された at-most-once 契約であり、テストも固定している (`test_s8b_floor_campaign.py:3858-3880`)。運用手順に「失敗 claim を自動削除しない」を明記する。

## F. ユーザー裁定が要る択一

1. **人間 authorize の方式**

   - (a) **推奨:** 新規 upstream launch receipt。sealed bundle・revision・wrapper を直接束縛し、循環しない。
   - (b) downstream active generation approval を流用。floor result が先に必要なので循環し、採用不可。
   - (c) protocol の `AI-Agent: none` commit/T-080 receipt を兼用。prediction・journal・実行 revision を束縛しないため不足。

2. **receipt の launch artifact への残し方**

   - (a) **推奨:** certificate v2 に receipt path/SHA/bundle/commit を直接追加。ratified 検証まで監査鎖が残る。
   - (b) launch 時だけ検査し clean-scan digest に暗黙包含。schema 変更は小さいが、後段から receipt を一意に再構成しにくい。

3. **authorization の寿命**

   - (a) **推奨:** `HEAD==receipt commit A` の間、同一 bundle の明示 retry/campaign に再利用。revision が一度でも動けば自動失効。
   - (b) descendant を許容し、保護 file closure の不変を検査。運用は楽だが履歴 verifier と攻撃面が増える。
   - (c) 一回限り receipt + consumption tombstone。最強だが crash/resume、run ID 先決め、不可逆 state machine が追加される。

4. **journal↔prediction の直接等値を floor 前へ昇格するか**

   - (a) 現行 floor preflight のまま、lineage 強化を既裁定どおり oracle waveへ残す。
   - (b) **推奨:** `s8b_ratified_freeze.py:2455-2700` の active 非依存部分を共有化し、claim/invocation/envelope の直接等値を解禁条件へ昇格。成果物 acceptance は狭くなるが、現行実 seal はこの等値を満たすことが E2E で characterization 済み。

5. **条件成立時の起動**

   - (a) **推奨:** receipt は permission のみ。人間の明示 PBS submit を別に要求。
   - (b) receipt 検出で自動起動。意図しない再実行面を作るため不採用。

## G. 本 wave の scope 外だが real な所見

- `docs/phase3.md:89-95` と `docs/worklog.md:864-868`, `:909-912` は T-080 receipt 待ちを残すが、実 receipt は `output/t080-migration/legacy-freeze-repin.receipt.json:1` に存在する。official launch receipt とは別物として文書を整理すべき。

- D80 の既知 residual、初回自己整合 bundle 捏造、historical digest preimage、content TOCTOU は `docs/decisions.md:3370-3375` に残る。`docs/worklog.md:853-855` で residual 受諾・lineage 後送り済みなので、再度 blocker にするなら明示再裁定が必要。

- `AI-Agent: none` は暗号学的人間証明ではない。この限界は floor protocol package `2026-07-16_s8b-floor-protocol-package.md:423-427` と同じ。署名方式へ上げるかは別裁定。

- real-seal insight の受入欄は未反映 placeholder のまま (`output/insights/2026-07-24_e2e-real-seal.md:32-37`)。文書だけを緑の根拠にしてはならない。

- 本 wave ではファイルを変更しておらず、pytest・check 群も実行していない。以上は静的検査結果であり、テスト緑や guard 解除後の実測成功は主張しない。
---

## 2. 段 3 敵対相談 レンズ A — 正しさ境界・防壁の破れ (逐語)

以下はすべて静的検査結果である。テスト・pytest は実行しておらず、「緑」の主張はしない。`【確認済み】` は現行ファイルから確認した事実、`【設計上の帰結】` は提示プランを実装した場合の帰結を表す。

## 所見一覧

- **ID**: A-01
- **重大度**: BLOCKER
- **主張**: 【確認済み】現行 public/CLI の official 受理集合は空集合である。【設計上の帰結】無条件 `False` を四項 conjunction に置換すれば、条件成立後の受理集合は厳密に拡大するため、「拒否削除ではないから規律 2 を緩めない」という説明は偽である。
- **根拠**: public wrapper は必ず `_assert_official_permitted` を通り、official は無条件例外となる (`orchestrator/campaign/s8b_floor_campaign.py:193-203`, `:2668-2679`)。CLI も全 official を protocol 読込み前に拒否する (`:3434-3441`)。したがって `A_now(public)=∅` に対し、本案は `A_plan(public)={official ∧ DefaultSurface ∧ Upstream ∧ Authorization ∧ Runtime}` となる。
- **成果物影響**: 現在は生成不能な official `launch_certificate.json`・journal・`result.json(eligible_for_refreeze=true)` が生成可能になり、v2 candidate の `floor_source` 受理集合が空集合から非空へ変わる。
- **推奨対応**: ユーザー裁定に受理集合差分を明記し、この guard を「正しさゲート」ではなく期限付き activation lock と再分類してよいか明示裁定する。規律 2 を文字どおり適用するなら T-088 自体が NO-GO である。

- **ID**: A-02
- **重大度**: BLOCKER
- **主張**: 【設計上の帰結】private core への `_official_permit` 引数は、既存契約が禁止する「引数による bypass 面」そのものである。private 型と AST callsite 固定は事故防止にしかならず、同一 Python process 内の敵対 caller に対する防壁ではない。
- **根拠**: 現契約は production flag・環境変数・引数による bypass を禁止する (`orchestrator/campaign/s8b_floor_campaign.py:193-197`)。private core は現在 guard を呼ばない (`:2682-2701`)。先例の `RatifiedFreeze` 自身も「任意 Python コードに対する偽造不能ではない」と明記する (`orchestrator/campaign/s8b_ratified_freeze.py:726-733`)。
- **成果物影響**: verifier を通らず同型 `_OfficialPermit` を構築した caller が private core の official 受理集合へ入り、official certificate・journal・`eligible_for_refreeze=true` の result を生成できる。
- **推奨対応**: core に proof object を渡さず、core 自身が固定 path の raw bytes・Git topology・receipt を再検証する。AST test は repo 内の偶発的 constructor 増加だけを防ぐものと明記し、security claim に数えない。

- **ID**: A-03
- **重大度**: BLOCKER
- **主張**: 【確認済み】`ReservationBinding.script_sha256` は実 wrapper の観測値ではなく環境変数からの自己申告である。したがって `reservation_binding.script_sha256 == permit.pbs_wrapper.sha256` は恒真化可能で、P3 の「環境変数 bypass を作らない」に反する。
- **根拠**: `script_sha256` を含む binding 全項目は `IZANAGI_RESERVATION_*` から構築される (`orchestrator/campaign/reservation.py:120-175`)。検査は SHA の形式、別の環境変数 `PBS_JOBID`、boot ID、時刻だけであり、scheduler spool や実行 script bytes を読まない (`:39-55`, `:218-270`)。専用 floor wrapper 自体も未実装である (`tools/pegasus/README.md:128-139`)。
- **成果物影響**: 承認 wrapper を経由していない直接起動でも既知 SHA を環境変数へ設定でき、reservation journal・certificate・result が誤った wrapper provenance を certified 値として保持する。
- **推奨対応**: PBS/scheduler が返す job record・spooled script bytes・job ID を独立取得して hash 検証するか、scheduler 署名済み submission receipt を導入する。環境変数同士の一致を authorization gate として数えない。

- **ID**: A-04
- **重大度**: BLOCKER
- **主張**: 【設計上の帰結】certificate に permit 内 authorization をコピーし、同じ permit を expected として再検証するだけなら自己整合 gate である。authorization namespace は現行 v3 clean digest に bytes として含まれないため、guard 後の receipt 差替え・削除を certificate 発行時に検知できない。
- **根拠**: 一般 repository file について v3 digest が保持するのは path 一覧だけで、path→SHA は `output/s8b-freeze` allowlist/chain record に限られる (`orchestrator/campaign/s8b_floor_campaign.py:1597-1630`)。新 authorization はその namespace 外である。既存 strict certificate は独立二回目 scan を expected にすることで恒真を避けている (`:1693-1718`; `docs/decisions.md:3340-3346`)。
- **成果物影響**: certificate が「発行時点に存在した receipt」ではなく過去に permit へ取り込んだ値を参照し、launch ledger と現在の authorization bytes が乖離する。
- **推奨対応**: certificate 直前に authorization file を `O_NOFOLLOW` 相当で再読し、A の Git blob・raw SHA・canonical body を独立再計算する。その `{path,sha256}` を clean-scan preimage または別の独立 expected 入力へ含め、certificate は二回目の capture から構築する。

- **ID**: A-05
- **重大度**: BLOCKER
- **主張**: 【確認済み】`AI-Agent: none` は人間性を証明せず、AI が同じ trailer の commit を作れる。したがって本案の `HumanLaunchAuthorization` は独立した第二防壁ではなく、名称に反する規約 attestation にすぎない。
- **根拠**: hook 正本自身が「AI が `none` commit を作れる以上、人間性の機械証明にはならない」と明記する (`hooks/README.md:49-53`)。Codex には hook が未配線であり (`:15-24`)、鍵署名が必要とも明記される (`:183-187`)。実 verifier も commit message の逐語一致しか検査しない (`orchestrator/campaign/s8b_ratified_freeze.py:525-549`)。
- **成果物影響**: AI が receipt と A commit を自己作成し、自身が生成した upstream bundleを「人間承認済み」として certificate・result・台帳へ流せる。
- **推奨対応**: allowlist 公開鍵による署名、署名済み Git tag、または AI から書込み不能な外部承認系を使う。署名を採らない場合は `NoneTrailerLaunchAttestation` 等へ改名し、P8 の二重防壁には数えない。

- **ID**: A-06
- **重大度**: BLOCKER
- **主張**: 【確認済み】official 前の既存 gate である §5-(viii)/B-005 の最終ユーザー受諾が、本案の receipt schema に束縛されていない。また `VerifiedUpstreamBundle` という名称は、既知の初回自己整合 bundle 捏造残余を閉じたかのように過大主張している。
- **根拠**: floor 前に残存限界一覧をユーザーが読んで受諾することが明示 gate である (`docs/phase3.md:66-68`)。B-005 は未裁定のまま残る (`output/insights/2026-07-24_e2e-real-seal.md:55-58`)。初回自己整合 bundle と FROZEN pin の同時捏造は既存 ancestry/journal/source 検証でも排除不能である (`docs/decisions.md:3370-3375`)。
- **成果物影響**: certificate 前削除・content TOCTOU・初回 seal 捏造の残余を受諾していない bundle が certified selector 選択、floor report、v2 台帳の根拠になり得る。
- **推奨対応**: exact な残存限界文書の `{path,sha256,decision}` を署名済み authorization に含める。単なる `scope` 文字列ではなく、受諾対象の版を機械束縛するまで official を閉じる。

- **ID**: A-07
- **重大度**: BLOCKER
- **主張**: 【確認済み】本案の activation 手順には、既存 `launch_validate` が要求する certificate-only commit C が存在しない。さらに推奨寿命 `HEAD==A` は、C を同一 worktree で作った瞬間に authorization を失効させる。
- **根拠**: certificate C は generation G の厳密祖先でなければ拒否される (`orchestrator/campaign/s8b_ratified_freeze.py:3043-3054`)。現 campaign には certificate 後 callback があるが (`orchestrator/campaign/s8b_floor_campaign.py:2894-2922`)、public official は callback 注入を拒否し、default は no-op である (`:2635-2667`)。既存設計資料も C commit または二段 API が必須とする (`output/insights/2026-07-18_s8b-c22-consultations.md:1024-1037`, `:1051`)。
- **成果物影響**: official result を生成できても、certificate lineage 不成立で v2 generation の `launch_validate` が拒否し、candidate/approval/active へ到達しない。
- **推奨対応**: `H(code) → A(authorization) → C(certificate-only) → G(result+generation) → P(approval/active)` の実行可能な二段 protocol を設計する。execution worktree を A に固定したまま別 control worktree で C/G を作る等、`HEAD==A` と C lineage の両立方法も明記する。

- **ID**: A-08
- **重大度**: MUST
- **主張**: 【設計上の帰結】receipt は「一回の launch」へ束縛されず、同じ A 上で無期限・複数 campaign に再利用できる。一方 filename が artifact bundle だけから導出されるため、同じ bundle のまま code basis や wrapper を変更すると正当な再承認を同じ path に置けない。
- **根拠**: 実 reservation には `job_id` と `nonce` が存在する (`orchestrator/campaign/reservation.py:26-37`) が、提示 schema にはなく、run ID も開始時刻から後で生成される (`orchestrator/campaign/s8b_floor_campaign.py:2816-2820`)。既存 approval path は承認対象そのものの generation hash から導出する (`output/insights/2026-07-16_s8b-floor-protocol-package.md:387-395`)。また既存 `H` は activation/current head を意味する (`orchestrator/campaign/s8b_ratified_freeze.py:726-738`, `:2776-2781`) ため、`authorization_basis_commit=H=A^` は識別子の二義化でもある。
- **成果物影響**: 一件の authorization から複数の official result が発行されるか、逆に wrapper/code 更新後の正当な再承認が immutable path collision で不可能になる。
- **推奨対応**: 「revision activation」か「単発 launch authorization」かを裁定する。前者なら key を bundle+basis+wrapper+policy/残存限界 digest から導出し、後者なら scheduler job ID・nonce・run identity と一回限りの consumption を束縛する。commit 名は `launch_basis_commit` とし `H` を再利用しない。

- **ID**: A-09
- **重大度**: MUST
- **主張**: 【確認済み】`VerifiedFreeze` は frozen dataclass だが内部 `document` は mutable `dict` である。【設計上の帰結】permit の検証後に同じ dict を core が利用する設計では、hash pin と実際に enumerate/build した freeze 内容が分離し得る。
- **根拠**: `VerifiedFreeze.document` は生の `dict` のまま返される (`orchestrator/campaign/s8b_freeze_io.py:30-38`, `:41-68`)。core は `freeze_doc.sha256` だけを protocol と比較した後、同 dict から cells/schedule を作る (`orchestrator/campaign/s8b_floor_campaign.py:2754-2769`)。対照的に `RatifiedFreeze` は再帰的に不変化する (`orchestrator/campaign/s8b_ratified_freeze.py:717-733`)。
- **成果物影響**: result が正しい v1 SHA を掲げながら、異なる holdout/configuration/cell schedule の計測値を保持し得る。
- **推奨対応**: guard で読んだ raw bytesを保持し、その strict parse 結果を再帰 immutable 化する。permit 内 mapping も shallow frozen dataclass ではなく深く不変化し、core はその captured object だけを使う。

- **ID**: A-10
- **重大度**: MUST
- **主張**: 【確認済み】共有 launch certificate を一律 v2 へ bump すると、D80 が明示的に維持した v1 validator・resume・ratified の受理集合を狭める。`eligible_for_refreeze` の変更だけには下流で証明力がなく、実際の narrowing は certificate/authorization lineage の追加から生じる。
- **根拠**: 現 certificate は v1・exact 6 keys である (`orchestrator/campaign/s8b_launch_cert.py:14-23`, `:50-126`)。resume と ratified は同じ validator を使う (`orchestrator/campaign/s8b_floor_campaign.py:3320-3325`; `orchestrator/campaign/s8b_ratified_freeze.py:2894-2903`)。D80 は validator の signature/意味と両 caller を不変と裁定した (`docs/decisions.md:3337-3346`)。ratified は現在、official 再導出と boolean `True` だけを要求する (`orchestrator/campaign/s8b_ratified_freeze.py:2228-2251`)。また official private-core 呼出しは少なくともテストの `:718`, `:2990`, `:3373`, `:3633`, `:3868`, `:3958`, `:3988` に存在し、提示 test list は全件を列挙していない。
- **成果物影響**: v1 certificate を持つ既存 resume/ratified fixture・consumer が拒否へ変わり、逆に下流 authorization edge を入れ忘れれば `eligible_for_refreeze` の certified 受理集合は実質不変となる。
- **推奨対応**: v1 historical validator を残し、新規 official 発行だけ v2 必須とする version dispatch を設ける。permit 配線と ratified の authorization 再構成を同一実装 wave の原子的変更にし、全 private-core/ratified fixture を列挙する。

- **ID**: A-11
- **重大度**: MUST
- **主張**: 【設計上の帰結】CLI の一回目の permit は捨てられ、public wrapper が同じ mutable 外部状態を再評価するため安全性を増やさない。二回目通過後の mapping drift は claim 永続化後に検出され、authorization refusal が ledger 副作用を残す。
- **根拠**: 現行順序は claim 永続化が `:2821-2854`、freeze allowlist・scan がその後の `:2856-2880` である (`orchestrator/campaign/s8b_floor_campaign.py`)。scan 不一致でも claim を残す契約はテストで明示される (`orchestrator/tests/test_s8b_floor_campaign.py:3858-3880`)。本案は permit mapping の exact 比較も同じ後段へ置く。
- **成果物影響**: certified result は fail-closed でも、同じ論理的 authorization failure が timing により rc=2/rc=1 に分岐し、campaign claim 台帳を消費する。
- **推奨対応**: CLI は public wrapper を一度だけ呼び、typed refusal を捕捉する。authorization・immutable bundle capture は claim 前に一度確定し、at-most-once 用の独立二回 scanだけを claim 後に残す。

- **ID**: A-12
- **重大度**: MUST
- **主張**: 【確認済み】`_selector_evidence_exempt_exact` は「意味検証済み全証拠集合」ではなく「scan 免除集合」を返す関数であり、payload を意図的に返さない。これを一つの中立 helper として authorization mapping に流用すると、payload の束縛漏れまたは誤免除が起きる。
- **根拠**: helper は claim の payload path/SHA 宣言一致だけを検査し (`orchestrator/campaign/s8b_ratified_freeze.py:2645-2653`)、raw/envelope は exemption に追加する (`:2674-2696`)。D80 は payload を免除しないことを明示する (`docs/decisions.md:3315-3320`)。一方 floor preflight allowlist は payload bytes も path→SHA に含める (`orchestrator/campaign/s8b_floor_campaign.py:1418-1452`)。
- **成果物影響**: authorization bundle SHA から payload bytes が抜けるか、payload が clean scan から誤って除外され、selector 入力改変または holdout hit が certified 選択へ混入する。
- **推奨対応**: shared helper は `all_bound_files`、`scan_exempt_files`、`non_exempt_payload_files` を型で分離して返す。authorization は前者、ratified scan は後二者を別々に使用し、集合間の包含・非包含を静的/変異テストで固定する。

## 総合判定

**NO-GO**。active ratified freeze を前提にすると実循環になるという判断自体は正しいが、提示案はそれを避ける過程で、規律 2 上の受理集合拡大、偽造可能な private permit、環境変数自己申告の wrapper gate、機械的に人間を証明しない receipt、未束縛の B-005、欠落した certificate commit C を残している。加えて v2 certificate の互換性、receipt TOCTOU、再利用寿命も未裁定であり、現状のままでは「条件付き解禁」ではなく複数の新しい bypass 面を同時に導入する。

凍結影響については、現行 `FROZEN_MANIFEST` の exact 23 件に certificate/authorization は含まれない (`orchestrator/tests/test_frozen_artifacts.py:38-114`, `:139-153`) ため、提示された file 変更だけなら既存凍結 bytes・holdout generator pin を直接変更する事実は確認できない。ただし authorization を新たな凍結族へ加えるなら exact key set の再裁定が必要であり、加えないなら dynamic Git-attested record と明記すべきである。

## 親 brief への反論

- **P1 — 支持**: 防壁変更は設計裁定後の別 wave に分離すべきであり、本 wave で guard を変更してはならない。

- **P2 — 支持**: 「§8 未裁定」は古いが、guard 自体は裁定後も意図的に残された dormant 防壁であり、単なる typo 修正として解除できない (`docs/phase3.md:53-60`)。

- **P3 — 否定**: 方針は妥当だが、本案は `_official_permit` 引数と環境変数由来 `script_sha256` を admission に使うため実際には満たしていない（A-02、A-03）。

- **P4 — 支持**: 多義的な `§8`・`F6` を診断文から除き、canonical path と具体的 reason code を用いるべきである。

- **P5 — 否定**: 現行の二重拒否は CLI と public wrapper であり、private core ではない。さらに同じ外部状態を二回評価して最初の結果を捨てる設計は防壁強化ではなく TOCTOU 面を増やす（A-11）。

- **P6 — 支持（ただし本案は未達）**: campaign ごとの再検査という原則は正しい。しかし同じ receipt を同じ A 上で無期限再利用でき、certificate 時点の receipt bytes を再捕捉しないため、提示設計は原則を実現していない（A-04、A-08）。

- **P7 — 支持**: active generation g1 は official result と `eligible_for_refreeze=true` を必要とし (`orchestrator/campaign/s8b_ratified_freeze.py:2228-2251`)、active 解決は generation/approval/pointer を必要とするため、これを最初の official floor の前提にすれば実循環となる。

- **P8 — 否定**: 実条件検査と独立した人間証明を二重化する考えはよいが、`AI-Agent: none` は人間証明ではない。現 hook 正本もその限界を明記しており、本案の receipt を第二防壁として数えることはできない（A-05）。
---

## 3. 段 3 敵対相談 レンズ B — 実在性・scope 肥大・[T-083] freeze 整合 (逐語)

静的検査のみを実施した。pytest・実 campaign・Pegasus job は走らせておらず、テストの緑は主張しない。

## 所見一覧

- **ID**: B-01
- **重大度**: BLOCKER
- **主張**: 親 brief の「人間の R receipt 発行が残 gate」は現ツリーでは偽である。T-080 receipt は既に発効し、その後に protocol 凍結・prediction seal まで完了している。
- **根拠**: receipt 本体は [legacy-freeze-repin.receipt.json:1](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-e2e-real-seal/output/t080-migration/legacy-freeze-repin.receipt.json:1)。protocol 発行は active-valid receipt を必須にする [s8b_floor_campaign.py:537-552](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-e2e-real-seal/orchestrator/campaign/s8b_floor_campaign.py:537)。worklog も R commit 発効を [docs/worklog.md:597-601](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-e2e-real-seal/docs/worklog.md:597)、protocol・prediction 完了を [docs/worklog.md:647-674](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-e2e-real-seal/docs/worklog.md:647) に記録している。`phase3.md:89-94` と worklog 末尾 `:909-912` が stale。
- **成果物影響**: floor の受理集合を誤って空扱いし、実在する protocol/prediction の proof chain を未発効扱いする。再発行を試みれば migration receipt の immutable history と衝突する。
- **推奨対応**: 残 gate から R receipt を削除する。新 launch approval と T-080 migration receipt を混同せず、worklog は追記で stale 状態を訂正する。

- **ID**: B-02
- **重大度**: BLOCKER
- **主張**: `output/s8b-floor-authorizations/<artifact_bundle_sha256>.json` は再発行不能である。コードまたは wrapper だけを修正すると bundle hash は不変なのに receipt 内容の `authorization_basis_commit`／wrapper hash は変わり、同じ path を再度「sole add」できない。
- **根拠**: bundle の素材となる allowlist は upstream artifact の path/hash だけで、revision・wrapper を含まない [s8b_floor_campaign.py:1418-1452](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-e2e-real-seal/orchestrator/campaign/s8b_floor_campaign.py:1418)。流用予定の topology は receipt path 一件の `A` だけを要求する [t080_freeze_migration.py:853-868](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-e2e-real-seal/orchestrator/campaign/t080_freeze_migration.py:853)。これはプランの組合せからの論理的帰結である。
- **成果物影響**: readiness 失敗後に修正すると、新 revision の official 受理集合が恒久的に空になる。回避のため immutable 検査を緩めれば、旧 authorization が別 revision を受理する。
- **推奨対応**: filename を `subject_sha256` から導出し、その preimage に `scope + H + artifact_bundle_sha256 + wrapper path/hash` を含める。少なくとも `<H>.json` とし、再発行・旧 record の扱いを規定する。

- **ID**: B-03
- **重大度**: BLOCKER
- **主張**: 「既存成果物に実在未確認 field はない」は gate 入力全体については誤りである。protocol・prediction・journal の field は実在するが、allowlist は関数戻り値、wrapper hash は環境変数由来の自己申告、wrapper path・実行 revision・launch authorization・certificate authorization field は不存在である。
- **根拠**: 実在確認できたものは protocol exact 18 fields [s8b_floor_contract.py:34-41](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-e2e-real-seal/orchestrator/campaign/s8b_floor_contract.py:34)、prediction の `pre_oracle_head/sources/execution_policy` [selector_predictions.json:2-33](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-e2e-real-seal/output/s8b-freeze/selector_predictions.json:2)、row の hash/path [selector_predictions.json:43-67](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-e2e-real-seal/output/s8b-freeze/selector_predictions.json:43)、journal records [journal.jsonl:1-15](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-e2e-real-seal/output/s8b-freeze/selector-runs/journal.jsonl:1)。一方、`script_sha256` は `IZANAGI_RESERVATION_SCRIPT_SHA256` から読むだけ [reservation.py:120-175](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-e2e-real-seal/orchestrator/campaign/reservation.py:120) で、検査は job/boot/time に限定される [reservation.py:218-270](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-e2e-real-seal/orchestrator/campaign/reservation.py:218)。現 certificate は6 fieldsだけ [s8b_launch_cert.py:14-23](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-e2e-real-seal/orchestrator/campaign/s8b_launch_cert.py:14)。
- **成果物影響**: 別 script が承認済み hash を環境変数へ設定しても、現比較案だけなら authorized とされ、誤った wrapper/revision 由来の result が `eligible_for_refreeze=True` になり得る。
- **推奨対応**: committed wrapper の実 bytesと、job-scoped submit artifact の `source_commit/job_script_sha256/job_id/nonce` を検査する。環境変数同士の比較を wrapper 実在性の証明と呼ばない。

- **ID**: B-04
- **重大度**: BLOCKER
- **主張**: 段2で「不存在 wrapper」とそれに依存する authorization/certificate/ratified 機構を同時実装する順序は DW-G04 違反である。
- **根拠**: 条件付き機能は発火可能な既存 artifact path または計測 ID がある場合だけ実装できる [docs/dev-wave/core.md:47-50](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-e2e-real-seal/docs/dev-wave/core.md:47)。floor 専用 wrapper は次 wave と明記される [tools/pegasus/README.md:136-139](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-e2e-real-seal/tools/pegasus/README.md:136)。
- **成果物影響**: tmp fixture だけで成立する phantom gate を production gate として実装し、実 repo の official 受理集合は空のままになる。
- **推奨対応**: wrapper-only waveを先行させ、実 wrapper pathと実 submit artifact IDを一度生成・確認してから admission 実装を再裁定する。それまでは authorization schema は設計メモに留める。

- **ID**: B-05
- **重大度**: BLOCKER
- **主張**: selector helper 抽出、certificate v2、ratified consumer、resume、private permit/AST、巨大 negative matrix は初回 cycle 前 blocker ではない。T-083 freeze と lineage 先送り裁定を逆流している。
- **根拠**: 新規機構は「実走を不可能にする blocker」に限定される [docs/phase3.md:79-88](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-e2e-real-seal/docs/phase3.md:79)、[docs/worklog.md:58-62](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-e2e-real-seal/docs/worklog.md:58)。lineage は oracle wave へ先送り済み [docs/worklog.md:853-855](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-e2e-real-seal/docs/worklog.md:853)、historical cert/ratified も同じ残余である [docs/decisions.md:3370-3375](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-e2e-real-seal/docs/decisions.md:3370)。現 ratified verifier は既に claim/invocation 等値を検査する [s8b_ratified_freeze.py:2645-2699](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-e2e-real-seal/orchestrator/campaign/s8b_ratified_freeze.py:2645)。実在6 rows/15 journal recordsは静的比較で不一致0だったが、これはテスト合格ではない。
- **成果物影響**: certificate schema と ratified 受理集合を floor 前に変更し、現 v1 consumerや正当な初回 floor を追加機構の不具合で拒否し得る。
- **推奨対応**: 初回前は wrapper、実行 revision/job binding、条件付き guard/CLI 解禁だけに限定する。selector exact 共有化、cert v2、ratified、resume、AST hardening は oracle/lineage wave または1 cycle後へ送る。

- **ID**: B-06
- **重大度**: MUST
- **主張**: 提案 receipt は campaign authorization ではなく revision activation である。job ID、nonce、campaign run ID、使用回数、期限がなく、同じ `HEAD=A` 上の無制限の official run を一件の receipt が承認する。
- **根拠**: job固有識別子は既に `ReservationBinding.job_id/nonce` として実在する [reservation.py:26-37](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-e2e-real-seal/orchestrator/campaign/reservation.py:26)。campaign固有値は certificate の `campaign_run_id` [s8b_launch_cert.py:16-23](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-e2e-real-seal/orchestrator/campaign/s8b_launch_cert.py:16)。提案 schema はいずれも持たない。
- **成果物影響**: 一件の人間 receipt に対応する certified result 集合が無制限となり、どの PBS job/result を人間が承認したか再構成できない。
- **推奨対応**: 「revision approval」と明記して再利用を仕様化するか、job-scoped submit artifact の `job_id + nonce` へ束縛する。per-run Git commit は運用コストが高いため推さない。

- **ID**: B-07
- **重大度**: MUST
- **主張**: 「新規 exact schema」と称しているが exact ではない。`schema` の literal、型、canonical preimage、domain separator、artifact件数・順序・重複、path文法、時刻形式、`commit` の意味が未定義である。
- **根拠**: 既存 certificate は literal、exact key集合、hash型、UTC、run identityまで規定する [s8b_launch_cert.py:14-23](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-e2e-real-seal/orchestrator/campaign/s8b_launch_cert.py:14)、[s8b_launch_cert.py:50-126](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-e2e-real-seal/orchestrator/campaign/s8b_launch_cert.py:50)。既存 approval も exact keys を固定する [s8b_ratified_freeze.py:113-121](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-e2e-real-seal/orchestrator/campaign/s8b_ratified_freeze.py:113)。
- **成果物影響**: producer/verifierごとに異なる `artifact_bundle_sha256` や receipt を受理し、certificate・台帳の authorization 参照が非一意になる。
- **推奨対応**: field表、exact型、literal、canonical bytes、hash preimage、重複拒否、UTC grammar、A/Hの意味を裁定パッケージ内で完全定義する。

- **ID**: B-08
- **重大度**: MUST
- **主張**: `HEAD==A` の一回検査だけでは「実行 revision 束縛」にならない。hours-long run 自体は A の寿命を切らさないが、検査後に worktree が変わっても一般 repo files は content hash されない。
- **根拠**: clean-scan v3 は一般 repository files について path一覧しか preimage に入れず、bytes hash は freeze allowlistだけ [s8b_floor_campaign.py:1623-1629](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-e2e-real-seal/orchestrator/campaign/s8b_floor_campaign.py:1623)。既存 calibration wrapper は job開始時に source commit、clean状態、script bytesを再照合する [certify_calibration.sh:174-196](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-e2e-real-seal/tools/pegasus/certify_calibration.sh:174)。
- **成果物影響**: certificate が A を指していても、後続 build が A 以外の worktree bytes を読めば、result の revision proof 参照が虚偽になる。
- **推奨対応**: detached A の専用 cloneを実行中変更禁止で使い、wrapperが job開始直後と build直前に `HEAD/status/script blob` を再検査する。単なる失敗再実行は同じ A で許し、コード変更時だけ新 approval とする。

- **ID**: B-09
- **重大度**: SHOULD
- **主張**: 提案された exact identifier 文字列自体の既存衝突は確認できなかったが、`authorization` は既に少なくとも三義ある。generic namespace は避けるべきである。
- **根拠**: floor内部では `session-start` を authorization と呼ぶ [s8b_floor_campaign.py:1878-1881](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-e2e-real-seal/orchestrator/campaign/s8b_floor_campaign.py:1878)、retry reasonも `retry-authorization` [s8b_ratified_freeze.py:2013-2022](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-e2e-real-seal/orchestrator/campaign/s8b_ratified_freeze.py:2013)。恒久 freeze は `authorization.*` reason namespaceを持つ [freeze-permanent-design-s2.md:1678-1687](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-e2e-real-seal/docs/freeze-permanent-design-s2.md:1678)。また既存人間承認 field は `approver/approved_at/scope` [s8b_ratified_freeze.py:113-121](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-e2e-real-seal/orchestrator/campaign/s8b_ratified_freeze.py:113)。
- **成果物影響**: refusal台帳やproof参照が、session retry・generation approval・launch revision approvalのどれを指すか曖昧になる。
- **推奨対応**: `floor-launch-revision-approval.*` の専用 reason namespaceを使い、record名も `floor_launch_revision_approval` とする。

- **ID**: B-10
- **重大度**: SHOULD
- **主張**: P5の「core と CLI の二重拒否」は現実と違い、提案の CLI事前検査＋public再検査にも安全上の意味がない。二回のgit/artifact検査は異なる snapshot を観測し得る。
- **根拠**: 現在の拒否は public wrapper [s8b_floor_campaign.py:2639-2669](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-e2e-real-seal/orchestrator/campaign/s8b_floor_campaign.py:2639) と CLI [s8b_floor_campaign.py:3434-3441](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-e2e-real-seal/orchestrator/campaign/s8b_floor_campaign.py:3434)。private core は guard を呼ばない [s8b_floor_campaign.py:2682-2698](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-e2e-real-seal/orchestrator/campaign/s8b_floor_campaign.py:2682)。production CLI は public wrapper を呼ぶ [s8b_floor_campaign.py:3443-3452](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-e2e-real-seal/orchestrator/campaign/s8b_floor_campaign.py:3443)。
- **成果物影響**: 一回目と二回目の間の状態変化で正当なrunが拒否され、またどちらのsnapshotをcertificateが表すか不明確になる。
- **推奨対応**: admission predicateは一回だけ実行し、検証済み snapshotを同一呼出し内で使う。CLIは例外をrc=2へ翻訳するだけにする。

- **ID**: B-11
- **重大度**: MUST
- **主張**: 文書更新先が誤っている。`phase3.md:53` は当時の歴史記述、worklog過去エントリは凍結済みであり、`worklog.md:915` を直接更新してはならない。
- **根拠**: 過去worklogは凍結 [docs/worklog.md:12-20](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-e2e-real-seal/docs/worklog.md:12)。可変状態の正本はworklog末尾と現行phase docだけ [CLAUDE.md:153-155](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-e2e-real-seal/CLAUDE.md:153)。`phase3.md:53` は直後の裁定完了記録と対になった歴史 [docs/phase3.md:49-60](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-e2e-real-seal/docs/phase3.md:49) で、実際に stale なのは現行チェックポイント [docs/phase3.md:89-96](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-e2e-real-seal/docs/phase3.md:89)。
- **成果物影響**: gateの現状・残作業・proof pointerが再び矛盾し、今回の「R receipt未発行」のような誤った受理判断を再生産する。
- **推奨対応**: phase現行チェックポイントを訂正し、worklogは新規末尾エントリを追加する。decisionsには耐久的な設計判断だけを書き、実装・発効状態を置かない。

## 最小案の提示

初回 cycle 前の分類は次のとおり。

| 要素 | 判定 |
|---|---|
| floor PBS wrapperとjob-scoped source/script/revision binding | 初回実走BLOCKER |
| 無条件guardとCLI固定拒否の条件付き解除 | wrapper実在後のBLOCKER |
| 既存protocol/prediction preflight、二重scan、certificate v1 | 実装済み。再利用のみ |
| 新Git launch receipt | G02上のblockerではない。明示PBS submitで代替可能 |
| selector exact helper抽出 | oracle/lineage waveへ延期 |
| certificate v2、ratified verifier追加 | lineage裁定どおり延期 |
| resume authorization | Pegasus `allow_resume=False` のため延期 |
| private permit型、AST caller pin、完全negative matrix | 1 cycle後のhardening |
| reason-code体系一般化 | 診断改善。1 cycle後 |
| 文書のR状態訂正 | 今回の裁定パッケージでMUST |

より小さい同等案は以下である。同等なのは「未承認official launchを止める防壁」であり、post-hoc lineage は既裁定どおり後送する。

1. まず wrapper-only waveを分離する。`tools/pegasus/submit_s8b_floor.sh` と job script を、既存の source/script/nonce receipt [submit_certify.sh:75-100](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-e2e-real-seal/tools/pegasus/submit_certify.sh:75)、job冒頭再照合 [certify_calibration.sh:174-205](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-e2e-real-seal/tools/pegasus/certify_calibration.sh:174)、reservation export [certify_calibration.sh:322-329](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-e2e-real-seal/tools/pegasus/certify_calibration.sh:322) と同型にする。

2. wrapperはcreate-only submission artifactに `source_commit/job_script_path/job_script_sha256/job_id/nonce/submitted_at` を記録する。人間の明示 `qsub` 自体を launch authorization とし、campaignはこのjob-scoped artifactと `ReservationBinding` を照合する。新しいGit receiptは不要である。

3. [s8b_floor_campaign.py:193-203](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-e2e-real-seal/orchestrator/campaign/s8b_floor_campaign.py:193) の無条件拒否を、一回だけ実行する admission predicateへ変える。public wrapperの13 seam拒否 [s8b_floor_campaign.py:2648-2667](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-e2e-real-seal/orchestrator/campaign/s8b_floor_campaign.py:2648) は維持する。

4. predicateは既存 `_floor_preflight_freeze_allowlist` の結果と、job submission artifact、HEAD/clean、実wrapper blobを検証する。そのmappingを既存二重scan [s8b_floor_campaign.py:1693-1718](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-e2e-real-seal/orchestrator/campaign/s8b_floor_campaign.py:1693) に渡し、同じbundleを再利用する。

5. CLIは [s8b_floor_campaign.py:3434-3441](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-e2e-real-seal/orchestrator/campaign/s8b_floor_campaign.py:3434) の固定拒否だけを削除し、public callから返る admission errorをrc=2へ翻訳する。事前にpredicateを重複実行しない。

6. certificate v1、ratified verifier、resume schemaは変更しない。authorization lineageのcertificate追加は、ユーザーが先送りしたoracle結線waveで行う。

別Git commitによる人間attestationをなお必須にするなら、新 module は `s8b_floor_authorization.py` 一本だけにし、filenameを上述のsubject digestで導出する。selector helper、certificate v2、ratified変更は同時に入れない。

## 総合判定

**NO-GO**。現案は、既に発行済みのR receiptを未発行とする誤前提、コード修正後にreceiptを再発行できないfilename設計、不存在wrapperと自己申告envに依存するphantom gate、そしてT-083・lineage先送りに反する大幅なscope肥大を含む。まず現状正本を訂正し、wrapperとjob-scoped revision bindingを独立に実在させた後、最小の一回限りadmission配線へ設計し直す必要がある。

## 親 brief への反論

- **P1 — 支持**: 本waveは設計・ユーザー裁定だけでよい。
- **P2 — 否定**: 文言は古いが防壁は意図的dormantである。またfloor protocol F6は「v2 generation approval」であってlaunch authorizationではない [floor-protocol-package.md:379-410](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-e2e-real-seal/output/insights/2026-07-16_s8b-floor-protocol-package.md:379)。「裁定済み・発効なし」へ一括置換すると別機構を混同する。
- **P3 — 原則支持、現案は不充足**: 実成果物への束縛は正しい。しかしallowlistは関数戻り値、script hashはenv自己申告、wrapper/revision/authorizationは不存在である。
- **P4 — 支持**: 多義的な`§8`・`F6`を新診断から排除するのは正しい。
- **P5 — 否定**: 現在はCLI＋public wrapperで、core拒否ではない。predicateの二重実行は防壁強化にならず、一回のsnapshot-bound検査で足りる。
- **P6 — 否定**: 提案receiptはcampaign固有fieldを持たず、同じAで無制限に再利用できる。campaignごとの人間authorizationではない。
- **P7 — 支持**: active v2 generationをfloor前提にすれば実循環になる。上流bundleを使うべきである。
- **P8 — 否定**: 一人運用での明示PBS submitとjob-scoped source/script receiptに加え、別Git launch receiptが必要という欠陥実例は示されていない。追加するならwrapper実在後の明示再裁定事項であり、初回cycle前blockerではない。