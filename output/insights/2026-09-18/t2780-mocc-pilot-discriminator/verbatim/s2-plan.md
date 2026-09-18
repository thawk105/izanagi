## 推奨案と現物との差分

scope 1〜3、P1〜P5 は基本的に採用する。ただし、**scope 2 に verifier の source 引数の修正を含める必要がある**。

現行 `tools/pegasus/mocc_trace_pilot.sh:2231` は `--ccbench-root "$CCBENCH_BASE"` を渡す。`CCBENCH_BASE` は同ファイル `:1660` の `external/ccbench`、patch 適用予定先は `:1681` の `BUILD_SOURCE` であり、両者は別である。射影 `patches-README-instr-mocc.md` は未計装 source を evidence-absent と説明し、既存 driver は実際に build した source を verifier に渡す（`orchestrator/campaign/s3_mocc_lock_coverage.py:387–421`）。

したがって、T1943 mode だけ verifier に `BUILD_SOURCE` を渡す。これは verifier の受理集合の変更ではなく、実行 binary と検査対象 source の配線修正である。未修正時の実 job 結果は未実測だが、patch 適用だけではこの配線は直らない。

以下の行番号は現物の変更前番号。必読射影は読めた。ファイル変更、pytest、compute 投入は実施していない。変異の KILLED は以下の受入予定条件であり、実測済みという意味ではない。

## scope 1：HYDRATE_PY の挿入と既存 pin

挿入位置は `tools/pegasus/mocc_trace_pilot.sh:1533/1534` 間。射影 `t2774-s2-plan-s4.md` の案を採用し、marker の task 番号だけ T2780 にする。

```bash
# BEGIN T2780 HYDRATE INTERPRETER GATE
HYDRATE_PY=""
hydrate_py_rejected=""
for py_name in python3 python3.10 python3.11 python3.12; do
  py_cmd=$(command -v -- "$py_name") || continue
  py_resolved=$(realpath -e -- "$py_cmd") || continue
  [[ -x "$py_resolved" ]] || continue
  if (
    cd "$REPO_ROOT" &&
    PYTHONPATH="$REPO_ROOT/orchestrator:$REPO_ROOT${PYTHONPATH:+:$PYTHONPATH}" \
    "$py_resolved" -c \
      'import sys; import orchestrator.campaign.silo_ladder_rung1; raise SystemExit(0 if sys.version_info >= (3, 10) else 1)' \
      "$REPO_ROOT"
  ) >/dev/null 2>&1; then
    HYDRATE_PY="$py_resolved"
    break
  fi
  hydrate_py_rejected+="${hydrate_py_rejected:+ }$py_name=$py_resolved"
done
if [[ -z "$HYDRATE_PY" ]]; then
  hydrate_gate_message="no python3 >= 3.10 candidate can import orchestrator.campaign.silo_ladder_rung1 (rejected: ${hydrate_py_rejected:-none})"
  printf '%s\n' "$hydrate_gate_message" \
    >"$ATTEMPT_DIR/third-party-hydrate.stderr"
  write_failure 2 third_party "$hydrate_gate_message"
  exit 2
fi
# END T2780 HYDRATE INTERPRETER GATE
```

`:1534–1537` は interpreter だけ置換する。

```bash
timeout 20 "$HYDRATE_PY" "$TOOLS/fetch_third_party.py" hydrate --repo-root "$REPO_ROOT" \
  --cache-root "$CACHE_ROOT" --staging-root "$THIRD_PARTY_STAGING_ROOT" \
  >"$ATTEMPT_DIR/third-party-hydrate.json" \
  2>"$ATTEMPT_DIR/third-party-hydrate.stderr"
```

import root の判断は次のとおり。

- `fetch_third_party.py:22–23,52–64` は `_CODE_ROOT`、`_ORCHESTRATOR_ROOT` の順に `insert(0, ...)` する。両方が未登録なら最終順序は orchestrator root → repo root。
- `from orchestrator.campaign import silo_ladder_rung1` は repo root から package 経由で到達する。`silo_ladder_rung1.py:37–53` の直接実行用 `sys.path` 挿入には依存しない。
- **この qualified import の探索だけなら `$REPO_ROOT` で足りる。** ただし、推移 import 全体について root を一つに減らしてよいことは未実測。fetch が与える二つの root を probe にも与える案を採る。`-c` の cwd は `$REPO_ROOT` とし、既存 `PYTHONPATH` は末尾に保存する。
- `:1538–1549` の JSON 読取りは stdlib のみなので、P4 どおり素の `python3` を維持する。

gate 失敗時の出力は stdout redirect の `>"…stderr"`、hydrate の出力は stderr redirect の `2>"…stderr"` である。このため `test_pegasus_tools.py:575,584` の後者 count==1 は維持できる。

`orchestrator/tests/test_pegasus_tools.py:560` の新しい逐語 pin：

```python
hydrate = 'timeout 20 "$HYDRATE_PY" "$TOOLS/fetch_third_party.py" hydrate --repo-root "$REPO_ROOT"'
```

`:585–587` の既存順序を保持し、gate の位置を挟む。

```python
assert (
    job.index("# END T1718 COMPILER VERSION BODY GATE")
    < job.index(cache_check)
    < job.index("# BEGIN T2780 HYDRATE INTERPRETER GATE")
    < job.index("# END T2780 HYDRATE INTERPRETER GATE")
    < job.index(hydrate)
    < job.index(root_read)
    < job.index(resolution)
)
```

既存の staging、cache argv、redirect、source_root 検査の count==1 は変更しない（同 test `:571–584`）。既存 checker/verifier の変数名・marker は複製しない。

## scope 1：契約 test 1 本と変異 matrix

`orchestrator/tests/test_mocc_trace_job_contract.py:1515` の checker test 群の直前に、次の **1 test 関数**を追加する。

```python
test_mocc_trace_hydrate_interpreter_gate_selects_and_fails_closed
```

抽出開始は `# BEGIN T2780 HYDRATE INTERPRETER GATE`、終端は次の文字列の直前とする。

```python
'THIRD_PARTY_SOURCE_ROOT=$(python3 - '
```

BEGIN、END、終端の exactly-one と順序を検査する。END marker で抽出を終えず、hydrate の timeout・argv・redirect まで実行する。

fixture は既存 `:1515–1597,1881–1991,2087–2166` に合わせる。

- `_make_executable`（`:41–43`）で絶対 shebang の fake interpreter を四つ作る。
- `PATH` は fixture の bin directory のみ。実 `realpath` と実 `timeout` の symlink を置く。
- fake は `-c` probe と hydrate 呼出を分けて記録する。probe の argv、cwd、PYTHONPATH、候補順序と、hydrate の interpreter identity、argv、cwd を別ファイルに残す。hydrate により probe 記録を上書きしない。
- prefix に `set -Eeuo pipefail`、`REPO_ROOT`、`TOOLS`、`ATTEMPT_DIR`、`CACHE_ROOT`、`THIRD_PARTY_CACHE_ENV`、`TMPDIR`、`THIRD_PARTY_STAGING_ROOT="$TMPDIR/thirdparty-src"` を設定する。cache 環境変数も対応する値に設定する。
- `write_failure` は shell の `printf` だけで rc・stage・message を保存する stub。fake `python3` を failure JSON 生成に使わない。
- `/bin/bash -c prefix + block + suffix`、`env={"PATH": str(bin_dir)}` を使い、必要な stub 用変数は prefix から export する。
- probe は subshell 内の repo cwd、hydrate は呼出元 cwd を引き継ぐ。両者を区別して assert する。現行 hydrate に不要な `cd` は追加しない。

| ケース | 設定と必須 assertion |
|---|---|
| (a) fallback 成功 | python3 の probe rc=1、python3.10 rc=0。hydrate は python3.10 の絶対 resolved path で実行され、cache/staging argv が一致。python3.11/3.12 の記録なし。 |
| (b) 先頭成功 | python3 の probe rc=0。同候補で hydrate 到達、後続三候補の記録なし。 |
| (c) 全拒否 | 四候補とも probe rc=1。shell rc=2、stage=`third_party`、message と `third-party-hydrate.stderr` の双方に全候補の `name=resolved`。hydrate 呼出記録なし、suffix 到達なし。 |
| (d) probe 契約 | 呼ばれた候補の記録で `-c`、module 名、`sys.version_info >= (3, 10)`、末尾 repo argv、repo cwd、二つの PYTHONPATH root の順を検査。 |

候補が見つからない場合は既存 checker と同じく `continue` され、rejected 一覧には載らない（pilot `:1756–1770`）。ケース (c) は四候補を実在させ、probe が拒否した一覧を検査する。

| 変異・正例 | KILLED／通過条件 |
|---|---|
| hydrate を素の `python3` に戻す | (a) の hydrate interpreter identity と実 argv が不一致。旧候補の hydrate を拒否する stub も併用する。 |
| version 比較を外す | (d) の **実際に渡された probe argv の文字列検査**で KILLED。 |
| rejected の追記を外す | (c) の message／stderr に四候補一覧が揃わず KILLED。 |
| 正例：成功候補で hydrate 到達 | (a)(b) が rc=0、hydrate argv 一致で通過。 |

固定 rc を返す fake は Python の version 式を評価しない。そのため、この設計で version 比較除去を殺すのは文字列検査である。明示条件を保つ契約として十分だが、旧 Python の意味実行を実証したとは扱わない。version 情報を模擬して probe 本文を実行する別 fixture も可能だが、今回の test 1 本の目的には不要。実環境の推移 import は scope 3 が担当する（F1027）。

## scope 2：patch 適用 block と verifier source

挿入位置は pilot `:1683` の worktree add 完了直後、`:1685` の `build_mode()` **定義前**。marker は次を提案する。

```text
# BEGIN T2780 INSTRUMENTATION PATCH
# END T2780 INSTRUMENTATION PATCH
```

T1943 mode の分岐内だけで patch を読む・当てる・artifact を作る。既存の touch set → apply の型は `patchharness.py:155–171,204–211` と `s3_mocc_lock_coverage.py:430–436`。sha 前後一致と source sha は射影 `t2774-runner-patch-apply.md:505–517` と揃える。

逐語案：

```bash
# BEGIN T2780 INSTRUMENTATION PATCH
PATCH_PATH=""
PATCH_SHA=""
PATCHED_SOURCE_SHA=""
if [[ "$T1943_G2" -eq 1 ]]; then
  if ! PATCH_PATH=$(realpath -e -- \
    "$REPO_ROOT/patches/instr-mocc-lock-coverage.patch"); then
    write_failure 2 instrumentation_patch "instrumentation patch cannot be resolved"
    exit 2
  fi
  if [[ ! -f "$PATCH_PATH" || -L "$PATCH_PATH" ]]; then
    write_failure 2 instrumentation_patch "instrumentation patch is not a real file"
    exit 2
  fi
  if ! PATCH_SHA=$(sha256sum "$PATCH_PATH" | awk '{print $1}'); then
    write_failure 2 instrumentation_patch "instrumentation patch hash failed"
    exit 2
  fi
  printf '%s\n' "$PATCH_SHA" >"$ATTEMPT_DIR/instr-patch.sha256"
  : >"$ATTEMPT_DIR/instr-patch-apply.stdout"
  : >"$ATTEMPT_DIR/instr-patch-apply.stderr"

  if ! git -C "$BUILD_SOURCE" apply --numstat "$PATCH_PATH" \
    >"$ATTEMPT_DIR/instr-patch.numstat" \
    2>>"$ATTEMPT_DIR/instr-patch-apply.stderr"; then
    write_failure 2 instrumentation_patch "instrumentation patch numstat failed"
    exit 2
  fi
  if ! awk -F '\t' '
    NF != 3 || $1 !~ /^[0-9]+$/ || $2 !~ /^[0-9]+$/ ||
      $3 != "cc/mocc/transaction.cc" { bad=1 }
    END { exit (bad || NR != 1) }
  ' "$ATTEMPT_DIR/instr-patch.numstat"; then
    write_failure 2 instrumentation_patch "instrumentation patch touch set differs"
    exit 2
  fi
  if ! git -C "$BUILD_SOURCE" apply --check "$PATCH_PATH" \
    >>"$ATTEMPT_DIR/instr-patch-apply.stdout" \
    2>>"$ATTEMPT_DIR/instr-patch-apply.stderr"; then
    write_failure 2 instrumentation_patch "instrumentation patch check failed"
    exit 2
  fi
  if ! git -C "$BUILD_SOURCE" apply "$PATCH_PATH" \
    >>"$ATTEMPT_DIR/instr-patch-apply.stdout" \
    2>>"$ATTEMPT_DIR/instr-patch-apply.stderr"; then
    write_failure 2 instrumentation_patch "instrumentation patch apply failed"
    exit 2
  fi
  if ! patch_sha_after=$(sha256sum "$PATCH_PATH" | awk '{print $1}'); then
    write_failure 2 instrumentation_patch "instrumentation patch post-apply hash failed"
    exit 2
  fi
  if [[ "$patch_sha_after" != "$PATCH_SHA" ]]; then
    write_failure 2 instrumentation_patch "instrumentation patch changed during application"
    exit 2
  fi
  if ! PATCHED_SOURCE_SHA=$(sha256sum \
    "$BUILD_SOURCE/cc/mocc/transaction.cc" | awk '{print $1}'); then
    write_failure 2 instrumentation_patch "patched source hash failed"
    exit 2
  fi
  printf '%s\n' "$PATCHED_SOURCE_SHA" >"$ATTEMPT_DIR/instr-patch-source.sha256"
fi
# END T2780 INSTRUMENTATION PATCH
```

real-file 検査は `:2292–2298` と同じ resolved target の検査であり、元の pathname が symlink でなかったことまで主張しない。

`set -Eeuo pipefail` は `:13`、ERR trap は `:154–161`。裸の apply 失敗は stage=`shell` になるため、P3 の stage を残すには上記の明示捕捉が必要である。既存にも `if ! …; then write_failure …` と `|| rc=$?` の両型がある（`:1670–1672,1782,1820–1825`）。今回は終了コードを 2 に統一するので `if !` でよい。artifact 自体を書けない障害まで stage 保存を保証する設計ではない。

verifier の直前、`:2225` 付近に次を置き、`:2231` の引数を置換する。

```bash
VERIFIER_SOURCE_ROOT="$CCBENCH_BASE"
if [[ "$T1943_G2" -eq 1 ]]; then
  VERIFIER_SOURCE_ROOT="$BUILD_SOURCE"
fi
```

```bash
--ccbench-root "$VERIFIER_SOURCE_ROOT"
```

`CCBENCH_BASE` 自体は書き換えない。worktree cleanup が同変数を使用するためである（`:781–782,3389`）。既存の `verifier_rc=0` と verifier invocation は一つのまま保ち、marker を複製しない。

## scope 2：manifest、receipt、schema

manifest は pilot `:411–474` の T1943 専用登録へ五つ追加する。

| artifact | 分類 | 記録する対象 |
|---|---|---|
| `instr-patch.sha256` | `correctness_evidence` | 適用前 patch bytes の digest |
| `instr-patch.numstat` | `correctness_evidence` | 検査した touch set |
| `instr-patch-source.sha256` | `correctness_evidence` | 適用後 transaction.cc bytes の digest |
| `instr-patch-apply.stdout` | `operational_diagnostic` | check／apply の stdout |
| `instr-patch-apply.stderr` | `operational_diagnostic` | numstat／check／apply の stderr |

`:622–631` の general-mode 漏れ検査にも五つの exact filename を加える。ファイル存在検査だけでは、誤って general manifest に登録されたが未生成の entry を検出しないためである。既存 test `test_mocc_trace_job_contract.py:3918–3957` の dedicated_paths と分類 assertion を更新する。

receipt は `source` 節（`:3206–3222`）を共通拡張せず、`:3087–3106` の `t1943_binding` に追加する。`:3255` の既存代入で載る。

```json
{
  "instrumentation_patch": {
    "repo_path": "patches/instr-mocc-lock-coverage.patch",
    "sha256": "<適用前後で一致したpatch digest>",
    "touched_paths": ["cc/mocc/transaction.cc"],
    "patched_source_sha256": "<適用後source digest>",
    "trace0_built_from_patched_source": true,
    "trace0_identity_witness": "orchestrator/tests/test_mocc_proof_surface.py::test_instr_patch_keeps_trace0_preprocess_identical"
  }
}
```

`trace0_identity_witness` は repo test の識別子であり、compute job 内で同 test を実行したという記録ではない。

値の渡し方：

1. shell argv の末尾、`:2512` の watermark sha の後、heredoc 開始前へ `"${PATCH_PATH:-}" "${PATCH_SHA:-}" "${PATCHED_SOURCE_SHA:-}"` を追加。
2. `:2541–2542` の tuple 末尾へ `patch_path, patch_sha, patched_source_sha` を追加。既存引数の順序は変えない。
3. `:2984` の T1943 分岐内で digest 形式と sidecar 一致、numstat の単一 path を確認する。既存 `read_regular_bytes`（`:2591`）を使い、patch と `build_source/cc/mocc/transaction.cc` の bytes の digest が捕捉値に一致することを確認して binding を作る。これは記録対象との一致確認であり、新しい性能・同一性 gate ではない。
4. `:3256–3266` の専用 artifacts に五つの artifact 名を登録する。general-mode receipt には出さない。

**schema v2 置換を採用する。** 検索で見つかった現行 v1 literal は次の四箇所。

| ファイル・行 | 更新 |
|---|---|
| pilot `:3164` | writer の T1943 schema を v2 へ |
| pilot `:3346` | admitted set の v1 を v2 に置換 |
| pilot `:3349` | T1943 binding 検査の分岐条件も v2 へ |
| job contract test `:4576` | expected schema を v2 へ |

`:3349` を残すと v2 receipt が専用 binding 検査を通らなくなるため、admitted set と同時に直す。v2 の専用検査では instrumentation_patch の必須 field と型も確認する。旧 v1 を並列受理しない。

`test_mocc_trace_job_contract.py:4562,4663` の v4 正例、`:4648` の v3 拒否例は維持する。`mocc_trace_pair.py:27` の `PILOT_SCHEMA = ".../v4"` も変更しない。

既存 fixture `_run_mocc_trace_finalization` の T1943 準備（`:3354` 以降）に patch/source と sidecar を用意し、variables（`:3546–3554` 付近）に三変数を渡す。`:4566` の receipt test で全 field と digest を実 bytes と照合し、job-result の存在も明示確認する。既存 schema 改変 helper（`:3111–3133`）は対象 schema を指定可能にし、**T1943 v2 receipt を v1 に変更して sidecar も再計算した場合でも job-result が作られない**ケースを加える。v3 拒否は残す。

## scope 2：TRACE=0 の保証範囲

patch は `#if TRACE` と論理行番号を戻す `#line` を用いる（D14、D1686、射影 `patches-README-instr-mocc.md`）。既存 witness test は `orchestrator/tests/test_mocc_proof_surface.py:435` に存在する。

T1943 mode は patch block 後に同じ `BUILD_SOURCE` から TRACE=0 と TRACE=1 を build する（pilot `:1690,1746,1895`）。D297 checker の呼出は `:1779` の OID 対を維持する。checker は `tools/check_trace0_preprocess_identity.py:528–529` で OID の source を読むので、今回の作業ツリー patch の同一性検査ではない。

親 brief の「nm/strings」は正確には次の処理である。

- `:1850–1866`：TRACE=0 binary を直接開き、bytes を読み、同 fd に対して `nm -a`。
- `:1867–1888`：T1943 の既定 token と symbol の不在を検査。
- `:3050–3079`：receipt が実 binary の sha、absence report、sidecar を照合。

これは patched TRACE=0 binary を直接検査するが、任意の計装除去や binary 同一性全体を証明しない。**既存 repo test の同一性 witness と binary の既存不在検査の役割を区別して記録し、要求外の objdump gate は追加しない。**

## scope 2：契約 test と patch 側変異

既存 job contract test は `_make_executable`／fake git の型を使う（`:41,83`）。同ファイル内に実 `git init`＋commit fixture の先例は今回の静的検索では見つからなかった。

推奨は **fake git＋実 sha256sum**。固定値だけ返す fake sha は apply を外しても postimage digest を返せるため、負例 (e) の検出には向かない。

marker 間を実行する test では：

- tmp `BUILD_SOURCE/cc/mocc/transaction.cc` に既知の preimage bytes を置く。
- fake git は `-C`、`apply --numstat`、`apply --check`、`apply PATCH_PATH` の argv を順に記録。
- numstat は `9\t1\tcc/mocc/transaction.cc\n`。
- apply の場合だけ fixture の postimage bytes を source に書く。check と numstat は書かない。
- bin directory に実 `realpath`、`sha256sum`、`awk` を配置。expected digest は test 側 `hashlib` で計算する。
- 正例で source bytes、digest、artifact、コマンド順、stage 未記録を確認。
- check／apply の非0、touch set 不一致、apply 中の patch bytes 変更では rc=2、stage=`instrumentation_patch`、build 到達なしを確認する。

実 patch の hunk 適用と build は compute job、TRACE=0 同一性は既存 witness test が担当する。この test は shell 配線と記録の被覆であり、fake git の成功を実 patch 適用実績とは扱わない。

| 負例 | 検出する test 条件 |
|---|---|
| (e) 実 apply 行を外す | 正例で source が postimage であること、source sidecar が postimage digest であること、apply 呼出記録を検査。preimage のままなら KILLED。 |
| (f) touch set 検査を外す | numstat を二 file にする。正常実装は apply 前に rc=2。変異時は rc=0／apply 到達となり KILLED。 |
| (g) T1943_G2=0 でも patch を適用 | mode=0 ケースで git 呼出ゼロ、source 不変、五 artifact 不在を要求。manifest／receipt の general-mode 正例も維持。 |
| receipt の patch binding を外す | `:4566` の既存 receipt test に追加した field／digest assertion が KILLED。 |

**(e) の主検出を「receipt binding 欠落」だけにしてはいけない。** apply 一行を除いても、後続の hash と receipt field は生成できる。既知 postimage との照合を test の判定にする。

追加の verifier source 配線は、mode=1／0 の二ケースで実 invocation fragment を fake verifier に渡し、`--ccbench-root` がそれぞれ `BUILD_SOURCE`／`CCBENCH_BASE` になることを検査する。候補 gate を通したことと source argv の一致は別々に確認する。

## scope 3：生死確認と受入条件

実装 commit 後、受入前に compute job **1 本**。投入形は operational-facts の job 4936 と同じ。

```bash
IZANAGI_PEGASUS_THIRDPARTY_CACHE=/work/1/SFC/tanab/izanagi-thirdparty-cache \
tools/pegasus/submit_mocc_trace.sh \
  --t1943-g2-discriminator \
  --attempts-root /work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2780-mocc-pilot-discriminator/attempts
```

wave worktree を cwd にする。submitter は `:372–383` で mode、nonce、policy sha、cache を qsub に渡す。queue=gen_S、node=1、walltime=3600 秒は pilot `:2–5`。

待機対象は返された PBS_JOBID をそのまま使う。`0:` を推測で足さない。

- done：`<worktree>/output/env/pegasus/mocc-trace/job-staging/<PBS_JOBID>/job-result.json`
- accounting：`<attempts>/submissions/<nonce>/pbs-job.stderr`
- 待機：operational-facts 記載の `tools/dev_wave_wait.py compute` に request-id、done-file、accounting-file、receipt-file を渡す。

受入では次を確認する。

1. `job-result.json` が存在し、receipt digest が実 receipt／sidecar と一致する。
2. receipt schema は T1943 v2。instrumentation_patch の patch sha、touch set、patched source sha と attempt artifacts が一致する。
3. verifier rc∈{0,1}、discriminator rc=0。
4. `discriminator.json` の conclusion∈{`no-g2`,`supported`,`contradicted`}。`indeterminate` は今回の生死確認失敗。
5. artifact classification が完了し、既存 finalization 修正も実 compute で通過したことを記録する。

`indeterminate` は現行 discriminator が出し得る結論であり、pilot の JSON／receipt 検査も受理している（discriminator `:600–624`、pilot `:2324,3026,3357`）。**今回の wave の受入条件として失敗とし、discriminator 対応表や pilot の結論集合は変更しない。**

verifier rc=1 は `:2239–2243` で停止せず、`:2278–2284` の completed anomaly 検査後に discriminator へ進む。finalization も `:2985` で rc=1 を許す。既存 receipt fixture は rc=1 を使っている（test `:3348,4602`）。一回の実 job が rc=0 なら、rc=1 の compute 通過は未実測と記す。rc=3 を通す変更はしない。

走行中は worktree の編集・commit・merge を止める。判定 source は pre/post で HEAD と clean state を確認する（pilot `:714–774`）。この検査は endpoint consistency であり、途中で戻された変更まで捉えるとは主張しない（`:3213–3219`）。

時間は historical job の151秒を参考値とし、hydrate と依存 build を含め **実行5〜20分を暫定見積、PBS枠60分、queue 待ちは別**とする。今回の所要は未実測。pilot 冒頭の1790秒計算（`:7–10`）は T1943 の二回 build の厳密な上限としては使わない。

## 親による検証と成果物

親は `tools/run_tests.py` 経由で以下を実行する。

- `test_mocc_trace_job_contract.py`、`test_pegasus_tools.py` の関連契約。
- `test_mocc_proof_surface.py::test_instr_patch_keeps_trace0_preprocess_identical`。
- 指定の hydrate 負例3本＋正例、patch 負例 (e)(f)(g)。
- 既存 marker 一意性（job contract `:4191–4209`）、v4 正例、v3／旧T1943 v1拒否、rc=1 finalization。
- repo の完了時 checker と commit 後 provenance 監査。

insight `output/insights/2026-09-18/t2780-mocc-pilot-discriminator/README.md` は次の骨子とする。

- 問い：正規 pilot が現行 verifier と discriminator finalization まで成立するか。
- 変更点：hydrate interpreter、patch 適用と source 配線、receipt v2。
- 契約検査：正例・負例、KILLED の実測結果、fake の被覆範囲。
- 生死確認：commit、job ID、投入形、所要、原本 path、receipt の patch binding と discriminator conclusion の短い引用。
- 限界：単一 job、G2 根因の確定ではないこと、TRACE=0 の保証範囲、実 job が通らなかった分岐の未実測事項。

campaign 成果物は複製せず原本 path を示す。

failures fragment は F1027 の恒久対応・再発検知へ実装 commit、test、実 job の結果を追記する。生死確認前に解消済みとは書かない。worklog fragment は実際の検査と投入結果を記録する。

decisions fragment は **schema v2 置換の判断を1件出すことを推奨**する。理由は patch 有無で receipt の source 命題が異なるため。旧 v1 非受理、general v4 維持、verifier の判定不変を短く記録し、D14／D297／D1686 を再裁定しない。

## 所有分割、レビュー、親 brief への異議

段5 author は **1本、実装3ファイルを単独所有**でよい。scope 1／2 を別 author にすると pilot と `test_mocc_trace_job_contract.py` の両方が重なる。

段6は二つのレンズを並列にする。

| レンズ | 主な検査 |
|---|---|
| A：正しさと契約 | 規律2、hydrate選択と実argv、失敗時記録、patch適用順、verifier source一致、marker一意性、schema置換、変異の検出条件 |
| B：実行とartifact | 五artifactの分類、general漏れ、receiptと実bytesの一致、TRACE=0の主張範囲、投入形、job-resultまでの完了、insight引用と原本の一致 |

operational-facts 記載の t2772 所有面と実装3ファイルは重ならない。`patches/README.md`、`test_ccbench_spawn_sites.py` は編集しない。親は着手時の fresh-worktree 前提と最新の所有面を確認する。新たに重なりが生じた場合は t2772 land 後に main を取り込む。

P1〜P5への評価：

- **P1：採用。** patch と verifier source の切替をT1943限定にする。
- **P2：採用。** v2への置換。`:3349` のschema分岐も更新する。
- **P3：採用。** apply失敗、realpath／hash失敗も明示的にstageを残す。
- **P4：採用。** 二rootとrepo cwd。stdlib JSON読取りは維持。
- **P5：採用。** 実装commit後に1本、走行中のsourceを固定する。

補正すべき点は、① verifier の source 配線追加、②「nm/strings」を実処理に合わせて記述、③ apply除去の検出をreceipt欠落に依存させない、の三点。新たな一般化や verifier／fetch の編集は不要である。

## 総括

- **scope 1**：pilot `:1533/1534` 間へ `# BEGIN/END T2780 HYDRATE INTERPRETER GATE`。契約testはgateからhydrate実呼出までを実行する。
- **scope 2**：`:1683` 直後、`build_mode()`前へ `# BEGIN/END T2780 INSTRUMENTATION PATCH`。T1943限定で適用し、`:2231` のverifier sourceもpatched `BUILD_SOURCE`へ接続する。
- **schema**：`mocc-trace-pilot-receipt/t1943-g2-v2`への**置換を推奨**。writer、admitted set、専用分岐、testを揃え、general v4を維持する。
- **親 briefへの異議**：patch適用だけではverifierのsource配線が残る。scope 2への追加が必要。TRACE=0検査の説明とapply除去のtest判定も上記のとおり補正する。
- **予算**：以後のCodex子はauthor 1＋review 2＝3本、必要時fix 1本。このplanを含め基本4本。computeは1 job。作業wallは暫定2〜4時間＋queue待ち、compute実行5〜20分見込み／予約60分。すべて見積であり、test・変異・compute結果は未実測。