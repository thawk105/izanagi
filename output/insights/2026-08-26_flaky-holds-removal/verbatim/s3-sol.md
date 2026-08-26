## 総括

- 静的検査のみ実施し、pytest や焦点走は実行していない。
- hold#1 は `join(10)` を `join(60)` にしただけで、F480 型の原因を除去していない。現時点の撤去根拠は不足している。
- hold#3 は xdist 3.8.0 の通知経路上、worker 記録が controller 記録へ因果的に先行する。撤去根拠は静的には成立する。
- directory metadata の正規化は、一時作成後削除を検出できた入力を受理側へ移す。これは実際の検出力低下である。
- ただし、その一時作成後削除を分離して検査する control は変更前から存在しない。既存の恒真な説明を本 wave の回帰と混同してはならない。
- 3 row の主要な障害情報は F136/F480 に残るが、exact observation と解消記録は不足する。該当 F 節へ closure を追記すべきである。

## 1. 恒真化の疑い

directory の `st_size`、`st_mtime_ns`、`st_ctime_ns` をすべて正規化すると、最終的な Git-visible entry 集合が同じ一時作成後削除について、`assert snapshot_after == snapshot_before` はその履歴入力を常に受理する。具体的には、`test_t080_stub_free_e2e_temp_roots_fail_closed_at_real_output_boundary` の副作用検査が該当する。

- snapshot の現在の timestamp 記録: `orchestrator/tests/test_s8b_oracle_driver.py:558-580`
- E2E の before/after assertion: `orchestrator/tests/test_s8b_oracle_driver.py:1192-1207`
- import 時境界の同型 assertion: `orchestrator/tests/test_real_repo_serialization.py:945-964`
- 正規化を提案する箇所: `s2-plan.md:126-133`

一方、docstring がいう一時作成後削除を独立に確かめる検査は存在しない。repository-wide の検索でも主張は次の2箇所だけである。

- `orchestrator/tests/test_s8b_oracle_driver.py:559`
- `orchestrator/tests/test_real_repo_serialization.py:542`

既存の positive control は entry を削除せず残しており、row 集合差だけで赤になる。

- `orchestrator/tests/test_s8b_oracle_driver.py:583-598`
- `orchestrator/tests/test_real_repo_serialization.py:566-582`

したがって、docstring の「独立証拠がない」という欠陥は本 wave より前から存在する。プランが docstring を永続状態だけの主張へ狭めることは恒真な説明の解消であり、回帰ではない。ただし、現在の helper が偶然にも検出できる一時履歴を捨てること自体は、本 wave による実際の受理集合拡大である。

hold#3 には機構固有の negative control がない。`orchestrator/tests/test_real_repo_serialization.py:3829-3836` の合成負例は `prewarm-worker` を追加して payer 不在 assertion を検査するだけで、decorator の削除や記録の `yield` 後移動を決定的に赤にしない。実 xdist trace は positive control であるが、順序強制機構との対になっていない。

そのほかは問題なし。D-a の absent/present control には規則削除または negation の負例が計画され、`runs-visible` には ignored `runs` の負例がある。P1 の source digest にも malformed digest と valid-format mismatch の負例が計画されているため、これらに「どんな入力でも通る」assertion は見つからない。

## 2. 撤去で失われる情報

| hold | `docs/failures.md` に残る情報 | 残らない、または弱い情報 |
|---|---|---|
| #1 | node、failure signature、絶対 wall-clock が原因であることは `docs/failures.md:13242-13272` に残る | row の exact `1 failed / 16384 passed / 60 skipped` と `1 passed / 13.56秒` は F480 にない。主要値は `docs/archive/worklog-phase3-0825-949.md:78-90` に分散し、未採番の再導入 slug は row 撤去で失われる |
| #2 | red/green observation、mtime signature、原因、F136、登録事実、T-1773 は `docs/failures.md:5084-5101` に残る。shard 競合の原因は `docs/failures.md:5012-5023` にもある | 解消 commit と hold 撤去の closure はまだない |
| #3 | red 2 走、green 4 node、trace、cause、F480、登録事実は `docs/failures.md:13306-13319` に残る。修理内容は `docs/failures.md:13321-13331` に残る | row の exact `61 skipped` と hold 撤去の closure はない。T-1803 の割当ては `docs/spool/FOLDED.md:2618` にだけ残る |

`failure_signature`、`cause`、`evidence_id` の核心は3件とも failures 台帳に残るため、row 撤去だけで障害知識が丸ごと消えることはない。しかし、台帳は現在「登録した」で終わっており、解消と再導入が記録されない。

実装と同じ commit で次を移すべきである。

- F136 に hold#2 の修理内容、解消 commit、撤去日、再導入した node を closure として追記する。
- F480 に hold#1/#3 の `639f2f28`、元の exact observation、撤去日を追記する。
- hold#1 を現状のまま撤去するなら、未解消の絶対時間上界を所有する T を正式に割り当てる。未採番 slug を黙って消すべきではない。
- hold#2/#3 の T 割当履歴は `docs/spool/FOLDED.md:2574,2618` に残るため移動不要である。

## 3. 検出力を落とさない代替案

一時作成後削除の検出を維持する具体案は二つある。

1. snapshot 区間を event journal にする。Linux の inotify で CREATE、DELETE、MOVED_FROM、MOVED_TO を記録し、event path を Git ignore 判定へ通す。最終 entry が消えていても Git-visible event があれば赤にできる。

   コストは高い。helper を context manager 化し、動的 directory watch、短命 event、queue overflow、rename、Linux 固有性、全 call site を扱う必要がある。プラン自身も `s2-plan.md:118-124` でこの費用を認識している。

2. snapshot は変更せず、競合する writer を観測 root 外へ移す。`output/runs` の launcher failure と `output/task-runs` の shard sidecar を各 shard の session root へ渡せば、directory timestamp を残したまま偽の赤を除ける。

   コストは acceptance runner、launcher、task-run の出力配線変更と writer 閉包の確認である。writer を一つでも漏らすと flake が再発するため、小変更ではない。

厳密に検出力を保存するなら、このどちらかが必要である。before/after の最終状態だけから、ignored child 作成と visible path の作成後削除を識別する代替は出せない。

hold#1 は倍率でなく、論理的な進捗と運用 watchdog を分ける案がよい。second thread が lock 取得を完了したことを event で観測し、結果、qsub 2 回、orphan hold 不在を性質として assert する。外側 subprocess の長い timeout は hang 時の回収だけに使い、合否となる latency assertion にしない。コストは subprocess 化、異常時の thread/process cleanup、診断出力の追加である。

hold#3 には、小さな pluggy harness で「observer wrapper の pre-yield 記録、内側の送信 hook、post-yield」の順を直接呼ぶ負例を追加できる。decorator 削除なら記録されず、記録を post-yield へ動かせば順序が反転するため、両変異を決定的に赤にできる。

## 4. hold#1 / hold#3 の撤去根拠

hold#1 は撤去根拠が不足している。

`orchestrator/tests/test_pegasus_dispatch_compute.py:5484-5488` は依然として絶対 wall-clock assertion であり、変更は 10 秒から60秒への受理集合拡大にすぎない。単独走13.94秒に対する4.3倍と、F480 の0.04秒に対する0.15秒の3.75倍を比較しても修理根拠にはならない。OS scheduling delay は単独走時間に比例せず、保証された上界もないためである。

十分な倍率は存在しない。倍率で語ること自体が誤りである。代表負荷下の反復走はフレーク率を推定できるだけで、有限倍率を正当性の証明にはできない。親の測定も「単独3 passed は修理証拠でない」「受入全走でしか確かめられない」と明記している (`parent-measurements.md:14-22`)。さらに `639f2f28` の差分は `join` の数値以外を変えていない。

したがって、hold#1 は論理的な進捗検査へ直すまで保持するか、少なくとも残余 risk の正式な所有 T を残すべきである。

hold#3 の順序保証は成立する。

1. worker plugin は `record("worker-hook")` を実行し、file を close してから `yield` する (`orchestrator/tests/test_real_repo_serialization.py:3767-3769,3785-3789`)。
2. xdist 3.8.0 の worker は、その内側の通常 `pytest_collection_finish` hook で初めて `collectionfinish` event を送る (`/home/SFC/tanab/.local/lib/python3.10/site-packages/xdist/remote.py:256-262`)。
3. controller は event 受信後に `pytest_xdist_node_collection_finished` を呼ぶ (`/home/SFC/tanab/.local/lib/python3.10/site-packages/xdist/dsession.py:274-287`)。
4. その controller hook で `controller-hook` が追記される (`orchestrator/tests/test_real_repo_serialization.py:3791-3792`)。

worker と controller が別 process でも、この二つの書込みは競走していない。worker の close、collectionfinish の送信、controller の受信、controller の append という因果鎖がある。controller 内での `controller-hook` と `prewarm-controller` の相対順序は未規定だが、現在の assertion はそこを要求していない。

よって hold#3 は静的根拠だけでも撤去してよい。ただし、wrapper を壊す決定的な negative control は追加した方がよい。実走で緑になったとは本検査では主張しない。

## 所見一覧

- **所見 1**: hold#1 の `join(60)` は F480 型を修理しておらず、現時点で hold を撤去してよい根拠にならない
  - 場所: `orchestrator/tests/test_pegasus_dispatch_compute.py:5484-5488`
  - なぜ問題か: 単独走への倍率は高並列時の scheduling delay を上界付けない。10秒から60秒の stall が新たに受理され、60秒超の flake は残る。
  - もし放置したら成果物 (受入の受理集合・台帳・レポート) の何がどう変わるか: 受入集合が10から60秒の遅延を受理し、未採番の所有先も台帳から消える。
  - 確度: high。commit 差分が timeout 値だけであり、親測定も単独走を修理証拠でないと明記している。

- **所見 2**: directory metadata 正規化は、Git-visible path の一時作成後削除に対する E2E 副作用検査を恒真化する
  - 場所: `orchestrator/tests/test_s8b_oracle_driver.py:1192-1207`
  - なぜ問題か: 最終 entry が消えた履歴は directory timestamp だけが証拠であり、それを除くと同じ最終 snapshot を必ず返す。
  - もし放置したら成果物 (受入の受理集合・台帳・レポート) の何がどう変わるか: fail-closed 経路が可視の一時副作用を起こしても受入が緑になりうる。
  - 確度: high。現在の row schema とプランの正規化後 schema から静的に決まる。

- **所見 3**: hold#3 の順序強制には、それ自体を壊す決定的な negative control がない
  - 場所: `orchestrator/tests/test_real_repo_serialization.py:3785-3789,3829-3836`
  - なぜ問題か: 現在の合成負例は payer 不在だけを検査し、decorator 削除や post-yield 移動は実 scheduler の偶然に再依存する。
  - もし放置したら成果物 (受入の受理集合・台帳・レポート) の何がどう変わるか: 順序強制が退行しても受入が間欠的に緑となり、同じ flake が再発しうる。
  - 確度: medium。負例の不在は静的に明確だが、実 xdist node 自体も一定の検出力は持つ。

- **所見 4**: 3 row の撤去と同時に F136/F480 へ解消 closure を書かないと、台帳が「登録した」で止まる
  - 場所: `docs/failures.md:5093-5101,13306-13331`
  - なぜ問題か: 原因と署名は残るが、exact observation、修理 commit、hold 撤去、残余 risk の所有状態が一箇所に閉じない。
  - もし放置したら成果物 (受入の受理集合・台帳・レポート) の何がどう変わるか: 受入では再導入済みなのに failures 台帳は active hold と読める状態になり、hold#1 の所有先は消える。
  - 確度: high。現行 F 節と registry row の逐語比較で欠落を確認できる。