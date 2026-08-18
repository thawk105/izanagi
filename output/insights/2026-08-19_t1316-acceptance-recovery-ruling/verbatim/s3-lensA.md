## 所見 1 — attempt 2 は P1 だけでは閉じない

**暫定判定: real（P1 は限定的）**

- `_MAX_ACCEPTANCE_ATTEMPTS = 2` は `tools/dev_wave_wait.py:227`、同じ `Path` は `tools/dev_wave_wait.py:4323-4338` で再利用される。
- しかし attempt 2 の self-claim は、要求した現在の `main_sha` と lease 内の `main_sha` の一致を要求する (`tools/dev_wave_wait.py:2875-2881`, `2795-2845`)。self-held lease は mtime だけ更新し、元の `main_sha` を返す (`tools/wave_land_window.py:733-761`, `390-398`)。
- 再現条件: attempt 1 の retry 後、attempt 2 の claim 前に main が進む。既存テストも `claim-self-unverified`、command 1 回、release 1 回を pin している (`orchestrator/tests/test_dev_wave_wait.py:10125-10138`)。有効な message file があっても回復しない。
- main が claim 後に進んだ場合は、P1 により merge までは進み得るが、receipt の `final_main_sha != claim_context.main_sha` で失敗する (`tools/dev_wave_wait.py:4026-4042`)。
- さらに元 file は attempt ごとに再読込され、snapshot は保持しない (`tools/dev_wave_wait.py:3702`, `3793-3797`, `4181-4185`)。attempt 2 まで同じ内容を保持することを規約に明記しない限り、削除・書換えでも `merge-message` が再発する。

したがって P1 が閉じるのは、main が不変で、message file が process 終了まで不変に保持される場合の `merge-message` 欠落サブレースだけである。

## 所見 2 — `owned-path-overlap` は P1 と無関係

**暫定判定: refuted（P1 が誤って救うという懸念は反証）**

`behind > 0` の中で `_owned_path_overlap` が message 検査より先に評価される (`tools/dev_wave_wait.py:3790-3797`)。重複 path があれば merge、message 読込、受入 command のいずれにも進まない。実装も `git diff --name-only HEAD...main` で判定する (`tools/dev_wave_wait.py:2637-2661`)。

有効な message file を渡しても terminal failure になることを既存テストが確認している (`orchestrator/tests/test_dev_wave_wait.py:6810-6863`)。P1 はこの正当な fail-closed 経路を変更しない。

## 所見 3 — message 内容は完全には main 非依存でない

**暫定判定: real**

`_message_has_ai_agent` と `_validated_message_copy` 自体は、非空・`AI-Agent:` 行・読取可能性しか見ない (`tools/dev_wave_wait.py:2891-2909`)。

しかし実際の merge 後には `check_ai_provenance.py --message-file` が実行される (`tools/dev_wave_wait.py:3816-3825`)。この検査は、

- `MERGE_HEAD` と HEAD から prospective parent を作る (`tools/check_ai_provenance.py:1316-1341`)
- parent 間の変更 path 集合を計算する (`tools/check_ai_provenance.py:1344-1349`)
- 実装面 path なら Codex `role=author` を要求する (`tools/check_ai_provenance.py:1231-1261`)
- correction trailer なら parent ancestry を検査する (`tools/check_ai_provenance.py:1769-1810`)

という main・具体的 commit 列依存を持つ。

従って、現在の通常 merge に対して完全な trailer を持つ静的 template は使える場合があるが、「どの main 状態・commit 列でも同じ静的内容でよい」は成立しない。`docs/ai-provenance.md:11-31` の要件変更でも前提は崩れる。`test_merge_message_requires_nonempty_ai_agent_trailer` (`orchestrator/tests/test_dev_wave_wait.py:8472-8483`) は trailer 欠落しか pin しておらず、完全 schema の不変性までは保証しない。

## 所見 4 — 無人 supervisor では運用規約の機械的強度がない

**暫定判定: real（現状は実経路未開放）**

`DW-CTX` は fresh な `claude -p`、予算、deadline、fail-closed 条件を定めるだけで (`docs/dev-wave/core.md:128-138`)、message file の生成・保持・argv 供給を supervisor が検査する規定はない。

既存 runbook にも「待機前に用意する」規約は既にある (`docs/pegasus-runbook.md:921-922`)が、F365 では実際に omission が発生している (`docs/failures.md:9277-9280`)。したがって `docs/dev-wave/operations.md` への追記だけなら、対話 manager と無人 manager の双方で同じ自己申告に依存する。

なお、外部 supervisor の DW-CTX 結線自体が現在 fake-only / runtime blocked と記録されている (`docs/phase3.md:1184`, `tools/dev_waves/daemon.py:1`)ため、無人経路の end-to-end 実測はできなかった。

## 所見 5 — D253/D486 の不変条件と `behind > 0` ゲートは変わらない

**暫定判定: refuted（「P1 が決定を変える」という懸念）**

D253 の FIFO・ticket・lease 意味論 (`docs/decisions.md:11616-11634`, `11649-11670`) と、D486 の retry 6 条件・lease 保持 (`docs/decisions.md:20259-20284`) は、P1 の運用変更では変わらない。

コード上も merge は依然として `behind > 0` のときだけ行われる (`tools/dev_wave_wait.py:3790-3798`)。`merge_message_file` が非 `None` でも、`behind == 0` なら merge は発生しない。retry も child command 後の肯定的証拠がある場合だけで (`tools/dev_wave_wait.py:3957-3969`, `4194-4238`)、`merge-message` failure を D486 retry に変える挙動はない。

ただし、規約を守った場合の実効動作は、従来の「message 欠落で lease release」から既存 merge 経路へ進むよう変わる。これは D253/D486 の意味論変更ではないが、P1 の意図した間接効果である。

## 所見 6 — 「唯一の呼び手」は狭く解釈すれば正しいが、brief の一般化は不正確

**暫定判定: partial**

本番コードの CLI 入口は `main()` から `run_acceptance()` へ渡す経路だけである (`tools/dev_wave_wait.py:4429-4447`)。repo-wide の静的検索では、別の production wrapper や CI からの実 CLI 呼出しは見つからず、この限定主張は反証できなかった。

一方、文字どおり「唯一の呼び手」ではない。

- テスト helper が API を直接呼ぶ (`orchestrator/tests/test_dev_wave_wait.py:1341-1365`, `7979-7984`)
- subprocess で CLI を直接呼ぶテストがある (`orchestrator/tests/test_dev_wave_wait.py:9083-9102`, `9205-9223`, `9353-9372`)
- brief の使用箇所は「8 行」と書かれているが、列挙された production source は 9 行 (`/home/SFC/tanab/.claude/jobs/a61c373c/tmp/dw-t1316/brief.md:50-55`; `tools/dev_wave_wait.py:1613,3689,3732,3739,3793,3795,4301,4329,4437`)

従って、P1 の規約対象は「manager 本人」ではなく、少なくとも全 production acceptance caller と明記する方が正確である。

## 総括

- 主要所見は6件。P1は `merge-message` 欠落だけを条件付きで閉じ、attempt 2 の main 進行や provenance 依存は残る。
- 最深刻なのは、attempt 2 が lease の旧 `main_sha` と不一致になり、message file が有効でも `claim-self-unverified` になる点。
- `owned-path-overlap`、`behind > 0` ゲート、D253/D486 の不変条件が P1で変わるという懸念は反証した。
- 本番 wrapper の追加呼出しは見つからなかったが、テスト/API 経路を含む「唯一の呼び手」という一般化は反証された。
