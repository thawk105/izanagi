単独段 dispatch: stage=review; sandbox=read-only; parent=/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2519-t2505-t316-inert

## 必読事項の射影

下記の絶対パスを読む。**この射影に挙げた file が読めなければ即停止**し、読めなかった path を
述べて終わること (自分で見つけた別 path の不在は停止理由にしない)。

1. `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2519-t2505-t316-inert/s4-adjudication.md` — 親の段 4 裁定
2. `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2519-t2505-t316-inert/s5-diff.patch` — **実装差分そのもの**
3. `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2519-t2505-t316-inert/s5-author-out.md`
   — 実装子の完了報告。**波及可能性の静的列挙を含む。その列挙の網羅性が本レンズの主題である。**
4. `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2519-t2505-t316-inert/measurement-1.md`
5. `/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2519-t2505-t316-inert/tools/pegasus/probes/t316_sandbox_backend_probe.py`
   — 変更後の現物
6. `/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2519-t2505-t316-inert/tools/pegasus/probes/t316_sandbox_backend_probe.pbs`
   — **`BOUND_PATHS` (54 行付近〜81 行付近) の sha256 照合。probe の bytes が変わる影響の中心。**
7. `/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2519-t2505-t316-inert/orchestrator/tests/test_t316_sandbox_probe.py`
   — 変更後の現物
8. `/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2519-t2505-t316-inert/docs/pegasus-runbook.md`
   — probe の分類表 (541 行付近)

## 立場と権限

- あなたは **read-only** の敵対レビュー者である。file を書けない。出力は最終メッセージだけである。
- **commit しない。docs を書かない。`qsub` / `qstat` / `qdel` を実行しない。**
- 書込可能な tmp が無いため pytest 緑は要求しない。**静的検査でよい。** テストの実走は親が行う。
  実走していないものを緑と書かないこと。
- 予算が尽きそうなら、途中までの結論を下記の出力形式どおりに書いて終わること。無出力が最悪である。
- **攻撃が成立しなかった項目は正直にそう書くこと。全項目を無理に成立させないこと。**

## 親が既に実走した結果

- `orchestrator/tests/test_t316_sandbox_probe.py` 全体: **145 passed in 4.61s** (rc=0)。
- 追加 test 単体: **1 passed in 4.44s** (rc=0)。
- 基底と現行の test 関数名集合: **削除ゼロ・追加 1 件**。
- **これ以外の file はまだ走らせていない。** 何を走らせるべきかが本レンズの主題である。

## レンズ — 波及と焦点走の範囲

このレンズの担当は **変更が届く先の全列挙**である。実装子は射影 3 で 5 つの波及先を挙げた。
**その列挙が網羅であるかを疑え。** 次を探せ。

1. **probe の bytes が変わることの波及を全列挙せよ。**
   - 射影 6 の `BOUND_PATHS` は live file と commit 済み blob の sha256 一致を要求する。
     **親が commit する前に job を投入すると何が起きるか。** commit した後の再投入で何が変わるか。
   - repo 内で `t316_sandbox_backend_probe.py` の内容・sha・行番号・分類を pin している箇所を、
     **path 検索だけでなく、role 名・分類名・xdist group 名など path 以外の key でも探せ。**
     path の hit 0 件を pin なしと結論しないこと。
   - 既存の receipt (`output/env/pegasus/t316-sandbox-backend/*/receipt.json`) は
     `runtime_sha256` に probe の sha を持つ。それらが今回の変更で無効になるか、ならないか。
2. **焦点走に含めるべき test file を全列挙せよ。** 実装子は `test_hooks.py`、
   `test_official_perf_closure.py`、`test_pytest_collection_config.py` を「未実走」と挙げた。
   - この 3 つで足りるか。**`_require_condition_gate` の呼び出し元、probe を import する経路、
     probe の行番号や構造を検査する meta-test、docs との整合を検査する checker を、
     間接参照まで 2 段辿って列挙せよ。** module 名の grep だけでは helper 経由の consumer を必ず外す。
   - 新しく追加された test が、**他の test file の実行時間や並列度に影響する**経路はないか
     (実 CMake を 2 回走らせる test である)。この repo は「テスト全体 5 分」を上限にしている。
3. **追加 test の所要時間。** 単体で 4.44 秒、file 全体で 4.61 秒だった。
   - この差は何を意味するか。追加 test が実際に CMake を 2 回走らせているなら、
     4.61 秒に収まるのは説明が要る。**説明がつかないなら、test が測りたい経路を通っていない疑いがある。**
     これは本レンズで最も重要な検査である。
4. **docs との整合。** 射影 8 の分類表や、probe を参照する docs に、今回の変更で更新が要るものがあるか。
   **無いなら無いと書け。** 仮想リスクで docs 更新を足さないこと。
5. **実装子の報告の誤り。** 射影 3 の記述と現物が食い違う箇所があれば file:line で示せ。

## 出力形式

次の見出しを H2 で立てて書くこと。

```
## bytes 変更の波及
## 焦点走に含めるべき file
## 追加 test の所要時間の説明
## docs 整合
## must-fix
## 成立しなかった攻撃
## 総括
```

`## must-fix` の各項目には、**放置すると成果物 (certified 選択・レポート・台帳) の値・受理集合・参照が
どう変わるかを 1 行で**書くこと。書けない項目は must-fix にせず nit として挙げること。
`## 成立しなかった攻撃` には、攻撃を試みたが証拠が支えなかった項目を正直に挙げること。
`## 総括` は 3 行以内。
