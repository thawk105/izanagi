## 所見 (正しさ境界)

1. **real / must-fix — P4 は保証範囲の限定として採用できる。ただし、A-2/A-6 の証拠欠落へ拡張してはいけない。**
   一次資料：D1993、`output/insights/2026-09-16/t2630-scan-boundary-reach/README.md` §§4–6、同 `verbatim/obs-m3b.json`、A-2/A-6 の `certification.json`。
   T-2630 は、**変異した template を当てた後の identity 層**で、token・pre-image・variant ID の一致と実 TU の不一致を示した。A-2/A-6 の無変異 template に同じ問題が発生した証拠ではない。両成果物では計6 cell の `bound`、legacy 1回＋performance条件5回の correctness が記録されており、D1993 の解除を戻す根拠はない。

   対案となる限定文：

   > **(v)** `src_token` の一致だけでは、実翻訳単位全体の意味の一致を保証しない。T-2630 は、変異した template の前処理指令が include 先や別 file に及ぼす効果を identity が捉えない例を示した。当該 A-2/A-6 attempt でこの変異が発生したことや、誤った認証結果が継承されたことを示すものではなく、D1993 の取得済み判定は維持する。

   **「D1993 の4限定＋今回明示する identity の限定」と書く。D1993 自身が5限定を裁定したとは書かない。**

2. **real / must-fix — P4 の「`#define`/`#undef` の効果を pre-image に乗せない」は範囲が広すぎる。**
   一次資料：T-2630 insight §5、`orchestrator/campaign/source_digest.py`。
   欠落するのは、単独前処理では見えない**別 file・include 先への効果**である。指令によって当該 file 自身の正規化本文が変われば digest も変わる。
   対案：「前処理指令の効果を一切束縛しない」ではなく、上記1の範囲へ限定する。§9 の「要求構成を言えるようにしたのは `src_token`」も、**token 単独の完全証明**と読めないよう同時に直す。§8 にだけ注記を足すのでは不足する。

3. **refuted / must-fix相当の変更は不要 — T-2630 を理由に A-2/A-6 を未取得へ戻す、coder 経路の突破と呼ぶ、認証結果の継承まで断定する案。**
   一次資料：T-2630 insight §§5–6、`orchestrator/campaign/diff_quarantine.py`、`orchestrator/campaign/build_admission.py`。
   生指令の hole 挿入は `HOLE_ESCAPE` が拒否する。stock admission は `src_token=stock` に加え `tracked_clean` と pin を要求する。receipt 発行・実 loop skip・cache hit・workload 実行は未実測である。
   対案：限定(v)を**証明力の上限**として置く。認証不在の復活や修理完了までの利用停止は追加しない。

4. **real / should-fix —「5変異で別プログラム」を実行結果5件へ読み替えさせない。**
   一次資料：T-2630 insight §4、指定 worklog fragment。
   M4 は compile 失敗、M4b は source 水準の意味差で、この x86-64 上では該当生成コードの差を確認していない。M6 は trace 差検査を通ったが、object の trace symbol は後段 nm 検査が捕捉する対象である。
   対案：「5変異で identity 一致・TU差。実行可能性と後段の検査は変異ごとに異なる」とする。plan のこの限定は正しい。

5. **real / must-fix — 新観測を追加する際、correctness の条件差を表の近傍に残す。**
   一次資料：B-10 権威 JSON
   `/work/1/SFC/tanab/b10-backoff-grid-t2500-formal/group-report-20260915/t2500-backoff-static-tail-formal.json`、`docs/b10-backoff-static-tail-preregistration.md` §4.5、D2044項3、D2083。
   権威 JSON で、B-10 は18区間すべて `declining`、120 correctness記録すべて certified・anomaly 0 を確認した。しかし検査条件は **4 threads・200 tuples・rr50 の legacy**であり、性能条件そのものの certification ではない。

   対案：§9 の正しさ欄でも条件を省略せず、`performance_certified: false` と固定表現
   **「この事前登録の述語では、表現可能域である 9999 マイクロ秒までに飽和を観測しなかった」**
   を維持する。B-7 は同一 variant の横断比較・床値超判定を供給せず未充足。非silo較正の `accepted` も correctness の認証へ昇格させない。

6. **real / should-fix — official 完走は、判定下限の一般的な較正完了ではない。**
   一次資料：`output/insights/2026-09-16/t2698-official-floor-resubmit/README.md` §3、D2077、D2083。
   rr20 / rr80 の floor 案はそれぞれ **35,817.945 / 46,065.78**。双方とも実測 noise 項より配線下限 `0.03 × stock median` が大きく、後者で決まった。
   対案：未発効の holdout 別 floor 案として記す。A-2/A-6 の3 workloadや、B-4の相対利得差 `D` の floor に転用しない。plan はこの区別を維持している。

## 所見 (引き写し・誤り・stale)

1. **real / must-fix — 誤り：初回 official 投入日は09-11ではなく09-09。**
   一次資料：`output/insights/2026-09-09/t1851-unit-c3b-floor-range/README.md` §2。
   `988501.nqsv` は **2026-09-09 22:09 JST投入、22:10:31 RUN観測**。旧版§5のD811/D926注記、§7前半32などの09-11表記は当時から誤り。
   対案：plan の訂正を採用し、09-16の初完走という stale 更新と分ける。

2. **real / must-fix — 誤り：D1341による「現在も未land」。**
   一次資料：commit `ce2769c32`、`docs/archive/worklog-phase3-0911-1450.md` のentry 1450、旧版起点 `af3762d62`。
   `ce2769c32` が旧版起点の祖先であることを確認した。過去 insight の「未land」を旧版の現在形へ持ち込めない。
   対案：**実装・記録のlandと、official原本の退避・再配置・commitを分ける。** D2077の後者が未完でも、前者を未landに戻さない。

3. **real / should-fix — stale：較正recordの件数を、workload数や床値の種類と混同しない。**
   一次資料：`output/env/pegasus/calibration/registered/*.json`、D2083、entry 1503。
   現物は **8 record**。旧来のrr50 record 2件、silo rr95・rr5各1件、mocc rr50・rr95、tictoc rr50・rr95である。非siloは**4 record・4対**、09-15の新規取得分は**3 record**。
   対案：旧版の「mocc 1件」「TicToc測定0件」を更新する。「非silo新規3件」と「登録対象4対」は両立するため、どちらかへ統一しない。Cicadaまで測定済みにしない。

4. **refuted / should-fix不要 — 旧版§7の58項という件数。**
   一次資料：`docs/paper-story/2026-09-14.md` §7。
   チェック項目を数え直し、**前半49＋後半9＝58**を確認した。
   対案：旧版の件数は訂正しない。新版で統合・追加した場合だけ新版を数え直す。旧版の「この版で追加」を新版の取得履歴として残さない。

5. **real / should-fix —「完了証明層1/12」は、充足可能集合と評価結果を分ける。**
   一次資料：`orchestrator/campaign/s8c_preregistration_evidence.py`、`docs/phase3-8c-preregistration.md` §§5–6。
   現行コードの充足可能集合は exact `{"C10"}`。しかし、この定数だけでは**現HEADでC10が実際に充足した**ことまでは再実測できない。§5は9欄中8欄が未記入で、「検定4点」だけは `no_hypothesis_test` のJSONがある。
   対案：「充足可能なのはC10のみ」と「09-14の評価結果1／1／10」を分ける。本段は評価器を走らせておらず、現HEADの再評価済みとは書かない。plan の注意は妥当。

6. **real / should-fix — briefの誤り：凍結対象 `results/` は6稿ではなく7稿。planも明示訂正していない。**
   一次資料：`docs/paper-story/results/` の現物、READMEのresults表。
   現在は**7稿**ある。限定件数も再計数し、09-16 B-7稿は**20件**、B-10稿は**15件**で記載と一致した。
   対案：briefを「results全7稿」とするか、件数を外して**ディレクトリ全体が凍結対象**と明記する。これは旧版の誤りではなく、今回のbrief自身の誤りである。

7. **real / should-fix — staleと訂正を同じ一覧へ押し込まない。**
   一次資料：D2049、D2050、D1993、T-2630 insight。
   D1640ラベル追補未実施は後続実施によるstale。一方、D1993の「4限定」は当時の裁定内容として正しい。T-2630の発見で、その歴史的件数が誤りになるわけではない。またD2050は**同じ事前登録の第2 cohort**についてであり、「2本目の論文」の規則ではない。
   対案：限定の新規明示、追補の実施、既存誤記の訂正を別々に記す。plan本文の注意に合わせ、再導出表の「2本目cohort」もこの意味を明示する。

**追加探索の限界：** planが既に挙げたものを除き、旧版本文の新たな「当時から偽」を本段で追加確定できたとは報告しない。独自に確定した追加訂正は、今回briefのresults件数である。未確認の疑いを訂正件数へ足さない。

## 親の暫定裁定への評価

| 対象 | 評価 | 根拠・必要な調整 |
|---|---|---|
| **P1** | **同意** | B-10統制稿§3限定11。09-15 cohort図は未作成。fig8・生成器名は今回の予定仕様と明記し、実在成果物扱いしない。 |
| **P2** | **同意** | D1993、A-2/A-6権威JSON。第4文の科学的内容を変える根拠はない。旧版の「この版で書き換えた」という履歴説明は更新する。 |
| **P3** | **不同意** | 初回投入日と未land誤認も当時からの誤り。planの追加訂正を採用する。 |
| **P4** | **条件付き同意** | identityの一般保証を弱める限定として適切。A-2/A-6の取得済み判定を弱めるなら過大。fileを跨ぐ効果・template経路・未実測の下流を省くなら説明不足。 |
| **P5** | **同意** | READMEの更新契約に適合。3注記をすべて吸収し、訂正一覧をP3の修正版へ揃える。恒久erratumは残す。 |
| **plan総括** | **概ね同意** | P3修正、旧判定保持、非pool、official未発効は一次資料と整合。限定(v)の正確な文面と件数の扱いを上記へ揃える。全面再導出済みの証明として、この地図自体を使わない。 |

## GO / NO-GO

**現状のbriefとplanを併存させたままならNO-GO。次の最小修正後は執筆へGO。**

1. P3を撤回し、投入日・未land誤認の訂正を採用する。
2. P4を上記限定文へ置換し、D1993の4限定と今回の追加限定を区別する。
3. `results/`の凍結対象を全7稿へ訂正する。

追加のgate・台帳・測定・実装修理は、この執筆の前提にしない。

## 総括

T-2630はidentity層の実在する欠陥だが、A-2/A-6の認証取消しの証拠ではない。
限定(v)は採用し、template経路とfileを跨ぐ効果へ正確に範囲を絞る。
P3は誤り。planの投入日・未land訂正を採用する。
旧版58項、B-7限定20件、B-10限定15件は現物と一致した。
較正は8 record、非siloは4対、resultsは7稿である。
旧値・新値のpool、B-7充足、correctnessから性能への昇格は認めない。
書込み・commit・push・pytest・build・測定は行っていない。