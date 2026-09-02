## 検査した範囲

- 指定された handoff、stage 6 patch、実装子申告、D1374、D1377、D19 を全文確認した。
- 変更 6 ファイル、全 `build_report` / `render` / acceptance 呼び手、`_campaign` 利用箇所、`validate_calibration_v2` consumer、全 `_assemble_v2` 呼び手を静的追跡した。
- 実在 calibration を production helperへ read-only で通した。pytest は実行していない。
- 既知の `parents[3]` による二重 `output` は real 所見へ数えていない。

## real 所見

1. **v2 の任意 `output_root` に pin artifact が存在するという新前提を、既存 consumer が満たしていない。**  
   `orchestrator/campaign/layer3_report.py:447-449` は v2 pin を照合条件に関係なく必ず strict 解決する。一方、`orchestrator/tests/test_autonomous_trial_completeness.py:3551-3620,3778-3780` は `<tmp>/output` に v2 campaign を作るが calibration を複製しない。この形では repo-root 深さは正しく解決されるため、既知の二重 `output` とは別に「pin file 不在」で硬直する。実運用の exploration も `orchestrator/campaign/p3_autonomous_workload_trial.py:2844-2848` が `<base>/exploration` を渡す一方、`orchestrator/campaign/layout.py:580-596` は campaign directories しか作らず `exploration/env/...` を作らない。  
   **放置時:** v2 exploration、trial-registry、autonomous completeness の受理集合が「floor 不一致なら report を出す」から「pin file 不在で report 自体を出さない」へ狭まり、親指定の suffix 修正後も解消しない。

2. **qualification の変更対象外 fixture は v2 authority と WAL `env_tag` が不一致で、正例が拒否される。**  
   `orchestrator/tests/test_t126_qualification_artifacts.py:325-332` は既定の `build_v2_lock` と `env_tag="test-env"` を組み合わせる。既定 authority は `orchestrator/tests/campaign_lock_test_support.py:29-30` の linux-baremetal であり、新経路は `orchestrator/campaign/layer3_report.py:351-354` で `expected_env_tag="test-env"` として拒否する。`test_m2_normal_formal_campaign_remains_accepted` (`test_t126_qualification_artifacts.py:375-381`) が影響対象。  
   **放置時:** 正常な formal-shaped qualification fixture が layer 3 の受理集合から外れ、期待される `layer3-material-report/v3` は生成されない。

3. **receipt 由来 genome の根拠語が、matching floor の成果物へ出力されない。**  
   `_floor_protocol_and_basis` は `receipt-derived-build-argv` を返すが、`orchestrator/campaign/layer3_report.py:531-544` は一致時に `genome-absent-legacy-record` だけを出力する。さらに現行 schema は `orchestrator/campaign/layer3_schema.json:255-258` で同 legacy literal しか許さない。追加試験も `orchestrator/tests/test_layer3_report.py:3191-3240` で helper と mismatch details だけを検査し、matching certified record を検査していない。  
   **放置時:** 新しい certified calibration の数値と source SHA は入るが、成果物から `receipt-derived-build-argv` が欠落し、canonical producer genome と receipt 由来 genome の参照根拠を下流が区別できない。

## refuted 所見

- **pin-only 化で Linux skew=0 が消える:** refuted。直下集合が維持され、CV `0.004726195977018071` を保持した。
- **registered 全 glob により Pegasus g1/g2 が衝突する:** refuted。追加候補は active g1 pin のみ。
- **`CalibrationV2.genome=None` が既存 consumer を壊す:** refuted。production consumer は `env_tag`、clock、profile、saturation 等だけを使用し、`.genome` を参照する既存箇所や直接 `CalibrationV2(...)` を構築する箇所はない。
- **非 certify 経路が signature 変更で壊れる:** refuted。`_assemble_v2` の全 3 呼び手は certify 内で更新済み。非 certify は `result_to_dict` を直接書き、genome 不在を維持する。
- **certify の basename / target 決め打ちが現 launcher を拒否する:** refuted。唯一の認定 launcher は `ycsb_silo.exe` と `--target ycsb_silo.exe`、単一 `&&` を生成する。既存 registered 2 件の receipt も新 helperで同一 canonical genomeを導出できた。
- **共有 `_campaign` 自体の WAL env 不整合:** refuted。既定 authority、`_record` の既定 `env_tag` はともに linux-baremetalへ揃い、test-env symlinkも作られる。pre-existing 利用テストは 84 件で、11 件に局所調整、73 件は未変更。影響を受けやすいのは floor 検索群、accepted-report 群、external/output-root 群、persisted-report 比較群だが、親提供の焦点走では同ファイル 187 件が通っている。
- **実装子の不変申告:** 確認できた。変更は申告どおり 6 ファイルのみ。docs、`layer3_schema.json`、launcher、between-run producer、activation、registered 2 件は未変更。registered SHA は `753f535a...` / `94a4b79f...` のまま。
- **既存 D1374 期待値の改変:** refuted。既存 `genome-absent-legacy-record` assertion は変更されていない。

## 呼び手ごとの挙動表

| 呼び手 | `output_root` の形 | v1 / v2 の挙動 |
|---|---|---|
| layer 3 CLI / default render | `<repo>/output` | v1 は直下のみ。v2 は global pin が存在し、Pegasus g1を追加できる |
| `test_layer3_report._campaign` | `<tmp>/repo/output` | v2 authorityとpinを新 helperが複製するため成立 |
| P3 autonomous producer | `<base>/exploration` | 現在は既知の二重 `output` 赤。suffix 修正後も local pin不在で real 1 が残る |
| autonomous completeness / trial registry | `<tmp>/output` または nested exploration root | v1 は従来どおり。v2 は pinを複製しない fixtureで real 1 |
| T126 qualification formal fixture | `<tmp>/repo/output` | v2 authority=linux-baremetal、WAL=test-env のため real 2 |
| acceptance API | caller指定 root | `build_accepted_report` が同じ `build_report` を呼ぶ。production consumerはまだ無く、`_campaign` ベースの試験はpin複製済み |
| v1 campaign 全般 | 任意の既存 root | authorityが `None` なので新 pin 解決を通らず、直下走査を維持 |

実在データでの結果:

| 環境・lock・workload | within-run 出力 | between-run 出力 |
|---|---|---|
| Pegasus v2、skew=0.9 / rr50 | g1 CV `0.011705837968885854`、`registered/calibration-753f...json`、legacy basis | 一致なし |
| Pegasus v1、skew=0.9 / rr50 | `no-matching-env-record` | 一致なし |
| Linux v2、skew=0 | CV `0.004726195977018071`、直下 skew0 record | 一致なし |
| Linux v2、skew=0.9 | CV `0.02280630204206476`、直下 skew0.9 record | CV `0.010671892063164597` |
| Linux v1、skew=0 | v2 と同じ `0.004726195977018071` | 一致なし |
| Linux v1、skew=0.9 | v2 と同じ `0.02280630204206476` | CV `0.010671892063164597` |

## nit

- `orchestrator/tests/test_layer3_report.py:269-276` の `_copy_contract_calibration` も `output_root.parent / ref.path` として `<repo>/output` 形を前提にする。test-only だが nested exploration rootを再現できず、real 1を覆い隠す。
- `direct_paths` の `.resolve()` 導入で、直下 JSON symlink の source path挙動は従来と変わる。ただし既存 calibration直下に該当 symlinkはなく、現時点の成果物影響は確認できない。
- `calibration_dir.parents[2]` による source相対化は既存コード由来で、今回新規の固定深さ前提ではない。

## 総括

既知の `parents[3]` 赤を除いて real は3件。数値面では M8 の中心要件を満たし、Linux v2 skew=0 は実在 CVを保持している。

ただし、任意 `output_root` でのpin materialization、qualification fixtureのauthority整合、matching certified floorへの根拠語出力が未完である。特に親指定のpath suffix修正だけでは real 1が残るため、このままでは回帰閉鎖にならない。