## 所見

### R1. cache hit が regular file の内容差し替えを見逃す

- **主張:** 同一 `main()` 中に対象が別の regular file 内容へ変わると、変更前だけが後段の違反を検出する。安定した作業木を保証する排他契約がない限り、受理集合は同一でない。
- **根拠:** `main()` は先に文書 guard を実行し ([tools/check_docs.py:5297](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1222-growth-leak-fix/tools/check_docs.py:5297))、例えば `docs/dev-wave/workers.md` を `newline=""` で読む ([tools/check_docs.py:4641](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1222-growth-leak-fix/tools/check_docs.py:4641))。後で living-doc 経路が同じ file を `newline=None` で読む ([tools/check_docs.py:5338](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1222-growth-leak-fix/tools/check_docs.py:5338), [tools/check_docs.py:5356](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1222-growth-leak-fix/tools/check_docs.py:5356))。しかし cache entry は outcome と本文だけで ([tools/check_docs.py:846](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1222-growth-leak-fix/tools/check_docs.py:846))、再度の `lstat()` は mode しか比較せず ([tools/check_docs.py:884](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1222-growth-leak-fix/tools/check_docs.py:884))、mtime、size、inode の変化を無視して旧本文を返す ([tools/check_docs.py:900](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1222-growth-leak-fix/tools/check_docs.py:900))。
- **具体例:** 最初の読取後、`docs/dev-wave/workers.md` を regular file のまま `README.md:1` を含む内容へ差し替える。変更前は後段の living-doc 読取が現在の内容を開き、行番号参照 finding を append する ([tools/check_docs.py:5365](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1222-growth-leak-fix/tools/check_docs.py:5365))。変更後は旧本文を返し、その finding を失う。symlink への差し替えは再検査で捕まるが、regular file の差し替えは捕まらない。
- **帰結:** 他の違反がない fixture では変更前 `rc=1`、変更後 `rc=0` となり、受理集合が拡大する。少なくとも cache entry に読取時の file identity/version を保持し、再 `lstat()` と違えば再読取する必要がある。
- **深刻度:** **blocker**

### R2. 事前登録 M3 を kill する cache-hit 故障 fixture がない

- **主張:** cache-hit 時の finding 再生を削除する reward-hack 変異 M3 に、焦点走内の期待赤 node が静的に見当たらない。
- **根拠:** M3 は明示的に事前登録されている ([s4-ruling.md:128](/work/1/SFC/tanab/dev-wave-jobs/t1222-growth-leak-fix/s4-ruling.md:128))。実装の荷重箇所は cached failure を呼出し固有 prefix で append する部分 ([tools/check_docs.py:916](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1222-growth-leak-fix/tools/check_docs.py:916))。既存 invalid UTF-8 fixture は、archive なら `previously_unreadable` で後続読取を止め ([tools/check_docs.py:2080](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1222-growth-leak-fix/tools/check_docs.py:2080))、command/reference なら `guard_unreadable` で living-doc 読取を止める ([tools/check_docs.py:4654](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1222-growth-leak-fix/tools/check_docs.py:4654), [tools/check_docs.py:5339](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1222-growth-leak-fix/tools/check_docs.py:5339))。親の差分 probe も成功本文へ違反文字列を足すだけで、読取失敗 cache hit を作っていない ([differential.py:34](/work/1/SFC/tanab/dev-wave-jobs/t1222-growth-leak-fix/differential.py:34))。
- **具体例:** `docs/pegasus-runbook.md` の invalid UTF-8 読取では、変更前は次の 2 prefix が順に必要になる。

  1. `tools/check_docs.py: dispatch inventory drift — docs/pegasus-runbook.md の読取失敗` ([tools/check_docs.py:2920](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1222-growth-leak-fix/tools/check_docs.py:2920))
  2. `tools/check_docs.py: Pegasus admission drift — docs/pegasus-runbook.md の読取失敗` ([tools/check_docs.py:3729](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1222-growth-leak-fix/tools/check_docs.py:3729))

  現実装は正しく再生するが、cached branch の append を消す M3 は 2 件目だけを消す。これを exact 件数・順序で固定する fixture がない。
- **帰結:** M3 が焦点 suite に受理され、finding 集合を 2 件から 1 件へ縮小する実装が着地可能になる。段 6 で cache-hit 故障 fixtureまたは同等の mutation probeを確定する必要がある。
- **深刻度:** **must-fix**

### R3. 親の「全出力 byte 一致」は順序を比較していない

- **主張:** 親の差分 probe は raw stdout ではなく整列後の行列を比較しているため、finding 順序不変の証拠にはならない。
- **根拠:** probe は `out.splitlines()` を `sorted()` してから出力する ([differential.py:51](/work/1/SFC/tanab/dev-wave-jobs/t1222-growth-leak-fix/differential.py:51))。一方、親報告はこれを「新旧の全出力」「決定的証拠」と表現している ([parent-verification.md:30](/work/1/SFC/tanab/dev-wave-jobs/t1222-growth-leak-fix/parent-verification.md:30))。
- **帰結:** append 順だけを変える退行は当該 probeを通る。ただし現差分では呼出し順と末尾の insertion-order 出力 ([tools/check_docs.py:5513](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1222-growth-leak-fix/tools/check_docs.py:5513)) に変更を認めなかったため、現時点の出力差そのものは示していない。
- **深刻度:** **nit**

## refuted

- **universal newlines の再実装:** 現実装は `\r\n` を先に `\n`、残る `\r` を `\n` にする。これは `newline=None` の変換集合と一致する。NEL、U+2028、U+2029、VT、FF は `str.splitlines()` では境界だが、universal-newline 変換対象ではなく、実装も変換しない。末尾 CR、混在、CRLF の内部 read 境界も、全文 `read()` 後の置換なので不一致にならない。既存 suiteにも実 `main()` の CRLF 正例がある ([test_check_docs.py:6704](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1222-growth-leak-fix/orchestrator/tests/test_check_docs.py:6704))。親の 21 ケース実測とも整合する。ここは refuted。
- **newline key の欠落:** key は `(Path, newline)` である ([tools/check_docs.py:900](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1222-growth-leak-fix/tools/check_docs.py:900))。raw と変換済み本文は別 entry。refuted。
- **prefix の取り違え:** cache は整形済み finding を保持せず、分類と detail だけを保持し、hit ごとに現在の `invalid_utf8_prefix` または `failure_prefix` を選び直す ([tools/check_docs.py:919](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1222-growth-leak-fix/tools/check_docs.py:919))。現実装の prefix 再生は正しい。R2 はその回帰検出の欠落である。
- **monkeypatch 経路:** 全15箇所が `_safe_read_text` の global name lookup のまま。`main()` は `_main()` を呼ぶだけで ([tools/check_docs.py:5282](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1222-growth-leak-fix/tools/check_docs.py:5282))、s8c の差し替えは各論理呼出しで見える。cache hitでも wrapper 自体は呼ばれるため `assert injected` は維持される。refuted。
- **symlink・非 regular 判定の省略:** 親 component の symlink loop と `lstat()` は cache lookup より前にある ([tools/check_docs.py:868](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1222-growth-leak-fix/tools/check_docs.py:868))。これらの finding は cacheされない。refuted。ただし regular file 内容の変化は R1。
- **process 全体への stale cache:** `main()` ごとに fresh dictを設定し、`finally` で tokenを復元する ([tools/check_docs.py:5285](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1222-growth-leak-fix/tools/check_docs.py:5285))。同一 process の複数回・入れ子呼出しでも前回本文は残らない。consumer 検索でも永続 cache を前提にする経路はなかった。refuted。
- **`open_newline` の非対称:** `Path.open` の monkeypatchなら引数差は観測可能だが、repository consumer は通常の `Path.open` へ委譲しており、通常の UTF-8 regular file の戻り本文には差がない。直接 `_safe_read_text` を呼ぶ cache 外経路は従来どおり `newline=None` を渡す。
- **実装子報告との静的食い違い:** R1の無条件な同一性主張と、R2の検出力根拠を除き、ContextVar の範囲、15 caller、prefix再生、newline key、安全判定に関する報告は実装と一致した。

pytest は実走していない。上記は静的検査と親提供の実測資料の監査結果であり、非実走を緑とは数えていない。

## 総括

**NO-GO。**

現実装は安定した file 内容に対する改行変換・prefix再生・順序・monkeypatch経路では整合している。しかし、regular file が同一 `main()` 中に変化する場合に旧 checker だけが拒否する具体的経路があり、「rcと受理集合が完全同一」を満たさない。加えて、事前登録 M3 を killする cache-hit 故障 fixtureが見当たらず、finding再生を削る reward-hack変異への防御が未成立である。