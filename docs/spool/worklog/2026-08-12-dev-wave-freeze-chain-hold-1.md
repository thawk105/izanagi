---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-08-12
wave: dev-wave-freeze-chain-hold
seq: 1
title: bytes 級 provenance 番人の棚卸しで保留対象は 4 function に絞れ、受入 wall は直列鎖が決めていると実測した — 保留の実装は並行 2 wave へ移譲 (docs のみ、branch worktree-dev-wave-freeze-chain-hold)
---

## 本文

- **依頼の前提が 2 つ実測とずれていた。** (1) ユーザーは「T 番号は新規起票」と指示したが、
  2026-08-12 rulings 第 4 束 (branch `worktree-rulings4-20260812`、main 未 land) が凍結チェーン
  検証の保留を確定し、その執行タスクを**既に起票済み**だった。新規起票は重複になるため行わず、
  既起票タスクの執行として進めた。(2) 同裁定の「v1 凍結証拠テスト 4 本を退役」は実測 **1 本**
  (t816 wave が記帳)。「4」は凍結 raw trace の本数由来と解される。
- **三つ巴の重複を peer 交渉で解いた。** ユーザーの追加指示「並行セッションと作業の重複があったら
  メッセージのやり取りして重複作業避けてね」に従い `SendMessage` で直接調整した。着手直前に
  **t816 wave のユーザーが同 session へ「あなたでやる」と直接指示し、実装子が既に稼働していた**。
  技術的にも t816 の tip でしか 32 赤が再現しない (gitlink 前進済み) ため、**本 wave は実装から
  降りた** (書いた実装コードはゼロ、衝突なし)。分界 = t816 が凍結チェーン 5 系統の production
  hold、growth-tests wave が成長比例軸と保留台帳機構、本 wave が凍結チェーン**外側**の棚卸し・
  実測・独立検証・[T-902]。land 順は t816 → growth-tests → 本 wave。
- **棚卸しは 331 node → 26 function → hold 4 / keep 18 / unsure 4。** 機構語の総当たりは
  331 node / 73 file を拾ったが**大半が誤マッチ**だった (Python の関数 `signature`、予算
  `reservation`、campaign の live origin 台帳 28 node)。production 側の呼び出し実体から逆引きして
  絞った。**F1 (承認署名・外部 trust root) は production に実装が存在しない** — 親が `grep` で
  検算し、署名機構は皆無 (`--no-gpg-sign` は署名を*無効化*する側)、`t810_preregistration.py:446`
  の `approval_receipt_trust_root_absent` は「trust root が無い」という宣言そのもの。
  **F2 (commit 束縛) は 14 function すべて live admission・防壁**で保留対象外。
- **保留を確定したのは `orchestrator/publication/ledger.py` の R2 番人 4 function (= 5 node) だけ。**
  `(root, kind, ordinal)` 一意性と append-only 履歴 (prefix-only、delete/recreate 拒否) とその
  positive control。[T-793] R2 が [T-499]「手番が不要になったもの」に入っており、親が
  **非 test caller ゼロ**を grep で独立検算した。4 件とも唯一検出者であり、消える検出力は実在するが
  裁定された縮小である。
- **本 wave は実装しない (`4→7→8→9`)。** 3 つの理由が独立に成立した。(i) 相乗り先の保留台帳
  `orchestrator/tests/growth_test_holds.py` が**まだ存在しない** (親が `git show` で確認、
  growth-tests wave は段 5)。(ii) 自前で作れば「機構は 2 つ作らない」peer 合意に反し conftest が
  衝突する。(iii) 解除機構が land しないと positive control (env 無指定で理由付き skip / exact env
  で収集・実行 / 無効 env では解除されない) が書けない。4 entry は仕様として確定させ、台帳 land 後に
  `1 行 + pin の件数・digest 更新`の差分で投入する。
- **敵対レビュー 2 本が BLOCKER 10 件。うち sol の 6 件中 5 件が同型**だった —
  {{F:hold-target-colocated-with-correctness-gate}}。**異なる 4 モジュールで独立に出た**ため
  `DW-G03` の族一般化条件を満たす。5 件はすべて t816 の担当範囲だったので全文を転送し、
  t816 は行単位化・keep 集合の明示・23 件一括 node の保留撤回で応じた。
- **親 brief の誤りを 1 件、敵対レビューが捕まえた。** brief が「8b protocol pin seal の入口」と
  書いた `test_protocol_builder_repo_tree_guard_is_wired_to_real_root` の実体
  (`test_real_repo_serialization.py:823-897`) は、guard が実 ROOT を受けることと builder/writer が
  同一 guard action 内でだけ動くことの検査 = **防壁の自己完全性**だった。保留対象外。t816 へ訂正済み
  (向こうのアンカー表に元々無く実害ゼロ)。
- **t816 の可視性設計に親が穴 2 件を指摘し、設計が変わった。** 「held marker を process 内 registry へ
  積む」案は、(1) CLI subprocess 境界 (`s8b_holdout_freeze` の verify CLI、
  `s1_known_axes_freeze.py:907-922` の `main`、oracle driver の subprocess) で子の registry が親から
  見えず**終端要約が「何も保留していない」と表示する**、(2) xdist 48 worker がそれぞれ別 registry を
  持ち集約経路が無い、の 2 点で破れる。**保留の意味論上、可視性だけが唯一の防波堤**であるため、
  届かない経路が 1 つでもあれば裁定要求 (可視な skip 印) を実質破る。t816 は
  **発火のたびに stderr へ機械可読 1 行**を出す方式へ変更し、両穴と conftest 衝突を同時に解いた。
- **`-p no:xdist` は使えない。** `tools/run_tests.py` が注入する `-n <N> --dist loadgroup` が
  pytest から unrecognized になり **rc=4 で走行ゼロ**になる (request `906469.nqsv`、6 秒で END)。
  直列化は **`-n 0`** で行う (xdist を生かしたまま worker 0 = in-process 直列)。
- **受入の判定 (docs-only、免除でなく実走)。** 変更は `docs/spool/` の fragment と
  `output/insights/` のみ (判定手順 = `git diff --name-only main` が 2 者だけを示す)。実装面ゼロ、
  変異 matrix は `DW-S04` により免除。実 repo を読む docs 不変条件 node が実在するため免除せず、
  `test_check_docs.py::test_real_repo_clean` /
  `::test_dev_wave_model_pins_accept_current_docs_contract` /
  `::test_normative_exact_section_pins_accept_real_repo` を計算ノードで焦点走し **3 passed / 11.70 秒**
  を実測した (受入形ではない)。`tools/check_docs.py` rc=0、`tools/spool_fold.py --dry-run` rc=0
  (`planned`)、`tools/check_ai_provenance.py` 全史 rc=0 (2,851 件・新規違反なし)。

## 次の一手差分

### 新規

- {{T:publication-ledger-r2-hold-entries}} **P2・新規**: 公表台帳 R2 番人 4 function (= 5 node) を
  保留台帳へ投入する。対象 = `test_t793_publication_ledger.py` の
  `test_duplicate_root_kind_ordinal_identity_is_rejected` /
  `test_unchanged_ledger_bytes_across_merge_history_are_accepted` /
  `test_committed_non_prefix_ledger_history_is_rejected` (2 node) /
  `test_committed_delete_and_recreate_is_rejected`。field は
  `hold_axis: provenance-chain` / `correctness_gate: false` /
  `release_condition: explicit-user-command-only` / `measured_seconds` = 直列実測
  (0.01 / 0.04 / 0.03+0.03 / 0.03、合計 0.14 秒)。**前提 = growth-tests wave の保留台帳の land。**
  投入は `1 行 + pin の件数・digest 更新`で、conftest には触れない。**鎖外なので `xdist_group`
  は付けない** (付けると `test_real_repo_serialization.py:567-615` の golden が赤になる)。
  正本 = `output/insights/2026-08-12_freeze-chain-hold-sweep/`。
- {{T:hold-manifest-integration}} **P2・新規**: 3 wave が land した後、保留を 1 箇所で読める統合
  manifest を作る。現状は 3 層に散る — t816 = production 検査点の hold (解除は定数の人手編集、
  可視化は stderr の機械可読行)、growth-tests = test 層の skip 台帳 (解除は env
  `IZANAGI_RUN_GROWTH_HELD_TESTS`)、本 wave = 同台帳への相乗り。**恒久保留の解除がユーザー明示命令
  のみである以上、ユーザーが「今なにが保留中か」を 1 箇所で読めないことは運用上の欠陥**である
  (段 3 luna B2 / M3)。
- {{T:holdout-scan-optimize-not-hold}} **P1・新規**: `s8b_holdout_freeze.search_repository`
  (11,988 file を毎回読み `re.search` 107,721 回) を、**保留でも除去でもなく最適化**する。
  [T-902] を阻んでいた「実装を 1 byte 変えると freeze 再発行が要る」の正体は `_verify_source` の
  generator pin (`SCRIPT_REL` の bytes 完全一致) であり、**t816 の保留が入った時点でこの阻害要因が
  消える**。3 軸 × 4 候補の走査は 1 パスへ畳めるはずで、保証 (holdout hit 0 + rr50 陽性対照非 0) を
  1 つも落とさずに済む。**前提 = t816 の保留 land。**
- {{T:brief-anchor-table-single-source}} **P3・新規・予算不足で自動是正を断念、裁定へ返す**:
  親 brief で「分類文」と「実アンカー表」を二重管理しない契約を `DW-O02` へ 1 文足す。
  **独立 2 例** — (i) 本 wave の brief が誤った入口 (`test_protocol_builder_repo_tree_guard_...`) を
  分類文へ書き段 3 が捕捉、(ii) t816 wave の prompt 冒頭の分類文に、実アンカー表から外した対象
  (`test_frozen_artifacts.py`) が残っていた (実害前に発見)。**子は分類文の方を広く読む**。
  対策案は「アンカー表が正本と明記」より「分類文を置かずアンカー表だけを渡す」が有力
  (t816 も後者に賛成)。**段 8 で実際に `DW-O02` へ追記を試み、予算で撥ねられた** — 最短形
  (1 行 99 bytes) でも L1.5 unique footprint が 9,693 bytes となり予算 9,566 bytes を 127 bytes
  超える。**現在の余白は約 3 bytes。** 自己改善契約「予算に収まらなければ…意味等価にできなければ
  変更を止めてユーザー裁定へ返す」に従い断念した。**予算値の引き上げは提案しない** — 択一は
  (a) L1.5 集合内の陳腐化した節を 1 つ retire して空ける、(b) この契約を諦める、
  (c) `DW-S01` 側 (別予算) へ置く。
