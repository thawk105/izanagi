## 判定

**NO-GO。must-fix 8 件です。** 静的検査のみ行い、file 書込み、pytest、commit、job 投入は行っていません。

## 所見

### must-fix 1 — `set +e` でも ERR trap が発火し、負の測定結果が二重出力になる

**主張:** Python の終了コード 1 を捕捉するつもりの箇所で `ERR` trap が生きたままです。環境変数の欠落・不一致という正規の負結果では、Python の詳細結果行と PBS shell の fallback 行が両方 stdout に出ます。

**根拠:** `ERR` trap は `tools/pegasus/probes/t1259_qsub_env_delivery_probe.pbs:29`、Python 呼出し前の `set +e` は同 `:90`、終了コード取得は同 `:95` です。Bash では `set +e` は `ERR` trap を無効化しません。Python は `ok=false` なら詳細行を flush して 1 を返します (`tools/pegasus/probes/t1259_qsub_env_delivery_probe.py:727-729,798-808`)。その 1 で trap が先に `fail_pbs` を呼ぶため、`:95-100` には到達しません。

**放置すると成果物の何が変わるか:** **これを直さないと、2 本目・3 本目の `-v` 欠落という測りたい負結果が「単一の権威結果」ではなく、内容の異なる 2 本の prefixed JSON になり、配送失敗と probe shell failure の受理集合を分離できません。**

**提案:** 子 stdout を scratch の専用 file に捕獲し、終了後に「prefixed JSON がちょうど 1 行」を検証してから PBS stdout へ 1 回だけ出してください。子の非 0 を取得する部分は `if ...; then ...; else rc=$?; fi` 等で `ERR` trap の対象外にし、行が無い、複数、parse 不可の場合だけ shell fallback を出すべきです。

### must-fix 2 — queued 中に submit-tree が変わると、未 commit の campaign を実行しても green になる

**主張:** submit 時には clean を確認しますが、job 開始時には HEAD と working-tree bytes の一致を要求していません。特に R2 が実行する campaign source は manifest hash に含まれません。

**根拠:** clean 検査は submit 時だけです (`tools/pegasus/probes/t1259_qsub_env_delivery_submit.sh:74-88`)。PBS 側は source の実在と tracked 性しか見ません (`tools/pegasus/probes/t1259_qsub_env_delivery_probe.pbs:47-62`)。manifest は HEAD と probe.py の hash だけを検証します (`tools/pegasus/probes/t1259_qsub_env_delivery_probe.py:227-239`)。repo snapshot は前後が等しいかしか判定せず、開始時から `tracked_status` が dirty でも green です (`:567,722-729`)。その状態で R2 は working tree 上の campaign を直接実行します (`:693-698`)。

**放置すると成果物の何が変わるか:** **これを直さないと、結果が commit の HEAD を参照しながら、実際の拒否値は別 bytes の campaign から得られます。承認拒否の観測値と参照 commit が食い違います。**

**提案:** job 開始時と終了時の両方で tracked-clean、全 untracked 集合、必要なら ignored 生成物まで拒否してください。probe、PBS、campaign の bytes を manifest または Git blob と照合し、submit-tree は 3 request の終端まで immutable としてください。

### must-fix 3 — group manifest を完了状態へ更新する経路が存在しない

**主張:** group manifest は 3 回の qsub 後に一度作るだけで、terminal state と結果 hash を回収する実装がありません。途中の qsub 失敗では group manifest 自体が作られません。

**根拠:** R1、R2、R3 を先に逐次投入し (`tools/pegasus/probes/t1259_qsub_env_delivery_submit.sh:424-439`)、その後に manifest を作ります (`:441-498`)。`terminal_state` は常に `"not-observed-by-submitter"` (`:469`)、`result_sha256` はその瞬間に `result.json` があれば読むだけです (`:470-473`)。stdout が一次 evidence なのに hash 対象は補助 `result.json` です (`tools/pegasus/probes/t1259_qsub_env_delivery_probe.py:784-807`)。段 4 裁定は terminal state と result hash の記録を要求しています (`s4-adjudication.md:85-88`)。

**放置すると成果物の何が変わるか:** **これを直さないと、実装が生成できる group 成果物は永久に indeterminate であり、部分投入時は期待 request 集合さえ残りません。成功した request だけを参照集合へ入れる誤読が可能になります。**

**提案:** 最初の qsub より前に create-only の group intent を書き、request ごとの受付 sidecar を追加してください。別の明示的な completion 処理で terminal state、prefixed stdout 行、その hash、scheduler evidence を検査し、create-only の completion manifest を発行してください。初期 manifest の上書きは避けるべきです。

### must-fix 4 — R1 の配送失敗時にも `projected_outcome="approval-bound"` と記録する

**主張:** source projection が観測値ではなく request ID で分岐しています。R1 の approval が届かなかった場合でも categorical outcome は `"approval-bound"` になります。

**根拠:** R1 分岐は approval の存在・一致に関係なく文字列を固定し、bool だけを実測値から計算します (`tools/pegasus/probes/t1259_qsub_env_delivery_probe.py:353-373`)。missing-value test は comparison だけを検査し、この projection の矛盾を見ません (`orchestrator/tests/test_t1259_qsub_env_delivery_probe.py:230-261`)。

**放置すると成果物の何が変わるか:** **これを直さないと、2 本目の `-v` が届かない実測で、JSON の categorical 値が「承認束縛済み」となり、同じ成果物内の `official_approval_bound=false` と矛盾します。**

**提案:** R1/R2 も実際の `approval_present`、approval、nonce から outcome を導出し、文字列と bool の整合を invariant にしてください。欠落、mismatch、unexpected-present の各負例を追加してください。

### must-fix 5 — scheduler preflight と qsub 後の有効性確認が状態を gate していない

**主張:** preflight は command の rc しか見ず、`gen_S` が DIS/INA でも進みます。また qsub rc=0 の後に request の可視性を確認していません。

**根拠:** `qstat -Q`、`pegasusinfo`、`qstat` は保存されますが、失敗判定は rc のみです (`tools/pegasus/probes/t1259_qsub_env_delivery_submit.sh:146-205`)。qsub 後は stdout から ID を parseして receipt を書くだけです (`:388-421`)。対象 file 内の `qstat -f` hit は 0 件でした。runbook は queue が DIS/INA なら投入禁止 (`docs/pegasus-runbook.md:338-340`)、背景 session からの投入では直後の可視性確認が必須です (`:1654-1667`)。さらに `qstat` は不存在でも rc=0 を返し得ます (`:169-181`)。

**放置すると成果物の何が変わるか:** **これを直さないと、実行不能 queue や無効な request ID が「submitted」として group の参照集合に入り、結果欠落を env 配送失敗または probe failure と誤分類します。**

**提案:** `gen_S` の semantic state を parse して利用不能なら qsub 前に停止してください。各 qsub 後は `qstat -f` 本文を poll し、ID、job name、owner、queued/running state を確認して receipt に束縛してください。terminal と計算ノード marker は completion 処理で回収してください。

### must-fix 6 — submitter に core dump 防止がなく、detached submit-tree を汚せる

**主張:** PBS job には `ulimit -c 0` がありますが、login-side submitter にはありません。submitter は clean 検査後も repo cwd で複数の外部 process を起動します。

**根拠:** submitter 冒頭は `set`、`umask`、`GIT_OPTIONAL_LOCKS` だけです (`tools/pegasus/probes/t1259_qsub_env_delivery_submit.sh:3-5`)。interpreter、Git、qstat、sha256sum 等を起動し (`:43-229`)、qsub 直前にも repo root へ移動します (`:390-396`)。`ulimit -c 0` の hit は 0 件です。対して PBS は外部 command より前に core を無効化し (`tools/pegasus/probes/t1259_qsub_env_delivery_probe.pbs:8-10`)、Python 前に scratch へ移動します (`:89`)。

**放置すると成果物の何が変わるか:** **これを直さないと、submitter または qsub client の異常終了が repo 内へ core file を作り、clean な固定 SHA という参照条件を壊した後でも job が測定を続行できます。**

**提案:** submitter 冒頭で `ulimit -c 0` を fail-closed に適用し、attempt root 作成後の preflight は外部 cwd で行ってください。各 qsub の直前と submitter 終了時にも repo clean を再確認してください。

### must-fix 7 — 未実測 submitter を `local-ok` にして admission 受理集合を広げている

**主張:** 新 submitter は静的分類だけで `local-ok` になっていますが、射影された runbook は新規 `local-ok` に実測を要求しています。

**根拠:** registry は `class="local-ok"`、`evidence="static login-side submitter classification"` です (`tools/pegasus/admission_registry.json:136-140`)。runbook は `local-ok` を規範値未満の実測済みと定義し (`docs/pegasus-runbook.md:442-448`)、legacy 4 本以外を `local-ok` にするにはユーザー端末での実測が必要としています (`:477-483,570-584`)。

**放置すると成果物の何が変わるか:** **これを直さないと、PEGASUS_LOGIN / PEGASUS_SUSPECT の admission 受理集合に、規定された資源証拠を持たない新 executable が追加されたままになります。**

**提案:** runbook の required fields を満たすユーザー端末実測を取得するまでは `unknown` にしてください。静的 login-side 分類を新しい例外として認める意図なら、先に明示裁定を取り、定義と registry を同時に更新してください。

### must-fix 8 — 新規 test が実装定数を fixture に戻し、cross-file 不整合を恒真化する

**主張:** manifest fixture が observer の schema、authority、request labels、env 順序をそのまま参照します。submitter は同じ値を別の literal として持つため、observer 側だけ変えても test が追随して green になり得ます。

**根拠:** fixture は `probe.REQUEST_ENV_NAMES`、`probe.REQUEST_LABELS`、`probe.SUBMISSION_MANIFEST_SCHEMA`、`probe.AUTHORITY` を使用します (`orchestrator/tests/test_t1259_qsub_env_delivery_probe.py:57-89`)。実 submitter は schema、label、path を独立した literal で生成します (`tools/pegasus/probes/t1259_qsub_env_delivery_submit.sh:245-305,424-439`)。shell/PBS tests は実行せず、substring と順序だけを検査します (`orchestrator/tests/test_t1259_qsub_env_delivery_probe.py:392-429`)。

例えば `REQUEST_LABELS["R1"]` だけを変えると fixture も変わるので probe tests は通りますが、実 submitter の `"with-explicit-approval"` は manifest validation で拒否されます。

**放置すると成果物の何が変わるか:** **これを直さないと、test の受理集合に「単体 test は green だが実 qsub manifest は必ず拒否される実装」が残ります。今回の ERR trap、group completion、qstat、ulimit の欠落も lexical test では検出されません。**

**提案:** 独立した literal contract を test 側に固定し、fake `qsub`、`qstat`、`pegasusinfo` を使う submitter 結合 test を追加してください。生成 manifest と argv、subshell env、部分投入、Python rc 0/1/異常、単一 stdout、group completion を動的に検査すべきです。

## nit

該当なしです。

## 確認できた点

- 3 request の raw 証拠設計自体は、manifest と stdout を正しく回収できれば、明示 env の欠落、ambient 継承、probe failure、ambient export 忘れを分離できます。
- ambient 対象名の subshell 内 unset と意図した 1 名だけの export は正しい順序です (`submit.sh:346-365`)。
- `-v "$export_spec"` は 1 argv として渡され、値の comma、LF、CR は投入前に拒否されます (`:371-395`)。
- `/scr` 作成失敗、Python 不在、`PBS_O_WORKDIR` 不正等は shell fallback を出します。scratch 作成後の EXIT cleanup 順序も妥当です (`probe.pbs:64-89`)。
- Python 3.10 以上の絶対 interpreter を選び、R2 subprocess へ同じ実体を渡しています。
- R2 driver は 60 秒 timeout、PBS walltime は 10 分です。現行 driver は承認 flag 不在を protocol load より前に rc=2 で拒否します。
- PBS 側の `GIT_OPTIONAL_LOCKS=0`、core 無効化、Python 前の scratch `cd` は有効な位置にあります。

## pin 閉包の独自検索

実行した検索と件数は次のとおりです。

- `git diff --name-status 0bb6e9209^ 0bb6e9209`
  - 7 hit: 新規 4 file、変更 3 file。
- `rg -n --hidden --glob '!.git/**' 't1259_qsub_env_delivery_(probe|submit)' .`
  - 34 line hit、8 file。
- registry の再帰 inventory、`test_hooks.py` の AST literal、runbook 投影表を比較する read-only Python 検査:
  - `tools/pegasus/` execution inventory 72、registry の同 subtree 72、差分 0。
  - registry 全体 73、expected classes 73、expected entries 73、key/value 差分 0。
  - runbook projection 73、registry との差分 0。
- `rg -n '^def test_bash_pegasus_(registry_schema_and_fixed_classes|execution_inventory_is_synchronized|registry_login_and_suspect_bits_are_pinned)|^def test_bash_other_and_compute_keep_all_pegasus_entry_bits' orchestrator/tests/test_hooks.py`
  - 4 hit。必要な registry、inventory、login/suspect、other/compute gate は存在します。
- `rg -n '^if __name__ == "__main__":|pytest\.main\(\[__file__\]\)' orchestrator/tests/test_t1259_qsub_env_delivery_probe.py`
  - 2 hit。plain-runner harness は存在します。
- `rg -n 'submission-group-manifest\.json|terminal_state|result_sha256' tools/pegasus/probes/t1259_qsub_env_delivery_submit.sh`
  - 3 hit。すべて初回 manifest 作成内で、completion/update 実装はありません。
- `rg -n 'qstat[[:space:]]+(-J[[:space:]]+)?-f' tools/pegasus/probes/t1259_qsub_env_delivery_submit.sh`
  - 0 hit。
- `rg -n 'ulimit[[:space:]]+-c[[:space:]]+0' tools/pegasus/probes/t1259_qsub_env_delivery_submit.sh`
  - 0 hit。

登録簿の単純な pin 同期によって別検査が赤になる箇所は静的には見つかりませんでした。ただし must-fix 7 の admission 方針違反は、golden 自体も同時更新されているため現行検査では赤になりません。

## 総括

**NO-GO。must-fix 8 件、nit 0 件です。** 最優先は ERR trap による二重結果、実行時の commit/bytes pin、そして group completion と scheduler lifecycle の欠落です。