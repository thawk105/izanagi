# [T-2266] B-10 に残っていた正式な静的 1000 マイクロ秒の標本を取った — 値は 999 マイクロ秒に近く、埋まったのは「要求した 6 点目が実現していない」という帳尻である

**種別:** 実測 + 記録。**実装面 (D95 決定 2) の差分はゼロ。**

各点は trace 有効ビルドで直列性の検査を通り、anomaly は 0 だった (`correctness_verified: true`)。
**性能値は trace 無効ビルドの別走行で得たもので、性能としては未認証である**
(`performance_certified: false`)。ここにある性能値を根拠に variant を採用してはならない (絶対規律 2)。

- 日付: 2026-09-09 投入 / 2026-09-10 完了 (JST)
- wave: `dev-wave-t2266-formal-1000us`、branch `worktree-dev-wave-t2266-formal-1000us`
- 起点 local main: `7f17e1c63`

## 0. この wave が主張すること・しないこと

**主張する。**

1. **正式系列 `run_kind = t2266-tail` の静的 1000 マイクロ秒の標本を、3 workload とも取った。**
   要求点 (`requested_us`) と実現点 (`realized_us`) がともに
   `[150, 200, 300, 500, 750, 1000]` になり、`unrealized` は空になった。
   **これで「正式な静的 1000 マイクロ秒の標本」という個別の未了項目は埋まった。**
2. **測った値は 999 マイクロ秒の値に近い。** median throughput の差は write-heavy −0.22%、
   balanced −0.27%、read-heavy −0.66%、abort 率の差は 3 workload とも 0.0001 以内である。
   物理的に 0.1% しか離れていない 2 点なので、これは想定どおりである。
3. **同じ job で測り直した共通 7 点が、2026-09-07 の走行と近い値を返した。** 静的 5 点は
   3 workload × 5 点の 15 組すべてで median throughput の差が −0.36%〜+0.33% に収まった。
4. **v2 系列の 6 静的点でも、median throughput と abort 率は 3 workload とも b について単調に減少する。**
   これは本 wave が report の値から直接確かめた範囲である。

**主張しない。**

- **B-10 を閉じたとは言わない。** 少なくとも 901〜998 マイクロ秒の帯、因果としての機序の同定、
  `binary` を含む待ち方の ladder が残っている。
  **B-10 の未了「総数」は書かない。** D1724 は adaptive の 3 定数を B-10 の内側に数え、D1637 は
  それを 2 本目の論文の主題として分けている。この食い違いは
  `output/insights/2026-09-09_t2266-b10-mechanism/README.md` §5-4 が裁定へ返したまま**未裁定**であり、
  本 wave はどちらへも寄りかからない。
- **「tail の形についての結論が変わらない」とは言わない。** 本 wave は歩行 model・13 点較正・
  tail の当てはめ・図のいずれにも v2 を入力していない。§4 のとおり、**下流 generator は
  schema v1 と 999 マイクロ秒に束縛されており、v2 を渡すと fail-closed で拒否する。**
  差し替えた場合にどうなるかは**未測定**である。
- **「独立な再現」とは言わない。** v1 と v2 は同じ driver・同じ seed・同じ測定順の別走行であって、
  別実装でも別解析系でもなく、事前登録した再現判定も持たない。§3 に書くのは観測した差の幅だけである。
- **旧系列を置き換えたとは言わない。** §3 のとおり両方が測定時点の事実として残る。
- 探索走 ([T-2418]、`run_kind = t2418-explore`、2000 / 4000 / 9999 マイクロ秒) の値を
  1 つも使っていないし、混ぜてもいない (D1813)。
- 性能を認証していない。直列性は検査したが、性能値は未認証のままである。

## 1. どう測ったか — 正式系列の手順をそのまま使った

driver は既存の `orchestrator/campaign/backoff_extended_sweep.py` を `--run-kind t2266-tail` で
呼ぶ経路で、**新しい実行体も新しい引数も足していない。**

- **`t2266-tail` の driver に 1 点だけ測る口は無い。** CLI は `workload` / `--output-root` /
  `--cache-root` / `--ccbench-dir` / `--run-kind` だけで、点を絞る引数を持たない。さらに report の
  受理側が 8 genome の完備を要求する (`if seen != set(expected) or len(points) != 8:`)。
  **したがって「コードを 1 byte も変えずに正式系列として使える最小単位」が 8 点である。**
  これは絶対規律 4 の意味で無駄に大きい規模ではない。部分測定の口を新設するのは依頼が scope 外と
  明示した追加機構にあたるので、**作らなかった。**
- 8 点は静的 6 点 + 文脈 2 点 (`none` / `adaptive`) で、workload ごとに固定した seed の並べ替え順で
  同じ job の中で測る。1 点だけ切り出して別 job で測ると job 間の分散が入る。

**1000 マイクロ秒が測れるようになっていたのは、本 wave より前の commit `91a5bfca3` (D1748) による。**
同 commit が `T2266_REALIZED_US` の 6 点目を 999 から 1000 へ差し替え、`T2266_UNREALIZED` を空にし、
report schema を `t2266-backoff-static-tail-report/v1` から `/v2` へ、campaign identity を
`t2266-backoff-static-tail` から `t2266-backoff-static-tail-v2` へ上げていた。
**本 wave はこの経路を初めて実際に走らせただけで、コードは 1 byte も変えていない。**

符号化は D1748 のとおりで、物理 1000 マイクロ秒は生値 `BACKOFF_FIXED=3000` に載る
(親が着手前に `encode_static_backoff_us(1000) == 3000`、`decode_static_backoff_us(3000) == 1000` を実測)。
job の stdout にも `[campaign] evaluate silo|BACKOFF_FIXED=3000,...` が 3 job とも出ている
(`t2266-tail-v2/job-<workload>.stdout`)。

**T-2419 の物理 intent 関門については、証拠の型が違う 2 つを分けて書く。**

- **実測:** 本 wave の 3 job は、生値 3000 を「1000 マイクロ秒のつもり」と宣言したうえで関門を通り、
  build と測定へ進んだ。関門 (`_require_condition_gate_before_measurement`) は
  `_prebuild_backoff_binaries` より前に fail-closed で走るので、**3 job が `status = complete` で
  完走したこと自体が、この宣言が実 C++ compiler の評価と一致したことの証拠である。**
- **読解 (実測ではない):** 親が射影した範囲では、`4bba06422` (T-2419) 以後に backoff 系の計測 job が
  走った記録を見つけられなかった ([T-2418] の探索走の checkout `c49cdca1d` はこの commit より前である)。
  **これは過去 job 全集合を監査した結果ではない。**「backoff 系で初めて関門を通した」と断定はしない。
  反例が 1 本出れば倒れる種類の主張であり、倒れても上の実測は影響を受けない。

## 2. 結果 — 静的 1000 マイクロ秒の正式標本

各点 5 rep、`records` / `threads` / `extime` は正式系列の共有定数のまま。

| workload | median throughput [tps] | abort 率 | 変動係数 | job |
| --- | ---: | ---: | ---: | --- |
| write-heavy | 991,345 | 0.0424 | 0.32% | `0:988519.nqsv` |
| balanced | 718,553 | 0.0587 | 0.43% | `0:988520.nqsv` |
| read-heavy | 1,699,329 | 0.0238 | 0.22% | `0:988521.nqsv` |

rep 単位の throughput [tps]:

| workload | rep 0 | rep 1 | rep 2 | rep 3 | rep 4 |
| --- | ---: | ---: | ---: | ---: | ---: |
| write-heavy | 991,345 | 993,390 | 990,711 | 985,687 | 993,610 |
| balanced | 716,329 | 722,613 | 718,553 | 723,549 | 718,141 |
| read-heavy | 1,699,329 | 1,697,425 | 1,701,986 | 1,697,804 | 1,706,661 |

3 workload とも genome は
`silo|BACKOFF_FIXED=3000,BACK_OFF=1,NO_WAIT_LOCKING_IN_VALIDATION=1,NO_WAIT_OF_TICTOC=0,WAL=0`、
`committed: true`、`correctness_verified: true`、`certified: false`。

同じ job で測った残り 7 点も含めた全値は `t2266-tail-v2/` の report にある。

## 3. 旧系列 (v1、999 マイクロ秒) との関係 — 置き換えない

**2026-09-07 の v1 系列 (job 979843 / 979844 / 979845) は、測定時点の事実としてそのまま残る**
(絶対規律 7)。本 wave はその値を 1 つも書き換えていない。両者は campaign identity と report schema で
機械的に分かれている。

| | v1 系列 | v2 系列 (本 wave) |
| --- | --- | --- |
| campaign identity | `t2266-backoff-static-tail-silo-<workload>-sweep-…` | `t2266-backoff-static-tail-v2-silo-<workload>-sweep-…` |
| report schema | `t2266-backoff-static-tail-report/v1` | `t2266-backoff-static-tail-report/v2` |
| 静的 6 点目 | 999 マイクロ秒 (`unrealized: [1000]`) | 1000 マイクロ秒 (`unrealized: []`) |

**同じ 7 点を別の日時に測り直したので、差の幅を観測できた。** 測定順は 3 workload とも v1 と同じ
並べ替え (6 点目の label だけ `fixed-999us` → `fixed-1000us`) で、親が逐一照合した。
**これは「独立な再現」ではない** — driver も seed も測定順も同じで、事前登録した再現判定も無い。

| 点の種類 | median throughput の差 (v2 − v1) の範囲 |
| --- | --- |
| 静的 5 点 (150 / 200 / 300 / 500 / 750)、3 workload = 15 組 | −0.36% 〜 +0.33% |
| `adaptive` 3 組 | −1.31% 〜 +2.12% |
| `none` 3 組 | −0.87% 〜 +4.58% |

**静的点はよく揃い、文脈 2 点はばらつく。** 走行内の変動係数も同じ向きで、静的点は v1 が
0.11〜0.62%、v2 が 0.04〜0.43% なのに対し、文脈 2 点は v1 が 0.93〜3.98%、v2 が 0.71〜4.50% である。
**「文脈点の変動係数は静的点より概して大きい」までが言えることで、全組が 1 桁差というわけではない。**
本 wave はこの差の原因を調べていない。

**tail の最上点どうし (999 対 1000) の比較は「再現」ではない。** 物理的に別の点だからである。
参考までに差を書くと write-heavy −0.22%、balanced −0.27%、read-heavy −0.66% で、
abort 率の差は 3 workload とも 0.0001 以内である (例: write-heavy は v1 も v2 も 0.0424)。
**0.1% 離れた 2 点の値がこの程度しか違わないのは想定どおりで、新しい知見ではない。**

## 4. 何が埋まって、何が埋まらないか

**埋まったのは帳尻である。** 2026-09-07 の記録は「要求点 1000 マイクロ秒は unrealized、999 マイクロ秒は
その代替枠」と書いていた (F718)。この状態では「静的 6 点を測った」と書くたびに
「ただし 6 点目は要求した点ではない」という但し書きが要る。本 wave でその但し書きが要らなくなった。

**埋まらないもの。**

- **下流成果物は v1 に束縛されたままで、本 wave は差し替えていない。** これは選択であると同時に
  構造でもある。`tools/t2216_backoff_walk_model.py` は `TAIL_BACKOFFS = (150, 200, 300, 500, 750, 999)`
  と `TAIL_REPORT_SCHEMA = "t2266-backoff-static-tail-report/v1"` を定数で持ち、
  `tools/plotting/plot_t2266_tail_mechanism.py` も `REPORT_SCHEMA` に v1 を持つ。
  **v2 の report を渡すと拒否される** — `orchestrator/tests/test_t2216_backoff_walk_model.py` の
  `test_t2266_tail_report_rejects_schema_version_mismatch` が、schema を v2 に差し替えると
  `ModelError` になることを固定している。
  **したがって「歩行 model・13 点較正・図の結論が v2 でも変わらない」とは書けない。未測定である。**
  差し替えるなら consumer 側の変更を伴う別の作業であり、事前に登録して行う。
- **901〜998 マイクロ秒の帯は今も未測である。**
- **B-10 は開いたままである。** 少なくとも 901〜998 マイクロ秒の帯、因果としての機序の同定、
  `binary` を含む待ち方の ladder が残っている。**未了の総数は書かない** (§0 のとおり
  D1724 と D1637 の食い違いが未裁定であるため)。
- **tail の形についての上限は動かない。** D1724 が定めた「機序として書けるのは記述的な会計まで」
  という限界は、本 wave の 1 点では動かない。

## 5. 実装面と変異検査

**実装面の差分はゼロ。** 変えた file は `docs/paper-story/README.md` (stale 注記の事実訂正)、
本 insight ディレクトリ、`docs/spool/` の fragment だけである。Python・shell・実行 bit 付き file・
symlink は 1 つも足していない。よって `DW-S04` により変異 matrix を免除する。
**受入全走は免除していない** (§6)。

親は着手前に、実装が既に 1000 マイクロ秒を実現していることを実測で確かめた
(`T2266_REALIZED_US == (150, 200, 300, 500, 750, 1000)`、`T2266_UNREALIZED == {}`、
`_t2266_points('balanced')` の 6 点目が `BACKOFF_FIXED=3000`)。実装を足す必要は無かった。

## 6. 受入と検査

- `python3 tools/check_docs.py` は**着手前** (worktree 作成直後、docs 未編集) と
  **docs 編集後**のいずれも **rc=0** (「違反なし」)。
- 段 6 の敵対レビュー 2 本は `tools/check_codex_output.py` が**両方 rc=0**。
  内容と採否は §7。
**受入全走 (1 回目) は赤 1 件で返った。本 wave に帰属しない。**

- `child_rc = 1`、`22303 passed / 68 skipped / 1 failed`、claim した main は `dd43fcb70`。
  待ち手は `stage=acceptance-command rc=70` で止まり、受領証は発行されていない。
- 赤は `orchestrator/tests/test_dev_waves_worker.py::test_stdout_stderr_combined_cap_minus_exact_plus_one_boundaries`
  の 1 件だけ。**本 wave の差分はこの test へ到達しない** — 変えたのは docs と測定記録だけで、
  test が測る `tools/dev_waves/worker.py` の byte 上限には触れていない。
  この test は子 process に 4096 byte 前後を stdout / stderr へ書かせ、
  `termination_grace_s=0.05` (50 ミリ秒) の猶予で打ち切って byte 数を突き合わせるもので、
  login node の負荷に感応する形をしている。
- `DW-O18` に従い**単独再走**した。`python3 tools/run_tests.py <当該 nodeid>` は **rc=0**、
  `1 passed in 4.08s` (Pegasus request `988969`)。**非再現である。**
- `docs/failures.md` にも `orchestrator/tests/flaky_test_holds.py` にも同 test の登録は無い。
  **再赤でも決定的赤でもないので、本 wave は hold を登録していない** (`DW-O18` の登録条件は
  「再赤 / 決定的赤」であり、非再現の 1 回はこれに当たらない)。

**受入全走 (2 回目) は緑。**

- `verdict = child-green`、`child_rc = 0`、`22307 passed / 68 skipped`、
  `red_nodeids = []`、`flake_nodeids = []`。
- tested main `66beffb6dc1ca1d5b713583239200fdb45144360`、
  tested tip `9fdfe73938c7a724c425e3844a8afe20d894669c`。
- 受領証は repo 外の job dir の `acceptance-receipt-2.json`
  (`dev-wave-acceptance-receipt/v5`)。走行前後の fingerprint は一致
  (`diff_bytes = 0`、`status_bytes = 0`)。

**本節を書いた commit は 2 回目の tested tip より後にある。** そのため land 対象の最終 tip に対して
受入を走らせ直す。**land が使う tested main / tested tip は、repo 外の job dir に並ぶ
`acceptance-receipt-<N>.json` のうち最後のものの値である** (`DW-O12`)。
**最後の走行の値を本節へ書くと、同じ理由でまた次の commit と次の走行が要る。** ここで止めないと
回帰が終わらないので、値は repo 外の受領証に置く。

**走行回数は land が成立するまでの競合回数で決まる。** 並行 wave が local main を進めると
land は `stale-main` で拒否し (main は 1 bit も動かない)、`DW-O23` に従って wave 側で main を
取り込み、受入を取り直して land をやり直す。**本 wave は実際にこれを踏んだ。**

- 3 回目の受入 (tested main `66beffb6d`、tested tip `ded6da49d`、`child-green`) の直後、
  land が lock を取る間に main が `960466384` へ進み、`status = stale-main`、
  `reason = main moved outside the tested audited closure while locking` で止まった。
- 5 回目の受入 (tested main `960466384`、tested tip `f9e2a5771`、`child-green`) の後は、
  land が 1 度目に `status = lock-busy` (別の協調 land が lock を保持、
  `retryable_same_request = true`)、同じ request の再試行で再び `stale-main`
  (main は `693c915b6` へ前進) となった。
- 以後は**受入と land を 1 本の script に連結**して、緑の受領証をその場で land へ渡す形にした
  (`accept-and-land.sh`)。窓を詰める以外に打てる手が無いためである。

**非帰属の赤が 3 回、それぞれ別の file で出た。** (i) `test_dev_waves_worker.py` の byte 上限 1 件、
(ii) `test_codex_worker_launch_budget.py` の 2 件、(iii) `test_t1259_qsub_env_delivery_probe.py` の
**12 件 setup error**。いずれも単独走では緑で ((iii) は同 file 51 passed)、
**本 wave の差分は docs と測定記録だけでどれにも到達しない。** 3 件とも subprocess を起こすか
PBS に触る test で、受入は 3 shard の並行走行である。`DW-O18` の登録条件 (再赤 / 決定的赤) に
当たらないので hold は登録していない。**この後さらに走行が要ったかどうかは、job dir に並ぶ
`acceptance-receipt-*.json` と `acceptance-child-*.log` の本数が示す。**

**(iii) 型の原因は junit から特定できた。読み取り方も含めて書いておく。** 受入の子 log は
FAILED の行しか持たないが、**shard の `session_root` に `junit.xml` があり、そこに
`failed on setup with ...` の本文が入っている** (`session_root` は子 log 冒頭の
`IZANAGI_ACCEPTANCE_SHARD_ARTIFACTS_V1` 行が示す)。本文は
`subprocess.TimeoutExpired: Command '['git', '-C', '<wave worktree>', 'ls-files', '--others',
'--exclude-standard', '-z']' timed out after 30.0 seconds` で、
`test_t1259_qsub_env_delivery_probe.py` の autouse fixture が実 repo の untracked 走査を
30 秒 timeout で行う形になっている。**親が同じ command を手で測ると 2.7 秒・untracked 0 件**
だった。**受入 3 shard の並行走行が file system を混ませると同じ走査が 30 秒を超える。**
変更に帰属する赤ではない。

## 7. 敵対レビューが見つけたもの

段 6 で 2 レンズを並列に走らせた。**2 本とも独立に NO-GO を返し、同じ 4 つの穴へ収束した。**
レンズ A は real 8 件 (must-fix 4)、レンズ B は real 4 件 (must-fix 4)。

**2 レンズが独立に指摘した 4 件 (すべて採用)。**

1. **B-10 の未了「総数」を確定していた。** 初稿は「4 項目のうち第 1 項が消え、残りは 3 項目になる」と
   書いた。これは D1724 と D1637 の未裁定の食い違いを、親が解決した扱いにするものだった。
   **総数を書かない形へ直した。**
2. **「tail の形についての結論を 1 つも動かさない」と断定していた。** 本 wave は下流へ v2 を
   入力していない。**レンズ B が下流 generator の定数を現物で示し、v2 が拒否されることまで突き止めた。**
   親が `test_t2266_tail_report_rejects_schema_version_mismatch` の実在を裏取りして §4 へ書いた。
3. **「初めて通した」という全履歴の否定を、現走行の通過と同じ強さで書いていた。**
   実測と読解を §1 で分けた。
4. **§6 が空のまま「受入は免除していない」「敵対レビューは実施した」と参照していた。**

**レンズ A だけが指摘した 4 件 (すべて採用)。**

5. 差の範囲を `−0.22〜−0.66%` と降順で書いていた (§3 を workload 別へ)。
6. 文脈点の変動係数を「静的点より 1 桁大きい」と一律に書いていた。実値は全組が 1 桁差ではない (§3)。
7. **「独立な再現になった」と書いていた。** 同じ driver・同じ seed・同じ測定順の別走行である (§0・§3)。
8. job の stdout と所要時間の根拠が repo 内の写しに無く、成果物 README 自身が根拠になる循環だった。
   **stdout 3 本を `t2266-tail-v2/job-<workload>.stdout` として写し、所要時間の主張は落とした** (§8)。

**refuted と判定したもの (レンズ B、いずれも親も同意)。** 生きた文書に「正式標本は未取得」の
取り残しは無い (過去 insight と凍結日付版は当時の事実として直さないのが正しい)。
`t2266-tail` に単一点の測定口は無い。8 点再走は絶対規律 4 に反しない。
v1 と v2 の campaign identity は衝突しない。`output/insights/` 配下に実行可能資材は無い。

**親の手順の失敗。** 親は段 4 で「設計択一は割れていない」と裁定して段 2・3 を起動しなかった。
その判断は **D1724 と D1637 の食い違いを見落としていた。** 見落としたのは「どう測るか」ではなく
「B-10 の未了をどう数えるか」であり、測定そのものはこの見落としに影響されない。
それでも、初稿はその食い違いの上に「残り 3 項目」と書いていた。**段 3 を省いた分の穴を、
段 6 の 2 レンズが両方とも独立に埋めた。**

**この near miss は F597 の再発として台帳へ送った** (段 8)。既存の 2026-09-01 例は
「段 3 を省いたため誤った判断がそのまま報告として出た」型で、本件は
**「測り方に択一が無い」ことを「主張に択一が無い」ことと取り違えた**型である。
再発検知として「段 1 で読んだ一次資料が『裁定へ返した』と書いている項目を列挙し、
そのいずれかが成果物の主張の土台になるなら軽量版にしない」を書いた。
**`DW-C00` 自体は変えていない** — 軽量版の適用境界は裁定境界であり、
`docs/skill-self-improvement.md` が裁定パッケージ側へ回す対象だからである。

## 8. 再現条件

| 項目 | 値 |
| --- | --- |
| 投入 checkout | `7f17e1c63` の detached worktree (`<job dir>/submit-tree`、tracked clean、submodule 再帰初期化済み) |
| CCBench PIN | `511c9538e` (`pin.CURRENT_PIN`) = submodule HEAD `511c9538e4e8efa54b45cda62e72389ed3b706ec` |
| freeze trees sha256 | `c405c742f60e19b4f96b4fa9922f9bfe37ebd23389ed4598d707bfeb09abf2f3` (投入前に親が計算、job も前後で照合) |
| 依存 source | `/work/SFC/tanab/github/gflags` `e171aa2d…`、`/work/SFC/tanab/github/glog` `8f9ccfe7…` (policy の pin と一致・clean) |
| 投入 command | `bash tools/pegasus/submit_b10_backoff_grid.sh --output-parent /work/1/SFC/tanab/b10-backoff-grid-t2266-formal --run-kind t2266-tail` (cwd = submit-tree) |
| group | `b10-backoff-grid-20260909T135503Z-1669897` |
| job | `988519` (write-heavy) / `988520` (balanced) / `988521` (read-heavy)、queue `gen_S`、2026-09-09 22:55 JST 投入 |
| 完了 (親が観測した wall-clock) | write-heavy 23:07、balanced 23:14、read-heavy 2026-09-10 00:28 (JST)。**queue 待ちを含む**。job ごとの計算時間は採取していない |
| 完了判定 | 3 本とも `completion.json` の `status = complete`、`.failure.json` 0 件 |
| 出力親 | `/work/1/SFC/tanab/b10-backoff-grid-t2266-formal/` |
| report sha256 | write-heavy `28b433c7…`、balanced `9b137c74…`、read-heavy `f7f89f4d…` (repo 内の写しと byte 一致を親が照合) |
| stdout sha256 | write-heavy `823c7714…`、balanced `d43278b2…`、read-heavy `8fd761f5…` |
| repo 内の写し | `t2266-tail-v2/` (report `.json` / `.dat` × 3、`completion-*.json` × 3、`job-*.stdout` × 3、投入受領証) |

**写しの permission は 0600 から 0644 へ正規化した。** job は `umask 077` で書くため出力親の実体は
0600 だが、内容の byte は変えていない (親が `cmp` 相当で照合済み)。

**投入 script は mode 100644 で実行権が無い。** `bash <path>` で起動する。直接実行して rc=126 を
1 度踏んだ。

## 9. エージェント工数

**Codex 子は 2 本** (段 6 の敵対レビュー、`--stage review`、`sandbox=read-only`、
model `gpt-5.6-sol`、effort `xhigh`、`effort_authority = docs`)。
model call はレンズ A が 32、レンズ B が 43 の計 **75**。両方 `outcome = accepted`、
`stop_reason = completed`、`tools/check_codex_output.py` rc=0。
段 2 (plan) と段 3 (敵対相談) は起動していない (`DW-C00` の軽量版)。その判断の穴は §7 に書いた。
