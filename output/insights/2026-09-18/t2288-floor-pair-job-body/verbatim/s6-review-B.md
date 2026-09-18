## 所見

対象 HEAD は `20aca300643fc846159d4cfbe069bf43fe562627`。指定した実装ファイルに同 commit との差分はありません。以下、J=`tools/pegasus/floor_pair_campaign.sh`、S=`tools/pegasus/submit_floor_pair.sh`、T=`orchestrator/tests/test_floor_pair_job_contract.py`。変異の判定は静的予測で、実走結果ではありません。

1. **環境変数の消去範囲が裁定より狭い。— must-fix**
   - **対象:** J:35–41、S:25–31、T:217–227。
   - **何が／正しくは:** 裁定 §4.2 は「`PYTHON*/LD_*/GIT_* unset`」。実装は `GIT_*` だけ全件で、Python は3変数、LD は2変数しか消していません。例えば `PYTHONWARNINGS`、`LD_BIND_NOW`、`LD_AUDIT` は残ります。`-I` は Python の環境依存を抑えますが、LD 系の消去を代替しません。prefix 全件の消去と、その実行観測が必要です。
   - **放置時の帰結:** 裁定上消去されるはずの環境値を保持したまま driver・binary を起動でき、測定環境の受理集合が広がります。

2. **TERM 契約テストの起動条件が計算ノードに対応せず、baseline が赤い。— must-fix**
   - **対象:** T:30–33、289–306、`test_pegasus_dispatch_compute.py:4705–4718`、`focus-1.log`。
   - **何が／正しくは:** 裁定 §4.4 は signal/wait の実行観測、§4.5 は「baseline 緑必須」。`_bash()` は継承した SIGTERM disposition/mask を調整せず Bash を起動します。指定された SIG_IGN 継承条件では、Bash 内の trap 設定だけでは TERM を捕捉できません。
   - 契約テスト用の**Bash を exec する前の子プロセス**で `signal.signal(SIGTERM, SIG_DFL)` と `pthread_sigmask(SIG_UNBLOCK, {SIGTERM})` を行うべきです。TERM を送る孫だけで reset しても、受信側 Bash は直りません。
   - **放置時の帰結:** request `5523.nqsv` は **503 passed / 1 failed / 1 skipped**。child/job rc=7 は回収できていますが、`reason=completed` のままで T:306 が失敗します。

3. **signal 後に driver が成功すると、その rc を伝播しない。— must-fix**
   - **対象:** J:187–190、T:289–306。
   - **何が／正しくは:** 裁定 §4.2 は「driver rc は保存して伝播」。実装は driver rc=0 かつ signal 観測時、job rc を143/129/130へ変更します。receipt の `driver_rc` は保存されますが、プロセス終了値の伝播は一致しません。signal は記録に残し、終了値は裁定どおりにする必要があります。
   - 現テストの child は両ケースとも `exit 7` なので、この分岐を検査していません。
   - **放置時の帰結:** TERM 捕捉後に driver が正常完了しても、job は rc=143 になります。

4. **本番 TERM trap の成立条件を runbook に具体化すべき。— should**
   - **対象:** J:176–184、`docs/pegasus-runbook.md:1702–1703`。
   - **何が／正しくは:** 裁定 §4.2 の signal 記録・再 wait は、Bash が signal を捕捉可能な入口条件に依存します。runbook は signal 配送を未実測としていますが、既知の SIG_IGN 継承とその帰結までは説明していません。
   - 「本 job の Bash が TERM を ignore せず、block もしない状態で起動することは未検証。ignore 継承時は `record_signal` が発火せず、walltime 後の KILL で driver が終了し、terminal/result が残らない可能性」を追加するのが適切です。本 job の配送条件は、焦点走のテスト経路から同一と断定できません。
   - **放置時の帰結:** trap の存在を終了記録の保証と誤読し、terminal のない凍結 JSONL を残す条件を見落とします。

5. **M1・M5 の期待失敗 node 集合が不完全。— should**
   - **対象:** `s5-author.md`「変異の exact old」、T:355–359、`test_hooks.py:4448–4454,4595–4604`。
   - **何が／正しくは:** 裁定 §4.5 は M1 の観測 node を probe で採る指定です。M1 は登録簿 golden に加え、login/suspect の受理 bit と sanctioned 集合の検査にも波及します。M5 は `test_driver_argv` に加え、禁止文字列 `--validate-only` を検査する `test_no_build_or_output_replacement` でも赤になります。
   - **放置時の帰結:** KILLED 自体は正しくても、期待 node 集合との不一致を余分な回帰として誤分類します。

6. **文字列検査と抽出実行には、接続を変える変異が生存する。— should**
   - **対象:** T:217–227、340–359。
   - **何が／正しくは:** 裁定 §4.4 の実行観測は site 以降・argv・dry-run・child 回収では実装されていますが、checkout の本番接続は文字列確認にとどまります。具体例は次のとおりです。
     - S:266 の `check_checkout` を `if false; then check_checkout; fi` に変更しても、関数内の検査文字列は全部残ります。`test_checkout_and_input_binding` はこの変異を殺せません。
     - 本番トップレベルに `cmake  --build "$REPO_ROOT/build"` を追加しても、二つの空白により禁止文字列 `"cmake --build"` に一致しません。既存の肯定文字列も残り、`test_no_build_or_output_replacement` は殺せません。
   - また finalize テストは header 不一致を投入していません。M10 は window 側テストで殺せますが、finalize だけ header 比較を無効化する変異には別の負例が必要です。
   - **放置時の帰結:** detached/clean 検査の未実行、build の追加、finalize 限定の HEAD 検査欠落が、対応する契約テストを通過します。

7. **hostname と CLI に小さな逐語差がある。— nit**
   - **対象:** J:139–141、T:175–178、S:88、T:129。
   - **何が／正しくは:** 裁定 §4.2 の regex は `^bnode[0-9]+$`。実装は先に lowercase 化し、`BNODE009` も受理します。これは既存 `site_policy._first_label()` と整合しますが、裁定の正規化条件としては省略されています。§4.3 の閉集合に列挙された help は `-h` のみですが、実装・テストは `--help` も受理します。
   - **放置時の帰結:** 記載された閉集合より受理集合が広がります。driver gate の緩和とは区別し、裁定側へ正規化・alias を明記するか実装を揃えるべきです。

8. **driver gate の置換・迂回は見当たらない。前段による mask は残る。— 情報**
   - **対象:** J:157–164、224–229、S:139–182、driver:1666–1714、2205–2347、2676–2793、2995–3144。
   - **何が／正しくは:** 裁定 §4.2–4.3 どおり、元の spec path を `main()` へ渡し、window/finalize の権威経路を呼びます。`--validate-only`、site 偽装、`FP_EXPECTED_HEAD` の上書き、凍結出力の事前作成はありません。finalize 前段も header/terminal の確認に限定され、driver の全 validator をコピーしていません。
   - ただし、例えば driver 側の binary SHA 検査を削除する変異に対し、破損 binary を shell 全体へ渡すだけでは、J:229 が先に rc=4 で拒否します。その負例は driver の検査欠落を識別できません。
   - **放置時の帰結:** M1〜M10 の殺傷を driver の検査強度の証明へ拡張すると、driver 変異が前段拒否に隠れます。

## 裁定照合表

「一致」は静的な実装照合です。裁定 §4.2 本文は拒否 token 全一覧、PBS_JOBID regex、result field 集合までは列挙していないため、それらの完全な「裁定との逐語一致」は主張しません。

| 裁定 | 項目 | 判定 | 照合結果 |
|---|---|---|---|
| §4.2 | 段順序 | 一致 | bootstrap → environment → interpreter → commands → checkout → input → site → time → scratch → time → driver → EXIT result。argv 構築は前倒しだが起動は driver 段 |
| §4.2 | PBS_*・FP_* 8変数 | 一致 | 必須10変数を確認。nonce=32hex、HEAD=40hex、SHA=64hex、mode/window の整合を検査 |
| §4.2 | PBS_JOBID | 一致〔既存例〕 | `^([0-9]+:)?[A-Za-z0-9._-]+$`。指定 A-5 の regex と同一 |
| §4.2 | spec/evidence/walltime 入力 | 一致・超過 | spec は凍結3 path に限定。evidence は絶対に加え既存 directory を要求。walltime は2桁HH、MM/SS範囲、正値を検査 |
| §4.2 | 固定 PATH・環境消去 | **緩和** | PATH/PBS保持/GIT全消去は一致。PYTHON*/LD_* は所見1 |
| §4.2 | interpreter | 一致 | `python3.10 python3.11 python3.12 python3`、realpath、実行可、≥3.10 |
| §4.2 | commands | 一致 | `git nm pgrep sha256sum hostname date realpath mkdir env` の9本 |
| §4.2 | checkout | 一致 | PBS_O_WORKDIR と Git root の双方を `realpath -e`。symlink 越しでも同じ実体なら一致。HEAD と期待値を比較 |
| §4.2 | input preflight | 一致 | spec 実 SHA、`artifacts[]` 全件の実在・実行可・実 SHA |
| §4.2 | hostname | **緩和〔逐語〕** | 第一 label 全体に regex。ただし lowercase 化を追加。所見7 |
| §4.2 | time・再検査 | 一致 | `now >= not_before`、`now + duration <= not_after`。scratch 後にも実時計で同関数 |
| §4.2 | scratch | 一致 | `/scr/${PBS_JOBID//:/_}`、`mkdir -m 0700` 1回、TMPDIR export、shimなし |
| §4.2 | driver argv | 一致 | `-I -B -c`、sys.path 挿入、`main()`、window ID付き execute／finalize |
| §4.2 | stdout/stderr | 一致 | noclobber で両方を開いてから child 起動。片方の衝突でも driver 未起動 |
| §4.2 | background/wait/signal | 一致〔条件付き〕 | 再 wait と signal 記録あり。ignore継承時の実効性は所見2・4 |
| §4.2 | result create-only | 一致 | `open(..., "x")`。shell noclobber と競合しない |
| §4.2 | EXIT trap | 一致〔範囲限定〕 | interpreter 選択後に設置。以後の `fail`/exit でも保存を試行。bootstrap・environment・interpreter失敗では保存しない |
| §4.2 | 入力2／前段4／receipt5 | 一致〔優先順位あり〕 | 入力・command不足2、checkout以降の前段4。result保存失敗は5。ただし既存の非0 driver rcを優先して保持 |
| §4.2 | driver rc伝播 | **超過** | signal観測時に driver rc=0 を非0へ変更。所見3 |
| §4.3 | 引数閉集合 | **緩和〔逐語〕** | workload/window/finalize/dry-runは一致。`--help`追加 |
| §4.3 | pin 3組 | 一致 | D2138項7・Sのcase・実file SHAを全64桁照合、すべて一致 |
| §4.3 | root/detached/clean | 一致 | canonical root、symbolic-ref rc=1のみ受理、0とその他を区別、`--untracked-files=no` |
| §4.3 | spec実file/HEAD blob | 一致 | 両方のSHAを独立取得しpinと比較。pipelineにpipefailあり |
| §4.3 | binary全件 | 一致 | 全 artifacts を検査 |
| §4.3 | window time/A5/A1 | 一致〔順序差あり〕 | 条件は全部存在。w2ではspec配列順にw1のA1を先に行うため、A5→A1の逐語順ではない。受理集合は同じ |
| §4.3 | finalize前段 | 一致 | summary不在、両窓存在、header一致、末尾terminal。`incomplete`を排除しない |
| §4.3 | evidence leaf | 一致 | 固定base、nonce32hex、baseのみmkdir-p、leafは0700で1回作成 |
| §4.3 | pre-submit→dry-run | 一致 | pre-submitを `"x"` で保存後、dry-run receiptを書いてreturn。qsubなし |
| §4.3 | cd/qsub argv | 一致 | `cd -P`、`-l/-N/-v/-o/-e`、相対script literal。walltimeはmode別の1箇所 |
| §4.3 | 8変数の値 | 一致 | comma・空白・`=`を含む値なし。spec pathには `/` と英数字もあるが、qsub分割を壊す文字はない |
| §4.3 | receipt status | 一致 | 最終receiptはdry_run/submitted/failed/indeterminate。pre-submitだけprepared |
| §4.3 | 再投入 | 一致 | 自動再投入経路なし |
| §4.3 | `check_outputs \|\| exit $?` | 一致 | 関数内ERR/errexitは抑制されるが、唯一のPython commandのrcをそのままexit。通常の拒否JSONをERR trapが重ねない |
| §4.1 | 登録簿・golden・runbook | 一致 | 下記の2 entryと3 golden、投影2行が一致 |

拒否 token は、bootstrap の `missing_binding/invalid_*`、interpreter の `python_unavailable`、commands の `required_command_missing`、checkout の `root_*/head_*`、spec の `hash_*`、binary の `missing_or_mismatch`、site の `compute_node_required`、window の `before_window/insufficient_remaining_time/invalid_window/clock_unavailable`、scratch の `create_failed`、driver の stream拒否、result の `receipt_failed` と固定 literal です。通常の明示拒否は1行JSONです。result保存にも失敗した場合は、その追加拒否行が出ます。

`job-result.json` の実 field 集合は次の16個で、T:259 の期待集合と一致します。

```text
schema_version pbs_jobid hostname nonce expected_head spec_relpath
spec_sha256 mode window_id driver_rc driver_stdout_sha256
started_epoch completed_epoch job_rc gate reason
```

登録簿 J entry は76行、S entryは352行。両者とも field順は `class, reason, primary_gate, evidence`、追加位置はpathソート順です。evidence はそれぞれ `static job-body classification`、`static login-side submitter classification`。`test_hooks.py` のclass期待値3176/3222行、全field期待値3314/3590行、local-ok evidence期待値4125行と一致します。runbook §7.0 の516/563行も同じpath/class/evidenceです。

pin の照合値：

| workload | D2138・実装・実bytesで一致したSHA-256 |
|---|---|
| rr95 | `990e3a6feb176ccf863315fde6e2afce43b7fc16053f50a1080641dde2570619` |
| rr50 | `b582d20c37268f491e4c47bb7436731197c18e737cdcca43694c64fa3e0d5e37` |
| rr5 | `d13c384473a5d24170e929f7e17aad9cc24479a5487ed0da21d06bc45430d8c4` |

login側の `python3` が3.9でも、固定PATHに使用可能な `python3.10` があれば先に選びます。3.10がなければ3.11→3.12→python3の順に試し、最後の3.9も拒否します。

## 変異 × test の殺傷表

baseline赤は変異のkillに数えません。以下は所見2を解消したbaselineに対する静的予測です。

| ID | author の exact old/new | 判定 | 検出根拠・期待nodeの補正 |
|---|---|---|---|
| M0 | J:203の通常commentへ`deliberately`追加 | **SURVIVED、等価** | 抽出範囲にも実行意味にも影響なし。非等価M0には該当しない |
| M1 | job entryのclassをlocal-okへ | **KILLED** | `test_registry_entries`、hook schema/golden。さらに `test_bash_pegasus_registry_login_and_suspect_bits_are_pinned`、`test_bash_sanctioned_pegasus_paths_are_derived_from_registry` も赤になる。完全集合はprobeで確定 |
| M2 | rr95 pin先頭9→8 | **KILLED** | `test_frozen_spec_pins` が抽出caseの出力を独立したD2138期待SHAと比較 |
| M3 | Jの`<=`→`<` | **KILLED** | `test_window_gate_boundaries` が6窓全部で `now=not_after-86400` の受理を要求 |
| M4 | hostname判定command→`:` | **KILLED** | `test_hostname_gate` のpegasus02・bnode009evil・空文字負例がrc=0になり失敗 |
| M5 | execute-window→validate-only | **KILLED** | `test_driver_argv` の実配列比較に加え、`test_no_build_or_output_replacement` も赤 |
| M6 | runbook §7.0 job行削除 | **契約testではSURVIVED／checkerでKILLED予測** | 対象oldはrunbook:516に存在。裁定のDW-O19対象。今回checkerは未実行 |
| M7 | site呼出しを`if false`内へ | **KILLED** | `test_gate_order_and_calls` のtraceからsiteが欠落。STOP=siteのrc期待にも違反 |
| M8 | `if (( DRY_RUN ))`反転 | **KILLED** | `test_dry_run_has_no_execution` のqsub呼出痕跡・statusが反転 |
| M9 | scratchのcolon正規化削除 | **KILLED** | `test_scratch_name_normalizes_colon` の実代入結果が `/scr/0:123.nqsv` になる |
| M10 | loaded_head比較を`if False`へ | **KILLED** | `test_submitter_head_consistency_preflight` のdifferent header負例が通過して失敗。finalize専用testには不一致負例がない |

author の報告は「未実走」「殺傷未観測」と明記しており、緑を装った不一致はありません。ただし期待node表は所見5の補正が必要で、現在の統合状態は親の焦点走によって「未実走」から「baselineに1件の失敗あり」へ更新されています。

## GO / NO-GO

**NO-GO。must-fix は所見1・2・3。**

特に baseline 赤のままでは、裁定 §4.5 の条件を満たさず変異結果の帰属も確定できません。修正後、親側で焦点走と期待node集合の観測が必要です。

## 総括

凍結pin、driver起動経路、create-only、登録簿・golden・runbook投影は整合しています。
環境消去の不足、TERMテストの入口条件、signal時の成功rc変更が必須修正です。
M0は等価で、M1〜M10の意図した検出は静的に成立しますが、M1・M5の期待node集合は不足しています。
pytest・実driver・qsub・ファイル変更は行っていません。実走証拠は親のrequest 5523.nqsvのみです。

補助的なPythonによる登録簿・golden自動照合は、PreToolUse hookがJSON pathを「未登録Pegasus実行体」と分類して実行前に拒否しました。迂回せず、当該照合はソースの静的読解による判定としています。