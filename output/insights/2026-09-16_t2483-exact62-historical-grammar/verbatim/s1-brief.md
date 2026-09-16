# 段 1 brief — [T-2483] exact-62 の campaign lock を読む経路

**研究前進 (土台):** 止めているのは「paper-story A-2 の attempt `t2364-20260907b` (D1993 決定 1 が
D1645 の解除条件を満たすと認定した attempt) と A-6 の `a6-20260908b` の認証証拠を、後から読み直す
経路」である。台帳 [T-2483] の実測では現行 consumer は 0 件で影響は潜在。最小差分は、歴史閲覧
decoder に exact-62 grammar を 1 件だけ収載すること。認証経路は 1 mm も変えない。

**確定済みユーザー裁定 (不変条件として扱う):**
- D1653 の必須条件 (逐語 = `ruling-D1653.md`)。とくに「通常 decoder / encode / resume /
  certified admission は現行 grammar のまま。union にしない」「別入口・別返却型。flag や boolean
  引数による緩和にしない」「grammar は exact ordered tuple で識別し subset / superset / 同数別集合 /
  順序違いを拒否」「旧 tuple は現行 tuple の slice ではなく独立 literal」「記録 commit blob との
  digest 照合を旧 grammar の全 path で維持」「歴史 epoch は記録 grammar の順序とその grammar 固有の
  scope 文言で計算し、現行適合は unknown」「互換実装を新 module へ分離しない」。
- D1653 の収載条件「実在 corpus が確認できたものだけ」は exact-62 について成立済み (実測 3 本)。
- ユーザー引数: 対象は既知の 3 本に限定。本題の読取り経路だけ。仮想リスク向けの gate・検査・台帳・
  一般化の追加は scope 外。規律 2 を緩めない。実装面は Codex author (D95)。

**scope (成果物影響つき):**
- (in) `orchestrator/campaign/campaign_lock.py` に exact-62 の独立 ordered literal を置き、
  歴史閲覧 decoder がその wire 順序を識別して受理する。影響 = この 3 本が歴史閲覧経路から読める。
- (in) `orchestrator/campaign/artifact_admission.py` で、exact-62 を記録 grammar とする lock を
  `HistoricalCampaignVerifierEpoch` (= certified acceptance へ入れない型) として扱い、
  exact-62 固有の epoch scope 文言を与える。影響 = 材料レポートの `identity_scope` が
  当時の閉包を正しく名乗る。
- (in) 新旧いずれの grammar でもない wire を拒否し続けることを示す否定テスト。
- (out) `CAMPAIGN_VERIFIER_EPOCH_SCOPE` の文面訂正 ([T-2482] の持ち分)。
- (out) 旧 grammar 8 / 12 / 14 / 25 / 27 の収載 ([T-2345]。実在 corpus 未観測で条件不成立)。
- (out) [T-2125] の policy 版上げ問題。3 本の記録値は現行 policy と bytes 一致で発火していない。
- (out) 3 本以外の corpus への一般化、再発防止 gate、台帳新設。

**不変条件:**
1. `decode_campaign_lock` (通常 decoder) は exact-63 のみ。exact-62 を受理しない。
2. `CampaignReadPurpose.CERTIFIED_ACCEPTANCE` の受理集合は変化しない。
3. exact-62 lock は `HISTORICAL_RAW` でしか decode されず、返却型は `DecodedHistoricalCampaignLock`。
4. exact-62 の 62 path すべてについて記録 commit blob との digest 照合を維持する。
5. 既存の pre-T733 exact-24 経路と B10 の consumer の挙動は bytes 単位で不変。
6. 「現行 63 から 1 path 落とした 62」を未知 grammar として使う既存の否定テストがあれば、
   別の真に未知な grammar へ差し替える。否定側を恒真にしない。

**(P1) 親の provisional 裁定 (攻撃対象):** exact-62 の宣言順は `2a9ba783f^` 時点の
`CONTRACT_LOADER_RELATIVE_PATHS` と定める。現行 63 から末尾 1 件を除いた列と集合・順序ともに
一致するが、独立 literal として書く。

**成果物の形:** exact-62 の独立 literal 1 件、歴史 decoder の識別分岐、admission 側の epoch 分類と
scope 文言、正例 1 本 (exact-62 が歴史閲覧で読める)・負例 2 本以上 (通常 decoder が拒否する /
未知 grammar が拒否される)。実 3 本での確認は親が repo 外で実行し逐語を insight へ残す。

**並列分割:** 編集面が 2 file に収まり相互依存するので段 5 の実装子は 1 本。
段 2 plan 1 本、段 3 敵対 2 レンズ、段 6 レビュー 2 レンズ。
