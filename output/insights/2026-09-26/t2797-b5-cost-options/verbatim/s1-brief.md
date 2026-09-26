# 段 1 brief — [T-2797] B-5 本走の計算費用削減案の比較 (提示のみ)

- 研究前進: B-5 生成器対照 (論文の LLM 必要性の図 1 枚) を、ユーザーが受け入れられる node 時間で完走可能か判断できる材料を出す。完了判定 = 案 (1)(2)(3) ごとに「図 1 枚あたり node 時間」「統計の強さへの影響」「429 を含む所要」を実測/換算/試算を分けて insight に置き、ユーザー裁定待ちの問いを 1 本に絞って提示する。
- scope: 読み取りと集計、insight・spool fragment の記録。本走 job・校正 job・実装は無し。計算ノード実測は T-2850 と重複しない B-5 固有分だけ、合計 < 2 node h。
- 確定裁定: D2227 項 2 (本走認可、k = 3、上限 680.7 h)。2026-09-26 ユーザー差し戻し「図 1 枚に 680 node 時間はありえない」。/rulings 第 35 回は本件を載せない (こちらで問う)。
- 不変条件: 規律 2 (legacy 1 + 性能 trace 5、anomaly 即 reject、bench 前の検証) を緩める案を出さない。trace 本数を減らす案は勧めない。仮想リスク向けの gate・検査・台帳・一般化は足さない。n・B 等の改訂は事前登録の改訂としてユーザー判断に回す。
- 覆す新事実 (段 4 で再裁定): (P1) 現行 cohort b5-registered-v1 は block 1 stage 1 の時点で、report の規則上 6 比較すべてが indeterminate-missing (LLM 4 系列が 429 → proposal-wait-timeout で score なし、wh random 2 系列が stock-unestablished)。「費用を削って続行」ではなく「新 cohort か、v1 の再開解釈か」が先の問いになる — 親の provisional 裁定・攻撃対象。
- (P2) 事前登録 §4.1 は評価ごとに単回呼出しで、同機体・同 job を要求するのは系列開始 stock と最初の評価だけ。§11 は親の待機・LLM 時間を別欄とする → 案 (1) は事前登録の改訂でなく発効束の実行契約の改訂で足りる — 攻撃対象。
- (P3) trace の取得は直列・専有のまま、取得済み trace の検査だけを並列化するなら、検査対象 (interleaving) は変わらない — 攻撃対象。
- 出発点の実測: b1-s1 12 job の Elapse 計 126,426 s。非 LLM の検証割合 95.0 %。read-heavy 1 session 585〜2,289 s。LLM 待ち 1 機会 255〜1,021 s。429 まで完了機会 22。
- 成果物: output/insights/2026-09-26/t2797-b5-cost-options/README.md (+ data/*.tsv)、worklog / decisions fragment、[T-2797] 項に「ユーザー裁定待ち」。
- 受入・実測環境: 受入は Pegasus 計算ノード (worklog の所在どおり)。docs-only のため変異 matrix は免除、受入全走は行う。
- 分割: 子は verifier 構造の調査 1 本 (Explore, sonnet) と、段 6 相当の独立 read-only レビュー 1 本 (codex)。
