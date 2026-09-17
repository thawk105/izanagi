## 所見別対応表

照合は指定資料に限定し、書き込み・web 取得・pytest は行っていない。以下、`候補表` は `docs/related-work/cc-candidates-2026-09-17.md`、`sources/` は指定 job directory 内を指す。追加照合3件は親の報告として確認したが、生データによる独立照合はできない。

**前巡の所見は closed 6件、partial 4件。親の closed 判定と食い違うのは 2・3・6・8。** 所見8の是正には新たな年代誤認が入っている。

| 前巡 | 判定 | 候補表 v2 の逐語と根拠 |
|---|---|---|
| 1 複数版・trace 費用 | **closed** | :188–190「実際に読んだ版と producer、最終版との区別、abort 後の復元、および commit 順との対応を保持できるかは未確認」「trace 専用 field 1 個で足りるとは判断せず、P3(c) は未確認」。前提と判定は是正済み。引用の誤記は後述の nit。 |
| 2 Polaris | **partial** | :113「priority による `LOCK_ERR_PRIO` は `lock` / `try_lock` が返す」は正しい。一方、同じ行の「**差は Silo の TID word と access / validate に収まる**」、:145–146「差は Silo の access / validate への予約検査」は残存。保存 source は release 処理も持ち、`validate` 自体は priority を検査しない。 |
| 3 P3 の再現性 | **partial** | :97–99「未確認を含む候補は保留」「定性的な見積りだけでは (c)(d) の充足としない」と定義したが、:157 は棄却理由を「**d の充足を示せない: Shirakami の S-OCC**」とする。また :114 の Plor「b=確認」は、他候補で区別した対話モード評価と CCBench API 適合を再び同一視している。 |
| 4 verifier の観測能力 | **closed** | :196–198「既存の committed-only trace でその違反や中間版 … の読みを検出できるとは確認していない」。:115 の S-LTX も「既存 trace の commit 順による版順復元との対応は未照合」。指定された verifier 前提と整合。 |
| 5 Bamboo 対照 | **closed** | :143–144「同じ移植で用意できるかは未確認。移植費用の共有や一般的な性能劣後は断定しない」。README 対応一覧と実装切替の確認を分離できている。 |
| 6 RW1 | **partial** | :37「追加候補の不在は結論しない」は改善。しかし :123「**LICENSE file なし**」は root 一覧の観測より広い。:114・119・120 の「表示に repo なし」も、検索結果全件が再現不能という :173 と併存する。検索語の追記だけでは列挙可能な母集合を補えない。 |
| 7 設計指定 | **closed** | :185–186「field・event・reason、採番方式、移植先 file、workload API の追加要否は本書では決めない」。具体的な採番・配置・reason の指定は撤去済み。:199 の timestamp に関する断定は設計指定ではなく、別の未立証主張として後述。 |
| 8 探索経路・除外記録 | **partial** | :31「Rebirth-Retire の baseline として…」で向きは修正。追加した :52–53「**年代外 = … SLOG / … DRP / DTA**」は原資料と不一致。OSDI 2024 の文献は名前だけで包含／除外理由が未記録。 |
| 9 Plor | **closed** | :114「3 行が該当」「§5 実装、§6.2.2 評価」「競合する trx 間で commit を timestamp 順に」は保存本文と一致。 |
| 10 README の語彙・認可 | **closed（前巡 refuted を維持）** | 候補表 :4–5「実装追加・pin 前進・変異探索面への追加のどれも認可しない」。README 差分も同じ境界を明記し、問題とされた「自動合成／自動設計」の転載はない。 |

## 新規所見

残存問題を含め、v2 で判断に影響する箇所を列挙する。

1. **real／must-fix — 三値規則の適用が候補間で揃っていない。**

   候補表 :115・157 の S-OCC は、不適合確認ではなく「充足を示せない」で棄却されている。保存本文 `sources/shirakami.txt:442–446` は変更点を WP checks と reader-epoch metadata と説明するが、その差が P3(d) を満たさないという尺度は提供されていない。

   Plor は :114 で `b=確認`。しかし :77–78 は明示的に、

   > 「対話型を評価した」は論文の実験モードの事実であり、CCBench の対話 API へ直接載ることの確認ではない。

   と定義する。Plor の実験モードは確認できるが、指定資料に CCBench API への直接適合確認はない。Bamboo と同じく `b=?` が整合する。

   :137–138 の RR「P1 の母集合に入り…唯一」も、P1 が要求する対話型直接適合と RR の `b=?` を両立させていない。**表のラベルを数えて1件であることと、P1 充足を確認したことは別である。**

2. **real／must-fix — Polaris の変更範囲を、是正後も過小に限定している。**

   候補表 :113・145–146 の access / validate 限定に対し、`sources/polaris-row_silo_prio.h` は次を持つ。

   - :138–142：`validate` は lock 状態と `data_ver` を検査。
   - :153・166：priority 比較は `lock` / `try_lock`。
   - :184–215：`reader_release`、`writer_release_abort`、`writer_release_commit` が priority・参照数・版情報を更新。

   「親の解釈」と付けても、変更範囲の閉じた列挙はこの source と一致しない。Silo variant としての到達範囲・移植の小ささを保証する根拠にはできない。

   「費用が最も低い」は推論と明示され、合格判定にも使われなくなったため、その順位表現単独は **nit** とする。ただし費用未記入の候補がある以上、本表全体の最小値としては未照合。

3. **real／must-fix — 追加した分類の一部が、題名・適応性から不適合を確定している。**

   - 候補表 :40–42 は “A Hybrid Approach to Integrating Deterministic and Non-Deterministic CC” を「決定論的 (batch、read / write set 既知)」として除外。`web-evidence.md:70` にあるのは題名だけで、その実行要件は未照合。
   - :124・159 は ATCC を「母集合外 (学習型)」。`web-evidence.md:18–26` が示すのは optimistic / pessimistic の動的適応であり、学習型という分類は確認できない。
   - :117 の Caracal は題名から `b=×`。当該題名の逐語自体が保存 web 記録にはなく、batch・事前宣言の詳細も候補表自身が未照合とする。`b=×` の独立根拠は不足している。API の GPL-2.0 分類と、具体的な取り込み形態の非両立判断も別であり、後者は未照合。

   これらは「実際には適合する」という指摘ではない。**未照合を確認済みの対象外へ倒さない**ための修正が必要。

4. **real／must-fix — 不在表現の範囲と証拠の粒度がまだ一致しない。**

   候補表 :123 の root 一覧は、仮に親の観測どおりでも子 directory 内の LICENSE を否定しない。「LICENSE file なし」ではなく root 直下に限定する必要がある。

   また、:114・119・120 の検索結果に関する不在は、query の文字列を加えても、返却結果の全件を列挙できない問題が残る。指定された 7.7.2 は「母集合と走査語を明示して全件列挙する」を条件とする。

   :124 の「抽出要約に code URL の記述なし」も、`web-evidence.md:24` には source code URL に関する否定的な記述自体がある。正確なのは「公開実装を確認できる URL は提示されていない」であり、「記述なし」と要約しない方がよい。

   追加照合3件について、`parent-fix-table.md:16` は観測の報告として読める。しかし root の生一覧、RR / Aria の LICENSE 本文は `sources/` にない。**親が取得していないとは判定しないが、今回の独立照合は未了。**

5. **real／must-fix — 新しい除外記録に年代誤認がある。**

   候補表 :46 の cutoff は2017年以降だが、:52–53 で年代外とした次の3件は cutoff 内。

   | 手法 | 保存資料 |
   |---|---|
   | DTA | `sources/rr.txt:759–763`：“2018. Dynamic Timestamp Allocation for Reducing Transaction Aborts.” |
   | DRP | `sources/bamboo.txt:1035–1037`：“Fourteenth EuroSys Conference 2019” |
   | SLOG | `sources/plor.txt:1208–1210`：“2019. SLOG: Serializable, Low-Latency, Geo-Replicated Transactions.” |

   SLOG は分散という別の対象外理由が使える。DRP は `bamboo.txt:973–983` に tame transactions の事前知識要件があるが、全体の包含判定とは分けるべき。DTA の P1 適合は未照合。

   OSDI 2024 の “Massively parallel multi-versioned transaction processing” も、:53 で名前を残しただけで理由がない。Strife は前巡が除外記録の対象に挙げたが、保存記録では「NeurCC 関連研究に未登場」としか確認できないため、検索で発見した候補として数える必要はない。その区別を記録すればよい。

6. **real／must-fix — timestamp 再割当から「commit 順に使えない」まで断定している。**

   候補表 :199：

   > 「timestamp を再割当する protocol (Rebirth) では timestamp を commit 順に使えない。」

   `sources/rr.txt` の §3.3 は commit-point ordering、§4.3 は再割当と worker ID を含む timestamp を説明する。しかし、これだけでは最終 timestamp と必要な版順・commit 順の対応可能性まで否定できない。

   初期 timestamp を固定の識別子として使えないことと、最終値・履歴を含めた対応が不可能であることを分け、後者は未照合に戻す必要がある。

7. **real／nit — 引用・分類数・出典表示の小さな誤り。**

   - 候補表 :111 の `a tuple may multiple versions` は `have` が欠落。出典節も §5 ではなく **§4.4**（`sources/rr.txt:480–484`）。
   - :100 の「判定は…3つ」に対し、実際の判定列には「母集合外」を含む4分類がある。
   - :46 の「2017 (MOCC / Cicada の年)」に対し、MOCC は保存参考文献で2016年（`sources/plor.txt:1206–1208`）。cutoff を変更する必要はなく、括弧の説明を直せばよい。
   - :53 の Shirakami「§7」は関連研究節ではなく結論。該当書誌は参考文献 [26]。
   - CormCC の「Polyjuice の baseline」(:119)、TXSQL の「disk 系」(:126)、ESSN の ERMIA 固有の実装関係 (:127) は、提供資料では未照合。これらを未照合と明示しても、現在の大分類を直ちに変更する必要はない。

8. **refuted — CormCC の混在・切替という説明には、提供資料内の裏付けがないという疑い。**

   `sources/plor.txt:1067–1069` に、

   > “CormCC [42] provides a framework for mixing different CC protocols and changing them online with minimal overhead.”

   がある。候補表が挙げる検索結果の逐語は未照合だが、機構の説明自体には保存された別論文からの裏付けがある。出典をここへ替えればよい。CormCC 原論文の独立確認ではない点は残る。

## 量化の検算

| 親の量化の文 | 原データからの再計算 | 判定 |
|---|---|---|
| 「追加対象…0件」(:100・133、README) | 17候補行のうち a〜d 全てが充足確認の行は0。 | **一致** |
| 「優先調査候補」3件 | RR、Bamboo、Polaris。 | **一致** |
| 「判定は…3つ」(:100) | 表の最上位分類は優先調査3、保留2、棄却5、母集合外7。合計17、分類は4つ。 | **不一致**。「P3内は3分類」なら整合する。 |
| 「2024年以降…aを確認できた唯一」(:137–138) | 明示的な `a=確認` は RR 2025、Bamboo 2021、Polaris 2023。年で絞れば RR の1件。 | **ラベル上は一致、P1充足は未照合**。RR 自身が `b=?`。 |
| 「config…define 集合は…同一」(:111) | RR / Bamboo の保存 config は各9,144 bytesで byte 単位一致。行頭 `#define` は各172件、既定は双方 `BAMBOO`。 | **一致**。実装切替の同一性までは示さない。 |
| 「LICENSE…Bamboo-Public と同文」(:111) | 保存された Bamboo / DBx1000 / Polaris の LICENSE は byte 単位一致。RR の LICENSE は保存20件に含まれない。 | **RRについて未照合**。親の追加報告のみ。 |
| Plor「3行」「URLを含む1行」(:114) | 大文字小文字を区別せず `github\|available\|artifact` を走査。該当は :90・428・1109 の3行。最後の1行に concurrentqueue URL。 | **一致** |
| YCSB 対応「7つ」(:77) | WORKLOADS 10行中、`ycsb` を含むのは tictoc / mocc / si / oze / ermia / cicada / silo。 | **一致** |
| Polaris「1 / 4 / 4 / 10 / 45」(:113) | header の latch 1bit、config :132–135 の4定数。合計64bit。 | **一致**。getter は `uint32_t` で、完全な版識別は別途未照合。 |
| 「候補比較で費用が最も低い」(:145) | 「低」は Polaris だけ。ただし費用が「—」の候補が複数あり、共通の単位も未確定。 | **全候補の最小としては未照合** |
| NeurCC root「4 dir」(:123) | README は4つの実験 directory を列挙。ただし API root 生一覧は未提供。 | **root の全件数としては未照合** |
| web 検索「3系統」、CormCC「2系統」、Tebaldi「1系統」 | 系統数は web-evidence の要約と一致。実行 query の逐語と返却全件は保存記録から再現できない。 | **報告数は一致、実行内容は未照合** |
| mocc「141行」、検査「3証拠」 | 141行の元 diff は指定資料にない。3証拠の列挙は D2114 の射影と整合するが、適用実測はない。 | **141行は未照合。3証拠は規則の再掲として一致** |

## 総括

**must-fix**

- **三値判定と分類（新規1・3）**：放置すると、未確認の S-OCC・ATCC 等が保留集合から落ち、Plor の直接適合と RR の P1 充足が確認済みとして読まれる。
- **Polaris の変更範囲（新規2）**：放置すると、移植・変異で扱う範囲を access / validate に過小限定する判断材料になる。
- **不在表現（新規4）**：放置すると、root の観測や再現不能な検索要約が、repo 全体の LICENSE・公開実装の不在として伝わる。
- **除外理由（新規5）**：放置すると、cutoff 内の DTA / DRP が誤った理由で候補調査から落ちる。
- **timestamp の断定（新規6）**：放置すると、未検証の trace 対応方法が不可能と扱われ、後続設計の選択肢を先に狭める。

**是正案の逐語**

1. S-OCC・Plor・RR の判定を次に改める。

   > 「S-LTX は事前宣言を要するため b=×。S-OCC は d=? として保留する。Plor は対話モード評価を確認したが、CCBench の対話 API への直接適合は未照合であり b=? とする。本表で2024年以降に発表され a=確認と記録した候補は Rebirth-Retire の1件だが、P1 の対話型直接適合は未確認である。」

2. 追加した未立証分類を次に改める。

   > 「ATCC の学習型という分類、および “A Hybrid Approach to Integrating Deterministic and Non-Deterministic CC” の batch・事前宣言要件は提供資料では未照合であり、母集合への包含判断を保留する。Caracal の b は未確認とする。GPL-2.0 という API 分類は確認したが、具体的な取り込み形態における利用条件は別途確認する。」

3. Polaris の限定と順位を次に改める。

   > 「保存 source では TID word、lock / try_lock、reader / writer release に priority 関連処理がある。validate 自体は lock 状態と data_ver の一致を検査する。Silo との差分全体と移植費用は未照合であり、変更範囲を access / validate に限定しない。費用は低い可能性があるという仮説に留め、候補間順位は確定しない。」

4. 不在・追加照合の記述を次に改める。

   > 「公開実装・利用許諾を今回の提供資料から確定できないため、未確認とする。親の追加照合報告では、NeurCC の root 直下に LICENSE 系 file は見つからず、RR の LICENSE は ISC、Aria は MIT だった。生一覧と LICENSE 本文は今回の照合資料に含まれず、独立照合は未了である。NeurCC の子 directory 内および利用許諾全体は未確認である。」

5. 年代外の列挙を次に改める。

   > 「DTA は2018年、DRP と SLOG は2019年であり年代内。SLOG は分散として対象外、DTA と DRP は包含判断を保留する。OSDI 2024 の “Massively parallel multi-versioned transaction processing” も包含判断を保留する。Strife は保存記録では NeurCC 関連研究への未登場という記述のみで、検索で得た候補としては数えない。」

6. §6 項4を次に改める。

   > 「Rebirth は実行中に timestamp を再割当する。初期値・最終値・再割当履歴と、実際に読んだ版および既存 trace の commit 順との対応は未照合であり、採取点と識別方法を確認する。」

**nit**

引用の脱字・節番号、判定分類数、MOCC の年、未照合の補助説明を直す。代表的な置換は次のとおり。

> 「Rebirth-Retire §4.4 は “a tuple may have multiple versions” と説明する。」

> 「P3 内の判定は優先調査候補・保留・棄却の3分類で、別に P1 の母集合外を記録する。」

これらの局所修正で収束可能。追加の実装・共通契約設計・性能測定は必要ない。