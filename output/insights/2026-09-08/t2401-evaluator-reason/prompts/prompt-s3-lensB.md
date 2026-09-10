単独段 dispatch: stage=consult; sandbox=read-only; parent=/home/SFC/tanab/.claude/jobs/78b62369/tmp/t2401/brief.md

## 必読事項の射影

次の絶対パスだけを読む。読めなければ即停止し、その旨だけを出力する。

- `/home/SFC/tanab/.claude/jobs/78b62369/tmp/t2401/brief.md` — 親の段 1 brief
- `/home/SFC/tanab/.claude/jobs/78b62369/tmp/t2401/s2-plan.md` — 段 2 のプラン (攻撃対象)
- `/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2401-evaluator-reason/orchestrator/campaign/s8c_preregistration.py`
- `/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2401-evaluator-reason/orchestrator/campaign/s8c_preregistration_evidence.py`
- `/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2401-evaluator-reason/orchestrator/tests/test_s8c_cli_entrypoints.py`
- `/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2401-evaluator-reason/orchestrator/tests/test_s8c_preregistration_core.py`
- `/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2401-evaluator-reason/orchestrator/tests/test_s8c_preregistration_predicates.py`
- `/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2401-evaluator-reason/orchestrator/tests/test_s8c_gate_report.py`

上記以外の repository 内 file は、上の file から辿って必要と判明した場合だけ読んでよい。
repository の root は `/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2401-evaluator-reason` である。親側の `/work/1/SFC/tanab/izanagi` を読まない。

## この段の仕事 — レンズ B: テストの実現可能性と実効性

段 3 の敵対相談である。**プランを守らせるのではなく壊しに行く。** 親の brief 自身も攻撃対象である。実装・編集・commit はしない。出力は最終メッセージ本文にすべて書く (file へ書けない sandbox である。省略記号で途中を切らない)。

sandbox は read-only で書込み可能な tmp が無いため、**pytest 実走は要求しない。静的検査でよい。**実走していない結果を「緑」と書かない。

このレンズの攻撃面は次のとおり。すべて `file:line` を添えて具体的に述べること。

1. **fixture が物理的に構成できるかの検算 (最重要)。** プランのテスト計画は「temporary repo に 11 件しか返さない evaluator module を置いて commit し、実体の `_normalize_predicate_results` に `PreregistrationError("predicate-result-type")` を送出させる」と書く。しかし `_default_registry_module` は evaluator module を **module 名で live import** し、`Path(module.__file__).read_bytes()` を commit 側 blob と比較して不一致なら `evaluator-blob-mismatch` へ倒す (`orchestrator/campaign/s8c_preregistration.py` の該当行を読んで確認せよ)。**tiny repo 側の evaluator を 11 件返す版に差し替えると live import 側の bytes と一致しなくなり、`_default_registry_results` へ到達しないのではないか。** 到達するなら、どういう構成なら到達するかを file:line で書け。到達しないなら、`evaluator-exception` 経路を実際に踏む代替の到達方法を 1 つ以上、実現可能性つきで提案せよ。
2. **正例が機構を通るか。** 提案されている正例が、diagnostic を生む実体 (`_default_registry_results` と `_normalize_predicate_results` と診断生成 helper) を本当に通るか。両層を stub した「機構を通らない緑」になっていないか。逆に、実体を通すために必要な stub がどこまでなら許容範囲かを述べよ。
3. **変異が本当に殺されるか。** プランの `## 変異事前登録候補` の各項について、指定された test が本当にその変異を殺すかを個別に判定せよ。殺さないものは殺さないと書き、殺すために足りない assertion を述べよ。**逆に、プランのテスト集合をすべて緑にしたまま、診断機構を無効化できる変異** (診断を常に空 tuple にする、callsite を定数にする、helper を恒真にする等) を新しく 2 件以上考案せよ。
4. **既存テストへの波及。** プランは `orchestrator/tests/test_s8c_preregistration_core.py:2680-2695` の monkeypatch 対象を新関数へ合わせると書く。これは「既存テストの期待値を変えない」規律に抵触しないか。抵触しない形にできるか。他に、CLI が sibling API を呼ぶよう変えたことで壊れる既存テストを全部挙げよ。
5. **F631 が本当に閉じるか。** F631 の実際の事故は「人間が CLI を打ったら 12 条件すべて ERROR と出た」である。この差分を当てた後、**同じ事故が起きたとき人間が打つ 1 コマンドで真因が読めるか。** 読めないなら何が足りないか。`--json` を付ける人と付けない人の両方について述べよ。
6. **プランの過大・過小。** 親 brief の scope (本題の実装だけ、gate・検査・台帳・一般化の追加は scope 外) に対し、プランが過大な箇所と、逆に本題を取りこぼしている箇所を挙げよ。

## 禁止

- 実装・編集・commit・push。
- 新しい gate・検査・台帳・一般化の追加提案 (親 brief の scope 外)。思いついたら `## scope 外の所見` へ分けて書く。
- 既存テストの期待値の変更・反転・緩和・skip・削除の提案。
- 実走していないものを緑と書くこと。
- 出力に結合文字 U+0300〜U+036F を使うこと。

## 出力形式

次の H2 見出しをこの順で使う。所見は 1 件ずつ `- 所見 N (深刻度: blocker | must-fix | nit):` の形で番号を振り、**それぞれに「放置すると成果物 (certified 選択・レポート・台帳) の値・受理集合・参照がどう変わるか」を 1 行で書く。書けない所見は nit にする。**

- `## fixture の実現可能性`
- `## 正例が機構を通るか`
- `## 変異の殺し損ね`
- `## 既存テストへの波及`
- `## F631 は閉じるか`
- `## 過大と過小`
- `## scope 外の所見`
- `## 総括`

予算が尽きそうなら、その時点の途中結論をこの出力形式どおりに書いて終われ。無出力が最悪である。
