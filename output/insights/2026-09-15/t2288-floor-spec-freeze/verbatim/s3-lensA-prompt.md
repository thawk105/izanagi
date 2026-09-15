単独段 dispatch: stage=consult; sandbox=read-only; parent=/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2288-floor-spec-freeze

必読事項の射影: 次の絶対パスだけを読む。**この射影に挙げた file を読めなければ即停止し、読めなかった path を報告せよ。** 射影外の path を自分で構成して不在だったことは停止理由にしない。

- /home/SFC/tanab/.claude/jobs/f1ebd45c/tmp/wave-t2288/s1-brief.md — 親の段 1 brief (検査対象)
- /home/SFC/tanab/.claude/jobs/f1ebd45c/tmp/wave-t2288/artifacts/dev-wave-t2288-floor-spec-freeze/s2-plan.md — 段 2 plan (検査対象)
- /work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2288-floor-spec-freeze/orchestrator/campaign/floor_pair_driver.py
- /work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2288-floor-spec-freeze/orchestrator/campaign/s8b_binary_admission.py
- /work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2288-floor-spec-freeze/orchestrator/campaign/p3_b4_floor_artifact_issuer.py
- /work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2288-floor-spec-freeze/orchestrator/campaign/p3_b4_material_report.py
- /work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2288-floor-spec-freeze/orchestrator/tests/test_floor_pair_driver.py
- /work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2288-floor-spec-freeze/docs/phase3-b4-reflux-ablation-preregistration.md
- /work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2288-floor-spec-freeze/docs/decisions.md — 見出し検索で該当 D だけ読む
- /work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2288-floor-spec-freeze/docs/failures.md — 型タグを攻撃面に含める
- /work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2288-floor-spec-freeze/output/insights/2026-09-09/t2288-b4-floor-cellset/README.md
- /work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2288-floor-spec-freeze/output/insights/2026-09-13/t2288-b4-floor-aggregate/README.md

## レンズ A — 正しさ境界と凍結境界

**あなたの仕事は plan を守ることではなく壊すことである。親 brief 自身も検査対象である。**

この wave は「B-4 床値の workload 別 3 凍結 spec (`floor-pair-spec/v3`) を、較正取得と床値実測を
scope 外にしたまま凍結できるか」を判定する。親は「できない、差分ゼロで返す」と provisional に裁定している。

**このレンズが探すのは、その判定の周辺で正しさ防壁が緩む経路である。** 具体的に次を攻めよ。

1. **「凍結できない」を「弱い凍結で通す」へ滑らせる経路。** plan または親 brief が、
   placeholder・仮値・前方参照・attestation_mode の緩い値・空の `artifacts`・cell 1 件だけの spec などで
   loader を通す案へ寄っていないか。`load_frozen_spec` と `_bind_checkout_inputs` の実コードで確かめよ。
2. **「差分ゼロで返す」が、実は緩和になっていないか。** 逆向きの攻撃である。凍結を今しないことで、
   後続が「凍結前に測る」「凍結を事後に書く」余地を残すなら、それは規律 2 の向きに反する。
   事前登録 §11.1 の手順 6 (結果を見る前に別 commit で凍結) と §5 floor 欄の解除条件で照合せよ。
3. **D15 の workload 署名 gate。** 2026-09-09 の wave は「workload 一致要求は欠陥」と判定して段 3 に
   反証された。今回の plan / brief に同型の誘導が再発していないか。
4. **恒真な保証。** plan または brief が「〜を保証する」と書いた検査のうち、実際には発火しないもの、
   候補集合に含意されて常に真になるものを名指しせよ。
5. **`docs/failures.md` の型タグ**を攻撃面に使い、過去に起きた型の再発を探せ。

## 禁止

- schema / validator の拡張案を出さない (D1696)。
- workload 一致要求を外す案を出さない (D15)。
- 床値の測定・較正の取得そのものを計画しない (scope 外)。
- 新しい gate・検査・台帳・一般化を提案しない。仮想リスク向けの防壁追加は依頼が scope 外と明示している。
- file を書かない。commit しない。sandbox は read-only である。pytest 緑は要求しない。静的検査でよい。

## 出力形式

## 総括
3〜6 行。plan と親 brief の中心判定が立つか、立たないか。

## 所見
所見ごとに H3。各所見に「主張」「現物 (file:line または artifact path)」「これが real なら成果物 (certified 選択・材料レポート・台帳) の値・受理集合・参照がどう変わるか」「scope 内か外か」を書く。
**実測で確かめた所見と、読解だけの所見を明示的に分けよ。**

## 親 brief と plan の誤り
行番号・件数・「0 件」の主張を自分で現物に当たって検算した結果。無ければ「無し」。

## 本報告が保証しないこと

予算が尽きそうなら、途中結論をこの出力形式どおりに書いて終われ。無出力が最悪である。
