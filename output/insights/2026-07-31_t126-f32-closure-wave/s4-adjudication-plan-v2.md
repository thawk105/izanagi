authority: none
default_effect: no-state-change

# T-126 F3-2 closure — 段 4 裁定 / plan v2

## 結論

段 5 へ進む。段 2 プランはそのまま採用しない。段 3 の両レンズが BLOCKER を返したため、
**retirement を `after-publish` lifecycle に限定**し、**B2 の regression を fail-closed guard で塞ぎ**、
**変異 4 件を再設計**した plan v2 へ差し替える。S1' (targetless) と第 5 経路 (B4) と B6 は
real だが scope 外とし、裁定パッケージでユーザーへ返す。

review 正本:

- `.codex/dev-wave-t126-f32-closure-jobs/s3-review-barrier/output.md` (レンズ A)
- `.codex/dev-wave-t126-f32-closure-jobs/s3-review-reach/output.md` (レンズ B)
- 段 2 plan: `.codex/dev-wave-t126-f32-closure-jobs/s2-plan/output.md`

## 所見裁定

| 所見 | 裁定 | 採否 / 最小境界 |
|---|---|---|
| A1 targetless 前倒し破棄が C4 (異常時 mutation なし) を破る | real / BLOCKER / scope 内 | **採用**。retirement を `lifecycle == "after-publish"` に限定する。targetless は global preflight + semantic 検査の後 (現行位置) に留める |
| B7 `verify_attempt` 拒否時に targetless bytes を破壊 | real / A1 と同一根 / scope 内 | A1 の裁定で同時に解消。追加で T9 (正例) と M9i (過剰破壊検出変異) を登録する |
| B2 A valid × B 構造不正で本修正が終端を悪化 (無変更拒否 → 非検証 receipt publish + `outcome_pending` 固着) | real / BLOCKER / scope 内 | **採用 (B2 択 1)**。`invalid` return の直前に `attempt_state == "valid"` の fail-closed guard を置く。受理集合は広げず、終端を `initial_submitted` に留める |
| B1 / A2 M9e の replacement が「削除」で kill 集合が M9a/M9b/fsync pin と交差 | real / BLOCKER / scope 内 | **採用**。M9e を「削除」でなく「移動」へ再設計する (下記変異事前登録) |
| B3 M9f も単一理由でない | real / HIGH / scope 内 | S1' を scope 外とするため **M9f を登録しない**。代わりに M9i を登録する |
| A3 「新たに閉じる失敗はすべて publication-failed」は S1 について偽 | real / HIGH / 文書訂正 | **採用**。retry 不増を支えるのは `artifacts.py:1113-1116` の series-result 存在 gate と `:1108` の observations gate であると plan v2 に明記。T5 が `retry_eligible is False` を pin する |
| B4 第 5 経路 (collector 自身の receipt staging crash 残余が `_manifest` で恒久拒否) | real / HIGH / **scope 外** | 本修正で悪化しない既存欠陥。裁定パッケージへ。T7 の必要性文言を撤回・訂正する |
| B5 production 到達性の引用 anchor 誤り + shell window に実行裏取りゼロ | real / HIGH / 文書訂正 | **採用**。anchor を `t126_qualification.sh:140-145` + `:150-154` へ訂正。shell 側 window は「静的読取のみで実行裏取り無し」と成果物へ明記する (live-shape テストは本 wave で足さない) |
| B6 `target_rejected=1` が `JOB_RESULT` を差し戻さない | real / MEDIUM / **scope 外** | 本修正と独立の既存欠陥。裁定パッケージへ。`tools/pegasus/**` は本 wave で変更しない |
| A4 `expected_nlink=1` が S1/S2 の防壁だったという因果は逆 | real / MEDIUM / 文書訂正 | **採用**。前 wave の erratum どおり「修正前は receipt 未生成」と訂正。retire の事実が receipt に残らない件は裁定パッケージへ |
| A5 T6 の 2 shape が順序制約を exercise しない + 恒真 assertion | real / MEDIUM / scope 内 | **採用**。順序 anchor は `early-malformed-name` 単独。他 2 shape は M9d 冗長 gate と明記。`verify_attempt(...)=="invalid"` の恒真 assertion は削除 |
| A6 T7 の必要性根拠が偽 | real / MEDIUM / 文書訂正 | **採用**。T7 は残すが根拠を「message 単位の独立 pin」へ訂正 (B4 と整合) |
| A7 到達性引用が load-bearing でない | real / MEDIUM / 文書訂正 | B5 と同一。crash 注入 seam は test seam であって production 経路ではないと明記 |
| A8 `DW-G05` 成果物影響の記載漏れ | real / MEDIUM / 文書訂正 | **採用**。「link/unlink window で落ちた成功 series が certified 選択の材料へ新規に入る」を明記 (下記) |
| A9 early namespace の preflight→apply window が `verify_attempt` 1 回分拡大 | real / MEDIUM / scope 外 | same-UID race は前 wave 裁定で scope 外。**実装しない**が plan v2 に非対称を明記する |
| B8 「根本は 1 つ」と実装 scope の不一致 | real / MEDIUM / 文書訂正 | **採用**。根本記述を「attempt 直下の job-result staging」へ狭め、B4 / B6 / S1' を同根の別経路として列挙する |
| B9 registry 追随の項目数と失敗モード | real / nit | **採用**。「4 箇所」「中間状態は import 時 KeyError で collection error」へ訂正 |
| B10 親 reproducer の行範囲引用誤り | real / nit | **採用**。`:100-117` は「series ありは両走行で拒否 = 診断変異が S1 を閉じなかった証拠」と読み替える |
| B11 targetless payload が 3 窓のうち 1 つ | real / nit | T9 を payload 2 param (`b""` / 完全 bytes) にして採用 |
| A10 埋め込み指示文字列の走査 | 異常なし | 記録のみ |

`DW-G02`/`DW-G05` により、scope 内とした所見は receipt、attempt ledger、closure manifest、
certified 選択の入力集合を実際に変えるため must-fix とする。scope 外とした 3 件は本修正で
悪化せず、閉じるには新しい artifact 種または production shell の変更を要するため、
`DW-S04` に従い実装せず裁定パッケージへ返す。

## 成果物影響 (`DW-G05`)

- **S1 を閉じる方向の影響**: publish と unlink の間で落ちた**成功 series** が、これまで final も
  failure も出せなかったのに final receipt を出せるようになる。すなわち certified 選択の材料に
  新規に入る attempt の集合が広がる。広がる集合の構成要素は「canonical と同一 inode・同一 bytes・
  nlink=2 の stage が 1 個あるだけの、それ以外は clean な attempt」であり、意味は 1 bit も変わらない。
- **S2 を閉じる方向の影響**: pre-series failure で rejected evidence と post-job copy を作った後も
  receipt / outcome event が出ず `initial_submitted` に固着していた正規 attempt が、
  failure receipt へ閉じる。
- **B2 guard の影響**: A valid × B 拒否の直積で、非検証 failure receipt を publish して
  `outcome_pending` に固着する終端が消え、`initial_submitted` の無変更拒否に留まる。
- **S1' を閉じないことの影響 (scope 外)**: series 完走後に publisher が link 前で落ちた attempt は
  引き続き final も failure も出せず `initial_submitted` に固着する。
- **B4 を閉じないことの影響 (scope 外)**: collector 自身が receipt publish 中に落ちた正規 attempt は
  引き続き `_manifest` で恒久拒否され `initial_submitted` に固着する。
- **B6 を閉じないことの影響 (scope 外)**: `attempt-pointer.json` 不一致時に rejection marker が
  attempt namespace へ落ちると、その attempt は `unreferenced in-job evidence` で恒久拒否される。
- retry authority は増えない。それを支えるのは `PERMANENT_NONRETRY_FAILURES` ではなく
  `artifacts.py:1113-1116` の series-result / final-receipt 存在 gate と `:1108` の observations gate である。

## plan v2

対象は `orchestrator/qualification/collector.py` と `orchestrator/tests/test_t126_pegasus_tools.py`
の 2 ファイルのみ。`t126_driver.py`、`artifacts.py`、`tools/pegasus/**` は変更しない。

### P1. preflight の hoist

1. 新ヘルパ `_preflight_job_result_namespaces(*, capability, attempt_dir, submit)` を
   `_rejected_result_evidence` の直後に追加する。既存 `_reconcile_result_namespace` を
   attempt → early job-staging の順で 2 回呼ぶだけの純関数とし、両方の 5-tuple を返す。
   呼出し回数・引数・順序は現行と同一にする。
2. 新ヘルパ `_retire_after_publish_attempt_staging(attempt_dir, attempt_preflight)` を追加する。
   preflight から stage / lifecycle を取り出し、**`lifecycle == "after-publish"` のときだけ**
   既存 `_apply_result_reconciliation` を呼ぶ。それ以外 (`targetless` / stage なし) は何もしない。
   この lifecycle 限定が A1 / B7 の裁定の実体であり、コメントで「targetless は唯一の複製であり、
   後段の fail-closed 拒否より前に破壊しない」と理由を書く。
3. `_apply_result_reconciliation` と `_reconcile_result_namespace` は逐語不変とする
   (M9a / M9b / M9d の anchor 保存)。

### P2. `collect()` への挿入

4. `collect()` の「attempt identity is not submission-derived」raise の直後、
   `series_path = attempt_dir / "series-result.json"` の直前に次を挿入する。

   ```
   attempt_preflight, staging_preflight = _preflight_job_result_namespaces(
       capability=capability, attempt_dir=attempt_dir, submit=submit)
   _retire_after_publish_attempt_staging(attempt_dir, attempt_preflight)
   ```

   この位置より上で attempt を触る資格 (submission evidence / ledger binding / accounting anchor /
   scheduler files / attempt dir 安全性 / marker-identity chain / submission snapshot 一致 /
   job_id 一致 / attempt identity の submission 派生) はすべて確立済みであることを段 3 レンズ A が
   逐語確認済みである。
5. `_reconcile_job_results` の呼出しへ `attempt_preflight=` / `staging_preflight=` を渡す。

### P3. `_reconcile_job_results` の受取りと二重 unlink の回避

6. `_reconcile_job_results` に keyword-only の `attempt_preflight` / `staging_preflight` を足し、
   2 回の `_reconcile_result_namespace` 呼出しをその unpack へ置換する。
   **再計算してはならない** — 再計算すると M9a mutant が観測不能になり `test_m9a_*` が
   mutant で緑になる (段 3 両レンズが逐語で裏付けた)。
   `staging_dir = _job_staging_directory(capability.root, submit)` は後段で使うため残す。
7. attempt 側の in-function apply (現行の
   `_apply_result_reconciliation(attempt_dir, attempt_stage, attempt_lifecycle)`) は
   **削除せず、`attempt_lifecycle == "targetless"` のときだけ呼ぶ**形へ変える。
   after-publish は P1-2 で既に retire 済みのため、そのまま呼ぶと `FileNotFoundError` になる。
   この形により `test_m9a_*[attempt]` (pre-series × targetless) は現行どおり緑を保ち、
   targetless の破棄は global preflight + semantic 検査の後という C4 準拠の位置に留まる。
8. staging 側の in-function apply は現在位置・現在形のまま変更しない
   (B が rejected evidence として保存される経路で staging stage を消さない契約の維持)。

### P4. B2 fail-closed guard

9. `invalid` return (`return "invalid", rejected_bytes, None`) の直前に次を置く。

   ```
   if attempt_state == "valid":
       raise CollectionError(
           "attempt canonical conflicts with a rejected early job-result")
   ```

   理由: 意味的に valid な canonical があるのに `canonical_state="invalid"` を返すと、receipt の
   `job_result` が null になり、`prepare_outcome` の**後**で公開 verifier の
   `valid canonical job-result requires a non-null exact pointer` が発火して ledger が
   `outcome_pending` に固着する。B の rejected evidence 保存はこの raise より前に完了しているため、
   証拠は保全されたうえで fail-closed になる。
10. 実装子は着手前に、現行テストのうち `invalid` return へ `attempt_state == "valid"` で到達する
    ものがあるかを静的に列挙し、完了報告に書く。親の静的確認では
    `test_semantic_invalid_early_result_is_preserved_before_adoption` と
    `test_rejected_target_publisher_crash_closes_nonretry` はいずれも attempt canonical 不在
    (`attempt_state == "missing"`) のため guard は発火しない。ここが覆るなら停止して報告する。

## 段 5 テスト設計 (plan v2)

追加先は `orchestrator/tests/test_t126_pegasus_tools.py` のみ。既存テストは削除・弱化しない。

| ID | テスト名 | 内容 | 唯一の制約対象 |
|---|---|---|---|
| T1 | `test_m9e_after_publish_retirement_precedes_series_verification` | `clean=True` + series timing 準拠の valid canonical + `os.link` stage、B なし。final receipt / stage 消滅 / `nlink==1` / canonical bytes 不変 / 公開 verify valid / ledger terminal / rerun 冪等 | retire が `verify_attempt` より前にあること |
| T3 | `test_m9g_attempt_retirement_is_not_skipped_by_rejection_returns` | `clean=False` + A valid canonical + stage、B は `wmax_s=29101`。failure receipt (publication-failed) / `job_result` 非 null (A bytes) / stage 消滅・canonical `nlink==1`・bytes 不変 / B の bytes と stat 不変 / `rejected-evidence/early-job-result.json` が B と一致 / ledger `initial_failed` / rerun 冪等 / 公開 verify valid | semantic-conflict return が retire を飛ばさないこと |
| T4 | `test_invalid_return_does_not_strand_attempt_staging` | `clean=False` + A canonical = `b'{"partial":'` (構造不正、0600) + stage、B = `b'{"invalid":'`。failure receipt publication-failed / `job_result is None` / stage 消滅・A bytes 不変 / B と rejected-evidence 保存 / rerun 冪等 / 公開 verify valid | invalid return 経路でも retire が効くこと (guard は attempt が valid でないため不発火) |
| T5 | `test_series_after_publish_semantic_conflict_closes_with_preserved_b` | `clean=True` + A valid canonical + stage、B は `wmax_s=29101`、accounting rc=0。failure receipt publication-failed / phase `job-result-recovery` / `job_result` 非 null / `observations_recorded == 2` / **`retry_eligible is False`** / stage 消滅 / B 保存 / 公開 verify valid / ledger `initial_failed` / rerun 冪等 | retire が `verify_attempt` と semantic-conflict return の**両方**より前にあること |
| T6 | `test_cross_namespace_preflight_rejects_before_attempt_stage_retire` | shape を `["early-malformed-name", "different-inode", "extra-hardlink"]` で parametrize。`clean=True` × attempt に valid A + stage。`CollectionError` / **A の stage が残存し nlink 不変** / canonical・B bytes と stat 不変 / receipt 未生成 / ledger `initial_submitted` | `early-malformed-name` のみが順序 anchor。他 2 shape は「M9d の冗長 gate / series あり側の網羅」と docstring に明記し単独変異の証拠から外す。**`verify_attempt(...)=="invalid"` の恒真 assertion は書かない** |
| T7 | `test_attempt_closure_rejects_unreconcilable_staging_bytes` | `clean=False` に `prologue/.toolchain-manifest.json.create-123-0123456789abcdef` を置く。`CollectionError` message が `attempt closure contains abandoned staging bytes` / 当該ファイル保存 / receipt 未生成 | `_manifest` の staging 規則を message 単位で独立 pin (B4 の経路が残るため依然 production 有効) |
| T8 | `test_m9j_valid_canonical_with_rejected_early_result_fails_closed` | `stage` を `[False, True]` で parametrize。`clean=False` + A = valid canonical (+ True なら stage)、B = `b'{"invalid":'`。`CollectionError` が新 message / **receipt 未生成** / ledger `initial_submitted` / A canonical bytes 不変 / B と `rejected-evidence/early-job-result.json` は保存済み / 再走が同じ error へ収束 | P4 の fail-closed guard |
| T9 | `test_m9i_targetless_attempt_staging_is_not_retired_before_verification` | `payload` を `[b"", 完全 job-result bytes]` で parametrize。`clean=True` + canonical **なし** + targetless stage (nlink=1 / 0600)。`CollectionError` に `series result failed read-only verification` と `unreferenced in-job evidence` と stage 名を含む / **stage が残存し nlink==1・bytes 不変** / receipt 未生成 / ledger `initial_submitted` / 再走が同じ error へ収束 | retire を targetless へ広げないこと (正例 = 過剰破壊の検出。`DW-M01` の正例要求) |

`DW-S05-C` に従い、テスト新設に伴う meta-test
`test_fr3_mutation_node_registry_is_exact_and_complete` も同じ単位で更新・実行対象にする。

## 変異事前登録 (`DW-M01` / `DW-M03` / `DW-M08`)

> **erratum への前方参照**: 本節の M9g / M9i の記述は段 6 で誤りと判明した。M9g の
> 「`_reconcile_job_results` 内の旧位置へ戻す」形は実登録形と異なり等価でもなく、M9i の
> 「`test_m9a_*[attempt]` は緑のまま」は二重 unlink により偽である。M9h の「挿入」形も
> 残存 call site により二重 unlink を再生産する。訂正と確定版の期待赤は
> `s6-review-adjudication.md` の「変異事前登録の訂正」と
> 「変異事前登録の期待赤 (fix 1 後の確定版)」を正本とする。本節は初回登録の記録として残す
> (`DW-M02`)。

既登録 M1〜M7 と M8a〜M11b は削除・弱化しない。M9a〜M9d の anchor は逐語不変。
**M9f は登録しない** (S1' が scope 外のため)。新規は次の 4 件とする。

| ID | 単一変異 (replacement は逐語完全形で registry へ登録する) | 事前登録した期待赤 node | 単一理由性 |
|---|---|---|---|
| M9e | `_retire_after_publish_attempt_staging` の呼出しを `collect()` 内で **`_reconcile_job_results` 呼出しの直前へ移動**する (削除ではない) | `test_m9e_after_publish_retirement_precedes_series_verification`、`test_series_after_publish_semantic_conflict_closes_with_preserved_b` | pre-series は retire が `_manifest` より前に残るため M9a/M9b/fsync pin は緑のまま。series あり側だけが `verify_attempt` 拒否で赤 |
| M9g | 同呼出しを `_reconcile_job_results` **内の旧位置** (attempt 側 in-function apply の位置) へ戻す | `test_m9e_...`、`test_m9g_...`、`test_invalid_return_does_not_strand_attempt_staging`、`test_series_after_publish_semantic_conflict_closes_with_preserved_b` | **過剰決定を宣言する**。S1 と S2 の両性質を同時に壊すため単一理由 kill の証拠には数えず、`DW-M03` の冗長 gate として記録する |
| M9i | `_retire_after_publish_attempt_staging` の `lifecycle == "after-publish"` guard を外して全 lifecycle を retire する | `test_m9i_targetless_attempt_staging_is_not_retired_before_verification` | 正例側の過剰破壊検出。after-publish 経路 (T1 / T3 / T5) と pre-series targetless (`test_m9a_*[attempt]`) は緑のまま |
| M9j | P4 の fail-closed guard 2 行を削除する | `test_m9j_valid_canonical_with_rejected_early_result_fails_closed` (`stage` 両 param) | guard 以外の gate はこの直積を拒否しないため赤理由が 1 つに絞れる |

正例は plain rc0 binding、valid after-publish、normal exact canonical、pre-attempt recovered
evidence、pre-series targetless (`test_m9a_*[attempt]`)、unrelated worktree dirt を維持する。
directory fsync は受理集合を変えないため kill に数えず diagnostic sensitivity pin とする。

### registry 追随 (`test_fr3_mutation_node_registry_is_exact_and_complete`)

4 箇所を**同一 commit・同一編集単位**で更新する。分割すると
`_T126_MUTATION_TRANSFORMS` の反復が import 時に `KeyError` を投げ、テストファイル全体が
collection error になる (1 テストが赤で済まない)。

1. 正規表現 `r"test_m(?:8|9|10|11)[a-d]_.+"` を `[a-j]` へ拡張する。既存 `def test_m*` は
   m6a–d / m8a–d / m9a–d / m10a–d / m11a–b の 18 本で、`m6*` は `(?:8|9|10|11)` に一致しないため
   新たに捕捉される既存名は 0 件である。
2. `expected` 集合へ T1 / T3 / T8 / T9 の 4 つの node 名を追加する。
3. key 集合へ `"M9e"` / `"M9g"` / `"M9i"` / `"M9j"` を追加する。
4. `T126_MUTATION_REGISTRY` と `_T126_MUTATION_TRANSFORMS` へ対応行を追加する。
   `source.count(old_anchor) == 1` を破る重複文字列を導入しない。

## 段 5 所有

単一 author unit。許可範囲は次の 2 ファイルだけとする。

- `orchestrator/qualification/collector.py`
- `orchestrator/tests/test_t126_pegasus_tools.py`

`orchestrator/qualification/t126_driver.py`、`orchestrator/qualification/artifacts.py`、
`tools/pegasus/**`、`docs/**`、`output/**`、`.codex/**`、Git index、commit、
既存 campaign / freeze / submodule は no-touch。

段 1 probe (`.codex/.../s1-premise/probe_after_publish_series.py`) と前 wave reproducer
(`.codex/.../compute-focused-review3-reproducer3/`) は本修正で期待が反転するが、いずれも
親所有・no-touch であり、受入 job の gate には混ぜない。T1 / T5 がその恒久版である。

## 訂正事項 (段 2 プランからの差分・コード影響なし)

- 根本の記述を「**attempt 直下の job-result staging** が、attempt 全体を見る 2 consumer より
  後でしか回収されない」へ狭める。回収 (`iterdir` × `.job-result.json.create-` 前置) は
  拒否 (`rglob` × 全名前) の真部分集合であり、同根の別経路として S1'、B4、B6 が残る。
- production 到達性の anchor は `t126_qualification.sh:140-145` (`write_terminal_result` 内の
  `pointer_ok` gate 付き再導出) と `:150-154` (唯一の publisher 起動点) である。`:707-713` は
  呼出し前の既定値設定にすぎない。crash 注入 seam (`:262-273`, `:291`) は test seam であって
  production 経路ではない。
- **shell 側の crash window には実行可能な裏取りが無い。** 既存テストは
  `IZANAGI_T126_TEST_EXIT_AFTER_BINDING` を常に設定するため `t126_qualification.sh:435-718` を
  一度も実行しない。本 wave は collector 側の挙動だけを実測で固定し、shell 側 window は
  「静的読取のみ」と成果物へ明記する。
- 修正前は S1 で `verify_attempt`、S2 で `_manifest` が先に raise するため receipt は生成されず、
  `expected_nlink=1` は S1/S2 の停止点ではない (前 wave の erratum どおり)。
- early job-staging の preflight→apply window は `verify_attempt` 1 回分だけ拡大し、attempt 側は
  縮小する。same-UID race は前 wave 裁定で scope 外のため本 wave では塞がない。
- 親 reproducer の `:100-117` は `expect_mutated` 非参照の無条件分岐であり、
  「診断変異を入れても series ありは閉じなかった」= 案 B/C-弱版では S1 が閉じない証拠である。

## 裁定パッケージ (ユーザーへ返す scope 外 real 所見)

1. **S1' — series 完走 × targetless staging**: publisher が link 前に落ちた成功 series が
   `unreferenced in-job evidence` で恒久的に閉じない。閉じるには targetless bytes を
   `rejected-evidence/attempt-job-result.{bytes,json}` 等へ保全してから retire する必要があり、
   新しい artifact 種・schema・verifier 受理・変異を伴う。本 wave では T9 + M9i で
   「現行挙動を保ち、retire を targetless へ広げない」ことだけを固定した。
2. **B4 — collector 自身の receipt staging crash 残余**: `create_or_verify_json` の
   `os.link` 成功後 `unlink` 前に落ちると `.attempt-failure-receipt.json.create-*` が残り、
   `_manifest` が `create_or_verify_json` の abandoned-stage 回収より前に拒否するため恒久 deadlock。
   本修正で悪化しないが閉じもしない。
3. **B6 — `target_rejected=1` が `JOB_RESULT` を job-staging へ差し戻さない**:
   `attempt-pointer.json` 不一致時に `target-rejection.json` が attempt namespace へ落ち、
   series ありなら恒久拒否される。`tools/pegasus/t126_qualification.sh` の 1 行修正で閉じる。
4. **A4 派生 — retire の事実が receipt / ledger に残らない**: link/unlink window で落ちた attempt の
   final receipt が clean publish のそれと bytes 上区別できない。監査可能性を残すなら
   receipt schema と `expected_ledger_payload` の変更が要る。
