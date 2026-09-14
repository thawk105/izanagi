単独段 dispatch: stage=fix; sandbox=workspace-write; parent=/work/1/SFC/tanab/izanagi/.codex/worktrees/t2519-impl

## 必読事項の射影

下記の絶対パスを読む。**この射影に挙げた file が読めなければ即停止**し、読めなかった path を
述べて終わること (自分で見つけた別 path の不在は停止理由にしない)。

1. `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2519-t2505-t316-inert/s4-adjudication.md`
   — 親の段 4 裁定。授権範囲と不変条件の正本。
2. `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2519-t2505-t316-inert/s6-lensA-out.md`
   — **敵対レビュー A。本 fix が閉じる must-fix の出典。**
3. `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2519-t2505-t316-inert/s5-diff.patch` — 現在の実装差分
4. `/work/1/SFC/tanab/izanagi/.codex/worktrees/t2519-impl/tools/pegasus/probes/t316_sandbox_backend_probe.py`
   — **編集対象。** `_require_condition_gate` (1932 行付近〜1985 行付近)
5. `/work/1/SFC/tanab/izanagi/.codex/worktrees/t2519-impl/orchestrator/tests/test_t316_sandbox_probe.py`
   — **編集対象 (test 追加)。** 既存の追加 test
   (`test_require_condition_gate_rejection_reports_detail_to_stderr`、42 行付近〜86 行付近)

## 作業 root と権限

- 作業 root は `/work/1/SFC/tanab/izanagi/.codex/worktrees/t2519-impl` である。**ここ以外を編集しない。**
- **`docs/` を 1 byte も編集しない。commit しない。`qsub` / `qstat` / `qdel` を実行しない。push しない。**
- `orchestrator/campaign/condition_meaning_gate.py` を変更してはならない。
- 変更してよいのは次の 2 file だけである。
  - `tools/pegasus/probes/t316_sandbox_backend_probe.py`
  - `orchestrator/tests/test_t316_sandbox_probe.py`

## 閉じる must-fix (レビュー A、親が real と裁定した)

> **診断出力の失敗が従来の拒否例外を置換する。**
> 対象: probe の追加 print (1968 行付近)。診断処理が失敗しても従来の `RuntimeError` を送出する
> 構造にしてください。
> **成果物への影響: receipt の `observations.S6.error.type/message` が条件関門の拒否情報から
> 出力障害の型・文面へ変わり、拒否理由が失われます。受理集合は広がりません。**

現在の実装では、`print(..., file=sys.stderr)` が例外を投げると (stderr が閉じている、書込み先の
障害など)、その例外が呼び出し元へ伝播し、**条件関門が拒否したという事実そのものが失われる**。
これは本 wave の目的 (拒否の理由を見えるようにする) と正反対の結果になる。

## 直す内容

**診断出力が何らかの理由で失敗しても、従来どおり `RuntimeError` が送出されるようにすること。**

設計の判断はあなたに任せる。ただし次を満たすこと。

- `RuntimeError` のメッセージは**現在と 1 文字も変えない**
  (`"condition gate rejected t316 CCBench build: supply=.../..., meaning=.../..."`)。
- 拒否そのものを緩めない。`admission.admitted` が真のときの経路を変えない。
- **診断出力の失敗を完全に無言にしない方が望ましいが、そのための追加処理が再び例外を投げて
  拒否を置換する形にはしないこと。** 拒否の送出が最優先である。
- 捕捉する例外の範囲は、握り潰しが監査で問題になる型を避けて選ぶこと。選んだ理由を報告に書くこと。

## 追加するテスト

診断出力が失敗する状況を作り、**それでも `RuntimeError` が従来のメッセージで送出されること**を
検査する正例を足すこと。

- 既存の追加 test (`test_require_condition_gate_rejection_reports_detail_to_stderr`) の作りに倣い、
  **実 CMake と実 gate を通す**こと。stub で機構を迂回した緑にしないこと。
- 診断出力を失敗させる手段は、実際に `print` が例外を投げる状況を作ること
  (例: `sys.stderr` を書込み不能なオブジェクトへ差し替える)。
  **`_require_condition_gate` 自体を monkeypatch で置き換えてはならない** — それでは機構を通らない。

## 守るべき既存の規律

- **既存テストの期待値を変更しない。** 反転・緩和・skip・削除を禁じる。既存 test が赤になったら
  実装側が誤りである。期待値のほうが誤りだと判断した場合は、実装を変えずに報告して止めること。
- テストを甘くして緑にしない。fixture へ現行 hash を差し込まない。
- 期待値へ揮発 payload (working tree hash、時刻、path 等) を焼き込まない。
- **テスト新設の単位について、親の名指しを網羅と見なさないこと。** 構造や命名を検査する制約
  meta-test を自分で洗い出して走らせること。
- 指示外の受理集合変更をしないこと。

## レビュー A が nit として挙げた点 (直すかはあなたの判断。直すなら理由を書くこと)

- `assert cmake in lines[0]` は `shutil.which` が symlink の別名を返す環境で、正しい出力でも
  失敗しうる。gate は executable を `resolve` する。
- `len(lines) == 2` は診断行の追加のような正しい変更でも壊れる、表示形式への過剰な固定である。

**これらは must-fix ではない。** 直さない判断も正当であり、その場合は理由を書くこと。

## 実走について

- この sandbox では repo の test runner が `rc=16` で動かないことがある。
  **走らせられたら走らせ、緑には実走した nodeid と範囲を併記すること。**
  走らせられなかった場合は **`closed` と申告せず「実装済み・未実走」と正直に書くこと。**
- 試した command と rc をそのまま報告すること。

## 完了報告に必ず含めるもの

- 変更した file と行範囲。
- 捕捉する例外の範囲と、その選択理由。
- 変更前後の受理・拒否挙動 (変わっていないことを明示)。
- 実走した test の nodeid と rc。実走できなかったならその旨と試した command。
- 所有外の caller・共有 fixture・consumer test への波及可能性の静的列挙。

## 出力形式

次の見出しを H2 で立てて書くこと。

```
## 変更した内容
## 例外捕捉の範囲と理由
## 受理・拒否挙動の変化
## nit への対応
## 実走結果
## 波及可能性の静的列挙
## 総括
```
