## 所見

照合範囲は指定資料のみ。書き込み・web 取得・pytest は行っていない。以下、`候補表` は `docs/related-work/cc-candidates-2026-09-17.md`、`sources/` は指定 job directory 内を指す。

1. **real／must-fix — Rebirth-Retire・Bamboo の「単版、ss2pl 型」という前提が誤っている。**

   候補表:87–88、113–116、157–158 は、版 stamp 1 個で trace を移植できるという判断につなげている。しかし `sources/rr.txt:482–490` は次を明記する。

   > “a tuple may have multiple versions”
   >
   > “transactions are allowed to read the corresponding version based on their timestamps”
   >
   > “their version chains may grow very long”

   Bamboo §3.5 Optimization 3 にも次がある。

   > “multiple uncommitted updates can exist on a tuple”

   これは永続的な MVCC 分類を確定する指摘ではない。**読まれる候補が複数あるため、最新 writer の stamp だけで足りるという推論が成立しない**という指摘である。実際に選択された版、その producer、中間版、abort 時の復元を追う費用は未照合。P3(c) の充足と第1候補の確定に直接影響する。

2. **real／must-fix — Polaris の `validate` の説明は source と不一致。trace 費用最小の判断も未立証。**

   候補表:89 の「`validate` が `data_ver` を照合し `LOCK_ERR_PRIO` で abort」は誤り。`sources/polaris-row_silo_prio.h` の逐語は次のとおり。

   ```cpp
   bool validate(ts_t old_data_ver, bool in_write_set) const {
       TID_prio_t v = _tid_word.load(std::memory_order_relaxed);
       if (!in_write_set && v.is_locked()) return false;
       return v.get_data_ver() == old_data_ver;
   }
   ```

   `LOCK_ERR_PRIO` は `lock` / `try_lock` が返す。呼出側の abort 処理は提供 source にない。

   bit 割当 `1 / 4 / 4 / 10 / 45` は config と一致する。ただし `get_data_ver()` の戻り型は `uint32_t`。45-bit field があることから、そのまま完全な版識別子として利用できるとは断定できない。commit ID の生成・一意性・producer 復元も未照合であり、「3 点 CC-native 相当」「Silo と同じ経路」「費用最小」は推論に留まる。

3. **real／must-fix — P3 は未確認を合格／失格へ倒しており、判定の再現性がない。**

   候補表:77–79 は四条件の conjunction だが、次の扱いが揃っていない。

   - **(a)** 公開実装を見つけられなかったことを「公開実装なし」として棄却している。
   - **(b)** Rebirth-Retire は stored-procedure 評価から対話型適合を推論して合格。Caracal / Tebaldi は提供記録に必要な abstract 逐語がないまま失格。
   - **(c)** 「定数費用」は、record 当たり・version 当たり・transaction 当たり・開発工数のどれか不明。「field 1 つ」は大域 sequence、producer 対応、読んだ旧版の保持費用を含まない。
   - **(d)** Polaris の priority policy を変異軸と評価すること自体は可能。しかし S-OCC の WP check / reader-epoch metadata は「差が小」で棄却し、双方に適用する採否基準を示していない。
   - 「単一 protocol」「学習型でない」「standalone」という除外条件が、P3 の条件と混在している。固定方策であることだけでは「新しい変異軸にならない」は導けない。

   **「(d) は弱い」だけで形式的矛盾とは断定できない**。弱くても満たす場合はある。実在する問題は、充足を判定する尺度と根拠が不足していることである。Shirakami S-LTX の WP 事前宣言による除外は、現行 P1(b) に照らせば整合する。

4. **real／must-fix — dirty read の正しさの前提と、verifier の観測能力を混同している。**

   候補表:165–168 の不変条件は、正しい Bamboo に関して支持される。`sources/bamboo.txt:180–183` は明示的に、

   > “T2 is able to commit only if T1 has successfully committed.”

   とし、§3.6 は committed transactions の serializability を証明する。

   しかし `docs/isolation-phenomena.md` は **G1a / G1b が観測不能**と明記する。したがって、この不変条件を現行 trace の検査項目へ足せることは別途立証が必要である。writer が commit していても、reader が writer の**非最終版**を読んだ場合は producer ID だけでは区別できない。Bamboo §3.3 は再 write 時に最初の write を読んだ transactions を abort する必要まで述べている。

   同様に Shirakami の「verifier は MVSR の schedule も G2 検出で扱える」（候補表:91）は未立証。`sources/shirakami.txt:447–473` の serialization epoch / order forwarding と、既存 trace の commit 順による版順復元との対応が示されていない。

5. **real／must-fix — Bamboo を「同じ移植の中の対照」にできる根拠が足りない。**

   `rr-readme.md` は Bamboo と Rebirth-Retire の双方を対応一覧に挙げる。保存された Bamboo / RR の config は `cmp` で一致し、既定 `CC_ALG=BAMBOO` も確認できる。

   ただし、それだけでは次は導けない。

   > 「Bamboo mode の実装を改変した形」
   >
   > 「別実装でなく同じ移植の中の対照として扱う」

   どの選択子で両者を切り替えるか、fork 内の Bamboo が元論文相当かは未照合。対照を置く研究上の理由は妥当でも、追加費用を共有できるという判断は未確認である。「単独では 2025 の後継に劣後」も一般的優劣を示す根拠がない。

6. **real／must-fix — RW1 の限定が要約時に落ちている。**

   候補表の判定列・§4・README 追記の「公開実装なし」は、限定付きの調査結果を世界の不在に変えている。詳細は下の RW1 判定に列挙した。

   「唯一の 2024 年以降の手法」（候補表:111）は、§4 の文脈から本表内とも読めるが、当該文に母集合がなく世界順位にも読める。しかも「4 条件を満たす」自体が所見1–3で未確定。

7. **real／must-fix — §6 の一部は要求列挙を超えて具体的な設計を決めている。**

   次は満たすべき性質ではなく実現方法の指定である。

   > 「版 stamp (last-writer の tx ID) と commit sequence を要する」
   >
   > 「X 行の reason に加える必要がある」
   >
   > 「commit point … で global sequence を採る」
   >
   > 「`include/lock.hh` / `rwlock.hh` へ写す」

   特に先頭の指定は所見1の誤った前提に依存する。既存 D1373 の関門の再掲は、新規設計ではない。

8. **real／must-fix — P1 の探索経路と除外記録が不完全。**

   候補表:29 の、

   > 「候補の論文が baseline に挙げた手法 (Bamboo → Rebirth-Retire」

   は、2021 年の Bamboo が 2025 年の Rebirth-Retire を baseline にしたという読みになる。提供資料で確認できる向きは逆で、Rebirth-Retire が Bamboo を baseline にしている。

   また、§1 で検索により拾ったとする ForeSight / Dodo / TxnSails / Focus! に表の判定行がない。資料にはさらに以下の名前がある。**採用すべきとの結論ではなく、包含／除外理由を残す対象**である。

   - `web-evidence.md`：Gria、Strife、題名のみの “A Hybrid Approach to Integrating Deterministic and Non-Deterministic CC”、GPU-Accelerated OLTP、Epoch-based OCC in Geo-replicated DB。
   - `shirakami.txt:943–947`：Oze（2025）、“Massively parallel multi-versioned transaction processing”（OSDI 2024、protocol 名は未照合）。
   - `rr.txt:763`：DTA。
   - `bamboo.txt` §6：ELR、CLV、DRP、Hekaton。
   - `plor.txt` §7：FOEDUS、Calvin、SLOG。
   - 保存 config / WORKLOADS：NO_WAIT、WAIT_DIE、DL_DETECT、TIMESTAMP、MVCC、HSTORE、OCC、VLL、HEKATON、ss2pl、d2pl、mvto、si、oze、ermia。既存実装・年代外・対象外を区別して処理できる。
   - CV-Rules は資料中にあるが、protocol 候補ではなく検証手法の近傍。

9. **real／nit — Plor の検索 hit 数と節番号が不正確。**

   候補表:90 の「`github` / `available` / `artifact` … hit … 1 件のみ」に対し、保存本文の該当行は `plor.txt:90,428,1109` の3行。最後だけが concurrentqueue URL である。自身の code URL ではないという結論と、語の hit 数を分ける必要がある。

   §5 は IMPLEMENTATION、対話モード評価は §6.2.2。§1 の local buffer、§4.3 の conflict serializability は一致する。「commit を timestamp 順に」は**競合する transactions 間**という限定が必要である。

10. **refuted — README 追記が literature map の「自動合成／自動設計」を正本語彙にした、または実装を認可したという疑い。**

    追記には該当語の転載がなく、実装追加・pin 前進・変異探索面化を認可しないと明記している。`docs/README.md` の地図追加にも問題は認めない。問題は追記内の「公開実装なし」「費用最小」「同 repo の Bamboo」という内容上の強さである。

## cell 照合表

**(a)** 指定資料と一致、**(b)** 不一致、**(c)** 指定資料では裏付け不足／親の推論・選定判断。混在 cell は併記した。**a記** は `web-evidence.md` の API 応答要約・抽出結果との一致であり、API 生応答や論文本文の独立確認ではない。**c0** は原表の「—／未確認」で、未照合のまま。**c判** は選定判断であり、それ自体が誤りを意味しない。

| 候補 | 一次資料 | 実装可用性 | ライセンス | YCSB 適合 | trace 費用 | 証明面 | 既存4 CCとの差 | 判定 |
|---|---|---|---|---|---|---|---|---|
| Rebirth-Retire | a | a/c① | a記 | a/c① | b/c① | a | a/c① | c判① |
| Bamboo | a | a | a | a | b/c② | a/c② | a | c判② |
| Polaris | a記 | a | a | a/c③ | a/c③ | b/c③ | a/c③ | c判③ |
| Plor | a | b/c④ | c0 | a/b④ | a/c④ | a | a/c④ | c判④ |
| Shirakami | a記/a | a | a | a | c⑤ | a/c⑤ | a/c⑤ | c判⑤ |
| Brook-2PL | a記 | c0 | c0 | a記/c⑥ | c0 | c0 | a記/c⑥ | c判⑥ |
| Caracal | a記/c⑦ | a記 | a記 | c⑦ | c0 | c0 | c⑦ | c判⑦ |
| Aria | a記 | a記 | a記 | a/c⑧ | c0 | c0 | a/c⑧ | c判⑧ |
| CormCC | a記/c⑨ | a記/c⑨ | c0 | c⑨ | c0 | c0 | c⑨ | c判⑨ |
| Tebaldi | a記/c⑩ | a記/c⑩ | c0 | c⑩ | c0 | c0 | c⑩ | c判⑩ |
| IC3 | a | a/c⑪ | a/c⑪ | a | c0 | c0 | a | c判⑪ |
| Polyjuice | a | a記/a | a記 | c⑫ | c⑫ | c⑫ | a/c⑫ | c判⑫ |
| NeurCC | a記/a | a/c⑬ | c⑬ | a | a/c⑬ | a記/c⑬ | a/c⑬ | c判⑬ |
| ATCC | a記 | a記/c⑭ | c0 | a記 | c0 | a記/c⑭ | a記 | c判⑭ |
| Sundial | c⑮ | a記 | a記 | a記 | c0 | c0 | c⑮ | c判⑮ |
| TXSQL | a記 | a記 | c0 | c⑯ | c0 | c0 | a記/c⑯ | c判⑯ |
| ESSN | a記 | a記/c⑰ | c0 | a記/c⑰ | c⑰ | a記 | c⑰ | c判⑰ |

**(b)/(c) の逐語と根拠：**

- **①** 「Bamboo mode の実装を改変した形」「事前宣言は不要」「単版 lock 系で版 ID が無い」「追加対象」。README/config は mode 内部を示さず、対話型直接適合は論文アルゴリズムからの推論。複数版については所見1の逐語と不一致。「MOCC と同じ…動機」は比較解釈。
- **②** 「上と同じ」「YCSB では機械的に置ける」「semaphore を verifier が読めるよう」「単独では…劣後」。§3.3 は every-write retire の正しさを支持するが、再 write の cascading abort 処理まで要する。§3.6 の証明と既存 verifier の能力は別。費用・劣後判断は未立証。
- **③** 「commit 順 = Silo 同様」「3 点 CC-native 相当」「X/P 不要」「`validate` … `LOCK_ERR_PRIO`」「差は Silo の1箇所」「合成しうる」。所見2参照。YCSB 対応は README/artifact が支持するが、CCBench の対話 API への直接適合までは未照合。
- **④** 「hit …1件のみ」「§5で実装・評価」「X/P 計装 + 版 stamp」「commit を timestamp 順に」「公開実装なし」。検索・節番号は所見9。費用は推論、web 検索の query/結果全件は未提供。§1 の説明は競合相手についての順序である。
- **⑤** 「protocol だけ切り出せない」「S-OCC 単体は Silo と同じ3点」「MVSR の schedule も G2 検出で扱える」「差が小」「費用高」。WP・epoch・多版機構の存在は確認できるが、切出し不能、移植費用、trace 対応は未照合。S-OCC の変更は本文で “additional WP checks … and reader-epoch metadata” と具体化されている。
- **⑥** 「事前解析が要る」は abstract 断片から支持される推論。「IC3 / Tebaldi の系」は親の分類。本文の代替実行経路は未照合。
- **⑦** 「abstract のみ」「batch、read / write set 既知」「Calvin / Bohm 系」。保存 web 記録には書誌・repo 情報のみで、当該 abstract 内容はない。GPL-2.0 の API 分類は一致するが、具体的な導入形態における非両立判断は本資料だけでは未照合。
- **⑧** 「決定論的 batch」は repo description と Polaris artifact の “due to batching” が支持する。「batch 内 reservation」は提供資料では未照合。batch を現行 P1 で除外するのは親の選定判断。
- **⑨** 「abstract のみ」「protocol 混在」「単一 protocol ではない」「Polyjuice の baseline」「公開実装なし」。web 記録は書誌と検索の要約までで、機構・baseline の一次逐語がない。検索語も未記録。
- **⑩** 「abstract のみ」「transaction type の階層的静的解析」「modular CC (階層)」「公開実装なし」。保存記録にはこれらを照合できる abstract 本体・断片がない。
- **⑪** 「Polyjuice … に実装あり」「ISC / Apache-2.0」。Bamboo README の IC3 対応、NeurCC README の “IC3 variant” は確認できる。Polyjuice 内部の IC3 実装と、各派生部分への license 適用は未照合。年代外・事前知識という除外は資料に整合。
- **⑫** 「YCSB は無く TPC-C / TPC-E / micro」「解釈器ごと移植」「validation 段が担う」「stock ではなく学習成果物」。指定された記録には必要な repo tree・本文がない。7.1 の「事前定義したアクション空間」の語彙は一致するが、固定方策を P3(d) で落とすのは別判断。
- **⑬** 「commit 1本」は README 7.1 の既存記述とは一致するが API 履歴は未提供。「なし」は API の `license: None` より強い。`learn.h/cc` と lookup table、BO は README と一致するが、「高」「移植が必要」「関数の族に対する証明」は未照合／解釈。
- **⑭** 「公開 code の記述なし」「証明の記述は…確認できず」「公開実装なし」。抽出要約は原文の全件走査の証拠ではない。動的適応の引用はあるが、証明不在を示す走査語がない。
- **⑮** 「PVLDB 11(10), 2018」「論理 lease (TicToc の分散版)」は保存 web 記録に対応する書誌・機構記述がない。`desc: … distributed OLTP database testbed` による対象外判断は支持される。
- **⑯** 「standalone でない」「disk 系」「棄却」。引用が直接示すのは “implemented in Tencent's database, TXSQL” まで。engine 内実装であることから、抽出可能性や YCSB 不適合までは導けない。
- **⑰** 「公開実装の記述なし」「ermia の SSN を置換する形なら定数費用」「ermia … の certifier 改良」。ESSN abstract は SSN の一般化と MVSR 保存・strict subsumption を主張するが、ERMIA への実装・置換費用は述べていない。protocol でなく基準として別枠に置く判断は理解できる。

**横断確認：**

- 記載された全 repo の `pushed_at` 日付は `web-evidence.md` の応答要約と一致。ただし最終 code 変更日を意味するとは限らない。
- Bamboo / Polaris / DBx1000 の保存 LICENSE は ISC、CCBench は Apache-2.0。RR、Aria、Caracal、Polyjuice、Sundial は API 分類まで。Shirakami は README の Apache-2.0 表示も確認。
- `TxExecutorLike` は記載どおり `read / update / insert / delete_record / scan×2 / commit / abort`。最初の6操作式は `Status`、`commit` は `bool`、`abort` は `void`。
- `WORKLOADS` の YCSB 対応7件は **silo / tictoc / mocc / cicada / ermia / si / oze** で一致。
- Bamboo §1 の両実行モード、§3.3 の every-write retire、§3.6 定理2は一致。Plor §1 の local buffering、§4.3 の証明は一致。RR §3.3 定理1、§5 の DBx1000 / stored-procedure 評価は一致。

## RW1 判定

問題となる逐語は以下。

| 問題の文・cell | 判定 |
|---|---|
| 「この走査語の範囲で ほかの2024〜2026の単一ノード in-memory 汎用 CC は検出できなかった」 | 検索語は前文、返却結果の母集合は列挙不能と自認している。内部の不在としての全件確認を再現できない。 |
| 「4条件を満たす唯一の2024年以降の手法」 | 本表内とも読めるが母集合が同文にない。世界順位への誤読に加え、四条件充足も未立証。 |
| 「棄却: (a) 公開実装なし」および「(a) 公開実装なし: Plor、CormCC、Tebaldi、ATCC」 | 母集合・走査語を欠く不在断定。README 追記の同語も該当。 |
| CormCC「公開 repo 未検出 (web 検索2系統、内部の不在)」 | 「2系統」は走査語ではなく、結果母集合も列挙されていない。 |
| Tebaldi「公開 repo 未検出 (web 検索1系統、内部の不在)」 | 同上。 |
| ATCC「公開 code の記述なし (HTML 本文の走査、内部の不在)」 | 母集合は示すが走査語がない。 |
| ATCC「証明の記述は本文走査で確認できず」 | 走査語がない。提供記録も原文ではなく抽出要約。 |
| ESSN「公開実装の記述なし (abstract 走査、内部の不在)」 | 走査語がない。 |
| NeurCC「なし」、§4「LICENSE なし」、§7「LICENSE 不在」 | API `license: None` と file 不在は同義でない。母集合・走査の証拠も不足。 |
| Polyjuice「YCSB は無く TPC-C / TPC-E / micro」 | 同 cell に走査語がなく、引用先の調査内容も今回未提供。 |
| §5「『公開 repo 未検出』はいずれも内部の不在」以下 | 注記で自己分類しても、CormCC / Tebaldi / ATCC の走査語欠落や、他 cell の無限定要約を補えない。 |

Plor の**本文に限定した** `github / available / artifact` 走査は、母集合と語が同 cell にあり形式上は適合する。ただし hit 数は誤りで、web 検索部分は再現不能。

「既存4 CC に無い変異軸」は母集合が明示され、世界の不在とは読まない。ただし比較内容は技術的推論。「費用が最も低い／費用最小」は文脈上候補比較であり、主問題は RW1 よりも費用根拠の不足である。

「上書きしない」「認可しない」「本文未読」「網羅を保証しない」などは規則・自己の作業状態・限界の記述で、先行研究の不在主張ではない。新規本文に「最新」「初めて」はない。既存 README の「最新」「本調査では未発見」は差分以前の文であり、この追記が新たに導入したものとは扱わない。

## 総括

**must-fix：**

- **所見1・4：trace の前提と費用。** 放置すると、複数版・dirty/intermediate read の対応費用を過小評価して Rebirth-Retire / Bamboo を合格扱いし、Shirakami の検証可能性も過大評価する。
- **所見2：Polaris の source 説明。** 放置すると、誤った validation 機構と未確認の trace 対応を根拠に README が「費用最小」を保証する。
- **所見3・5：判定規則と対照の実装可用性。** 放置すると、未確認を合格または棄却へ倒し、同じ基準で候補を比較できない。
- **所見6：RW1。** 放置すると、限定された調査結果が「公開実装なし」「唯一」という事実として読まれる。
- **所見7：要求と設計の境界。** 放置すると、候補調査だけの成果物が field・event・移植先の設計を先に拘束する。
- **所見8：探索経路と除外記録。** 放置すると、検出済み候補を落とした理由が不明なまま「唯一」の選定結果が成立する。

**適用可能な是正案の逐語：**

1. P3 の判定説明を次に置換する。

   > 「各条件は『充足確認／不適合確認／未確認』で記録する。追加対象の確定には四条件の充足確認を要し、不適合を確認した候補は理由付きで棄却する。未確認を含む候補は保留とする。本調査での優先調査候補と、条件を確認済みの追加対象を区別する。trace 費用の単位・内訳と変異軸の採否基準は未確定であり、定性的な見積りだけでは (c)(d) の充足としない。」

2. Rebirth-Retire / Bamboo の trace cell と §6 項1・3–4を、次の内容へ改める。

   > 「Rebirth-Retire と Bamboo は未 commit の複数版を読む場合がある。実際に読んだ版と producer、最終版との区別、abort 後の復元、および commit 順との対応を保持できるかは未確認である。正しい Bamboo は reader の commit を writer の成功後に制限するが、既存の committed-only trace でその違反や中間版の読みを検出できるとは確認していない。trace 専用 field 1 個で足りるとは判断せず、P3(c) は未確認とする。」

3. Polaris の証明面を次に置換する。

   > 「論文の証明は未読。保存 source の validate は、write set 外の locked record を拒否し、data_ver の一致を検査する。priority による LOCK_ERR_PRIO は lock / try_lock が返す。呼出側の abort 処理、commit ID の生成、producer 復元、既存 trace への対応は未照合である。」

4. Bamboo 対照の説明を次に置換する。

   > 「Rebirth-Retire の README は Bamboo と Rebirth-Retire の双方を対応一覧に挙げる。両者を切り替える実装経路と、元の Bamboo に相当する対照を同じ移植で用意できるかは未確認である。Bamboo は対照候補として記録し、移植費用の共有や一般的な性能劣後は断定しない。」

5. 不在断定を次の語に統一する。

   > 「公開実装・利用許諾を今回の提供資料から確定できないため、P3(a) は未確認。」

   NeurCC の license cell は、

   > 「GitHub API 応答要約は license: None。LICENSE file の不在および利用許諾の全体は未照合。」

   §1 の検索結論は、

   > 「この検索で把握した候補を記録する。検索結果全件を再現できないため、追加候補の不在は結論しない。」

6. §6 項2・5–6の具体的設計指定を次に置換する。

   > 「retire 後の再 write、priority、依存関係、および CCBench の workload API を損なわずに観測・実行できることが確認課題となる。trace の field・event・reason、採番方式、移植先 file、workload API の追加要否は本書では決めない。」

7. README 追記の判定要約を次に置換する。

   > 「優先調査候補は Rebirth-Retire、Bamboo（対照候補）、Polaris。trace 対応・固有実装費用・判定条件の未確認事項を併記し、追加対象の確定とは区別する。その他の候補は、確認できた対象外理由と、公開実装・利用許諾等の未確認事項を表に記録した。同表は実装追加・pin 前進・変異探索面化のどれも認可しない。」

8. P1 の系譜説明を次に置換し、検索で得た未掲載候補には保留／除外理由の行を加える。

   > 「Rebirth-Retire の baseline として Wound-Retire（Bamboo）/ Silo / MOCC / TicToc / DL_DETECT / Wound-Wait を確認した。」

**nit：** Plor の検索 hit 数・評価節番号、競合間 timestamp 順の限定、「移植であって port でない」という同義語の対比。Plor の検索文は次に直せる。

> 「保存した Plor 本文を github / available / artifact で走査すると3行が該当し、URL を含む1行は依存ライブラリ concurrentqueue の参考文献だった。」

**未照合のまま残る cell：** 照合表の **(c)、c0、c判**。特に採否を左右するのは、RR の対話 API・版追跡、Bamboo/RR の実装切替、Polaris の commit/版識別、Shirakami の trace 対応、Caracal/CormCC/Tebaldi の機構、Polyjuice の workload/validation、NeurCC の許諾、ATCC の公開実装・証明、ESSN の移植費用である。これらを未確認として残す修正で本 wave は収束でき、実装追加や共通契約の設計は不要である。