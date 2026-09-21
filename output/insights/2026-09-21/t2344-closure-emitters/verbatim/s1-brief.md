# 段 1 brief — [T-2344] source-bound closure の次段: 発行器 6 本 + 発行器起点にだけ居る module を収載する (85 → 96)

**研究前進 (土台):** certified 選択結果の正しさ防壁の土台。D1075 / D1884 が名指しした穴「認証成果物を発行する module 自身が
束縛の集合の外にある」を、D2194 項 4 (ユーザー裁定) が選んだ順 (発行器先行) で塞ぐ。着手 commit `5efd69367` の実測
(measured-facts.md §1) では発行器 6 本はすべて未収載 (5 本は tuple 起点の発見集合の外)。最小差分は、発行器 6 本と
発行器起点にだけ居る 10 本の和 **11 本** (10 本のうち 5 本は発行器自身) を末尾に足して exact 96 にし、exact-85 の
歴史 grammar を同 commit で収載すること。完了判定 = tuple が exact 96、発行器 6 本が収載され、96 seed の発見集合 173 のうち
未収載 77 を D2081 形式の scope 文言で名乗り、exact-85 が HISTORICAL_RAW でだけ読め (§(P2) の条件つき)、通常 decoder は exact-96 のみ、
独立 literal の test が同 commit で追随、変異の正例・負例が事前登録どおりに落ちる。図表・記録済み成果物の bytes は変えない。

**確定済みユーザー裁定 (不変条件、逐語 = rulings-verbatim.md):**
- D2194 項 4 (1): 次段 = 発行器 6 本と発行器起点にだけ居る 10 本を先に収載。tuple 起点の 2 段目 23 本は含めない。tuple を動かす変更単位には
  直前 grammar の歴史収載を同 commit で含める (D2193)。(2): 記録済み exact-63 成果物 20 本の最新 consumer での certified 再解析は (c) 現状維持
  (HISTORICAL_RAW と記録 commit)。本 wave は exact-63 の経路に触れない。(b) 再測定は採らない。
- D1884 / D1075: 閉包が閉じるまで「certified 経路が source-bound」を推移閉包の意味で名乗らない (本 wave 後も未収載 77)。一度に全部は広げない。
- D1653 / D1770: 旧 grammar は歴史閲覧限定 decoder (別入口・別返却型、exact ordered tuple、独立 literal、記録 commit blob 照合、grammar 固有 scope、
  現行適合 unknown)。通常 decoder / encode / resume / certified admission は現行 grammar のまま、union にしない。**収載は実在 corpus が確認できた grammar だけ**。
- D2193: 既存の宣言順を動かさず末尾へ path の sorted 順。scope 文言は D2081 の形式 (日付・commit・本版 tuple を起点に同じ source 木で再測した数値、内訳は書かない)。
- ユーザー引数: Codex author (D95)、変異負例。着手直前の local main から fresh worktree。規律 2 を緩めない。本題だけ。gate・台帳・一般化の追加は scope 外。

**scope (成果物影響つき、DW-G05):**
- (in) `campaign_lock.py:49` の tuple を 85 → 96 (既存 85 の順は不変、11 本を末尾へ sorted 順)。影響 = 新規 campaign の lock が発行器 6 本を含む 96 blob を記録し、
  E1 epoch の preimage が 96 path になる。certified 受理時の「現行収載 path が clean committed」前提 (`artifact_admission.py:1186-1206`、D1163) が 11 本へ広がり、
  発行器を未 commit の編集のまま certified 受理・campaign 起動に使えなくなる (記録時と発行時の bytes 同一は要求しない — D1163 のまま)。
- (in) exact-85 の歴史 grammar (独立 literal + 兄弟 validator + 歴史 decoder 分岐 + admission の歴史 scope 定数 = 現行 85 の scope 文言を byte 同一で凍結)。
  影響 = 記録済み exact-85 lock (measured-facts §2) が tuple 前進後の checkout の HISTORICAL_RAW で読め続ける。
- (in) `artifact_admission.py:76-86` の現行 scope 2 定数を 96 / 173 / 77 (2026-09-21、5efd69367 の source 木、本版の 96 path を起点) へ。
  影響 = 新規 report の `identity_scope` / `excluded_scope` (layer3 / s8b oracle report の unavailable 分岐を含む) が現物の被覆を名乗る。記録済み report は不変。
- (in) 独立 literal の test 追随 (measured-facts §3 の一覧)、docstring の「85」、git timeout 派生値 850 → 960 (10 秒 × 96)。
- (in) 受理集合の変化 (D1653 の帰結、開示のみ): tuple 前進後の checkout では記録済み exact-85 campaign は certified の decode 段で拒否される。
- (out) 2 段目 23 本、発行器以外の seed 追加、exact-63 成果物の再解析・解析 checkout の用意、実行時に閉包を数える機構、`enrolled ⊆ discovered` gate、
  発行時 bytes = 記録 bytes の新検査、production 入口 registry、lock 再発行、docs の日付付き既述 (真のまま)、`b10_backoff_shape_sweep.py:3141` の pre-T733 限定。

**不変条件:**
1. `decode_campaign_lock` は exact-96 のみ (v2 authority)。exact-85 / 63 / 62 / 24 を受理しない。`CERTIFIED_ACCEPTANCE` に旧 grammar は 1 本も入らない。
2. exact-85 は `HISTORICAL_RAW` でだけ decode、返却型 `DecodedHistoricalCampaignLock`、epoch `HistoricalCampaignVerifierEpoch` (現行適合 unknown)、scope は凍結した 85 文言。
3. epoch の hash 式は不変。既存 85 の宣言順は不変 → exact-85 の固定 epoch は現行 test 固定値と同一 (親 oracle で確認済み)。
4. exact-63 / 62 / 24 の経路は bytes 単位で不変 (D2194 項 4 (2) の (c))。
5. 否定側を恒真にしない: 未知 grammar として使う test の grammar が収載後も未知であること (96−1 が既知 85 と衝突しないか等)。
6. 「推移閉包」「source-bound」を推移閉包の意味で名乗る文言をコード・docstring・test・docs に足さない。発行器の束縛を「発行時 bytes の同一性」と書かない。

**(P1) 収載対象 = 11 本 (6 ∪ 10)、既存 85 の後に path の sorted 順で append (measured-facts §1)。** 親の provisional 裁定・攻撃対象。
**(P2) exact-85 の歴史収載を同 commit で行う — 実在 corpus は着手時点で 0 本 (measured-facts §2)。** 親の provisional 裁定・**主攻撃対象**。
D1653 (D1770 追認) は「収載は実在 corpus が確認できた grammar だけ」、D2193 は同 commit 収載の条件を D1653 の corpus 確認と書く。一方、D2194 項 4 (ユーザー裁定、
より新しく本件に特定) と本 wave の引数は「tuple を動かす変更単位には直前 grammar の歴史収載を同 commit で含める」と無条件で書く。
provisional = 収載する。理由: (i) exact-85 は 09-21 00:21 以降 main の現行 grammar で、本 wave の land までに main から起動された campaign はすべてこれを記録する。
land 時点の corpus を事前に 0 と確定する手段が無く、収載しないと D2193 が防ごうとした「両経路から読めない lock」を再発させうる。(ii) 収載の受理拡大は
HISTORICAL_RAW の exact ordered tuple 1 個に限られ certified へ入らない (D1653 の必須条件はすべて満たす)。(iii) D1653 の corpus 条件が狙うのは使われたことの無い
grammar の投機的収載で、exact-85 は main の履歴に実在した production grammar。**開示:** D1653 の corpus 条件は着手時点で未充足と明記し、受入直前に全域走査を再実行して
land 時点の本数を記録する。decisions fragment で解釈を残す。対案 = (B) corpus 0 なら収載しない (D1653 字義)、(C) 受入直前の再走査で 1 本以上なら収載・0 なら収載しない。
**(P3) scope 文言 (案):** identity = 「enforcement source closure (curated exact 96 path; source-import 推移閉包ではない; 発見集合は収載 tuple を起点に
静的 import と package 初期化を辿った集合であり、2026-09-21 (5efd69367 の source 木、本版の 96 path を起点) の実測では 173 module、うち収載 96)」、
excluded = 先頭を「同実測の発見集合の未収載 77 module、」に (他は現行と同一)。
**(P4) 固定値 (親 oracle、oracle-fixed-values.json):** 合成 E1 `E1:244d998f35b0f7deae215a4053d9dde5acf60fc0775e4ea4c7a315579e7da07a`、
順序付き path sha256 `5c2c4a6a45ec44f46d655f1d9c43f1d877d5547fc46ff308fbdaa61df6683af4`、exact-85 固定 epoch = `E1:bc8a6c8c…423dc7` / path sha `bea36246…6b5a1`。
**(P5) 識別子名:** `T2344_EXACT85_CONTRACT_LOADER_RELATIVE_PATHS`、`T2344_EXACT85_CAMPAIGN_VERIFIER_EPOCH_SCOPE` / `_EXCLUDED_SCOPE` (T2429_EXACT63 と同じ命名規則)。
**(P6) 変異 (段 4 で事前登録):** 正例 = 新 11 本の 1 本 (発行器) を tuple から落とす / 末尾 2 本の順を入れ替える → 独立 literal・固定 epoch・順序 sha の test が赤。
負例 = 歴史 decoder の exact-85 分岐を外す (歴史正例が赤)、通常 decoder に sorted(85) を union (certified 拒否 test が赤)、歴史 validator を superset へ緩める、
exact-85 歴史 scope を現行文言へ差し替える、新規発行器の drift を certified が受理する方向へ緩める。

**成果物の形:** 実装面 = `campaign_lock.py`、`artifact_admission.py`、`contract_loader_binding.py` (docstring)、tests (`test_artifact_admission.py`、`test_campaign_lock_codec.py`、
`test_t671_source_binding.py`、`test_layer3_report.py`、`test_s1_9pair_figure_provenance.py`)。insight `output/insights/2026-09-21/t2344-closure-emitters/`。spool fragment (worklog / decisions)。

**並列分割・段構成:** 受理集合が変わり正しさ防壁に触るので DW-C00 の独立敵対検証子を置く。段 2 plan 1、段 3 2 レンズ、段 5 実装子 1 (相互依存)、
段 6 レビュー 2 + fix、変異 matrix、受入全走 (`dev_wave_wait.py acceptance --lease-optional`、Pegasus 計算ノード)。焦点走は commit 済みの木で dispatch。

---

## 訂正 (段 6 レビュー B-3 を受けて、2026-09-21 09:3x JST)

(P2) の「実在 corpus は着手時点で 0 本」は「**指定走査条件では 85-key v2 未検出、exact 照合済み corpus は未確認**」に読み替える
(`measured-facts.md` の訂正節が正本)。scope の「記録済み exact-85 lock (measured-facts §2) が …読め続ける」も、
**記録済み exact-85 lock が存在する場合に**読め続ける、という条件文として読む。
(P2) の採否は既裁定から必然的に導ける結論ではなく、本 wave の政策判断である (段 4 裁定 §8 を正本とする)。
