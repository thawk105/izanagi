# 段 4 裁定 — [T-2863] silo-function-policy 段階 D (2026-09-23、親 = Claude manager)

入力: brief.md、s2-plan.md、s3-consult-A.md (NO-GO、must-fix A1・A2)、s3-consult-B.md (NO-GO、must-fix B1・B6)。
裁定 inbox 再走査: 第 32 回 (2026-09-23 08:2x) 項 1 で CCBench pin 更新 wave (T-2858) が起きる。本 wave は `axis.PIN` を実行時に読み結果 JSON に記録するので、pin が wave 中に動いても測定の意味は変わらない (規律 7)。本 wave から pin を触らない。
記法: C/ = orchestrator/campaign/、Q/ = orchestrator/tests/。

## 1. 所見の裁定

| ID | 判定 | 採否・内容 |
|---|---|---|
| A1 / B5 | real | 採用。job 割付は `L xor S xor R xor M` の偶奇 (各 job で各因子 4 点ずつ)。job 内の順序は ID 順で固定し、基準 abort0 は初走 job では**末尾**、再測 job では**先頭** (順序の反転) |
| A2 | real | 採用 (局所)。`aggregate` は入力の照合を行う: 初走 2 job の IR 点の和集合 = 列挙 16 点 (重複・欠落は null)、各点の本文 sha256 = 凍結した列挙の描画 sha256、全入力の workload・PIN・toolchain・schema 一致、初走と再測の job 識別子 (PBS_JOBID と hostname と開始時刻) が異なる、中央値・比・再測対象は生の rep から再計算。campaign admission や外部証拠の認証とは称さない |
| A3 | real | 採用。描画器は hook の入口で、出力・次状態の式が参照する state field を**すべて**局所へ写してから計算し、最後に field へ代入する。`f0'=f1, f1'=f0` の入替えと「出力 StateRef(0)・次状態 f0'=0」を、描画した C++ を実 compile・実行して検査する test を置く |
| A4 | real (限定) | 規則は維持し限定を明記: high-abort = 候補の abort 率の 5 rep 中央値 > 同 job の abort0 の 2 倍。abort0 比の暫定フィルタで、基準率 ≥ 0.5 では不発、絶対的な高 abort や公平性を除かない。基準率 0 は判定不能 (null)。先例 (D46 は stock 比、trigger は ident_all 比) からの変更として記録 |
| A5 / B1 | real | 採用。二値の文言を固定: 「固定 16 点のテンプレート部分空間で、両 verify certified・非 high-abort の点が、同 job の abort0 に対して 5 rep 中央値で 3% 超を示し、それが別 job の再測でも再現したか」。「なし」は全 IR の地形不在を意味せず、「あり」は既知最良 (B0-L-W0) 超え・統計的優位・LLM の必要性を意味しない。3% は p2_2.py の過去の between-run 指標の暫定流用で、Pegasus・新骨格で較正されていない。stock・B0-L-W0 は別掲の参考値 |
| A6 | real | 採用。bench は両 verify が既存 `_certified()` を満たす点だけ (bench 0 回で除外、status に記録)。TRACE=0 は段階 C の `trace0` と同じ確認 (compile command に `IZANAGI_` define なし・前処理に probe/break 断片なし) を各点の TRACE=0 build で行い、不成立なら除外。射程は owner TU の確認であり、trace 全体の除去証明とは書かない |
| A7 | real | 採用 (局所)。`aggregate` は詳細 JSON とは別に二値だけの投影 JSON (`binary`: true/false/null、固定の射程文、除外件数) を書く。点 ID・hash・順位・因子を含めない。E 段の入力制御は scope 外で、機械的 firewall を完成させたとは称さない。閲覧事実の記録義務は insight と worklog の引継ぎに書く |
| A8 / B6 | real | 採用。P6 の「単価」は撤回し、§4 の用途別総額でユーザー確認を取る |
| B2 | real | 採用。再測は初走の該当点を ID 順に 1 job で、各点ごとに両 verify + 5 rep を行い、最初に再現した点で終了 (「あり」確定)。「なし」は全該当点の再測完了が必要。未完了は null |
| B3 | real | 採用。abort0 は各 job、stock は job 0、B0-L-W0 は job 1 に各 1 回 (初走 20 case)。B0-L-W0 は参考値として残す (人間判断の材料として既知最良との位置関係に価値がある)。そのため `_build_variant` に狭い `stock_backoff` 引数を足す (stock=True のときだけ 0/1、既定 1) |
| B4 | real | 採用。`_source(body=...)` を足す (plan 5 のとおり)。任意 Genome・任意 flags・新 build wrapper は作らない |
| B7 | real | 採用。全点の grammar + 単独 TU compile は 1 本の parameterized test (未使用引数の確認を統合)。循環検出の独立機構は作らない (frozen dataclass + 深さ上限で足りる)。UBSan は既存 harness で login 正式 1 回。driver test は本文が既存入口を通ること・verify 失敗時の停止・5 rep・集計境界・照合に絞る |
| B8 | real | 採用。`canonical_ir()` の JSON 入出力・復元・schema 移行は作らない。各 run は case ID + 本文 sha256 で参照し、IR は記録用の決定的な文字列表現 (repr) だけ残す |
| plan 1 | 採用 | IR は frozen dataclass の型付き式木 + hook ごとの同時代入。深さは葉 = 1、全出力・次状態式の最大 ≤ 4。node は全 hook の式木の出現数の合計 ≤ 64。field ≤ 4 (名前 f0〜f3)。数値二項演算は同型同士。`rand` は入れない。`validate_ir()` を `render_policy()` の先頭で必ず呼ぶ |
| plan 3 | 採用 | 16 点 = L (即 abort / attempt < 4 の間 retry、lock 待機 0)・S (静的 / f0 に飽和加算・min 1000・commit で 0)・R (全要因 / lock_conflict だけ待つ、状態は全 abort で更新)・M (5 / 10 µs) の完全要因。退化点 abort0 は IR でも表し、対照として各 job で測る。0000・0001 は段階 C の static5・static10 と同じ本文になりうるが、段階 C の値は転用しない |

## 2. plan v2 (所有と単位)

- **単位 A** (所有: 新設 `C/silo_policy_ir.py`、新設 `Q/test_silo_policy_ir.py`): IR 型・`validate_ir`・`render_policy`・`enumerate_recon()` (16 点、ID = 4 bit 文字列 LSRM)・`degenerate_policy()` (abort0)・`job_of(case_id)` (parity 割付)・login 正式検査の小さい CLI (`python3 -m orchestrator.campaign.silo_policy_ir check --out <json>`: 16 点 + abort0 を一時 dir に書き、全点を `check_policy_body` に通し、`run_ubsan_harness` を 1 回、本文 sha256・compiler version・結果を JSON に出す)。
- **単位 B** (所有: 新設 `C/silo_policy_recon.py`、新設 `Q/test_silo_policy_recon.py`、既存 `C/silo_policy_coverage.py`、既存 `Q/test_ccbench_spawn_sites.py`、必要時のみ `C/materializer_admission.py` の説明文): A の interface を使う。sub-command `run --phase initial --job {0,1} --out` / `run --phase remeasure --candidates ID,... --out` / `aggregate --initial J0 J1 [--remeasure R] --out --projection-out`。`_source(body=...)`・`_build_variant(stock_backoff=...)` の最小追加。既存 coverage / smoke の挙動と既存 test は不変 (既存 test file の期待値を変えない。行番号 pin の追随だけは許す)。
- A → B の順 (B は A の land 後に A の patch を当てた木で始める)。

## 3. 不変条件 (実装子へ渡す)

- 正しさゲート: 全点に legacy + 性能構成 (write-heavy) の verify。非 certified は bench へ進めない。TRACE=0 確認不成立も除外。診断 build は NON_ADMISSIBLE (既存登録の再利用)。
- policy-C++ v1 の受理契約 (C/silo_policy_grammar.py)・4 段検査 (`prepare_policy`)・骨格の上限は変えない。
- 新しい gate・台帳・reject 理由・一般化は作らない。
- 動作点: 1M records・48 threads・skew 0.9・rratio 5・rmw false・max_ope 10・extime 3・bench 5 回。legacy は既存 `LEGACY`。clocks_per_us と NUMA は既存 `_run` のまま。

## 4. node 時間の見積り (ユーザー確認用、用途別)

出所: 段階 C smoke (job Elapse 793 秒、5 case、各 case = build 2 + verify 2 + bench 1 rep、balanced、job 準備込み)、段階 C coverage (1,016 秒、33 case)、B-5 試走の write-heavy 性能構成 verify 1 回 34〜91 秒 (別骨格の実測)、受入 1 回 ≈ 0.25 node 時間 (2026-09-22 実測)、焦点走 1 回 10〜230 秒。write-heavy でのこの骨格の verify 所要は未測定なので、各 job に walltime 上限を付けて上限を線の下に固定する。

| 用途 | 規模 | シナリオ (実測の組合せ、上下限ではない) | walltime 上限 |
|---|---|---|---|
| 初走 | 2 job × 10 case (IR 8 + abort0 + 軸 OFF 1) | 各 job 1,900〜3,000 秒 + 準備 → 計 1.1〜1.75 node 時間 | 1 時間 × 2 = 2.0 |
| 再測 | 条件成立時だけ 1 job (abort0 + 該当点、最初の再現で停止) | 通常 2〜3 case で 0.15〜0.25 | 1.0 |
| 焦点走 | 4〜6 回 | 0.1〜0.3 | — |
| 変異 probe・final | 2〜4 回 | 0.1〜0.3 | — |
| 受入 | 1〜2 回 | 0.25〜0.5 | — |
| 合計 | | 約 1.7〜3.1 | 上限 4.0 |

再測で全該当点を測りきる前に walltime に当たったら、二値は null (「なし」にしない) で報告し、追加の計測はユーザーに再確認する。

## 5. 変異の事前登録 (実装前、DW-M01)

期待 node は実装後に login self-run か初回 dispatch probe で完全集合を集める。各変異は赤理由が 1 つに絞れることを実装後に確かめ、絞れなければ登録から外して erratum に書く。

| ID | 壊すもの (位置) | 検出を期待する test |
|---|---|---|
| M-SNAPSHOT | 描画器の入口状態の写し (field を直接読む形に戻す) | 入替え・同時代入の実行 test |
| M-SATADD | 飽和加算の guard 除去 (`a + b` を直接) | 飽和境界 (MAX 付近) の実行 test |
| M-SATSUB | 飽和減算の guard 除去 | 下限 0 の実行 test |
| M-DEPTH | 深さ上限 4 → 5 | 深さ 5 の拒否 test |
| M-NODES | node 上限 64 → 65 | node 65 の拒否 test |
| M-FIELDS | field 上限 4 → 5 | field 5 の拒否 test |
| M-SHIFT | shift 量の幅未満検査の除去 | 幅と同じ shift 量の拒否 test |
| M-PARTITION | job 割付を ID 偶奇に | 各 job の因子均衡 test |
| M-CERT | bench 前の `_certified` 分岐の除去 | verify 失敗時 bench 0 回の test |
| M-REPS | bench 回数 5 → 4 | 5 rep の test |
| M-FLOOR | 床の比較を `> 1.03` → `>= 1.0` | 3% 境界の集計 test |
| M-HIGHABORT | high-abort 除外の除去 | high-abort 点の除外 test |
| M-NULL | 再測未完了を false に | 未完了 → null の test |
| M-AGG-SHA | 集計の本文 sha256 照合の除去 | 本文不一致 → null の test |
| M-BODY-GATE | `_source(body=...)` で `prepare_policy` を経ずに書く | 本文入口の接続 test (拒否される本文) |
| M-PROJECTION | 投影 JSON に点 ID を含める | 投影の内容 test |

## 6. 追補 (2026-09-23、ユーザー指示「一瞬で終わらせてね。計算ジョブを分割して投げることで」、計算の承認 = 合計 4.0 node 時間を上限、超えそうなら止めて再確認)

- 初走は 8 job に分割して同時投入する。job k は IR 2 点 = {ID, ID の bit 反転} の組 (8 組で 16 点を覆い、各 job で各因子の 0 と 1 が 1 点ずつ = A1 の均衡を強めた形) + 基準 abort0。stock は job 0、B0-L-W0 は job 1 に 1 件ずつ。job 内の順序は IR 2 点 (ID 順) → 軸 OFF 対照 → abort0 (末尾)。
- 単位 A の `job_of` (偶奇 2 分割) はこの組割付に置き換える (単位 B が所有して修正)。
- 再測は候補ごとに 1 job (abort0 を先頭、候補を後) で同時投入する。候補が 4 を超えるときは ID 順に 4 本ずつの組で投入し、ある組で 1 点でも再現したら次の組は投げない (「あり」確定)。「なし」は全候補の再測完了が必要。
- 見積り: 1 job ≈ 準備 + 3〜4 case。初走 8 job の合計はシナリオで約 1.5〜2.2 node 時間 (abort0 と準備が 8 回になる分増える)、各 job の walltime 上限 30 分で上限 4.0 に収まるよう投入時に合計を確かめる。上限を超えそうなら止めてユーザーへ再確認。
