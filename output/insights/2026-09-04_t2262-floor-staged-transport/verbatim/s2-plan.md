## 実測した機構

静的検査のみ実施した。pytest は実走していない。

親 brief の erratum 8 行は次のとおり照合した。

| # | 判定 | コード上の事実 |
|---|---|---|
| 1 | 追認 | [submit_floor.sh:621](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2262-floor-staged-transport/tools/pegasus/submit_floor.sh:621) が `IZANAGI_SUBMISSION_NONCE=$NONCE` を組み、[同:633](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2262-floor-staged-transport/tools/pegasus/submit_floor.sh:633) から [同:635](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2262-floor-staged-transport/tools/pegasus/submit_floor.sh:635) が `qsub -v` へ渡す。 |
| 2 | 追認 | job は bootstrap の [floor_campaign.sh:41](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2262-floor-staged-transport/tools/pegasus/floor_campaign.sh:41) と submit binding の [同:547](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2262-floor-staged-transport/tools/pegasus/floor_campaign.sh:547) で exact 32 桁小文字 hex を要求する。receipt の nonce とも [同:647](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2262-floor-staged-transport/tools/pegasus/floor_campaign.sh:647) で一致を検査する。 |
| 3 | 追認 | [floor_campaign.sh:971](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2262-floor-staged-transport/tools/pegasus/floor_campaign.sh:971) が検証済み submission nonce を `IZANAGI_RESERVATION_NONCE` へそのまま export する。 |
| 4 | 追認 | driver が import する checkpoint module は [floor_job_checkpoint.py:474](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2262-floor-staged-transport/orchestrator/campaign/floor_job_checkpoint.py:474) から環境を取り、[同:486](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2262-floor-staged-transport/orchestrator/campaign/floor_job_checkpoint.py:486) で reservation nonce を読む。同 module の正規表現も [同:33](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2262-floor-staged-transport/orchestrator/campaign/floor_job_checkpoint.py:33) で 32 桁小文字 hex 固定。 |
| 5 | 未追認 | `certified_writer_admission.py` は必読射影に含まれていないため読んでいない。この行は導出可能性の必要条件ではなく、1、2、3、6、8 の追認結果には影響しない。 |
| 6 | 追認 | job の `OUTPUT_ROOT` と固定 attempts root は [floor_campaign.sh:280](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2262-floor-staged-transport/tools/pegasus/floor_campaign.sh:280) から [同:282](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2262-floor-staged-transport/tools/pegasus/floor_campaign.sh:282)、submission leaf は [同:552](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2262-floor-staged-transport/tools/pegasus/floor_campaign.sh:552)。submitter の `--attempts-root` 分岐は存在するが、実 submission では override を [submit_floor.sh:72](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2262-floor-staged-transport/tools/pegasus/submit_floor.sh:72) から [同:75](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2262-floor-staged-transport/tools/pegasus/submit_floor.sh:75) が拒否する。production は [同:277](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2262-floor-staged-transport/tools/pegasus/submit_floor.sh:277) から [同:284](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2262-floor-staged-transport/tools/pegasus/submit_floor.sh:284) の固定 root になる。 |
| 7 | 追認 | payload root は [floor_campaign.sh:716](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2262-floor-staged-transport/tools/pegasus/floor_campaign.sh:716) の `$SUBMISSION_DIR/masstree-payload`。 |
| 8 | 追認 | job の root は [floor_campaign.sh:46](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2262-floor-staged-transport/tools/pegasus/floor_campaign.sh:46) の `$PBS_O_WORKDIR`。driver は同 root 下の file を [同:1227](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2262-floor-staged-transport/tools/pegasus/floor_campaign.sh:1227) で直接起動し、Python 側の `ROOT` は [s8b_floor_campaign.py:84](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2262-floor-staged-transport/orchestrator/campaign/s8b_floor_campaign.py:84) から [同:87](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2262-floor-staged-transport/orchestrator/campaign/s8b_floor_campaign.py:87) の `__file__` 由来。同一 checkout である。 |

したがって、親 brief の初稿 [brief.md:41](/work/1/SFC/tanab/dev-wave-jobs/t2262-floor-staged-transport/brief.md:41) から [同:42](/work/1/SFC/tanab/dev-wave-jobs/t2262-floor-staged-transport/brief.md:42) は誤りで、erratum の固定式は production について追認できる。

現状は二段階のコピーになっている。

- submitter は persistent third-party source を submission payload へ検査付きでコピーする。[submit_floor.sh:396](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2262-floor-staged-transport/tools/pegasus/submit_floor.sh:396) から [同:506](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2262-floor-staged-transport/tools/pegasus/submit_floor.sh:506) の処理であり、これは残す。
- job script は submission payload を `$TMPDIR/izanagi-floor-fetchcontent` へ [floor_campaign.sh:697](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2262-floor-staged-transport/tools/pegasus/floor_campaign.sh:697) から [同:721](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2262-floor-staged-transport/tools/pegasus/floor_campaign.sh:721) で再コピーし、その path を [同:1231](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2262-floor-staged-transport/tools/pegasus/floor_campaign.sh:1231) から caller seam として渡す。移す対象はこちらである。

driver の現状では、`None` は [s8b_floor_campaign.py:2990](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2262-floor-staged-transport/orchestrator/campaign/s8b_floor_campaign.py:2990) から [同:3038](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2262-floor-staged-transport/orchestrator/campaign/s8b_floor_campaign.py:3038) で空の `mkdtemp` を作る。さらに [同:3234](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2262-floor-staged-transport/orchestrator/campaign/s8b_floor_campaign.py:3234) から [同:3273](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2262-floor-staged-transport/orchestrator/campaign/s8b_floor_campaign.py:3273) は、`None` のとき source-dir を渡さず prebuild する。この経路が外部取得へ落ちうる legacy 既定である。

一方、既存 staged 検査は [s8b_floor_campaign.py:2570](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2262-floor-staged-transport/orchestrator/campaign/s8b_floor_campaign.py:2570) から [同:2787](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2262-floor-staged-transport/orchestrator/campaign/s8b_floor_campaign.py:2787) にあり、3 source の non-symlink、Git top-level、policy pin、dirty・untracked・ignored 状態を検査する。prebuild は3つの explicit source-dir を [buildcache.py:2035](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2262-floor-staged-transport/orchestrator/campaign/buildcache.py:2035) から [同:2051](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2262-floor-staged-transport/orchestrator/campaign/buildcache.py:2051) で CMake へ渡せる。後段 build は post-oracle binding があると [同:1948](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2262-floor-staged-transport/orchestrator/campaign/buildcache.py:1948) から [同:1971](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2262-floor-staged-transport/orchestrator/campaign/buildcache.py:1971) で `FETCHCONTENT_FULLY_DISCONNECTED` も付く。

親 brief と区別すべき点として、現 HEAD には staged transport 以外にも official の独立 blocker がある。public/core の `_assert_official_permitted` は [s8b_floor_campaign.py:7038](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2262-floor-staged-transport/orchestrator/campaign/s8b_floor_campaign.py:7038) から [同:7044](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2262-floor-staged-transport/orchestrator/campaign/s8b_floor_campaign.py:7044) と [同:7140](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2262-floor-staged-transport/orchestrator/campaign/s8b_floor_campaign.py:7140) に残り、CLI も [同:8433](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2262-floor-staged-transport/orchestrator/campaign/s8b_floor_campaign.py:8433) から [同:8440](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2262-floor-staged-transport/orchestrator/campaign/s8b_floor_campaign.py:8440) で official を無条件拒否する。正規 job も [floor_campaign.sh:1228](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2262-floor-staged-transport/tools/pegasus/floor_campaign.sh:1228) では pilot 固定である。本プランが解くのは transport 固有の blocker であり、現 HEAD 全体を直ちに official 実走可能にはしない。

## 導出規則の確定

規則は次の1つに固定する。

```text
nonce = os.environ["IZANAGI_SUBMISSION_NONCE"]
payload_root =
  ROOT / "output/env/pegasus/floor/attempts/submissions"
       / nonce
       / "masstree-payload"
staging_base =
  canonical TMPDIR / "izanagi-floor-fetchcontent"
```

`nonce` は driver 側でも `re.fullmatch(r"[0-9a-f]{32}", nonce)` で再検査する。32 桁小文字 hex は `/`、`.`、path separator、NUL、絶対 path prefix をすべて排除するため、nonce からの traversal・別 root 選択はできない。ただし固定 prefix の symlink 化、payload leaf の交換、内容の改変までは防がないため、non-symlink 検査と既存 pin・clean 検査は省けない。

この規則を採る理由は、real submission では attempts-root override が禁止され、job と driver の checkout root が一致し、nonce が receipt に束縛されるためである。`IZANAGI_RESERVATION_NONCE` を読む案も同値だが、payload namespace の直接 producer が qsub で渡す `IZANAGI_SUBMISSION_NONCE` なので、余分な alias を導出式へ入れない。

新 env 変数は作らない。`IZANAGI_FLOOR_JOB_STAGING` や checkpoint path から逆算する案は submission namespace と無関係なので落とす。directory 走査、最新 submission の探索、候補列挙も、入力経路を暗黙に増やすため採らない。

scratch への `cp -a` は driver へ移す。job script に残すと、argv seam は消せても「job が作る固定 scratch path を driver が暗黙に知る」という producer/consumer 合意が残る。driver が source の導出、destination の作成、コピー、pin 検査まで所有すれば、その合意を1箇所へ閉じられる。

`_canonical_floor_fetchcontent_base(None)` の legacy 分岐は削除する。`None` を「空 base」ではなく上記 default staged transport と定義し直し、production・private helper のどちらからも base-only 外部取得へ入れない。

CLI の `--fetchcontent-base-dir` は pilot 専用 seam として残す。[s8b_floor_campaign.py:8235](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2262-floor-staged-transport/orchestrator/campaign/s8b_floor_campaign.py:8235) で parse され、non-`None` は [同:6941](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2262-floor-staged-transport/orchestrator/campaign/s8b_floor_campaign.py:6941) で不適格 seam になる。public official は [同:7038](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2262-floor-staged-transport/orchestrator/campaign/s8b_floor_campaign.py:7038) から [同:7042](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2262-floor-staged-transport/orchestrator/campaign/s8b_floor_campaign.py:7042) で副作用前に拒否する。現 CLI ではその前に official 全体の拒否も発火する。

## 変更プラン

1. [s8b_floor_campaign.py:184](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2262-floor-staged-transport/orchestrator/campaign/s8b_floor_campaign.py:184) から [同:194](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2262-floor-staged-transport/orchestrator/campaign/s8b_floor_campaign.py:194) に、既存 nonce env 名、固定 submission prefix、`masstree-payload`、固定 scratch leaf 名を定数化する。導出式を一意にし、探索を実装できない形にするため。

2. [s8b_floor_campaign.py:2986](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2262-floor-staged-transport/orchestrator/campaign/s8b_floor_campaign.py:2986) 付近に driver-owned staging helper を置き、`None` 分岐を置換する。payload root と3 source は `lstat` 相当で directory かつ non-symlink、destination は `os.path.lexists` で事前不在、base は exclusive `mkdir`、各コピーは exact `cp -a -- source destination`、コピー後も destination が non-symlink directory であることを検査する。

3. 同 helper は `$TMPDIR/izanagi-floor-fetchcontent` 以外を default destination にせず、既存なら拒否する。失敗を別 base、legacy、network へフォールバックさせず、既存 `_FloorOraclePreflightError` 系へ閉じて返す。job-local `TMPDIR` 自体は [floor_campaign.sh:269](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2262-floor-staged-transport/tools/pegasus/floor_campaign.sh:269) から [同:274](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2262-floor-staged-transport/tools/pegasus/floor_campaign.sh:274) の create-only 契約を維持する。

4. [s8b_floor_campaign.py:3201](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2262-floor-staged-transport/orchestrator/campaign/s8b_floor_campaign.py:3201) から [同:3273](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2262-floor-staged-transport/orchestrator/campaign/s8b_floor_campaign.py:3273) の `_prepare_floor_oracle_dependency` から `None`/base-only 分岐を除く。常に `_verify_pristine_floor_dependency_sources` を通し、常に masstree・mimalloc・googletest の explicit source-dir を prebuild へ渡し、binding の transport mode を `source-dir` にする。これが pin 検査と外部取得禁止を担う。

5. [s8b_floor_campaign.py:4127](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2262-floor-staged-transport/orchestrator/campaign/s8b_floor_campaign.py:4127) から [同:4144](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2262-floor-staged-transport/orchestrator/campaign/s8b_floor_campaign.py:4144) を一本化する。raw `fetchcontent_base_dir` が `None` なら driver default を stage、非 `None` なら pilot seam を canonicalize し、どちらも同じ staged検査・prebuild へ渡す。seam 分類後の build 内部で実体化するため、default path は `fetchcontent_base_dir` seam として数えない。

6. [floor_campaign.sh:697](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2262-floor-staged-transport/tools/pegasus/floor_campaign.sh:697) から [同:721](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2262-floor-staged-transport/tools/pegasus/floor_campaign.sh:721) の scratch staging function・phase・呼出しを削除し、[同:1231](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2262-floor-staged-transport/tools/pegasus/floor_campaign.sh:1231) の CLI seam 追加も削除する。job は mode と protocol だけを渡し、payload transport を driver default に委ねる。

7. [submit_floor.sh:396](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2262-floor-staged-transport/tools/pegasus/submit_floor.sh:396) から [同:517](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2262-floor-staged-transport/tools/pegasus/submit_floor.sh:517) は変更しない。これは login node で pinned-clean source を submission payload に発行する前段で、driver がコピー元として必要とする。

8. [s8b_floor_contract.py:42](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2262-floor-staged-transport/orchestrator/campaign/s8b_floor_contract.py:42) から [同:50](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2262-floor-staged-transport/orchestrator/campaign/s8b_floor_contract.py:50)、[s8b_floor_campaign.py:6918](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2262-floor-staged-transport/orchestrator/campaign/s8b_floor_campaign.py:6918) から [同:6967](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2262-floor-staged-transport/orchestrator/campaign/s8b_floor_campaign.py:6967) は literal 無変更とする。default は raw argument `None` のまま分類されるため、official・fresh・非既定 seam ゼロだけが真という意味を変えない。

## テスト計画

**新設**

- `orchestrator/tests/test_s8b_floor_campaign.py::test_floor_fetchcontent_default_derives_fixed_payload_and_copies_three_sources`  
  nonce と `ROOT` から exact payload root を導出し、固定 TMPDIR leaf へ3 source を `cp -a` することを検査する。

- `orchestrator/tests/test_s8b_floor_campaign.py::test_floor_fetchcontent_default_rejects_invalid_submission_nonce[missing]`
- `...::test_floor_fetchcontent_default_rejects_invalid_submission_nonce[uppercase]`
- `...::test_floor_fetchcontent_default_rejects_invalid_submission_nonce[path-separator]`  
  32 桁小文字 hex 以外から path が作られないことを検査する。

- `orchestrator/tests/test_s8b_floor_campaign.py::test_floor_fetchcontent_default_rejects_unsafe_layout[payload-symlink]`
- `...::test_floor_fetchcontent_default_rejects_unsafe_layout[staging-exists]`
- `...::test_floor_fetchcontent_default_rejects_unsafe_layout[staging-symlink]`
- `...::test_floor_fetchcontent_default_rejects_unsafe_layout[masstree-missing]`
- `...::test_floor_fetchcontent_default_rejects_unsafe_layout[mimalloc-missing]`
- `...::test_floor_fetchcontent_default_rejects_unsafe_layout[googletest-missing]`
- `...::test_floor_fetchcontent_default_rejects_unsafe_layout[source-symlink]`  
  shell から移す全構造検査を1件ずつ固定する。

- `orchestrator/tests/test_s8b_floor_campaign.py::test_floor_default_transport_verifies_pins_and_passes_all_source_dirs`  
  コピー後に既存3-pin・clean 検査が走り、prebuild argv が3つの source-dir を持つことを検査する。

- `orchestrator/tests/test_s8b_floor_campaign.py::test_default_staged_transport_is_not_counted_as_refreeze_seam`  
  default staging 後も捕捉済み seam 集合は空、fresh official は true、pilot は false であることを固定する。

**改訂**

- `test_floor_fetchcontent_base_uses_explicit_seam_or_job_unique_tmpdir` は成功系2テストへ分割する。現行の「`None` ごとに別の空 mkdtemp」という期待は、固定 staged transport の裁定と矛盾する。

- `test_floor_dependency_base_only_reads_and_binds_payload_policy` は `test_floor_dependency_default_transport_reads_and_binds_payload_policy` へ改名し、`transport_mode == "source-dir"` と3 source-dir を期待する。default の `base-only` は外部取得可能なので現行期待が誤り。

- `test_real_floor_prepare_material_oracle_and_capability_series_when_configured` は、空 base を prebuild stub が埋める fixture をやめ、nonce に対応する3-source submission payload を用意する。

- `test_production_floor_dependency_preflight_failure_persists_private_attempt[checkout|base|configure|target|source-missing]` は、default staging が意図した failure より先に失敗しないよう、固定 payload fixture を追加する。

- `test_floor_dependency_disappearance_race_persists_closed_detail_before_oracle[base-stat]`、`[source-stat]` と `test_floor_dependency_head_mismatch_outranks_source_stat_failure_before_oracle` は `tempfile.mkdtemp` 注入を外し、導出済み固定 staging base を対象にする。

- `test_floor_dependency_base_creation_failure_persists_before_oracle_or_build` は `mkdtemp` failure ではなく、固定 destination の exclusive `mkdir` failure を注入する。現行期待の発生機構が削除されるため。

- `orchestrator/tests/test_pegasus_floor_tools.py::test_floor_job_invokes_fixed_pilot_cli_without_bypass` は期待 argv から `--fetchcontent-base-dir` の2 token を削除する。caller が transport seam を渡す現行期待が裁定と逆になるため。

- `test_floor_job_stages_payload_before_driver_and_passes_base_dir` は `test_floor_job_leaves_fetchcontent_staging_to_driver_default` へ改名し、shell function、`FETCHCONTENT_STAGING`、CLI flag が存在しないことを期待する。

- `test_floor_protocol_resolution_is_shared_by_all_consumers` は記録される driver argv から同2 token を削除する。

- `test_floor_job_hardens_interpreter` は checkpoint stage の期待列から `fetchcontent-staging` を削除する。Python invocation 数は変えない。

- `_receipt_validator_fragment` の終端を `CURRENT_STAGE=fetchcontent-staging` から `CURRENT_STAGE=source-identity` へ変更する。これを使う `test_submit_receipt_round_trips_through_job_validator[producer-receipt-accepted]` と `[different-job-rejected]` の意味は維持する。

- `_driver_tail` fixture から `FETCHCONTENT_STAGING` の補完行を削除する。

**既存のまま**

- `test_submit_floor_qsub_exports_nonce_and_stages_third_party_payload`
- `test_submit_floor_copies_and_reverifies_all_floor_third_party_sources`
- `test_floor_dependency_prebuild_uses_pinned_checkout_and_exact_helper_once`
- `test_floor_pristine_staged_preflight_verifies_three_pins_and_clean_status`
- `test_run_campaign_parser_accepts_fetchcontent_base_dir`
- `test_main_forwards_fetchcontent_base_dir_to_run_campaign`
- `test_public_official_rejects_fetchcontent_base_dir_before_side_effects`
- `test_public_official_rejects_each_nondefault_seam_before_side_effects[fetchcontent_base_dir-seam_value]`
- `test_refreeze_seam_classifier_covers_and_classifies_every_core_seam`
- `test_fetchcontent_seam_disqualifies_refreeze_eligibility`
- `test_policy_unit_fresh_official_default_context_is_refreeze_eligible`
- `test_pilot_default_context_is_not_refreeze_eligible`
- `test_official_resume_is_not_refreeze_eligible_even_without_seams`

これらは、explicit pilot seam の維持、official の explicit seam 拒否、18 名閉集合、公式適格式の literal 不変を既に固定している。

## 残る不確実性

- erratum 5 行目の `certified_writer_admission.py:66` は射影外のため独立確認できなかった。
- read-only かつ writable tmp 不在の条件に従い、pytest と shell integration test は実走していない。記載したのは静的到達性とテスト改訂計画である。
- `cp -a` の実計算ノード filesystem 上の挙動と所要時間は測定していない。
- この wave 後も、現コードの official permit gate と正規 job の pilot 固定が残る。したがって「transport が official を不適格にする矛盾」は解消するが、production official 全体の起動確認にはならない。

## scope 外候補

- `_assert_official_permitted` と CLI の §8 拒否を、承認束縛の実装と同時に解除する別 wave。
- `floor_campaign.sh` の `--mode pilot` 固定を official submission の認可済み mode 選択へ結線する別 wave。
- official 実走と floor 値の性能測定。今回の transport 実装には混ぜない。

## 総括

採る案は、submission nonce と固定 path 式から driver が payload を導出し、scratch への `cp -a` も driver が所有する構成である。  
新 env、directory discovery、caller の新 seam は作らない。  
`None` の空 base・外部取得経路は削除し、default と explicit pilot の両方を既存 pin 検査へ合流させる。  
18 名集合、適格判定式、official の explicit seam 拒否は literal 無変更で維持できる。  
最大の risk は、transport 修正だけでは現存する official permit gate と pilot 固定を解除できず、official 実走可能性の完全な証明にはならない点である。