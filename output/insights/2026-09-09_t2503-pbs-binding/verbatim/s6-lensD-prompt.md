単独段 dispatch: stage=review; sandbox=read-only; parent=/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2503-pbs-binding

必読事項の射影:

- `/home/SFC/tanab/.claude/jobs/2b56bf14/tmp/dw/t2503-pbs-binding/s5-impl.diff` — レビュー対象の実装差分 (逐語)。読めなければ即停止。
- `/home/SFC/tanab/.claude/jobs/2b56bf14/tmp/dw/t2503-pbs-binding/s4-adjudication.md` — 親の段 4 裁定。読めなければ即停止。
- `/home/SFC/tanab/.claude/jobs/2b56bf14/tmp/dw/t2503-pbs-binding/s5b-author-out.md` — 実装子の報告。読めなければ即停止。
- `/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2503-pbs-binding/orchestrator/tests/test_t316_sandbox_probe.py` — 適用後の現物。読めなければ即停止。
- `/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2503-pbs-binding/orchestrator/tests/conftest.py` — 収集規約・受入台帳・site fixture。読めなければ即停止。
- `/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2503-pbs-binding/orchestrator/tests/acceptance_duration_ledger.json` — 受入台帳。巨大なので必要な範囲だけ引け。読めなければ即停止。

## 依頼

あなたはレンズ D = **受入・統合・波及**の敵対レビュー子である。実装を守るのではなく攻撃せよ。
コードを編集してはならず、commit してはならない。所見が無い項目は「所見なし」と書いてよい。

## 攻撃面 (各項目に「real / refuted」と根拠の file:line を付ける)

1. **受入全走で赤になる経路。** 新しい 2 node と helper が、repository 全体の受入で
   赤になりうる経路を列挙せよ。少なくとも次を一次資料で検査せよ。
   - 受入台帳 (`acceptance_duration_ledger.json`) の未知 node の扱い。
     **台帳を実際に検索して、新 node が不在であることと、不在が赤にならないことを確かめよ。**
   - test 収集規約・命名規約・meta-test (`conftest.py` と `test_pytest_collection_config.py` 等)。
   - xdist group 割当と並列実行時の分離。`monkeypatch.setenv` した PBS 環境変数が
     同一 worker 内の他 test へ漏れないか。
   - test 実行時間の予算 (git subprocess を 5 回叩く helper が 2 node 分走る)。
   - `subprocess` と `os` の import 追加が既存の lint / import 規約検査に掛からないか。
2. **並行実行と汚染。** helper は実 git subprocess を起動し tmp に repo を作る。
   受入が並列実行されるとき、この test が他 test を汚染する経路 (環境変数、cwd、
   git の global 設定、process 数、ファイル記述子) を検査せよ。
3. **login node と計算ノードの差。** この 2 node は正規 runner がどちらで走らせても
   同じ結果になるか。`socket.gethostname` を固定しているので login node でも通るはずだが、
   計算ノード側で追加で壊れる要素 (`/scr` の tmp、`TMPDIR`、git の可用性、
   `shutil.which("git")` の解決) を検査せよ。
4. **consumer 波及。** `t316_sandbox_backend_probe.py` の bytes が変わることで
   赤になる consumer を、間接参照を 2 段辿って列挙せよ。
   `test_official_perf_closure.py`、`test_hooks.py`、`docs/pegasus-runbook.md`、
   凍結 manifest、driver ID の独立 oracle を含めよ。
   **実際に赤になるものがあれば real 所見にせよ。無ければ「無し」と根拠つきで書け。**
5. **scope 逸脱と欠落。** 実装が本題 (束縛対象の訂正 + 負例) を超えていないか。
   逆に裁定が指示したのに実装が落としているものが無いか。段 4 裁定の
   「プラン v2」の各項目を 1 つずつ照合せよ。
6. **実装子の報告の裏取り。** 「編集は許可された 2 file だけ」「commit/add/stash/branch 操作なし」
   「制約 meta-test 全 182 node が rc=0」を、差分と現物から検証できる範囲で検証せよ。
   検証できない主張は「未検証」と明記せよ。

`docs/failures.md` の型タグ [ドリフト] [手順漏れ] [計測汚染] [テスト代表性] を攻撃面に含めよ。

## 制約

- read-only sandbox。**pytest を実走しなくてよい**。静的検査で足りる。
  実走していないものを「緑」「赤」と書いてはならない。
- 仮想リスク向けの gate・検査・台帳・一般化の追加を推奨しない。scope 外の real 所見は
  「scope 外」と明記して裁定候補として返せ。
- 所見には**成果物影響**を 1 行で添えよ。書けない所見は nit と明記せよ。

## 出力形式

見出しは H2 (`##`) で統一し、最後に `## 総括` を置く。各所見は「所見 / real か refuted か /
根拠 file:line / 成果物影響 / 提案」の 5 点で書く。結合文字 U+0300〜U+036F を使わない。
予算が尽きそうなら、途中でもこの出力形式どおりに結論を書いて終われ。無出力が最悪である。
