単独段 dispatch: stage=consult; sandbox=read-only; parent=/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2503-pbs-binding

必読事項の射影:

- `/home/SFC/tanab/.claude/jobs/2b56bf14/tmp/dw/t2503-pbs-binding/brief.md` — 親の段 1 brief。**これ自身も検査対象**。読めなければ即停止。
- `/home/SFC/tanab/.claude/jobs/2b56bf14/tmp/dw/t2503-pbs-binding/s2-plan-out.md` — 段 2 の plan。読めなければ即停止。
- `/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2503-pbs-binding/tools/pegasus/probes/t316_sandbox_backend_probe.py` — 修正対象。読めなければ即停止。
- `/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2503-pbs-binding/orchestrator/tests/test_t316_sandbox_probe.py` — 負例を置く単位。読めなければ即停止。
- `/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2503-pbs-binding/orchestrator/tests/test_hooks.py` — 3060-3350 行付近に t316 の dispatch 分類がある。読めなければ即停止。
- `/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2503-pbs-binding/orchestrator/tests/test_official_perf_closure.py` — 88 行付近に t316 の path がある。読めなければ即停止。
- `/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2503-pbs-binding/docs/pegasus-runbook.md` — 541 行付近の分類表。読めなければ即停止。

## 依頼

あなたはレンズ B = **整合・実効性**の敵対検証子である。plan を守るのではなく攻撃せよ。
親 brief の前提・実測値・一般化も同じ強さで攻撃せよ。plan に賛成する所見は書かなくてよい。
コードを編集してはならず、commit してはならない。

## 攻撃面 (各項目に「real / refuted」と根拠の file:line を付けて答える)

1. **consumer 閉包の取り逃がし。** この変更で bytes が変わる `t316_sandbox_backend_probe.py` を
   束縛・参照している場所を、**path 検索だけでなく間接参照を 2 段辿って**列挙せよ。
   file 全体の sha256 golden、行番号 pin、正規表現アンカー、role 名・group 名など path 以外を
   key にする pin も検索せよ。親 brief は「凍結 pin 不在」と書いている — これを反証できるか。
2. **受入で赤になる経路。** 新しい test node を足したときに赤くなりうる検査を列挙せよ。
   受入台帳 (`orchestrator/tests/acceptance_duration_ledger.json`)、収集規約、xdist group、
   test 実行時間の上限、`tools/check_docs.py`、hooks の dispatch 分類 (`test_hooks.py`) を含めよ。
   親 brief の「未知 node は unknown 扱いなので赤にならない」を一次資料で検証せよ。
3. **plan の実効性。** plan の負例が実際に collect され、実行され、期待どおり失敗するか。
   fixture が用意する git repo の作り方 (`git init` の可否、user.name/email の不在、
   sandbox での subprocess 実行、`.gitignore`、`git status --porcelain` の出力) に穴が無いか。
   `_run_command` が使う timeout・環境変数の扱いも見よ。
4. **scope 逸脱。** plan が本題 (束縛対象の訂正 + 負例) を超えて、新しい gate・検査・台帳・
   一般化・framework・互換層を足していないか。足しているなら real 所見にせよ。
   逆に、本題に必要なのに plan が落としているものがあれば書け。
5. **親の実測値とその一般化。** brief が挙げた commit (`5e12db6ce`、`0218acc61`)、
   receipt の sha256 (`44a35985…31b32`)、file の sha256 (`d7607e0a…ce802`)、blob
   (`32644847…2ef0`)、「`test_t316_sandbox_probe.py:1282` が `_execution_binding` を
   monkeypatch している」を一次資料で検証し直せ。誤りは real 所見にせよ。
   また brief が 1 例から族へ一般化している箇所があれば指摘せよ。
6. **変異の帰属。** 段 6 の変異走で「比較対象を誤らせる変異」を作るとき、その変異が
   plan の負例**以外**の test で先に殺されてしまい、負例の検出力が測れなくなる可能性を検査せよ。
   誰が殺すかを file:line で予測せよ。
7. **所有範囲。** 実装子が触るべき file と触ってはいけない file を列挙せよ。
   docs の更新が必要になるか (`docs/pegasus-runbook.md` の分類表など) を判定せよ。

`docs/failures.md` の型タグ [ドリフト] [手順漏れ] [テスト代表性] [計測汚染] を攻撃面に含めよ。

## 制約

- あなたは書込可能な tmp を持たない read-only sandbox で走る。**pytest を実走しなくてよい**。
  静的検査で足りる。実走していないものを「緑」「赤」と書いてはならない。
- 仮想リスク向けの gate・検査・台帳・一般化の追加を推奨しない。scope 外の real 所見は
  「scope 外」と明記して裁定候補として返せ。

## 出力形式

見出しは H2 (`##`) で統一し、最後に `## 総括` を置く。各所見は「所見 / real か refuted か /
根拠 file:line / 提案」の 4 点で書く。結合文字 U+0300〜U+036F を使わない。
予算が尽きそうなら、途中でもこの出力形式どおりに結論を書いて終われ。無出力が最悪である。
