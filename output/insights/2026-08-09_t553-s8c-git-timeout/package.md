# [T-553] s8c 事前登録の git wall-clock gate — 裁定パッケージ

- wave: `dev-wave-red-suite-20260809` (branch `worktree-dev-wave-red-suite-20260809`)
- base: main `bcda1c02`
- 起票: 2026-08-09、dev-wave-red-suite-20260809 の親 (Claude)
- 状態: **実装差分ゼロで終端。R1 の裁定が下りるまで [T-553] は開いたまま。**
- 依頼 (逐語): 「今、テストやチェックがコケる問題がある。すべて直してください。
  並行セッションの活動を閲覧し、並行重複した仕事をしないでください」

## 1. main `bcda1c02` の赤は 2 つだけである (全数調査)

| # | 赤 | 実測 | 処置 |
|---|---|---|---|
| 1 | `tools/check_ai_provenance.py` rc=1 (1947 件中 23 新規違反) | 形式違反 22 + `2c192953` の Codex author 欠落 1 | **並行 wave t682 (登録) / t139 (land 関門) の所有。本 wave は不接触** |
| 2 | 受入全走 `1 failed / 7569 passed / 20 skipped` (request `896686`、1463 秒) | `test_s8c_preregistration_invariant.py::test_candidate_freeze_matches_contract_and_generation_chain` が `PreregistrationError: git-timeout` | **本 wave の scope = [T-553]。実装せず裁定へ返す** |

緑を実測した検査 (すべて本 worktree、main `bcda1c02`):
`check_docs.py` / `check_codex_agents.py` / `check_wave_startup.py --external-handoff` /
`ruleops.py check` (candidate 0、structurally_valid) /
`task_run_check.py static-check` / `task_run_check.py docs-check`。
`tools/dev_waves/cli.py` の supervisor が束ねる 4 検査 (codex-agents / docs / orchestrator /
provenance) は、いずれも上記または #2 の全走で個別に実測済みである。
`check_workflow_models.py` は対象 directory 不在で非該当。
並行 wave t657 が抱える floor 由来の赤は、再発行 commit `8780332c` が main 未着のため main では発火しない。

## 2. #2 は既知の族で、これが 6 回目である

`docs/failures.md` の F57。**同一 nodeid の再発は本走行を含めて 6 回**
([T-459] 2026-08-06 / [T-522] 2026-08-06 / [T-639] 2026-08-08 / [T-656] 2026-08-08 /
[T-664] 2026-08-08 / 本走行 2026-08-09)。
[T-648] 2026-08-09 は同族だが nodeid が異なる (`test_ruleops.py`、producer は同じ git)。

毎回、単独再走は緑である。本走行の単独再走は **8 passed / 40.48 秒 / rc=0** (request `896706`)。

## 3. 機序 (実測)

- `_commit_graph` (`s8c_preregistration.py:1063`) は `rev-list` で**全履歴**を取る。
- `_batch_oids` (`:1102`) はその「全 commit × path」を**単一の `git cat-file --batch-check`** へ入れる。
- 現在 `git rev-list --count HEAD` = **2286**、generation は g1 のみ → path 3 本 →
  **約 6,861 要求 / 呼び出し**。
- `_git` (`:880`) の上限は `GIT_TIMEOUT_SECONDS = 15.0` の**固定値**で、履歴長に依らない。
- 無負荷参考値 (login node、warm、単独): 2286 要求・1 path で **0.690 秒**。
  production CLI `check` 全体で **3.700 秒**。

**この 2 つの参考値から負荷下や将来規模を外挿してはならない** — 段 3 レンズ A が
「warm・login node・単一 path の線形外挿」として refuted した。real なのは
(i) 全走負荷下で 15 秒を超えたという直接観測、(ii) cardinality が `commits × paths` であること、
の 2 点だけである。

## 4. 評価した 5 案と、両レンズの判定

段 2 プラン (codex sol/max)、段 3 レンズ A (sol/max・有効性)、レンズ B (luna/max・正しさ境界)、
段 3v2 レンズ C (sol/max・規律 2)、レンズ D (luna/max・依頼達成と終端の正直さ) による。
逐語は本 dir の `s2-plan.md` / `s3-lensA.md` / `s3-lensB.md` / `s3v2-lensC.md` / `s3v2-lensD.md`。

| 案 | 内容 | 判定 | 決め手 |
|---|---|---|---|
| 段 2 案 | git 呼び出しを上限つき chunk へ分割し、旧 invocation ごとの 15 秒は据え置く | **棄却** | プラン自身が「赤は閉じない」と自認。総締切が変わらない以上、分割は赤に無関係。加えてレンズ B が chunk 境界で `cat-file-truncated` / `cat-file-size` / `cat-file-extra` の reason code が入れ替わる経路を real と判定 |
| B | `validate_condition_freeze_at` に timeout 引数を足し、テストだけ 180 秒を渡す | **棄却** | レンズ A が Critical。`timeout=10**9` を止めるものが無い public な迂回口になり、かつ「実 repo で production 既定の 15 秒が効くか」を断言する唯一のテストが無効化される |
| C | 要求数から内部算出する上限付き比例予算 | **裁定待ち (R1)** | レンズ A の第 1 推奨。ただし wall-clock 受理集合を明確に広げ、かつ §5 の write path に到達する |
| E | production 不変のまま、テストが `git-timeout` に限って有限回再試行 | **棄却** | レンズ C が**規律 2 違反**と判定。「production 既定での一発成功」という現に成立している断言を「有限回中一成功」へ緩める。再試行で OS/git cache が温まるため、親が主張した「恒常的劣化なら全試行が落ちる」分界線が成立しない |
| F | 実 repo を読む重い git テスト群を同一 xdist group へ統合し、既知の同時競合を除く | **未評価** | レンズ C が代替行動として提案。assert も production も timeout も触らない。ただし本 wave では敵対レビューも実測もしていない |

## 5. 親 brief の誤りを 1 件訂正する (レンズ B の B-08、blocker)

段 1 brief v1 は「DW-O09 / DW-O10 は成立しない (出力 producer に触れない)」と書いたが**誤りである**。
`prepare_revision` は `s8c_preregistration.py:1688` で `validate_condition_freeze_at` を呼び、
その成功後に `:1713-1725` で `gN.json` を exclusive-create して書く。
したがって **validator の受理集合に触る案 (C) は、凍結成果物の producer write path に到達する** —
旧 `git-timeout` が新実装で通れば、旧来作られなかった generation が作られうる。
案 C を裁定する際は DW-O09 / DW-O10 の pin 閉包・producer 棚卸しが必要である。

## 6. 要裁定 (R1〜R3)

### R1 — 固定 15 秒の wall-clock gate を、作業量比例の上限付き予算へ変えるか (本体)

現状は `GIT_TIMEOUT_SECONDS = 15.0` の固定値である。案 C はこれを要求数 `R` から内部算出する
予算 `B(R)` へ変え、`MAX_BATCH_REQUESTS` 相当点で絶対 cap を置く。

- **これは gate の緩和である。** `B(R) > 15` の領域では、従来 `git-timeout` で reject された実行が
  成功する。レンズ A・B とも「無裁定で入れてはならない」と判定した。
- **同時に、現状の固定値は運用上不整合でもある。** モジュールは `MAX_COMMITS = 10_000` /
  `MAX_BATCH_REQUESTS = 50_000` を受理可能と宣言しているのに、15 秒で完走する契約はどこにもない。
  現に 6,861 要求で 6 回落ちている。
- **§5 のとおり凍結成果物の生成条件が変わりうる。**

**選択肢:**
- **(a) 採る (親の推奨)** — レンズ A が挙げた 5 条件を必須要件とする:
  ①予算は caller 引数にせず実要求数から内部で一意に算出する、
  ②旧 logical invocation 全体に deadline を 1 つ置く、
  ③`MAX_BATCH_REQUESTS` 相当点で絶対時間 cap を設ける、
  ④rate は warm 0.690 秒の線形外挿で決めず、**cold / contended な計算ノード条件で実測してから**裁定する、
  ⑤invariant テストは引数を渡さず production と同じ計算式を通す。
  加えて §5 により DW-O09 / DW-O10 を成立として扱う。
- (b) 採らない — 固定 15 秒を絶対維持する。#2 の赤は構造的に残り、
  受入全走は今後も約 20% の頻度で 1 failed になる。
- (c) 案 F (xdist group 統合) を先に試し、それでも再発するなら R1 へ戻る。
  production を一切触らずに済む可能性があるが、有効性は未実測である。

### R2 — 「受理集合不変」に `git-timeout` を含めるか

レンズ B の B-01 と総括が親へ返した択一。`git-timeout` を
**意味論的な reject** (入力の性質による拒否) と見るなら、それを通す変更はすべて受理集合の変更であり
R1 は必ず裁定事項になる。**環境依存の false reject** と見るなら、R1 は「正しさの変更」ではなく
「可用性の修復」として扱える。この区別は今後の同型案件すべてに効く。

- **(a) 意味論的 reject として扱う (親の推奨)** — fail-closed 側に倒す。R1 は裁定事項のまま。
- (b) 環境依存の false reject として扱う — R1 の敷居が下がるが、
  「負荷で落ちた検査は無視してよい」という前例を作る危険がある。

### R3 — 案 F を本 wave の外で起票するか

レンズ C の代替行動 3。s8c candidate / ruleops / その他の実 repo 読み取りテストを
同一 xdist group へ入れ、既知の同時 git 競合を除く。[T-639] は実際に
ruleops と s8c が**同一走行で同時に**落ちたことを記録している。

- **(a) 起票する (親の推奨)** — production も assert も触らないため、R1 と独立に進められる。
- (b) 起票しない — R1 の裁定に一本化する。

## 7. 本 wave が実装しなかった理由 (DW-S04)

設計択一が割れ (5 案中 3 案が棄却、本命 C は受理集合と凍結 producer に到達)、
親 brief の前提 1 件が段 3 で refuted された (§5)。
`DW-STOP` の「承認済み裁定の前提を覆す未見の新事実」に該当するため、親が不採用にせず
ユーザー再裁定へ戻す。実装差分ゼロで `4→7→8→9` を通る。

## 8. 留保 (レンズ D の必須留保)

- 段 8c の**発効判定は本 wave で 1 mm も改善していない**。負荷時の `freeze_reason_code="git-timeout"` は残る。
- **単独再走の緑は全走条件下の証拠ではない。** 40.48 秒の単独走行は 48 worker 競合を再現していない。
- **provenance の 23 件は残っている。** 所有は t682 / t139 だが、`DW-O17` の
  full-history 監査は本 wave の commit でも rc=1 のままである
  (本 wave の commit が**新規違反を 1 件も増やさない**ことは別途確認する)。
- 段 2・段 3 の子はいずれも pytest を実行していない。静的レビューのみである。
