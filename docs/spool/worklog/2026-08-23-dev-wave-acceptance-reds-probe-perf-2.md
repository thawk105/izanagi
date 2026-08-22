---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-08-23
wave: dev-wave-acceptance-reds-probe-perf
seq: 2
title: 非帰属判定の collection dispatch を畳み込み worktree rc=128 を限定再試行した。worktree 再利用と並列化は正しさを証明できず却下した (コード+テスト、branch worktree-dev-wave-acceptance-reds-probe-perf)
---

## 本文

- ユーザー依頼は「`tools/check_acceptance_reds.py` の非帰属判定を高速化する。まず内訳を計測して
  支配項を特定し、並列化・worktree 再利用・submodule 初期化の共有化を比較して最小の変更から
  段階導入する」であった。制約として、正確性と regression 見逃しゼロを緩めないこと、
  テスト対象を間引かないこと、`tools/run_tests.py` の変更が要るなら着手前に裁定へ返すことが
  与えられた。**結果として 3 案のうち 2 案を却下し、1 案だけを採った。**
- **支配項の実測。** 一次資料は T-1458 の実物 artifact。`acceptance-run-17.log` (03:00:26) から
  `acceptance-receipt-17.json` (03:39:12) まで 2326 秒 / 26 件 = 89.5 秒/件。
  親がローカル git 側を実測して内訳を分けた: `worktree add --detach` 16.21 秒、
  submodule cache-only init 5.33 秒、fingerprint 1.33〜1.62 秒 × 5 回/件、
  `worktree remove --force` 9.63 秒 = 小計約 38.4 秒 (43%)。
  残り約 51 秒 (57%) は `run_tests.py --force-dispatch` **2 回**である。
  **依頼書が想定していなかった事実として、1 nodeid あたり dispatch が 2 回発生する** —
  テスト再実行だけでなく前段の `pytest --collect-only` も dispatch 経由だからである。
- **重複の全数実測。** `dev-wave-jobs` 配下の `*.acceptance-red-check.json` を全 130 件解析した
  (find で列挙、切り詰めなし、130 件すべてパース可)。node 総数 476。
  `len(collections) == len(nodes)` が 130 件すべてで成立し、collect-only は例外なく
  node 1 件につき 1 回発生していた。distinct path へ畳むと 476 回 → 169 回 (307 回削減、64.5%)。
  node 数が最大級の receipt ほど distinct path が少なく (37 node で 3 path、
  26 node で 1 path が 7 receipt)、**痛いところほど無駄が大きい**構造だった。
- **却下 1: worktree 再利用。** 詳細は {{D:probe-worktree-reuse-cannot-prove-isolation}}。
  親の対照実験、段 2 プラン、段 3 レンズ A の 3 経路が独立に同じ結論へ達した。
  潜在利得は probe worktree 構築 705 回 → 230 回と大きいが、状態隔離を証明できない。
- **却下 2: 並列化。** 段 2 プランが新しい論拠を出した — **並列化は worktree 再利用と
  原理的に両立しない** (各 worker が専用 worktree を要る)。加えて同時 PBS 数の上限を決める機構が
  本 wave の対象内に無く、`tools/run_tests.py` の変更は禁止されている。
  親の追加実測で `queue_wait_s` は約 5.23 秒と判明し、1 dispatch 約 25 秒のうち queue 待ちは
  約 20% で残りは job 起動・実行・後片付けだった。並列化の利得自体はあるが本 wave では採らない。
- **却下 3: 依頼書項目 4 の「既知の環境要因を許可リストで高速判定する」。**
  テストを実行せずに非帰属と決める設計であり規律 2/3 に正面から抵触するため、提案しなかった。
  `tools/run_tests.py` への変更も発生しなかったので裁定へ返す事由は生じなかった。
- **親の推論が子に訂正された。** 親は receipt の `stdout_sha256` が 10 種類に割れる理由を
  「所要時間文字列のせいで nodeid 集合は同一」と判定したが、段 2 プランが
  「`stdout_sha256` は scheduler stdout tail のハッシュであって nodeid 集合のハッシュではない」と
  指摘した。正しい。親の判定は receipt からは導けない言い過ぎだった。
  親が本番経路で独立 2 PBS job (937273 / 937274) と login node の計 3 観測を比較し、
  62 nodeid が完全一致することを実測して埋め直した。
  なお `run_tests.py` の画面出力は digest 化されて切り詰められる (62 件中 37 件しか残らない) ため、
  比較は PBS の生 stdout を一次資料として行った。
- **親の設計案が両レンズに否定され、より正直な案へ変えた。** 段 2 プランは
  「1 回の collection 観測を node 数だけ複製して `collections` の件数を保つ」を提案したが、
  段 3 の両レンズが独立に「偽の証跡になる」と指摘した。`request_id` 等は 1 回の dispatch に
  固有の値であり、複製すると 26 回 dispatch した外観になる。cache 由来を示す field 追加は
  consumer の 6 field 契約により不可能。親が live code で件数非拘束を全数確認したうえで
  「1 観測 = 1 entry」へ畳む方式を採った。
- **親の裁定より子の判断が優れていた例が 1 件。** 親は「rc=128 retry の前に残骸を cleanup する」と
  裁定したが、実装子は「残骸があれば retry せず fail-closed で止める」を選んだ。
  残骸の自動削除より安全で、結果は rc=2 (checker infra 失敗) であって誤判定ではない。
  親は実装側を採用し裁定を修正した。
- **実装子が指示外の受理集合変更を 1 件入れ、親が差し戻した。** wave_tip 側 probe に
  collection を走らせる変更で、(a) 2 tip の collection 不一致という新しい拒否を足し、
  (b) wave_tip への dispatch を新たに発生させて高速化の目的に反していた。
  ただし原因の半分は親の仕様の矛盾で、親が「cache key から tip を落とす変異を殺すテスト」を
  要求したが、wave probe が collection しない設計では collection する tip は 1 つしかなく
  その変異は実効 gate を持たない。`DW-M01` に従い変異を `path_text` 軸へ再照準した。
- **変異 harness の baseline が本物の欠陥を捕まえた。** 新規テスト 8 本が
  `monkeypatch.setattr(CAR.time, "sleep", ...)` でプロセス全体の `time.sleep` を差し替えており、
  pytest-xdist 内部や subprocess のポーリングまで捕捉して
  `assert sleeps == [1.0]` が実測 11149 件多い値と比較されて落ちた。
  混入量は実行スケジュール依存で、**同じ commit の 1 回目は 100 passed、2 回目は 1 failed** だった。
  `DW-O14` / D78 に従い monkeypatch をやめ、同 file に既にある注入規約と同じ流儀で
  `Sleeper` seam を追加した。親が 3 回連続実行して 3 回とも 100 passed / rc=0 を確認した。
  **baseline 緑の要求が無ければ、全 wave の受入を間欠的に赤くする欠陥を main へ入れていた。**
- **変異 matrix (最終、repo_head d32b944c):** baseline PASSED、登録 9 / 完了 9、
  **KILLED 8・SURVIVED 1・MISMATCH 0・TIMEOUT 0**。
  生存した `ardp.m09b` (signal を保留する `defer` handler 単独の変異) は相互マスクである。
  `defer` を即送出へ変えても `_worktree_remove` の `except _TerminationSignal` が signum を
  拾い直すため挙動が変わらない。逆に `except` 単独の変異 (初回走行の `ardp.m09`) も
  handler が送出しないため到達せず生存した。`DW-M02` に従い両層同時変異
  `ardp.m10-bothlayers` を登録したところ **KILLED** で、性質は 2 層が揃って成立すると裏取りできた。
  注入実在は `anchor_counts` 各 1 件一致と非空の `injection_diff_sha256` で確認済み。
- **初回走行の erratum を保存した** (`mutation-ledger-run1-erratum.json`)。
  `rerun_rc` を決め打ちする変異 (`ardp.m03`) は 28 node を落とし、赤理由を 1 つに絞れなかった。
  rerun は cache の外で無条件に呼ばれる構造なので「cache が rerun を飛ばす」という
  単一理由の gate は存在しえない。`DW-M01` に従い登録から外した。
  28 テストが落ちること自体は、rerun が全面的に load-bearing である証拠として残す。
- **段 6 レビュー所見のうち 1 件は残余リスクとして受け入れた** —
  詳細は {{D:collection-cache-residual-selector-risk}}。refuted とはしていない。
- **段 6 レビュー所見のうち 1 件は前提の誤読として refuted した。** レンズ B は brief の
  「受入・テストは pegasus 計算ノード占有で最悪 5 分以内」を本ツールの実行時間 SLO と読んだが、
  この制約は wave 自身がテスト・受入をどう走らせるかの作法である。
  ただし目標値の有無はユーザーへ確認する価値があるため下記へ起票した。
- **子の工数 (receipt 実測):** codex 子 9 本、model call 合計 348、wall 合計約 7132 秒。
  内訳は plan 42 / consult 18・14 / author 86 / review 13・51 / fix 48・54・22。
- **セッション異常 2 件。** (1) 親が救済案の生死確認を使い捨て worktree でなく wave の作業
  worktree で走らせ、`external/ccbench/build/` 配下に空ファイルを作った。
  `hooks/guard_bash.py` は `external/ccbench` を全域で削除から保護するため正規の手段で消せず、
  hook は迂回しなかった。実害は無い (`sort_swo_oracle.py` の依存検査が要求するのは
  `build/_deps/masstree-src` という特定の入れ子 path であり、`build/` 直下の空ファイルでは
  偽 green にならない。gitignore 済みで commit にも入らない)。
  (2) 親が変異走行中に repo tree へ decisions fragment を書き、harness が untracked file を
  検出して fail-closed した。既知の禁止事項の違反である。fragment を commit してから再走した。

## 次の一手差分

### 新規

- {{T:probe-state-isolation-proof-design}} **P2・新規**: 非帰属 probe の worktree 再利用を
  実現するには、まず「probe の状態隔離を何によって証明するか」の設計が要る。
  worktree 内の `git status` では足りないことが本 wave で確定した
  (ignored ディレクトリの折り畳み、submodule 内部の不可視、worktree 外の副作用)。
  内容ベースの再帰 manifest か、probe を状態から切り離す別の隔離機構を設計する。
  潜在利得は probe worktree 構築 705 回 → 230 回 (全 130 receipt の全数実測)。
  正本 = {{D:probe-worktree-reuse-cannot-prove-isolation}}。
- {{T:nonattributable-probe-parallelism}} **P3・新規**: 非帰属判定の並列化。
  worktree 再利用とは原理的に両立しないため、どちらを追うかの設計分岐になる。
  同時 PBS 数の上限を決める機構が別途要る。`queue_wait_s` は約 5.23 秒 (実測) で
  1 dispatch 約 25 秒の約 20% にすぎないため、隠せるのは主に job 実行側である。
- {{T:nonattributable-probe-latency-target}} **P2・新規**: 非帰属判定は最悪何分以内であるべきか、
  目標値をユーザーへ確認する。本 wave の畳み込み単独では 26 件で
  collect-only dispatch を 26 回 → 1 回に減らすに留まり、全体の一部改善である。
- {{T:dispatch-artifact-cleanup-on-missing-receipt}} **P2・新規**:
  `tools/check_acceptance_reds.py` の `_authoritative_command_stdout` は、dispatch が
  control prefix なしで artifact だけ残した場合に `_dispatch_receipt_path` が `None` を返し、
  cleanup せず local stdout として扱う。既存テストは正常 receipt と既知残骸しか検査しない。
  本 wave の変更に起因しない既存の穴である (段 6 レビュー レンズ A 所見 9)。
- {{T:red-check-receipt-node-collection-binding}} **P3・新規**: red-check receipt は
  `nodes` と `collections` の対応を束縛しておらず、consumer も検査しない
  (変更前から同様で、空の `collections` と非空 `nodes` を受理する fixture が実在する)。
  node ごとの collection 根拠を検証可能にするには schema 変更が要るため別裁定。
