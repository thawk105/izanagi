## 実行順序と cleanup

**refuted — outside 短絡・関門例外で cleanup が飛ぶ。**

- **根拠:** `t316_sandbox_backend_probe.py:2052` の `checkout` 内で基底 identity を検査し、`:2075` の単一 `applied` が outside／inside 両方を包む。outside 失敗時は inside だけを省略する（`:2087`）。`patchharness.py:262` が revert、`:373` が木の撤去を `finally` で実行する。
- **成果物影響:** 通常の短絡・Python 例外による patch 持越しは認められない。
- **通る正例:** outside 成功→inside 成功→revert→worktree 撤去。outside 失敗でも同じ exit 処理へ進む。

`applied` の二重適用もない。ただし、Git 自体の停止や撤去失敗まで cleanup 成功を保証する構造ではない。これは後述の時間上限と区別する。

## sandbox 境界と時間予算

**refuted — requested 木が scratch の writable bind に覆われる。**

- **根拠:** probe `:2069` が scratch 配下を拒否し、`:2073` が readonly roots に追加する。mount 順は `:847` の `/tmp`、`:849` の readonly roots、`:851` の scratch writable bind。実経路の scratch は別途 `mkdtemp` した子ディレクトリ（`:2534`）、requested は host TMPDIR の別の子（harness `:362`）。
- **成果物影響:** この実経路では requested source の read-only mount が維持される。
- **通る正例:** 同じ TMPDIR の下に scratch と requested の親が兄弟として作られる配置。

checkout／apply／revert と gate 呼出しは host 側。追加した配線に sandbox 内 Git 呼出しはない。CMake 入力が内部で起動する全プロセスについての実測保証ではない。

**real — S6 の時間内完了にはコード上の有限上限がない。受入上の未解決事項。**

- **根拠:** policy `:8–14` は deadline 5100 秒、S6 開始条件3600秒、CCBench build 片側1200秒。ところが harness `_git` `:90` は timeout なし、`flock` `:130` も待機上限なし。checkout／apply／revert に deadline は渡らない。
- **成果物影響:** S6 終端・受領証確定前にジョブ walltime に到達し得る。
- **通る正例:** harness 処理と両 gate が速やかに戻り、両 build が残予算内で完了する走行。

数値上も余裕は保証されない。片側のコマンド cap 合計は **2700秒**、両側で **5400秒**。実行時には残 deadline で切られるが、3600秒は成功保証ではない。追加 identity の設定 timeout 合計は **45秒**（probe `:1738`, `:1765`）。ただし timeout 後の `communicate()` は無期限（`:645`）なので、これも厳密な wall-clock 上限ではない。

親裁定 `s4-adjudication.md:94–102,167` はこの問題を実経路の確認走で判断するとしている。一般化した timeout 改修を本レビューから追加要求はしない。

## メタテストと波及

**refuted — Python／PBS の束縛集合が不一致。**

- **根拠:** probe `:2327–2335` と PBS `:54–62` は同じ7入力。
- **成果物影響:** patch／harness の片側だけの束縛漏れはない。
- **通る正例:** 7入力が clean で、実体と commit blob が一致する状態。

**refuted — 新規 node が `_run()` から走らない。**

- **根拠:** test `:2024–2026` は当該ファイル全体を `pytest.main` に渡す。
- **成果物影響:** 新規6関数・8 node は収集対象になる。
- **通る正例:** 通常の pytest collection。

確認した波及面：

- `test_hooks.py:4392` の inventory は `tools/pegasus` の実行ファイル集合を検査する。今回の既存ファイル編集・harness import は集合を増やさない。
- `test_official_perf_closure.py:91,536,827` の対象に probe は含まれる。今回の配線が新しい perf predicate を追加する箇所は認められない。
- conftest の real-repo inventory／access 分割、receipt memo／oracle inventory に新規 node の登録はない。新規 Git 操作対象は一時 repo で、既存 patchharness テストの除外説明（`conftest.py:753`）と整合する。
- **「未登録なので全走で必ず赤」とは判定できない。** `test_real_repo_serialization.py:1591–1619` は登録集合・独立 golden・共有 fixture 閉包を検査しており、任意のソース読取りを自動発見する検査ではない。
- duration 台帳の90%条件は全 collection 依存。今回、成立を確認していない。

## 新規配線検査の検出力

以下は**静的判定であり、変異 KILL の実測ではない**。

| 変異 | 判定・根拠 | 成果物影響／通る正例 |
|---|---|---|
| M4：gate は requested、build は stock | **real：検出箇所あり。** `test_s6_live_requested_gate_and_both_build_roots_match` の `:1935–1938` が実 configure argv の `-S` を照合する。 | build と無関係な gate 証拠を拒否。正例は両 `-S` が requested。 |
| M5：control を patched copy に変更 | **real：検出箇所あり。** profiler が capture/gate 入口で control header に `BACKOFF_FIXED` がないことを要求（`:1887–1892`）。さらに `:1929` が stock の実 path を照合。 | patched control の共有を拒否。正例は元の stock。 |
| M6：基底 identity を恒真化 | **real：赤にはなるが帰属に問題。** wrong-head 注入は `:1875–1876`。probe の拒否を外すと harness `assert_pinned_clean`（`:257`, `:192`）が先に例外を出す。 | wrong-head node の赤を、probe 固有の identity 検査の独立した検出力とは数えられない。正例は正しい clean 基底。 |
| M7：未参照変数を戻す | **real：独立した検出箇所あり。** `test_s6_shared_configure_excludes_named_unused_variables` `:1997–2001` が3名称を直接拒否。 | 未使用変数の再混入を拒否。正例は3名称なし、BACKOFF_FIXED は維持。 |

**must-fix：M6 wrong-head の KILL 帰属を修正すること。**

親裁定 `:190` の「別層が先に拒否するなら登録し直す」に該当する。dirty は untracked witness（test `:1878`）なので、tracked のみを見る harness に同じ mask はない。

また identity 呼出し自体を削除する変異では、注入もその呼出しに依存するため、`:1911` の `requested_roots` 件数 assertion が先に赤になる。これも wrong HEAD／dirty 拒否の意味的な証拠と混同できない。

## 実装子の報告の裏取り

**refuted — 報告が pytest の緑を申告している。**

- **根拠:** 報告は実走 nodeid 0件、pytest 起動前停止、実 CCBench 未確認と明記している。
- **成果物影響:** 未実走を合格証拠として扱う記述ではない。
- **通る正例:** 現在の「実装済み・未実走」という限定。

コード上、6関数・8 node、実関数への profiler、束縛 fixture と dirty 対象の追加、`_run()` 収集は存在する。外部参照 test の検索結果も `test_hooks.py`／`test_official_perf_closure.py` と一致した。

**報告にあってコードに存在しない実装・テストは、今回確認した範囲では特定していない。** runner の rc・checker の成功は履歴ログを裏取りしておらず、報告値としてのみ扱う。

**nit：** 「新規8 node」とは別に、既存 dirty parametrization に patch／harness × staged／unstaged の4ケースも追加されている。総追加ケース数の説明は分けた方が正確。

## 総括

**目的状態への到達は未証明。静的に確認できた production 配線から、必ず失敗する欠陥は特定しなかった。**

- **must-fix:** M6 wrong-head の変異検出力の帰属。harness の先行拒否を独立した証拠に数えない。
- **受入で未解決:** 実 CCBench の supply exact pair、両 build、trace-disabled、時間内のS6終端。
- **nit:** 追加テスト件数の説明。

pytest・変異・計算ノード走行は本レビューでは実行していない。