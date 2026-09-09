## 総括

推奨案は、永続 cache を job へ直接渡さず、submit 側で `fetch_third_party.py hydrate` を実行し、その hydrate 済み staging root を渡す形である。job は三依存を `$TMPDIR/fetchcontent/{masstree,mimalloc,googletest}-src` へ `cp -a` し、その job-private copy だけを CMake と silo 条件関門へ供給する。

理由は、永続 cache の `verify` は ignored artifact を拒否しない一方、hydrate 後の検証と `_verify_pristine_floor_dependency_sources` は ignored artifact まで拒否するためである。

基本プランでは walltime 式と `calibration_v1.json` は変更しない。hydrate は login-side、offline configure は既存 configure の置換、job 内の copy・再検査は既存 `CCBench=900` build envelope に含める。ただし、式の既存不整合は親裁定へ返す。

編集、git 操作、pytest 実走は行っていない。静的通読と検索のみである。

## 変更計画 (file:line)

**[tools/pegasus/submit_certify.sh](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2535-certify-offline-fetch/tools/pegasus/submit_certify.sh:20)**

- 現行 20 行 `PROTOCOL_EXPLICIT=0` の直後に次の変数を置く。

  - `THIRD_PARTY_CACHE_ROOT=${IZANAGI_PEGASUS_THIRDPARTY_CACHE:-}`
  - `THIRD_PARTY_STAGING_ROOT` は `--repo-root` の解析後でなければ確定できないため、ここでは設定しない。

- 現行 49 行の protocol whitelist 終端直後、51 行の job script 検査より前に、`THIRD_PARTY_CACHE_ROOT` が非空であることを検査する。これにより正しい ratio/protocol の依頼は cache 未指定なら directory 作成前に停止する。既存の ratio/protocol 負例はそれ以前に停止するので弱まらない。

- 現行 56–57 行で `POLICY` と `CALIBRATION_POLICY` を決めた直後に、次を設定する。

  ```bash
  THIRD_PARTY_STAGING_ROOT="$REPO_ROOT/output/env/pegasus/silo_ladder_rung1/job-staging/thirdparty-src"
  ```

- 現行 119–126 行の `capture_required` 定義直後、128 行の scheduler preflight より前に、login-side hydrate を一度だけ実行する。

  ```bash
  third_party_hydrate_rc=0
  capture_required third-party-hydrate \
    python3 "$REPO_ROOT/tools/pegasus/fetch_third_party.py" hydrate \
      --repo-root "$REPO_ROOT" \
      --cache-root "$THIRD_PARTY_CACHE_ROOT" \
      --staging-root "$THIRD_PARTY_STAGING_ROOT" \
    || third_party_hydrate_rc=$?
  ```

  非ゼロなら `qstat` / `qsub` へ進まず終了する。

- `third-party-hydrate.stdout` を Python で再読し、以下を exact に検査して `THIRD_PARTY_SOURCE_ROOT` を得る。

  - top-level key が `schema_version, operation, cache_root, source_root, sources`
  - `schema_version == "pegasus-thirdparty-fetch/v1"`
  - `operation == "hydrate"`
  - `source_root` が canonical な `THIRD_PARTY_STAGING_ROOT`
  - source 名が順序込みで `masstree, mimalloc, googletest`
  - 各 record で `head == pin`
  - `resolved_path` がそれぞれ `source_root/<name>`
  - source root が絶対 path で、comma、`=`、newline を含まない

- 現行 189 行の `export_spec` を次の三値へ書き換える。

  ```bash
  export_spec="IZANAGI_SUBMISSION_NONCE=$NONCE,IZANAGI_CALIBRATION_RRATIO=$RRATIO,IZANAGI_CALIBRATION_THIRD_PARTY_SOURCE_ROOT=$THIRD_PARTY_SOURCE_ROOT"
  ```

  protocol 明示時の現行 190–192 行はそのまま末尾へ `IZANAGI_CALIBRATION_PROTOCOL` を加える。pre-submit / submit receipt の schema や field は増やさない。

**[tools/pegasus/certify_calibration.sh](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2535-certify-offline-fetch/tools/pegasus/certify_calibration.sh:150)**

- 現行 169 行の protocol 検査終端直後、170 行の legacy tolerance 検査より前に以下を追加する。

  - `IZANAGI_CALIBRATION_THIRD_PARTY_SOURCE_ROOT` 必須検査
  - `THIRD_PARTY_SOURCE_ROOT=$IZANAGI_CALIBRATION_THIRD_PARTY_SOURCE_ROOT`
  - absolute、comma / `=` / newline なし、root 非 symlink、`realpath -e` 後も入力と同一、directory であること
  - `masstree`, `mimalloc`, `googletest` の三子がいずれも実 directory かつ非 symlink であること

  失敗 stage 名は `submit_binding` とする。

- 現行 535 行のコメント `# (iv-c) pinned-clean CCBench + /scr の fresh worktree/build。` は文字列も位置も維持する。その直後、現行 536 行 `CCBENCH_BASE=...` の直前に次を挿入する。

  ```bash
  FETCHCONTENT_BASE_DIR="$TMPDIR/fetchcontent"
  mkdir "$FETCHCONTENT_BASE_DIR"
  for third_party_name in masstree mimalloc googletest; do
    cp -a \
      "$THIRD_PARTY_SOURCE_ROOT/$third_party_name" \
      "$FETCHCONTENT_BASE_DIR/${third_party_name}-src"
  done
  ```

- copy 直後に Python を起動し、既存の
  `orchestrator.campaign.s8b_floor_campaign._verify_pristine_floor_dependency_sources`
  へ `Path(FETCHCONTENT_BASE_DIR)` と `repo_root=Path(REPO_ROOT)` を渡す。非ゼロ時は
  `write_failure 2 third_party_copy "job-private FetchContent sources are not pinned-pristine"`
  で停止する。

  既存の `# (iv-c)` anchor を動かさないので、`test_pegasus_tools.py:459-494` の glog→CCBench fragment 境界を壊さない。

- 現行 576–581 行の `configure_argv` を、既存 `ENABLE_SANITIZER` と `ccbench_define_argv` の間に次の順序で五 token を置く形へ書き換える。

  ```bash
  "-DFETCHCONTENT_BASE_DIR=$FETCHCONTENT_BASE_DIR"
  -DFETCHCONTENT_FULLY_DISCONNECTED=ON
  "-DFETCHCONTENT_SOURCE_DIR_MASSTREE=$FETCHCONTENT_BASE_DIR/masstree-src"
  "-DFETCHCONTENT_SOURCE_DIR_MIMALLOC=$FETCHCONTENT_BASE_DIR/mimalloc-src"
  "-DFETCHCONTENT_SOURCE_DIR_GOOGLETEST=$FETCHCONTENT_BASE_DIR/googletest-src"
  ```

- 現行 389–403 行の `run_condition_gate`、586–588 行の silo-only 呼出し、600–601 行の configure/build timeout は変更しない。五 token は `${configure_argv[@]:5}` の一部として silo 条件関門へ自動的に渡る。

- 現行 652–735 行の receipt schema は変更しない。`ccbench.build_argv` に五 token が焼かれるだけとする。

- 現行 689–694 行の walltime 式は基本プランでは変更しない。

**[orchestrator/tests/test_pegasus_calibration_workload.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2535-certify-offline-fetch/orchestrator/tests/test_pegasus_calibration_workload.py:113)**

- `_protocol_shell_observation` に、既定値を維持した keyword fixture 引数を追加する。

  - `cmake_path="/fixture/cmake"`
  - `build_source="/fixture/source"`
  - `build_dir="/fixture/build"`
  - `fetchcontent_base_dir="/fixture/fetchcontent"`

- 137–149 行の shell fixture へ `FETCHCONTENT_BASE_DIR=<quoted value>` を追加する。既存テストの期待 path は変わらない。

- `run_condition_gate` stub は gate 回数に加え、呼出時の `configure_argv` を `gate_configure_argv` へ snapshot する。戻り値へ同配列を追加し、silo に限って offline 五 token が同じ base で渡ったことを検査する。

- 現行 318 行のテスト名は byte-compatible ではなくなるため、
  `test_default_silo_build_and_calibrate_argv_match_offline_contract`
  へ改名する。

- 現行 321–333 行の expected configure argv は、`-DENABLE_SANITIZER=OFF` の直後へ次を挿入する。

  ```text
  -DFETCHCONTENT_BASE_DIR=/fixture/fetchcontent
  -DFETCHCONTENT_FULLY_DISCONNECTED=ON
  -DFETCHCONTENT_SOURCE_DIR_MASSTREE=/fixture/fetchcontent/masstree-src
  -DFETCHCONTENT_SOURCE_DIR_MIMALLOC=/fixture/fetchcontent/mimalloc-src
  -DFETCHCONTENT_SOURCE_DIR_GOOGLETEST=/fixture/fetchcontent/googletest-src
  ```

- 現行 467 行の submit fixture helper の前へ、三つの小さい独立 Git repository を持つ cache fixture を作る helper を置く。copied policy と copied `ThirdParty.cmake` の pin/ref をその fixture commit に同期させ、各 repository の origin は policy URL と一致させる。これは現行 production hash を fixture へ差し込む案ではなく、独立 fixture の正負 pin 検査である。

- `_run_submit_dry_run_in_clean_fixture` は環境へ `IZANAGI_PEGASUS_THIRDPARTY_CACHE=<fixture cache>` を渡す。現行 560–563 行と583–591 行の exact qsub pin は hydrate root export を含む形へ更新する。

## 供給元の決定 (P1)

**hydrate 済み staging root を渡す。永続 cache root は login-side hydrate の入力に限定する。**

根拠は次の通り。

- [fetch_third_party.py:393](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2535-certify-offline-fetch/tools/pegasus/fetch_third_party.py:393) の通常 `verify` は untracked file を検査するが、ignored file は検査しない。`reject_ignored=True` のときだけ 400–409 行で ignored artifact を拒否する。
- hydrate 経路は [同:637](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2535-certify-offline-fetch/tools/pegasus/fetch_third_party.py:637) で `git clone --no-hardlinks` を使い、648–662、670–677 行で hydrate 後の三 repository を `reject_ignored=True` で検査する。
- [paper_story_a2_certification.sh:340](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2535-certify-offline-fetch/tools/pegasus/paper_story_a2_certification.sh:340) は供給 root を scratch へ `cp -a` し、子名を `*-src` に変えてから driver へ渡す。
- `_verify_pristine_floor_dependency_sources` は [s8b_floor_campaign.py:2572](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2535-certify-offline-fetch/orchestrator/campaign/s8b_floor_campaign.py:2572) で、base が canonical absolute directory、repo 外、非 symlink であることを要求し、2638 行で `name-src` を期待する。さらに 2745–2787 行で untracked と ignored の両方を拒否する。
- hydrate root は repo の `output/` 配下なので、この verifier へ直接渡すと「repo 外」契約に反する。したがって、A-2 と同じく `$TMPDIR` へ copy してから verifier に渡す必要がある。

pristine 保証を担う手順は明確に三段ある。

1. `fetch_third_party.py hydrate` の `--no-hardlinks` と `reject_ignored=True` が、永続 cache から独立した pinned-pristine staging clone を作る。
2. job の `cp -a` が staging clone を job-private `$TMPDIR/fetchcontent/*-src` へ複製する。
3. `_verify_pristine_floor_dependency_sources` が copy 後の実体を pin、Git top-level、tracked/untracked/ignored clean の全条件で再検査し、CMake はその copy だけを指す。

したがって、masstree の `config.h` や archive が configure/build 中に生成されても、hydrate 済み staging source は汚れない。

## テスト契約の更新

(a) `_protocol_shell_observation` に新たに必要な fixture 変数は `FETCHCONTENT_BASE_DIR` 一つだけである。三つの source dir は production と同じく `${FETCHCONTENT_BASE_DIR}/<name>-src` から導出し、`MASSTREE_SOURCE_DIR` 等の独立 fixture は作らない。

submit dry-run fixture には別途 `IZANAGI_PEGASUS_THIRDPARTY_CACHE` が必要になる。

(b) fragment 境界は壊れない。

- `case "$CALIBRATION_PROTOCOL" in`
- `configure_argv=(`
- `# The current CCBench pin`
- `if [[ "$CALIBRATION_PROTOCOL" == "silo" ]]`
- 二つ目の protocol `case`
- `BINARY=...`

これらの目印文字列はすべて維持する。copy block は最初の protocol `case` より前、五 define は `configure_argv` の内部なので、現行 115–129 行の `source.index(...)` は変更不要である。

(c) exact argv pin は上記五 token を `ENABLE_SANITIZER` の直後へ加える。build argv と calibrate argv は変更しない。

既存負例は弱めない。

- 現行 252–264 行の `test_certify_non_silo_defines_contain_no_axis_outsider` は `-DCCBENCH_` prefix だけを抽出するため、`-DFETCHCONTENT_*` は outsider 集合へ入らない。
- protocol define の `case` 本体は変更しないため、`_certify_protocol_define_table` の独立 parse 契約も維持される。
- 現行 306–315 行の gate 回数は silo 1 / mocc 0 / tictoc 0 のまま。
- `run_condition_gate` が除外する token は引き続き `-DCCBENCH_BACKOFF_FIXED=-1` 一つだけで、offline token は除外しない。
- ratio/protocol 不正テストは cache 検査より前に停止させ、side-effect-free 契約を維持する。

## 新規テスト

すべて `test_pegasus_calibration_workload.py` 内へ追加する。

- `test_certify_offline_fetchcontent_contract_is_identical_for_all_protocols`

  silo / mocc / tictoc の observation から `FETCHCONTENT_` token を抽出し、三者すべてで exact に同じ五 token、同じ順序、各一件であることを検査する。これにより `FULLY_DISCONNECTED` だけ、SOURCE_DIR の一部だけ、protocol ごとの差分のいずれも赤になる。

- `test_certify_condition_gate_receives_same_fetchcontent_base`

  silo の gate snapshot に、measurement configure と同じ base、FULLY_DISCONNECTED、三 SOURCE_DIR があることを比較する。同時に production `run_condition_gate` fragment が `${configure_argv[@]:5}` を走査し、各 token を `--configure-arg=` へ積むことを検査する。mocc / tictoc の gate 回数は従来どおりゼロを要求する。

- `test_certify_job_copy_keeps_hydrated_sources_pristine`

  `masstree`, `mimalloc`, `googletest` の marker を持つ hydrate-layout fixture を作り、production の copy fragment を shell で実行する。copy 側 marker を変更しても upstream bytes と inode が変わらず、三 destination が symlink でないことを確認する。これが「job が pristine source を汚さない」手順の実体検査になる。

- `test_certify_offline_fetchcontent_resolves_three_local_sources_without_git`

  production copy fragmentで作った `masstree-src`, `mimalloc-src`, `googletest-src` を使い、最小 CMake project を実際に configure する。project は三つの実名で `FetchContent_Declare` し、remote は到達不能な `.invalid` URL にする。各ローカル source の `CMakeLists.txt` が自身の source path を result file に記録するようにし、configure 後に三 path が job-private copy と exact 一致することを確認する。

  各 protocol で positive configure を行い、silo では masstree、mocc では mimalloc、tictoc では googletest の SOURCE_DIR tokenを一つ除いた negative configure が失敗することも確認する。これにより「argv に define が在るだけ」の恒真検査にならない。

- `test_submitter_hydrates_and_exports_verified_third_party_root`

  dry-run の qsub `-v` に cache root ではなく hydrate root が一件だけ出ること、hydrate root の三 repository が cache repository と hardlink inode を共有しないことを検査する。

- `test_submitter_rejects_dirty_or_pin_mismatched_third_party_cache`

  三 source のうち一つへ untracked file を置く場合と HEAD をずらす場合を負例化し、qsub command が生成されないことを検査する。既存 pin を現在値へ差し替える fixture は使わない。

## walltime 予算 (P3)

基本プランでは式を変更しない。

- login-side hydrate は PBS job walltime の外である。
- offline configure は configure を一回増やすものではなく、現行 600 行の同じ `timeout 900 "${configure_argv[@]}"` の入力を閉じる変更である。
- 現在の永続 cache の静的サイズは masstree 39 MiB、mimalloc 18 MiB、googletest 20 MiB、合計約 77 MiBだった。これは copy 時間の実測ではない。
- job-side copy と pristine 再検査は、配置上も意味上も現行 `build_cap(CCBench=900...)` の CCBench 準備へ含める。
- mocc / tictoc では条件関門 300 秒が発火しないため、7200−6610=590 秒の未割当差分がある。silo を top comment の式で見ると 7200−6910=290 秒である。

ただし、現行式には既存の不整合がある。

- 冒頭 7–11 行は `condition_gate(300)` を含む `6910`。
- receipt の 689–694 行は同じ gate を含まない `6610`。
- configure と build はそれぞれ 900 秒 timeout だが、式は CCBench 全体を 900 と数える。同様に gflags/glog も複数 command timeout の合計ではない。

したがって「新しい copy に独立した cap を必ず与える」という解釈へ変えるなら scope 拡大である。その場合は親裁定後に次を同時変更する。

- `certify_calibration.sh:689` を worst-case silo として `6910 + COPY_VERIFY_CAP_S` にする。
- 690–694 行の文字列へ `condition_gate_silo(300)` と `third_party_copy_verify_cap(C)` を明記する。
- 冒頭 7–11 行も同じ合計へ同期する。
- `C <= 290` なら `calibration_v1.json:5-6` の 7200 は維持できる。
- `C > 290` なら [calibration_v1.json:5](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2535-certify-offline-fetch/tools/pegasus/policies/calibration_v1.json:5) の HMS と 6 行の秒数、および `certify_calibration.sh:4` の PBS 要求を同時に増やす必要がある。
- exact frozen formula を検査する `orchestrator/tests/test_pegasus_tools.py:200-214` も scope に追加する必要がある。

静的サイズだけから新しい cap 値を捏造すべきではないため、この拡大案では compute-node 実測後に `C` を裁定する。

## 波及の静的列挙

| 面 | 直接 consumer | 2 段目 | 影響 |
|---|---|---|---|
| configure argv | `certify_calibration.sh:398-403` の条件関門 | `condition_meaning_gate` の requested/control configure | silo に同じ offline base が渡る。判定式・受理集合は不変 |
| configure argv | `certify_calibration.sh:600` の CMake | CCBench `cmake/ThirdParty.cmake` | masstree / mimalloc / googletest を local source から解決 |
| receipt build argv | `make_acquisition_receipt.py:36-48` | `schema_v2.CcbenchReceipt:403-413` | list[str] なので追加 token を受理。field 追加なし |
| receipt build argv | `calibrator/cli.py:373-464` | `Genome` / `SPACES` | `-DCCBENCH_` 以外を無視するため genome 不変 |
| walltime | `calibrator/cli.py:695-737` | `schema_v2.CalibrationV2:522-539` | required≤qsub と reserve 条件のみ。式文字列を解釈しない |
| registered calibration | `calibration_verify.py:81-142` | `env_attestation.py:1028-1041` | schema/hash を再検証。追加 argv token は許容 |
| toolchain binding | `s8b_floor_campaign.py:4172-4190` | `toolchain_binding.py:25-95` | C/CXX compiler define だけ抽出するため不変 |
| silo provenance | `silo_ladder_rung1.py:3769-3803` | `toolchain_binding.extract_silo_compiler_paths` | compiler と gflags/glog pin の抽出は不変 |
| report | `layer3_report.py:477-492` | report view 生成 | acquisition receipt の存在を basis 名へ使うだけ |

`load_verified_calibration` の二段目 consumer は、少なくとも以下である。いずれも calibration 全体を schema/hash 検証後に使い、FetchContent token の個数を固定していない。

- `orchestrator/campaign/loop.py:186`
- `orchestrator/campaign/screening_driver.py:315`
- `orchestrator/campaign/env_contract.py:466,617`
- `orchestrator/campaign/s8b_floor_campaign.py:7348`
- `orchestrator/campaign/s8b_ratified_freeze.py:1996`
- `orchestrator/campaign/s8b_oracle_driver.py:970`
- `orchestrator/campaign/s8b_oracle_report.py:1717`
- `orchestrator/campaign/silo_ladder_rung1.py:2033`
- `orchestrator/campaign/floor_pair_driver.py:1154`
- `orchestrator/campaign/certified_writer_admission.py:173`
- `orchestrator/qualification/t126_driver.py:451`
- `orchestrator/campaign/p2_2.py:159`

変更対象外だが静的に影響確認が必要なテストは以下。基本プランでは修正不要の見込みである。

- `orchestrator/tests/test_pegasus_tools.py:134-214,432-538`
- `orchestrator/tests/test_calibrator_certify.py:433-541`
- `orchestrator/tests/test_schema_v2.py:291-315`
- `orchestrator/tests/test_silo_ladder_rung1_evidence.py:669,1309-1312`
- `orchestrator/tests/test_s8b_floor_campaign.py:2506-2517`
- `orchestrator/tests/test_ccbench_spawn_sites.py:2634-2639`
- `orchestrator/tests/test_official_perf_closure.py:70-94`

## 親 brief への反証

- brief 42–44 行の「`fetch_third_party.py verify` rc=0 だから汚れなし」は pristine 契約としては強すぎる。通常 verify は ignored artifact を検査しない。hydrate 後と `_verify_pristine_floor_dependency_sources` は ignored まで拒否する。

- brief 73–76 行の「永続 cache root または hydrate root」は同値ではない。pristine source として job へ渡すなら hydrate root が上位であり、永続 cache は hydrate 入力に限定すべきである。

- `_verify_pristine_floor_dependency_sources` は `*-src` 子と repo 外 base を要求するため、repo の `output/.../thirdparty-src` を直接渡して検査する案は失敗する。A-2 の scratch copy は単なる性能対策ではなく、この契約を成立させる手順である。

- `screening_driver.py:189-207` は `prepare_masstree_fetchcontent` 後に `FETCHCONTENT_BASE_DIR` だけを条件関門へ渡す base-only 先例である。三 SOURCE_DIR と FULLY_DISCONNECTED の all-or-nothing 先例ではない。

- walltime の親記述は二つの既存式を混同している。top comment は 6910、receipt は 6610 であり、後者には silo 条件関門 300 秒がない。

- 現行行番号のずれがある。

  - `submit_certify.sh` の export/qsub は 190–196 ではなく 189–195 行。
  - non-silo 負例は 250–264 ではなく 252–264 行。
  - `cli.py` の token filter は 424–437 だけでなく、実体は 425–444 行。
  - `configure_argv`、条件関門、exact argv の主要 anchor は概ね正しい。

## 未解決と裁定へ返す項目

- 基本プランでは `cp -a` と pristine 再検査を既存 `CCBench=900` envelope に含め、walltime 式を変えない。この解釈を親が認めない場合、式・policy・PBS directive・`test_pegasus_tools.py` を同時変更する scope 拡大裁定が必要である。

- 既存の 6910 / 6610 不一致を T-2535 と同時に是正するかは別裁定にすべきである。推奨は、最初の実測を gate のない mocc で通す本修正を先行し、式の再凍結は独立 wave に分離すること。

- 新規 CMake fixture と submit hydrate fixture の実走は親が行う必要がある。本段では書込可能 tmp がないため、bash parse、pytest、実 configure の成功を主張していない。