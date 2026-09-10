# 段 1 brief — dev-wave-red-suite-20260809

base main `bcda1c02` / worktree `dev-wave-red-suite-20260809` / branch `worktree-dev-wave-red-suite-20260809`

## 依頼と、赤の全数調査 (親の前提実測、2026-08-09)

依頼 = 「今、テストやチェックがコケる問題がある。すべて直してください。並行セッションの活動を
閲覧し、並行重複した仕事をしないでください」。main `bcda1c02` の赤は**ちょうど 2 つ**である。

| # | 赤 | 実測 | 所有 |
|---|---|---|---|
| 1 | `tools/check_ai_provenance.py` rc=1 (1947 件中 23 新規違反) | 形式違反 22 + `2c192953` の Codex author 欠落 1 | **並行 wave t682 (登録) + t139 (land 関門)。本 wave は触らない** |
| 2 | 受入全走 `1 failed / 7569 passed / 20 skipped` (request `896686`、1463 秒) | `test_s8c_preregistration_invariant.py::test_candidate_freeze_matches_contract_and_generation_chain` が `PreregistrationError: git-timeout` | **無所有。本 wave の scope** |

緑を実測した検査: `check_docs.py` / `check_codex_agents.py` / `check_wave_startup.py` /
`ruleops.py check` (candidate 0・structurally_valid)。`check_workflow_models.py` は対象 dir 不在で
非該当。t657 wave が抱える floor 由来の赤は再発行 commit `8780332c` が main 未着のため main では発火しない。

## scope

**[T-553] (P2・起票済み・無所有) を実装して #2 を閉じる。** #1 には触れない。

## 確定済み裁定と一次資料

- [T-553] 起票文 (`docs/archive/worklog-phase3-0806-248.md:360`) =
  「timeout 値の個別延長ではなく『全走負荷下の git 呼び出し』を**族として**扱う必要がある」。
- F57 (`docs/failures.md:1349`) の恒久対応方針 = 「**production wall-clock gate を緩めず**
  test fixture を harden する」。[T-190] の失敗 artifact 保存は launcher 族の話。
- 先例 [T-327] は同型 (`git add -A` の 30 秒 timeout) を session fixture 化 + test 側 180 秒で塞いだ。
  その**直後に別の git 呼び出し (`_batch_oids`) で再発**したのが [T-553] の起票理由。
- 本テストの再発は台帳既載で **6 回**: 2026-08-06 [T-522] / 08-08 [T-639] / 08-08 [T-656] /
  08-08 [T-664] / (08-09 [T-648] は同族の `ruleops` 側) / 本走行。族一般化の独立 2 例要件 (DW-G03) は充足済み。

## 前提実測 (親、本 worktree)

- 単独再走は緑 = **8 passed / 40.48 秒 / rc=0** (request `896706`)。負荷なしでは再現しない。
- 規模: `git rev-list --count HEAD` = **2286**。`condition-freeze` の generation は **g1 のみ** →
  `_batch_oids` の path は 3 本 → 1 回の `cat-file --batch-check` に **約 6,861 要求**。
- 素の所要 (login node、warm、単独): 2286 要求 1 path で **0.690 秒** → 3 path 換算で約 2 秒。
  production の `GIT_TIMEOUT_SECONDS = 15.0` に対し余裕は約 7.5 倍。
- production CLI `python3 -m campaign.s8c_preregistration check --repo-root ..` 全体で 3.700 秒。
- **構造的欠陥**: `_commit_graph` は `rev-list` で全履歴を取り、`_batch_oids` はその
  「全 commit × path」を**単一の git 呼び出し**へ入れる。作業量は履歴長に比例して増えるのに、
  上限は履歴長に依らない固定 15 秒である。モジュール自身が宣言する規模上限
  (`MAX_COMMITS = 10_000` / `MAX_BATCH_REQUESTS = 50_000`) は、15 秒では原理的に捌けない
  作業量を許容している。**guard が自己矛盾している。**
  現在 2286 commit で余裕 7.5 倍。10,000 commit では約 9 秒となり余裕 1.7 倍で、負荷なしでも危うい。

## 既存被覆と純増検出力 (DW-S01 / [T-317] 裁定「書く前に既存被覆を検索する」)

`orchestrator/tests/test_s8c_preregistration_core.py` は 4 つの guard を個別に被覆済み —
`git-timeout` (:984)、`git-input-limit` (:997)、`git-output-limit` (:1011)、
`batch-request-limit` (:1024、`MAX_BATCH_REQUESTS` を monkeypatch)。
**純増検出力**は次の 3 つだけで、既存テストはどれも発火しない。
(a) 分割実行と単一実行の**結果同一性**、(b) 分割後も**集計上限**(総要求数・総出力 bytes) が
分割前と同じ入力集合で発火すること、(c) 分割によって**総 wall-clock 上限が失われていない**こと。

## 不変条件

1. `validate_condition_freeze_at` の**受理集合を変えない**。今日 reject される入力は今日どおり
   reject し、reason code も変えない。
2. **production の wall-clock gate を緩めない** (F57 の明示方針)。per-call 15 秒を延ばさない。
3. 検査を弱める方向の変異を採らない (規律 2)。テスト側で履歴範囲を縮めて逃げる案は不採用。
4. 凍結成果物 (`output/s8c-preregistration/condition-freeze/*.json`) の bytes を変えない。
   本 wave は読み取り経路だけを触る (DW-O09 は成立せず — 出力 producer に触れないため)。
5. 実装面は Codex `role=author` が書く。親は直接編集しない。

## 親の provisional 裁定 (いずれも攻撃対象)

- **(P1)** 採る形は「`_batch_oids` / `_batch_blob_bytes` の git 呼び出しを**上限つき chunk へ分割**し、
  各 chunk に既存の per-call 15 秒を掛ける」。timeout 定数は上げない。
- **(P2)** (P1) の素朴な実装は**総時間上限を N×15 秒へ膨らませる**回帰である
  (50,000 要求 / chunk 2,000 = 25 chunk → 375 秒)。したがって
  **operation 全体の monotonic な締切予算**を併せて導入し、総 wall-clock を分割前と同等に縛る。
  この予算値は攻撃対象 — 「分割前と同等」を 15 秒とするか、履歴長に比例させるかは択一。
- **(P3)** `MAX_GIT_OUTPUT_BYTES` は per-call 判定のままだと分割で緩む。**chunk 横断の累積**で判定する。
- **(P4)** chunk 幅は定数 (例 2,000 要求) とし、環境変数や引数で外から変えられるようにしない。
- **(P5)** 同じ O(履歴) 単一呼び出しである `_commit_graph` (`rev-list`) と
  `_history_namespace_paths` (`log --name-only`) は、観測された producer ではないので**本 wave では変えない**
  (DW-G03: 族一般化は独立 2 例で許すが、この 2 つはまだ 0 例)。所見としてだけ残す。

## 成果物影響 (DW-G05)

放置した場合: `validate_condition_freeze_at` は段 8c 事前登録の**発効判定の中核**である。
履歴が伸びるほど timeout 確率が上がり、発効判定が `PreregistrationError` で fail-closed する。
すなわち「条件を満たしているのに発効しない」= 段 8c 正式系列の**発効可否そのものが履歴長に依存する**。
受入全走も再発のたびに 1 件赤となり、land 前受入の再走コスト (1 走 20〜25 分) が積み上がる。

## 段の選択

軽量版にしない。理由 = 資源 guard (timeout / 出力上限 / 要求上限) という**正しさ防壁に触り**、
(P2)(P3) のとおり**受理集合が変わりうる** (DW-C00)。段 2 プラン + 段 3 敵対 2 レンズ +
段 6 レビュー 2 本を立てる。実装は Codex `role=author` 1 単位 (production + テストは同一 module 族のため分割しない)。

## 受入・実測環境

Pegasus。テストは `tools/run_tests.py` (dispatch → 計算ノード、48 worker)。
無負荷 baseline は login node。受入全走は lease `claim` が `acquired` のときだけ投入する。
