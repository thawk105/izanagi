単独段 dispatch: stage=consult; sandbox=read-only; parent=/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2670-b7-three-run-materials

## 必読事項の射影

次の絶対パスだけを読む。**この射影に挙げた file が読めなければ即停止し、その旨を出力に書く。**
停止規則の射程はこの射影 file に限る — 自分で探した path が不在でも、それは停止理由にしない。

1. `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2670-b7-three-run-materials/brief.md` (親の段 1 brief)
2. `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2670-b7-three-run-materials/plan-out.md` (段 2 の plan)
3. `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2670-b7-three-run-materials/verbatim-d1993.md`
4. `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2670-b7-three-run-materials/verbatim-d1874.md`
5. `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2670-b7-three-run-materials/verbatim-b7-item.md` (版 §8 の B-7 項の逐語)
6. `/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2670-b7-three-run-materials/docs/paper-story/results/2026-09-14-b7-all-workload-regression.md`
7. `/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2670-b7-three-run-materials/output/insights/2026-09-07_t2364-paper-story-a2-certification/certification.json`
8. `/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2670-b7-three-run-materials/output/insights/2026-09-08_t2411-paper-story-a6-certification/certification.json`
9. `/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2670-b7-three-run-materials/docs/paper-story/figures/fig6_a2_certification_observed_positive.provenance.json`
10. `/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2670-b7-three-run-materials/output/insights/2026-09-08/t2411-a6-readheavy-submitted/README.md`
11. `/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2670-b7-three-run-materials/output/insights/2026-09-08/t2430-a6-readheavy-mechanism/README.md`
12. `/work/1/SFC/tanab/t1998-balanced-stock-inline-runs/t1998-balanced-stock-inline-20260913T132723Z-548740-balanced/result.json`
13. `/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2670-b7-three-run-materials/output/insights/2026-09-15/t1998-landed-main-recheck/README.md`
14. `/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2670-b7-three-run-materials/output/insights/2026-09-14_t2589-consumer-real-artifact-repair/README.md`

必要なら次も読んでよい (任意、読めなくても停止しない)。

- 同 worktree の `output/insights/2026-09-07_t2364-paper-story-a2-certification/raw-manifest.json`
- 同 worktree の `output/insights/2026-09-08_t2411-paper-story-a6-certification/raw-manifest.json`
- 同 worktree の `output/insights/2026-09-13_t2557-balanced-stock-inline/README.md`
- [T-1998] の走行の同じ dir にある `reservation.json`
- 同 worktree の `docs/phase3-main-experiment.md` の「失敗条件」節

## レンズ

**数値の出所・限定の欠落・規律への抵触。** 「この稿に載る値と限定が、一次資料が言っていること
そのものか」だけを攻める。配置や系列規則の当否は別の相談子が担当するので、そちらへは踏み込まなくてよい。

**親 brief 自身も検査対象である。** plan を守らない。plan の値の対応表を 1 行ずつ現物で検算する。

## 攻めどころ (これに限らない)

1. **plan の値の対応表の検算。** plan が指定した JSON path・節・逐語表記が現物と一致するか。
   **一致しないもの、path が存在しないもの、値が違うものを名指しする。**
   特に次を疑う — `effects` の key 名、`cells[]` の構造と median の field 名、`current_pin` の長さ、
   `attempt_id` / `source_commit` / `protocol_sha256` / `policy_sha256` / `request_ids` の実在。
2. **生標本・ばらつき・abort 率の転記元。** certification.json はこれらを持たないと plan は言う。
   実際の転記元 (A-2 = 図 6 の provenance、A-6 = attempt 記録と事後解析) に載っている値が、
   2026-09-14 稿の掲載値と一致するか。**一致しない値があれば名指しする。**
   ばらつきの定義が資料ごとに違う件 (2026-09-14 稿 §2.3) は 3 走行になっても成立するか。
   [T-1998] の変動係数の定義は資料に書かれているか、書かれていないなら何と書くべきか。
3. **[T-1998] の正しさの記録。** `result.json` に correctness 欄が無いことを現物で確かめる。
   無いとき、稿は何と書けば「検査していない」とも「certified である」とも言わずに済むか。
   **絶対規律 1 (性能は trace-disabled の別走行、正しさは trace-enabled)** の観点で、
   [T-1998] の走行について言えることの上限を定める。
4. **集計に見える形。** plan が示した主表は D1993 項 6 の「1 つの横断実験として集計しない」に
   抵触しないか。列の取り方・行の並べ方・脚注の位置で集計に読める箇所があれば名指しする。
   **A-2 の outer status が 2 workload の論理積である点が表で潰れていないか。**
5. **規律 2 と規律 7。** 稿の文面が、性能値を根拠に variant を採用してよいと読める箇所を作らないか。
   旧 attempt (`t2022-20260828c`) の判定を前後比較として読ませる経路が無いか。
   **D1874 の「事前登録前の生値を主張へ転用しない」に触れる値が、3 走行のどこかに混ざらないか。**
6. **限定の過不足。** plan の限定一覧 (既存 11 件の再指定 + 追加 12 件) に、
   **余計なもの (資料が言っていないことを言う限定) と、足りないもの**が無いか。
   特に [T-1998] 固有の限定が「資料が実際に書いていること」に収まっているかを現物で確かめる。
7. **親 brief の誤り。** brief の一次資料表・数値・前提に現物と食い違うものがあれば名指しする。
   plan が既に挙げた 7 件については、**同意するか反対するかを 1 件ずつ書く**
   (同意の追認だけで終わらせない)。

## 禁止

- file を書かない・編集しない・commit しない。read-only である。
- 新しい測定を提案しない。既存の凍結物の bytes を変える案を出さない。
- 3 走行をプールした効果量・共通の outer status・有意差・床値超の判定を作る案を出さない。
- B-7 の充足・不充足を宣告する案を出さない。
- **数値を版 (`docs/paper-story/2026-09-14.md`) や本 prompt の引用から取らない。出所は一次資料だけとする。**
  brief の引用と一次資料が食い違ったら、**一次資料が正しい**。
- plan の案を守る方向の補強だけを返さない。所見が無いなら「無い」と根拠つきで書く。
- 書込み可能な tmp は無い。pytest の緑を求めない。静的検査でよい。テストの実測は親が行う。

予算が尽きそうなら、途中結論を下の出力形式どおりに書いて終える。無出力が最悪である。

## 出力形式

次の H2 見出しをこの順で使う。各所見には `重大度: must-fix | should-fix | nit` と、
**放置したとき成果物 (統制稿・入口の表・下流の執筆) の値・受理集合・参照がどう変わるか**を 1 行で書く。

## 値の対応表の検算
## 生標本・ばらつき・abort 率の転記元
## T-1998 の正しさの記録
## 集計に見える形
## 規律への抵触
## 限定の過不足
## 親 brief と plan の誤り
## 総括
