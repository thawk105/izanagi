## 総括

実装上、N-1〜N-6 をすべて closed 候補としました。変更は [codex_reasoning_ab.py](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t181-reasoning-ab/tools/codex_reasoning_ab.py:1702) と [test_codex_reasoning_ab.py](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t181-reasoning-ab/orchestrator/tests/test_codex_reasoning_ab.py:1172) の2ファイルだけです。docs編集・commitは行っておらず、両ファイルだけが `git status` で untracked のままです。

N-1では、freshな0700 custodian directory内の乱数名0600ファイルへmappingを格納し、`make-packets` の返値からmap・秘密path・keyを除去しました。`reveal-mapping` は両読者のverdict集合、packet/verdict hash、freeze timestampを検証してから秘密を探索します。評価者向けpacket stateは`packet_id`と均一filenameだけになり、output SHAはfreeze後のrevealed artifactへ移しました。freeze前にはcustodianへ到達しない負例も追加しています。ただし別OS権限processまでは新設しておらず、同一owner内のadvisory custodianという残差は残ります。

N-2ではlaunch receipt、snapshot oracle、done、attempt ledgerをsandbox外のattempt directoryへ残し、agent側は乱数名workspaceへ分離しました。bwrapの書込bindは専用CODEX_HOME、answer、stdout、stderrだけで、snapshotはread-onlyです。attempt directoryやlaunch metadataがbind集合へ入らない負例を追加し、slot・block・attempt・armをagent可視pathから拒否する検査も入れました。

N-3は片側technical-invalid時にmateを構造化`pair-invalidated`へ変換し、両側の次generationを正規retryとして許可します。旧attemptを含むtoken、wall、model-call等のresource行は削除せず保持します。一方だけを再実行する既存拒否は維持しました。

N-4はcompleteness、POS四分岐、NEG除外、post-treatment reliability、resourceの順に整理し、POS eligibilityへNEG除外を論理ANDするよう修正しました。POS四分岐×NEG両arm有無の16通りを独立parametrizeしています。N-5はMarkdown inline emphasisを除いた正規形へ一文decision grammarを適用し、`**GO** との判断は保留する。`など4種の曖昧表現を拒否します。N-6は恒真だった数値`logical_turns`をreceipt/resourceから除去し、single-turn固定を文字列で明示した上で比較指標を`model_calls`へ差し替えました。

M1〜M12の期待node名、500-byte境界、歴史focus1/focus2 control、pair timing、submodule/object-store、raw replay等の既存nodeは静的に維持しています。許可された `python3 -m py_compile` は成功しました。ユーザー指示どおり、pytest、`tools/run_tests.py`、snapshot build/verify、`git submodule update`、外部cloneは一切実行していません。したがってテスト緑は主張しません。

波及点は、CLIが`--secret-root`／`--mapping-secret`から`--custodian-root`へ変わること、revealed mappingが公開後SHA joinを担うこと、agent出力とsessionがopaque workspaceへ移ること、resource schemaから`logical_turns`が消えて`turn_accounting`が加わることです。旧形式の凍結manifestや親fixtureは再生成・追随が必要です。未達は同一owner custodianのOS権限分離、scope外のN-7/N-8、および計算ノードでの実測と最終焦点レビューです。