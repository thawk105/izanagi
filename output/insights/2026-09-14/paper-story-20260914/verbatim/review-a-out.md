## 所見

1. **対象:** §3 項目5・§9末尾「変わった理由が『測っていた構成が違った』と特定できる」  
   **主張:** 測定対象の違いを、符号反転の原因の同定へ広げている。`src_token` は構成の違いを示すが、その違いの因果寄与は示さない。  
   **一次資料:** `docs/paper-story/figures/README.md` の fig6 キャプション正文、D1645。  
   **確度:** **高**。正文は「the cause of the sign difference has not been identified」と明記し、本稿§9中段も原因未同定としている。  
   **分類:** **must-fix**。  
   **是正案:** 「測定対象が違ったことを特定できるが、符号差の原因は未同定」と両箇所を訂正する。

2. **対象:** §2 第2幕「測定契約の但し書き」  
   **主張:** 同一 campaign 内の対比較について「write-heavy と read-heavy については取れていない」は誤り。  
   **一次資料:** D496、A-2／A-6 の `raw-manifest.json` と、それぞれが束縛する rr5／rr95 の campaign WAL。  
   **確度:** **高**。実 WAL で、同じ campaign 内に stock と fixed10／fixed2 の `build_start`・`commit` を確認した。未取得なのは A-1 の登録済み配置・推定対象による測定である。  
   **分類:** **must-fix**。  
   **是正案:** A-2／A-6 の同一 campaign 対は取得済みと書き、未取得の限定を A-1 の測定契約へ絞る。

3. **対象:** §8 B-10「直列性の検査を通していない (`performance_certified: false`)」  
   **主張:** 性能未認証と、別走行での正しさ検査の有無を混同させている。  
   **一次資料:** `output/insights/2026-09-10/t2266-formal-1000us/README.md`、同 `t2266-tail-v2/t2266-backoff-static-tail-{write-heavy,balanced,read-heavy}.json`。  
   **確度:** **高**。3 report は `correctness_verified: true` と `performance_certified: false` を別々に持ち、README も trace 有効の別 build で検査済みと明記する。  
   **分類:** **must-fix**。  
   **是正案:** 「別の trace-enabled 走行で正しさは検査済みだが、trace-disabled 走行の性能値は未認証」と書く。

4. **対象:** §0 前進6・§2(c)・§8 A-4 の走行間ばらつきの取得日  
   **主張:** write-heavy／balanced を測った日を **2026-09-07** としているが、実測日は **2026-09-05**。  
   **一次資料:** `output/insights/2026-09-05/t1942-between-run-floor-write-balanced/README.md` §1・§2。  
   **確度:** **高**。日付だけでなく request `978588.nqsv`／`978589.nqsv`、投入20:31・終了20:36 JSTまで記録されている。CVの値自体は一致する。  
   **分類:** **must-fix**。  
   **是正案:** 測定日を9月5日へ直し、9月7日が収録・着地日なら別に明示する。

5. **対象:** §5・§8 A-5 の一次資料ポインタ  
   **主張:** 明示された参照先5件が不在で、日付直後の `_` を `/` に変えた位置に実在する。  
   **一次資料:** 次の実在 path。
   - `output/insights/2026-08-28/t1434-science-slice/`
   - `output/insights/2026-09-04/t2228-a2-gate-layers/README.md`
   - `output/insights/2026-09-04/t2202-missing-population-caveats/`
   - `output/insights/2026-09-04/t2211-a5-second-boot-resubmit/README.md`
   - `output/insights/2026-09-10/paper-methods-ja/methods.md`
   
   **確度:** **高**。本文の指定先の不在と、上記の実在を確認した。図の拡張子なし共通 stem は不在所見に数えていない。  
   **分類:** **must-fix**。  
   **是正案:** 5件と、それに従属する `implementation.md`／`ruling-package.md` の参照基点を実在位置へ直す。

6. **対象:** §8 B-7・§9の4文要約  
   **主張:** A-2 の `observed-positive` と A-6 の `reject` を述べた直後に「3つの独立した protocol」と書いている。  
   **一次資料:** A-2／A-6 の `certification.json`、T-1998 事前登録。  
   **確度:** **高**。そこで列挙された判定は2 protocol・3 workloadであり、第3の T-1998 の `accepted` は当該文に登場しない。  
   **分類:** **nit**。  
   **是正案:** 当該箇所を「2 protocol」に直すか、T-1998 の判定を明示して3 protocolを列挙する。

7. **対象:** 冒頭「2026-09-08以降に作られた記録は日付／slug形式である (D1941)」  
   **主張:** D1941 の日付・配置規則・例外を正確に表していない。  
   **一次資料:** **D1941（2026-09-10）**。  
   **確度:** **高**。裁定は日付直下の `topic.md` も許し、固定 path の実験・凍結資料等は旧位置を保持すると明記する。指定射影の A-6 も旧形式で実在する。  
   **分類:** **nit**。  
   **是正案:** 新規配置の原則と既存固定 path の保持例外を書き、日付だけで形式を断定しない。

**照合済み:** 指定の主要数値 **10群**を照合した。

- A-2 の4 median・2 effects、A-6 の2 median・1 effectは一致。代表例は rr5 **2,438,295 → 3,987,794、+63.5485%**。
- balanced の10標本・2 median・2 CV・ratio・improvement_percentは実 `result.json`／WALと一致。**11.225375361916456%**。
- P2-4 の3利得・6 median・無 backoff 分母は旧3 campaign の WALと一致。
- P2-5 の2 A・2 pは訂正込みの `output/campaigns/p2-5-summary.json` と一致。厳密 p は **0.0002521080185096**。
- S' の4判定、B-10 の3族 Holm p、走行間CVの3値、A-1 の3 workloadすべての **n=30／df=29／t=2.8315526875186725** は各権威資料と一致。
- 1000／999 µs の3差は両 report から計算して **−0.22／−0.27／−0.66%** と一致。

旧4 cell の訂正は妥当。stock 2 cell は `BACK_OFF=0`、adopted 2 cellだけが `BACK_OFF=1`。機構名の適応制御への訂正も pin の実装と一致した。新6 cellも、無 backoff対照3 cellと採用静的値3 cellである。

D参照124件は全て定義が存在し、T参照22件も台帳・archiveで存在を確認した。指定された **D1645、D1936項21、D1829、D1678、D1870、D1986項5、D1858** の射程は概ね正しく、A-2解除と旧fig5の恒久制限を分離できている。確認した差分では既存版・`results/`・`figures/`・`claim-evidence/` の変更は無い。

## land 可否

**NO-GO。** 所見1〜5の修正が必要。  
主要数値とA-2解除判断は支持できるが、原因同定・取得範囲・正しさ検査・測定日・参照先に誤記が残る。

## 総括

最も重いのは **所見1「符号反転の原因を同定したという断定」**。fig6正文と本稿自身の限定に反する。  
旧母集合の訂正と、correctnessを性能認証へ昇格させない基本整理は妥当である。  
静的照合のみを実施し、書き込み・commit・push・pytest・build・測定は行っていない。