## 所見一覧 (番号・real/refuted・must-fix/nit・scope 内/外・根拠 file:line)

以下、`brief` / `plan` は `/home/SFC/tanab/.claude/jobs/1031d339/tmp/wave/` 配下の `s1-brief.md` / `s2-plan.md`、`test` は `orchestrator/tests/test_pegasus_dispatch_compute.py`、`production` は `tools/pegasus/dispatch_compute.py` を指す。判定は静的検査のみ。

1. **real / must-fix / scope 内 — 変異 A の期待赤 node が完全集合になっていない。**
   plan:110 は `[repo-current]` を「環境依存なので必須赤に指定しない」とする。しかし旧検査へ戻すと、checkout、ユーザー名、basetemp のいずれかに `release` があれば、この node も赤になる。期待集合を必須部分集合として扱うことは DW-M08 に反する。A の走行対象を `[repo-release-path]` 一つに限定すれば、環境によらず期待集合を固定できる。
   根拠: plan:92,110、test:2583–2592、docs/dev-wave/mutation.md:60–61。

2. **real / must-fix / scope 内 — テスト側変異と新旧両走の登録が不足している。**
   A は production 変異ではなく、test file の検査を旧式へ戻す変異である。plan の matrix は変更後テストだけを対象としており、変更前 HEAD 版との比較がない。また、A の予定 anchor は旧 HEAD に存在しないため、そのまま同一置換を旧版へ適用できない。
   B は旧検査も拒否するので、「新テストだけが handshake を検出した」とは報告できない。本 wave の差分は **path による偽赤の解消と、handshake 拒否の維持**である。この区別を新旧比較へ明記する必要がある。
   根拠: plan:84–110,124–142、test:2592、docs/dev-wave/mutation.md:7–10,63–64。

3. **real / must-fix / scope 内 — brief の P2 は plan の安全な限定を正本へ反映する必要がある。**
   brief:26–27 の「`str(_REPO)` と `str(tmp_path)` の両方（と quote 形）を除く」だけでは、全域置換とも読める。全域置換では、本文に追加された同じ path を含む marker 操作まで削って `release` の証拠を隠す経路がある。また path の除去だけでは、独立して埋まる job name は除去できない。
   plan:53–57 の **代入名・directive を含む位置指定＋完全な値だけの置換**に統一すべき。plan 通りなら `REPO=<値>; wait_for_release` の末尾や別行の `RELEASE=1` は残る。
   根拠: brief:26–27、plan:46,53–57、production:863,866–872。

4. **refuted / nit / scope 内 — quote 形と生 path の二重置換は必須ではない。**
   production は各 path を常に `shlex.quote(str(path))` で埋める。したがって、その完全表現を同じ方法で再構成して除けば十分。空白だけなら生 path が引用符内に連続して残る場合もあるが、単引用符入り path は shell の引用区切りによって分断され、生文字列だけの置換では残存し得る。plan の `repo release's checkout` はこの差を扱う入力になっている。
   根拠: production:866–872、plan:55,64–66。

5. **refuted / nit / scope 内 — P3 は追加 gate ではなく、指定された正例対照の具体化である。**
   同 test の入力を増やす parametrize は、依頼の「repo path に release を含む fixture」に対応する。`_job_script` は path の結合・文字列化だけで、実在確認も script 実行も行わない。plan の絶対合成 path も、例示された `_REPO.parent / "scope-release" / _REPO.name` も、静的には問題なく生成へ渡せる。後者は実 checkout の `while` 等も継承するため、plan の独立した合成 path の方が対照として明確。
   repo 全体の検索では、旧 node の参照は test 定義、duration ledger、docs、過去の収集・変異記録だった。稼働する node 固定 allowlist は見つからなかった。新 node の duration は `1.0` に fallback する。
   根拠: test:2579–2589、production:845–858、orchestrator/tests/acceptance_duration_ledger.json:13320、tools/acceptance_shards.py:397–404、output/insights/2026-08-26/t360-mutation-transport-task/mutation-ledger.json:562。

6. **refuted / nit / scope 内 — P1 の「狭い同一行共起では検出力が落ちる」という前提は正しい。**
   現行 assert は `RELEASE=1` 単独行もコメント中の `release` も拒否する。同一行の marker 参照を必須にすれば見逃す。ただし、これは「すべての release 行が handshake である」証明ではない。FA-4 が禁じるのは親→job の待機関係であり、plan の方式はその保守的な代理検査である。plan:34 の説明を維持し、構文解析を実現したとは称さないこと。
   根拠: brief:23–25、plan:19,28–34、test:2592、verbatim/FA-4-T188.md:1。

7. **real / nit / scope 外 — `while` による F1022 型の偽赤は残る。裁定パッケージ候補。**
   worktree や basetemp に小文字の `while` が含まれると、元 script に対する既存 assert が赤になる。今回それを触らない判断は依頼の「本題の検査置換だけ」と整合する。一方、brief:4,16 の「repo path の語に依らず」「path だけで反転しない」という無限定な完了条件は成立しない。**brief の表現を release 検査についての保証へ限定する修正は scope 内で必要**。
   根拠: test:2593、brief:4,15–16,30、plan:76–80、production:866–872。

8. **refuted / nit / scope 内 — plan の現物参照に行番号・名称の誤りは見つからなかった。**
   対象 test の 2579–2593、production の 828–831・863・866–872・890–892、consumer の 1054–1073・1115–1131・2290–2313・5924–5937、および追加呼出し 4080・4142・5055・5340・6119・6616 を照合した。`_job_name`、`_COMPUTE_MARKER_NAME`、`_REPO` の参照も一致。production の B/M0 anchor と現行 release/while 連続 assert は、文字列出現数を各 **1** と確認した。新 A anchor は未実装なので未確認。
   根拠: plan:7–11,40–48,116–124,150–155,170、test:24,2579–2593、production:82,828–831,890–892。

9. **refuted / nit / scope 内 — 同じ `release` 語不在検査が別 test に残るという証拠は見つからなかった。**
   repo の test ファイルについて `not in script`、`not in .*lower()`、`release` と `not in` の組合せを検索した。script/path に対する同種の `release` 不在検査は対象の一件のみ。`test_dev_wave_land.py` の `lease_release` 不在検査は payload 等に対する別契約である。したがって、この穴を理由とする wave 名の `release` 禁止は、修正の実測確認後には撤去可能と判断する。**全 path 語への耐性まで保証するものではない。**
   根拠: test:2592–2593、orchestrator/tests/test_dev_wave_land.py:9674,9693,10075、verbatim/F1022.md:17–19。

## 残る環境依存文字列の表

| 要素 | repo path だけ除去した場合 | plan の7値置換後 | 根拠 |
|---|---|---|---|
| `REPO` / `DISPATCHER` | 正しく quote 処理しなければ残る | 完全な埋込み値は除去される | production:870–871 |
| `RESULT` / `PROBE` / `REQUEST` / `MARKER` | ユーザー名・basetemp の `release` が残る | 各完全 path を除去するため残らない | production:866–868,872 |
| pytest の test basename | submission path に残る | path とともに除去される | test:2584–2586 |
| `job_name` | path 除去とは独立して残る | `#PBS -N` の値として除去される | production:831,847,863 |
| hostname | 実際の hostname は生成時に入らない | `$host` と `hostname` という固定本文が残る | production:882–889 |
| 環境変数 | 実値ではなく `$PATH`、`${PBS_JOBID:-unknown}` 等の参照が残る | 同左。生成時の環境にある `release` は転写されない | production:878,889,910–913 |
| interpreter candidates・queue 等 | 固定値 | 固定値のまま | production:65–66,408–412,857–860 |
| hash・walltime | 本 test では固定引数 | 固定値のまま | test:2587–2588 |
| 元 script の path | `while` を含めば別 assert が赤 | release 用本文の正規化とは無関係に赤 | test:2593 |

既定の test basename 先頭30文字は `test_compute_marker_is_cross_n`、job name に使う先頭10文字は `test_compu`。現 test では job name 自体に `release` は入らない。ユーザー名や basetemp の `release` は親ディレクトリ由来なので job name へは伝播しないが、4本の submission path へは伝播する。

## 変異登録への修正案 (anchor・期待 node・単一理由性)

node を次のように定義する。

- **C** = `orchestrator/tests/test_pegasus_dispatch_compute.py::test_compute_marker_is_cross_namespace_evidence_without_release_handshake[repo-current]`
- **R** = `orchestrator/tests/test_pegasus_dispatch_compute.py::test_compute_marker_is_cross_namespace_evidence_without_release_handshake[repo-release-path]`
- **O** = 変更前 HEAD の同関数名、parameter suffix なし。

| 登録 | anchor・対象 | 期待失敗集合 | 単一理由性・注意点 |
|---|---|---|---|
| baseline | 変更後 C/R | 空集合 | 元 script の `while` 偽赤がない実行環境を確認する |
| A：旧検査復帰 | plan:100–106 の test 側 anchor。実装後に一意性確認 | **R のみを走らせ、`{R}`** | 合成 repo path の `release` による旧 assert の拒否。C を走らせるなら、その環境での完全な期待集合が別途必要 |
| B：handshake 注入 | production:890–892 の一意 anchor に `${{MARKER}}.release` の `until` 行を追加 | C/R だけを走らせ、`{C,R}` | marker 名と `mv` の順序は維持。`until` なので `while` assert による拒否を追加しない |
| M0：コメント | 同じ production anchor に plan:139 のコメントを追加 | 空集合 | mutated diff で注入実在を確認してから equivalent とする |
| 旧 HEAD 比較 | 旧版用 anchor/node を別登録 | B は `{O}`、M0 は空集合を期待 | release のない環境で比較し、B は新旧とも検出することを記録する |

新旧比較では、release-path 入力に対する **旧赤／新緑**を独立して示すこと。旧版には `repo_root` 引数も R node もないため、旧版に同じ入力を与える fixture 変更箇所を別途事前登録する必要がある。A の変更後専用 anchor を旧版へ流用してはならない。

B の期待集合は、対象 C/R に走行を限定した場合のもの。consumer を含む広い走行の期待集合を、静的検査だけで `{C,R}` と断定しない。生成 script を実行する経路へ B を流せば待機が発生し得るため、焦点検査の走行範囲を登録時に明確にする。

また、P2 の限定性は、実装レビューで「値の削除」になっていることを確認する。行全体削除への逸脱は `REPO=<値>; wait_for_release` を隠すため不採用。

## 裁定パッケージ候補

- **`while` 偽赤の別件対応 — real / nit / scope 外。**
  対象は test:2593。path に `while` を含む場合の同型問題は残る。今回の実装へ含めず、必要なら正規化本文に掛ける別件として裁定する。今回の完了説明は release に限定する。

- **暫定防壁の撤去。**
  別 test に同種の `release` 不在検査は発見されず、継続が必要という real 所見はない。正例対照・handshake 負例・受入を親が実測した後、F1022 に対応する `release` 禁止の撤去を記録できる。`while` の残存問題を理由に、無関係な `release` 禁止を維持する必要はない。

## 総括

plan の位置限定置換と P3 は静的には妥当。ただし、**A の期待 node 完全集合、新旧両走の登録、brief の除去方式と保証範囲**を修正する必要がある。P1 は検出力維持の代理検査として扱い、handshake 構文を厳密に判定したとは報告しない。

ファイル変更・pytest 実行は行っていない。緑、KILLED、SURVIVED はいずれも未実測。
