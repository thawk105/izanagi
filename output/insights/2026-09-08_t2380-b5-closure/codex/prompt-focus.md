単独段 dispatch: stage=focus; sandbox=read-only; parent=/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2380-b5-successor-freeze

必読事項の射影:
- /home/SFC/tanab/.claude/jobs/9218ced6/tmp/t2380/artifacts/dev-wave-t2380-b5-successor-freeze/fix_1.md (fix 子の報告と closed 表。読めなければ即停止)
- /home/SFC/tanab/.claude/jobs/9218ced6/tmp/t2380/artifacts/dev-wave-t2380-b5-successor-freeze/review_a_1.md と review_b_1.md (段 6 レビュー。RA-08、RB-01、RB-05〜RB-12 が fix の対象。読めなければ即停止)
- /home/SFC/tanab/.claude/jobs/9218ced6/tmp/t2380/rulings-stage6.md (親の裁定。RA-04/RA-05 は bytes 不変で小文字 index・number year を裁定済み。読めなければ即停止)
- /work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2380-b5-successor-freeze/orchestrator/tests/test_axis_b5_search_catalog.py (fix 後の test。読めなければ即停止)
- /home/SFC/tanab/.claude/jobs/9218ced6/tmp/t2380/snapshot-prefix/test_axis_b5_search_catalog.py (fix 前の test。差分の基準。読めなければ即停止)
- /work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2380-b5-successor-freeze/orchestrator/axis_b5_search/catalog.py (不変のはず。読めなければ即停止)

## 役割 — 焦点再レビュー (fix 後、1 本)

read-only sandbox。pytest は走らせなくてよい (親が自走 harness 17 passed を実測済み)。fix 子の closed 表を鵜呑みにせず、所見ごとに closed / partial / regressed を自分で判定する。

1. RA-08: 3 test の期待値が production の renderer から作られていないか (tracked bytes と固定 SHA-256 literal が oracle か)。
2. RB-01: 全 1622 query の ID・枝・`term_groups`、全 1602 DBLP record の三者対応、全 entry の `{CUR}`/`{POS}` 置換関係、全 272 venue entry の完全照合が、test 側の独立 literal から組み立てられているか。production の `BLOCKS` / `BRANCHES` / helper を期待値の生成に使っていないか (検査対象としての呼び出しは可)。
3. RB-05〜RB-12 の直接 oracle が既存 test 関数の中に入り、新しい test 関数を作っていないか (nodeid 17 本)。
4. 退行: fix 前 (snapshot) にあった検査が落とされていないか。期待値が緩められていないか。`catalog.py` と生成 JSON が不変か。
5. 変異 spec (/home/SFC/tanab/.claude/jobs/9218ced6/tmp/t2380/mutation/spec-probe.json) の 13 変異が、fix 後の test でどの node を赤にするかを静的に見積もり (完全集合)、等価変異 #13 が SURVIVED になるかを判定する。

## 禁止

ファイルを書かない・変更しない。git 操作をしない。外部 network を使わない。新しい gate・検査・台帳・一般化を推奨しない。結合文字 U+0300〜U+036F を使わない。

## 出力形式

見出しは全部 H2 (`## `)。最後の節は必ず `## 総括` (`#` を 2 個)。`### 総括` と書かない。

## 所見ごとの closed / partial / regressed 表
## 変異 13 件の赤 node 見積り
## 総括
