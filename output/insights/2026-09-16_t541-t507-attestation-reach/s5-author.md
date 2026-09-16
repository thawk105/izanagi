## 実装前の現行挙動

実装前の静的確認: `_attest` は `compare_profiles` の expected に `CalibrationV2` を渡しており、一致観測も `AttestationError`（expected が AttestationProfile でない）を QualificationDriverError で包装して拒否する。受理集合は空。層 1 だけを直しても、return 内の expected 専用 `profile_sha256(observed)` が観測型を拒否する。後者は旧実装では例外包装の外側だった。空 comparisons・一行でも非 pass の拒否は既存条件である。

追加で判明した計画入力の矛盾: `test_schema_v2._valid_document()` の `effective_clock.tolerance_pct` は 5.0。一方、実 `_recorded_verdict` は現行 `EFFECTIVE_CLOCK_TOLERANCE_PCT = 2.0` との一致を要求する。このため、指定どおりの fixture を無変更で使うと、二層修正後も clock 行は fail し、一致受理例は成立しない。新設テスト内の入力だけを 2.0 に揃える可否を非同期質問したが、本報告時点で未回答。共有 fixture・実較正・判定条件は変更していない。

## 変更した file と内容

- `orchestrator/qualification/t126_driver.py`: `_attest` のみ変更。expected を `.calibration.attestation_profile` に変更。probe 完了後の epoch を含む exact 4 key v2 JSON を実 parser に通し、比較と observed hash は同じ parsed 値を使用する。変換・parse・比較・hash は既存例外包装内。envelope は exact 6 field の v2 とし、projection schema は `parsed.schema_version`。全行 pass・非空条件を維持。
- `orchestrator/tests/test_t126_qualification_driver.py`: 旧現挙動保存テストを実 VerifiedCalibration と実比較/parser/hash による受理・governor mismatch・clock 上下端/直外・probe 例外・空 comparisons の境界テストへ置換。較正読込みと probe の二つだけを置換し、空 comparisons 専用ケースだけ比較 stub を追加。観測 hash は観測 fixture mapping の標準 json/hashlib から独立算出。21 field を明示列挙。**入力 tolerance の矛盾が未解決のため、テストは未完成の草稿。現状の受理例・端値例は実走しても拒否される見込みであり、mismatch 例の単一理由性も未成立。**
- `output/insights/2026-09-16_t541-t507-attestation-reach/attest.sh`: NQSV gen_S / SFC / 5 分の最小 job script。絶対 worktree root を cwd とし python3.10 で `_attest` を一回だけ直接呼ぶ。実行時の calibration_ref・contract hash・HEAD・host・job ID を先に stdout へ flush し、成功 payload を stdout に出す。例外は traceback と非ゼロ終了をそのまま残す。世代の決め打ち・較正変更はない。未投入。

`-o` の出力先が会話に提示されていないため、本報告は上記 output ディレクトリの `s5-author.md` に保存した。commit・git add・ブランチ操作・docs 編集はしていない。

## 実走した検査 (nodeid と範囲)

pytest の緑は **0 nodeid**。検査子が起動せず、テスト結果は得られていない。

実走して通過した静的検査:

- `bash -n output/insights/2026-09-16_t541-t507-attestation-reach/attest.sh`
- 標準 `ast.parse` による driver・対応テスト・job 内 Python の構文確認。
- `git diff --check`（driver と対応テストの追跡差分）。

## 実走できなかったもの

次の二呼出しは `python3.10 tools/run_tests.py` 経由で試行したが、共に rc=16、child_started=false。NQSV `qstat -Q` の `NQSconnect: [API EACCTAUTH] Unknown user-id. (uid: 31609, errno: 1)` により preflight が失敗した。qsub/qlogin は実行されておらず、検査の成功・失敗は判定できない。保護経路を迂回する pytest 直接起動はしていない。

1. `orchestrator/tests/test_t126_qualification_driver.py -k t541 -v`
   対象 nodeid（共通 prefix: `orchestrator/tests/test_t126_qualification_driver.py::`）:
   - `test_t541_attest_accepts_matching_profile_with_v2_envelope`
   - `test_t541_attest_rejects_governor_mismatch`
   - `test_t541_attest_clock_band_boundary[endpoint-lower]`
   - `test_t541_attest_clock_band_boundary[endpoint-upper]`
   - `test_t541_attest_clock_band_boundary[just-outside-lower]`
   - `test_t541_attest_clock_band_boundary[just-outside-upper]`
   - `test_t541_attest_wraps_probe_exception`
   - `test_t541_attest_rejects_empty_comparisons`
   parameter ID はソースからの列挙であり、収集実走による確認ではない。
2. 制約 meta-test を検索して次の三つを選び、同時に試行:
   - `orchestrator/tests/test_acceptance_schedule_order.py::test_g5_real_ledger_covers_at_least_90_percent_of_real_collection`
   - `orchestrator/tests/test_acceptance_schedule_order.py::test_g6_all_real_repo_items_stay_one_unit_and_keep_relative_order`
   - `orchestrator/tests/test_real_repo_serialization.py::test_real_repo_group_collection_exactly_matches_canonical_nodes`

検索範囲は `orchestrator/tests` の命名/prefix/重複名・collection・nodeid 参照と conftest。対象モジュール固有の命名 meta-test は見つからなかった。旧テスト名を参照する Python consumer も見つからなかった。台帳被覆・収集群と相対順序の制約は上記に該当する。

失敗 receipt:
- `output/pegasus-dispatch/a27e7654da836b1ea6da6010f2d5abb2/receipt.json`
- `output/pegasus-dispatch/5a65b29e839d3e64f38927f920be57ca/receipt.json`

対応テスト全体、共有 attestation テスト、consumer suite、全受入、変異検査、計算ノード実データ受理は未実走。check_codex_agents/check_docs/provenance も実走していない。commit は親の担当であり作っていない。親の段 6 の実走を代替しない。

## 波及可能性の静的列挙

- driver 内ローカル `attest` caller は `_attest` の payload に stage/round_index を加え、capability 経由で保存する。保存時は 8 field。汎用 JSON 読戻しと file_record、最終 evidence_manifest による bytes 参照が存在する。未使用の attestation_records list を根拠に「保存先がない」とは扱わない。
- repo 内 Python 検索で attestation envelope の版別解釈 consumer は見つからない。外部 consumer が v1/exact 5 field を仮定する場合は v2/6 field（保存時 8 field）への追随が必要となりうる。共有 env_attestation の signature・意味は変更なし。
- ident / artifact_admission → contract_loader_binding の live 経路は HEAD/disk の一致を要求する。未 commit の driver 差分で先行拒否しうる。fixture に現行 hash を埋めて回避していない。
- b10_backoff_shape_locks の balanced/read-heavy/write-heavy .campaign.lock と `test_b10_backoff_shape_sweep.py` は記録 commit の blob と比較する。三共有 fixture は無変更で、現行 driver の hash への更新は不要。
- `test_t126_qualification_driver.py` の prologue/member callsite AST pin と build context source pin は対象外部分を維持。`test_t126_pegasus_tools.py` の M4a node 参照は従来テスト名のまま維持。
- `test_env_attestation.py` の parser/projection/hash 契約、qualification artifacts/series/pegasus tools、campaign pipeline、live loader binding の consumer テストは関連回帰範囲。未実走。
- `test_schema_v2._valid_document` は共有されているため変更していない。新テスト増加・改名は acceptance_duration_ledger の既知 node 比率と収集群の制約に波及する可能性があり、台帳更新なしで meta-test を試行したが未起動。

## scope 外として実装しなかったもの

1. [T-506]/D155 loader 自己整合 gate。一次裁定は同 wave で扱うと述べていたが、本 wave の引数で scope 外となった。carry は残る。
2. 拒否時の比較行の保存・伝達（R-2）。既存の欠落であり、本変更には追加しない。
3. 計算ノードでも mismatch した場合の較正世代 [T-419] U-2 の扱い。実測も field 別根拠もないため帰属しない。

新 gate・検査機構・台帳・互換層・schema 定義・共有 API 変更は追加していない。D96 の新 D と worklog は親の段 7 の担当。全 qualification の完走、attempt evidence 保存の実証、certified 選択の成立は本 script の証明範囲に含めない。

## 総括

**driver と job script は実装済み・未実走。境界テストは入力矛盾の確認待ちで未完成。closed ではない。** 新設テスト内の較正入力だけを現行 2.0 に揃える可否が次の判断点である。実データ accepted は未達・未測定であり、計算ノードなら一致するという見込みは主張しない。
