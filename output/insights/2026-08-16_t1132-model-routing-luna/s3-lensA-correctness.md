## 1. legacy v1/v2 parser と routing 境界

### 所見1 — `refuted`: 現行 live 経路から v1 を選ぶ経路はない

`run` は必ず `_preflight_run()` を通り、そこで `snapshot_authority(args.repo_root)` を `commit` なしで呼びます。その導出値がそのまま `codex exec -m` に入ります（[codex_worker_launch.py:1335](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1132-model-routing-luna/tools/codex_worker_launch.py:1335)、[同:1881](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1132-model-routing-luna/tools/codex_worker_launch.py:1881)、[同:2234](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1132-model-routing-luna/tools/codex_worker_launch.py:2234)）。

`commit=` を渡す唯一の production call site は、v3 receipt を読む監査経路です（[同:2852](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1132-model-routing-luna/tools/codex_worker_launch.py:2852)）。これは `check-receipt` 分岐から呼ばれ、worker を spawn しません（[同:3126](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1132-model-routing-luna/tools/codex_worker_launch.py:3126)、[同:3156](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1132-model-routing-luna/tools/codex_worker_launch.py:3156)）。したがって、提案どおり「元の引数が `commit is None` なら v2 のみ」と実装する限り、現在の live call graph に v1 fail-open はありません。

### 所見2 — `real`: parser 選択仕様はまだ fail-closed に閉じていない

プランは「live は v2、historical は v1/v2」とだけ定めています（[s2/output.md:39](/work/1/SFC/tanab/dev-wave-jobs/2026-08-16_t1132-model-routing-luna/s2/output.md:39)）。次を明文化しないと、`v2 を試して失敗時だけ v1` のような実装が二重権威を見逃します。

- live: `v2_count == 1` かつ `v1_count == 0`
- historical: `v1_count + v2_count == 1`
- v1 と v2 が各1行ある入力は、どちらかを優先せず拒否

現行 `_one_normative_line()` は単一 regex の件数しか数えません（[launch_authority.py:306](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1132-model-routing-luna/tools/dev_waves/launch_authority.py:306)）。また、`commit=` を明示すると working-tree byte 比較も省略されます（[同:377](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1132-model-routing-luna/tools/dev_waves/launch_authority.py:377)）。現在の caller は安全ですが、historical snapshot と live-eligible snapshot が同じ型で、`derive_launch()` に用途区別もありません（[同:64](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1132-model-routing-luna/tools/dev_waves/launch_authority.py:64)、[同:421](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1132-model-routing-luna/tools/dev_waves/launch_authority.py:421)）。receipt に出さない内部 `authority_format`、または historical 専用 API が必要です。

### 所見3 — `real`: historical v1 receipt の互換方針自体は成立する

v3 receipt が保存する authority は commit・3 section・digest だけです（[launch_authority.py:74](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1132-model-routing-luna/tools/dev_waves/launch_authority.py:74)、[codex_worker_launch.py:1746](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1132-model-routing-luna/tools/codex_worker_launch.py:1746)）。監査はその commit から再構築し、`as_dict()` と stage 別導出値を照合します（[codex_worker_launch.py:2852](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1132-model-routing-luna/tools/codex_worker_launch.py:2852)）。

したがって、v1 の旧 `other` を `plan_author_model` と `stage6_model` の両方へ入れ、section 順・digest 計算・`as_dict()` を変えなければ、旧 plan/author と review/fix/focus の両方を再構築できます。単純 regex 置換で壊れるというプランの指摘は正しいです。

ただし互換テストは最低でも旧 v1 receipt の「plan/author側」と「stage6側」の2 stage が必要です。片側だけでは、分割後のもう一方の field 初期化ミスを検出できません。将来の receipt 用に historical v2 正例も必要です。

### 所見4 — `real`: `stage6_model == consult_sol` は「実際に sol」を保証しない

この不変条件は値同士の等値しか保証しません。`consult_sol=luna` と `stage6=luna` を同時に置けば通ります。現行も capture 名と lane の意味を検査せず、位置で選ぶだけです（[launch_authority.py:31](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1132-model-routing-luna/tools/dev_waves/launch_authority.py:31)、[同:426](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1132-model-routing-luna/tools/dev_waves/launch_authority.py:426)）。

`check_docs` の exact literal は最終 land を止めますが（[check_docs.py:3846](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1132-model-routing-luna/tools/check_docs.py:3846)）、launcher は起動前に `check_docs` を呼びません。従って「stage6 は runtime で sol に固定」ではなく、「正規 workflow の最終検査が sol literal を pin」が正確な主張です。

### 所見5 — `real`: stage5 出力を stage6 証拠なしで land できる

文書上は段6にレビュー2本・変異・受入があります（[dev-wave.md:50](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1132-model-routing-luna/.claude/commands/dev-wave.md:50)）。しかし land API が受け取る証拠は acceptance receipt だけで（[dev_wave_land.py:123](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1132-model-routing-luna/tools/dev_wave_land.py:123)）、その schema に review/focus receipt、所見裁定、mutation ledger はありません（[同:66](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1132-model-routing-luna/tools/dev_wave_land.py:66)）。検証内容も全走 receipt と provenance です（[同:520](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1132-model-routing-luna/tools/dev_wave_land.py:520)、[同:2626](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1132-model-routing-luna/tools/dev_wave_land.py:2626)）。

従って stage5 の luna 出力は、テストが通れば stage6 sol review・変異の実施証拠なしでも機械上 land 可能です。これはv2分割が新設する穴ではなく既存の手続依存ですが、プランが stage6 を stage5 の安全根拠にするなら未閉鎖です。

さらに stage5 effort は caller 指定のままです。任意の許可 effort が forwarding され（[dev_wave_codex.py:167](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1132-model-routing-luna/tools/dev_wave_codex.py:167)、[同:233](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1132-model-routing-luna/tools/dev_wave_codex.py:233)）、launcher もその値で置換します（[codex_worker_launch.py:1891](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1132-model-routing-luna/tools/codex_worker_launch.py:1891)）。従って提案は機械的には「luna@max」ではなく「luna@caller-effort」です。

## 2. brief の P1/P2

### 所見6 — `real（限定）`: 段6は最終の独立 semantic review 層

段2は段3の異なるレンズで攻撃され（[workers.md:10](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1132-model-routing-luna/docs/dev-wave/workers.md:10)）、段5は段6のレビュー2本・焦点再レビュー・変異・受入へ進みます（[同:45](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1132-model-routing-luna/docs/dev-wave/workers.md:45)、[同:63](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1132-model-routing-luna/docs/dev-wave/workers.md:63)）。段7〜9には新しい semantic/model reviewer はありません。したがって「段6の model blind spot を別 model が後で読む層はない」は real です。

ただし「段6後には一切検出層がない」は refuted です。段7には docs commit 後の scan・影響テスト再走があり（[core.md:97](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1132-model-routing-luna/docs/dev-wave/core.md:97)）、段9には acceptance receipt と全史 provenance の再検証があります。これらはテスト化済み欠陥や stale/race を検出できますが、semantic blind spot の代替ではありません。

また、「後段が攻撃するから段2/5の未知品質変更は安全」という一般化は成立しません。D207 自身が、段2出力が後段で攻撃されても弱い起草による must-fix 漏れ・巡回増を排除できないとしています（[decisions.md:9907](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1132-model-routing-luna/docs/decisions.md:9907)）。

### 所見7 — `refuted`: T-184/T-189 がともに「未着手」は不正確

T-184 は reasoning 面を採用済みで、resource/retry だけ残っています（[phase3.md:1069](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1132-model-routing-luna/docs/phase3.md:1069)）。T-189 は妥当な model-routing 比較実験の「設計」が未了です（[同:1191](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1132-model-routing-luna/docs/phase3.md:1191)）。また brief の「A/B 未認証」も stale で、D266 は再走を認証済みと記録しています（[decisions.md:12272](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1132-model-routing-luna/docs/decisions.md:12272)）。

### 所見8 — `real`: sol→luna の品質非劣性証拠は依然ゼロ

認証されたのは段6 focused review の `high` 対 `max` であり、model 比較ではありません。D266 も非劣性・同等性を主張せず、段2/3/5の観測はゼロと限定しています（[decisions.md:12278](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1132-model-routing-luna/docs/decisions.md:12278)）。

唯一の luna pilot は n=1・非盲検・循環評価で policy 根拠から明示除外されています（[phase3.md:1052](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1132-model-routing-luna/docs/phase3.md:1052)、[decisions.md:11249](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1132-model-routing-luna/docs/decisions.md:11249)）。この wave 内の即席 n=1 を新証拠にできないという P2 の中心結論は real です。

## 3. DW-M01 事前登録

### 所見9 — `real`: 段2末尾の一覧は DW-M01 を未充足

プランの一覧は結果だけで、変異位置、mask 層、期待失敗 node の完全集合、単一赤理由を持ちません（[s2/output.md:276](/work/1/SFC/tanab/dev-wave-jobs/2026-08-16_t1132-model-routing-luna/s2/output.md:276)）。DW-M01 は前後層の拒否不存在と単一理由性をコードで確認するよう要求し（[mutation.md:5](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1132-model-routing-luna/docs/dev-wave/mutation.md:5)）、DW-M08 は失敗 node 完全集合の一致を要求します（[同:50](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1132-model-routing-luna/docs/dev-wave/mutation.md:50)）。

不足候補は次です。

- live selector を v1 許可へ倒す変異と、`_preflight_run` を通す E2E kill
- live/historical の v1+v2二重行拒否
- historical v1許可・historical v2許可の独立正例
- legacy v1 I1、v2 consult同一拒否、v2 stage6不一致拒否を各別変異
- plan、author、review、fix、focus の routing を個別に誤配線する変異
- 旧 v1 receipt の plan/author側とstage6側の2正例
- docs policy drift、parser invariant、`derive_launch` routing を別層の変異として分離

特に docs 行を直接変えると `check_docs` exact pin と parser/test が同時に赤になり得ます。単一理由性を得るには、parser invariant は synthetic repo の単一 node、policy drift は `check_docs` node、routing は独立 docs extractorとの照合 nodeへ分ける必要があります。派生関数自身から期待値を取る恒真テストは既に実害済みです（[failures.md:5520](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1132-model-routing-luna/docs/failures.md:5520)）。

## 4. 段6 reasoning effort

### 所見10 — `real`: 段6の `high→max` は正当化されず、不採用

推奨案は段6 modelを solのまま据え置きながら（[s2/output.md:23](/work/1/SFC/tanab/dev-wave-jobs/2026-08-16_t1132-model-routing-luna/s2/output.md:23)）、review/focus effortだけmaxへ変更します（[同:68](/work/1/SFC/tanab/dev-wave-jobs/2026-08-16_t1132-model-routing-luna/s2/output.md:68)）。model分割に必要な変更ではありません。

D243 はユーザーが段6限定でhighを選び、従前のmax裁定を明示 supersede した決定です（[decisions.md:11309](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1132-model-routing-luna/docs/decisions.md:11309)）。D266 も review/focus=high を「値を1つも変更しない」形で採用しています（[同:12259](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1132-model-routing-luna/docs/decisions.md:12259)）。新しいmodel証拠も、solのままmaxへ戻す因果理由もありません。

なお reasoning変更自体は brief に明記済みです（[s1-brief.md:3](/work/1/SFC/tanab/dev-wave-jobs/2026-08-16_t1132-model-routing-luna/s1-brief.md:3)）。brief が落としたのは `workers.md` という変更アンカーであって、変更要求そのものではありません。

**結論: 段6 の effort 変更は不採用。S06-A/C と既存 high pin は維持する。**

静的検査のみで、pytest/checkerは実走していません。編集なし、worktreeはcleanです。

## 総括

- **NO-GO（現プランのまま）**。parser分割自体は修正可能だが、安全性の根拠が閉じていない。
- live v1 fail-open は refuted、historical v1互換は成立するが、二重grammar拒否とv1/v2歴史正例が必要。
- stage5 luna@max と必須stage6再検査は機械束縛されず、landはreview/mutation証拠を要求しない。
- sol→lunaの有効な品質証拠ゼロはrealだが、T-184/T-189未着手・A/B未認証という記述はstale。
- 段6 effort変更は不採用。DW-M01の層別・単一理由・完全node事前登録を作り直す必要がある。