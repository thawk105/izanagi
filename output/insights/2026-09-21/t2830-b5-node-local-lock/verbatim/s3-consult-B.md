## 1. (P2) の根拠

**判定：real — brief の因果説明は誤り。refuted — job ごとの submit-tree 対応自体は残す。**

build は bench lock の外で走る。trace/perf の build は [pipeline.py:2016](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2830-b5-node-local-lock/orchestrator/campaign/pipeline.py:2016)、performance verify の lock 取得は同ファイル `:2399`。系列開始 stock は探索や LLM handshake より先に実行されるため、**最初の stock build は現行の共有 lock でも並行に到達可能**である。[b5_generator_contrast.py:697](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2830-b5-node-local-lock/orchestrator/campaign/b5_generator_contrast.py:697)

試走については、次を区別すべき。

- 「4 job がほぼ同時に開始」は正確ではない。3 job は投入後13秒、LLM は6分25秒後に RUN。[insight-8.md:25](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2830-b5-node-local-lock/verbatim/insight-8.md:25)
- 記録された成功機序は「先着の公開を後続が cache hit」。時刻差と cache hit は二者択一ではなく、後続が公開・claim 解放後に到達したから hit できたという関係。ただし、claim 到達時刻の差や、その差を生んだ前処理までは提示資料から確定できない。[d2199.md:16](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2830-b5-node-local-lock/verbatim/d2199.md:16)
- 59% は flock 待ちを直接測った値ではなく、session wall 内訳からの推定。これを build 同時性増加の実測根拠にはできない。[insight-6-3.md:9](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2830-b5-node-local-lock/verbatim/insight-6-3.md:9)

lock 分離で後続 session の進行が速まり、単位時間当たりの build 要求が増える可能性はある。しかし、同時 build が必ず増える、まして本走が必ず落ちるとは静的には言えない。

それでも tree 分離には独立した根拠がある。隔離 worktree を使っても cache root は submit-tree 内に残る。[p3_s4_loop.py:3444](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2830-b5-node-local-lock/orchestrator/campaign/p3_s4_loop.py:3444) 同じ namespace・digest に到達すると、既存 claim は完成 entry より先に拒否され、claim 取得競合にも待機・retry がない。[buildcache.py:2716](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2830-b5-node-local-lock/orchestrator/campaign/buildcache.py:2716)、同 `:2222`。系列開始 stock が成立しなければ系列も終了する。[b5_generator_contrast.py:702](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2830-b5-node-local-lock/orchestrator/campaign/b5_generator_contrast.py:702)

**残す最小の差分：** tree 分離対応は残し、brief `:29–30` を「lock 変更前から存在する共有 cache の同時 claim リスクを、job ごとの独立した cache 配置で除く」に差し替える。「同時性が上がるので本走が落ちる」は削除する。

## 2. 新しい検査の混入

**判定：real — `previous_trees` と common repo 一致の拒否は削れる。path を分ける必要性そのものは refuted。**

[s2-plan.md:49](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2830-b5-node-local-lock/codex/s2-plan.md:49) は、既存 validator に新しい拒否条件を足している。「独立した検査コマンドではない」という同 `:64` の説明では、依頼の「検査の追加は scope 外」を解消できない。

common repo 一致は cache 分離の必要条件ではない。同じ HEAD の別 clone でも、各 checkout の CCBench/cache が独立していれば目的を満たす。`common_repo` の現用途は出力先を repository 外に制限することであり、全 tree で一致させることではない。[b5_contrast_launch.py:165](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2830-b5-node-local-lock/tools/pegasus/b5_contrast_launch.py:165)

一方、同じ path を4回渡せば共有 cache に戻る。この指摘は正しい。ただし、**異なる tree を供給する条件**と、**誤った入力を新たに runtime で拒否する機能**は分けられる。親が4本を準備する P3 の下では、後者を実装しなくても本走用の正しい配置は構成できる。

**残す最小の差分：** `validate_submit_tree` は変更せず4回利用する。実装は job ごとの tree 選択に限定し、異なる4 path が env・argv・cwd に届くことをテストする。common repo 比較とその負例は削除する。

**裁定パッケージ候補・scope 外：** 同一 path の誤投入も launcher 自身に拒否させるなら、正規化済み path の重複拒否だけを別途裁定対象にする。既存 validator 内への追加であっても、新しい検査であることを明記する。

## 3. test の重複

**判定：real — NUL 区切りの別ファイル記録は冗長。**

既存 harness は shell が渡した `sys.argv[1:]` を JSON に保存し、復元後の配列を固定期待値と完全一致比較している。[test_p3_s4_loop_job_contract.py:1297](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2830-b5-node-local-lock/orchestrator/tests/test_p3_s4_loop_job_contract.py:1297)、同 `:1894`、`:1915`。引数の順序・境界・空白を含む値・起動回数は既に対象である。

提案された NUL 記録も同じ `args` を `os.fsencode` するだけで、別の実行境界を観測しない。[s2-plan.md:93](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2830-b5-node-local-lock/codex/s2-plan.md:93) 現在の fixture と実行環境に対する argv bytes の固定として、新たな検出能力はない。任意の encoding や入力全般を保証するテストでもない。

**残す最小の差分：** 既存の完全一致比較をそのまま受入に使う。NUL 記録ファイル、二組目の期待 literal、その読取り処理は追加しない。pair 引数削除・fixture 値変更の変異も既存比較で検出する。

## 4. 継承値の test

**判定：real — 独立した継承値 test は本題の最小差分から外せる。**

launcher の環境辞書に `IZANAGI_BENCH_LOCK` はなく、qsub argv は明示的な `-v` 列挙で、`-V` もない。[b5_contrast_launch.py:182](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2830-b5-node-local-lock/tools/pegasus/b5_contrast_launch.py:182)、同 `:211`。この投入経路に、親 shell の任意の bench lock 値を転送する配線は見当たらない。

直接 shell を起動して値を渡すこと自体は可能なので、「継承経路は存在しない」とまでは言えない。しかし、提案された test はその追加入力条件を固定するもので、今回の launcher 経路に必要な証拠ではない。[s2-plan.md:133](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2830-b5-node-local-lock/codex/s2-plan.md:133)

**残す最小の差分：** harness で外部の bench lock 値を除去し、既存 test に以下だけを足す。

- B-5 driver が `$TMPDIR/bench.lock` を観測する。
- 非 B-5 driver には新たに設定されない。

これで export の欠落、home への差替え、B-5 分岐外への移動を検出できる。job body に継承値を消す処理は足さない。

## 5. CLI 形

**判定：real — API の検証責務移設と手順更新漏れは縮小・修正対象。refuted — 共有 fallback を残す必要はない。**

試走の API 利用は、呼出し側が `validate_submit_tree` と `replace` を行ってから `launch` に渡していた。[submit_pilot.py.txt:25](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2830-b5-node-local-lock/output/insights/2026-09-20/t2797-b5-contrast/pilot/submit_pilot.py.txt:25)、同 `:47`。`launch` に path、HEAD、third-party root を渡して再構成させる変更は、複数 tree 対応とは別の責務変更である。

**残す最小の差分：**

```python
launch(jobs, trees_by_arm, *, submit, runner=None)
```

値は既存の `SubmitTree` とし、呼出し側が従来どおり検証・構成する。`launch` は `trees_by_arm[job.arm]` を env と cwd の双方に使うだけにする。

CLI の4必須引数は固定4 arm に対して単純であり、それ自体を過剰とは判定しない。別案として既存名を使った `--repo-root` の4値指定も可能だが、順序依存になるため明白に優れた縮小案ではない。単一 tree fallback や旧 API との union 型互換層は不要。

ただし、現行 README の実行例は単一 `--repo-root` なので、そのままでは新 CLI と不整合になる。[tools/pegasus/README.md:475](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2830-b5-node-local-lock/tools/pegasus/README.md:475) **現行の利用例だけ更新する**。過去の `submit_pilot.py.txt` は実行記録として変更しない。

## 6. 削れる変更

**判定：real — 次の変更は削除・縮小できる。**

| 削除・縮小対象 | 残す最小の差分 |
|---|---|
| `previous_trees`、common repo 一致拒否 | 単一-tree validator をそのまま反復利用 |
| 関係比較用の同一 superproject・4 worktree fixture | 既存 validator fixture を維持。launcher test では4つの異なる `SubmitTree` を使用 |
| `launch` 内への Git 検証移設 | 呼出し側で検証済み tree を構成。既存 dry-run test の subprocess 禁止も維持 |
| NUL 記録ファイルと二重の期待値 | 既存 argv 完全一致比較 |
| 独立した継承値 parameterized test | 既存 test に B-5 の exact lock path と非 B-5 の未設定観測 |
| common repo 比較を無効化する変異 | 比較自体とともに削除 |
| lock literal の新しい静的 pin・順序 assertion | 実 shell→driver の環境観測で必要な挙動を固定 |

最後の静的 pin 追加は [s2-plan.md:143](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2830-b5-node-local-lock/codex/s2-plan.md:143) のもの。環境観測があれば export 行削除の検出に重複する。既存の pin は維持する。

変異負例は、lock 行削除・home 差替え・分岐外移動・tree 共有への戻しを中心に残す。env と cwd は別々に誤配線できるため、両者の照合は必要。`export` 脱落も環境伝播を直接扱う有用な負例である。

また、**この変更だけで本走全体が投入可能になる、という完了表現は避けるべき**。現行 launcher は write-heavy・series 1・block 1 の試走条件を拒否条件として固定している。[b5_contrast_launch.py:111](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2830-b5-node-local-lock/tools/pegasus/b5_contrast_launch.py:111) 今回はその認可境界を広げず、「本走前に必要な lock と tree 配置の実装を整える」までとする。

## 総括

**残す核は、B-5 分岐内の export 1行、job 別 `SubmitTree` の env・cwd 配線、既存テストへの環境観測追加と必要な変異負例。**

P2 は結論を維持し、根拠を「lock 変更による同時性増加」から「既存の共有 cache に待機しない claim 競合がある」へ修正する。common repo 一致検査、NUL 記録、検証責務の移設、継承値専用 test は削れる。

静的検査のみ。ファイル変更、テスト・変異実走、実機投入は行っていない。