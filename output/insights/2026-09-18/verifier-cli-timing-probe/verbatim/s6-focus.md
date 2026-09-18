## 判定と検査範囲

**GO。A1〜A8・B1〜B7 は closed と判定します。** 観測値の訂正・再測定を必要とする問題はありません。修正文には、下記の軽微な表現・参照の所見が残ります。

指定資料の静的検査、保存 JSON の算術検算、逐語ファイルの照合を行いました。bench・verifier・selftest・pytest は再実行していません。ファイルへの書込みもしていません。

以下、`README` はレビュー対象の insight README、ソースの相対パスは指定 worktree 内を指します。

## 訂正文のソース照合

| 対象 | 確認結果 |
|---|---|
| §2.1：backoff ヘッダはコンパイル対象に残る | 正しい。`external/ccbench/cc/silo/include/transaction.hh:9` は無条件 include、同 `:51` にメンバ、`:69` に構築がある。 |
| §2.1：`#if BACK_OFF` が除くのは呼出し | 当該 backoff 動作の説明として正しい。`transaction.cc:42` が `Backoff::backoff()`、`:719` が `leaderBackoffWork()` を囲む。厳密には前者には `ADD_ANALYSIS` 有効時の計時コードも含まれるが、ヘッダやオブジェクト構築を除外しないという訂正の核心は正しい。 |
| §2.1：当時の `BACKOFF_FIXED=-1` は stock 分岐 | 正しい。`git show 0a07481b8:patches/silo-backoff-fixed.patch` で確認。`#if BACKOFF_FIXED >= 0` は偽となり、`#else` の `Backoff_.load(...)` を選ぶ。`BACKOFF_NOINLINE` の既定は 0。当時の patch の SHA256 は記載の `36cd974c…` と一致。 |
| §2.1：prefix map 等の所在 | `orchestrator/campaign/buildcache.py:1914` の `_binary_path_cmake_defines` で確認。当時の版にも同じ配線がある。ただし policy 未指定なら追加なし、debug prefix map は staging root 指定時に追加される。 |
| §3・§5：CLI と pipeline の差 | `core.py:200` 以降の source/genome/admission 束縛、`:353` 以降の snapshot を渡す呼出しと整合。共通の検証本体でも計時範囲・束縛が異なるという説明は妥当。 |
| §4.1：worker 16 の限界 | 妥当。`parse.py:628` の並列処理が結果不成立を返すと、`:787` 以降の呼出し側が逐次読出しへ fallback する。CPU/wall だけでは全 worker の正常完走を証明できない。 |
| §4.3：既往値の併記 | 妥当。t2229 README §2 の 13 反復・欠測 attempt の 3 反復・除外後中央値 1398.7 秒と一致。§4・§5.2 の引用値も一致し、31.4%・1/36 による比の提示は削除されている。 |

`s4-ruling.md` §6 は旧 §2 の P1 を誤りと明示し、主張を backoff 動作の対応までに限定しています。今回の射影範囲では訂正は成立しています。

## 数値の再照合

通常の秒数は原本から小数第3位に丸めました。割合・単価・Popen 復帰時間は README の表示桁に合わせています。

| 箇所・項目 | 原本からの値／再計算 | 判定 |
|---|---|---|
| §1・§4.1：T_trace / T_count / T_verify | 3.343941605 → **3.344** / 16.857903951 → **16.858** / 421.706717790 → **421.707 秒** | 一致 |
| 3 区間合計 | 441.908563346 → **441.909 秒** | 一致 |
| 3 区間の割合 | **0.76% / 3.81% / 95.43%** | 一致 |
| §1：入力規模 | **48 file、204,048,743 行、6,520,332,111 bytes** | file 別 JSON の独立合算と一致 |
| bench commit / batch / abort | **17,128,612 / 0 / 3,066,603** | 一致 |
| bench user / sys / maxrss | **143.193 / 5.214 秒 / 529,672 KiB** | 一致 |
| bench Popen 復帰 / communicate 近似窓 | **0.0002 / 3.344 秒** | 一致 |
| count 単価 | **0.984 μs/commit、82.6 ns/行** | 一致 |
| inventory / 複製 | **16.676 / 3.979 秒** | 一致 |
| verifier user / sys | **1812.169 / 88.976 秒** | 一致 |
| verifier CPU 合計 | 1901.145549 → **1901.146 秒** | B1 の訂正が正しい |
| CPU/wall / maxrss | **4.51 / 46,084,868 KiB＝43.95 GiB** | 一致 |
| verifier Popen 復帰 / communicate 近似窓 | **0.0003 / 421.706 秒** | 一致 |
| §4.2：rc / verdict / certified | **0 / serializable / true** | 一致 |
| txns / edges | **17,128,612 / 296,980,787** | 一致 |
| anomaly_count / total_cycles | **0 / 0** | 保存 `verifier.json` と一致 |
| integrity | **clean=true、列挙された違反数すべて0、notes 空** | 一致 |
| proof_surfaces_present | **false** | JSON に当該キーなし |
| 出力規模 | verifier JSON **1,237 bytes**、両 stderr **0 bytes**、bench stdout **21 行** | 実ファイルと一致 |
| verifier 単価 | **24.62 μs/txn、1.42 μs/edge** | 一致 |
| §4.4：smoke の各時間 | trace **1.048**、count **4.741**、inventory **4.601**、verify **92.806**、複製 **1.228 秒** | 一致 |
| smoke の規模・件数 | commit **4,933,099**、abort **3,330,543**、**57,674,153 行、1,812,744,103 bytes**、edge **92,352,511** | 一致 |
| smoke の結果・資源 | **0 / serializable / true**、user **413.954**、sys **22.207 秒**、maxrss **13,585,176 KiB** | 一致 |

smoke の条件 10,000 records / 1 秒 / 48 thread、binary hash `258440e6…` も一致しました。作成された smoke summary の数値・真偽値54項目は原本と一致しています。

**意図した変更は CPU 合計の丸め訂正と total_cycles の直接表記です。それ以外の検査対象値に原本との不一致はありません。** trace 全体の再走査・再ハッシュはしていません。

## 総括

**判定：GO。closed 15件、partial 0件、regressed 0件。** A3 の closed は、初回の疑義棄却が維持されているという意味です。

| 所見 | 判定 | 修正を確認した箇所・根拠 |
|---|---|---|
| A1 | closed | README §2.1、裁定 §6。無条件 include・構築を明記し、コンパイル入力／binary 同一性を撤回。`transaction.hh:9,51,69` と当時の patch が裏付ける。 |
| A2 | closed | README §2.1。buildcache と plain cmake の差を列挙し、一致対象を workload argv と列挙した defines に限定。`buildcache.py:1914` と整合。 |
| A3 | closed | README §3。file 出力と pipe の差、近似計時、pipeline の厳密な再現ではないことを明記。主要計時・件数も原本と一致。 |
| A4 | closed | README §3・§4.1・§5。CLI 固有費用、source 束縛と snapshot、worker 選択値の限界を追記。`core.py:200,353`、`parse.py:628,787` と整合。 |
| A5 | closed | README §3・§5。inventory の追加読出しと、cache への効果量が未測定であることを明記。 |
| A6 | closed | README §4.1。maxrss を process tree の同時合計 RSS／cgroup peak と区別。 |
| A7 | closed | README §4.3。31.4%・1/36 を削除し、時点・code・node・計時範囲が異なる値の併記へ変更。 |
| A8 | closed | README §4.2。`0 / 0` が保存 JSON の anomaly_count / total_cycles と一致。 |
| B1 | closed | README §4.1。原本の和 1901.145549 を **1901.146 秒**へ正しく丸めた。 |
| B2 | closed | README §4.3。13 反復・欠測 attempt の3反復・除外後1398.7秒を明記。t2229 §2 と一致。 |
| B3 | closed | README §3・§5。A5 と同じ追加読出し条件を明記。 |
| B4 | closed | README §4.1。A6 と同じく、合算メモリピークとの誤読を解消。 |
| B5 | closed | smoke summary、`verbatim/s6-review-A.md`／`s6-review-B.md` が実在し読取可能。レビュー2本は job dir の原本と byte 単位で一致。 |
| B6 | closed | README §1・§4.3。節番号を t2229 README §4／§5.2 の参照に訂正。 |
| B7 | closed | README §4.3。「1/36」自体を削除し、近似表記の問題を解消。 |

新規所見は以下の **nit 3件**です。must-fix・should はありません。

| 番号 | 重要度 | 箇所 | 所見・推奨修正 |
|---|---|---|---|
| N1 | nit | README:66、§3 | 「page cache にその読出しが載った状態」は cache 常駐状態を確認したようにも読める。記録が示すのは追加読出しの実施までなので、「追加読出し後。cache の常駐状態・効果量は未測定」とすると正確。§5 の限界記述は既に適切。 |
| N2 | nit | README:121、§5 | 「§2.1 の X / P emitter」は参照先違い。該当記載は **§4.2**。個数×3と P emitter L432 自体は stock `transaction.cc` と一致。 |
| N3 | nit | README:140、§7 | 「全件 real」は直後の A3・B8〜B10 の refuted と不整合。また B の「全行・派生値が一致」は B1 の丸め差を省略している。「修正提案を採用。主要値は一致し、CPU 合計の丸め差を訂正」と整理すると正確。 |

**読めなかった指定資料：なし。** HANDOFF の訂正は今回の射影対象外であり、本判定には含めていません。