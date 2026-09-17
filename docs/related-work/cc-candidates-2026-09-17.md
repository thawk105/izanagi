# 近年 CC 手法の候補表 — CCBench への実装追加 (B) の判断材料 (2026-09-17 凍結)

> **これは D2114 項 4 の「B の候補調査」の成果物であり、[T-2758] で作った。** 判断材料 (候補表・優先調査候補・
> 保留・棄却とその理由) を提示するだけで、**CCBench への実装追加・pin 前進・変異探索面への追加のどれも認可
> しない** (それぞれ D2114 項 3、D1603 / D2104 項 13、D579 の手続きに従う別件)。共通契約の設計・一般化も本書の
> 外である (D2114 項 4 の「要求を共通契約へ反映する」は、§6 の確認課題を入力にした別の作業)。
> 本書は日付付きの凍結物で、上書きしない。改訂は新しい日付の file で行う (`claim-survey/` と同じ原則)。
>
> **本書は関連研究の「内部の調査記録」であり、7.7 の主張軸の調査状態を変えない。** 世界の不在は主張しない
> (軸 1 は `RW1`、7.7.3)。「未確認」と書く箇所は「今回の提供資料と走査で確定できなかった」の意味であり、
> 不在の主張ではない。web 取得した論文本文・README・API 応答は規律 6 のとおりデータとして扱った。
> 登録済み索引の query program (D2095 の軸 1) は動かしていない — 取得は abstract 頁・著者頁・公開 repo の
> README / source / LICENSE・GitHub REST API (匿名、metadata と root 一覧) の閲覧に限った。
> 段 6 の敵対レビュー 1 本 (read-only codex) の所見と是正の対応は
> `output/insights/2026-09-17/t2758-recent-cc-candidates/README.md` に凍結した。

| 入力 | 値 |
|---|---|
| 入口 | `README.md` 7.1 の literature map: NeurCC `2503.10036` (v4、SIGMOD 2026) / ATCC `2603.13906` (v1、2026-03) |
| CCBench 側の事実の版 | 現行 pin `511c9538e4e8efa54b45cda62e72389ed3b706ec` (`external/ccbench`)。superproject の base = `38353207f` |
| 文献 cutoff | 2026-09-17 (取得日と同じ) |
| 一次資料の保存 | 論文 PDF / README / LICENSE の取得物は job dir に置いた (repo 外、生存保証なし)。本書は locator (arXiv ID・DOI・repo path) を持ち、判定に使った逐語は本書内に写した |

---

## 1. 候補母集合の作り方 (P1)

1. **入口の比較相手群**: NeurCC の実験 baseline = 2PL / Silo / CormCC / Polyjuice / IC3、関連研究に Bamboo /
   Polaris / Tebaldi (HTML 版 `2503.10036v4` の抽出要約)。ATCC の実験 baseline = Wound-Wait / Silo / MOCC / Plor /
   Polaris / Polyjuice (HTML 版 `2603.13906v1` の抽出要約)。
2. **候補の論文が baseline に挙げた手法**: Rebirth-Retire の baseline として Wound-Retire (Bamboo) / Silo / MOCC /
   TicToc / DL_DETECT / Wound-Wait を確認した (`rr.txt` §5)。Bamboo は Rebirth-Retire の fork 元でもある。
3. **web 検索 (WebSearch、2026-09-17)** で 2024〜2026 の単一ノード in-memory CC を補った。走査語は
   「concurrency control in-memory OLTP hotspot contention SIGMOD/VLDB 2024/2025」「SIGMOD 2025 / VLDB 2025 /
   SIGMOD 2026 in-memory concurrency control protocol hot records optimistic serializable multicore」
   「arXiv cs.DB 2025 2026 concurrency control in-memory YCSB TPC-C optimistic pessimistic hybrid」の 3 系統。
   **この検索で把握した候補を記録する。検索結果全件を再現できないため、追加候補の不在は結論しない。**
   把握した題名と扱いは次のとおり (表の行にしなかったものの除外理由をここに残す):
   - 表に載せた: Rebirth-Retire、Brook-2PL、TXSQL、ESSN。
   - 題名の「Deterministic」から決定論的と分類し P1 の条件 (対話型) 外とした: ForeSight (`2508.17375`)、Dodo
     (FGCS 2024)、Gria (FCS 2023)。本文は未読で、batch・事前宣言の詳細は未照合。
   - 包含判断を保留: 「A Hybrid Approach to Integrating Deterministic and Non-Deterministic CC」(VLDB 2025) は
     題名しか確認しておらず、実行要件 (batch・事前宣言) は未照合。
   - protocol でない: TxnSails (VLDB 2025、isolation level の選択)、CV-Rules (`2606.25409`、CC の検証手法、未読)。
   - 実行環境が対象外: Focus! (DOI `10.1145/3769793`、on-disk)、GPU-Accelerated OLTP (`2406.10158`)、
     Epoch-based OCC in Geo-replicated DB (`2602.21566`、分散)。
4. **母集合の条件**: 2017 (Cicada / MOCC の会議年。MOCC の PVLDB 掲載は 2016 表記) 以降に発表され、単一ノード in-memory で serializable を
   主張し、YCSB 型の対話トランザクション (read / update を 1 op ずつ発行、read / write set の事前宣言なし) を
   直接実行できる単一の汎用 CC。条件を満たさないものも表に残し、除外理由を書いた。
   IC3 (2016) は年代外だが入口 2 本の baseline なので表に残した。
5. **一次資料の関連研究節に現れ、候補に含めなかった名前** (列挙のみ): CCBench 既存系 = Silo / TicToc / MOCC /
   Cicada / ERMIA (SSN) / Oze / ss2pl / mvto / d2pl / si、DBx1000 既存の CC_ALG = NO_WAIT / WAIT_DIE / DL_DETECT /
   TIMESTAMP / MVCC / HSTORE / OCC / VLL / HEKATON、年代外 = Hekaton / FOEDUS / Calvin / ELR / CLV (Bamboo §6、
   Plor §7 の引用)。**年代内で包含判断を保留する名前**: DTA (2018、`rr.txt` 参考文献)、DRP (EuroSys 2019、
   `bamboo.txt` 参考文献。tame transaction の事前知識要件が本文に見えるが全体の包含判定は未照合)、Shirakami の
   参考文献にある OSDI 2024 の多版並列処理 (protocol 名は未照合)。SLOG (2019) は分散として対象外。Strife は
   NeurCC の関連研究に未登場と確認しただけで、検索で得た候補としては数えない。

**母集合の外 (網羅を保証しない):** SIGMOD / PVLDB / OSDI / SOSP / EuroSys / ATC の年次一覧の全走査、ACM DL、
DBLP、OpenAlex、arXiv API の検索、書籍・技術報告・学位論文・非英語文献、索引化されていない実装。
分散 CC (Sundial / Morty / Lotus / Cornus 系) と GPU / NVM / ディスク特化 CC は対象外で、表には代表 1 件
(Sundial) だけを対照として残した。

---

## 2. 列の定義 (P2) と判定規則 (P3)

CCBench 側の事実は現行 pin の source から取った。

- **一次資料**: venue / 年 / arXiv ID または DOI。本文を読めなかったものは「abstract のみ」または「検索結果の
  表示のみ」と書く。
- **実装可用性**: 公開 repo、基盤 codebase、最終 push (GitHub API `pushed_at`、2026-09-17 取得。最終 code 変更日
  とは限らない)。
- **ライセンス**: CCBench は Apache-2.0 (`external/ccbench/LICENSE`)。ISC / MIT は Apache-2.0 の tree へ
  取り込める permissive license、GPL-2.0 は取り込めない (copyleft)。法的助言ではなく、実装追加の段で LICENSE 文の
  同梱・著作権表示の要件を確認する。
- **YCSB 適合**: CCBench の protocol は `include/tx_executor_concept.hh` の `TxExecutorLike`
  (`read` / `update` / `insert` / `delete_record` / `scan` 2 種 / `commit` / `abort`) を満たし、workload 層
  (`include/ycsb.hh`) が op を 1 つずつ発行する。**事前宣言 (read / write set、transaction template の静的解析、
  batch) を要する手法は YCSB 対話型に直接適合しない。** YCSB を持つ現行 protocol は silo / tictoc / mocc /
  cicada / ermia / si / oze の 7 つ (`cc/<p>/CMakeLists.txt` の `WORKLOADS`)。候補側の「対話型を評価した」は
  論文の実験モードの事実であり、CCBench の対話 API へ直接載ることの確認ではない。
- **trace 移植費用**: verifier が要る 3 点 = 各 read の (key, 読んだ版 ID, その版を書いた tx)、各 write の
  (key, 値)、global な commit 順 (`ccbench-anatomy.md` §4)。参照点: Silo は 3 点とも CC-native (Tidword /
  WriteElement / maxtid)、cicada も CC-native (`Version::wts_`)、**ss2pl は版 ID を持たないので trace 専用
  field が要る** (同 §4)。lock 系はさらに lock 被覆 (X 行) と permutation (P 行) の `#if TRACE` 計装が要り、
  mocc の実費は `cc/mocc/transaction.cc` へ 141 行追加 (hook branch 先端 `e9e477ca1b55…` と現 pin の diff、
  `output/insights/2026-09-17/cross-protocol-scope-release/README.md` §4)。D14 の契約 (性能 build から完全
  除去、`#line` 復元) と D1373 の関門 (SOURCES に列挙された file に `#if TRACE`・`trace.hh` include・
  `izanagi_trace::next_txid()` の 3 証拠) は新規 protocol にもそのまま掛かる。**費用は定性 (低 / 中 / 高) の
  見積りで、単位 (record 当たり・版当たり・trx 当たり・開発工数) を分けていない。**
- **証明面**: 論文が示す正しさ主張 (証明の有無と主張する基準)、verifier が trace から検査できる範囲、
  trace 意味論の特記 (未 commit 版の読み、timestamp の再割当、複数版)。**現行 trace は committed trx だけを
  記録し、G1a / G1b (dirty read 系) は観測できない** (`isolation-phenomena.md`)。
- **既存 4 CC との差**: Silo (単版 OCC) / MOCC (OCC + 温度で選択的 2PL) / TicToc (timestamp OCC) / Cicada
  (MVCC) と機構がどう違うか (親の技術的解釈)。**差が「Silo の 1 箇所の改変」に収まるものは、stock として持つ
  より izanagi の変異 (EVOLVE-BLOCK) の到達点候補として意味がある** — この観点は判定に書いた。
- **判定規則 (P3)**: 追加対象の条件は (a) 公開実装があり license が Apache-2.0 と両立、(b) YCSB 対話型に直接
  適合、(c) trace 3 点が CC-native または trace 専用 field と X/P 計装までの定数費用、(d) Silo / MOCC / TicToc /
  Cicada と機構が異なり新しい変異軸の素材になる。**各条件は「充足確認 / 不適合確認 / 未確認」で記録する。
  追加対象の確定には四条件の充足確認を要し、不適合を確認した候補は理由付きで棄却する。未確認を含む候補は
  保留とする。本調査での優先調査候補と、条件を確認済みの追加対象を区別する。trace 費用の単位・内訳と
  変異軸の採否基準は未確定であり、定性的な見積りだけでは (c)(d) の充足としない。** したがって本書の判定は
  P3 内では「優先調査候補 / 保留 / 棄却」の 3 分類で、「追加対象 (確定)」は 0 件である。別に P1 の母集合外
  (学習型・分散・engine 内最適化・certifier 基準・単一 protocol でない) を記録し、これは P3 の前に落とす
  (表の最上位分類は 4 つ)。

---

## 3. 候補表

判定 cell の記法: `a=確認` は充足確認、`a=×` は不適合確認、`a=?` は未確認 (b〜d も同じ)。

| 候補 | 一次資料 | 実装可用性 | ライセンス | YCSB 適合 | trace 移植費用 | 証明面 | 既存 4 CC との差 | 判定 |
|---|---|---|---|---|---|---|---|---|
| **Rebirth-Retire** | PVLDB 18(9):3162-3174, 2025 (`vldb.org/pvldb/vol18/p3162-zhang.pdf`、本文精読) | `gitzhqian/RebirthRetire` (Bamboo-Public の fork、DBx1000 基盤、push 2025-04-22)。README の対応 protocol = DL_DETECT / Wound-Wait / Bamboo / Silo / Rebirth-Retire / TicToc / MOCC。`config-std.h` の define 集合は Bamboo-Public と同一で `CC_ALG` 既定は `BAMBOO`。両者を切り替える実装経路は未照合 (source 未読) | ISC (LICENSE file 実在、Bamboo-Public と同文) | 論文の評価は stored-procedure mode (§5)。read / write set の事前宣言は algorithm 上不要 (§3) だが、対話型での評価は未確認 | **中〜高、未確定**: retire 後の未 commit 版を読み、`rr.txt` §4.4「a tuple may have multiple versions」「transactions are allowed to read the corresponding version based on their timestamps」→ 単版ではない。実際に読んだ版と producer、最終版との区別、abort 後の復元、commit 順 (Rebirth で timestamp が動く) との対応を保持できるかは未確認。lock 系なので X/P 計装も要る | §3.3 定理 1「Every schedule in Rebirth-Retire is serializable」。未 commit 版の読みを現行の committed-only trace で検査できるかは未確認 (§6 項 3) | MOCC と同じ「hot / cold で振る舞いを変える」動機を lock 側から解く (passive retire + timestamp 再割当、親の解釈)。OCC 系 3 つとは機構が別 | **優先調査候補** (a=確認 b=? c=? d=?) |
| **Bamboo (Wound-Retire)** | SIGMOD 2021 / arXiv `2103.09906` (Extended Version、本文精読)、DOI `10.1145/3448016.3457294` | `ScarletGuo/Bamboo-Public` (DBx1000 基盤、push 2022-04-08) | ISC (LICENSE file 実在) | ✓ 対話型・stored-procedure 双方を評価 (§1)。CCBench の対話 API への直接適合は未照合 | **中〜高、未確定**: 上と同じ。`lock_retire()` の位置は注釈または解析 (§3.3「every write can be immediately followed by lock_retire()」) — ただし retire 後に同じ tuple を再 write すると、最初の write を読んだ trx を abort する処理が要る (§3.3)。§3.5 最適化 3「multiple uncommitted updates can exist on a tuple」 | §3.6 定理 2 (committed trx の schedule は serializable)。reader の commit は writer の成功後に限られる (§3.1「T2 is able to commit only if T1 has successfully committed」) | 2PL の early lock release + dirty read 追跡。既存 4 CC のどれとも別系統 | **優先調査候補 (対照候補)** (a=確認 b=? c=? d=?)。Rebirth-Retire と同じ移植で対照を用意できるかは未確認、一般的な性能劣後も断定しない |
| **Polaris** | PACMMOD 1(1):44 (SIGMOD 2023)、DOI `10.1145/3588724`。**本文未読** (ACM 403・著者頁 404)、abstract は検索結果の表示、機構は公開 source から | `chenhao-ye/polaris` (DBx1000 + Bamboo-Public 基盤、push 2023-07-10、ARTIFACT.md あり) | ISC (LICENSE file 実在) | ✓ YCSB / TPC-C (`config-std.h` `WORKLOAD`)。CCBench の対話 API への直接適合は未照合 | **低い可能性があるという仮説 (候補間順位は確定しない)**: Silo の 64-bit TID word を `latch 1 / prio_ver 4 / prio 4 / ref_cnt 10 / data_ver 45` に再分割 (`row_silo_prio.h`)。読んだ版 = `data_ver` (`get_data_ver()` の戻り型は `uint32_t`、45-bit との関係は未照合)。commit ID の生成・一意性・producer 復元は未照合。X/P は OCC なので不要と見込む (未照合) | 論文の証明は未読。保存 source の `validate` は write set 外の locked record を拒否し、`data_ver` の一致を検査する (priority は検査しない)。priority による `LOCK_ERR_PRIO` は `lock` / `try_lock` が返す。呼出側の abort 処理、既存 trace への対応は未照合 | 保存 source では TID word、`lock` / `try_lock`、`reader_release` / `writer_release_abort` / `writer_release_commit` に priority 関連処理がある。Silo との差分全体と移植費用は未照合であり、変更範囲を access / validate に限定しない。izanagi が Silo variant として合成しうる機構という見方は親の仮説 | **優先調査候補 (対照用)** (a=確認 b=? c=? d=?)。stock としての価値は「人間設計の Silo 拡張の到達点」との対照 |
| **Plor** | SIGMOD 2022、DOI `10.1145/3514221.3517879` (著者頁 PDF 精読) | **公開実装は未確認** — 保存した本文を `github` / `available` / `artifact` で走査すると 3 行が該当し、URL を含む 1 行は依存ライブラリ concurrentqueue の参考文献だった。WebSearch 1 系統 (「Plor General Transactions with Predictable Low Tail Latency SIGMOD 2022 github」) の表示にも repo なし | 未確認 | 対話モードを実装し評価 (§5 実装、§6.2.2 評価)。CCBench の対話 API への直接適合は未照合 | 中と見積る (推論): 書きは local buffer (§1)、read / write lock に timestamp を保持 → X/P 計装 + 版 stamp | §4.3 で conflict serializability を証明 | OCC と Wound-Wait の hybrid (悲観 lock + 楽観 read、競合する trx 間で commit を timestamp 順に)。MOCC とは「hot だけ悲観」でなく全 record に lock を置く点で別 | **保留** (a=? b=? c=? d=?)。機構の追加価値はあり、実装を得られれば優先調査候補へ |
| **Shirakami (S-OCC + S-LTX)** | arXiv `2303.18142` v3 (2026-07-02)、本文精読。venue 表記なし (arXiv DOI のみ) | `project-tsurugi/shirakami` (独立 KVS、Yakushima index 依存、push 2026-09-17) | Apache-2.0 (API 分類 + README) | 部分: S-OCC は Silo 改。S-LTX は write preservation (書く storage の事前宣言) を要し、長 read-write trx の regime 向け | 高と見積る (推論): 独立 engine からの切り出し (epoch / WP / 多版 GC が一体) の可否は未照合。S-OCC の Silo からの変更は「additional WP checks … and reader-epoch metadata」(本文) | Silo 系の SERIALIZABLE (S-OCC) と MVSR (S-LTX) の併存。S-LTX の serialization epoch / order forwarding と既存 trace の commit 順による版順復元との対応は未照合 | S-OCC は Silo との差が WP 検査と reader-epoch metadata、S-LTX は Cicada / ERMIA と同じ多版だが「長 trx と短 trx の共存」が対象 — izanagi の YCSB 短 trx campaign の regime の外 | S-LTX は **棄却**: b=× (事前宣言)。S-OCC は **保留**: d=? (Silo との差が WP 検査と reader-epoch metadata であることは確認したが、d を満たさないと判定する尺度は本書に無い)。長 trx regime を campaign が扱う時に再評価 |
| **Brook-2PL** | arXiv `2508.18576` (2025-08)、DOI `10.1145/3769767` (PACMMOD)。abstract のみ | 未確認 | 未確認 | b=×: abstract の「static transaction analysis」「statically analyzing … SLW-Graph」→ transaction template の事前解析が要る (本文の代替経路は未照合) | — | — | 静的解析で deadlock-free 2PL + 部分 chopping (親の分類) | **棄却**: b=× |
| **Caracal** | SOSP 2021、DOI `10.1145/3477132.3483591`。題名と検索結果の表示のみ | `uoft-felis/felis` (push 2025-11-23) | **GPL-2.0** (API 分類) | b=?: 題名「Deterministic Concurrency Control」から決定論的と読めるが、batch・read / write set 事前宣言の詳細は未照合 | — | — | 決定論 (題名からの親の分類) | **棄却**: a=× (GPL-2.0 という API 分類は確認。具体的な取り込み形態での利用条件は別途確認)。b=? |
| **Aria** | PVLDB 13(11), 2020 (検索結果の表示のみ) | `luyi0619/aria` (push 2024-04-15) | MIT (LICENSE file 実在) | b=×: repo 記述「Deterministic OLTP Database」、Polaris ARTIFACT の「due to batching」 | — | — | 決定論 batch (親の分類) | **棄却**: b=× |
| **CormCC** | USENIX ATC 2018 (`usenix.org/conference/atc18/presentation/tang`)。検索結果の表示のみ | 未確認 (WebSearch 2 系統: 「CormCC Toward Coordination-free and Reconfigurable Mixed Concurrency Control Tang Elmore USENIX ATC 2018 source code」と「CormCC source code」の表示に repo なし) | 未確認 | 母集合外: Plor §7「CormCC [42] provides a framework for mixing different CC protocols and changing them online with minimal overhead」→ 単一 protocol ではない (原論文は未読) | — | — | 複数 CC の混在・切替 (Polyjuice の baseline という位置づけは未照合) | **母集合外 (単一 protocol でない、Plor §7 の記述に依拠)**。a=? |
| **Tebaldi** | SIGMOD 2017、DOI `10.1145/3035918.3064031`。検索結果の表示のみ (abstract 未取得) | 未確認 (WebSearch 1 系統: 「Tebaldi Bringing Modular Concurrency Control to the Next Level SIGMOD 2017 source code github」の表示に repo なし) | 未確認 | 未確認 (transaction type の階層的静的解析という理解は親の記憶で未照合) | — | — | modular CC (階層、親の記憶) | **保留**: a=? b=? |
| **IC3** | SIGMOD 2016 (年代外) | Bamboo-Public の `CC_ALG IC3`、NeurCC README の「IC3 variant」 | Bamboo-Public は ISC。Polyjuice 内部の IC3 実装への license 適用は未照合 | b=×: 「assumes column accesses of all transactions to be known before execution」(Bamboo §2.2 の引用) | — | — | transaction chopping + 依存追跡 | **棄却**: 年代外、b=× |
| **Polyjuice (固定方策)** | OSDI 2021 / arXiv `2105.10329` (実装状態は `literature-map/gap-research-2026-07-10.md`) | `derFischer/Polyjuice` (Silo 基盤、push 2025-02-11、TF 1.14 世代の訓練層) | Apache-2.0 (API 分類) | 未確認 (gap-research の記録は TPC-C / TPC-E / micro、YCSB の有無は今回未照合) | 高と見積る (推論): 方策表の解釈器ごと移植 | 学習済み方策が serializable であることは論文の設計が担う (親の理解、今回未照合) | 「事前定義したアクション空間の中の配合」(7.1 の書き分け)。学習成果物 | **母集合外 (学習型)**。入口としてのみ使う |
| **NeurCC (固定関数)** | SIGMOD 2026 / arXiv `2503.10036` v4 (§4.5 に serializability 証明、抽出要約) | `neurdb/neurcc` (Silo + Polyjuice 基盤、`ycsb-interactive` は 2PL variant 由来、push 2026-03-12) | **root 直下に LICENSE 系 file なし** (親の追加照合: GitHub API contents の root 一覧 = `.gitignore` / `Dockerfile` / `README.md` / `environment.yml` / 4 dir、API `license: None`)。子 directory 内と利用許諾全体は未確認 | `ycsb-interactive` あり (README) | 高と見積る (推論): lookup table + 特徴収集 (`learn.h/cc`) ごと移植、最適化は Python (BO) | §4.5 の証明 (抽出要約) | 学習型 | **母集合外 (学習型)**。a=? |
| **ATCC** | arXiv `2603.13906` v1 (2026-03)、抽出要約 | 未確認 (HTML の抽出要約では公開実装を確認できる URL は提示されていない。原文の全件走査ではない)。openGauss-MOT 上 | 未確認 | agentic-like YCSB / TPC-C | — | 「optimistic と pessimistic の動的適応」(抽出要約)。証明の有無は未確認 | 適応型 (入口)。「学習型」は `README.md` 7.1 の既存分類に従う。抽出要約で確認できたのは動的適応まで | **母集合外 (入口、7.1 の既存分類「学習型」に依拠)**。a=? |
| Sundial (対照) | 2018 (repo 作成 2018-04、venue・機構は未照合) | `yxymit/Sundial` (push 2020-09-25) | ISC (API 分類) | 母集合外: repo 記述「distributed OLTP database testbed」 | — | — | 分散 (親の記憶では TicToc 系の論理 lease、未照合) | **母集合外 (分散)** |
| TXSQL (対照) | arXiv `2504.06854`、SIGMOD 2025 Companion (`10.1145/3722212.3724457`、検索結果の表示) | Tencent 製 DBMS 内 (abstract「implemented in Tencent's database, TXSQL」) | 未確認 | 母集合外: engine 内の lock manager 最適化 (standalone 実装の有無は未確認) | — | — | 既存 DBMS 内の lock manager 最適化 (disk 系という分類は未照合) | **母集合外 (engine 内最適化)** |
| ESSN (近傍) | arXiv `2511.22956` (2025-11)。abstract のみ | 未確認 (abstract の抽出要約に URL なし) | 未確認 | — (certifier 基準であって protocol でない) | ERMIA への実装・置換費用は abstract に無い | MVSR を保存し SSN を真に包含すると主張 (abstract) | SSN の certifier 基準の改良 (CCBench の ermia との実装関係は未照合) | **母集合外 (protocol でない)**。ermia 系を扱う時の候補として記録 |

---

## 4. 優先調査候補・保留・棄却 (要約)

**追加対象 (四条件の充足確認済み) は 0 件。** 本調査で決められるのは優先調査候補までである。

**優先調査候補 (候補表上の判定。実装認可ではない):**

1. **Rebirth-Retire (2025)** — 本表で 2024 年以降に発表され a=確認と記録した候補は Rebirth-Retire の 1 件だが
   (本表内の数であり、世界順位ではない)、P1 の対話型直接適合は未確認である (b=?)。lock 系で hot / cold に適応する点は MOCC と動機が同じで
   機構が違うため、既存 4 CC に無い変異軸 (retire の受動化、timestamp 再割当) の素材になりうる (d は未確認)。
   費用は未確定 — 未 commit の複数版を読む protocol なので、trace 専用 field 1 個で足りるとは判断しない
   (§6 項 1)。
2. **Bamboo (2021、対照候補)** — Rebirth-Retire の fork 元で、同 README が両者を対応一覧に挙げる。
   両者を切り替える実装経路と、元の Bamboo に相当する対照を同じ移植で用意できるかは未確認。移植費用の共有や
   一般的な性能劣後は断定しない。
3. **Polaris (2023、対照用)** — 費用は低い可能性があるという仮説に留め、候補間順位は確定しない (§3)。
   保存 source では TID word、`lock` / `try_lock`、reader / writer release に priority 関連処理があり、Silo との
   差分全体と移植費用は未照合 (変更範囲を access / validate に限定しない)。izanagi が Silo variant として合成
   しうる機構という見方は親の仮説で、stock として持つ意義は「人間設計の Silo 拡張の到達点」との対照にある。
   論文本文は未読 (§5)。

**保留 (未確認の条件だけで落ちる候補):** Plor (a=? b=?、機構の追加価値あり — 実装を得られれば優先調査候補へ)、
Tebaldi (a=? b=?)、Shirakami の S-OCC (d=?)。

**棄却 (不適合を確認した候補):**

- b=× (事前知識・決定論・batch): Brook-2PL、Aria、IC3、Shirakami の S-LTX (write preservation)。
- a=× (license 非両立、API 分類): Caracal (GPL-2.0。b は題名から決定論的と読めるが未確認)。

**母集合外 (P3 の前に落とす):** 学習型 = Polyjuice、NeurCC、ATCC (入口の 3 本は候補でなく、**その baseline 群から
stock 候補を取るための入口**)。単一 protocol でない = CormCC。分散 = Sundial。engine 内最適化 = TXSQL。
certifier 基準 = ESSN。

---

## 5. 未確認事項 (読者が誤って強く読まないための注記)

- **Polaris の論文本文は読めていない** (ACM DL は 403、著者頁の PDF は 404)。機構の記述は公開 source
  (`concurrency_control/row_silo_prio.h`、`config-std.h`) から取った。証明の有無・baseline の一覧は未確認。
- **Brook-2PL / ESSN / TXSQL は abstract、Caracal / Aria / CormCC / Tebaldi / Sundial は題名・repo 記述・検索結果の
  表示までしか読んでいない。** 棄却理由が b=× の Brook-2PL / Aria は、abstract・repo 記述の文言 (static analysis /
  deterministic / batching) で決めた。本文で対話型を扱っていた場合は再評価する。
- **親の追加照合 3 件 (レビュー後、2026-09-17)**: NeurCC の root 直下に LICENSE 系 file なし、Rebirth-Retire の
  LICENSE = ISC、Aria の LICENSE = MIT。生一覧と LICENSE 本文は段 6 レビューの照合資料に含まれておらず、独立照合は
  未了 (insight の `verbatim/` に親の取得記録を残す)。
- **「未確認」はいずれも今回の提供資料と走査で確定できなかったという意味**であり、不在の主張ではない。
  著者頁・機関 repo・要求ベースの配布は走査していない。web 検索は 7.7.4 の索引ではなく、結果全件を再現できない。
- **ライセンスの読み**: ISC / MIT を「Apache-2.0 の tree へ取り込める」と書いたのは permissive license 同士の
  一般的な扱いであり、法的助言ではない。「API 分類」は GitHub REST API の `license.spdx_id` で、LICENSE file を
  読んだものは「LICENSE file 実在」と書き分けた。
- **費用の見積りは定性 (低 / 中 / 高) の推論**で、行数の実測は mocc の 141 行だけである。単位 (record 当たり・
  版当たり・trx 当たり・開発工数) を分けていない。
- **NeurCC / ATCC の本文は抽出要約 (WebFetch の小モデル要約) で読んだ**。原文の全件走査ではない。

---

## 6. 優先調査候補が共通契約に課す確認課題 (列挙のみ。設計は別件)

D2114 項 4 の「要求を共通契約へ反映する」への入力。ここでは満たすべき性質と確認課題だけを列挙し、trace の
field・event・reason、採番方式、移植先 file、workload API の追加要否は本書では決めない。

1. **未 commit の複数版を読む protocol の trace**: Rebirth-Retire と Bamboo は未 commit の複数版を読む場合が
   ある。実際に読んだ版と producer、最終版との区別、abort 後の復元、および commit 順との対応を保持できるかは
   未確認である。trace 専用 field 1 個で足りるとは判断せず、P3(c) は未確認とする。既存の D297 検査
   (`tools/check_trace0_preprocess_identity.py`) の保証範囲が SILO_SPACE の context 列挙と mocc の `trace.hh`
   1 行特例に限られる (cross-protocol insight §4) ことも、新規 protocol の trace 専用 field に対する確認課題である。
2. **lock 系の証明面**: retire 後の再 write、priority、依存関係 (commit semaphore) を損なわずに lock 被覆 (X) と
   permutation (P) を観測できることが確認課題となる。mocc の 3 検査点 (入口 / payload 直前 / publish 直前、
   `output/insights/2026-09-07/t2294-mocc-lock-instrumentation/README.md` §1) がそのまま当てはまるかは未確認。
3. **未 commit 版の読みと verifier の観測能力**: 正しい Bamboo は reader の commit を writer の成功後に制限する
   (§3.1) が、既存の committed-only trace でその違反や中間版 (writer の非最終版) の読みを検出できるとは確認して
   いない (`isolation-phenomena.md` は G1a / G1b を観測不能とする)。
4. **commit 順の採取点**: Rebirth は実行中に timestamp を再割当する。初期値・最終値・再割当履歴と、実際に読んだ版
   および既存 trace の commit 順との対応は未照合であり、採取点と識別方法を確認する (commit point は Bamboo §3.6
   定義 1)。
5. **DBx1000 由来の実装の移植**: `TxExecutorLike` の API (`update` / `insert` / `delete_record` / `scan`)、
   Masstree、gflags、epoch 管理、`Result` 集計を CCBench 側で満たす必要があり、DBx1000 の lock manager
   (`row_lock` / `row_bamboo`) をどこへ写すかを含めて固有実装費用の主部になる (配置は決めない)。
6. **priority 付き protocol の workload 層**: Polaris は priority 割当を要する。abort-aware policy
   (`SILO_PRIO_INC_PRIO_AFTER_NUM_ABORT`) は protocol 内で完結するが、固定 priority の実験に workload 側の口が
   要るかは確認課題。
7. **D1373 の関門 (既存)**: 新規 protocol も `cc/<p>/CMakeLists.txt` の SOURCES に列挙された file に `#if TRACE`・
   `trace.hh` include・`izanagi_trace::next_txid()` の 3 証拠を持たなければ between-run floor の測定に入れない。

---

## 7. 一次資料 locator

| 候補 | locator |
|---|---|
| NeurCC | `arxiv.org/html/2503.10036v4`、`github.com/neurdb/neurcc` (README、root 一覧に LICENSE なし) |
| ATCC | `arxiv.org/html/2603.13906v1` |
| Rebirth-Retire | `vldb.org/pvldb/vol18/p3162-zhang.pdf` (PVLDB 18(9):3162-3174)、`github.com/gitzhqian/RebirthRetire` (README、`config-std.h`、LICENSE = ISC) |
| Bamboo | `arxiv.org/abs/2103.09906` (Extended Version)、DOI `10.1145/3448016.3457294`、`github.com/ScarletGuo/Bamboo-Public` (branch `dbx1000-bamboo`、LICENSE = ISC) |
| Polaris | DOI `10.1145/3588724`、`github.com/chenhao-ye/polaris` (README、ARTIFACT.md、`concurrency_control/row_silo_prio.h`、`config-std.h`、LICENSE = ISC) |
| Plor | DOI `10.1145/3514221.3517879`、`storage.cs.tsinghua.edu.cn/papers/sigmod22plor.pdf` |
| Shirakami | `arxiv.org/abs/2303.18142` (v3)、`github.com/project-tsurugi/shirakami` |
| Brook-2PL | `arxiv.org/abs/2508.18576`、DOI `10.1145/3769767` |
| Caracal | DOI `10.1145/3477132.3483591`、`github.com/uoft-felis/felis` |
| Aria | `github.com/luyi0619/aria` (LICENSE = MIT) |
| CormCC | `usenix.org/conference/atc18/presentation/tang` |
| Tebaldi | DOI `10.1145/3035918.3064031` |
| Sundial | `github.com/yxymit/Sundial` |
| TXSQL | `arxiv.org/abs/2504.06854` |
| ESSN | `arxiv.org/abs/2511.22956` |
| CCBench (現行 pin) | `external/ccbench/LICENSE`、`include/tx_executor_concept.hh`、`cc/*/CMakeLists.txt`、`docs/ccbench-anatomy.md` §2 / §4 |
