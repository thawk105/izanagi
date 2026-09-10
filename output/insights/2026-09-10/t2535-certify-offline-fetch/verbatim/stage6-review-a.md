## 総括

- 主張 / 登録済み M1–M7 はいずれも赤になるが、同じ契約を壊す未登録変異が少なくとも 2 件生存する。
- 失敗シナリオ / production の gate slice を `:5` から `:12` へ変える、または実 configure 呼出し側で FetchContent token を切り落とす。どちらも射影された 35 test は静的には緑のままになり得る。
- 根拠の file:line / `tools/pegasus/certify_calibration.sh:414-417,659`、`orchestrator/tests/test_pegasus_calibration_workload.py:115-189,555-568,621-643`。親の変異 matrix は未実走: `parent-test-results.md:39-43`。
- 深刻度 / **高**。

本レビューではテストを実走していない。親報告は対象ファイルの焦点走 `35 passed` のみで、受入全走・変異 matrix・所有外 consumer は未実走である。

## 変異 M1-M7 の帰属検査

| 主張 | 失敗シナリオ | 赤になる assert | 根拠の file:line | 深刻度 |
|---|---|---|---|---|
| M1 は殺される | `FULLY_DISCONNECTED` を削除 | protocol 共通 token の exact 比較、CMake test 内の事前 exact 比較 | `test_pegasus_calibration_workload.py:549-552,626-632` | 残存なし |
| M2 は殺される | mimalloc を不存在 path へ | M1 と同じ exact 比較。実 CMake の path 照合へ到達する前に赤 | 同 `:549-552,626-632` | 残存なし |
| M3 は殺される | pristine verifier 呼出しを削除 | dirty fixture が rc=0 となり `returncode == 2` が赤 | 同 `:727-741` | 残存なし |
| M4 は殺される | masstree だけ copy | loop 文字列の exact pin、または verifier 失敗により clean 正例が赤 | 同 `:544-546,614-620,710-716` | 残存なし |
| M5 自体は殺される | 5 token を index 0–4 へ移動 | stub の `:5` から token が落ち `:561-564` が赤。full argv exact pin も順序差で赤 | 同 `:159-162,507-524,555-564` | 残存なし |
| M6 は殺される | source root と base dir を同一化 | 最初の正例の `source_root != base_dir` が赤 | 同 `:651-653`。copy test も `:715-717` | 残存なし |
| M7 は殺される | job 側構造検査を削除 | 抽出可能なら malformed job が rc=0 となり `:808` が赤。block 全削除なら helper の `.index()` 自体が赤 | 同 `:361-380,807-809` | 残存なし |
| M5′ は殺せない | production だけ `:5`→`:12`、または append を削除 | test は production 関数を実行せず、自前 stub の `:5` を観測するため緑 | production `certify_calibration.sh:405-420`、stub `test_pegasus_calibration_workload.py:159-162` | **高** |
| M1′ は殺せない | line 659 を `"${configure_argv[@]:0:7}"` 等へ変え、使用時だけ 5 token を落とす | test は assignment から token を再構成して別の CMake command を起動する。production の configure use-site は未観測 | `certify_calibration.sh:659`、test `:621-648` | **高** |

M1/M2 は「実 CMake の意味検査」で殺されるというより、`tokens == expected` で先に殺される。M6 も coupled-base 対照ではなく、直接の非同一 assert で先に殺される。

## 恒真・過剰決定の検査

- 主張 / `test_certify_condition_gate_receives_the_same_fetchcontent_tokens` は、実 gate 転送に対して実質的に恒真化できる。
- 失敗シナリオ / production の slice または `condition_gate_argv+=` を壊しても、stub が独立に正しい `:5` を実行する。
- 根拠の file:line / `certify_calibration.sh:414-417`、test `:159-162,555-568`。
- 深刻度 / **高**。

- 主張 / 実 CMake test は copy、verifier、argv exact pin、CMake 意味検査が過剰決定されている。
- 失敗シナリオ / verifier の無関係な回帰でも CMake 起動前の `copied.returncode == 0` で赤になる。M1/M2 も CMake の結果ではなく exact token 比較で赤になる。
- 根拠の file:line / test `:614-632,639-668`。
- 深刻度 / **中**。

- 主張 / 「staging sources untouched」は各 tree の `marker.txt` しか束縛していない。
- 失敗シナリオ / copy 後に上流の `CMakeLists.txt` など marker 以外を変更しても、copy 側 verifier と marker 検査は緑になり得る。
- 根拠の file:line / test `:703-724`、verifier 対象は copy 側 `certify_calibration.sh:568-579`。
- 深刻度 / **中**。

- 主張 / ignored artifact の負例は mimalloc だけに固定されている。
- 失敗シナリオ / production 呼出しを `source_names=("mimalloc",)` に狭めても負例は赤のままで、masstree/googletest の汚れを受理できる。
- 根拠の file:line / test `:727-741`、verifier の選択可能な `source_names` と loop `s8b_floor_campaign.py:2572-2583,2637`。
- 深刻度 / **中**。

- 主張 / malformed staging test は non-symlink regular-file child を扱わない。
- 失敗シナリオ / child 判定を `! -d` から `! -e` へ弱めても、missing・symlink・valid の現 fixture はすべて期待どおりになる。
- 根拠の file:line / fixture `test_pegasus_calibration_workload.py:756-817`、production `submit_certify.sh:58-63`、`certify_calibration.sh:178-184`。
- 深刻度 / **中**。

## 正しさ防壁への影響

- 主張 / 「条件関門は間接的にも不変」は成り立たない。関門へ渡る入力は 5 token 増えている。
- 失敗シナリオ / 従来 FetchContent で停止した呼出しが stock comparison まで到達する。裁定自身もこれを「制御された拡張」としている。
- 根拠の file:line / `certify_calibration.sh:414-417,629-647`、`stage4-ruling.md:124-127`。
- 深刻度 / **中・意図された影響**。

`configure_argv` を実際に数えると、index 0–4 は順に cmake、`-S`、source、`-B`、build dir。index 5–6 は build type と sanitizer、index 7–11 が新規 5 token、index 12 以降が従来の CCBench define である。したがって production の `:5` は新旧すべての従来 configure option を保持し、新規 5 token も含む。旧実装でも CCBench define は index 7 からだったため、既存引数が slice 外へ落ちた事実はない。根拠は `certify_calibration.sh:629-640` と base `7f17e1c63:tools/pegasus/certify_calibration.sh:576-581`。

protocol `{silo,mocc,tictoc}`、ratio `{20,50,80}`、既定 silo、stock-comparison option は変更されていない。新しい構造検査は whitelist 判定後に置かれ、有効入力を追加で拒否する方向だけに働く。根拠は `submit_certify.sh:18-20,40-64`、`certify_calibration.sh:154-185,405-420`。

## fail-closed の穴

指定された三経路について、失敗を飲み込む実行経路は静的には見つからない。

- 主張 / staging root・child の失敗は明示的な `exit 2` に直結する。
- 失敗シナリオ / `write_failure` 自体が失敗しても内部の `|| true` で記録失敗だけを飲み、その後の `exit 2` は維持される。
- 根拠の file:line / `certify_calibration.sh:50-76,170-185`、`submit_certify.sh:51-64`。
- 深刻度 / 穴なし。

- 主張 / `timeout 120 cp -a` の rc は OR-list で捕捉され、124 を含む非 0 は明示的な rc=2 終了になる。
- 失敗シナリオ / `set -e` が OR-list 内で抑制されても、直後の数値検査が閉じる。
- 根拠の file:line / `certify_calibration.sh:556-565`。
- 深刻度 / 穴なし。

- 主張 / verifier の Python rc、`cd` の rc、timeout rc は subshell の最終 status として捕捉される。
- 失敗シナリオ / heredoc は `python3 -` の stdin であり、delimiter 後に成功 command はない。import・verifier・timeout の失敗はいずれも `third_party_verify_rc` へ入る。
- 根拠の file:line / `certify_calibration.sh:567-588`。
- 深刻度 / 穴なし。

ただし、copy の timeout/nonzero を直接注入するテストは新規 6 件にない。親の実走も dirty verifier の rc=2 までである。根拠は `stage5-author.md:42-45`。

## 既存テストへの影響

- 主張 / 指定された 2 test の本体は base `7f17e1c63` から一行も変わっていない。
- 失敗シナリオ / ただし共有 helper `_protocol_shell_observation` は変更されており、テスト本体の byte 不変だけでは意味不変の十分条件にならない。
- 根拠の file:line / 現行 test `:438-451,492-501`、base 同 test `:252-264,306-315`、helper の変更面 `:115-189`。
- 深刻度 / **低**。

`test_certify_non_silo_defines_contain_no_axis_outsider` は引き続き `-DCCBENCH_` だけを抽出するため、新規 `-DFETCHCONTENT_` は受理集合へ混入しない。一方、helper 全体を実行するため offline argv の構文不良にも赤になるという、無関係な追加感度は生じている。

`test_certify_keeps_backoff_fixed_and_condition_gate_silo_only` の gate 回数の意味は維持されるが、以前から production の関数本体を実行していない。今回必要になった「gate へ実引数が届く」という意味までは、この既存 test も保証しない。

## 名乗りと実体の食い違い

- 主張 / `test_certify_condition_gate_receives_the_same_fetchcontent_tokens` は「condition gate が受領」と名乗るが、受領者は test stub である。
- 失敗シナリオ / production forwarding を破壊しても test 名どおりの失敗にならない。
- 根拠の file:line / test `:159-162,555-564`、production `certify_calibration.sh:405-420`。
- 深刻度 / **高**。

- 主張 / `test_certify_job_copy_leaves_the_staging_sources_untouched_and_writable` は、全 source の不変と writable 対象を曖昧に名乗る。
- 失敗シナリオ / upstream は marker 一個だけを検査し、書込みを試すのは upstream ではなく copy 側だけである。
- 根拠の file:line / test `:703-724`。
- 深刻度 / **中**。

- 主張 / `...missing_or_malformed...` の「malformed」は fixture が網羅する形より広い。
- 失敗シナリオ / regular-file child を受理する弱体化が生存する。
- 根拠の file:line / test `:756-817`。
- 深刻度 / **中**。

- 主張 / 実装報告の「copy 3 本と verifier は既存 CCBench 900 秒 envelope 内」は実コードの timeout 構造と一致しない。
- 失敗シナリオ / copy は最大 3×120 秒、verifier は120秒で、その後に configure 900秒と build 900秒が別々に直列実行される。全体を包む 900 秒 timeout はない。
- 根拠の file:line / `stage5-author.md:5`、`certify_calibration.sh:555-568,659-660`。
- 深刻度 / **中**。

## 裁定パッケージ候補

- 主張 / silo の実認定は pristine masstree に `config.h` がないため条件関門で停止し得る。
- 失敗シナリオ / offline source 供給が正しくても「silo 認定が通る」とは名乗れない。
- 根拠の file:line / `stage4-ruling.md:22-25,118-125`、`parent-test-results.md:29-33`。
- 深刻度 / **高・T-2534 裁定対象**。

- 主張 / submit が検査する `--repo-root` と job の `PBS_O_WORKDIR` は束縛されない。
- 失敗シナリオ / checkout A の staging を precheck して checkout B で job が開始し、投入後に job 側で拒否される。
- 根拠の file:line / `submit_certify.sh:13-15,51-64,210`、`certify_calibration.sh:33-35,170-185`、`stage4-ruling.md:26-27,61-62`。
- 深刻度 / **中・既存 P4**。

- 主張 / receipt は第三者 pin を記録せず、`pinned_clean=True` と一時 path の argv だけを残す。
- 失敗シナリオ / 後から receipt 単独で masstree・mimalloc・googletest の exact input を再構成できない。
- 根拠の file:line / `certify_calibration.sh:769-773`、`stage4-ruling.md:25-26,122-123`。
- 深刻度 / **中・既存 P3**。

- 主張 / 追加された最大 480 秒と「900 秒 envelope」の関係は、既存 walltime 不整合 P2 と一緒に再裁定が必要。
- 失敗シナリオ / 直列 timeout 上限を過小に説明したまま運用判断される。
- 根拠の file:line / `certify_calibration.sh:557-568,659-660`、`stage4-ruling.md:25`。
- 深刻度 / **中・walltime 裁定パッケージ**。