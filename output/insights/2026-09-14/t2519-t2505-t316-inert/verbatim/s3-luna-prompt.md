単独段 dispatch: stage=consult; sandbox=read-only; parent=/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2519-t2505-t316-inert

## 必読事項の射影

下記の絶対パスを読む。**この射影に挙げた file が読めなければ即停止**し、読めなかった path を
述べて終わること (自分で見つけた別 path の不在は停止理由にしない)。

1. `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2519-t2505-t316-inert/s1-brief.md` — 親の段 1 brief
2. `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2519-t2505-t316-inert/measurement-1.md` — 計算ノード実測の逐語
3. `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2519-t2505-t316-inert/analysis-1-configure-failed.md` — 親の原因分析
4. `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2519-t2505-t316-inert/s2-plan-out.md`
   — 段 2 plan 子の起草。**本レンズの主たる攻撃対象。**
5. `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2519-t2505-t316-inert/verbatim-d1936-item17.md`
6. `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2519-t2505-t316-inert/verbatim-d1856.md`
7. `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2519-t2505-t316-inert/verbatim-d1625.md`
8. `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2519-t2505-t316-inert/verbatim-d1849.md`
9. `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2519-t2505-t316-inert/verbatim-tasks.md`
10. `/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2519-t2505-t316-inert/tools/pegasus/probes/t316_sandbox_backend_probe.py`
    — 少なくとも `_execute_ccbench_build` (1826 行付近〜1930 行付近)、`_require_condition_gate`
    (1932 行付近〜1975 行付近)、`observe_s6` (1975 行付近〜)、受理理由コード集合 (120 行付近)
11. `/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2519-t2505-t316-inert/tools/pegasus/probes/t316_sandbox_backend_probe.pbs`
12. `/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2519-t2505-t316-inert/orchestrator/campaign/condition_meaning_gate.py`
    — 少なくとも CLI の main (4155 行付近〜4230 行付近) と `_run_process` (1580 行付近〜1625 行付近)
13. `/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2519-t2505-t316-inert/output/insights/2026-09-09/t2213-probe-condition-gate/README.md`

## 立場と権限

- あなたは **read-only** の敵対検証者である。file を書けない。出力は最終メッセージだけである。
- **commit しない。docs を書かない。`qsub` / `qstat` / `qdel` を実行しない。**
- 書込可能な tmp が無いため pytest 緑は要求しない。**静的検査でよい。** テストの実走は親が行う。
  実走していないものを緑と書かないこと。
- 予算が尽きそうなら、途中までの結論を下記の出力形式どおりに書いて終わること。無出力が最悪である。
- **攻撃が成立しなかった項目は正直にそう書くこと。全項目を無理に成立させないこと。**

## レンズ — scope と実効性

このレンズの担当は **依頼が定めた scope の境界と、提案された次の一手が実際に効くか**である。
本 wave の依頼は次のとおりである (ユーザーの逐語):

> 実測が目的なので、関門を通すためだけの修正で偽の緑を作らない。規律 2 を緩めない。本題の実測だけ。
> 仮想リスク向けの gate・検査・台帳・一般化の追加は scope 外。

次を探せ。

1. **段 2 plan の「実装面の変更は現時点で不要」は本当か。** plan は「既存 CLI をそのまま計算ノード job
   で実行する」ことを最優先に置いた。
   - その job を走らせるには何が新たに必要か (pbs、shell script、依存 build、環境変数、投入手順)。
     **それらは「実装面 (コード・テスト・実行可能な probe / harness / script・機械設定)」に当たらないか。**
     当たるなら「実装面の変更は不要」は誤りであり、その旨を file:line で示せ。
   - 既に repo にある機構だけで、新しい実行可能物を 1 byte も足さずに同じ診断ができる経路はあるか。
     あるなら具体的に示せ。無いなら無いと書け。
2. **費用対効果。** 原因の直接証拠 (CMake stderr の逐語) を取るために計算ノード job を 1 本足すことは、
   本 wave の目的 (T-2519 / T-2505 の実測) に対して**必要**か、それとも**あれば嬉しい**に留まるか。
   - 射影 3 の親の分析は、直接証拠なしで原因を特定したと主張する。その主張が十分なら追加 job は不要になる。
     不十分なら何が足りないかを 1 行で書け。
   - 追加 job を打たずに本 wave を閉じた場合、成果物 (insight・worklog・decisions) に何が書けて
     何が書けないかを列挙せよ。
3. **T-2519 / T-2505 を閉じられるか。** 依頼は「2 件は同じ probe で満たせる見込みなので 1 wave に
   まとめ、満たせないと段 1 で分かった時点で分ける」と言う。
   - 実測 1 の結果を踏まえ、**2 件は分けるべきか、まとめたままでよいか。** 逐語を引いて判定せよ。
   - 「到達しない」という実測結果で台帳項を閉じられるか。閉じられないなら、台帳へ何を書き残すのが
     正しいか。
4. **親 brief 自身の誤り。** 射影 1 の brief には、実測前に書かれた前提がある。実測後の今、
   誤っていた記述、過大だった不変条件、実際には効かない成果物の形があれば file:line で示せ。
   - 特に brief の「成果物の形」は receipt に supply entry と `comparison` が残ることを期待していた。
     実際には例外で失われた。この期待は最初から成立しえなかったのか、条件付きで成立したのか。
5. **scope 外への滑り。** 親の分析と段 2 plan が、依頼の scope を超えて gate・検査・台帳・一般化を
   足す方向へ滑っていないか。滑っているなら、どこで止めるべきかを書け。
   **逆に、scope を狭く読みすぎて本題の実測が未完のまま閉じられようとしていないかも見よ。**

## 出力形式

次の見出しを H2 で立てて書くこと。

```
## 「実装面の変更は不要」の検証
## 追加 job の費用対効果
## T-2519 / T-2505 を閉じられるか
## 親 brief の誤り
## scope の滑り
## 成立しなかった攻撃
## 総括
```

`## 成立しなかった攻撃` には、攻撃を試みたが証拠が支えなかった項目を正直に挙げること。
`## 総括` には、親が段 4 で裁定すべき争点を 3 行以内で書くこと。
