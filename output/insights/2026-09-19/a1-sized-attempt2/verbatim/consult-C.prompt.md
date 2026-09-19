単独段 dispatch: stage=consult; sandbox=read-only; parent=/work/1/SFC/tanab/izanagi/.claude/worktrees/dw-a1-sized-attempt2

必読事項の射影:
- /work/1/SFC/tanab/dev-wave-jobs/dev-wave-a1-sized-attempt2/adjudication.md (親の段 4 裁定と裁定パッケージ案。点検対象そのもの。読めなければ即停止)
- /work/1/SFC/tanab/dev-wave-jobs/dev-wave-a1-sized-attempt2/brief.md (親の段 1 brief。読めなければ即停止)
- /work/1/SFC/tanab/dev-wave-jobs/dev-wave-a1-sized-attempt2/consult-B.out.md (前段の相談 B。所見 1 と裁定パッケージ候補を読む。読めなければ即停止)
- /work/1/SFC/tanab/dev-wave-jobs/dev-wave-a1-sized-attempt2/submit.stderr (既存 submit 経路を 1 回実走した拒否本文。読めなければ即停止)
- /work/1/SFC/tanab/dev-wave-jobs/dev-wave-a1-sized-attempt2/materials/d2096.md (既裁定 D2096 の逐語。項 5 を必ず読む。読めなければ即停止)
- /work/1/SFC/tanab/dev-wave-jobs/dev-wave-a1-sized-attempt2/materials/d2120-item3.md (既裁定 D2120 項 3。読めなければ即停止)
- /work/1/SFC/tanab/izanagi/.claude/worktrees/dw-a1-sized-attempt2/orchestrator/campaign/paper_story_a1_paired.py (`grep -n "_assert_no_prior_v3_bench_start\|_policy_identity\|_durable_measurement_base\|_exact_materialization_destination\|V3_SIZED"` で索引し該当関数だけ読む。全文は読まない。読めなければ即停止)
- /work/1/SFC/tanab/izanagi/.claude/worktrees/dw-a1-sized-attempt2/orchestrator/campaign/paper_story_a1_source.py (CONTRACTS 表。読めなければ即停止)
- /work/1/SFC/tanab/izanagi/.claude/worktrees/dw-a1-sized-attempt2/output/insights/2026-09-13/paper-story-a1-balanced5-sized-preregistration/README.md (§2.1・§6・§7 を読む。読めなければ即停止)
- /work/1/SFC/tanab/izanagi/.claude/worktrees/dw-a1-sized-attempt2/docs/decisions.md (`grep -n "^## D1986\|^## D1323\|^## D1295"` で見出しを索引し、D1986 前文と D1323 の決定部分だけ読む。読めなければ即停止)

上の射影以外は、必要になった箇所だけを `grep -n` で索引して読む。全文を読み込まない。
書込可能な tmp は無い。pytest の実走は求めない (静的検査でよい)。
予算が尽きそうなら、その時点の結論を下の出力形式どおりに書いて終われ (無出力が最悪)。

## 目的

これは自分たちの計測基盤の設計レビューである。A-1 balanced5 sized study の attempt-0002 (ユーザーが独立再現として 1 attempt
認可) は、既存 submit 経路の gate `_assert_no_prior_v3_bench_start` (規律 2 由来、commit abff80d1b) により、qsub の前に
`prior attempt reached the bench barrier; group rerun is prohibited` で拒否された (実走済み、副作用なし)。親はユーザーへ返す
裁定パッケージ (adjudication.md 末尾: 択 1 = 認可記録付き gate 解除、択 2 = 別 study として登録 (推奨)、択 3 = 行わない) を起草した。
**このパッケージを点検せよ。** 推奨を守らせるのではなく、通してはいけない理由を最も強い形で作り、成立しなかった攻撃は正直に
「成立せず」と書け。全項目を無理に成立させるな。

## レンズ C — 裁定パッケージの点検

1. **択 2 (別 study) は本当に既存 gate に触れないか。** 新 study の durable base・公開先が別なら `_assert_no_prior_v3_bench_start` と
   `_exact_materialization_destination` は通るか。`_policy_identity` の固定分岐・`CONTRACTS` 表・policy sha 定数・test の pin
   (`orchestrator/tests/test_paper_story_a1_paired.py`、`test_paper_story_a1_job_contract.py`、`test_a1_non_certifying_marker.py`、
   `tests/test_paper_story_a1_source.py` 等を `grep -n "sized-v1\|CONTRACTS\|_policy_identity"` で索引) のうち、何を変える必要が
   あるか file 単位で列挙せよ。D2096 項 5「3 study 目の枠組みは作らない」・D1986 前文・D1323 と、固定表への 1 行追加の関係を判定せよ。
2. **択 1 (認可記録付き gate 解除) の危険の言語化。** 規律 2 (正しさゲートを緩める変異を許さない) の射程に入るか。
   「認可があれば再走できる」経路と「性能値を見た後の再投入」を機械が区別できないという親の主張は成立するか。
   事前登録 §6.4 の閉じた列挙に「認可済み独立再現」を erratum で足すことの当否。
3. **root seed の扱い (択 2 の下位選択)。** 事前登録 §2.1 は本走の seed を pilot と別にした理由を「同じ組番号の順序 bit の共有」と
   している。独立再現で attempt-0001 と同じ seed (同じ物理順) を使う案と、新 seed を凍結する案のどちらが「同じ配置」の要求と
   事前登録の趣旨に合うか。統計的独立性への影響の有無。
4. **推奨の当否。** 親推奨 (択 2) を独立に評価し、同意 / 反対 / 根拠不足 / 既裁定誤引用 のいずれかを付けよ。第 4 案があれば書け。
   択 3 (行わない) を選ぶ場合の研究上の帰結 (attempt-0001 稿の限定 L-A1S-4 が残る) の重さも評価せよ。
5. **本 wave の停止判断の当否。** ユーザー裁定「どこかの層で落ちたら再投入せず報告して止める」に対し、submit 層の gate 拒否を
   「落ちた」と数えて止めたことは妥当か。既存経路を 1 回実走して拒否を実測した (qsub に達せず、intent・attempt root は未作成) ことの
   当否 (1 attempt の認可を消費したと見るべきか)。

## 出力形式 (見出しは全部 `##`。最後の節は必ず `## 総括` で、`### 総括` と書いてはならない)

## 所見
番号付き。各所見に 成立 / 成立せず / 根拠不足、根拠 (file:line)。

## 択 2 の変更面
file 単位の列挙 (code / JSON / docs / tests)。

## 推奨の評価
同意 / 反対 / 根拠不足 / 既裁定誤引用 と理由。第 4 案があれば。

## 総括
3〜5 行。
