単独段 dispatch: stage=review; sandbox=read-only; parent=/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2724-t080-defer-active-v2

## レンズ B — 実効性・test 品質のレビュー (接続 fixture・4 経路の切り離し・登録簿追随・consumer 波及・両木の緑)

あなたは段 6 の敵対レビュー子である。実装 commit `7a763575f` (wave worktree `/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2724-t080-defer-active-v2`、基点 main `24ede1d11`、chain 無し) を、段 4 裁定の確定仕様と親の実測 log に対して攻撃する。Codex author の報告も検査対象とする。

## 必読事項の射影

次の絶対パスを読む。**この射影に挙げた file が読めなければ即停止**する。自分が推測して探した path が不在でも停止理由にしない。

- `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2724-t080-defer-active-v2/s4-adjudication.md` — 段 4 裁定 (確定仕様)
- `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2724-t080-defer-active-v2/artifacts/dev-wave-t2724-t080-defer-active-v2/s5-author-1.md` — Codex author の最終報告
- `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2724-t080-defer-active-v2/artifacts/dev-wave-t2724-t080-defer-active-v2/s3-b.md` — 段 3 レンズ B の所見 (B-1 接続 fixture の障害、B-2 literal 2 本、memo consumer 検算、floor 3 段 assertion、新負例の配置)
- `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2724-t080-defer-active-v2/focus-nochain-1.log` — 親の焦点走 (chain 無し木 7a763575f、7 file)
- `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2724-t080-defer-active-v2/focus-chain-1.log` — 親の焦点走 (chain 有り scratch `897224a9f` = 7a763575f + 229982652 の merge、7 file)
- `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2724-t080-defer-active-v2/focus-nochain-2.log` — 親の consumer 回帰 (chain 無し木)
- `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2724-t080-defer-active-v2/focus-base-failed-nodes.txt` — 修正前 chain 有り木の 45 赤 node (対照)
- `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2724-t080-defer-active-v2/g-wave-failure-table.txt` — 45 node の 4 経路と assertion 本文

差分は wave worktree で `git show 7a763575f` / `git diff 24ede1d11 7a763575f -- <path>` で読む (13 file)。現物は同 worktree の path を `grep -n` / `sed -n` で 200 行以内ずつ読む。**親が実行済みの分担**: patch の展開と commit、runbook の docs 編集 (未 commit、レビュー対象外)、修正前の対照走 (45 赤)。Codex author は pytest を走らせられない (sandbox の socket 拒否と growth-hold guard) ので、報告の「未実走」は怠慢ではない。

**大きい file を全文 `cat` しない。**

## 攻撃対象 (この順で)

1. **接続正例 `test_t080_active_v2_delegation_accepts_full_receipt` が実機構を通っているか。** fixture (stub-free T-080 repo → selector seed → protocol → C → G → A → X) が B-1 の障害 (既存 g1 / selector 証拠の複製、`history-mutated`、selector 祖先) を初期 commit 前に避けているか、`load_ratified_freeze` / `launch_validate` / `verify_receipt` を stub・monkeypatch していないか、`active-valid` の assertion が refusals 空まで要求しているか。親の log で緑か赤か、赤なら fixture のどの段で何が拒否されたかを log の assertion 本文から特定し、fix 指示を書く。
2. **負例群の実効性。** `test_t080_unactivated_chain_hit_is_invalid`、`test_t080_failed_launch_preserves_receipt_refusal`、`test_t080_active_v2_preserves_nonlayer2_receipt_refusal`、`test_t080_delegated_campaign_start_rechecks_receipt[changed|missing]`、`test_t080_delegated_campaign_start_rejects_late_hit`、`test_v1_gate_does_not_delegate_with_active_v2`、`test_layer2_delegation_rejects_*`、`test_delegated_scan_keeps_frozen_document_bindings[...]`、`test_launch_token_retains_immutable_scan_and_root` のそれぞれについて、拒否理由が exact で単一か、fixture が過剰決定 (他の gate が先に拒否) でないか、代役に落ちていないか。author が申告した `[missing]` の仕様不整合 (receipt 削除は再 launch の列挙拒否が epoch 比較より先に発火) を現物で判定し、期待値を緩めずに直す形 (実装側 / fixture 側のどちらが正しいか) を示す。
3. **4 経路の切り離しの正確さ (T-2776 の必須条件 (i)〜(v))。** S の宣言 (official namespace 全体 ∪ `V2_CANDIDATE_REL`)、`_copy_git_visible_output` の除外と ancestor 構成、copy 契約 test の差分集合検査、floor の 2 clone 経路 (`_clone_committed_head_with_ccbench` と `_protocol_binding_public_preflight`) の削除 helper と 3 段 assertion、`test_replay_clone_removes_only_declared_chain_artifacts`、新負例 `test_clean_scan_rejects_synthetic_chain_artifacts[official|candidate|both]` の配置 path と `conjunction_hits` 確認と無害 bytes 対照、`test_t080_draft_rejects_synthetic_hit_outside_replay_deletions`、g7 の exact 集合不変。chain 有り木で 45 node が全部緑になったか (`focus-chain-1.log` と `focus-base-failed-nodes.txt` の照合)、chain 無し木で退行が無いか。
4. **memo consumer 登録簿の追随。** `RECEIPT_MEMO_CONSUMER_NODES` (conftest)、`_RECEIPT_MEMO_CONSUMERS_GOLDEN` / opt-out golden、`:2853` 系の導出、34/37 → 8/8 pin、B-2 の literal 2 本、`test_run_tests_task_run.py` の選択検査への波及、prewarm の起動条件 (残存 consumer 選択時だけ) の barrier test。log に赤があれば帰属。
5. **consumer 波及と pin。** `LaunchValidatedFreeze` / `ReverifiedFreeze` の直接 constructor 7 箇所 + `dataclasses.replace` 派生、`test_ccbench_spawn_sites.py` の行番号 pin (1788→1803 が同じ sink か)、`test_real_repo_serialization.py` の resource 分類 golden (新 test の実 root 読取り分類)、`test_frozen_artifacts` 等の凍結 pin に影響が無いか、`focus-nochain-2.log` の赤の帰属。
6. **test 時間。** 新 fixture (接続正例、clone 負例 3 ケース) の所要を log の duration から読み、受入 5 分上限 (全体) への寄与を見積もる。過大なら共有 base / parametrize の縮約を提案 (検出力は落とさない)。
7. **author 報告と実体の不一致。** 報告の「実装した」項目が差分に無い、差分にあるが報告に無い、nodeid の名前違い、を列挙する。

## 親の一次判定 (攻撃対象。誤りなら指摘せよ)

焦点走の実測: chain 無し木 = 1086 passed / 9 failed / 11 skipped、chain 有り木 = 1085 passed / 10 failed / 11 skipped。修正前 45 赤のうち 44 は chain 有り木で緑になり、残る 1 は `test_real_seal_protocol_to_floor_official_core_e2e` (`clean_calls == [expected_clean_digest]*2` の不一致 — clone に残る G の世代文書 `output/s8b-freeze/holdout_freeze.v2.g1.json` を production の `clean_scan_digest` は chain record として path + sha256 を digest に含めるが、test 側の `expected_clean_digest` は `frozen_paths` だけを allowlist に入れるため)。両木共通の新規赤 9 = (a) 8 本の接続系 test が `_build_t080_active_v2_repo` → `build_production_emitter_g1` の build seam (`test_s8b_ratified_freeze.py:520` `compiler_input_rel = "fixture.txt"`) で `external/ccbench/fixture.txt` を実 ccbench clone に探して `FileNotFoundError` (接続 fixture は `_make_fixed_ccbench` を使わないので固定 file が無い)、(b) 既存 `test_v2_floor_disk_swap_after_launch_uses_same_validated_object` が `refused` — campaign-start 前の `launch_validate` 再実行が floor artifact を disk から再読して swap を観測するため、E3b / A3-6 (launch 済みの同一 object だけを使い disk を再読しない) の契約と衝突。親の fix 方針: (b) は再 launch をやめ、artifact を再読しない**走査だけの再検査** (`s8b_ratified_freeze` に token を受ける helper で HEAD / root 一致 → exempt 再導出 → 前後の列挙 digest 一致 → `search_repository` → 陽性対照 → per-holdout `conjunction_hits` が token の `search_report` と完全一致) を campaign-start 前に置き、通れば gate 時 token で委譲付き再解決 + epoch 比較する。(a) は build seam の `compiler_input_rel` を接続 fixture から指定可能にし、実 ccbench 内の実在 file を渡す (test 側のみ)。e2e の残る 1 赤は、test 側の `expected_clean_digest` が clone に実在する chain record (`_CHAIN_RECORD_PATTERNS` に一致する path とその sha256) を allowlist 項に含める形で production の digest 定義 (D2077) に追随する。これらの穴 (期待値の追随が検出力を落とさないか、接続 fixture の他の障害) を指摘せよ。

## 禁止

- file を作成・編集しない。git の状態を変えない。pytest を走らせない (親の log を根拠にし、走らせていない結果を緑と書かない)。
- 規律 2 を緩める提案 (走査除外・hold・test の緩和、検査の削除、skip flag / env 免除、既存 test の期待値の変更) を出さない。
- gate・検査・台帳・tool の新設や一般化を提案しない。
- 三軸の値 (holdout の workload 定義) を出力に逐語で書かない。

## 出力形式

**出力は file に書かず、最終メッセージの本文に全文を書け。** 見出しはすべて `##` (H2)、最後の節は必ず `## 総括`。予算が尽きそうなら、その時点の結論を出力形式どおりに書いて終われ。

各所見は `RB-<番号>` を付け、**must-fix / should / nit** に分類し、**放置時に成果物 (両木の緑・land 可否・受入の赤・oracle 到達・検出力) がどう変わるか**を 1 行で書く。示せない所見は nit。fix 指示は file:関数 粒度で、変更してよい範囲と変更してはならない範囲 (既存 test の期待値) を分けて書く。最後に **GO / NO-GO** を 1 語で書く。

節の順:

## 所見 (RB-1 …)
## 接続正例の判定
## 45 node の解消表 (chain 有り木、解消 / 残存 / 新規)
## 焦点走の赤の帰属と fix 指示
## 報告と実体の不一致
## 総括
