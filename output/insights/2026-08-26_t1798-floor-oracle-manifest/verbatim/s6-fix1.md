### 直したもの (file:line 粒度、赤 1 件ごとに対応づける)

1. [test_buildcache_v2.py:461](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1798-floor-oracle-manifest/orchestrator/tests/test_buildcache_v2.py:461)
   - production 系列の合成 source を Git repository として初期化し、期待 HEAD を設定。

2. [test_s8b_floor_campaign.py:3121](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1798-floor-oracle-manifest/orchestrator/tests/test_s8b_floor_campaign.py:3121)
   - staged postflight の既存入力 binding に従来の config hash を明示。assert は不変。

3–5. [test_s8b_floor_campaign.py:3676](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1798-floor-oracle-manifest/orchestrator/tests/test_s8b_floor_campaign.py:3676)
   - production drift 正例部分の oracle receipt を実 source の config hash と一致させ、tracked・archive・inode の各意図した postflight gate まで到達可能にした。

6. [s8b_floor_campaign.py:3993](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1798-floor-oracle-manifest/orchestrator/campaign/s8b_floor_campaign.py:3993)、[s8b_floor_campaign.py:4266](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1798-floor-oracle-manifest/orchestrator/campaign/s8b_floor_campaign.py:4266)、[s8b_floor_campaign.py:4404](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1798-floor-oracle-manifest/orchestrator/campaign/s8b_floor_campaign.py:4404)
   - lease cleanup wrapperを維持しつつ、実際の `build_fn(...)` gateway を public `build_cells` の所有に戻した。
   - 静的 registry 再現結果は admitted gateway 2 件一致、missing 0 件。

7. [s8b_floor_campaign.py:3809](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1798-floor-oracle-manifest/orchestrator/campaign/s8b_floor_campaign.py:3809)
   - base-only postflight は従来どおり再検証結果を直接返す。source-dir の追加 metadata だけ `replace()` を使う。

8. [test_s8b_floor_campaign.py:4801](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1798-floor-oracle-manifest/orchestrator/tests/test_s8b_floor_campaign.py:4801)
   - marker の既存入力 binding に従来の config hash を明示。marker 実装の hash 出所と assert は変更していない。

### 実装側を直した理由 (赤ごとに、なぜ期待値でなく実装が誤りだったか)

1. production observer は実 Git top-level と HEAD を再取得するため、probe だけを模擬した合成 root が不完全だった。
2. wave 用共有 fixture の config 値が既存 staged 正例へ混入していた。独立 expected hash の既存契約が正しい。
3–5. drift 以前に oracle receipt と actual source が不一致だったため、意図した単一 drift 理由へ到達していなかった。
6. build authority の登録単位は public `build_cells` であり、helper への呼出し移動が registry から gateway を消していた。
7. canonical metadata が不要な base-only 経路でも無条件に新 object を作る退行だった。
8. marker は binding の config hash を記録する既存契約が正しく、共有 fixture の混線が原因だった。

今回の fix では既存 assert、skip、xfail、期待 detail codeを変更していない。

### 期待値が誤りだと判断したもの (あれば。実装は変えずに報告する)

なし。

### 実走した検査 (nodeid と範囲を併記)

pytest の緑は 0 件。

次の exact 8 nodeid を通常 dispatch 1 回、force-dispatch 2 回試みたが、すべて `qstat -Q preflight rc=1`、`child_started=false`、rc=16 でテスト child は未起動だった。

- `test_buildcache_v2.py::test_production_dependency_series_materializes_oracle_pass_then_miss_hit`
- `test_s8b_floor_campaign.py` の帰属赤 7 nodeid全部。production drift は archive、source-inode、tracked の3 parameterを個別指定。

実走できた静的検査:

- 変更対象6 Python fileの AST parse
- campaign 全体の materializer registry 再現: admitted gateway一致、missing 0
- `git diff --check`
- 結合文字なし
- index変更なし
- 禁止対象9件を個別確認し、すべて変更なし

### 実装済み・未実走のもの

- 上記 exact 8 nodeid
- `test_buildcache_v2.py` と `test_s8b_floor_campaign.py` の全体回帰
- 新設 `test_sort_swo_dependency_material.py`
- M01〜M08 の変異巡。静的には各照準と単一 detail reason を維持
- real-root opt-in と裁定の production 正例再実測

### 所有外への波及可能性 (静的列挙)

- `build_cells` の通常実行・resume caller。公開 signature と builder identity 検査は不変。
- `buildcache.build_v2` の post-oracle caller。6-key capability は floor のみで、generic caller は不変。
- `s1_direct_comparison.prepare_cell` は floor callerから canonical rootを受ける。
- plain-runner coverage、pytest collection、既存 oracle E2E。
- receipt・digest の pin consumer、共有 Masstree fixture、oracle primitiveは未変更。
- 非帰属の `output_snapshot_ignores.py` と該当赤には触れていない。

## 総括

8件の帰属赤に対応する修正を未 commit・未 stage の作業ツリーへ残した。禁止対象、docs、外部 subtree、非帰属赤は変更していない。

pytest は dispatch infrastructure failureにより未実走なので、完了・closed・緑とは申告しない。