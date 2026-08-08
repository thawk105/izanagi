静的検査のみで、テストは実行していない。

[所見 1] blocker / 場所 (`s2-plan.md:30,47-49,67-81,90-95`; `hooks/guard_bash.py:246-256,563-575,913-951,1082-1094,1151-1181`; `docs/decisions.md:9145-9151`) / 何が起きるか / canonical な非 Pegasus `local-ok` を許す一般化により、壊れた・敵対的 registry が従来拒否されていた重量コマンドへ許可を与えられる。例えば `"pytest": {"class":"local-ok", ...}` は計画の helper を通り、`_SANCTIONED_PATHS` に入り、`_pegasus_admission_entry()` も返す。`_baseline_first_token_violation()` は `local-ok` を拒否せず、`_is_sanctioned()` の早期許可が通常の pytest 拒否より先に発火する。`_provenance_violation()` は provenance 専用、`_executor_output_violation()` は出力先専用なので防壁にならない / 再現または検出方法 / canonical JSON または synthetic loader に `pytest = local-ok` を置き、LOGIN/SUSPECT で `decide("pytest -q")` を評価する。現行は外部 key を wrapper が拒否し、その後の通常 pytest 判定も拒否する。計画後は allow に反転する。同様に `cmake = local-ok` で `cmake --build build` を通せる / 提案 / 非 Pegasus entry は loader と hook wrapper の両方で `unknown` または `dispatch-required` のみに制限する。lookup にも defense-in-depth を残し、非 Pegasus `local-ok` が注入されても sanctioned にしない。将来の非 Pegasus `local-ok` は別裁定・別 schema 変更に分離する。この案なら今回の ledger deny を実現しつつ受理集合は単調に縮む。

[所見 2] blocker / 場所 (`s2-plan.md:127-153`; `orchestrator/tests/test_hooks.py:1484-1504,1566-1638,1674-1741,1903-1908,1953-1982,1985-2004,2181-2204`) / 何が起きるか / 計画は既存の管轄外-key 防壁を複数箇所で撤去し、さらに最重要テストを変更一覧から漏らしている。実装後に緑へするには、裁定されていない期待値反転が必要になる。

既存テスト変更の判定は次のとおり。

- 明示裁定内: `_PEGASUS_EXPECTED_CLASSES` / `_PEGASUS_EXPECTED_ENTRIES` への ledger=`unknown` 追加、LOGIN/SUSPECT bit の deny 追加、OTHER/COMPUTE の既存 allow 維持、failure helper への ledger deny 追加。
- 明示裁定内: `test_bash_pegasus_execution_inventory_is_synchronized()` の registry 側を厳密な `tools/pegasus/` subtree に絞る変更。Pegasus の未登録閉包を維持する限り弱体化ではない。
- 保守変更: stale な `24 entry` 文言・`exact_24` 名の更新、新しい canonical 負例の追加。
- 防壁弱体化: `loader-outside-local-ok` を failure/postcondition matrix から削除し、absolute-path の負例だけへ置換する変更。
- 防壁弱体化: `outside-path` の `local-ok` 負例を negative corpus から丸ごと削除する変更。非 Pegasus `unknown` の正例を追加しても、同じ path の `local-ok` 負例は残せる。
- 最大の漏れ: `test_bash_pegasus_entry_lookup_rejects_registry_keys_outside_subtree()` (`test_hooks.py:1972-1982`) を計画が列挙していない。計画どおり registry-first lookup にすると、この既存 assert は必ず失敗する。削除・期待値反転は防壁の弱体化であり、縮小版裁定からは導けない。
- `test_check_docs.py` は新規テスト追加のみで、既存期待値の書き換え要求は見当たらない。

/ 再現または検出方法 / 現在の `loader-outside-local-ok` fixture を変更せず、計画実装後の subprocess に `pytest -q` を渡す。または既存の `test_bash_pegasus_entry_lookup_rejects_registry_keys_outside_subtree` をそのまま保持する。どちらも計画の危険な一般化を検出する / 提案 / これら三つの防壁を削除せず、「非 Pegasus unknown/dispatch は受理する」「非 Pegasus local-ok は loader・wrapper・lookup の各層で拒否する」という class 条件付き期待値へ改訂する。

[所見 3] blocker / 場所 (`hooks/guard_bash.py:185,1598-1612`; `s2-plan.md:51-104`) / 何が起きるか / registry load failure 用 fallback は ledger を捕らえるが、`main()` の内部例外 fallback は依然 `tools/pegasus` の raw mention しか認識しない。登録予定の `tools/claude_session_ledger.py` で `decide()`、site 判定、parser のいずれかが例外になると、`main()` は rc=0 で fail-open する / 再現または検出方法 / stdin に ledger command の payload を置き、`GB.decide` を `RuntimeError` / `SystemExit` にする既存テスト同型の probe を追加する。現在の分岐では `_MENTION_RE` と `_PEGASUS_RAW_MENTION_RE` の双方に一致せず `main()==0` へ到達する / 提案 / fallback 集合に載る非 Pegasus pathについて、direct・`./`・絶対 path・`-m` spellingsを raw-error detector の対象に加え、実 subprocess で exact rc=2 を固定する。

P2 の狭い範囲では、静的 fallback literal と実 registry の key 集合比較は恒真ではない。JSON 側だけの追加、literal だけの増減、fallback branch の `None` 化は、計画された meta-test/failure matrix で検出可能である。ただしそれは「正常終了した敵対的 loader」と「`main()` 内部例外」を閉じない。

[所見 4] must-fix / 場所 (`s1-brief.md:15-17,28-35,39-41,62-68`; `docs/decisions.md:8651-8654,9145-9151`) / 何が起きるか / 親の実測 3 からの一般化が過剰である。実測が証明したのは「現行二層が非 Pegasus key を一律拒否するため、ledger=`unknown` を登録できない」ことだけであり、「非 Pegasus `local-ok` まで許可可能にする必要がある」ことではない。D188 は wrapper が管轄外 key を sanctioned にしないことを明示的に防壁としている / 再現または検出方法 / `ledger=unknown` と `pytest=local-ok` の二つの synthetic registry を同じ一般化 helper に通す。前者だけが今回の裁定に必要だが、計画は両方を受理する / 提案 / brief の S1/P1 を「canonical 非 Pegasus path は deny class のみ受理」と狭める。D188 の supersede も必要最小限にし、将来の非 Pegasus `local-ok` 能力を今回の変更へ先取りしない。

[所見 5] must-fix / 場所 (`s2-plan.md:220-247`; `orchestrator/tests/test_hooks.py:1953-1982`) / 何が起きるか / 事前登録された変異 1〜9には、記載どおり実装されれば提示テストが失敗しないものは見つからなかった。しかし最も危険な変異が事前登録から欠落している。すなわち「canonical 非 Pegasus `local-ok` を loader が返す」「その path を sanctioned に導出する」という変異であり、現在これを殺している fixture/test を計画自身が削除する / 再現または検出方法 / M10 として synthetic loader `pytest=local-ok` を追加し、wrapper load failure・`_SANCTIONED_PATHS` 非包含・LOGIN/SUSPECT deny の三点を要求する。M11 として ledger command 中の `decide()` 例外が rc=2 になることも登録する / 提案 / 変異 matrix に M10/M11 を追加し、deny-only domain invariant と raw-error fallback の独立検出器へ帰属させる。

[所見 6] must-fix / 場所 (`s1-brief.md:28-30`; `s2-plan.md:104,140-145`; `hooks/guard_bash.py:552-560,913-938,1082-1094`; `docs/pegasus-runbook.md:430-432`) / 何が起きるか / 新規 deny テストは repo-root からの direct spelling だけで、`_script_targets()` は segment 間の cwd を追わない。`cd tools && python3 claude_session_ledger.py --scan` では lookup path が `claude_session_ledger.py` となり、登録 key と一致せず allow へ落ちる。これは既知の F121 型限界で新しい既存 deny の消失ではないが、brief の「純増検出力」の無限定な表現は成立しない / 再現または検出方法 / 実装後に上記 command、`env --chdir=tools ...`、direct/absolute/`-m tools.claude_session_ledger` の spelling matrix を静的または親実走で確認する / 提案 / cwd を admission parser に渡して閉じるか、今回受理する既知限界として brief・受入期待を「parser が exact target と認識した綴り」に限定し、親裁定へ返す。

意図された JSON が ledger=`unknown` 一件だけの場合、Pegasus 未登録 sentinel、既存 unknown/dispatch deny、既存 local-ok、OTHER/COMPUTE の allow は静的には維持される。問題は、その一点を実現するために受理可能な registry の権限を `local-ok` まで広げていることにある。

## 総括

最危険は、非 Pegasus `local-ok` が `pytest` 等の既存 deny を sanctioned 早期許可へ反転できる点。  
次に、その侵入を止める既存 lookup/loader テストを削除・未列挙のまま期待値反転させる点。  
三点目は、ledger path が hook 内部例外時に raw mention fallback を受けず rc=0 になる点。  
親への未決は「非 Pegasus は deny class 限定にするか」と「既知の cwd-relative 穴を今回閉じるか」。  
テストは未実行であり、上記はすべて静的検査結果である。