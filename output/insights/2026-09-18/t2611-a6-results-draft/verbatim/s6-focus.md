| 所見 | 判定 | 根拠 |
|---|---|---|
| A MF-1：`high_variance` / `rounds` の出所 | closed | §2.1「raw JSON の `performance` は `unstable = false`、`rep_notes = []`、campaign WAL の `bench_done` は `high_variance = false`、`rounds = 1`」。raw 2 件と WAL の `bench_done.payload` 2 件でそれぞれ実在・値一致を確認。§5.3 も同じ出所分離になった。 |
| A MF-2：A-2 の status / genome の出所 | closed | §5.3 に「§3.4 の A-2 attempt、outer status、adopted genome、判定の合成規則」の行を追加し、A-2 `certification.json` と復号 policy を指定している。掲載 SHA-256、§3.4 の `observed-positive`・「rr5 = 10 µs、rr50 = 5 µs」・論理積は現物と一致。 |
| A N-1：WAL 行数内訳 | closed | §5.2「20 行 (`build_start` 2・`build_done` 2・`verify_done` 12・`bench_done` 2・`commit` 2)」。WAL 全行を数えた結果と一致し、内訳の合計も 20。 |
| A N-2：「canonical policy bytes」 | closed | §1.3「`policy_bytes_base64` を復号した policy file bytes の SHA-256」「producer の canonical JSON 直列化の hash ではなく file bytes の hash」。復号 bytes の SHA-256 が掲載値 `96ed47d0…d12384a` と一致。 |
| B MF-1：§2.2 の性能と正しさの結合 | closed | §2.2「adopted cell の `correctness.status` は、別の trace-enabled 走行の検査結果として `certified` と記録されている」と「性能の観測値と `reject` 判定は §2.1 に示した」を別文にした。旧引用候補を除去し、検査の射程も限定 (i)〜(v) に束縛している。 |
| B MF-2：D1506 の括弧 | closed | §5.4「2026-09-02 の非認証較正に基づく、無 backoff と調整済み adaptive の基準線の裁定」。D1506 の日付、基準線 2 本、「認証されていない」という限定と一致。 |
| B SH-1：「protocol」の曖昧さ | closed | §3.1「共通するのは CC protocol の Silo」と特定し、「A-6 の認証 protocol と B-10 の測定契約が同一という意味ではない」「実行 argv の一致は観測ではなく B-10 の spec による」と明記。T-2430 §2 の対応表と整合する。 |
| B SH-2：trace 側比率の範囲 | closed | §2.3「performance 条件の trace-enabled 走行各 5 回」と対象を限定し、「legacy 各 1 回は…別 workload…この範囲に含めない」と明記。括弧内の「rratio 50・4 thread・200 tuple・rmw true」は復号 policy と一致。 |
| B N-1：表の単位 | closed | §2.1 の列名が「標本 sd (tps)」「95% CI 半幅 (tps)」「min – max (tps)」になっている。 |
| B 総括の主判定文案 | closed | §0 は「stock を 5.7841% 下回り…`reject` だった」「これは 1 attempt・各 5 標本の中央値比較の結果」「別の trace-enabled 走行では、2 cell とも `correctness.status = certified`」の 3 文。数値・status は権威 bytes と §2 に一致し、他記録を同じ文に取り込んでいない。 |

## 新規所見

なし。指定された焦点範囲で、fix による新しい誤りは認めなかった。

A-2 の追加出所行は、現物 bytes の SHA-256 が次の掲載値と完全一致した。

`e74d0f870497941b95ac4d1e244634188813e249f2821d571178e4854a3ed671`

同ファイルで `attempt_id = t2364-20260907b`、`status = observed-positive`、adopted genome は rr5 が `(BACK_OFF=1, BACKOFF_FIXED=10)`、rr50 が `(1,5)`。base64 復号後の workload 順序は rr5 → rr50、`certification_composition.outer_certification` は逐語で `logical conjunction in policy workload order` だった。

A-6 の raw は両 cell とも `trace_enabled = false`、各 5 標本。権威 bytes は outer `reject`、2 cell とも correctness `certified`、正しさ検査の観測回数は legacy 1・performance 5 を記録している。§0 の追加文はこの区別を保持している。

README 行の「限定 12 件」は、§4 の最上位番号 1〜12 と一致する。(i)〜(v) は第 4 項の内訳であり、別の最上位項として加算していない。D1993・D2108・D2120 項 7 による限定も保持されている。

## 派生値の再計算

raw JSON の `performance.samples_tps` から一度だけ再計算した。標本 sd は分母 `n−1`、CI 半幅は稿どおり `2.776445 × sd / √5`。以下はすべて fix 後の §2.1 とレビュー A の修正前確認値に、掲載桁で一致した。

| 項目 | stock | fixed2 |
|---|---:|---:|
| 標本数 | 5 | 5 |
| median (tps) | 10,088,796 | 9,505,248 |
| mean (tps) | 10,132,250.6 | 9,565,649.4 |
| 標本 sd (tps) | 133,406.6 | 112,221.9 |
| cv | 0.0132 | 0.0117 |
| 95% CI 半幅 (tps) | 165,646.2 | 139,341.9 |
| min–max (tps) | 10,029,940–10,365,808 | 9,488,225–9,753,031 |

効果は `9505248 / 10088796 − 1 = −0.057841193339621455`、百分率で **−5.7841%**。権威値・§0・§2.1・README 行が一致する。生標本は raw と WAL で記録順も一致した。

## 総括

**GO。10 行すべて closed。partial / regressed はなく、新規所見もない。**

指定資料の静的照合と読み取り再計算で確認した。ファイル変更・pytest 実行は行っていない。