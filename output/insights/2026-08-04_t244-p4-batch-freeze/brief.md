# 段 1 brief — [T-244] D121 P4 batch freeze (2026-08-04)

- **scope:** D121 P4 (batch freeze = batch cardinality・全候補の事前 commit・seal までの結果非公開)
  の機械部品を、独立 leaf `orchestrator/campaign/reflux_batch.py` (仮名) + テストとして実装する。
  D149 (P1) と同じ順序 — **独立 golden を先に凍結 → 実装 → 監査**。production wiring はしない。
- **確定済みユーザー裁定:** 択一 3 = 軸 (iii) 必須化、triple をセットで定義
  (`docs/archive/worklog-phase3-0803-125-126.md` (126))。D150 = P4 は無条件義務。
  択一 1 = 予算値は下限式 `Q >= 1 + 32R + E_min` から再導出 (`docs/archive/worklog-phase3-0804-161.md`)。
  **U-A〜U-D (P3 origin ledger、うち U-D = batch を ledger の第一級にするか) は裁定待ち**
  (`docs/archive/worklog-phase3-0804-165.md`)。
- **不変条件:**
  1. `MAX_APPROVED_GENERATIONS = 1` (D114) 不変。cap-lift へ結線しない。
  2. 「P4 充足」と名乗らない — 名乗りは「P4 用 batch-freeze codec/FSM prototype」まで
     (D147 決定 (3)・D149 先例)。
  3. **U-D を予断しない** — origin ledger の event 文法・slot 表現・root/lock 設計を本 leaf で
     定義しない。P3 プランの nullable seam `batch_commitment_sha256` が将来の結合点。
  4. cardinality 下限の**値は未裁定** — ハードコードせず immutable 注入 + 欠落は fail-closed
     (D147 決定 (4) の floor 制約と同型)。既定値を持たない。
  5. freeze 後の member 変更拒否・seal 前の結果開示拒否は fail-closed (例外 = 失敗、黙過なし)。
  6. 凍結成果物 (`output/s1-freeze/`、proof chain、`docs/phase3-main-experiment.md`) に触れない。
- **成果物の形:** leaf 1 本 + 独立 golden (実装より先に凍結) + テスト + spool fragment
  (worklog / decisions) + 変異事前登録 (段 4、DW-M01) と実走。
- **並列分割:** 実装子 1 単位 (leaf + golden + テスト。所有 = 新規 file のみ、既存 file 編集なし)。
  段 2 プラン 1 本、段 3 敵対レンズ 2 本、段 6 レビュー 2 本 (設計択一が割れうるため軽量版にしない)。

## 親の provisional 裁定 (攻撃対象)

- **(P1)** 実装面 = batch commitment codec (member = `reflux_ir` wire 形式の候補文字列を
  `parse_wire`→`encode_wire` 往復で正準化、正準 bytes 列 → sha256 commitment、cardinality 記録)
  + freeze→seal の lifecycle (open→frozen→sealed) + 開示 gate (sealed 前は member 別結果を返さない)。
  親の provisional 裁定であり攻撃対象。
- **(P2)** DW-G04 との整合 = 本 leaf は「条件付き機能」ではなく D149 先例の「機械部品 + golden」と
  位置づける。発火する production path は現存せず、**実装したふりをしない** (テストだけが consumer)。
  この位置づけ自体を攻撃対象とする。
- **(P3)** member の重複は拒否 (batch は set。重複を許すと cardinality 下限が水増しで恒真化する)。
  攻撃対象。
- **(P4)** 結果の受理は frozen 後のみ・commitment に束縛された member のみ。seal は全 member の
  結果が揃うか明示 abort のときだけ許す (途中 seal で「非公開」が空文化しないため)。攻撃対象。

## DW-G05 (成果物影響)

実装しない場合: cap-lift の P4 が未充足のまま多世代開放が閉じ続けるだけで、現行の certified 選択・
材料レポート・試行台帳の値・受理集合・参照は 1 つも変わらない (承認上限 1 不変のため)。

## 前提実測 (段 1、2026-08-04)

- `orchestrator/campaign/reflux_ir.py` に `parse_wire` / `encode_wire` / `emit_predicate` が実在
  (P1 land 済み、golden = `orchestrator/tests/reflux_ir_expected_goldens.py`)。
- orchestrator/campaign に batch freeze 系実装は不在 (grep "batch" — s8b の git batch-check と
  silo_ladder の batch_commit カウンタのみで別性質)。
- 被覆検索 (性質 = 候補集合の事前 commit・開示遅延): orchestrator/tests に同性質の被覆なし。
  `test_reflux_ir.py` は IR 単体、`test_frozen_artifacts.py`/s8b freeze 系は成果物 bytes 凍結で別性質。
  **純増検出力 = 本 wave のテスト全部**。
- local main との乖離 0 commit (check_wave_startup rc=0、submodule 初期化済み)。
- DW-O08/O09/O10 = 不成立と判定 (freeze 族・凍結 bytes・producer write-path に触れない)。
  DW-O13 = 読了 — gate 入力の実在: member は wire 形式 (実在 field)。floor 値は実在 field 無し →
  注入 + fail-closed、同名識別子の二義化なし。
- 受入環境: 本 worktree (login node)。`tools/run_tests.py` 全走 + `check_docs.py`。性能実測なし (純 leaf)。

## erratum 1 (段 2 完了後・段 3 起動前、2026-08-04)

- **「U-A〜U-D は裁定待ち」は誤り。** worklog (171) (2026-08-04 の /rulings、本 worktree 作成前に
  land 済み) で **U-A〜U-G は全件親推奨どおり裁定済み**。特に **U-D = batch を origin ledger の
  第一級にする**、U-G = P3 充足は producer 結線と P7 まで含めて数える。
  親は起動時 snapshot の worklog (169)(170) と archive (165) だけを読み、(171) を見落とした。
  段 2 planner が反論として検出した (F31 と同型)。
- **不変条件 3 の読み替え:** 「U-D を予断しない」→「**採用済み U-D (第一級) と整合する**こと。
  本 leaf は ledger の event 文法・slot・root・lock を定義しないが、将来の第一級 batch event が
  格納・束縛すべき canonical bytes / digest / cardinality / policy を提供する codec/FSM とする」。
- 段 2 プランはこの訂正済み前提で起草されており流用可。段 3 レンズは訂正後の前提を攻撃対象にする。
