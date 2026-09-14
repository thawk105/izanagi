単独段 dispatch: stage=author; sandbox=workspace-write; parent=/work/1/SFC/tanab/izanagi/.codex/worktrees/t2519-impl

## 必読事項の射影

下記の絶対パスを読む。**この射影に挙げた file が読めなければ即停止**し、読めなかった path を
述べて終わること (自分で見つけた別 path の不在は停止理由にしない)。

1. `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2519-t2505-t316-inert/s4-adjudication.md`
   — **親の段 4 裁定。本作業の授権範囲と不変条件の正本。**
2. `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2519-t2505-t316-inert/measurement-1.md`
   — 何を見えるようにしたいのかの実測背景
3. `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2519-t2505-t316-inert/verbatim-d1849.md`
4. `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2519-t2505-t316-inert/verbatim-d1625.md`
5. `/work/1/SFC/tanab/izanagi/.codex/worktrees/t2519-impl/tools/pegasus/probes/t316_sandbox_backend_probe.py`
   — **編集対象。** 特に `_require_condition_gate` (1932 行付近〜1975 行付近)、
   `_condition_gate_receipt_summary` (320 行付近)、受理理由コード集合 (120 行付近)
6. `/work/1/SFC/tanab/izanagi/.codex/worktrees/t2519-impl/orchestrator/tests/test_t316_sandbox_probe.py`
   — **編集対象 (test 追加)。** 既存の条件関門まわりの test を先に読むこと
7. `/work/1/SFC/tanab/izanagi/.codex/worktrees/t2519-impl/orchestrator/campaign/condition_meaning_gate.py`
   — **読むだけ。1 byte も変更してはならない。** `ConditionArmRecord` の定義と
   `evidence` の構造、`_run_process` (1580 行付近〜1625 行付近)

## 作業 root と権限

- 作業 root は `/work/1/SFC/tanab/izanagi/.codex/worktrees/t2519-impl` である。**ここ以外を編集しない。**
- あなたはコードとテストだけを編集する。**`docs/` を 1 byte も編集しない。commit しない。
  `qsub` / `qstat` / `qdel` を実行しない。push しない。**
- `orchestrator/campaign/condition_meaning_gate.py` を変更してはならない (親の裁定 3)。
- 変更してよいのは次の 2 file だけである。
  - `tools/pegasus/probes/t316_sandbox_backend_probe.py`
  - `orchestrator/tests/test_t316_sandbox_probe.py`

## 実装する内容

`t316_sandbox_backend_probe.py` の `_require_condition_gate` は、`admission.admitted` が偽のとき
`RuntimeError` を投げる。現在そのメッセージは `terminal_status` と `reason_code` しか載せない。
**計算ノードで実際に何が起きたか (CMake の rc・stderr・argv) が失われている。**

拒否の直前に、**`supply` と `meaning` の各 record が持つ `evidence` の `detail` を、
process の stderr (`sys.stderr`) へ出力する**こと。拒否そのものは現行どおり維持する。

### 不変条件 (親の裁定 3。1 つでも破ったら停止して報告すること)

- **receipt へ `evidence` mapping を追加しない。** `_condition_gate_receipt_summary` と
  `SCHEMA_VERSION` を変えない。D1849 (射影 3) の逐語を 1 文字も動かさない。
- **受理理由コードの 2 契約 exact 一致を変えない。** D1625 (射影 4) を緩めない。
- **`if not admission.admitted: raise RuntimeError(...)` の拒否そのものを維持する。**
  拒否を緩める変更は絶対規律 2 の違反であり、無条件に禁止である。
- `evidence` は添字参照せず `.get("detail")` を使う。理由は D1849 が挙げているものと同じで、
  `detail` を持たない record (`unestablished` 等) で `KeyError` に化けさせないためである。
- 出力は `sys.stderr` へ書く。`print(..., file=sys.stderr)` でよい。stdout へ書かないこと
  (stdout は receipt path と verdict の JSON 1 行に使われている)。
- `detail` が `None` または空のときも、その旨が分かる形で 1 行出す (無音にしない)。

## 追加するテスト

`orchestrator/tests/test_t316_sandbox_probe.py` に、次を検査する正例を足すこと。

- admission が拒否されたとき、`supply` と `meaning` の `detail` が **stderr へ出ること**。
- そのとき **`RuntimeError` は現行どおり送出されること** (拒否が消えていないこと)。
- `detail` が無い record でも例外に化けず、拒否が起きること。

**機構の正例は実体を名指しし、依存先を stub で置き換えて機構を通らない緑にしないこと。**
`_require_condition_gate` を実際に呼ぶ形にすること。既存 test が使っている fixture や helper が
あればそれに倣うこと (射影 6 を先に読む)。

## 守るべき既存の規律

- **既存テストの期待値を変更しない。** 反転・緩和・skip・削除を禁じる。既存 test が赤になったら
  実装側が誤りである。期待値のほうが誤りだと判断した場合は、実装を変えずに報告して止めること。
- テストを甘くして緑にしない。fixture へ現行 hash を差し込まない。
- 期待値へ揮発 payload (working tree hash、時刻、path 等) を焼き込まない。
- **テスト新設の単位について、親の名指しを網羅と見なさないこと。** この repo には test file 自体の
  構造や命名を検査する制約 meta-test がありうる。自分で洗い出して走らせること。
- 指示外の受理集合変更をしないこと。変更前の現行の受理・拒否挙動を報告に明記すること。

## 実走について

- この sandbox では repo の test runner が動かないことがある。**走らせられたら走らせ、
  緑には実走した nodeid と範囲を併記すること。** 走らせられなかった場合は
  **`closed` と申告せず「実装済み・未実走」と正直に書くこと。** 実走は親が行う。
- `python -m pytest` が環境の guard に拒否される場合がある。repo の自走 harness があればそれを使い、
  `PYTHONPATH=.` が要ることがある。試した command と rc をそのまま報告すること。

## 完了報告に必ず含めるもの

- 変更した file と行範囲。
- 変更前後の受理・拒否挙動 (変わっていないことを明示)。
- 実走した test の nodeid と rc。実走できなかったならその旨と試した command。
- **所有外の caller・共有 fixture・consumer test への波及可能性の静的列挙。**
  `_require_condition_gate` の呼び出し元、`t316_sandbox_backend_probe.py` を import する test、
  BOUND_PATHS の sha256 を検査する経路を必ず含めること。

## 出力形式

次の見出しを H2 で立てて書くこと。

```
## 変更した内容
## 受理・拒否挙動の変化
## 実走結果
## 波及可能性の静的列挙
## 総括
```
