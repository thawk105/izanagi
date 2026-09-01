## 前提の確認

- **所見:** 必読 4 点と関連 consumer を読めた。コード変更・probe・pytest・official 実走は行っておらず、緑は主張しない。
- **根拠:** HEAD `08a17b3b3271dc6e0db575a7c15afbbbb91f6328`。共有 admission root は `/work/1/SFC/tanab/izanagi/.git/izanagi/s8b-holdout-admission-v1/`。現物は旧 `claims=36`、旧 `consumed=228`、現行 `measurement-generation-claims=24`、現行 `measurement-generation-consumed=192`、`ledger.jsonl=60` 行、`attempt-ledger.jsonl=420` 行。
- **放置したとき:** 本回答は静的検査結果であり、投入時点の TOCTOU や書込み成功までは保証しない。
- **提案:** G-A/G-B の最終記録も「実走済み」と「静的に衝突なし」を分ける。

## must-fix 候補

1. **G-B を「official が claim できる」と判定する設計は広すぎる。**

   - **所見:** 段 2 の「予定 claim path が不存在なら緑」「実際の衝突述語は O_EXCL 失敗だけ」は不正確である。read-only probe が証明できるのは、共有 lock を保持した一時点での「予定 identity に既存衝突がなく、既存証拠が構文上整合する」まで。
   - **根拠:** fresh reservation は resume marker 全件検査も行う（[s8b_holdout_admission.py:1612](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1942-floor-gate-recheck/orchestrator/campaign/s8b_holdout_admission.py:1612)）、12 claim を順次 `O_EXCL` 作成する（[同:1636](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1942-floor-gate-recheck/orchestrator/campaign/s8b_holdout_admission.py:1636)）、その後 ledger 全体を検証して追記する（[同:1742](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1942-floor-gate-recheck/orchestrator/campaign/s8b_holdout_admission.py:1742)）。書込みは collision 以外の任意の `OSError` でも拒否される（[同:1094](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1942-floor-gate-recheck/orchestrator/campaign/s8b_holdout_admission.py:1094)）。計画の該当箇所は [plan.md:81](</work/1/SFC/tanab/dev-wave-jobs/dev-wave-t1942-floor-gate-recheck/plan.md:81>)。
   - **放置したとき:** G-B 緑でも、権限・容量・exclusive lock・ledger 異常・lock 解放後の競合により実投入は拒否され、先行して作られた一部 claim だけが残り得る。
   - **提案:** verdict を `identity-conflict-free-at-<time>` に狭める。root/子 directory/lock の型・owner・mode、全 resume marker、main ledger、候補 12 claim path、候補 120 attempt pathを検査し、投入直前に同じ検査を再実行する。実際の claim 成功は production reservation のみが確定できると明記する。

2. **G-B は既存 `measurement-generation-consumed/` の全件整合検査を欠いている。**

   - **所見:** 候補 120 path の不存在だけでは、最初の planned attempt が通るか判定できない。
   - **根拠:** `consume_attempt_ticket()` は対象 path だけでなく、現行 generation の consumed directory 全体を走査し、各 marker を claim・main ledger・attempt ledger と再照合する（[s8b_holdout_admission.py:4827](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1942-floor-gate-recheck/orchestrator/campaign/s8b_holdout_admission.py:4827)、[同:4847](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1942-floor-gate-recheck/orchestrator/campaign/s8b_holdout_admission.py:4847)、[同:4877](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1942-floor-gate-recheck/orchestrator/campaign/s8b_holdout_admission.py:4877)）。[plan.md:84](</work/1/SFC/tanab/dev-wave-jobs/dev-wave-t1942-floor-gate-recheck/plan.md:84>) は候補 path を確認するが、既存 consumed 192 件の双方向整合を明記していない。
   - **放置したとき:** claim 12 件は取得できても、最初の attempt 消費で既存 marker の破損により停止し、受理集合が空になる。
   - **提案:** 現行 consumed 192 件を canonical path、claim、main-ledger、attempt-ledger と全件照合する。unsafe entry、孤立 marker、孤立 ledger row、duplicate identity を赤にする。

3. **attempt registry を G-B の予算根拠に使ってはならない。**

   - **所見:** 「実 pilot の登録簿がないので official 枠は 0 から始まる」は、結論ではなく不要な概念であり、根拠として誤っている。
   - **根拠:** fresh floor reservation は旧 effect-key claim を明示的に無視し（[s8b_holdout_admission.py:1618](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1942-floor-gate-recheck/orchestrator/campaign/s8b_holdout_admission.py:1618)）、generation-scoped claim だけを作る。registry は scheduler recovery が retry を開く場合だけ読む（[同:4960](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1942-floor-gate-recheck/orchestrator/campaign/s8b_holdout_admission.py:4960)、[同:5173](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1942-floor-gate-recheck/orchestrator/campaign/s8b_holdout_admission.py:5173)）。budget 10 もその recovery replay 内だけで検査される（[同:5195](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1942-floor-gate-recheck/orchestrator/campaign/s8b_holdout_admission.py:5195)）。さらに現物 fixture は `floor-attempt-registries/<freeze>/<protocol>/registry.jsonl` だが、現行 consumer の canonical path は `floor-attempt-registries/<freeze>/registry.jsonl`（[s8b_attempt_profile.py:378](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1942-floor-gate-recheck/orchestrator/campaign/s8b_attempt_profile.py:378)）。
   - **放置したとき:** 無関係な fixture registry の有無によって official の可否を誤判定する。
   - **提案:** G-B から「registry budget が 0」を削除する。planned claim の権威は generation claim、planned attempt の権威は generation-consumed marker と ledger、registry は recovery retry 限定と記録する。`transactions/` は R33 n-pilot 専用で floor claim 判定には使わない。

4. **G-A より先に staged/default transport を確定すべきである。**

   - **所見:** 現計画の G-A は actual collector→issuer を通るため leaf-only ではないが、どちらの transport を測るか未固定で、production official 経路の測定とはまだ言えない。
   - **根拠:** production core は `fetchcontent_base_dir` をそのまま `build_cells()` に渡す（[s8b_floor_campaign.py:7415](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1942-floor-gate-recheck/orchestrator/campaign/s8b_floor_campaign.py:7415)）。現行 job script は staged base を無条件指定する（[floor_campaign.sh:1226](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1942-floor-gate-recheck/tools/pegasus/floor_campaign.sh:1226)）一方、official wrapper はその非既定 seam を拒否する（[s8b_floor_campaign.py:6990](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1942-floor-gate-recheck/orchestrator/campaign/s8b_floor_campaign.py:6990)）。計画順は G-A の後に transport 衝突解決を置いている（[plan.md:94](</work/1/SFC/tanab/dev-wave-jobs/dev-wave-t1942-floor-gate-recheck/plan.md:94>)）。
   - **放置したとき:** default probe の緑は現行 staged job を測らず、staged probe の緑は refreeze-eligible official 経路を測らない。
   - **提案:** transport 裁定を G-A より前へ移す。必要なら「staged compiler regression」と「予定 official default transport」を別 probe・別 verdict にする。

5. **G-A の one-cell 緑を 12-cell readiness へ一般化してはならない。**

   - **所見:** `sort_best` 1 セルは既知の masstree 31 件と dependency-prefix 7 件を通す良い回帰 probe だが、他構成の compiler-input 集合が同一であることは証明しない。
   - **根拠:** 計画は 1 cell のみ（[plan.md:40](</work/1/SFC/tanab/dev-wave-jobs/dev-wave-t1942-floor-gate-recheck/plan.md:40>)）。現行 12 セルは `rr20`/`rr80` × `backoff_fixed_best, ident_all, p2_2_flag_opt, sort_best, stock_common, system_gate`。各セルは個別に build・receipt 発行される（[s8b_floor_campaign.py:4128](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1942-floor-gate-recheck/orchestrator/campaign/s8b_floor_campaign.py:4128)）。
   - **放置したとき:** 未観測構成だけ別の一時 root を参照すると、G-A 緑後も full official build が claim 前に停止する。
   - **提案:** G-A の主張を「既知 38-path regression が解消」に狭めるか、12 セルを build する。少なくとも構成ごとの build identity／manifest が同一になることを機械的に示してから重複を省く。

6. **read-heavy の「保守側と確認済み」は狭める必要がある。**

   - **所見:** 「read-heavy を一度も測っていない」は誤りだが、「0.030 の保守性を確認済み」も無限定には成立しない。
   - **根拠:** linux-baremetal rr95 は within 0.19%、fresh between 0.11%（[JSON:13](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1942-floor-gate-recheck/output/env/linux-baremetal/calibration/between_run_noise_t48_skew0p9_rr95_rmw0.json:13)）。Pegasus rr95 も within 1.00%、between 0.22%（[JSON:14](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1942-floor-gate-recheck/output/env/pegasus/calibration/between_run_noise_t48_skew0p9_rr95_rmw0.json:14)）。しかし両成果物は cold-boot・温度ドリフトを含まない下限と明記し、`s8a_trigger_sweep.py` も genuine-between 未較正とする（[s8a_trigger_sweep.py:44](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1942-floor-gate-recheck/orchestrator/campaign/s8a_trigger_sweep.py:44)）。
   - **放置したとき:** 成果物が read-heavy の genuine between/block floor まで較正済みと誉張し、現行 official 測定の科学的価値を取り違える。
   - **提案:** 「rr95 の fresh within/between は測定済みで、観測値は 0.030 未満。ただし genuine cross-campaign/between-block floor は未較正」と書く。

7. **D926 の submission confirmation と D1161 の人間 budget approval を別名・別段として固定すべきである。**

   - **所見:** plan 自体は budget approval 文書を AI が完成させる設計ではない。ただし親の「AI が起草→ユーザー承認」は、AI が canonical approval を完成させる意味に拡張してはならない。
   - **根拠:** budget approval の唯一の production consumer は `build_v2_g1_candidate()`（[s8b_holdout_freeze.py:2014](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1942-floor-gate-recheck/orchestrator/campaign/s8b_holdout_freeze.py:2014)）。approval pin を先に要求し（[同:2018](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1942-floor-gate-recheck/orchestrator/campaign/s8b_holdout_freeze.py:2018)）、その後 official result を読む（[同:2047](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1942-floor-gate-recheck/orchestrator/campaign/s8b_holdout_freeze.py:2047)）。既存 tool が AI に許すのは `draft-not-an-approval` skeleton だけで（[s8b_budget_approval_preflight.py:157](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1942-floor-gate-recheck/tools/s8b_budget_approval_preflight.py:157)）、完成 candidate は read-only 検証のみ（[同:184](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1942-floor-gate-recheck/tools/s8b_budget_approval_preflight.py:184)）。
   - **放置したとき:** AI が `approver`・予算値・日時を埋めた canonical JSON と pin を作り、D1161 の人間承認境界を空洞化し得る。
   - **提案:** D926 は「投入 confirmation」、D1161 は「走行後の freeze-budget human approval」と呼び分ける。AI は非承認 skeleton と検証結果まで、canonical candidate と pin の確定はユーザー手番に残す。

## nit

- なし。上記はいずれも受理集合、投入可否、または成果物の科学的主張を変え得るため nit ではない。

## 親の実測と一般化への所見

1. **旧 manifest の結論は妥当だが、件数記述が誤っている。**

   - **所見:** 588 件すべてが root tag 無しなのは正しいが、絶対 path は 549 件で、39 件は snapshot-relative である。
   - **根拠:** [旧 completion.json](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t1981-holdout-oneshot-removal/mainprobe/output/s8b-build-cache/contracts/e576e9cd1369bba3ae8faca084d1b7256bf919a7dd2e5d6facb093cd9e242c01/87aa2e6a61d85ef61b1ba88616bb19c39b5dfe49030f6f78fdc68175102d5c94/completion.json) の実読結果は schema v1、入力 588、root tag 0、absolute 549。v1 は現行 validator の legacy 分岐へ入る（[s8b_compiler_input.py:1020](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1942-floor-gate-recheck/orchestrator/campaign/s8b_compiler_input.py:1020)）。
   - **放置したとき:** 記録上の入力分類が 39 件ずれるが、「旧再走は現行 v3 collector の生死を測らない」という結論自体は変わらない。
   - **提案:** 「588 件すべて root tag 無し、549 absolute + 39 snapshot-relative」に訂正する。旧 failure の歴史的事実は維持する。

2. **旧 consumed 228 件の集計は正しいが、current fresh claim の拒否根拠ではない。**

   - **所見:** floor 96 件が 12 セル×8、n-pilot 132 件という観測は正しい。そこから current official の可否は直接引けない。
   - **根拠:** six-field effect key は [s8b_holdout_admission.py:753](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1942-floor-gate-recheck/orchestrator/campaign/s8b_holdout_admission.py:753)。現行 claim identity はさらに `observation_role + campaign_run_id` の generation digest を加える（[同:782](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1942-floor-gate-recheck/orchestrator/campaign/s8b_holdout_admission.py:782)、[同:805](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1942-floor-gate-recheck/orchestrator/campaign/s8b_holdout_admission.py:805)）。
   - **放置したとき:** 歴史 marker 数を現行 generation-scoped admission の残枠と誤認する。
   - **提案:** 228 件は歴史説明に限定し、G-B は現行 24 claim・192 consumed と prospective generation identity を対象にする。

3. **dependency binding の 12 セル一般化は静的には妥当である。**

   - **所見:** official default 経路で `dependency_binding=None` になるセルはない。ただし各 manifest の内容が同じという意味ではない。
   - **根拠:** `prepare_fn is prepare_cell` かつ `sort_best` が一つでもあれば run-wide binding を作る（[s8b_floor_campaign.py:4013](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1942-floor-gate-recheck/orchestrator/campaign/s8b_floor_campaign.py:4013)、[同:4057](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1942-floor-gate-recheck/orchestrator/campaign/s8b_floor_campaign.py:4057)）。cell 列挙は各 holdout に `sort_best` を必須とする（[s8b_floor_contract.py:674](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1942-floor-gate-recheck/orchestrator/campaign/s8b_floor_contract.py:674)）。current masstree root は全セルの receipt に渡る（[s8b_floor_campaign.py:4392](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1942-floor-gate-recheck/orchestrator/campaign/s8b_floor_campaign.py:4392)）。
   - **放置したとき:** 影響なし。ただし「全セルで root context がある」と「全セルの receipt が実測済み」を混同すると G-A の受理集合を過大評価する。
   - **提案:** 前者は静的保証、後者は未実測として分離する。

4. **D1161 の表現より D589 の位置づけが実装と一致する。**

   - **所見:** budget approval は official 走行そのものの前提ではなく、official result を v2 g1 freeze candidate へ昇格させる段の前提である。
   - **根拠:** campaign/submitter から budget approval consumer への呼出しはなく、唯一の呼出しは candidate builder。pin `None` の fail-closed は [s8b_holdout_freeze.py:1298](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1942-floor-gate-recheck/orchestrator/campaign/s8b_holdout_freeze.py:1298)。D589 も approval artifact・pin・official result 不在を candidate 生成の三条件としている（[decisions.md:23791](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1942-floor-gate-recheck/docs/decisions.md:23791)）。
   - **放置したとき:** 不存在の approval を投入前 blocker と誤認するか、AI が走行前に承認を完成させようとして人間境界を破る。
   - **提案:** D1161 の「official 経路」は「official 結果の freeze 昇格までを含む経路」と限定解釈する。現状で candidate builder を呼べば `budget-approval-not-ratified` だが、official campaign 自体はここでは止まらない。

## 総括

G-B は「衝突なしの瞬間観測」までに狭め、既存 generation-consumed と ledger の全整合を追加すべきである。  
G-A は transport 裁定後に同じ経路で測り、one-cell 緑を 12-cell readiness と呼ばない。  
budget approval は走行後の人間手番であり、AI は非承認 skeleton と検証までに留める。