結論: P1 は `merge-message` 欠落だけを対象にした暫定 mitigation としては効きますが、運用規約だけでは恒久策として不十分です。編集・commit は行っていません。

## 所見

### 1. [real] 運用規約だけでは omission を防げない

`CLAUDE.md:32-36` は task-class や契約が prompt 規律であり、hooks による機械強制をしないと明記しています。さらに F365 自身が、prompt 規律では「1 セッションしか直らない」ため、受入経路へ機械関門を入れた理由を記録しています (`docs/failures.md:9307-9312`)。

既存の Pegasus runbook にも同じ規約があります (`docs/pegasus-runbook.md:809-813`, `921-922`)。それでも t1180 は `--merge-message-file` を渡さず lease 取得後に失敗しました (`docs/failures.md:9277-9280`)。

再現条件は、CLI の optional 引数 (`tools/dev_wave_wait.py:1607-1614`) を省略し、claim 後に `main` が進むことです。`merge-message` で child command は未投入、retry evidence は無く (`tools/dev_wave_wait.py:3793-3797`, `4186-4192`)、lease は release されます (`tools/dev_wave_wait.py:4255-4261`)。既存テストもこの挙動を固定しています (`orchestrator/tests/test_dev_wave_wait.py:6736-6745`)。

P1 は「遵守された場合」に限り race を閉じます。恒久策には CLI と `run_acceptance` API の必須化、および claim 前 snapshot が必要です。

### 2. [real] P1 は message の安定性と完全な provenance を保証しない

`_validated_message_copy` は「非空」かつ `AI-Agent:` 行の存在しか検査しません (`tools/dev_wave_wait.py:2891-2909`)。しかし実際の `--message-file` 検査は merge 後の prospective parents と変更 path に依存します (`tools/check_ai_provenance.py:2585-2609`, `1316-1349`)。完全な trailer 形式・実装 author 条件も別途必要です (`docs/ai-provenance.md:9-33`, `tools/check_ai_provenance.py:1231-1261`)。

例えば `AI-Agent: codex` だけの file は前段を通っても、`merge-message-provenance` で受入 command 前に落ち得ます (`tools/dev_wave_wait.py:3799-3825`)。また queue 待ち中の file 削除・書換えも、検証が claim 後 (`3793-3797`) なので P1 では防げません。

暫定判定は real。草稿もこの残余を部分的に認識していますが、P1 単独の「race window を閉じる」という表現は過大です。

### 3. [real / refuted] 他の failure path は分けて扱う必要がある

| 経路 | lease 取得後か | retry / release | 暫定判断 |
|---|---:|---|---|
| `preflight-index-flags` | いいえ。claim (`3773`) より前の `3717` | lease 消費なし | **refuted** |
| `preflight-submodule-ready` | いいえ。`3718`、実体は `2261-2276` | claim なし | **refuted** |
| `owned-path-overlap` | はい。`3791-3792` | retry せず通常 acquired lease を release | **real** |
| `merge` / `merge-history-provenance` / `merge-message-provenance` | はい。`3799-3825` | retry せず release | **real** |
| `commit-message-postcheck` / `postcheck` / `commit-head-postcheck` / `prerun-clean` | はい。`3841-3868` | retry せず release | **real** |
| `prerun-fingerprint` / `restart-required` / receipt 準備 | はい。`3869-3904` | 通常 acquired では同じ。`held-self` は保持 | **real、ただし例外あり** |

`retry_evidence_reason` が設定されるのは child command 後の `3957-3969` だけです。したがって command 投入前のこれらは同じく retry されません。テストも複数 stage をまとめて「submission なし・release あり」と固定しています (`orchestrator/tests/test_dev_wave_wait.py:7073-7213`)。`held-self` は release 権限が無く lease を保持するため、全経路が完全に同一という草稿の一般化は反証されます (`tools/dev_wave_wait.py:3188-3194`, `orchestrator/tests/test_dev_wave_wait.py:6328-6355`)。

brief の scope (`brief.md:5-6`) は広い「lease 取得後・command 前」ですが、草稿は `R-B` で message input だけへ狭めています (`s2-plan.md:57-80`)。少なくとも全 failure inventory と、D486 を変える retry/release 案を別裁定へ送る明示が必要です。

### 4. [real] operations 追記は段 7 の直接編集ではなく、段 8 routing が必要

段 7 は記録、段 8 が自己改善の裁定です (`.claude/commands/dev-wave.md:43-56`, `docs/dev-wave/core.md:101-119`)。自己改善契約も「候補の記録」と「本文・正本の編集」を分離し、dev-wave の候補は段 8 に一度だけ裁定するとしています (`docs/skill-self-improvement.md:9-19`, `57-60`)。

したがって段 7 では F365 再発と P1 候補を記録し、`operations.md` の変更可否は段 8 で裁定すべきです。既存 runbook に同内容があるため、全文複製ではなく既存 leaf への短い参照にする必要があります (`docs/skill-self-improvement.md:27-37`)。

予算も逼迫しています。

- `dev-wave.md` は実測 9,492 / 9,500 bytes。上限は `tools/check_docs.py:183-190`。
- `DW-O18` は実測 995 / L2 単節上限 1,000 bytes。上限検査は `tools/check_docs.py:257-259`, `4264-4270`。
- `docs/skill-self-improvement.md` も 5,963 / 6,000 bytes。
- 現状の `python3 tools/check_docs.py` は違反なし。

よって `operations.md` への意味ある追記は、そのままでは 5-byte 枠に収まりません。圧縮、既存文との統合、または独立した予算審査が必要です。

### 5. [partial real] 裁定パッケージの形式は満たすが、択一の排他性が曖昧

草稿は R-A/R-B とも「事実→効き→択一→親の推奨」を持ち、R-A には P1、コード側 P2/P3、現状維持の 4 択があります (`s2-plan.md:3-55`)。親推奨も理由付きで明記されています (`s2-plan.md:51-55`)。この点は先例の形式 (`ruling-package.md:8-46`) を満たしています。

一方、P1 と P2 は厳密には相互排他的ではありません。草稿自身が「P2 を恒久策、P1 を暫定 mitigation」と併用しています (`s2-plan.md:31`, `53`)。また「fail-closed 維持」と P1/P2 も別軸で併用可能です。

段 4 では、少なくとも次の二軸に分けて択一を定義すべきです。

- message input の供給: P1 / P2 / 自動生成 / 現状維持
- pre-command failure の lease 処理: D486 の fail-closed 維持 / retry 境界変更

### 反証できなかった主張

- valid で安定した message file を全 invocation に渡せば、`merge_message_file is None` による `merge-message` 分岐は到達しません (`tools/dev_wave_wait.py:3788-3797`, `4323-4338`)。
- `preflight-index-flags` と `preflight-submodule-ready` は claim 前であり、lease 喪失型ではありません。
- `owned-path-overlap` を P1 で救わず terminal failure にする草稿の扱いは、実装順序 (`3791-3797`) と runbook (`995-999`) に整合します。
- 草稿の file:line 根拠、推奨理由、最低 3 択の存在自体は確認できました。

## 総括

- 所見は 5 件（real 4、partial real 1）；最大の問題は、既存規約があるのに omission が再発した機械強制欠如。
- P1 は message 欠落の条件付き mitigation に留まり、全 postclaim/pre-command failure を救わない。
- preflight 2 経路は同型ではないが、commit/provenance/prerun 系は同じ release 構造を持つ。
- operations 追記は段 8 裁定が必要で、O18 は 995/1,000 bytes のため単純追記できない。
- 安定した valid file なら特定の `merge-message` race を閉じる点と、基本的な裁定パッケージ形式は反証できませんでした。
