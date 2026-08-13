実装前は build admission に trigger block の意味検査がなく、binding 省略経路では非正準 source も admission を通る状態でした。

実装後は次の挙動です。

- source root／対象 file 不在、marker・骨格 token とも不在なら no-op。
- 凍結 pristine block、または mask 0〜31 の canonical hole だけを受理。
- marker/frame/newline/indent/BOM/NUL/重複、非 canonical hole、非 ENOENT I/O error は `BuildAdmissionError`。
- raw bytes は一度だけ読み、derive と require で再検査。
- persistent receipt replay は live source を読まず従来どおり受理。
- receipt key、body、policy、SHA、enum は未変更。

変更箇所:

- [axis_trigger_gating.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t897-trigger-admission/orchestrator/campaign/axis_trigger_gating.py:27): 凍結 block/hole の定数 1 組。
- [build_admission.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t897-trigger-admission/orchestrator/campaign/build_admission.py:240): 単一 read の semantic validator と derive/require 結線。
- [test_build_admission.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t897-trigger-admission/orchestrator/tests/test_build_admission.py:288): 正負例、receipt replay、patch golden、import/call-site meta-test。

段 4 §3 の RP-2 に従い、N12（END 後の外部代入）は scope 外です。「N01〜N14 を負例化」という再掲とは矛盾するため、正本である段 4 裁定を優先し、N12 の reject 実装・テストは追加していません。

検査結果:

- `py_compile`、`git diff --check`、UTF-8 NFC、変更対象 3 ファイル限定: 成功。
- 手動診断: pristine、全 mask 0〜31、追加した全負例、no-op、再読/replay、patch golden、AST meta-testで assertion なし。
- pytest は未実走です。  
  `python3 tools/run_tests.py orchestrator/tests/test_build_admission.py -x -q` は、local reservation ledger を安全に更新できず dispatch へ倒れ、`qstat -Q preflight rc=1`、最終 rc=16。実走 nodeid は 0 件で、pytest の緑は申告しません。

所有外の波及候補は `pipeline.py`、`buildcache.py`、S8a sweep/coverage/frequency、S-1 direct/extime、S8b oracle/floor。関連 consumer test は `test_campaign.py`、`test_buildcache_v2.py`、`test_s8a_trigger_sweep.py`、`test_s1_direct_comparison.py`、`test_s8b_oracle_driver.py`、`test_s8b_floor_campaign.py`、`test_p3_build_authority_cli.py` です。synthetic `SourceEvidence` fixture は対象 file 不在のため no-op を維持します。

docs 編集・commit は行っていません。

## 総括

semantic admission の実装と帰属可能なテストは完了し、変更は許可された 3 ファイルだけです。焦点 pytest のみ Pegasus 実行基盤 rc=16 により未実走なので、親の段 6 で runner が利用可能な環境から再走してください。