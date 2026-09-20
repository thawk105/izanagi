# 段 1 brief — [T-2344] enforcement source closure を推移閉包へ向けて 1 段進める (63 → 85)

**研究前進 (土台):** 論文が「certified 経路は source-bound」と言うための土台。D1075 (ユーザー裁定) は
verifier / calibrator / buildcache を含む推移閉包まで束縛を広げよと命じ、D1884 は段階実装の継続を裁定した。
止めているのは「正しさ防壁自身が束縛されていない穴」(verifier を弱めても既存 lock の照合を通る) で、
着手時の実測 (measured-facts.md §1) では収載 63 に対し発見集合 163、未収載 100 (発行器起点を含む和では 173 / 110)。
本 wave の最小差分は、現行 63 の 1 段目 (直接 import 先 + package 初期化) 22 本を収載して exact 85 にし、
未収載を 100 → 78 (和では 110 → 88) にすること。完了判定 = tuple が exact 85、exact-63 の歴史 grammar が
HISTORICAL_RAW で読める、certified decoder は exact-85 のみ、scope 文言が D2081 形式で 85 / 163 / 78 を名乗る、
独立 literal の test が同 commit で追随、変異の正例・負例が pre-registered どおりに落ちる。図表は変えない。

**確定済みユーザー裁定 (不変条件、逐語 = rulings-verbatim.md):**
- D1075: 推移閉包へ広げる。段階実装可。**閉包が閉じるまで保証の文言は広げない。**
- D1884: 現行 63 で終端しない。段階の範囲は wave が決めてよい。名乗りを先に広げない。一度に 165 (→ 今は 173) へは広げない。
- D1653 / D1770: 旧 grammar は歴史閲覧限定 decoder (別入口・別返却型) で読む。収載は**実在 corpus が確認できた grammar だけ**。
  旧 tuple は独立 literal。通常 decoder / encode / resume / certified admission は現行 grammar のまま、union にしない。再発行しない。
- D2081: scope 文言は現行 tuple の値と、日付・commit 付きの発見集合の実測値で書く。実行時計算・発行器名は書かない。
- ユーザー引数: tuple の curated 順を保つ。policy epoch (E1 fixture の固定文字列) の追随 test を同 commit で更新。Codex author (D95)。
  収載追加の正例と未収載検出の負例の変異。規律 2 を緩めない。本題だけ。仮想リスク向けの gate・検査・台帳・一般化は scope 外。

**scope (成果物影響つき):**
- (in) `campaign_lock.py:49` `CONTRACT_LOADER_RELATIVE_PATHS` を 63 → 85 (既存 63 の順は不変、22 本を末尾へ)。
  影響 = 新規 campaign の lock は 85 key を記録し、E1 epoch の preimage が 85 path になる。
- (in) exact-63 の歴史 grammar (独立 literal + 兄弟 validator + 歴史 decoder の分岐 + admission の歴史 scope 定数、T-2483 と同型)。
  影響 = 記録済み exact-63 lock 20 本 (measured-facts §3) が HISTORICAL_RAW から読め続ける。無ければ exact-62 のときと同じ「両経路から読めない」が再発する。
- (in) `artifact_admission.py:76-86` の現行 scope 2 定数を 85 / 163 / 78 (2026-09-20、f94b61fc8) へ。旧 63 文言は歴史 scope 定数として凍結。
  影響 = 材料レポート `identity_scope` / `excluded_scope` が現物の被覆を名乗る。
- (in) 独立 literal の test 追随 (measured-facts §4 の一覧)、docstring の「63」。
- (in) 受理集合の変化 (D1653 が裁定済みの帰結): tuple 前進後の checkout から記録済み exact-63 campaign 20 本を CERTIFIED_ACCEPTANCE で読むと
  decode 段で拒否される (`_validate_authority` の exact key 集合)。読み直しは記録 commit の checkout か HISTORICAL_RAW。E1 の blob 差は従来どおり拒否しない (D1163)。
- (out) 発行器 6 本の seed 追加、2 段目以降、実行時に閉包を数える機構、`enrolled ⊆ discovered` gate、production 入口 registry、旧 grammar 8 / 12 の収載、
  lock の再発行、paper-story docs の日付付き既述 (真のまま)、`b10_backoff_shape_sweep.py:3141` の pre-T733 限定 (不変)。

**不変条件:**
1. `decode_campaign_lock` は exact-85 のみ。exact-63 / 62 / 24 を受理しない。`CampaignReadPurpose.CERTIFIED_ACCEPTANCE` に旧 grammar は 1 本も入らない。
2. exact-63 は `HISTORICAL_RAW` でだけ decode され、返却型は `DecodedHistoricalCampaignLock`、epoch は `HistoricalCampaignVerifierEpoch` (現行適合 unknown)。
3. epoch の hash 式 (`campaign-verifier-epoch/v1` + path\0blob) は不変。tuple の順序が preimage に効く。
4. exact-63 の 63 path すべてで記録 commit blob との digest 照合を維持。exact-62 / 24 の経路は bytes 単位で不変。
5. 否定側を恒真にしない: 「未知 grammar」として使う test の grammar が収載後も未知であること (85−1、63+1、順序違いなど)。
6. 「推移閉包」「source-bound」を推移閉包の意味で名乗る文言をコード・docstring・test・docs に足さない。

**(P1) 次段の範囲 = 現行 63 起点の 1 段目 22 本 (measured-facts §2)。** 根拠: BFS 深さで切る規則は probe で再現でき、drift 2 本と
production 到達 2 本を含む。却下: drift 2 本だけ (1 段と言えない)、発行器 6 本の seed 追加 (候補集合の定義変更で次段の裁定対象)、22+6。
**(P2) exact-63 の歴史 grammar を同 commit で収載する** (D1653 の corpus 条件は 20 本で成立)。
**(P3) tuple 順 = 既存 63 の順 + 22 本を path の sorted 順で末尾に append** (T-2429 が 63 本目を末尾に足した先例と同形)。
**(P4) scope 文言 (案、段 4 で確定):** identity = 「enforcement source closure (curated exact 85 path; source-import 推移閉包ではない;
発見集合は収載 tuple を起点に静的 import と package 初期化を辿った集合であり、2026-09-20 (f94b61fc8) の実測では 163 module、
うち収載 85 (2026-09-16 時点の 63 と、その直接 import 先・package 初期化の 22))」、excluded = 先頭を「同実測の発見集合の未収載 78 module、」に。
**(P5) 変異 (段 4 で事前登録):** 正例 = 22 本のうち 1 本を tuple から落とす / 順序を 1 対入れ替える → 独立 literal・固定 epoch・順序 sha の test が赤。
負例 = 歴史 decoder の白名単を superset へ緩める / exact-63 を現行分岐へ流す / certified decoder に sorted(63) を union する → 拒否 test が赤。

**成果物の形:** 実装面 = `campaign_lock.py`、`artifact_admission.py`、`contract_loader_binding.py` (docstring)、tests 5 file。
insight `output/insights/2026-09-20/t2344-closure-stage1/` (brief・実測・相談・裁定・変異台帳の逐語)。spool fragment (worklog / decisions)。

**並列分割・段構成:** 受理集合が変わり正しさ防壁 (source binding) に触るので DW-C00 の独立敵対検証子を置く。段 2 plan 1 本、段 3 2 レンズ、
段 5 実装子 1 本 (3 file + tests は相互依存)、段 6 レビュー 2 + fix、変異 matrix、受入全走。受入は `dev_wave_wait.py acceptance --lease-optional` (Pegasus 計算ノード)。
codex 子は login node、read-only 子は pytest 非実走 (静的検査)。
