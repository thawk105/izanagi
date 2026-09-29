# [T-2872] 段 1 brief (親) — 2026-09-29

**研究前進:** 論文の比較表に残す MOCC read-heavy cell (D2277 項 2「普通に使う・修理もする」) の stock G2 (3/109) を、修理可能な本体欠陥か計器の誤記録かに切り分ける。完了判定 = 下の判定規則のどれに落ちたかを insight に構造化し、本体欠陥なら修理方針を次の一手に書く。

**scope:** 切り分けだけ。CCBench の修理・pin 前進・上流送信は含めない (T-2854 と transaction.cc が重なる、D16)。VHash wave 所有の `orchestrator/campaign/condition_meaning_gate.py`・`screening_driver.py` は非接触。verifier・判定・受理集合・gate・台帳は変えない (規律 2、DW-G05)。repo の実装面の変更 0 (probe・patch・runner は job dir、Codex author、D95)。

**確定済みユーザー裁定:** D2277 項 2 (切り分けは AI 手番、観測者効果の小さい計器、既往 T-2774 §7・T-2779 §3)。t2849・t2868 の値は pin C 上の測定として有効 (規律 7)。計算は 1 タスク合計 2 node 時間以上でユーザー確認 (Elapse 実測単価)。

**純増 (既存被覆の検索結果):** 既往の計器 (T-1943 witness・T-2798 軽量 witness) は全部 TRACE=1 上の payload 出所識別で、G2 の出た反復で一度も発火していない (識別対象 0)。T-2779 の診断 patch は 2 変更を束ねた受理集合縮小で、機序を観測していない。**trace 無し build での直接観測と、witness ごとの独立経路での突き合わせは未実施** — これが本 wave の純増。D2186 項 7 の「軽量 witness 追加実験の見送り」は、D2277 項 2 の修理指示で再訪条件 (certified 系列が要る) が成立したと読む。

**機序の導出 (親の provisional、攻撃対象):**
- (P1) pin C `cc/mocc/transaction.cc` validation の read set 走査は、版の load (1035-1036) → 比較 → lock 状態の load (1049 `ldAcqCounter() == W_LOCKED`) → `max_rset_` 更新で版を再 load (1062)。2 取引の rw 閉路 T1(read x, write y)・T2(read y, write x) が両方 commit するには、**一方の validation の [版 load, lock load] の間に、相手が当該 key を publish (1259) し unlock (1271) し終えていることが必要** (場合分け: T1 の lock load が T2 の x 施錠より前なら T2 側に、T2 の unlock より後なら T1 側に窓が要る)。温度の高い record は read lock で守られるので窓は楽観読みの record だけ。
- (P2) 計器 (診断 patch、独自 macro で compile 時除去、macro off の前処理後 source は pin C と同一): read set 走査で (a) 版 load の直前に lock 状態を 1 回 load (L0、新規 load 1 つ)、(b) 1062 の再 load を local に受けて比較 (新規 load 0)。commit した取引について「L2 が未施錠で V3≠V1」を hit、うち「L0 が他者の W_LOCKED」を strict hit と数え、(thid, commit epoch, commit tid, key, V1, V3, class) を thread ごとの固定長配列へ。abort した取引の hit は捨てる。出力は run 終了後。
- (P3) 予測 (結果を見る前に固定): (iii) の機序 (a) が正しければ、TRACE=1 の各 G2 witness について片側に一致する hit (同 thid・同 commit 版・同 key・V1=witness の読んだ版・V3≥上書き版) が必ずある。
- (P4) 観測者効果: probe は 検査済み read item あたり load 1 + 比較 2、hit 時だけ store。TRACE=0 の probe あり/なしの commit 数で量る。

**判定規則 (事前登録):**
- R1 TRACE=0 probe arm で strict hit > 0 → 「trace 無しで、Silo の単一 word 検査なら拒否される commit が実際に起きる」(機序 (a) の実在)。0 なら (a) は trace 条件でしか観測されない。
- R2 TRACE=1 probe arm の G2 witness 全件に (P3) の一致 hit → witness は trace と独立な観測で裏付けられ (iv) 記録誤りは当該 witness で否定、(iii) に帰属。
- R3 一致 hit の無い witness が 1 件でもある → その witness は機序 (a) で説明されない (iv か別機序)。(iii) を全体の結論にしない。
- R4 TRACE=1 arm の G2 が 0 件 → 帰属は未達。R1 だけを書く。

**成果物:** insight `output/insights/2026-09-29/t2872-mocc-g2-split/README.md` (`output/README.md` 形式、CCBench 所見の構造化・修理方針)、worklog fragment、job dir に patch・runner・全出力。

**実測環境:** Pegasus 計算ノード gen_S (48 core、128 GiB)、generic dispatch。smoke 1 job で単価 (Elapse) を測り、本走が 2 node 時間以上ならユーザー確認。verifier は 1 回 RSS 約 17 GB・116〜168 s なので、各 round で benchmark を全部走らせた後に T arm の trace だけ 4 並列で検査 (benchmark と verifier を重ねない)。trace は `/scr`、G2 の反復だけ保全。

**arm (同一 block で round ごとに順番を回す):** T = TRACE=1+probe (verifier あり)、N = TRACE=0+probe、P = TRACE=0 素 (観測者効果の対照)。build 条件は比較 harness の stock (pin C、genome `mocc|BACKOFF_FIXED=-1,BACK_OFF=1,KEY_SORT=0,TEMPERATURE_RESET_OPT=1`、template patch、同じ compiler・define)。workload = 48 thread・1,000,000 record・rr95・rmw 0・max_ope 10・zipf 0.9・3 秒。

**分割:** 段 2 plan (read-only 1 本: harness の build argv の抽出、runner の差分、patch の挿入行)、段 3 相談 2 本 (A 機序導出と判定規則の正しさ、B 過剰・費用・観測者効果)、段 5 Codex author 1 本 (patch + runner、repo 外へ退避)、段 6 レビュー 1 本 (事実の再抽出)。変異 matrix は repo 実装面の差分 0 で免除、probe の機構は selftest の正例・負例 (合成した interleaving) で確かめる。
