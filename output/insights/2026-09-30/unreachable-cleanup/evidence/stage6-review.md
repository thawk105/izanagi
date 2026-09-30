1. **real — `discard-scratch` に救出判断が必要な成果物が含まれる。** [plan.json](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-unreachable-cleanup/output/insights/2026-09-30/unreachable-cleanup/evidence/plan.json) の `58c35f73af15…` は main に同一 blob がない図 PDF・provenance JSON など 13 対、`cb241cf43d1…` は図・比較表など 7 対を持つ。`b6911273bb63…` にも `scratch-output-pruning/` の実装・selftest 5 対がある。最上位名だけで「scratch」と判定した結果であり、依頼の「価値がある、または判断がつかない → rescued」に反する。放置すると、これらを含む `pending` 99 件が一括喪失受容の対象に残る。

2. **real — 承認カードが類型 A の損失を過小に説明している。** [README.md:58](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-unreachable-cleanup/output/insights/2026-09-30/unreachable-cleanup/README.md:58) は「試行の中間物」「記録は main にある」と述べるが、上記 `58c35f73af15…`・`cb241cf43d1…` の `pairs` には main に同一 blob がない研究図・provenance・比較表が含まれる。放置すると、ユーザーは失われる記録を把握しないまま 99 件を受容しうる。

3. **real — 新規 23 entry が `pending` を経ずに `rescued` として追記された。** [台帳の遷移契約:44](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-unreachable-cleanup/docs/unreachable-object-ledger.md:44) は新規 entry の初期状態を `pending` と定める。[ledger_tool.py](/work/SFC/tanab/tmp/unreachable-cleanup-2026-09-30/ledger_tool.py) の `build` は `rescue-body` を直接 `rescued` にして追記する。最終 field は揃っているが、初期状態と遷移の監査履歴が残らない。

4. **refuted — D2065 違反は確認されない。** [D2200 項 2](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-unreachable-cleanup/docs/decisions.md:70109) が人間の喪失受容を明記する `cleanup-20260921-*` だけが `accepted-loss` 227 件で、新規捨て候補 130 件は `pending`。放置によって AI 判断だけで受理集合が増える箇所は見つからない。

5. **refuted — 台帳の field 数・既存行の非対象 field に破損は見つからない。** 基準 `d79fd352…` との JSON 比較では既存 278 行の削除はなく、追加 153 行。全 431 行が 26 field で、既存行の変更は `status`・`resolved_at`・`rescue_ref`・`resolution_note` に限られた。解決 field と `rescue_ref` の文字列形式にも不整合は見つからない。[台帳 schema](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-unreachable-cleanup/docs/unreachable-object-ledger.md:11)。台帳値への追加影響は所見 3 の遷移履歴に限る。

6. **refuted — P1・P2 の食い違いは説明されている。** P1 は固定後の原 repo では監査対象が到達可能になるため複製を使用し、off 監査の 2034／238／1197 が一致した。[README.md:28](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-unreachable-cleanup/output/insights/2026-09-30/unreachable-cleanup/README.md:28)。P2 は依頼外の同時実行だが、[D2200 項 2](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-unreachable-cleanup/docs/decisions.md:70109) の既裁定を実行したもの。いずれも、この静的確認では受理集合の誤変更を示さない。

7. **refuted — 件数・sha256・日時の明白な食い違い、指示めいた入力は見つからない。** evidence の off 238 件、full 183 件・抑止 600 対・確認不能 2415 件は [README.md:28](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-unreachable-cleanup/output/insights/2026-09-30/unreachable-cleanup/README.md:28) と一致し、full evidence の SHA-256 も新規台帳値と一致した。確認した題名・path・監査出力に作業者への指示と読める文字列はなかった。放置による台帳値の変化は確認されない。

## 総括

**real 所見: 1、2、3。** 特に一括承認前に、研究図・provenance・実装を含む `discard-scratch` を再判定し、承認カードの損失説明を直す必要がある。実行中の ref の到達性、監査や tool の再実走、blob 内容そのものは確認していない。