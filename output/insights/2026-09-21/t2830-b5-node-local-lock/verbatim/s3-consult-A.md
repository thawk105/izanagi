静的検査のみ実施しました。テスト・変異実走・計測・投入は未実施です。brief は、13:45 追補に加えて D2200 を記した追補2まで読みました。

## 1. lock の被覆

**判定: refuted（被覆漏れなし）。**

B-5 分岐内の driver 直前で export すれば、現行 B-5 の取得箇所を覆います。

- `p3_s4_loop_pegasus.sh:648–662` では全 arm が同じ driver 起動を通る。
- `b5_generator_contrast.py:478–509` の slot 起動は `env={**os.environ, ...}` で環境を継承する。実呼出しは同ファイル `:592`。
- `lock.py:24–34,49–54` は取得時に環境変数を参照する。
- performance verify は `pipeline.py:2399`、bench は `:1386` で取得する。

fanout による上書きも、この経路では発生しません。[pipeline.py:2422](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2830-b5-node-local-lock/orchestrator/campaign/pipeline.py:2422) の分岐は `BACKOFF_REPRO` 限定ですが、B-5 の stock・機械生成・LLM は `p3_s4_loop.py:3407–3413` で `BACKOFF_SWEEP` を使います。worker 自体も `verify_fanout_worker.py:183–184` で generator を限定しています。

worker の上書き先は `:534–536` の task-local `/scr/.../bench.lock` ですが、これを B-5 の被覆漏れとは数えません。

親の「driver 内部でだけ取る」は、**driver の子プロセス以下を含む意味なら正しい**です。B-5 driver 自身が flock する意味ではありません。prebuild の `buildcache.prepare_masstree_fetchcontent`（`buildcache.py:2034–2110`）は configure/build であり、bench lock は取得しません。

## 2. 規律2：正しさゲートを緩めない

**判定: refuted（判定手順・critical section の変更なし）。**

`pipeline.py:2180–2189` は全 repetition を順に実行し、1件でも失敗すれば返ります。この呼出し全体が `:2395–2433` の lock 内にあります。trace と verifier の選択・実行は `:504–524` 以下であり、提案変更はそこに触れません。

legacy verify は従来から lock 外です（`pipeline.py:1642–1648,2434–2435`）。全 pass 成功後にのみ `:2440` へ到達する構造も維持されます。

ただし、**同じ lock を共有する相手の範囲は狭くなる**ため、計測環境への影響は項目3と分けて扱う必要があります。

## 3. F3：計測汚染と親の実測の一般化

**判定: real — must-fix（成立範囲の説明）。コード変更の撤回要求ではありません。**

「自分の scheduler request が別ノードになる」という前提の下では、4 job 間の CPU/cache/メモリ帯域競合は新たに生じません。別ノード同士を home lock で直列化することに、これらの資源の単独性を守る意味はありません。

一方、[brief.md:34](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2830-b5-node-local-lock/brief.md:34) の前提は、同一ノードに残る同ユーザーの別 campaign・手動起動 process まで排除しません。従来それらが home lock を取得していたなら、B-5 は今回から相互排他しなくなります。`lock.py:12–13,47` が説明する machine-wide 排他からの縮小です。

既存 probe は残りますが、`pipeline.py:1394–1408,2405–2431` は**観測後に実行する構造**であり、別 lock を使う2 process の「双方が競合なしと観測してから開始」を原子的には防ぎません。したがって brief `:36–37` は、probe を排他の代替保証として読めないよう限定すべきです。[F3:381](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2830-b5-node-local-lock/docs/failures.md:381) も、割当てが専有保証ではないとしています。

B-10 `:278–280`、A-5 `:257–259` も job 固有 scratch を使うため、この限界は同じです。先例は実装の根拠にはなりますが、単独性の証明にはなりません。

**放置時の成果物への影響:** 同居が起きれば、検知時は machine-failure／score 欠測、見逃せば throughput・endpoint・score が汚染され得ます。verifier 成功による certified は、性能の無汚染まで証明しません。

**追加判定: real — nit（数値の証拠区分）。**

brief `:3–4` の「59%＝8.8 h が待ち」「並列化しても総 wall が縮まない」は断定が強すぎます。[d2199.md:13](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2830-b5-node-local-lock/verbatim/d2199.md:13) は、flock 待ちを直接計測していないと明記しています。「台帳区間とコードからの帰属・推定」と記述すべきです。build や legacy verify まで直列化されるわけでもありません。

**放置時の成果物への影響:** 既存 score／certified は変わりませんが、本走の所要・walltime 判断に推定値を確定値として持ち込むおそれがあります。

## 4. 既存3経路の argv 不変

**判定: refuted（完全一致を検査している）。**

`test_p3_s4_loop_job_contract.py` の該当箇所は次のとおりです。

| 対象 | 完全一致の根拠 |
|---|---|
| proposal／fixture、stock 未設定・`0` | `:1892–1910`。独立した期待配列に対し `history == [expected]` |
| proposal＋pair、K2 pair | `:1914–1927`。`--stock-control` を含む全配列を比較 |
| 空白入り manifest の K2 | `:1432–1445`。起動回数と全 argv を比較 |

したがって [s2-plan.md:87](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2830-b5-node-local-lock/codex/s2-plan.md:87) の説明は正しいです。`in` 検査だけの別テスト（`:1462–1465`）との混同はありません。

現行観測は JSON 化した文字列配列です。提案する NUL 区切り bytes と独立期待値の比較は、その上に bytes 契約を追加するものです。

## 5. launcher・tree 分離の実効性

**判定: real — must-fix（不要な受入条件の追加）。cwd の設計自体は refuted。**

各 command に tree を保持して `runner(argv, cwd=tree.repo)` を呼ぶ設計なら、相対 `JOB_BODY` と `IZANAGI_S4_REPO_ROOT` は同じ tree を指します。根拠は `b5_contrast_launch.py:183,208–214,238` とプラン `:61,66–72`。job body も `p3_s4_loop_pegasus.sh:169,281` で当該 repo に移動します。

通常の独立 checkout 配置なら、同一 HEAD でも次は分かれます。

- CCBench: `p3_s4_loop.py:3428–3429`
- cache: 同 `:3444`
- `patchharness.checkout` の base: 同 `:3087,3517,3573`
- 一時 worktree: `patchharness.py:360–364`

問題は [s2-plan.md:49](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2830-b5-node-local-lock/codex/s2-plan.md:49) の **`common_repo` 不一致拒否**です。同一 HEAD・別 path・独立 CCBench/cache の4 clone は目的を満たすのに、この条件で拒否されます。現行 validator `:78–108` にこの制約はなく、依頼逐語も同じ common repo を要求していません。

既存関数内へ置いても、新しい受入条件であることは変わりません。重複 tree の拒否とは分け、common repo 一致要求はプランから外すべきです。

また、親が観測した CCBench git dir の独立性を validator の一般保証とは扱えません。現行 `:94–106` は checkout root・PIN・tracked cleanliness を検査しますが、CCBench の common git dir 同士は比較しません。プラン `:81` の主張は、親が供給する独立配置を前提として維持するのが適切です。

**放置時の成果物への影響:** 有効な4 clone 配置が投入前に拒否され、台帳・score が生成されません。certified の誤受理ではなく不要な拒否です。

## 6. D2205 の維持

**判定: refuted（提案変更による破壊なし）。**

B-5 は `p3_s4_loop_pegasus.sh:79–81` で pair 入力と排他的です。pair は `:152–156,665–672` の1 driver 起動を維持します。B-5 slot の `--stock-control` 単独も `b5_generator_contrast.py:484` のままです。

プランは `loop.py`／`p3_s4_loop.py` を編集せず、`STOCK_PINS`、pair の argv・rc 検査も保持するとしています（プラン `:155`）。認可 session・claim 再照合・結合検査の変更は含まれていません。

これは静的な変更範囲の判定であり、結合検査の実走合格を意味しません。

## 7. 恒真ゲート・テスト代表性・変異帰属

**判定: real — nit（削除変異の失敗先の記述）。観測テスト自体の恒真性は refuted。**

プラン `:137` は fake driver の限界を明示しています。検査できるのは shell→driver の環境伝播であり、実 flock、ノード間の独立性、性能改善ではありません。この説明は適切です。

変異候補の静的な帰属は以下です。

| 変異 | 判定 |
|---|---|
| home／other.lock へ変更 | 独立した exact path 比較で検出可能 |
| `export` 除去 | lock 未設定入力のケースなら検出可能。継承済み入力だけでは export 属性が残り得る |
| B-5 分岐外へ移動 | default／pair の環境観測で検出可能 |
| 全 arm を random tree に戻す | 全4件の環境・argv・cwd 比較で検出可能 |
| cwd だけ先頭 tree にする | submit テストの **rc=0** ケースで検出可能。rc=9 は最初の job で止まるため単独では検出不能 |
| pair 引数削除／fixture 20→21 | 既存の全 argv 比較でも検出可能 |
| 重複 repo 拒否を無効化 | 提案する負例で検出可能 |
| common repo 比較を無効化 | テストは失敗し得るが、項目5の不要条件を守る負例であり、必要な欠陥検出とは数えない |

削除変異について、プラン `:163` が指定する `test_b5_fragment_mutants_have_one_static_failure` は、正常 source から内部で変異を作る**メタテスト**です（[test_p3_s4_loop_job_contract.py:1969](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2830-b5-node-local-lock/orchestrator/tests/test_p3_s4_loop_job_contract.py:1969)）。外部で既に export を削除すると `:1971` の出現回数前提で失敗します。これを環境伝播の検出へ帰属させてはいけません。

削除の実効的な失敗先は、通常の静的契約テスト `:577–578` と、追加する B-5 環境観測です。メタテストが内部変異を期待どおり拒否した結果とは分けて記録してください。

**放置時の成果物への影響:** B-5 台帳・score・certified は直接変わりませんが、変異結果が防護の実効性を過大表示します。

## 総括

B-5 直前の export、子への環境継承、verify／bench の lock 被覆、既存3経路の argv 比較、D2205 維持は成立しています。

修正必須は、**probe が job 間排他を代替するという一般化を避けること**と、**common repo 一致という不要な受入条件を外すこと**です。数値の証拠区分と削除変異の帰属も修正してください。

新しい gate・検査・台帳は提案しません。common repo 一致条件を維持する判断は、本依頼の scope 外の裁定パッケージ候補として分離する必要があります。