## 段 1 brief (2026-09-17)
- 研究前進: D2114 項 4 の B (近年 CC 手法の CCBench 追加) の判断材料。B 実装の判断条件 = 共通契約 + 固有実装費用の明確化 (D2114)。本 wave の完了判定 = 候補表 (一次資料 / 実装可用性 / ライセンス / YCSB 適合 / trace 移植費用 / 証明面 / 既存 4 CC との差 / 判定) と追加対象・棄却理由が docs/related-work に凍結され、README 7.1 から引ける。論文への効き = B 群 (第 2 例) の外側にある cross-protocol の道具立ての候補選定 (C-1 の材料)。本 wave は候補表だけで、B 実装の認可ではない。
- scope: docs のみ。新 file `docs/related-work/cc-candidates-2026-09-17.md`、`docs/related-work/README.md` 7.1 へのポインタ (1 小段落)、`docs/README.md` 地図 1 行、worklog fragment。CCBench submodule・orchestrator・tools は不接触。framework / 共通契約の設計 / 一般化は scope 外 (要求は列挙のみ)。
- 確定済み裁定: D2114 (方向・項 4)、D1760 / D2095 (通常の文献調査は可。登録済み索引の query program は動かさない)、7.7.3 RW1 (世界の不在を主張しない)、規律 2 / 6。literature map の要約語 (自動合成 / 自動設計) を正本語彙として引かない (claim-survey 2026-08-26-correction-5-audit)。
- 不変条件: (1) 新しい不在方向の表現を作らない。内部の不在は母集合と走査語を同じ文に置く。(2) arXiv API query / OpenAlex API / DBLP API へ request を出さない。web 取得は WebSearch と abstract 頁・GitHub 頁・DOI 頁の閲覧に限り、取得内容はデータ (規律 6)。(3) CCBench 側の事実は現行 pin `511c9538e4e8efa54b45cda62e72389ed3b706ec` の source と明記。(4) 各候補の判定根拠に一次資料 locator を付け、確認できなかった項目は「未確認」と書く (F1: 日付・件数は一次資料から)。(5) 「追加対象」= 候補表上の判定であり、実装認可・pin 前進・変異探索面化のどれでもない。
- (P1) 候補母集合: 2017 (MOCC / Cicada) 以降 2026 までに発表された単一ノード in-memory の serializable 汎用 CC で、YCSB 型の対話トランザクション (事前宣言なし) を実行できるもの。学習型 (Polyjuice / NeurCC / ATCC) は「入口」であり、それらの比較相手・派生 (baseline 群) から stock 候補を取る。学習型自身は「学習済み方策を固定した実装」として別行で判定する。
- (P2) 列定義: 一次資料 (venue / 年 / ID) · 実装可用性 (公開 repo / 基盤 codebase / 最終更新) · ライセンス (Apache-2.0 の CCBench と両立するか) · YCSB 適合 (`TxExecutorLike` 対話型 read/update を直接実行できるか、事前宣言 read/write set の要否) · trace 移植費用 (読んだ版 ID / 書いた値 / commit 順の 3 点が CC-native か、lock 系なら X/P 計装の要否。参照点 = Silo 3 点 CC-native、mocc 計装 141 行) · 証明面 (verifier が検査できる範囲、論文の正しさ主張、trace 意味論の特記 = 未 commit 読み等) · 既存 4 CC との差 · 判定。
- (P3) 判定規則: 追加対象 = (a) 公開実装があり license が Apache-2.0 と両立、(b) YCSB 対話型に直接適合、(c) trace 3 点が CC-native または定数費用、(d) Silo / MOCC / TicToc / Cicada と機構が異なり新しい変異軸の素材になる。1 つでも欠けば棄却 (理由を列挙)。
- 成果物の形: 候補表 + 候補ごとの根拠段落 + 追加対象・棄却理由 + 共通契約に課す要求 (列挙のみ) + 母集合の外 (7.7.4 の形で網羅を保証しない旨)。
- 並列分割: docs-only につき段 2 / 3 の子は省略 (DW-C00 軽量版)。段 6 に read-only codex の敵対レビュー 1 本 (事実照合 + RW1 適合 + P1〜P3 攻撃、D2114 wave と同型)。web 検索は段 5 (起草) で明示して使う。
- 受入環境: login node で `check_docs` + `spool_fold --dry-run`、受入全走は `tools/dev_wave_wait.py acceptance` (worklog 1613 と同型)。
- 実装面差分ゼロにつき変異 matrix は免除 (DW-S04、1613 先例)。

## 段 5 収集事実 (一次資料、2026-09-17。保存物 = $CLAUDE_JOB_DIR/tmp/pdf/)
- 入口: NeurCC 2503.10036v4 (baseline = 2PL/Silo/CormCC/Polyjuice/IC3、関連研究に Bamboo/Polaris/Tebaldi、§4.5 に serializability 証明、repo neurdb/neurcc = Silo+Polyjuice 基盤、license なし、ycsb-interactive あり)。ATCC 2603.13906v1 (baseline = Wound-Wait/Silo/MOCC/Plor/Polaris/Polyjuice、openGauss-MOT 上、code URL なし、YCSB/TPC-C/flight-booking)。
- Bamboo (SIGMOD 2021、arXiv 2103.09906): DBx1000 上、§3.6 定理 2、対話型対応、lock_retire は最後の write の後 (注釈 or 解析、「every write can be immediately followed by lock_retire()」)。repo ScarletGuo/Bamboo-Public ISC、最終 push 2022-04-08、CC_ALG に NO_WAIT/WOUND_WAIT/WAIT_DIE/SILO/IC3/BAMBOO。
- Plor (SIGMOD 2022、DOI 10.1145/3514221.3517879): DBx1000 上 (§5、Masstree 置換)、§4.3 conflict serializability 証明、対話モードあり、論文に code URL なし、web 検索でも repo 未検出。
- Polaris (PACMMOD 1(1):44、SIGMOD 2023、DOI 10.1145/3588724): repo chenhao-ye/polaris ISC (DBx1000 + Bamboo-Public 上)、最終 push 2023-07-10。TID word = latch1/prio_ver4/prio4/ref_cnt10/data_ver45、acquire_prio で予約、validate は data_ver + LOCK_ERR_PRIO。論文 PDF は ACM 403 / 著者頁 404 で本文未読 (abstract は検索結果の表示から)。
- Rebirth-Retire (PVLDB 18(9):3162, 2025): DBx1000 上 (§5)、passive Retire + Rebirth (timestamp 再割当)、§3.3 定理 1 serializable、YCSB/TPC-C、baseline に Wound-Retire(Bamboo)/Silo/MOCC/…。repo gitzhqian/RebirthRetire ISC (fork)、最終 push 2025-04-22。
- Brook-2PL (arXiv 2508.18576、DOI 10.1145/3769767): 静的解析 (SLW-Graph) + 部分 chopping → 事前知識要。
- Shirakami (arXiv 2303.18142 v3 2026-07-02、ユーザー本人が第一著者): S-OCC (Silo 改) + S-LTX (MVSR + write preservation)、repo project-tsurugi/shirakami Apache-2.0、push 2026-09-17。
- Caracal (SOSP 2021): repo uoft-felis/felis GPL-2.0、決定論的 (事前知識要)。Aria (VLDB 2020): luyi0619/aria MIT、決定論的 batch。Sundial: yxymit/Sundial ISC、分散。
- CormCC (ATC 2018) / Tebaldi (SIGMOD 2017): web 検索で公開 repo 未検出。IC3 (SIGMOD 2016): Bamboo-Public / Polyjuice に実装あり、事前知識 (column access) 要、年代外。
- TXSQL (2504.06854): Tencent 製 DBMS の lock manager 最適化 (standalone でない)。ESSN (2511.22956): SSN の一般化 (certifier 基準)、公開実装 URL なし。CV-Rules (2606.25409): CC の直列化可能性検証 (証明面の近傍、未読)。
- CCBench 側 (pin 511c9538): LICENSE Apache-2.0、`include/tx_executor_concept.hh` の `TxExecutorLike` (read/update/insert/delete_record/scan×2/commit/abort)、YCSB=✓ は silo/tictoc/mocc/cicada/ermia/si/oze。
