# 段 1 brief — [T-1232] failure-only build report を root 引数なしで独立検証できるようにする

基準 commit: d97c423bdd14e0b416cb4f585d350e6c2b251287 (着手直前の local main)。
worktree: `/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1232-rootless-failure-report`
(branch `worktree-dev-wave-t1232-rootless-failure-report`、lock 済み、submodule 初期化済み、
`tools/check_wave_startup.py --mode fresh` rc=0)。以下の file:line はすべてこの worktree の現物である。

## 研究前進

8c 正式系列は失敗した試行について「なぜ壊れたか」を構造化した診断 report を出す (規律 3)。その report を
運用者が**手元の 2 file (journal と report.json) だけで独立に再検証できる**ことが、診断成果物が
診断として成り立つ条件である。現行の standalone verifier は、失敗しかない build report にまで
campaign 出力 root を要求する場合が残っており、**診断が要る失敗走ほど独立検証できない**。
完了判定: producer が実際に出す失敗のみの build report を、CLI が root 引数なしで検証できる。
かつ admitted cell を含む report は従来どおり root を要求する (負例が生きている)。

## scope (これだけ)

`verify_autonomous_trial_files` (`orchestrator/campaign/autonomous_trial_completeness.py:5036`〜`:5096`) と
その CLI `main` (`:5099`〜`:5121`)。テストは `orchestrator/tests/test_autonomous_trial_completeness.py`。
編集面はこの 2 file だけ。producer (`p3_autonomous_workload_trial.py`)、受入 (`trial_registry.py`)、
`verify_s8c_cross_binding`、`assert_campaign_layer3_chain` の**受理集合は変えない**。

## 確定済みユーザー裁定・既裁定 (覆さない)

- **規律 2**: 正しさゲートを緩める変異を採らない。root 要求の一律撤去・既存負例の反転は禁止。
- **D95**: 実装面 (コード・テスト・probe) は Codex `role=author` が書く。親は直接編集しない。
- **D1460** (`docs/decisions.md:45850`): 「層 3 の空走は受入限定で閉じる。全 verifier へ広げる案は採らない」。
  これは *より強い* gate を全 verifier へ広げる案の却下であり、本 wave の向き (root 省略の根拠を
  閉じた述語で与える) とは逆。ただし同裁定は `verify_autonomous_trial_files` の既存 2 免除を
  「意図的に許す」と位置づけている (`output/insights/2026-09-04/t2120-layer3-empty-run-acceptance/brief.md`)。
  **本 wave はこの 2 免除を削らない。**
- 依頼の明示 scope 外: 仮想リスク向けの gate・検査・台帳・一般化の追加。

## 実測 (brief 前、この worktree の現物)

**性質の申告:** 以下 1〜6 は**現物の source 読解**であり、テストや producer を実走させて得た値ではない。
7〜8 は `git` と `sha256sum` の**実行結果**である。1〜6 を「実走で確かめた」と扱ってはならない。
実走による裏取りは段 5 で足すテストと段 6 の焦点走が担う。

1. **T-1232 の前提は一部すでに閉じている (依頼文を覆す新事実)。** root 要求 (`:5069`) には免除が 2 つある。
   - `fatal_without_cells` (`:5054`): `do_build=True` かつ `fatal_error` かつ `cells == []`。
   - `failure_without_campaign` (`:5059`): `do_build=True` かつ全 cell が
     `is_exact_campaignless_failure_fallback_cell` (`:363`、実体 `:336`) に厳密一致。
   後者は 2026-08-18 の commit `79194aebf9` (T-1348 の C09/C10 consumer 配線) で入った。
   T-1232 起票 (2026-08-16) より後だが、T-1232 を閉じる意図では入っていない。
2. **producer の campaignless fallback は既に免除に当たる。** `p3_autonomous_workload_trial.py:3691`〜`:3696` が
   4 key の cell を作り、`_finalize_cell_admission` (`:3247`) が `pending_critic_disposition` と
   `admission_decision` を足して 6 key になる。述語の `set(cell) == {6 key}` に一致する。
   → **この形は現行でも root なしで通る。**
3. **残る穴 (T-1232 の生存部分)**: `_partial["cell"]` 経路 (`:3679`〜`:3690`)。cell は `:4083`〜`:4096` で
   生成された時点で `campaign_root` (`:4093`, `layout.root`) と `campaign_id`、`descriptor` 等を持つ。
   campaign 成果物が 1 byte も書かれる前に supervisor が落ちると、`_finalize_build_cell_admission`
   (`:3099`) が「build cell campaign has no reports directory」で失敗し admission 失敗 decision が付く。
   この cell は key が 6 個を超えるので免除述語に当たらず、**root を要求される。**
   実在する producer 走の例: `test_p3_autonomous_workload_trial.py:8876` 付近
   (`formal-noncertifying-build-crash`、`do_build=True`、`cells[0].stop_reason == "supervisor-error"`)。
4. **root が今やっている仕事 (削ってはいけない中身)。** `assert_campaign_layer3_chain` の失敗 cell 区間
   (`:4906`〜`:4924`) は root を使って 3 つを検査する。(a) `campaign_root == output_root/campaigns/campaign_id`
   の path identity 束縛、(b) その root 配下に `reports/layer3_report.json` が**無い**こと、
   (c) `require_admitted_campaign` が失敗する (= 独立には admitted でない) こと。
   **root 省略でそのまま失われるのは (a) だけである。(b)(c) は report 自身が宣言する `campaign_root` に対しても
   実行できる (file system の事実であり report 内部の恒真ではない)。**
5. **保たねばならない負例**: `test_autonomous_trial_completeness.py:2352`
   `test_build_file_verification_with_cells_still_requires_campaign_root` (admitted cell は root 必須)。
6. **被覆の穴**: `failure_without_campaign` を `verify_autonomous_trial_files` 経由で通す正例テストが 0 件。
   既存の該当テスト (`:5103`) は `assert_campaign_layer3_chain` 単体を叩いている。
7. **凍結 pin 閉包 (DW-O09)**: 編集面 2 file を bytes / sha256 で pin する台帳は**無い**。
   - `orchestrator/campaign/s8c_preregistration_evidence_contract.v1.json:398` は path + `field_paths` +
     `reachable_from` を pin するが、entrypoint は `verify_s8c_cross_binding` であって本 wave の編集面ではない。
   - `paper_story_a1_paired.py:174` の `NON_CERTIFYING_SOURCE_RELATIVE_PATHS` に本 file は**入っていない**。
   - **`test_s8c_preregistration_predicates.py:262` は `git show <HEAD>:orchestrator/campaign/autonomous_trial_completeness.py`
     で HEAD blob から読む。** 未 commit の編集はこの検査に映らない。→ 段 6 の焦点走の前に commit する。
   - `orchestrator/tests/acceptance_duration_ledger.json` に nodeid 単位の所要台帳がある (F902)。
     **新規 test は nodeid を台帳へ足さないと受入で赤になる。**
8. **編集面の重複 (DW-O20、worktree 113 本 + codex 木を全走査、内容 sha256 照合)**: 差があるのは
   `dev-wave-t304-throughput-rename` とその子 `t304-impl` の 1 組だけ。作業ツリーは branch tip と一致 (dirty でない)。
   未着地 commit `4c6f03048` が両 file を触るが、変更行は impl 427/436・test 53/2909-2917 で、
   **本 wave の行域 (impl 5036〜5096、test 2352 付近) と重ならない。同一 file なので land 時に取り込む。**

## 不変条件

- admitted cell を 1 つでも含む build report は、従来どおり root なしでは通らない。
- 既存 2 免除 (`fatal_without_cells`、`failure_without_campaign`) の受理集合を変えない。
- `assert_campaign_layer3_chain`、`verify_s8c_cross_binding`、受入 `assert_trial_registry_acceptance` の
  受理集合を変えない。producer の出力 bytes を変えない。
- 既存テストの期待値を変えない。緩和・反転・skip・削除を禁じる。

## 割れうる前提 (親の provisional 裁定・段 3 の攻撃対象)

- **(P1) 既定を緩めず、明示 opt-in を足す。** `verify_autonomous_trial_files(root=None)` の既定挙動は
  一切変えない。別に閉じた述語 (全 cell が厳密な `cell-admission-failure/v1` decision を持ち、
  admitted cell が 1 つも無い) を満たすときだけ通る**明示引数** (CLI では新 flag) を足す。
  flag を付けても admitted cell があれば fail-closed。→ 「root を省いてよい根拠」が引数側に署名として残る。
- **(P2) root 省略時も (b)(c) は検査する。** report が宣言する `campaign_root` に対して
  「persisted layer3 report が無い」「独立には admitted でない」を実行する。検査しないのは (a) path identity 束縛だけとし、
  検証していないことを構造化して申告する (規律 3)。
- **(P3) この経路は certifying に使えないと署名で書く。** 通る正例を 1 つ添える (DW-S04)。
- **(P4) 実装 1 単位で足りる。** 編集面が素集合に割れない (同一関数) ため段 5 は 1 子。

## 成果物の形

- `autonomous_trial_completeness.py`: 新しい閉じた述語 + 明示引数 + CLI flag。既定経路は無改変。
- `test_autonomous_trial_completeness.py`: 正例 1 (producer 実形に一致する partial 失敗 cell が新 flag で通る)、
  負例 n (flag 付きでも admitted cell / 非厳密 decision / persisted layer3 report 有りは通らない、
  flag 無しでは従来どおり root 必須)。既存 `:2352` の負例は無改変で緑のまま。
- `acceptance_duration_ledger.json` への新 nodeid 追記。
- 変異事前登録は段 4 で確定する。

## 分割方針

段 2 plan 1 本 → 段 3 敵対 2 レンズ → 段 4 裁定 → 段 5 実装 1 子 → 段 6 レビュー 2 本 + fix + 変異 + 受入。
