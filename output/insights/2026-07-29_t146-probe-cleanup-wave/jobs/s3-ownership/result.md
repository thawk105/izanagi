指定6ファイルをすべて読了し、production の比較箇所も静的確認した。pytest・テスト・probe は実走しておらず、green とは判定しない。編集も行っていない。

現 plan は **NO-GO**。主因は、pathname 所有権、複合例外の優先順位、close 失敗時の契約が未確定なままだからである。

## Real findings

### R-0 — 親の単一注入から例外族・所有権へ一般化している

- severity: **major / 段4 must-fix**
- file:line: [s1-brief.md:6](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-t146-probe-cleanup/output/insights/2026-07-29_t146-probe-cleanup-wave/s1-brief.md:6)、[result.md:31](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-t146-probe-cleanup/output/insights/2026-07-29_t146-probe-cleanup-wave/jobs/s2-plan/result.md:31)、[result.md:55](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-t146-probe-cleanup/output/insights/2026-07-29_t146-probe-cleanup-wave/jobs/s2-plan/result.md:55)
- 再現 sequence:
  1. unlink wrapper が real unlink を済ませる。
  2. 同じ `PermissionError` を後付けする。
  3. 親の注入と例外型は同じだが、`.s` は残らない。
  4. 同様に、bind 前後の absent/present は「wrapper が作った」場合と「別 actor が作った」場合を区別しない。
- 成果物影響: exception class ごとの mutation 証明に見えて、実際には「side effect 前に投げた一つの mock」だけを認証する。受理集合の過剰縮小・拡大を防いだ証拠にならない。
- 最小 fix: fault ごとに `before-side-effect` / `after-side-effect` を明記し、errno から残留有無を推定しない。非 FNF は pathname が残るからではなく「namespace 状態を正常終了として証明できない」ため送出、と裁定する。

### R-1 — absent-before / present-after は一般には所有証明でない

- severity: **blocker（並行 writer まで不変条件に含める場合）／major（single-writer に狭める場合）**
- file:line: [s1-brief.md:12](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-t146-probe-cleanup/output/insights/2026-07-29_t146-probe-cleanup-wave/s1-brief.md:12)、[result.md:33](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-t146-probe-cleanup/output/insights/2026-07-29_t146-probe-cleanup-wave/jobs/s2-plan/result.md:33)、[result.md:114](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-t146-probe-cleanup/output/insights/2026-07-29_t146-probe-cleanup-wave/jobs/s2-plan/result.md:114)
- 再現 sequence:
  1. pre-bind stat が FNF。
  2. 他 thread または signal handler が `.s` を作る。
  3. probe の bind は `EADDRINUSE`。
  4. post-bind stat は present。
  5. plan は `owns_path=True` とし、別 actor の entry を unlink する。
- 別 sequence:
  1. probe が A を作り、post-bind stat が A を観測。
  2. cleanup 前に別 actor が A を unlink し、同名 B を置く。
  3. boolean ownership のまま B を unlink する。
- 成果物影響: active server の pathname や別 actor の regular file/symlinkを消し、long-path node を failed/SKIP にする。production bytes は変えなくても受理結果と certified 参照を不安定化する。
- 最小 fix:
  - 段4で single-writer を明示的に採否する。`xdist_group` は ownership lock ではない。
  - 採用する場合も、post-bind の `(st_dev, st_ino)` を保存し、unlink 直前に一致を確認する。production に既存の同型 guard がある（[protocol.py:75](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-t146-probe-cleanup/tools/dev_waves/protocol.py:75)）。
  - identity 不一致なら foreign replacement を unlink せず、bool も返さず ownership violation を送出する。
  - 最終 stat と unlink 間の race は原子的に閉じないため、hostile writer まで要求するなら同 basename の name-based unlink 案は NO-GO。

### R-2 — bind、ownership stat、unlink、dirfd close の例外優先順位が未定義

- severity: **major / 段4 must-fix**
- file:line: [result.md:34](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-t146-probe-cleanup/output/insights/2026-07-29_t146-probe-cleanup-wave/jobs/s2-plan/result.md:34)、[result.md:49](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-t146-probe-cleanup/output/insights/2026-07-29_t146-probe-cleanup-wave/jobs/s2-plan/result.md:49)、現行 [test_dev_waves_integration.py:1123](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-t146-probe-cleanup/orchestrator/tests/test_dev_waves_integration.py:1123)
- 再現 sequence:
  1. real bind 後に wrapper が `EIO`。
  2. post-bind stat が `PermissionError`。
  3. outer `os.close(fd)` も `EIO`。
  4. 通常の入れ子 `finally` では最後の dirfd close 例外が outward exception になり、ownership stat と bind EIO は context に追いやられる。
- 別 sequence: listen の `EACCES` で verdict は False、unlink が `PermissionError`、dirfd close が `EBADF`。plan が約束する「unlink の生の型・errno」は保存されない。
- 成果物影響: 同一 fault が実装順だけで False、PermissionError、EIO のいずれにもなり、acceptance と診断記録が安定しない。
- 最小 fix: 次の優先順位を実装前に固定し、pairwise fault test を置く。
  1. ownership/stat/unlink の namespace safety error
  2. socket/dirfd の resource-close error
  3. capability verdict
  4. capability OSError は cleanup が正常な場合だけ False。上位 error があれば bool は返さず、元 bind error は明示的な cause/note として保存する。

  `bind+post-stat`、`bind+unlink`、`unlink+dirfd-close`、`socket-close+unlink` の組合せが最低限必要。

### R-3 — socket close の全 `OSError` 抑止は「全経路で閉じる」と両立しない

- severity: **major / 段4 must-fix**
- file:line: [s1-brief.md:12](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-t146-probe-cleanup/output/insights/2026-07-29_t146-probe-cleanup-wave/s1-brief.md:12)、[result.md:42](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-t146-probe-cleanup/output/insights/2026-07-29_t146-probe-cleanup-wave/jobs/s2-plan/result.md:42)、現行 [test_dev_waves_integration.py:1126](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-t146-probe-cleanup/orchestrator/tests/test_dev_waves_integration.py:1126)
- 再現 sequence:
  1. socket wrapper の `close()` が real close より前に `EIO`。
  2. `contextlib.suppress(OSError)` が消す。
  3. pathname と dirfd は片付くが raw socket FD は生存。
  4. helper は True/False を通常返却する。
- 成果物影響: worker に FD が残り、後続 node の資源状態と mutation matrix を汚す。brief の resource lifetime 保証は恒真文になる。
- 最小 fix:
  - close 例外でも pathname と dirfd cleanup は続行するが、close failure 自体は収集して最終的に送出する。抑止を維持するなら brief を「close を試行する」まで弱め、raw FD の閉鎖観測を全対象 test で必須にする。
  - dirfd close の no-op、before-close error、real-close-after-error も分ける。
  - test finalizer は patch context を抜けてから、保存済み real unlink/close を使う。captured fd は対象 directory の dev/inode と一致する場合だけ閉じ、再利用された別 FD を閉じない。

### R-4 — 「real partial bind」と「sandbox 非依存」は同時に成立しない

- severity: **major / mock-fidelity must-fix**
- file:line: [result.md:69](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-t146-probe-cleanup/output/insights/2026-07-29_t146-probe-cleanup-wave/jobs/s2-plan/result.md:69)、[result.md:97](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-t146-probe-cleanup/output/insights/2026-07-29_t146-probe-cleanup-wave/jobs/s2-plan/result.md:97)
- 再現 sequence:
  1. wrapper が raw socket の real `bind(alias)` 後に EIO を足す設計にする。
  2. sandbox が AF_UNIX bind を EPERM で拒否。
  3. wrapper は後付け EIOへ到達しない。
  4. helper は False、`.s` は absent、socket/dirfd は closed。plan の期待をすべて満たして test が偽緑になり得る。
- 逆の問題: `Path.touch()` で entry を置けば sandbox 非依存になるが、実 AF_UNIX partial bind を再現したとは言えない。
- 成果物影響: 対象 branchへ一度も到達しない positive control が mutation kill として記録される。または restricted sandbox を新規 fault node が偽赤にして受理集合を縮める。
- 最小 fix:
  - mandatory test は「pathname materialization 後 error」の state-machine test と正直に限定し、regular entry を使う。
  - real-bind wrapper は、既存 long-path nodeの capability 成立後にだけ観測するか、親の環境限定実測として分離する。
  - real-bind 完了フラグと error injection 到達フラグを必ず assert する。

### R-5 — syscall 列の不変条件と planned test が一致していない

- severity: **major / 段4 must-fix**
- file:line: [s1-brief.md:11](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-t146-probe-cleanup/output/insights/2026-07-29_t146-probe-cleanup-wave/s1-brief.md:11)、[result.md:11](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-t146-probe-cleanup/output/insights/2026-07-29_t146-probe-cleanup-wave/jobs/s2-plan/result.md:11)、現行 [test_dev_waves_integration.py:1099](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-t146-probe-cleanup/orchestrator/tests/test_dev_waves_integration.py:1099)
- 再現 sequence:
  1. ownership 用 stat を複数追加する。
  2. helper の capability stat または chmod だけを削除する。
  3. 現在の正負 gateは socket factory、bind、listenしか明示注入していない（[test_dev_waves_integration.py:1167](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-t146-probe-cleanup/orchestrator/tests/test_dev_waves_integration.py:1167)）。
  4. permissive positive pathとproduction roundtripは通り、syscall parity 退行が生存し得る。
- さらに M-T146-A の「`owns_path=True` を削除」は、成功 bind 側まで消すと既存の残留 assertion が先に kill し、新規 partial-bind test に検出力が帰属しない（[result.md:124](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-t146-probe-cleanup/output/insights/2026-07-29_t146-probe-cleanup-wave/jobs/s2-plan/result.md:124)）。
- 成果物影響: mutation 台帳が純増検出力を誤帰属し、「同じ syscall 列」の保証が未発火になる。
- 最小 fix:
  - 「完全に同じ syscall 列」ではなく、literal `.s` に対する `socket → bind → chmod → capability-stat → listen` の**順序付き subsequence**を維持すると brief を修正する。ownership/cleanup stat は明示的な追加列とする。
  - chmod と capability-stat の独立 fault injectionを追加する。
  - M-T146-A は bind-exception branch の identity assignmentだけを壊す一意な変異に限定し、既存 gate PASS・新規 node FAILを事前登録する。

### R-6 — preexisting socket の no-touch が test 計画から抜けている

- severity: **medium**
- file:line: [result.md:78](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-t146-probe-cleanup/output/insights/2026-07-29_t146-probe-cleanup-wave/jobs/s2-plan/result.md:78)
- 再現 sequence: 実装を「regular/symlink なら早期 return、socket なら bindを試す」に変異すると、計画された二ケースは通る。bind が `EADDRINUSE`、post-stat present、誤 ownership、既存 socket unlink となり得る。
- 成果物影響: listening socket は FD 上では生き続けても pathname を失い、client 接続とlong-path nodeが失敗する。
- 最小 fix: actual AF_UNIX socket ケースを既存 capability-gated long-path node内で実施する。既存 probe が True のときだけ real socketを置き、helperが Falseを返して元 inodeを保存することを確認すれば、新しい SKIP consumerを増やさない。

## Refuted findings

### F-1 — 最初の stat 時点ですでにある regular file / broken symlink の削除

- severity: **refuted（planどおり実装される条件付き）**
- `os.stat(..., follow_symlinks=False)` はbroken symlink自身も存在として返し、plan はその場で False、bind/unlinkなしとしている（[result.md:19](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-t146-probe-cleanup/output/insights/2026-07-29_t146-probe-cleanup-wave/jobs/s2-plan/result.md:19)）。
- regular/socketも型を見ない同じ存在branchならno-touchになる。問題は初回観測後の競合と、R-6の未被覆変異である。

### F-2 — real `FileNotFoundError` を抑止すると必ず偽緑になる

- severity: **refuted（single-writer / planned assertion 内）**
- real unlink または別actorのunlink後のFNFなら、その時点のnamespace postconditionは満たす。computed boolを保存する裁定は妥当。
- no-op unlink はFNFではなく成功returnであり、planned testの「helper return時に `.s` absent」が殺す。raise-only FNF mockでpathを残しても同assertionが赤にする。
- ただしassertion前にtest finalizerが消してはならず、FNF mockはplanどおりreal unlink後に投げる必要がある。

### F-3 — production または isolation meta-test の変更が必須

- severity: **refuted**
- production の変更は不要。既存 production は basename `.s` とcore列を比較対象として読めば足りる（[protocol.py:246](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-t146-probe-cleanup/tools/dev_waves/protocol.py:246)）。
- isolation meta-test は `socket.socket` を語彙に持ち、helper callerへ推移する（[test_dev_waves_isolation_contract.py:35](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-t146-probe-cleanup/orchestrator/tests/test_dev_waves_isolation_contract.py:35)）。全新規 node に既定 markerを付ける限り本体no-changeでよい。

## Scope外裁定候補

### S-1 — hostile concurrent writerに対する原子的no-touch

- conditional severity: **scope内なら blocker**
- 現 caller はhelper呼出しが `thread.start()` より前（[test_dev_waves_integration.py:1191](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-t146-probe-cleanup/orchestrator/tests/test_dev_waves_integration.py:1191)、[同:1208](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-t146-probe-cleanup/orchestrator/tests/test_dev_waves_integration.py:1208)）で、`Supervisor.__init__` もthreadを起動しない（[daemon.py:459](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-t146-probe-cleanup/tools/dev_waves/daemon.py:459)）。現在の一callerについてsingle-writer裁定は可能。
- ただし「test-private directory」だけでは一般的証明にならない。段4でこの呼出順とcaller限定を契約に入れなければならない。

### S-2 — production `bind_repo_socket()` の同型 partial-bind fault

- conditional severity: **別タスク候補**
- production も bind成功return後にだけ `created=True` とする（[protocol.py:260](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-t146-probe-cleanup/tools/dev_waves/protocol.py:260)）。
- wrapperがreal bind後に例外を足せば同型残留を作れるが、通常のkernel bindで再現した証拠はない。T-146でproduction bytesを変える根拠には不足しており、no-touch裁定は妥当。通常syscallでの独立再現が出た場合だけ別taskへ昇格すべきである。

## 総括

**NO-GO。**

段4の must-fix は次の5点。

1. single-writerを明示採用するか、hostile writerまで要求して設計を差し戻す。採用時もdev/inode guardとreplacement testを入れる。
2. bind、ownership stat、unlink、socket close、dirfd closeの複合例外優先順位を固定する。
3. blanket close suppressionを正当化・検証するか廃止し、mutation時にもworkerを汚さないtest finalizerを具体化する。
4. sandbox非依存のstate-machine testとreal AF_UNIX partial-bind実測を分離し、target branch到達をassertする。
5. 「同 syscall 列」を順序付きcore subsequenceへ限定し、chmod/stat faultと一意なM-T146-Aで純増検出力を固定する。
