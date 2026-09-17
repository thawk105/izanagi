単独段 dispatch: stage=review; sandbox=read-only; parent=/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2731-cpp-normalize-dd/s4-ruling.md

## 必読事項の射影

次の絶対パスを読む。**この射影に挙げた file が読めなければ即停止**する。これは射影 file 限定の
停止規則であり、自分が推測して探した path が不在でも停止理由にしない。

- `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2731-cpp-normalize-dd/s4-ruling.md`
  — 親の段 4 裁定 (plan v2、gate の署名と正例、規律 7 の発火条件、変異登録、主張の限定)
- `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2731-cpp-normalize-dd/s5-author-out.md`
  — 実装子の最終報告 (実走 nodeid・波及列挙)
- `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2731-cpp-normalize-dd/s5-impl.diff.txt`
  — 実装差分 (commit bd21bc501 の `git show`、wave worktree)
- `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2731-cpp-normalize-dd/s5-focus-run.log`
  — 親の焦点走 log (login、実 compiler)
- `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2731-cpp-normalize-dd/s3-a-out.md`
  — 段 3 レンズ A の所見 (A-1〜A-5、主張の限定)
- `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2731-cpp-normalize-dd/verbatim-rulings.md`
  — 既裁定 (D2104 項 2 の原文 = 第 20 回 rulings 項 2)、F1016、D34、親の前提実測
- `/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2731-cpp-normalize-dd/orchestrator/campaign/source_digest.py`
  — 実装後の現物 (`_cpp_normalize`、`_CPP_ENV_PREFIX_CACHE`)
- `/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2731-cpp-normalize-dd/orchestrator/tests/test_campaign.py`
  — 実装後の現物 (新 8 node)

上記以外に repo 内を読んでよい。

## レンズ A — 正しさ境界 (実装後)

実装を守らず攻める。**裁定 s4-ruling.md 自身も検査対象**である。

1. **拒否の署名と正例。** 裁定 §3 の拒否 1 / 拒否 2 / 正例が、実装の現物で本当にその通りか。拒否が warning・skip・
   best-effort に格下げされていないか。`startswith` 検査が恒真になる経路 (prefix が空文字、cache の取り違え、`cxx` ごとの
   cache key の衝突、defines の順序依存) が無いか。
2. **剥がしすぎ / 剥がし残し。** source 先頭が prefix 末尾と同文の `#define` (H)、builtin の `#undef` → 再 `#define`、
   `-Werror=undef` との相互作用、非決定 builtin (`__COUNTER__`、`__DATE__`)、で `removeprefix` が誤る経路。
   cache に失敗結果や部分出力が入る経路。再帰呼出し (`_environment_only=True`) が空入力以外で呼ばれる経路。
3. **不変条件。** inert template = stock (`BACKOFF_FIXED` と `BACKOFF_NOINLINE` の追加供給)、`compute == baseline ⇔ 同一 pre-image`、
   `_trace_pair_diff` の比較式不変、`HOLE_ESCAPE` / nm 層不変。実装がこれらを保つか現物で追う。
4. **test の恒真化。** 新 8 node が、修正前 HEAD でどれが赤になるか (A/B/F/G/H が赤、C/D/E 緑の予測) を静的に再導出し、
   assert が実体 (`resolve` / `compute` / `baseline`) を名指しているか、G の偽 compiler が `_cpp_normalize` の argv 契約
   (`-x c++ -` と stdin) を本当に通るか、fixture を甘くしていないか、揮発 payload を焼き込んでいないか。
5. **規律 7 の発火条件との整合。** 裁定 §4 の予測表 (M3b / M6 4 node、M0 SURVIVED、baseline の variant token 同値) を
   実装の挙動から再導出し、食い違いがあれば書く。
6. **主張の限定。** 裁定 §6 の「書いてよい / 書いてはいけない」に対し、実装後に追加・削除すべき項があるか (A-1 / A-2 / A-3 の
   限界が docstring に正しく書かれているか、過大主張が無いか)。

## 禁止

- gate・検査・台帳・一般化の新設を提案しない。裁定 (a) を他案へ差し替える提案をしない。規律 2 を緩める方向を書かない。
- commit・push・file の書き込みをしない。テストの実走を成功条件にしない — **pytest 緑を要求しない。静的検査でよい。**
  親が実走した log (s5-focus-run.log) を読んでよいが、自分が実走していないものを緑と書かない。

## 出力形式

Markdown。次の H2 節をこの順で必ず置く。所見は 1 件ずつ `A6-1`, `A6-2`, … と番号を付け、各件に
**根拠 (file:line)**・**real と主張する理由**・**must-fix / should / nit の別と、放置時に成果物 (certified 選択・レポート・台帳) の
値・受理集合・参照がどう変わるか 1 行**・**是正案 (scope 内 / scope 外)** を書く。

## 所見 (real 候補)
## 拒否の署名と正例の照合
## 不変条件と規律 7
## 主張の限定の更新
## 総括

予算が尽きそうなら、途中までの結論をこの出力形式どおりに書いて終える。**無出力が最悪である。**
