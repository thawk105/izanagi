単独段 dispatch: stage=consult; sandbox=read-only; parent=/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2519-t2505-t316-inert

## 必読事項の射影

下記の絶対パスを読む。**この射影に挙げた file が読めなければ即停止**し、読めなかった path を
述べて終わること (自分で見つけた別 path の不在は停止理由にしない)。

1. `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2519-t2505-t316-inert/s1-brief.md` — 親の段 1 brief
2. `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2519-t2505-t316-inert/measurement-1.md` — 計算ノード実測の逐語
3. `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2519-t2505-t316-inert/analysis-1-configure-failed.md`
   — **親が実測の原因を特定したと主張する分析。本レンズの主たる攻撃対象。**
4. `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2519-t2505-t316-inert/s2-plan-out.md` — 段 2 plan 子の起草
5. `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2519-t2505-t316-inert/verbatim-d1936-item17.md`
6. `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2519-t2505-t316-inert/verbatim-d1856.md`
7. `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2519-t2505-t316-inert/verbatim-d1625.md`
8. `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2519-t2505-t316-inert/verbatim-d1849.md`
9. `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2519-t2505-t316-inert/verbatim-tasks.md`
10. `/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2519-t2505-t316-inert/orchestrator/campaign/condition_meaning_gate.py`
    — 少なくとも `_run_process` (1580 行付近〜1625 行付近)、`_configure_compile_commands` (1683 行付近)、
    `_configure_defines` (1664 行付近)、inert 分岐 (2600 行付近〜2710 行付近)、CLI の main (4155 行付近〜)
11. `/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2519-t2505-t316-inert/tools/pegasus/probes/t316_sandbox_backend_probe.py`
    — 少なくとも `_execute_ccbench_build` (1826 行付近〜1930 行付近) と `_require_condition_gate` (1932 行付近〜1975 行付近)
12. `/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2519-t2505-t316-inert/output/insights/2026-09-02/a2-condition-gate-patched-root/README.md`
    — 同型の先行事例
13. `/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2519-t2505-t316-inert/external/ccbench/cmake/Options.cmake`
    — 素の CCBench が持つ CMake option の一覧

## 立場と権限

- あなたは **read-only** の敵対検証者である。file を書けない。出力は最終メッセージだけである。
- **commit しない。docs を書かない。`qsub` / `qstat` / `qdel` を実行しない。**
- 書込可能な tmp が無いため pytest 緑は要求しない。**静的検査でよい。** テストの実走は親が行う。
  実走していないものを緑と書かないこと。
- 予算が尽きそうなら、途中までの結論を下記の出力形式どおりに書いて終わること。無出力が最悪である。
- **攻撃が成立しなかった項目は正直にそう書くこと。全項目を無理に成立させないこと。**

## レンズ — 正しさ境界と整合

このレンズの担当は **絶対規律 2 (正しさゲートを緩める変異を許さない) と絶対規律 3 (正しさシグナルを
後付けにしない)**、および一次資料との整合である。**親 brief と親の分析 (射影 3) 自身が主たる検査対象
である。** 次を探せ。

1. **親の分析 (射影 3) の推論の穴。** 親は「configure-failed の原因は (A) 素の木に
   `CCBENCH_BACKOFF_FIXED` が無いこと、(B) CCBench が使わない izanagi 固有変数 3 件を渡していること」
   と断定した。**この断定は、今回の job が出した CMake stderr の逐語を見ずに下されている。**
   - 事実 1〜5 のどれかが、主張を支えていないのに支えているかのように書かれていないか。
   - **requested 側と stock 側のどちらで落ちたか**が未確定なまま、原因を両側に帰属させていないか。
   - (A) と (B) 以外に、同じ reason code を出す経路で**排除されていないもの**が残っていないか。
   - 親が引いた行番号・逐語が、現物と食い違っていないか。食い違いは file:line で示せ。
2. **「偽の緑」への滑り。** 射影 12 の A-2 insight は「関門だけを通す修正は偽の緑を作りうる」と
   名指しで警告している。親の分析と段 2 plan (射影 4) が示す次の一手に、この滑りの芽が無いか。
   - 段 2 plan が勧める「既存 CLI を計算ノードで走らせて `evidence.detail` を得る」案は、
     gate の判定を迂回して**緑の代用**を作らないか。CLI の緑を t316 実経路の緑と読み替える危険はないか。
   - 段 2 plan の「実装面の最小変更」案 (P:1967-1972 で `detail` を job stderr へ 1 行出す) は、
     D1849 / D1625 を実際に守るか。守らない箇所があれば file:line で示せ。
3. **規律 3 との整合。** 「なぜ壊れたか」を構造化して返すことは規律 3 の要求である。
   一方で本 wave の依頼は「本題の実測だけ。仮想リスク向けの gate・検査・台帳・一般化の追加は scope 外」
   と定める。**原因の直接証拠を取る行為が、この 2 つのどちらに属するか**を判定せよ。
4. **完了判定の正しさ。** T-2519 と T-2505 を「満たした」と書ける条件は何か。
   D1936 項17・D1856・台帳本文の逐語だけから導け。親と段 2 plan の判定 (どちらも「未完」寄り) が
   **厳しすぎる / 緩すぎる**なら、逐語を引いて示せ。
5. **親の実測値の一般化。** 親は 1 allocation・1 ノード・1 commit の観測から何を一般化したか。
   一般化してはいけないものを一般化していないか。

## 出力形式

次の見出しを H2 で立てて書くこと。

```
## 親の分析への攻撃
## 偽の緑への滑り
## 規律 3 と scope の境界
## 完了判定の判定
## 成立しなかった攻撃
## 総括
```

`## 成立しなかった攻撃` には、攻撃を試みたが証拠が支えなかった項目を正直に挙げること。
`## 総括` には、親が段 4 で裁定すべき争点を 3 行以内で書くこと。
