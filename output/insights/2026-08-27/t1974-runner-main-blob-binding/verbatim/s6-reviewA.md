所見は 4 件です。pytest と checker は実走していません。

**所見 1: K=2/3 では fork worker が申告 write-fd を継承し、子孫による偽造が可能**

- 種別: 停止級
- 根拠: `tools/acceptance_launcher.py:573-589` が write-fd と nonce、tested main を runner に渡します。`tools/run_tests.py:2310-2352` は shard 実行を `acceptance_shards.run_parallel` へ渡し、`tools/acceptance_shards.py:1201,1243-1255` は明示的に `multiprocessing.get_context("fork")` で worker を起動します。fork は `close_fds` や `FD_CLOEXEC` と無関係に、開いている fd を複製します。worker は fd を閉じず、`tools/acceptance_shards.py:1000-1015` から dispatcher を呼び、`tools/pegasus/dispatch_compute.py:789-820,3687-3692` がその fd へ書きます。
- 根拠: worker は環境から fd、nonce、tested main、K をすべて取得できます。main と tip の runner bytes は事前に等値なので digest も算出可能です。tip 側 `acceptance_shards.py` または dispatcher は qsub なしで compact JSON を K 件書き、rc 0 を返せます。これは裁定の「dispatcher は同一 process」という前提と異なります。
- 根拠: exec される通常の子では `subprocess` の既定 `close_fds=True` が原 fd を閉じますが、環境の fd 番号は残ります。番号が別 fd に再利用された後に nested dispatcher が動くと、pipe identity 検査がないため別 fd へ誤書き込みする経路も残ります。`os.set_inheritable` の呼び出しはありませんが、fork 経路には効果がありません。
- 反証条件: 実 K=3 worker 内で `os.fstat(int(os.environ[FD_KEY]))` が `EBADF` になり、worker からの直接書き込みが launcher の read 端へ届かないことを測れば反証できます。現実装では届くはずです。
- 成果物影響: 偽造された K 件が通ると、実 compute runner が束縛実行されていなくても v5 受領証が生成され、land は `acceptance_verdict="child-green"` と受領証 SHA-256 を台帳へ記録できます。fd を保持するだけなら launcher は EOF 待ちで停止します。

**所見 2: scope 外の既存 E2E が本 wave 自身の全受入を確実に赤へする**

- 種別: 停止級
- 根拠: `orchestrator/tests/test_resume_gate_acceptance_boundary.py:258-274` は現在の launcher を fixture repo へコピーしますが、同 file `:192-221` の環境には `IZANAGI_ACCEPTANCE_SHARDS` がありません。`:379-404` はその launcher で受領証成功を要求します。新 launcher は `tools/acceptance_launcher.py:570` で runner 起動前に停止します。Kを追加しても synthetic runner は申告を書かないため、次に申告件数で停止します。
- 根拠: `orchestrator/test_selection_contract.py:61` の除外集合は空で、このテストは通常の全受入対象です。追加された P2 テストは unbound dispatcher の pathname fallback だけを検査し、この実 Git waiter E2E を保護していません。
- 反証条件: 親が当該 nodeid を current diff 上で実走し、waiter rc 0、phase `started/verified`、非空 v5 受領証を観測すれば反証できます。
- 成果物影響: full acceptance が green にならず、本 wave の authoritative 受領証を作れません。land は成立せず、台帳の acceptance receipt SHA-256 と verdict は記録されません。

**所見 3: dispatcher の申告 JSON と launcher の canonical 形式が不一致で、正規申告が全拒否される**

- 種別: must-fix
- 根拠: `tools/pegasus/dispatch_compute.py:487-492` の `_canonical_json_text` は `indent=2` の複数行 JSONです。`:927-928` はこれを申告 channel へ書きます。一方、`tools/acceptance_launcher.py:115-125` は空白なしの一行 JSONを canonical とし、`:293-307` は一行ごとに parseして exact bytes 比較します。dispatcher 出力の最初の `{` 行で JSON decode errorになります。
- 根拠: `orchestrator/tests/test_pegasus_dispatch_compute.py:4187-4216` は申告全体を `json.loads` するだけで canonical framing を検査しません。launcher 側テストは dispatcher writer ではなく launcher 自身の serializer を使うため、この seam が未検査です。
- 反証条件: `_write_runner_binding_report` の実出力をそのまま `_parse_binding_reports` に渡し、例外なく 1 件になることを測れば反証できます。
- 成果物影響: launcher は outcome を書いた後、`tools/acceptance_launcher.py:615` で停止し、completion を読まず受領証も書きません。post-P の正常 dispatch は land 不能となり、台帳値は作られません。

**所見 4: index 検査の長さ条件は先行 reject により恒真**

- 種別: nit
- 根拠: `tools/acceptance_launcher.py:347-348` が `len(reports) != expected_k` をすべて拒否するため、`:349-353` に到達した時点の `len(reports) == expected_k` は常に真です。これを偽にして同位置へ到達する入力はありません。
- 反証条件: 長さ不一致の入力で `:349` の条件評価まで到達できれば反証できます。
- 成果物影響: なし。削除しても受理集合、受領証、land、台帳値は変わりません。なお、裁定で gate から外すよう指定された `argv_policy` と `child_script` は `tools/pegasus/dispatch_compute.py:811-812` の assert に留まり、発火 gate には入っていません。

受領証不変性は照合済みです。land の exact 27 fields、共通 32 条件、fingerprint 11 条件、green 7 条件、red 16 条件、launcher identity の main 6条件/bootstrap 8条件、waiter/runner 15条件、red checker 8条件を追いました。27 fields と `_ENV_PROJECTION_FIELDS` の4項目は不変で、値の意味も変更されていません。

同一 buffer 束縛は `tools/pegasus/dispatch_compute.py:868-893` で成立しています。`blob.stdout` と同一 bytes objectを hash と `input` に使用し、cat-file 非ゼロは拒否します。空または不完全な rc 0 出力も launcher の独立 main digest 照合で拒否されます。`tools/run_tests.py` は HEAD と SHA-256 が一致し、差分は 0 byteです。Kも launcher の明示環境値だけから決まり、argvや申告値からの逆流はありません。

## 総括

最重の所見は、K=2/3 の fork worker が申告 fd を保持し、子孫隔離が成立していないことです。  
親は最初に actual shard worker 内の `fstat(fd)` と直接 pipe write を測るべきです。  
その後、dispatcher writer の bytes を launcher parserへ直結し、canonical mismatch を確認してください。