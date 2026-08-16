結論は、投入器の同名 CLI flagを起点に、承認時だけ exact literal `1` の env と exact Boolean `true` の receipt fieldを生成し、job 側で両者の一致を必須にする形を推奨する。未承認時は env と field をともに省略し、既存 argv・receipt schema・serializer を維持する。

## 1. `tools/pegasus/submit_floor.sh`

### 引数の受理

- [tools/pegasus/submit_floor.sh:7-11](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1180-pilot-approval/tools/pegasus/submit_floor.sh:7) の usage に、値を取らない `--confirm-irreversible-pilot-holdout` を追加する。driver の既存 flag と同名にして別名を増やさない。
- [同:28-34](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1180-pilot-approval/tools/pegasus/submit_floor.sh:28) に `CONFIRM_IRREVERSIBLE_PILOT_HOLDOUT=0` を置く。
- [同:36-70](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1180-pilot-approval/tools/pegasus/submit_floor.sh:36) の `case` に zero-arity flag として追加し、指定時だけ値を `1` にする。後続の値を消費しないため、`--confirm-... true` は `true` が unknown argument となって拒否される。
- [同:72-76](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1180-pilot-approval/tools/pegasus/submit_floor.sh:72) の override 制限には加えない。承認 flag は実投入でも必要であり、`--dry-run` 専用 override ではない。`--dry-run` と併用した場合は意図だけを記録し、[同:429-439](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1180-pilot-approval/tools/pegasus/submit_floor.sh:429) により qsub は実行しない。

### env 伝播

[同:411-423](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1180-pilot-approval/tools/pegasus/submit_floor.sh:411) は次の骨格にする。

```bash
export_spec="IZANAGI_SUBMISSION_NONCE=$NONCE"
if [[ "$CONFIRM_IRREVERSIBLE_PILOT_HOLDOUT" -eq 1 ]]; then
  export_spec+=",IZANAGI_CONFIRM_IRREVERSIBLE_PILOT_HOLDOUT=1"
fi
```

- env 名は `IZANAGI_CONFIRM_IRREVERSIBLE_PILOT_HOLDOUT`。
- 承認値は exact literal `1`。`true`、`yes`、`0` などの truthy/falsey 解釈は導入しない。
- 未指定時は `=0` を出さず、env 項目そのものを省略する。これにより既存の `export_spec` と qsub argv は承認関連では 1 byte も変わらず、I1/I4を保つ。
- `qsub -v` へは一つの comma-separated operand が渡る。現状は nonce だけ、承認時は nonce と上記 env の2本だけであり、`-V` のような submitter 環境全体の転送にはしない。

### pre-submit / submit-receipt

field は両方へ追加するが、承認時だけ存在させる。

- key: `confirm_irreversible_pilot_holdout`
- JSON 型: exact Boolean
- 承認時: `true`
- 未承認時: field 自体を省略。`false` は書かない。
- schema version:既存の `pegasus-floor-pre-submit/v1` と `pegasus-floor-submit-receipt/v1` を維持する。

具体的には次を行う。

- [同:331-340](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1180-pilot-approval/tools/pegasus/submit_floor.sh:331) の pre-submit writer argv に shell の `0`/`1` を追加し、[同:353-368](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1180-pilot-approval/tools/pegasus/submit_floor.sh:353) で値が `"1"` の場合だけ `payload[key] = True` を実行する。
- [同:466-485](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1180-pilot-approval/tools/pegasus/submit_floor.sh:466) の receipt writer は pre-submit の field をコピーする。field が存在するのに値が `True` 以外なら writer 自体を失敗させ、偽値を正規化して消さない。
- [同:369-371](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1180-pilot-approval/tools/pegasus/submit_floor.sh:369) と [同:486-495](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1180-pilot-approval/tools/pegasus/submit_floor.sh:486) の serializer 設定は変更しない。
- `sort_keys=True` により、承認時は ASCII 順で `confirm_irreversible_pilot_holdout` が object の先頭 key になる。receipt では compact な `"confirm_irreversible_pilot_holdout":true` となる。未承認時は field が無いため、既存の key 順・空白・separator に承認関連の差分は生じない。
- 裁定控えの絶対 path や承認者 identity は field に足さない。authority の参照は親が段7で既存の裁定控え `2026-08-16-rulings-full-43rulings.md §3.3` へ結ぶ。

## 2. `tools/pegasus/floor_campaign.sh`

### env の受領と exact literal 検査

- scheduler が `qsub -v` の値を job 環境へ設定した後に script が起動する。
- [tools/pegasus/floor_campaign.sh:27](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1180-pilot-approval/tools/pegasus/floor_campaign.sh:27) は Python 系3変数しか unset しないため、承認 env をここへ追加して消してはならない。
- [同:32-35](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1180-pilot-approval/tools/pegasus/floor_campaign.sh:32) の nonce bootstrap 検査直後に、承認 env が「未設定」または exact `1` のどちらかであることを検査する。`${VAR+x}` で未設定と空文字を区別し、設定済みなら `1` 以外を bootstrap `rc=4` で拒否する。これにより `set -u` 下で未設定を正常系として扱える。
- nonce 検査は独立のまま残す。承認 env は nonce の代用にも、nonce 不正の救済にも使わない。

### receipt の closed set と env 束縛

[同:405-493](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1180-pilot-approval/tools/pegasus/floor_campaign.sh:405) の既存 Python 呼出しを再利用し、新しい Python process は増やさない。

- [同:417-423](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1180-pilot-approval/tools/pegasus/floor_campaign.sh:417) の duplicate key 拒否はそのまま維持する。
- [同:428-441](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1180-pilot-approval/tools/pegasus/floor_campaign.sh:428) の `top_keys` を base set として保持し、許可する集合を次の2個だけにする。

```python
base_top_keys
base_top_keys | {"confirm_irreversible_pilot_holdout"}
```

- optional key がある場合は `document[key] is True` を要求する。`False`、整数 `1`、文字列 `"true"`、`null` はすべて拒否する。未知の追加 key も従来どおり拒否する。
- validator は receipt に field があれば `"1"`、無ければ `"0"` を command substitution 内へ出す。shell 側でも env を `"1"`/`"0"` に正規化し比較する。
- [同:491-494](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1180-pilot-approval/tools/pegasus/floor_campaign.sh:491) の strict validation 成功後、[同:496](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1180-pilot-approval/tools/pegasus/floor_campaign.sh:496) の source identity 検査より前に不一致を止める。

両方向の不一致に対する停止は次で固定する。

```bash
write_failure 2 submit_binding \
  "pilot holdout confirmation differs between qsub environment and submit receipt"
exit 2
```

これにより env だけが `1`、または receipt だけが `true` のどちらでも、build・driver 起動前に `failure.json` を create-only で残して停止する。[同:180-215](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1180-pilot-approval/tools/pegasus/floor_campaign.sh:180) の既存 writer と stage 名を再利用し、新しい失敗記録機構は作らない。

### driver argv

[同:947-965](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1180-pilot-approval/tools/pegasus/floor_campaign.sh:947) は bash 配列へ置き換える。

```bash
driver_argv=(
  "$PY" -I -B "$REPO_ROOT/orchestrator/campaign/s8b_floor_campaign.py"
  --mode pilot
  --protocol "$REPO_ROOT/$PROTOCOL_PATH"
)
if [[ "${IZANAGI_CONFIRM_IRREVERSIBLE_PILOT_HOLDOUT-}" == "1" ]]; then
  driver_argv+=(--confirm-irreversible-pilot-holdout)
fi

driver_rc=0
"${driver_argv[@]}" \
  >&"$DRIVER_STDOUT_FD" 2>&"$DRIVER_STDERR_FD" || driver_rc=$?
```

- 未承認時の実 argv は現在の4引数と完全一致する。
- 承認時だけ既存 CLI flag を末尾へ1回 append する。
- `eval`、文字列再解釈、無条件 flag は使わない。
- `"$PY" -I -B` は同じ行に残し、既存の interpreter 文字列・呼出し数 pin を維持する。
- [s8b_floor_campaign.py:5255-5263](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1180-pilot-approval/orchestrator/campaign/s8b_floor_campaign.py:5255)、[同:6197-6200](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1180-pilot-approval/orchestrator/campaign/s8b_floor_campaign.py:6197)、[同:6402-6407](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1180-pilot-approval/orchestrator/campaign/s8b_floor_campaign.py:6402) は編集しない。

## 3. `orchestrator/tests/test_pegasus_floor_tools.py`

[orchestrator/tests/test_pegasus_floor_tools.py:36-61](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1180-pilot-approval/orchestrator/tests/test_pegasus_floor_tools.py:36) の `PRE_KEYS` / `RECEIPT_KEYS` は未承認 base schema のままにする。別に confirmation key 定数と `BASE_KEYS | {confirmation_key}` を置く。

追加テストは次のとおり。

1. `test_submit_floor_explicit_pilot_confirmation_is_exported_and_recorded`

   [同:1198-1245](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1180-pilot-approval/orchestrator/tests/test_pegasus_floor_tools.py:1198) の helper に追加引数を渡せるようにし、実 qsub stub へ flag 付き投入を行う。qsub `-v` が `nonce,IZANAGI_CONFIRM_IRREVERSIBLE_PILOT_HOLDOUT=1`、pre/receipt の field が `is True`、key 集合が base+1、compact receipt が canonical であることを固定する。env が欠落・値違い・field が欠落/文字列/unsorted なら赤になる。

2. `test_submit_floor_confirmation_dry_run_is_scheduler_free`

   [同:1098-1175](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1180-pilot-approval/orchestrator/tests/test_pegasus_floor_tools.py:1098) と同じ sentinel 構成で `--dry-run --confirm-...` を実行する。qsub 系 sentinel が作られず、両 JSON に `true` と `dry_run: true` が残ることを固定する。承認 flag が dry-run を迂回して scheduler を呼べば赤になる。

3. `test_floor_job_bootstrap_rejects_nonliteral_confirmation_environment`

   [同:254-324](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1180-pilot-approval/orchestrator/tests/test_pegasus_floor_tools.py:254) の preflight fixture に追加 env を渡せる seam を設け、空文字、`0`、`true`、`yes` を parameterize する。bootstrap `rc=4`、scratch/output/driver marker が未変更であることを固定する。truthy 判定や空文字を未設定扱いすると赤になる。

4. `test_submit_receipt_confirmation_round_trips_through_job_validator`

   [同:1839-1879](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1180-pilot-approval/orchestrator/tests/test_pegasus_floor_tools.py:1839) の validator fragment に、field=`true` かつ env=`1` の confirmed receipt を通す。optional top key、exact Boolean、env 正規化がすべて整合しないと赤になる。

5. `test_submit_receipt_confirmation_mismatch_records_submit_binding_failure`

   receipt=`true`/env 未設定と、receipt field 無し/env=`1` の2方向を parameterize する。いずれも rc=2、stage=`submit_binding`、上記 exact message で `write_failure` が1回呼ばれることを固定する。片側だけで driver 適格になる、または silent exit すると赤になる。

6. `test_submit_receipt_rejects_non_true_confirmation_field`

   optional field の値を `False`、整数 `1`、文字列 `"true"`、`None` に差し替え、strict validation が rc=2 になることを固定する。Python の truthiness や `bool(value)` を使うと赤になる。未知の top-level key も同じ test matrix に含め、closed set を保つ。

7. `test_floor_job_confirmation_controls_only_driver_flag`

   [同:987-1052](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1180-pilot-approval/orchestrator/tests/test_pegasus_floor_tools.py:987) の argv recorder を未設定/`1` の2ケースへ拡張する。未設定時は現行4引数、`1` 時は同じ4引数の末尾に flag がちょうど1個あることを固定する。無条件付与、重複、protocol argv の分割・順序変更で赤になる。

### 既存 pin の全件影響

限定 grep では、推奨形で赤になる既存テストは0件と見込む。次の pin を壊さない書式が前提である。

- `test_floor_job_hardens_interpreter` [同:686-699](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1180-pilot-approval/orchestrator/tests/test_pegasus_floor_tools.py:686): `"$PY" -I -B` 15回、submit 側 Python 5回、driver path 文字列を pin。Python process を増やさず、array 内でも同じ文字列を残すため緑。
- `test_floor_job_invokes_fixed_pilot_cli_without_bypass` [同:987-1052](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1180-pilot-approval/orchestrator/tests/test_pegasus_floor_tools.py:987): 未承認 argv、driver path 1回、`--mode pilot` 1回を pin。未承認分岐を不変にするため緑。
- `test_floor_job_does_not_swallow_driver_rc` [同:1055-1062](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1180-pilot-approval/orchestrator/tests/test_pegasus_floor_tools.py:1055): `|| driver_rc=$?` と最終 exit を pin。配列起動でも同じ literal を保つため緑。
- `test_submit_floor_qsub_exports_nonce_without_third_party_cache` [同:1065-1074](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1180-pilot-approval/orchestrator/tests/test_pegasus_floor_tools.py:1065): initial `export_spec` を完全一致で pin。初期代入を変えず、承認時だけ後置 append するため緑。
- `test_submit_floor_dry_run_is_scheduler_free_and_writes_exact_receipts` [同:1098-1175](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1180-pilot-approval/orchestrator/tests/test_pegasus_floor_tools.py:1098): base `PRE_KEYS` / `RECEIPT_KEYS` と scheduler-free を pin。未承認時は field を省略するため緑。
- `test_submit_floor_non_dry_run_success_writes_real_submission_record` [同:1211-1245](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1180-pilot-approval/orchestrator/tests/test_pegasus_floor_tools.py:1211): default qsub argv を完全一致で pin。未承認時に env を出さないため緑。
- `test_submit_receipt_round_trips_through_job_validator` [同:1851-1879](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1180-pilot-approval/orchestrator/tests/test_pegasus_floor_tools.py:1851): field 無しの既存 receipt を pin。base set を許すため緑。
- `_driver_tail()` を使う driver/result 系テスト [同:1882-1884](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1180-pilot-approval/orchestrator/tests/test_pegasus_floor_tools.py:1882)、[同:2005-2276](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1180-pilot-approval/orchestrator/tests/test_pegasus_floor_tools.py:2005): env 未設定でも `set -u` に触れない `${VAR-}` を使うため緑。
- 別ファイルでは driver gate/CLI flag が [test_s8b_floor_campaign.py:4035-4051](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1180-pilot-approval/orchestrator/tests/test_s8b_floor_campaign.py:4035) に既に pin されており、driver 無編集なので緑。`certified_writer_fixtures.py:129-149` の default receipt fixtureも field 無しのまま緑。
- shell script の総行数 499/1135 を pin するテストは限定 grep で0件。行数に近い pin は上記 Python 呼出し回数だけである。

## 4. I1〜I5 の対応

- **I1**: zero-arity submit flagを既定0とし、env・receipt field・driver flagを承認時だけ生成し、env/receipt 一致も要求する。
- **I2**: `s8b_floor_campaign.py:5255-5263` は無編集で、既存 CLI flag を通じて exact Boolean `True` を渡すだけにする。
- **I3**: 既存 CLI、`qsub -v`、既存 receipt、既存 `write_failure` だけを使い、store・署名・鍵・allowlist・新台帳を作らない。
- **I4**: 未承認時は env と optional field を省略し、runtime driver argv、base key 集合、serializer、既存テスト期待値を維持する。
- **I5**: confirmation flag の有無にかかわらず `DRY_RUN=1` は `qsub_cmd` を構築・表示するだけで、`qsub` を実行しないことを専用テストで固定する。

## 5. P2 receipt 束縛の推奨

receipt 束縛は採用を推奨する。

env だけでは、job 側は「submitter の明示 CLI flag から生成された `1`」と「別経路で注入された `1`」を識別できず、I1 の「投入時に明示」を transport の存在だけへ弱めてしまう。一方、既存 receipt は nonce、job ID、source commit、job script hash と既に束縛され、job 側も create-only copy 後に strict validation している。この既存 record に optional Booleanを一つ載せ、env と一致させるのが最小の provenance 追加である。

これは新しい承認機構とは評価しない。承認を決める authority は人間の CLI flag と既存裁定控えのままで、receipt field は決定・保管・再利用を行わない単なる per-submission evidence だからである。署名や identity 保証も追加せず、粗い provenance の範囲に留まる。ただし既存 v1 の accepted key set を広げるため、confirmed receipt を読む strict consumer の互換性が最大の検査点になる。

## 6. リスク

1. [floor_campaign.sh:428-441](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1180-pilot-approval/tools/pegasus/floor_campaign.sh:428): producer だけ field を追加すると confirmed job がすべて top-level mismatch で停止する。逆に field を常時必須にすると旧/default receipt を拒否する。
2. [submit_floor.sh:411-423](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1180-pilot-approval/tools/pegasus/submit_floor.sh:411): comma、順序、値の引用を誤ると nonce まで job に届かなくなる。未承認時の initial assignment を触らないことが重要。
3. [floor_campaign.sh:27-35](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1180-pilot-approval/tools/pegasus/floor_campaign.sh:27): 承認 env を `unset` へ加える、または未設定変数を直接展開すると、正当な confirmed job や既定 job が bootstrap で落ちる。
4. [floor_campaign.sh:961-965](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1180-pilot-approval/tools/pegasus/floor_campaign.sh:961): flag の無条件 append は一回性 holdout を既定で消費する重大回帰。配列条件と2ケース argv testが必須。
5. [submit_floor.sh:369-371](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1180-pilot-approval/tools/pegasus/submit_floor.sh:369) と [同:486-495](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1180-pilot-approval/tools/pegasus/submit_floor.sh:486): field を常時 `false` で書くと default receipt schema・canonical bytes が変わり、I4と既存 exact-key tests を破る。
6. [floor_campaign.sh:380-494](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1180-pilot-approval/tools/pegasus/floor_campaign.sh:380): env/receipt 比較を driver 後へ置くと不可逆消費後の検出になる。strict receipt 成功直後、source/build/driver 前で停止させる必要がある。
7. `pegasus-floor-submit-receipt/v1` の optional 拡張は、古い exact consumer が confirmed receipt だけを拒否する可能性がある。限定 grep で test fixture は default schema のみだったため、confirmed path の新規 validator testを代替証拠にする。

## 総括

- 推奨形は、同名 CLI flag → 承認時だけ env=`1` → optional receipt Boolean=`true` → 両者一致後だけ driver flag、である。
- 未承認時は env/fieldを省略し、既存 argv・base receipt・Python 呼出し回数を維持する。
- 最大のリスクは receipt v1 の exact key consumer と、driver flag の誤った無条件付与である。
- 親が段4で裁定すべき択一は P2 であり、本起草は既存 receipt への optional 束縛を採用する側を推奨する。
- 本起草では編集・pytest・Web アクセスを行っていない。