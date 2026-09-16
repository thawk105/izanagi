## 現行挙動の表

以下、`C = orchestrator/campaign/autonomous_trial_completeness.py`、`P = orchestrator/campaign/p3_autonomous_workload_trial.py`、`T = orchestrator/tests/test_autonomous_trial_completeness.py`、`PT = orchestrator/tests/test_p3_autonomous_workload_trial.py` と略記する。行番号は現物の変更前。

**重要な訂正：campaign identity を持つ admission-failure cell は、現行では root を与えても通らない。** root 要求の解除だけでは本件は完了しない。

表の「条件付き受理」は、journal/report の整合性・digest・該当する束縛検査がすべて成功する場合を指す。`fatal_error` 有りは整合する Mapping を意味し、null・不正型・terminal event 不一致は先行検査で拒否される。

| `do_build` | `fatal_error` | cells の形 | root 無し | root 有り |
|---|---|---|---|---|
| False | 無し | 空 | 拒否：要求 workload の未実行を説明できない | 同左 |
| False | 有り | 空 | 条件付き受理：provider/transport 初期化失敗、開始前 wall-budget 等 | 条件付き受理。空の campaign-chain 検査も実行 |
| False | 無し | 非空、各 decision が `{"admission_status":"not-applicable"}` | 条件付き受理 | campaign-chain はその decision を build admission として受理しないため拒否 |
| False | 有り | 同上、terminal と整合 | 条件付き受理 | 同上 |
| False | 有無両方 | admitted／failure decision を含む | 拒否：no-build decision 違反 | 同左 |
| True | 無し | 空 | 拒否：workload coverage 等 | 同左 |
| True | 有り | 空 | 条件付き受理：`fatal_without_cells` | 条件付き受理。cross-binding は省略、空の chain は実行 |
| True | 無し | 厳密 campaignless fallback 1 cell | 拒否：`supervisor-error` に対応する terminal/fatal が無い | 同左 |
| True | 有り | 厳密 campaignless fallback 1 cell | 条件付き受理：`failure_without_campaign` | 条件付き受理 |
| True | 有無両方 | campaign identity 付き厳密 admission-failure 1 cell | 拒否：root 必須 | **拒否：cross-binding と failure chain の条件が両立しない** |
| True | 有無両方 | admitted のみ | 拒否：root 必須 | 条件付き受理：cross-binding と campaign-chain の双方が必要 |
| True | 有無両方 | admitted prefix ＋ 最後に failure 1 cell | 拒否：root 必須 | campaignless fallback なら条件付き受理。identity 付き failure なら拒否 |
| True | 有無両方 | failure 複数／failure が最終でない／非厳密 decision | 先行 completeness で拒否 | 同左 |
| 両方 | 有無両方 | cells が list でない／要素が Mapping でない | 先行 shape 検査で拒否 | 同左 |

根拠：

- 共通先行検査：`C:5043–5053`。decision と failure の個数・位置：`C:3112–3185`。
- fatal と terminal の対応：`C:2395–2458`。coverage：`C:2803–2867`。
- 既存免除と dispatch：`C:5054–5096`。
- identity 付き failure は、campaign directory 不在なら `C:4255`、Layer-3 不在なら `C:4374–4379` で拒否。一方、Layer-3 が存在すれば `C:4911–4915` の failure chain が拒否する。

## 穴の同定

**partial cell 経路だけではない。穴は実在するが、brief の説明より広い。**

| producer 経路 | 出力される失敗形 | 根拠 |
|---|---|---|
| workload 中の例外 | identity 付き cell、`supervisor-error`、fatal 有り、admission failed | `P:4083–4099` で cell 保存、`P:3679–3690` で回収、`P:3705` で admission 終結 |
| workload 正常 return 後の admission 失敗 | identity 付き cell、fatal 無しでも成立 | `P:3739–3745`、失敗 decision は `P:3264–3335`、`P:3814` で後続 workload を停止 |
| role-invalid による正常 return | campaign 未作成のまま admission failed、通常 fatal 無し | 例：planner invalid は `P:4246–4252` → `P:4471` → `P:3740`。reports directory 不在を `P:3110–3111` が検出 |
| cell 内 wall-budget による正常 return | identity 付き failure、wall-budget fatal 有り | `P:4116–4133` → `P:3740` → `P:3779–3802` |
| reports directory はあるが Layer-3 render に失敗 | 上記各経路の failure に厳密 diagnosis が付く場合がある | `P:3115–3128`、`P:3324–3335` |

これらは最初の cell で発生すれば failure-only report になる。既存 completeness は failure を最大一つに制限するため、**非空の failure-only report は実質 1 cell**である。

ただし、例外を捕まえたものがすべて report になるわけではない。`P:3956–3988` の publish 前検査を通る必要がある。既存 Layer-3 があるケースや独立 admission が成功するケースは、producer 側 chain が拒否する。

また、brief が根拠にした `PT:8800` のテストは正例として使えない。

- `PT:8808–8816` で completeness と digest-chain を無効化。
- `PT:8825–8836` で admitted decision を返す fake render。
- `PT:8837` で campaign-chain も無効化。

`stop_reason == "supervisor-error"` だけでは admission failed を証明しない。さらに registered の identity 付き failure は `C:1137–1141` の digest 検査にも拒否され、producer も登録済み試行では同検査を呼ぶ（`P:3960`）。**本 wave の正例は、これらの検査を mock しない exploratory producer 走で作るべきである。**

## 設計案 (file:line)

**P1 は維持する。ただし、P2 の「path identity だけ未検証」を撤回し、独立した診断結果を返す契約への親裁定が必要。以下はその条件付き実装案である。**

「既存 verifier の受理集合を一切広げない」を新 opt-in の診断結果にも適用すると、目的と両立しない。既定の成功集合を保存し、新経路は **非 certifying の診断検証成功**として区別する。

1. **`C:5036` 直前：閉じた failure-only 述語を追加する。**

   identity 付き cell の基本 key 集合を次に固定する。

   ```python
   K = {
       "workload", "workload_flags", "perf_config_scale",
       "descriptor", "descriptor_binding",
       "campaign_id", "campaign_root", "generations", "stop_reason",
       "admission_decision", "pending_critic_disposition",
   }
   ```

   許す形は、`set(cell)` が次のいずれかに**厳密一致**するものだけ。

   ```python
   K
   K | {"error"}
   K | {"layer3_admission_diagnosis"}
   K | {"error", "layer3_admission_diagnosis"}
   ```

   追加条件：

   - `do_build is True`、`status == "partial"`、`cells` は長さ 1 の list。
   - decision は既存 `is_exact_cell_admission_failure_decision`（`C:244`）。
   - disposition は既存厳密述語（`C:318`）。
   - diagnosis がある形は既存厳密述語（`C:262`）。
   - `error` は `supervisor-error` の形だけに許し、`set(error) == {"type", "message"}` と型を確認。
   - campaign ID/root は非空文字列。残りの状態・journal 対応は既存 completeness に委譲。
   - 既存 campaignless 述語（`C:336`）は変更しない。

2. **`C:5036–5053`：明示引数を追加する。**

   ```python
   failure_only_diagnostic: bool = False
   ```

   sibling、completeness、execution digest の既存検査は先にそのまま実行する。既存 2 免除も優先して従来経路へ流す。

3. **`C:5069` の直前：新しい診断分岐を置く。**

   発動条件は `failure_only_diagnostic is True`、root 未指定、上記厳密述語成立の積。admitted cell、混在 report、非厳密 cell には発動しない。

   root 指定時は従来検証を実行し、flag による検査省略を認めない。

4. **`C:5036` 直前：診断検証 helper を追加する。**

   - root に依存しない role raw／provider payload・envelope の検査を、`C:4279–4314` と同じ条件で実行する。
   - proposal 検査は既存 `_cross_binding_proposals`（`C:3453`）を呼ぶ。
   - 宣言 root を既存 `_path_identity` で解決し、その `parent.parent` を使って**既存 `assert_campaign_layer3_chain` をそのまま呼ぶ**。
   - これにより workload flags、campaign ID/path の内部整合、Layer-3 不在、独立 admission 失敗を保持する。呼出元が指定した外部 root との一致は証明しない。
   - `verify_s8c_cross_binding` 全体の成功にはしない。例外を捕まえて成功扱いする実装も採らない。

   この helper は既存検査の必要部分だけを扱い、WAL が無い失敗に WAL/build/bench 成功を要求する一般化はしない。

5. **診断分岐の戻り値と `C:5099–5119` の CLI：署名を残す。**

   API は既定経路の `None` を維持し、新分岐だけ固定 schema の receipt を返す。CLI は `--failure-only-diagnostic` を追加し、その receipt を JSON 出力する。

   最低限の固定フィールド：

   ```json
   {
     "schema_version": "autonomous-trial-failure-only-diagnostic/v1",
     "verification_mode": "failure-only-diagnostic",
     "certifying": false,
     "campaign_output_root_binding": "not-verified",
     "s8c_cross_binding": "not-established"
   }
   ```

   これに検証済み journal/report の SHA-256 と実行した検査の固定一覧を含める。これは検証範囲の明示であり、暗号署名ではない。producer report は書き換えない。

**編集対象は実装・テスト・所要台帳の 3 file。** producer、registry、cross-binding 本体、campaign-chain 本体は変更しない。P4 の実装 1 単位を維持する。

## root 省略で失われる検査

brief 実測 4 の分類は、**chain の failure 分岐だけについては概ね正しいが、standalone 全体の説明としては誤り**。

| 検査 | root 引数無しでの扱い |
|---|---|
| (a) 外部指定 root と宣言 campaign root の一致 | 証明できない。receipt で未検証を明示 |
| (a) のうち `campaigns/<campaign_id>` という内部 path 整合 | 宣言 root から親を導出して既存 chain を呼べば維持できる |
| (b) `reports/layer3_report.json` 不在 | 宣言 root に対し実行可能。dangling symlink も拒否する既存条件を保持 |
| (c) 独立 admission が成功しない | 宣言 root に対し実行可能。既存 chain で保持 |
| role raw／payload／envelope／proposal の束縛 | root 引数に依存しないため実行する |
| cross-binding の directory・standard driver・Layer-3/build population 要件 | root 省略とは別の要件。現行のままでは対象 report が拒否される |
| Layer-3 を起点とする WAL・source・build/bench の完全束縛 | 対象の失敗 report では成立を証明できない。診断 receipt で未成立とする |

特に `C:4374–4379` は「root が無いから検査不能」ではなく、**失敗 report に build population が無いことを拒否する gate**である。ここを黙って飛ばし「(a) だけ省略」と報告してはいけない。

また「journal と report の 2 file だけ」は一般には成立しない。role が実行済みなら既存検査も raw 等を読む。正確な完了条件は、**campaign output root 引数を不要にすること**であり、参照成果物まで不要にすることではない。

## テスト計画

新 helper は `T:1743` 付近、新 API/CLI テストは `T:2376` 直後へ置く。既存 `test_build_file_verification_with_cells_still_requires_campaign_root` の定義は現物では **`T:2353`**。本文・期待値とも無改変とする。

| 新テスト名 | 正負 | 内容 |
|---|---|---|
| `test_failure_only_diagnostic_accepts_producer_partial_cell` | 正 | cell 保存後・campaign 作成前に fault injection。producer の completeness・digest・chain・finalizer を無効化せず、実出力を検証 |
| `test_failure_only_diagnostic_accepts_producer_normal_return_failure` | 正 | role-invalid の正常 return → 実 finalizer の reports 不在失敗。fatal 無しを確認 |
| `test_failure_only_diagnostic_requires_explicit_opt_in` | 負 | 同じ正例を flag 無しで拒否 |
| `test_failure_only_diagnostic_rejects_admitted_cell` | 負 | 既存 admitted fixture を新 flag 付きでも拒否 |
| `test_failure_only_diagnostic_rejects_mixed_cells` | 負 | admitted prefix ＋ failure を拒否 |
| `test_failure_only_diagnostic_rejects_nonexact_shape` | 負 | `cell-extra`、`decision-extra`、`error-extra`、`disposition-extra`、`diagnosis-extra` の明示 ID |
| `test_failure_only_diagnostic_rejects_persisted_layer3` | 負 | `file`、`dangling-symlink` の両方 |
| `test_failure_only_diagnostic_rejects_independently_admitted_campaign` | 負 | `T:5040` の実 campaign 構築方式を利用。Layer-3 を除いても admission 成功なら拒否 |
| `test_failure_only_diagnostic_preserves_supplied_root_checks` | 負 | flag があっても誤った supplied root を救済しない |
| `test_failure_only_diagnostic_preserves_provider_binding` | 負 | journal/report 整合を保ったまま provider payload bytes を改変し拒否 |
| `test_failure_only_diagnostic_cli_emits_noncertifying_receipt` | 正 | subprocess で flag 配線、終了値、固定 receipt、入力 digest を検査 |
| `test_campaignless_failure_file_verification_without_root` | 正 | 既存免除を files API 経由で検証。flag 無し |
| `test_failure_only_diagnostic_does_not_change_existing_exemptions` | 正 | `fatal-empty`、`campaignless` に flag を加えても既存検査経路・戻り値を維持 |

正例で新述語や verifier を mock しない。producer 走の障害注入と、検証機構を無効化する mock を区別する。

## 所要台帳への追記

`orchestrator/tests/acceptance_duration_ledger.json:2` の `duration_seconds_by_nodeid` に以下を追加する。全行の接頭辞は
`orchestrator/tests/test_autonomous_trial_completeness.py::`。

```text
test_failure_only_diagnostic_accepts_producer_partial_cell
test_failure_only_diagnostic_accepts_producer_normal_return_failure
test_failure_only_diagnostic_requires_explicit_opt_in
test_failure_only_diagnostic_rejects_admitted_cell
test_failure_only_diagnostic_rejects_mixed_cells
test_failure_only_diagnostic_rejects_nonexact_shape[cell-extra]
test_failure_only_diagnostic_rejects_nonexact_shape[decision-extra]
test_failure_only_diagnostic_rejects_nonexact_shape[error-extra]
test_failure_only_diagnostic_rejects_nonexact_shape[disposition-extra]
test_failure_only_diagnostic_rejects_nonexact_shape[diagnosis-extra]
test_failure_only_diagnostic_rejects_persisted_layer3[file]
test_failure_only_diagnostic_rejects_persisted_layer3[dangling-symlink]
test_failure_only_diagnostic_rejects_independently_admitted_campaign
test_failure_only_diagnostic_preserves_supplied_root_checks
test_failure_only_diagnostic_preserves_provider_binding
test_failure_only_diagnostic_cli_emits_noncertifying_receipt
test_campaignless_failure_file_verification_without_root
test_failure_only_diagnostic_does_not_change_existing_exemptions[fatal-empty]
test_failure_only_diagnostic_does_not_change_existing_exemptions[campaignless]
```

19 nodeid。現物の `nodeid_count` は `:23122` の 23118 なので、この案だけなら 23137。ただし親の最終 collect と照合して確定する。所要秒は親の実走値で埋め、未計測値を実測として記録しない。

## 変異候補

新設位置はすべて `C:5036` 直前または files API／CLI 内。正確な新行番号は段 4 で実装予定 diff に固定する。

| 壊す機構の 1 行 | 赤になるべきテスト |
|---|---|
| 診断分岐の `failure_only_diagnostic is True` を恒真にする | `test_failure_only_diagnostic_requires_explicit_opt_in` |
| cell key の厳密一致を部分集合判定に変える | `test_failure_only_diagnostic_rejects_nonexact_shape[cell-extra]` |
| 診断 helper の既存 `assert_campaign_layer3_chain(...)` 呼出しを削除 | persisted Layer-3 の 2 ケース、独立 admitted の負例 |
| 診断 helper の provider payload digest 検査呼出しを削除 | `test_failure_only_diagnostic_preserves_provider_binding` |
| CLI から新引数を渡す行を削除 | `test_failure_only_diagnostic_cli_emits_noncertifying_receipt` |
| 新診断分岐の dispatch を無効化 | producer partial／normal-return の正例 |

receipt の `certifying` を書き換えるだけの変異は、機構を殺していないため主変異に採らない。既存共通検査に遮られる decision 変異も、新機構の独立 kill としては数えない。

## 総括

採用候補は、既定と既存 2 免除を保つ明示 opt-in の非 certifying 診断経路である。
穴は partial 例外だけでなく、正常 return 後の admission 失敗にも存在する。
現行 cross-binding は対象 failure を root 有りでも拒否するため、「path identity だけ省略」という P2 は成立しない。
親の択一は、**診断契約への scope 修正を認めて上記案を進めるか、既存全検査の成功を必須としたまま本 wave を再裁定へ戻すか**。前者を推奨する。
静的確認のみ実施した。ファイル編集・pytest 実走は行っておらず、既存・新規テストの成功は未確認である。