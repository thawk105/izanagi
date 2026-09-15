## 選択

**O-C を採る。** 既存の `t2500-tail-formal` 本走を投入・回収し、事前登録された飽和判定を進める。P1 の「帯の内部測定に研究価値が一つもない」は証明されていないが、今回の資料には内部点で検証する具体的な仮説・判定基準もない。P2 は「現行の凍結文書・実装では同時充足できない」という範囲で正しい。ただし、driver 名から依頼者の真意までは確定できない。**O-C は明示的な scope 選択であり、901〜998 µs の測定や T-2266 の完了としては扱わない。**

以下の相対パスは、すべて指定 worktree 内を指す。

## 親 brief の検査

- **F-1：回収・解析完了の記録を確認。**  
  `output/insights/2026-09-10/t2266-formal-1000us/README.md:17` に格子一致、`:88` に3 job の集約値、`:94` に rep 生値がある。再投入不要という判断は支持する。ただし投入日は同文書 `:9` では **9月9日投入・10日完了**。worklog 射影の「9月10日投入」と不一致。また同射影の `2026-09-10_t2266-…` は誤ったパスで、実在するのは日付後が `/` のパス。

- **F-2：裏取り不能。**  
  qstat の現在状態は静的資料から確認できない。親 brief のゼロ行という観測を、今回確認した事実には数えない。投入直前の再確認が必要。

- **F-3：確認。**  
  `orchestrator/campaign/backoff_extended_sweep.py:55` の拡張格子、`:86` の T2266、`:92` の T2418 に901〜998はない。`:1490` の CLI に点指定引数もない。formal 格子にもない（事前登録 `:160`）。

- **F-4：確認。ただし制約付きの結論。**  
  `orchestrator/campaign/b10_backoff_static_tail_formal.py:232` は正本パス・commit・作業ツリーの bytes を照合し、`:148` で格子を再生成、`:245` で spec から測定点を得る。`:777` の CLI に格子差替え引数はない。事前登録 `:1051` は定数置換を禁止する。**現在の契約を保ったまま、この driver で帯を測ることはできない。**

- **F-5：測定済みは確認。P1 への使い方に誤り。**  
  900の3 workload の値は `output/insights/2026-09-04/t2266-backoff-static-tail/README.md:59`、999は `output/insights/2026-09-07/t2266-tail-measurement/README.md:109`、1000は上記9月10日資料 `:88` にある。指定された9月2日資料 `:209` にも900までの完走訂正がある。  
  **−0.22〜−0.66% は999対1000の差であり、帯を挟む900対999の差ではない。** P1 の「両端の差は0.66%以内」は成立しない。また別日時の標本なので同一 job 内の比較でもない。

- **F-6：コード分岐を確認。性能の滑らかさは未証明。**  
  `backoff_extended_sweep.py:64` と `:71` より901〜998はそのまま符号化・復号できる。`patches/silo-backoff-fixed.patch:70` でも900・999と同じ商0の定数枝。これは内部で性能の局所変化が起こらない証拠にはならない。

- **F-7：先例の内容を確認。**  
  [D1848 射影](/home/SFC/tanab/.claude/jobs/a6836a0d/tmp/wave/t2266-tail-band/ref-D1848.md:3) は専用 identity による分離を決定し、`:29` で凍結格子への追加と既存 T2266 の一般化を却下している。ただし直接の対象は D1813 の探索走であり、帯そのものの価値を否定する裁定ではない。

- **F-8：裁定の内容を確認。P1 は導けない。**  
  [D1724 射影](/home/SFC/tanab/.claude/jobs/a6836a0d/tmp/wave/t2266-tail-band/ref-D1724.md:3) は18点の会計と誤差0.064%以内を記し、`:14` の列挙に901〜998はない。しかし列挙にないことは不要の証明ではなく、記述的モデルの追加検証も禁止していない。下流の v1 束縛は `tools/t2216_backoff_walk_model.py:53`、`tools/plotting/plot_t2266_tail_mechanism.py:38` で確認した。

- **F-9：実装・配線と過去の未投入記録を確認。現在の未投入は未確認。**  
  T2566 insight `output/insights/2026-09-14_t2566-tail-formal-driver/README.md:3` と T2593 insight `output/insights/2026-09-14/t2593-tail-formal-submission/README.md:136` に未投入とある。現在の submit script `:55` は `extended / t2266-tail / t2418-explore / t2500-tail-formal` の**4種**を受理し、job script `:616` は formal driver を起動する。約20分/job は事前登録 `:216` の**見積り**で、formal 本走の実測時間ではない。

## 計画

**コード・テスト・script の編集はゼロ。** 親が行う操作と記録を次に限定する。

| 段階 | file:line | 実行内容・判定 |
|---|---|---|
| scope 記録 | 新規 `output/insights/2026-09-15_t2266-tail-band/README.md:1` | O-C を選び、901〜998は未測のままと明記する。 |
| 重複確認 | `docs/b10-backoff-static-tail-submission.md:42` | 現在の queue と既存 submit receipt・完了成果物を確認。既投入 formal cohort があれば回収へ進み、重複投入しない。 |
| DW-G01 | `tools/pegasus/submit_b10_backoff_grid.sh:43` | 下記1 command で入口の生死を確認する。 |
| 入力確定 | 手順書 `:15`、formal driver `:232`・`:351` | 作業場所、正本 bytes と一致する祖先commit、実在する探索 campaign、repo外の出力親を確定する。探索 campaign は mode の参照に使う。 |
| 投入 | 手順書 `:29`、submit script `:244`、job script `:616` | 確定した入力を手順書の argv に入れ、3 workload を1回投入。group ID・job ID・入力を記録する。 |
| 規模 | 事前登録 `:160`・`:199` | 1000 / 1250 / 1768 / 2500 / 3535 / 5000 / 7070 / 9999、3 workload、性能・正しさ各5 rep。格子・rep を増減しない。 |
| 回収 | 手順書 `:49`、job script `:694` | 各 job の8 genome と execution report、`completion.json` を確認。部分投入失敗時は receipt の成功済み job を先に調べ、submit 全体を反射的に再実行しない。 |
| 集団解析 | 手順書 `:60`、formal driver `:571`・`:645` | 同じ group の3 campaign を明示して report を実行。WAL由来の整数カウンタ・正しさ記録・identity を検査する。 |
| 記録 | 新規 README、`docs/spool/` の新規 fragment | rep 生値、median、abort率、CV、job ID、区間判定、集団 verdict と失敗理由を保存。既存測定記録を上書きしない。 |

### DW-G01 の1 command

```bash
bash /work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2266-tail-band/tools/pegasus/submit_b10_backoff_grid.sh --help
```

`--dry-run` はない。引数処理は `:19`、未知引数拒否は `:47`、`--help` は `:43` で usage を出して終了する。したがってこれは**script の入口が動くことだけを確かめる最安の確認**であり、scheduler・入力・計算ノード・driver の健全性までは証明しない。本投入経路は `:126` 以降の環境確認、`:232` の receipt 書込み、`:250` の qsub に進む。

## 研究前進

事前登録 `docs/b10-backoff-static-tail-preregistration.md:123`・`:138` の「全 workload で登録述語を満たす飽和位置が存在する」を、右 tail の新規 cohort で検証し、throughput の費用も併記する。  
完了判定は全24 cell の規定標本と集団報告が揃い、飽和・域内非飽和・判別不能・invalid を規定どおり報告すること。肯定結果は完了条件にしない。

## 危険

- **scope の取り違え：** O-C 完了を901〜998の測定済み、T-2266完了、B-10完了へ読み替えない。
- **凍結・consumer：** 既存格子・事前登録 bytes・受理集合・schema を変更せず、formal report を v1 消費者へ渡さない。
- **標本の混入：** 過去の1000を流用しない。今回の1000は事前登録 `:181` が要求する同一 cohort の境界参照である。探索値も本格標本へ混ぜない。
- **誤認証：** formal driver `:346`・`:611` の `payload.certified is True` と anomaly 0 を維持する。`completion.json` の存在だけでは集団を valid としない。性能は未認証のまま。
- **走行中の変更：** 投入前に必要な文書変更を確定し、走行中の作業ツリー書込みは `output/` に限定する。

## 総括

O-C は既存の投入経路で、具体的な事前登録仮説を検証できる。  
P1 は過剰な断定であり、特に999対1000の差を900対999へ転用している点を訂正すべきである。  
P2 は現行契約下で成立するが、依頼者の真意の証明にはならない。  
本回答は静的読解のみ。ファイル変更・投入・テスト実走は行っていない。