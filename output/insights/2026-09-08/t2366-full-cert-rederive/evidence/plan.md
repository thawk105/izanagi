## 現物確認

指定された次の 3 file のみを参照した。

- [brief.md:1](/home/SFC/tanab/.claude/jobs/b4871f75/tmp/dev-wave-t2366-full-cert-rederive/brief.md:1)
- [paper_story_a2_certification.py:1725](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2366-full-cert-rederive/orchestrator/campaign/paper_story_a2_certification.py:1725)
- [test_paper_story_a2_certification.py:1359](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2366-full-cert-rederive/orchestrator/tests/test_paper_story_a2_certification.py:1359)

現物の非対称は brief の記述どおりである。

- partial v2 は [paper_story_a2_certification.py:4384](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2366-full-cert-rederive/orchestrator/campaign/paper_story_a2_certification.py:4384) で `acquisition_path` を取り、[同:4388](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2366-full-cert-rederive/orchestrator/campaign/paper_story_a2_certification.py:4388) で evidence を読み直す。[同:4428](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2366-full-cert-rederive/orchestrator/campaign/paper_story_a2_certification.py:4428) から `_canonical_partial_report` を再実行し、[同:4433](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2366-full-cert-rederive/orchestrator/campaign/paper_story_a2_certification.py:4433) で report 全体の不一致を拒否する。legacy v1 は [同:4410](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2366-full-cert-rederive/orchestrator/campaign/paper_story_a2_certification.py:4410) の identity-only である。
- `_canonical_partial_report` は [同:2861](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2366-full-cert-rederive/orchestrator/campaign/paper_story_a2_certification.py:2861) から始まり、frozen `raw_results`、`raw_files`、`attempt_root` を [同:2881](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2366-full-cert-rederive/orchestrator/campaign/paper_story_a2_certification.py:2881) で分類し直している。
- full v4 は [同:4437](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2366-full-cert-rederive/orchestrator/campaign/paper_story_a2_certification.py:4437) 以降で report の形、identity、receipt/schema chain、request IDs、固定 field、cell field を検査するだけで、[同:4526](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2366-full-cert-rederive/orchestrator/campaign/paper_story_a2_certification.py:4526) では渡された `evidence` をそのまま返す。`status`、`effects`、正形の `cells` が evidence から導出されたものかは未検査である。
- full report の生成本体は `_collect_command` の [同:4733](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2366-full-cert-rederive/orchestrator/campaign/paper_story_a2_certification.py:4733) から [同:4766](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2366-full-cert-rederive/orchestrator/campaign/paper_story_a2_certification.py:4766) にだけ存在する。driver failure、manifest failure、`collect_results`、例外畳み込み、`source_commit` 付加が一体になっている。
- `materialize` は [同:4531](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2366-full-cert-rederive/orchestrator/campaign/paper_story_a2_certification.py:4531) で validator の戻り値を受け直し、その evidence の receipt bytes を [同:4551](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2366-full-cert-rederive/orchestrator/campaign/paper_story_a2_certification.py:4551) 以降で出力する。したがって validator が canonical evidence を返せば、出力形式を変えず P4 を満たせる。
- `validate_acquisition_bundle` の必要 field は [同:1804](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2366-full-cert-rederive/orchestrator/campaign/paper_story_a2_certification.py:1804) から揃っている。

brief の行番号には軽微なずれがある。

- brief 10 行目の partial 関連行は正確。
- brief 11 行目の full validator 終端 `4528` は、実コード上は `return evidence` の 4526。4527–4528 は空行。
- brief 12 行目の full else 本体は 4733–4766。4767 は `materialize` 呼び出し。
- brief 13 行目の evidence return range は `acquisition_path` も含めるなら 1806 ではなく 1804 から。
- brief 14 行目の synthetic positive は、関数定義が [test_paper_story_a2_certification.py:5274](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2366-full-cert-rederive/orchestrator/tests/test_paper_story_a2_certification.py:5274)。5275 は関数本体の先頭である。

## 設計の選択

採る設計は「full v4 の exact shape を確認した直後に acquisition を読み直し、その canonical evidence を既存 identity/schema 検査、report 再導出、materialized receipt の共通入力にする」である。report は expected で置換せず、完全一致を要求して、受理済みの元 report を従来どおり serialize する。

brief 21 行目の「既存 identity 検査の後に読み直す」より、partial の実際の配置に忠実な射影として、shape 検査の後・identity/schema 検査の前に読み直す。

- 得る保証: 渡された evidence dict だけを full chain に見せかけても、acquisition_path の実体が別 identity／partial chain なら受理されず、検査と出力 receipt が同じ canonical evidence に束縛される。
- 失う保証: malformed v4 入力で従来と同じ検査エラーが最初に選ばれるというエラー優先順位は維持しない可能性がある。受理集合・report bytes・成果物形式の保証は失わない。

(P1)〜(P4) の判断は次のとおり。

- **(P1) 採用（配置を補強）**: `evidence["acquisition_path"]` の実体を `validate_acquisition_bundle` で読み直す。渡された dict は authority としない。読み直しは full exact-shape 確認後、identity/schema 検査前に置く。
- **(P2) 採用**: synthetic positive は現物では 5274–5286。live raw と frozen raw は、未変更 fixture では同じ raw、condition receipt、lock/WAL/claim bytes を読むため、静的には一致する。実走で差が出た場合だけ report 構築を 2418 と同型へ寄せ、期待値は変えない。
- **(P3) 採用**: full canonicalizer の driver/manifest 分岐、`AuthorityError` 再送出、既存例外 tuple の indeterminate 畳み込み、`reason=str(exc)`、成功時の `source_commit` 付加を逐語的に移す。
- **(P4) 採用**: validator から canonical evidence を返す。`materialize` の receipt、manifest、COMPLETE 構築自体は変更しない。

legacy v3 full は読み直しも report 比較も追加せず、現在の identity-only 経路を保つ。legacy v1 partial も変更しない。

## 変更プラン

1. [paper_story_a2_certification.py:4688](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2366-full-cert-rederive/orchestrator/campaign/paper_story_a2_certification.py:4688) の `_indeterminate_report` 直後に `_canonical_full_report(policy, evidence, *, attempt_id, current_pin)` を追加する。

   なぜこの行か: full 固有の indeterminate envelope と現在の full collector 本体の間に置けば、既存処理を移動するだけで済み、partial や schema 定義を動かさない。

   内容は [同:4733](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2366-full-cert-rederive/orchestrator/campaign/paper_story_a2_certification.py:4733) から [同:4766](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2366-full-cert-rederive/orchestrator/campaign/paper_story_a2_certification.py:4766) をそのまま切り出す。`attempt_root` だけは `Path(evidence["attempt_root"])` として得る。partial の対応先は `_canonical_partial_report` の [同:2861](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2366-full-cert-rederive/orchestrator/campaign/paper_story_a2_certification.py:2861)、frozen evidence を分類へ渡す [同:2881](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2366-full-cert-rederive/orchestrator/campaign/paper_story_a2_certification.py:2881)、authority exception を分離する [同:2887](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2366-full-cert-rederive/orchestrator/campaign/paper_story_a2_certification.py:2887) である。

2. [paper_story_a2_certification.py:4720](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2366-full-cert-rederive/orchestrator/campaign/paper_story_a2_certification.py:4720) の `_collect_command` を、partial/full の canonicalizer を選ぶだけの形にする。

   なぜこの行か: partial は既に [同:4729](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2366-full-cert-rederive/orchestrator/campaign/paper_story_a2_certification.py:4729) で canonicalizer を呼んでおり、その直後の full else を同型にできる。

   [同:4728](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2366-full-cert-rederive/orchestrator/campaign/paper_story_a2_certification.py:4728) の既存 authority check と、attempt ID/root の照合は維持する。full else は `_canonical_full_report(policy, evidence, attempt_id=attempt_id, current_pin=args.current_pin)` 一呼び出しへ置換する。

3. [paper_story_a2_certification.py:4437](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2366-full-cert-rederive/orchestrator/campaign/paper_story_a2_certification.py:4437) の full/legacy 共通枝で、[同:4441](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2366-full-cert-rederive/orchestrator/campaign/paper_story_a2_certification.py:4441) の exact report-key 検査後に `canonical_evidence = evidence` を置く。`report_schema == CERTIFICATION_SCHEMA` の場合だけ、`acquisition_path` の文字列性を要求して `validate_acquisition_bundle(policy, acquisition_path, current_pin=report.get("current_pin"))` で上書きする。

   なぜこの行か: partial の「shape/cells → acquisition_path 確認 → 読み直し」という [同:4372](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2366-full-cert-rederive/orchestrator/campaign/paper_story_a2_certification.py:4372)、[同:4384](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2366-full-cert-rederive/orchestrator/campaign/paper_story_a2_certification.py:4384)、[同:4388](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2366-full-cert-rederive/orchestrator/campaign/paper_story_a2_certification.py:4388) の配置に対応し、legacy v3 には I/O を追加しない。

4. 現在の full identity、schema chain、request ID 検査が参照する [paper_story_a2_certification.py:4450](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2366-full-cert-rederive/orchestrator/campaign/paper_story_a2_certification.py:4450)、[同:4465](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2366-full-cert-rederive/orchestrator/campaign/paper_story_a2_certification.py:4465)、[同:4476](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2366-full-cert-rederive/orchestrator/campaign/paper_story_a2_certification.py:4476) の `evidence` を `canonical_evidence` に切り替える。

   なぜこの行か: report 再導出だけ canonical にして既存 identity/schema 検査を forged dict に残す隙間を作らず、partial の canonical chain 検査 [同:4390](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2366-full-cert-rederive/orchestrator/campaign/paper_story_a2_certification.py:4390) と同じ保証にするため。

5. [paper_story_a2_certification.py:4525](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2366-full-cert-rederive/orchestrator/campaign/paper_story_a2_certification.py:4525) の既存 analysis/indeterminate 形検査後、current v4 に限り `_canonical_full_report` で expected を作る。`attempt_id` は `canonical_evidence["attempt_id"]`、`current_pin` は `report["current_pin"]` を渡し、`report == expected` でなければ `CertificationError("certification result differs from evidence re-derivation")` を送出する。最後は `canonical_evidence` を返す。

   なぜこの行か: partial の expected 構築 [同:4428](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2366-full-cert-rederive/orchestrator/campaign/paper_story_a2_certification.py:4428)、全体比較 [同:4431](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2366-full-cert-rederive/orchestrator/campaign/paper_story_a2_certification.py:4431)、専用エラー [同:4433](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2366-full-cert-rederive/orchestrator/campaign/paper_story_a2_certification.py:4433)、canonical return [同:4435](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2366-full-cert-rederive/orchestrator/campaign/paper_story_a2_certification.py:4435) の逐語的な full 射影になる。

6. [paper_story_a2_certification.py:4529](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2366-full-cert-rederive/orchestrator/campaign/paper_story_a2_certification.py:4529) 以下の materialization、certification JSON、manifest、COMPLETE 構築は変更しない。

   なぜこの行か: [同:4531](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2366-full-cert-rederive/orchestrator/campaign/paper_story_a2_certification.py:4531) が validator の戻り値を既に採用しているため、canonical receipt bytes への切替は自動的に反映され、成果物の形を変更する必要がない。

## テストプラン

[test_paper_story_a2_certification.py:2980](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2366-full-cert-rederive/orchestrator/tests/test_paper_story_a2_certification.py:2980) 付近に、partial fixture と並ぶ `_full_materializer_forgery_case` を追加する。

- `_write_receipt_bundle` [同:1359](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2366-full-cert-rederive/orchestrator/tests/test_paper_story_a2_certification.py:1359) で全 driver 成功、full acquisition、valid full raw manifest を作る。
- `validate_acquisition_bundle` で evidence を得る。
- `_canonical_full_report` で正規の `observed-positive` report を作る。
- `_partial_materializer_forgery_case` は failed-driver/partial chain 専用なので流用せず、fixture の責務を混ぜない。

追加する負例は次の 3 node とする。いずれも現行 validator の形・identity 検査を通過できる実体であり、変更後は `match="differs from evidence re-derivation"` で拒否され、tracked destination が存在しないことを確認する。

- `test_full_materializer_rejects_forged_status_from_positive_evidence`: 正規 report の `status` だけを `"observed-positive"` から `"reject"` に変更する。cells/effects/historical context はそのままなので現行コードは通す。
- `test_full_materializer_rejects_forged_effects_from_positive_evidence`: `effects["rr5"]` を正規値から別の finite float へ変更する。現行コードは `effects` が dict であることしか見ないため通す。
- `test_full_materializer_rejects_indeterminate_report_from_full_success_acquisition`: disk 上の acquisition は全 driver 成功のまま、渡す evidence dict の `driver_rcs["rr5"]` だけを 7 に偽造し、それと整合する `"compute driver exited nonzero: {'rr5': 7}"` を理由にした `_indeterminate_report` を渡す。現行コードは通すが、変更後は acquisition の読み直しによって positive expected が得られ、拒否される。この node は P1 の読み直し自体も検査する。

正例は次を維持する。

- [test_paper_story_a2_certification.py:2418](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2366-full-cert-rederive/orchestrator/tests/test_paper_story_a2_certification.py:2418): `evidence["raw_results"]`、`raw_files`、`attempt_root` を使った canonical full report が materialize できる。必要なら `_canonical_full_report(...) == report` と `certification.json == _canonical_json(report)` を追加し、切り出し前後の bytes 同一性を明示する。
- [同:5274](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2366-full-cert-rederive/orchestrator/tests/test_paper_story_a2_certification.py:5274): synthetic PBS-free positive をそのまま通す。brief の「5275」は定義行としては 1 行ずれている。
- [同:3331](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2366-full-cert-rederive/orchestrator/tests/test_paper_story_a2_certification.py:3331) と `_materialization_case` 利用 node [同:3395](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2366-full-cert-rederive/orchestrator/tests/test_paper_story_a2_certification.py:3395)、[同:3431](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2366-full-cert-rederive/orchestrator/tests/test_paper_story_a2_certification.py:3431)、[同:3455](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2366-full-cert-rederive/orchestrator/tests/test_paper_story_a2_certification.py:3455)、[同:3477](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2366-full-cert-rederive/orchestrator/tests/test_paper_story_a2_certification.py:3477)、[同:3499](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2366-full-cert-rederive/orchestrator/tests/test_paper_story_a2_certification.py:3499) も canonical frozen inputs を使うため、そのまま緑でなければ実装誤りである。
- cross-chain 負例 [同:2947](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2366-full-cert-rederive/orchestrator/tests/test_paper_story_a2_certification.py:2947) は、同じ `SchemaChainError` と既存 message match を保つ。

既存 test の破損分類は次のとおり。

- **report 構築が collector と違う型**: 候補は 5274 のみ。現在は [同:5280](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2366-full-cert-rederive/orchestrator/tests/test_paper_story_a2_certification.py:5280) で `load_raw_results` を使い、`frozen_files` と `attempt_root` を省略している。静的には同じ未変更 bytes を読むため一致見込み。もし再導出差だけで赤なら、2418 の [同:2426](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2366-full-cert-rederive/orchestrator/tests/test_paper_story_a2_certification.py:2426) と同じ構築へ寄せる。status や成果物期待値は変えない。
- **実装の誤り型**: 2418、3331、3395、3431、3455、3477、3499、および 5274 を canonical 構築へ寄せた後の失敗。これらが赤なら、full helper の切り出し、source_commit 付加、例外畳み込み、canonical evidence の選択のいずれかが旧 collector と違うため、テストは変更せず実装を直す。
- `_COLLECT_TEST_TOKEN` を使う 2106、2150、2446、3544、3558、4043 の各 test は materialize へ進まないため、破損対象ではない。

sandbox 指示に従い pytest は実行せず、ここでは静的検査のみとする。

## 変異の候補

- **report 再導出そのものを外す変異**

  old:

  ```python
  expected = _canonical_full_report(
      policy, canonical_evidence,
      attempt_id=canonical_evidence["attempt_id"],
      current_pin=report["current_pin"])
  ```

  replacement:

  ```python
  expected = report
  ```

  期待 KILL node: 上記 3 件の `test_full_materializer_rejects_*`。特に status と effects の偽造で確実に赤になる。

- **acquisition の読み直しを外す変異**

  old:

  ```python
  canonical_evidence = validate_acquisition_bundle(
      policy, acquisition_path, current_pin=report.get("current_pin"))
  ```

  replacement:

  ```python
  canonical_evidence = evidence
  ```

  期待 KILL node: `test_full_materializer_rejects_indeterminate_report_from_full_success_acquisition`。渡された偽 `driver_rcs` を信じると indeterminate report と一致してしまうためである。

- **過剰拒否の変異**

  old:

  ```python
  if not report_matches_rederived_evidence:
  ```

  replacement:

  ```python
  if True:
  ```

  期待 KILL node: `test_p2_a6_full_v3_path_collects_and_materializes` と `test_synthetic_pbs_free_preregister_through_analyze_positive`。加えて 3331 と `_materialization_case` 系の正例も赤になる。

- **等価変異**

  old:

  ```python
  report_matches_rederived_evidence = report == expected
  ```

  replacement:

  ```python
  report_matches_rederived_evidence = expected == report
  ```

  期待結果: SURVIVED。full exact-shape 検査後の `report` と canonicalizer の戻り値はいずれも dict であり、比較方向を変えても意味は変わらない。

## 残る限界

- legacy v3 full と legacy v1 partial は、要求どおり identity-only のままであり、report 全体の再導出保証を持たない。
- 保証の根は既存の acquisition、completion、manifest、WAL、claim、source authority 検査である。それらより上流の信頼モデルや暗号学的真正性は強化しない。
- `collect_results` や `_canonical_full_report` の戻り値を materialize せず直接消費する呼び手には、この最終一致検査は働かない。
- current v4 の report schema、status 語彙、例外から indeterminate への既存畳み込み規則自体は変更しない。
- 新しい gate、schema version、台帳、一般化、publication 後の再監査は追加しない。

## 総括

full v4 にだけ、partial v2 と同じ acquisition 読み直し・canonical report 再生成・report 全体一致を追加する。  
full collector 本体は `_canonical_full_report` へ逐語的に切り出し、report bytes と例外畳み込みを維持する。  
legacy 経路と成果物形式は触らず、受理集合は evidence と一致しない v4 report の分だけ縮小する。  
3 件の具体的偽造負例、既存正例、読み直し・比較・過剰拒否・等価の変異で境界を固定する。