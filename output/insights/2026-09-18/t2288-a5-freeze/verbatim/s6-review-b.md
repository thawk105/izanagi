**must-fix はありません。** 指定の8観点で不一致は見つかりませんでした。read-only の照合とメモリ上の再計算を実施し、loader・測定・集約の実走はしていません。

参照略号：

- **D**＝[決定 fragment](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2288-a5-freeze/docs/spool/decisions/2026-09-18-dev-wave-t2288-a5-freeze-1.md)
- **I**＝[insight](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2288-a5-freeze/output/insights/2026-09-18/t2288-a5-freeze/README.md)
- **F**＝[floor_pair_driver.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2288-a5-freeze/orchestrator/campaign/floor_pair_driver.py)
- **A**＝[集約 issuer](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2288-a5-freeze/orchestrator/campaign/p3_b4_floor_artifact_issuer.py)
- **V**＝I と同じ directory の `verbatim/`

1. **［情報］凍結 bytes・親 commit・変更集合は一致。**  
   `sha256sum` と Python の独立計算は以下で一致し、D:44–46、I:43–44、V/specs.sha256.txt:1–3、V/s3-lens-b.md の表とも全桁一致しました。

   | spec | 実測 SHA-256 |
   |---|---|
   | rr95 | `990e3a6feb176ccf863315fde6e2afce43b7fc16053f50a1080641dde2570619` |
   | rr50 | `b582d20c37268f491e4c47bb7436731197c18e737cdcca43694c64fa3e0d5e37` |
   | rr5 | `d13c384473a5d24170e929f7e17aad9cc24479a5487ed0da21d06bc45430d8c4` |

   3 spec と D の作業ツリー bytes は凍結 commit の blob と一致。`0b4fbd7a6^` は `d2ebef7a407dc6be61622ed596cf08b8b518f606` で、全 spec の `source_commit` と一致しました。凍結 commit は指定の4ファイルのみ、485行追加です。

2. **［情報］較正・receipt・既決値は一致。**  
   3較正の実 SHA-256 は各 spec:86–89 の pin と全桁一致。`records` は rr95/rr50 が `1000000`、rr5 が `2000000`、全件 `threads=48`・`env_tag=pegasus`・`clocks_per_us=2100`。workload は較正 JSON と一致し、D2089.md:11–15 の文字列 `"0"`・`"95"/"50"/"5"`・`"0.9"` も逐語一致しました。

   receipt の実 SHA-256 は `760287f629ee96c5c0e31c43be7b6dc30bfbf48dd5ebbe4c0da8b5b0b3e389b0`。receipt:3003 の binary hash と全 artifact の値も一致し、receipt:3007 の genome は `silo|BACK_OFF=1,NO_WAIT_LOCKING_IN_VALIDATION=1,NO_WAIT_OF_TICTOC=0,WAL=0` です。

3. **［情報］seed 式と生成器を追試できた。**  
   D:31 の UTF-8・区切り `|`・改行なしの式で3 seed を再計算し、spec:95、D:44–46、V/specs.sha256.txt と全桁一致しました。指定 `make_specs.py:47` の式も同じです。さらに生成器をメモリ上で評価し、生成 JSON の直列化 bytes が3実ファイルと完全一致しました。

4. **［情報］集約予測名は一致。**  
   A:189・749・1189・1226 の直列化と命名を標準ライブラリで再現しました。末尾改行を含む canonical JSON の hash は workload が `7095cfaaa30f9b4f5228`、campaign が `3553fb844072ea43111a` となり、D:54 の予測名と一致します。期待3 path は重複なし、hash 一致、各2窓で、A:1036 の当該条件を満たします。summary の実内容による集約検証は未実施です。

5. **［情報］指定された loader の静的受理条件に適合。**  
   F:92・460・470・869・1060・1276 と照合し、ID、相対 path、UTC、非空・非重複の窓、参照閉包、`closed_strata`、各 spec 内の3出力相異を確認しました。3 spec 横断でも9出力は相異。全出力の親は spec と同じ実在 directory で、worktree 内の途中 component に symlink はなく、出力 leaf は全9件未作成でした。

6. **［情報］wave の実装面差分は0。**  
   観測 HEAD は凍結 commit 自身。`git diff --stat d2ebef7a…HEAD` は上記4ファイルのみで、`git diff HEAD` は空でした。`git ls-files --others --exclude-standard` の未追跡11件は worklog・insight・verbatim の記録類のみ。指定の `orchestrator/`・`tools/`・`hooks/` 配下の非 md や `.py`・`.sh` はありません。

7. **［情報］insight の記録間整合と binary 現物を確認。**  
   V/plan-summary.txt:1・3・5 の3 `plan_sha256` は I:54–56 と全桁一致。各248 session・496測定・各窓124 session、candidate/reference 各248件も一致します。負対照 stderr:12 の期待 hash `…0618`、観測 hash `…0619` は I:57 と一致しました。

   配置済み binary の実 hash は `7cdf0dc345f7eccdb50604e77521ce625c1792cc0eb8966b544f65a15ef274a4`、**701,760 bytes・mode 744** で、I:53 と一致。ただし過去の `place` の rc・当時の tree clean・policy 検査成功、および validate-only の rc・stdout bytes・stderr 空は、今回の指定資料から独立には確認していません。

8. **［情報］後続申し送りは実装と一致。**  
   I:95 の HEAD 固定は F:2230 の実行時照合と F:2700–2722 の header exact 比較に一致します。I:70 の「session 開始時刻」は F:2091 の `started < window.not_before or started >= window.not_after` と一致。48時間の隙間を終了→開始の分離保証と扱っていない点も適切です。

## 総括

**(a) must-fix 一覧**

- なし。凍結 bytes・記録・申し送りに修正必須の不一致は検出しませんでした。

**(b) 実測して一致した項目**

- spec 3 hash、凍結 blob、親 OID、4ファイルの変更集合。
- 較正 hash・セル値・workload 逐語、receipt hash・binary hash。
- seed 3件、生成器の出力 bytes、集約予測名。
- 出力 path の相異・親 directory・symlink 不在、実装面差分0。
- plan-summary と insight、負対照 hash、binary の bytes・mode。

**(c) 未確認のまま残る項目**

- loader／validate-only の独立再実行、plan 全文からの hash 再導出、過去の rc・stdout/stderr サイズ。
- `place` 実行当時の経路・policy・tree clean。
- 実測・finalize・集約の成功、実 campaign の時間分離と採用条件。