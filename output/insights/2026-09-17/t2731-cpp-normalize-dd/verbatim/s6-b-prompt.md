単独段 dispatch: stage=review; sandbox=read-only; parent=/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2731-cpp-normalize-dd/s4-ruling.md

## 必読事項の射影

次の絶対パスを読む。**この射影に挙げた file が読めなければ即停止**する。これは射影 file 限定の
停止規則であり、自分が推測して探した path が不在でも停止理由にしない。

- `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2731-cpp-normalize-dd/s4-ruling.md`
  — 親の段 4 裁定 (plan v2、変異登録 (a)(b)、段 5〜6 の手順)
- `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2731-cpp-normalize-dd/s5-author-out.md`
  — 実装子の最終報告 (実走 nodeid・波及列挙)
- `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2731-cpp-normalize-dd/s5-impl.diff.txt`
  — 実装差分 (commit bd21bc501 の `git show`、wave worktree)
- `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2731-cpp-normalize-dd/s5-focus-run.log`
  — 親の焦点走 log (login、実 compiler)
- `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2731-cpp-normalize-dd/s3-b-out.md`
  — 段 3 レンズ B の所見 (B-1〜B-4、consumer と pin の連鎖、変異帰属)
- `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2731-cpp-normalize-dd/mutation-spec-src.json`
  — source-level 変異 spec (a) の現物 (anchor の逐語と期待 node)
- `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2731-cpp-normalize-dd/recipe-spec-v2.json`
  — recipe v2 spec (b) の現物
- `/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2731-cpp-normalize-dd/orchestrator/campaign/source_digest.py`
  — 実装後の現物
- `/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2731-cpp-normalize-dd/orchestrator/tests/test_campaign.py`
  — 実装後の現物 (新 8 node)
- `/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2731-cpp-normalize-dd/docs/dev-wave/mutation.md`
  — 変異契約 (DW-M01〜M08)

上記以外に repo 内を読んでよい (`tools/mutation_harness.py`、`tools/check_trace0_preprocess_identity.py`、
`orchestrator/campaign/p3_s4_loop_trigger_gating.py`、`orchestrator/tests/test_ccbench_spawn_sites.py`、
`orchestrator/tests/test_skip_classification.py` は一次資料)。

## レンズ B — 整合・変異の帰属・報告と実体の一致 (実装後)

実装を守らず攻める。**裁定 s4-ruling.md 自身も検査対象**である。

1. **報告と実体の一致。** s5-author-out.md の「変更した file」「実走 nodeid」「波及列挙」が s5-impl.diff.txt と現物に一致するか。
   実走したと書かれた node が焦点走 log に本当にあるか。「実装済み・未実走」の申告漏れ。
2. **consumer 整合。** `_normalize_contexts` / `_trace_pair_diff` / `canonical_source_preimage_bytes` /
   `tools/check_trace0_preprocess_identity.py` / `p3_s4_loop_trigger_gating.py` (pre-image artifact の再利用停止) が、
   実装の変更で意図せず挙動を変えないか。spawn site 登録簿と静的 call 数登録簿を触っていないか (触っていれば must-fix)。
3. **変異の帰属 (DW-M01 / M03 / M04 / M08)。** (a) の各変異について、anchor (old 逐語) が実装後の現物に exactly one で
   存在するか、期待 node が完全集合か (同じ変異で他の node も赤になるなら列挙漏れ = 期待不一致で harness が MISMATCH)、
   赤理由が一つに絞れるか (同じ入力を拒否する他層が無いか)。(b) の anchor が carrier の現物に exactly one か。
   runner の `-k` 式が 8 node だけを選ぶか (collection で他 node が混ざれば KILLED の集合が変わる)。
4. **scope。** 裁定外の gate・検査・台帳・helper・一般化を実装が足していないか。docstring が主張の限定 (§6) を超えていないか。
5. **既存テストの期待値。** 既存 test の期待値変更・skip・削除が無いか。あれば must-fix。

## 禁止

- gate・検査・台帳・一般化の新設を提案しない。規律 2 を緩める方向を書かない。
- commit・push・file の書き込みをしない。テストの実走を成功条件にしない — **pytest 緑を要求しない。静的検査でよい。**
  親が実走した log を読んでよいが、自分が実走していないものを緑と書かない。

## 出力形式

Markdown。次の H2 節をこの順で必ず置く。所見は 1 件ずつ `B6-1`, `B6-2`, … と番号を付け、各件に
**根拠 (file:line)**・**real と主張する理由**・**must-fix / should / nit の別と、放置時に成果物 (certified 選択・レポート・台帳) の
値・受理集合・参照がどう変わるか 1 行**・**是正案 (scope 内 / scope 外)** を書く。

## 所見 (real 候補)
## 報告と実体の一致
## 変異の帰属 (anchor の一意性・期待集合・単一理由)
## consumer 整合と scope
## 総括

予算が尽きそうなら、途中までの結論をこの出力形式どおりに書いて終える。**無出力が最悪である。**
