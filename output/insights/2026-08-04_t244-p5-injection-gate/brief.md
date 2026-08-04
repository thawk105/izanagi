# 段 1 brief — [T-244] D121 P5 (provider 注入・role 間 session 共有・未予約 token の拒否)

worktree: `/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t244-p5-injection-gate` (base 50db269)
job dir: `/work/1/SFC/tanab/dev-wave-jobs/t244-p5-injection-gate/`

## scope

D121 決定 (7) の前提条件 **P5 のみ**を実装する。P5 = 「provider 注入・role 間 session 共有・
未予約 token が正式経路で拒否される」。**新規 leaf 1 本 + 最小配線 + テスト**に閉じる。

- **scope 内**: 新規 leaf (pure evaluator + 薄い wrapper)、`p3_autonomous_workload_trial.py` の
  `run_trial` / `main` / `_provider_set` への最小配線、`claude_projected_provider.py` の
  session ledger 注入口、新規テスト、D96 の新 D (spool fragment)、変異 matrix
- **scope 外 (触らない)**: P1 面 (固定 5-bit IR・正準 emitter)、P3 面 (origin ledger の durable /
  CAS / crash replay)、cap-lift 結線 (`MAX_APPROVED_GENERATIONS` は 1 のまま。D121 §8 択一 2 未裁定)、
  `docs/phase3-main-experiment.md` (事前登録、§8.5)、予算値 (択一 1)、軸 (iii) (択一 3)

## 確定済みユーザー裁定・上位契約

- ユーザー指示 (本 wave): 「D121 P5 のみ。新規 leaf に閉じ、P1 と P3 の面には触らない」
- D121 決定 (7): P5 は**無条件の義務**であり現時点で未充足。D121 決定 (6): 設計は draft、実装ゼロ
- D96: 受理集合を変える改修は (1) 新しい D の記録 (2) 境界テストの同時更新を**同じ変更単位**で行う
- 絶対規律 2 / 3: 正しさゲートを緩める変異を採らない。拒否は fail-closed

## 不変条件

1. 既定 (token 非提示) の挙動は byte 単位で現行保存。既存テストの期待値を一切変更しない
2. 新設拒否はすべて fail-closed (判定不能 = 拒否)。診断文字列だけの差で受理集合を変えない
3. `MAX_APPROVED_GENERATIONS = 1` と `_validate_generation_budget` の受理集合は不変
4. 「P5 を満たした」と名乗るのは、実際に発火する検査が付いた要件だけ。process 内 single-use に
   留まる限界 (cross-process 偽造は閉じない = P3 の職掌) を D と leaf docstring に明記する
5. P1 / P3 の並行 wave と編集ファイルが衝突したら止めて報告する (rebase / force で迂回しない)

## 成果物の形

新規 leaf 1 本 + `orchestrator/tests/` の新規テスト 1 本 + 上記 2 ファイルへの最小配線。
docs は段 7 の spool fragment (worklog / decisions) のみ。insights は逐語を置く。

## 親の provisional 裁定 (攻撃対象。**D121 の P1〜P10 と衝突するため `(P1)` 採番を使わず `(PROV-n)` とする**)

- **(PROV-1)** 3 要件を 1 leaf にまとめる (要件ごとに leaf を割らない)
- **(PROV-2)** token は**新規 leaf 内の process-local single-use reservation** とし、durable ledger を
  作らない (P3 非侵襲)。issue は CLI `main()` だけが行う
- **(PROV-3)** token 非提示の run は現行どおり受理し、**formal token 提示時だけ**注入 3 seam
  (`providers` / `drive` / `preview`) を拒否する
- **(PROV-4)** role 間 session 共有は、4 role の provider が**共有する session ledger** を
  `_provider_set` で注入して拒否する (role ごとの既存 `_observed_session_ids` は残す)
- **(PROV-5)** formal consumer (`autonomous_trial_completeness.py`) は attestation の schema 整合だけを
  検査し、新 flag を作らない。「formal を要求する」判定は run-time 側に置く

## 純増検出力 (既存被覆の実測、base 50db269)

| 要件 | 既存被覆 | 本 wave の純増 |
|---|---|---|
| provider 注入 | `run_trial:1551` の `allow_pegasus_compute_transport and providers is not None` の 1 経路のみ (test_claude_transport.py 6 箇所が transport 側で触る) | transport flag と独立に、formal token 提示時の `providers` / `drive` / `preview` 注入を拒否 |
| role 間 session 共有 | **ゼロ**。`claude_projected_provider.py:177,295` の `_observed_session_ids` は instance 単位で、role 間は構造的に検出不能 | 4 role 横断の session_id 衝突を拒否 |
| 未予約 token | **ゼロ**。該当概念が存在しない (`reservation.py` は PBS walltime 用で無関係) | 未発行 / 二重使用 token を拒否 |

## 成果物影響 (DW-G05)

- provider 注入: 放置すると formal 8c 試行の certified 選択が caller 差し替えの role provider で
  生成されえ、材料レポートの role projection 帰属が検証不能になる
- role 間 session: 放置すると planner→coder が session 経由で漏れ、「LLM が独立に合成した」という
  段 4/5 の synthesisability 主張 (D39/D47) が無効化される
- 未予約 token: 放置すると `drive_iteration()` 直接反復の産物が試行台帳に載り、generation gate を
  経ない run が受理集合へ入る

## 既存の先例 (親が実測。プランはこれを出発点にすること)

- `orchestrator/campaign/build_admission.py` の `CoderBuildAuthority` は
  **「private argparse action だけが発行する process-local な不透明 token」**であり、
  `_ISSUED_AUTHORITY_NONCES` / `_CLAIMED_AUTHORITY_NONCES` で未発行・二重使用を拒否する。
  冒頭 docstring は**閉じていない境界 (in-process issuer 等) を正直に列挙する**。
  P5 の「未予約 token の拒否」はこの型の再利用が自然である
- `run_trial` は既に `coder_authority: CoderBuildAuthority | None` を受け、`do_build` 時に必須化する
- 識別子の二義化回避 (DW-O13 / D75): `reservation.py` は **PBS walltime 予約**、
  `session_ledger` は **s1_direct_comparison の CCBench session 台帳**、`*_admission` は既に
  build / artifact / materializer / transport の 4 種がある。新設名はこれらと衝突させない

## 並列分割方針

実装単位は 1 つ (leaf + テスト + 配線は相互依存)。段 3 と段 6 のみ 2 本並列。

## 環境

受入全走 = `python3 tools/run_tests.py` (ログインノードから計算ノードへ自動 dispatch)。
親のテスト実行 cwd は worktree root。login ノードで pytest を直接叩かない。
