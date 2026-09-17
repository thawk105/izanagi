## 段 1 brief (2026-09-17)

**研究前進 (土台):** 止めている実測 = 非 silo (mocc / tictoc) の between-run floor と certified な cross-protocol 性能比較 1 対 (paper-story 2026-09-17 §8 C-1「性能比較 0 件」、D1373 関門 + D2104 項 13 保留で停止)。最小差分 = 2026-07-27 裁定 (1) の「当面」を終える裁定の記録 (phase3.md 改訂 + decisions) と、pin 非依存で進められる準備の T 起票。論文への効果 = システムの主張 (workload ごとに certified な variant を合成・選択できる) を silo 1 例から 2 protocol へ広げる足場を「将来スコープ C」から「必要条件 B」へ移す。

**scope (docs-only、実装面 0 byte):**
1. 回答: silo 固定は生きている — (裁定) phase3.md 2026-07-27 改訂 (1)、失効宣言なし。(実装) genome 空間は 2026-09-02 に tictoc/cicada 登録済み・較正 4 件・within-run floor 登録済み (D2083) だが between-run は D1373 関門で未実測、mocc hook は pin 511c9538 の祖先でない、性能比較 0 件、D579 で mocc は変異探索面外。(論文) paper-story 2026-09-17 は C-1 を「Silo 固定した以上、必要条件ではない」と将来スコープに置く。
2. 裁定パッケージ (段 4 で親が確定、ユーザー発話 3 件を一次資料に): (a) 2026-07-27 裁定 (1) の「当面」終了 — 合成対象 protocol の拡大 (mocc を 2 例目) と C-1 を論文必要条件 B 群へ。裁定 (2) (8b selector の優先度下げ) は据え置き。(b) 段 7 発火条件を「8b+層3 後」から付け替え。(c) D2104 項 13 の再裁定 — pin 前進を「主経路完了まで保留」から「D1603 材料 3 点が揃った時点で再承認を諮る」へ。(d) 順序 A→B。
3. docs 変更: phase3.md (2026-09-17 改訂節、段 7 発火条件、見送り台帳 T-167 の状態語)、spool fragment (D 1 件、worklog 1 件、T 起票 = pin 非依存の準備鎖)、paper-story README「最新スナップショット以後に確定したこと」1 項。

**確定済みユーザー裁定 (触らない):** 2026-08-11 T-755 Q1〜Q3 (a) = trace-hook 移植だけが certified 比較、stock 専用経路は偵察でも解禁しない (D1360)。D1373 関門は迂回も緩和もしない (D2083 項 4)。D1603 = pin 前進は材料 3 点が揃えば前進してよい。D579 = mocc を変異探索面へ入れる wave は独立の auditor-live 相当の機械実証を別途用意する。

**不変条件:** 絶対規律 2 (正しさゲート不変)、規律 7 (現行 pin との差だけを理由に過去測定を無効にしない)。roadmap 本体 (§9 E の順序文) は改訂しない — 2026-07-27 改訂と同じく phase3.md 改訂 + decisions 記録に留める。

**(P1) 親の provisional 裁定・攻撃対象:** 順序 A (mocc を 2 例目の certified 合成対象にする基盤) → B (CCBench へ近年手法を追加) とし、B は A の道具立てが protocol 汎用になるまで着手しない。理由 = DW-G03 の精神 (一般化には独立 2 例)、B を先にすると silo 専用の道具立てのまま 2 つ目を手で開通し費用が二重になる、B の候補選定は停止中の文献調査 (D1760 / D1931) の再開を要する。
**(P2) 攻撃対象:** D2104 項 13 の理由「主経路 (A-1/A-2/H1H2) は現行 pin で設計」は、pin 前進が主経路の凍結物 (事前登録・campaign.lock identity) を実際に無効化するか path で示されていない。D297 の同一性検査で silo の TRACE=0 前処理出力が同一なら束縛は内容ハッシュへ移せる (規律 7) のではないか。
**(P3) 攻撃対象:** cross-protocol 2 例目は本当に論文のパンチを強めるか — silo+mocc で言える主張の文面と、言えない主張 (10 protocol 選択、descriptor 駆動の因果) の線引き。
**(P4) 攻撃対象:** roadmap §9 E「以上の後に判断」の順序を phase3.md 改訂で前倒しすることが roadmap 改訂セレモニーを要するか。

**成果物の形:** docs-only。変異 matrix 免除 (DW-S04)、受入全走は実施。**並列分割:** 段 2 plan 1 本 (read-only codex、file:line で改訂箇所と T 鎖)、段 3 レンズ 2 本 (A = 論文価値・主張の線引き、B = 主経路衝突・pin 前進の実害・pin 非依存項の実在)。実装子なし (親が docs 本文を編集)。
**受入環境:** login node、worktree checkout、`tools/dev_wave_wait.py acceptance --lease-optional`。
**模擬/実の差:** 本 wave は計測ゼロ。pin 前進の可否は実測せず裁定の付け替えに留める。
