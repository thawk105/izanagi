単独段 dispatch: stage=review; sandbox=read-only; parent=/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2519-t2505-t316-inert

## 必読事項の射影

下記の絶対パスを読む。**この射影に挙げた file が読めなければ即停止**し、読めなかった path を
述べて終わること (自分で見つけた別 path の不在は停止理由にしない)。

1. `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2519-t2505-t316-inert/s4-adjudication.md`
   — **親の段 4 裁定。実装の授権範囲と不変条件の正本。**
2. `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2519-t2505-t316-inert/s5-diff.patch` — **実装差分そのもの**
3. `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2519-t2505-t316-inert/s5-author-out.md` — 実装子の完了報告
4. `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2519-t2505-t316-inert/measurement-1.md`
5. `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2519-t2505-t316-inert/verbatim-d1849.md`
6. `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2519-t2505-t316-inert/verbatim-d1625.md`
7. `/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2519-t2505-t316-inert/tools/pegasus/probes/t316_sandbox_backend_probe.py`
   — **変更後の現物。** `_require_condition_gate` (1932 行付近〜1985 行付近)、
   `_condition_gate_receipt_summary` (320 行付近)、受理理由コード集合 (120 行付近)
8. `/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2519-t2505-t316-inert/orchestrator/tests/test_t316_sandbox_probe.py`
   — **変更後の現物。** 追加された test (42 行付近〜86 行付近) と、その前後の既存 test
9. `/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2519-t2505-t316-inert/orchestrator/campaign/condition_meaning_gate.py`
   — 読むだけ。`_run_process` (1580 行付近〜1625 行付近) と `ConditionArmRecord` の `evidence`

## 立場と権限

- あなたは **read-only** の敵対レビュー者である。file を書けない。出力は最終メッセージだけである。
- **commit しない。docs を書かない。`qsub` / `qstat` / `qdel` を実行しない。**
- 書込可能な tmp が無いため pytest 緑は要求しない。**静的検査でよい。** テストの実走は親が行う。
  実走していないものを緑と書かないこと。
- 予算が尽きそうなら、途中までの結論を下記の出力形式どおりに書いて終わること。無出力が最悪である。
- **攻撃が成立しなかった項目は正直にそう書くこと。全項目を無理に成立させないこと。**

## 親が既に実走した結果 (これを緑の根拠として再利用してよい)

- `orchestrator/tests/test_t316_sandbox_probe.py` 全体: **145 passed in 4.61s** (rc=0)。
- 追加 test 単体 (`::test_require_condition_gate_rejection_reports_detail_to_stderr`):
  **1 passed in 4.44s** (rc=0)。
- 基底 (変更前 HEAD) と現行の test 関数名集合を突き合わせた結果、**削除ゼロ・追加 1 件**。

## レンズ — 正しさ防壁と偽の緑

このレンズの担当は **絶対規律 2 (正しさゲートを緩める変異を許さない)** である。次を探せ。

1. **拒否が本当に維持されているか。** `if not admission.admitted:` の分岐と `RuntimeError` の送出が、
   変更前と意味的に同一か。print が例外を飲み込む経路、print が例外を投げて拒否より先に脱出する経路
   (例: `evidence` が dict でない、`record` が期待型でない、stderr が閉じている) が無いか。
   **拒否より先に別の例外で脱出するなら、それは拒否の意味を変えている。**
2. **受理集合が変わっていないか。** D1625 の 2 契約 exact 一致 (P:124-133、374-386)、
   `_condition_gate_receipt_summary`、`SCHEMA_VERSION` のいずれかが動いていないか。
3. **D1849 に反していないか。** receipt へ `evidence` mapping が載る経路が生まれていないか。
   `RuntimeError` のメッセージは receipt の `observations.S6.error.message` に載る。
   **print した内容がそこへ回り込む経路が無いことを確かめよ。**
4. **追加 test が機構を通る正例になっているか。** 依存先を stub していないか、実体を名指ししているか。
   - 実 CMake と実 gate を通しているか、それとも見かけだけか。
   - `FATAL_ERROR` を仕込んで configure を失敗させる作りは、**測りたい機構 (拒否時に detail が出る)
     を本当に通しているか。** 測りたいものと違う経路で緑になっていないか。
   - 期待値へ揮発 payload (path、時刻、hash) が焼き込まれていないか。
     `assert cmake in lines[0]` は `shutil.which("cmake")` の結果に依存する。これは揮発か否か。
   - test が**将来の正しい変更で壊れる**過剰な exact 一致を持っていないか
     (例: `len(lines) == 2`、`captured.out == ""`、例外メッセージの完全一致)。
     壊れるとしたら、それは守るべき契約か、単なる脆さか。
5. **テストを甘くする方向の変更が紛れていないか。** 既存 test の期待値が 1 文字でも動いていないか
   (射影 2 の diff で確認せよ)。

## 出力形式

次の見出しを H2 で立てて書くこと。

```
## 拒否の維持
## 受理集合と D1849 / D1625
## 追加 test は機構を通るか
## must-fix
## 成立しなかった攻撃
## 総括
```

`## must-fix` の各項目には、**放置すると成果物 (certified 選択・レポート・台帳) の値・受理集合・参照が
どう変わるかを 1 行で**書くこと。書けない項目は must-fix にせず nit として挙げること。
`## 成立しなかった攻撃` には、攻撃を試みたが証拠が支えなかった項目を正直に挙げること。
`## 総括` は 3 行以内。
