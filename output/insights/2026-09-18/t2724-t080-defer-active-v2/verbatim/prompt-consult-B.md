単独段 dispatch: stage=consult; lane=sol; sandbox=read-only; parent=/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2724-t080-defer-active-v2

## レンズ B — 実効性・整合・費用 (両木で緑に到達するか、fixture は作れるか、受入で赤になる consumer は尽くしたか)

あなたは段 3 の敵対相談子である。段 2 の plan と親の段 1 brief の**両方**を攻撃する。plan を守らず、親の実測値とその一般化も検査対象とする。

## 必読事項の射影

次の絶対パスを読む。**この射影に挙げた file が読めなければ即停止**する。自分が推測して探した path が不在でも停止理由にしない。

- `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2724-t080-defer-active-v2/s1-brief.md` — 親の段 1 brief
- `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2724-t080-defer-active-v2/artifacts/dev-wave-t2724-t080-defer-active-v2/s2-plan.md` — 段 2 plan
- `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2724-t080-defer-active-v2/rulings-verbatim.md` — 確定済みユーザー裁定の逐語
- `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2724-t080-defer-active-v2/g-wave-failure-table.txt` — 45 node の nodeid と assertion 本文の集計
- `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2724-t080-defer-active-v2/chain-land-readme-sec3-5.md` — 並行 wave の §3 / §5 (test 切り離しの必須条件 (i)〜(v))
- `/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2724-t080-defer-active-v2/orchestrator/tests/test_s8b_oracle_driver.py` — `_git_visible_output_paths` / `_copy_git_visible_output` (780〜870)、`_T080SharedBases` 〜 `_build_t080_stub_free_e2e_repo` (880〜1500)、`_run` / `_run_with_real_manifest_gate` (2951〜3010)、`_never_issued_resolution` / `_fake_launch_validated` (grep)、`test_run_block_resolves_receipt_once_and_propagates_observation_to_wal_and_result` (3636 付近)、`test_run_block_rejects_receipt_epoch_drift_before_campaign_start_g4` (3677 付近)、`receipt_memo.patch_driver_resolver()` の直接呼出し (3345、3459、3738、4216、4246、5160、5240) だけ
- `/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2724-t080-defer-active-v2/orchestrator/tests/test_s8b_floor_campaign.py` — `_clone_committed_head_with_ccbench` 〜 `_remove_post_seal_floor_protocols_from_replay` (2291〜2350)、`test_real_seal_protocol_to_floor_official_core_e2e` (12072〜12200)、`_protocol_binding_public_preflight` (15600〜15660)、5 node (15790〜15850) だけ
- `/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2724-t080-defer-active-v2/orchestrator/tests/test_s8b_ratified_freeze.py` — fixture helper (109〜260)、`build_production_emitter_g1` (grep、1002 付近) とその使用 test 1 本だけ
- `/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2724-t080-defer-active-v2/orchestrator/tests/s8b_v2_freeze_fixture.py` — `_holdout_hit_text` (313〜)、`candidate_repository` (737〜) の docstring だけ
- `/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2724-t080-defer-active-v2/orchestrator/tests/conftest.py` — `RECEIPT_MEMO_CONSUMER_NODES` (712〜745)、`_prewarm_receipt_memo` と selected-consumer 条件 (880〜930) だけ
- `/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2724-t080-defer-active-v2/orchestrator/tests/test_real_repo_serialization.py` — `_RECEIPT_MEMO_CONSUMERS_GOLDEN` (503〜540)、consumer 導出と count pin (2840〜2920) だけ
- `/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2724-t080-defer-active-v2/orchestrator/tests/real_repo_receipt_memo.py` — 冒頭 docstring (1〜20) だけ
- `/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2724-t080-defer-active-v2/orchestrator/tests/growth_test_holds.py` — 185〜270、520〜550 だけ
- `/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2724-t080-defer-active-v2/orchestrator/tests/test_ccbench_spawn_sites.py` — 3370〜3395 だけ (driver の行番号 pin)
- `/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2724-t080-defer-active-v2/docs/dev-wave/operations.md` — `DW-O14`、`DW-O18` だけ
- `/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2724-t080-defer-active-v2/docs/phase3-8b-restart-runbook.md` — §1.1 (122〜146)、§2 (148〜160)、§6 (693〜697) だけ

repo root は `/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2724-t080-defer-active-v2` (chain 無し)。chain 有り木の現物は `git show 229982652:<path>` で読める。git 読取りは自由。親は修正前の chain 有り木 (本 branch + `229982652` の merge、scratch) で 6 file の対照焦点走を投入済み (結果は未着)。

**大きい file を全文 `cat` しない。** `grep -n` で位置を出し `sed -n` で 200 行以内ずつ読む。

## 攻撃対象 (この順で)

1. **正例 fixture の実現可能性。** plan は「T-080 発行済み合成 repo (`_build_t080_stub_free_e2e_repo`) の上に full emitter (`build_production_emitter_g1`) の G / A / X を積み、実 `load_ratified_freeze` → 実 `launch_validate` → 実 `verify_receipt` で active-valid を得る」を着地条件にする。両 fixture が要求する repo の性質 (ccbench submodule、known_axes / holdout の basis blob、closure path、`frozen_at_head`、calibration / protocol / selector 材料、official run_dir、`launch_certificate`) を現物で列挙し、**同じ 1 repo で両立しない要求**が無いか (例: T-080 の `_verify_ccbench_current_or_hold` と emitter の ccbench pin、`_copy_git_visible_output` の除外集合と v2 closure の必要 path、receipt の `migration_basis_commit` と G の親)。両立しないなら、着地条件 (A-3 の同等性を境界 test で確認) を満たす最小の代替 (predicate 単体 + driver e2e の分離で、何をどこまで実証できるか) を示し、「実証済み」と言えない範囲を明記する。構築費用の見積り (秒) と、受入 5 分上限 (test-time 規律) への影響。
2. **memo consumer の追随の正確さ。** plan の「34 関数 / 37 node → 8 関数 / 8 node」を、conftest `RECEIPT_MEMO_CONSUMER_NODES`、serialization golden、`test_real_repo_serialization.py:2853` の導出 (AST で `_run(` 呼出しを consumer と数える) から検算する。残る 8 が何か、`memo_receipt=False` の 2 node の扱い、prewarm の起動条件 (残存 consumer が選択された時だけ) の barrier test が新しい集合で通るか。`_run` の既定を `_never_issued_resolution()` に変えたとき、`_run` 経由で `_campaign_t080_value` が `never-issued` 側を通る test が「active-valid 側の epoch record を WAL に載せる契約」を失わないか (該当 test があれば名指し)。
3. **floor 5 node の切り離しの正確さ。** `_clone_committed_head_with_ccbench` (1 node) と `_protocol_binding_public_preflight` の直接 clone (4 node) の両経路に削除 helper を入れる形で、`HEAD^ == source_head` 等の exact assertion をどう保つか。削除集合 S が chain 無し木で空、chain 有り木で official 5 file のみになること (`git ls-tree 229982652` で検算)。新負例 `test_clean_scan_rejects_synthetic_chain_artifacts[official/candidate/both]` の合成 bytes が `clean_scan_digest` の走査対象に入る path (`_CHAIN_RECORD_PATTERNS` の allowlist と走査除外の関係) を現物で確認し、置く path を 1 つに定める。「無害な bytes なら通る」対照が本当に通るか (clean clone の HEAD で `clean_scan_digest` が他の理由で拒否しないか)。
4. **受入で赤になる consumer の網羅。** plan の表に無い consumer を探す: (a) `LaunchValidatedFreeze` / `ReverifiedFreeze` の直接構築 7 箇所以外 (`dataclasses.replace`、`_replace`、kwargs 展開)、(b) `verify_receipt` / `_resolve_t080_receipt` の call 回数・引数を pin する test (mock の `assert_called_once_with(root=...)` 形)、(c) driver の行番号 pin (`test_ccbench_spawn_sites.py` の 1788 行以外)、(d) `orchestrator/tests/` の inventory test (production dir を `glob` / `rglob` / AST 走査するもの) で `s8b_ratified_freeze.py` の dataclass field 数や driver の return 文を数えるもの、(e) `docs/` の check_docs literal pin (runbook §1.1 / §2 の文言を逐語で pin する test の有無)。
5. **P3' (親の追加問い) の費用対効果。** 初回 receipt 解決を launch 判定の後ろへ移して解決回数を 1 回 (+ campaign-start 前 1 回) にする代替は、plan の「初回維持 + 委譲付き再解決」より test の追随 (call_count pin、epoch drift test の side effect 列) が少ないか多いか。G wave の 407 秒 (receipt 解決 1 回、login node) を根拠に、run_block の gate 到達までの所要が plan 案と代替案でどう違うか概算する (走査回数・履歴検査回数)。
6. **両木の焦点走と受入の設計。** chain 有り scratch (本 branch + `229982652` merge) で緑になるべき node 集合と、それでも赤が残ると予測される node (例: growth hold 外で実 root を読む他の test、`test_s8c_preregistration_invariant` の非 held node) を列挙する。chain 有り木は受入全走の対象ではない (land は chain 無し main) が、G wave の後続 land のために「chain 有り木で全走したら何が残るか」の予測を 1 表にする。
7. **runbook 文案と fragment の整合。** 「A / X 後 = 設計上の期待、未実測」を書く形が runbook §6 の更新契約 (値の無い前方参照と placeholder を書かない) に抵触しないか。抵触するなら書き方を示す。worklog fragment で T-2776 を完了にできる条件。
8. **親の brief の誤り。** P1〜P5、変更面アンカー、稼働 wave 照合 (t2613 / t2627 と交差しない) の記述で、現物と食い違う点を挙げる。

## 禁止

- file を作成・編集しない。git の状態を変えない。pytest を走らせない (静的検査でよい。走らせていない結果を緑と書かない)。
- 規律 2 を緩める提案 (走査除外・hold・test の変更、検査の削除、skip flag / env による免除、既存 test の期待値の緩和) を代替案として出さない。
- gate・検査・台帳・tool の新設や一般化を提案しない。
- 三軸の値 (holdout の workload 定義) を出力に逐語で書かない。

## 出力形式

**出力は file に書かず、最終メッセージの本文に全文を書け。** 見出しはすべて `##` (H2)、最後の節は必ず `## 総括`。予算が尽きそうなら、その時点の結論を出力形式どおりに書いて終われ。

各所見は `B-<番号>` を付け、**must-fix / should / nit** に分類し、**放置時に成果物 (両木の緑・land 可否・受入の赤・oracle 到達) がどう変わるか**を 1 行で書く。示せない所見は nit とする。plan と brief の**どちら**への所見かを明記する。

節の順:

## 所見 (B-1 …)
## 正例 fixture の実現可能性と代替
## memo consumer と floor clone の検算
## P3' の費用対効果
## chain 有り木で残る赤の予測表
## brief と plan の食い違い
## 総括
