# 段 6 fix 裁定 — レビュー所見 + 親の dogfood 所見

`adjudication-plan-v2.md` を仕様の正本とし、本書はそれに対する**追加の must-fix 一覧**である。
出所: `rev_a.md` / `rev_b.md` (静的敵対レビュー 2 本) と
`parent-dogfood-findings.md` (親が request `874266` で実測)。

## FIX-A の担当 (dispatcher / run_tests / site_policy)

| ID | 所見 | 出所 | 対応 |
|---|---|---|---|
| FA-1 | **終了済み request で状態機械が END を認識せず 35 分空回りし、子が緑でも rc=16 になる**。`qstat -f <終了 ID>` は `Batch Request: ... does not exist on nqsv.` を **rc=0** で返す | 親実測 D1 (**blocking**) | rc=0 でも request 不在なら終端として扱う。`immediate qstat で可視だった`ことを前提に「一度可視だったものが不在になった = END」と導く。未知状態が続く場合も総時間上限で必ず抜けることを保つ |
| FA-2 | `Current State = Staging` が state map に無く UNKNOWN になる。`STG` は `qstat -Q` にも実在する | 親実測 D2 | `Staging`/`STG` を queue 側、`Exiting`/`Post-running`/`EXT` を終端側へ map する |
| FA-3 | **`site_policy.py` が Python 3.9 で import 不能** (`str \| None` + future import 無し)。計算ノードの素の `python3` は 3.9.13 | 親実測 D3 / rev_b M6 | `from __future__ import annotations` を足す。**さらに、変更対象の全 module が future import を持つことを静的に検査するテスト**を置く (F46 同型の再発防止) |
| FA-4 | **F49(a) の「実 FS 永続」が自己確認**。親が書いた path を同じ process が `is_file()` するだけ | rev_a MF1 / rev_b M3 | **計算ノード側が submission dir へ marker を書き、親はその marker の実在を永続性の証拠とする** (cross-namespace 証拠)。親→job の release handshake は作らない (親死亡で job が待つ形にしない) |
| FA-5 | **会計判定が一単語 OR で偽陽性**。子 stderr の `MemoryError` 等で `accounting_verified=true` になる | rev_a MF2 / rev_b M1 | Request ID の一致と必須 field (`Request ID` / `Started Request Time` / `Ended Request Time` / `Elapse`) を連言で要求する。既存の正しい実装 `orchestrator/campaign/silo_ladder_rung1.py:3662` の作法に寄せる |
| FA-6 | **receipt を一度も保存できなくても子 rc を返す** | rev_a MF3 / rev_b M5 | receipt 永続に失敗したら rc=16 (infra) にする |
| FA-7 | queue wait の起点が preflight 前で過大。RUN を観測できないと値が欠落 | rev_a MF4 | 起点を **qsub 復帰時刻**にする。RUN 未観測でも終端時刻から上界として記録し、`observed: false` を明示する |
| FA-8 | **qsub rc=0 の後 parse 失敗すると `active=False` のまま = 孤児ジョブ** | rev_b M2 | qsub rc=0 の**直後**に active を立てる。request ID が取れない場合も qdel を試み (job name / submission dir から特定を試みる)、失敗は receipt に残す |
| FA-9 | **immediate qstat の一時障害で恒久ラッチ**が発火し自動復旧不能になる | rev_b M4 | immediate qstat は**再試行**する (例: 3 回 / 5 秒間隔)。**`qstat` 自体が失敗した場合はラッチしない** (F47 型ではない)。ラッチは「qstat が成功したのに request が不在」または「FA-4 の marker が来ない」の場合に限る |
| FA-10 | 進捗が block-buffered で見えず、ハングと正常待機を区別できない | 親実測 D4 | 投入・request ID・状態遷移・収集の節目を `flush=True` で 1 行ずつ出す |
| FA-11 | **M5 の kill が無効** (probe を記録だけにしても `_job_run()` の再 assert が受理挙動を維持する) | rev_a MF7 | DW-M01/DW-M04 に従い**両層同時変異へ再照準**する。probe と `_job_run()` の両方を無効化したときに赤くなるテストを置き、期待赤 node を明示する |
| FA-12 | **M7 の kill が無効** (親の pop を変異しても dispatcher の allowlist / job script / job child が 3 重に除去する) | rev_a MF7 | 実効 gate へ再照準する。**job script と子環境の実際の内容**を検査するテストを置き、どの 1 箇所を落としても台帳が二重記録になる形を赤にする |
| FA-13 | dispatch 免除の閉集合テストが production 定数を parametrize しており自己追認 | rev_a SF2 | テスト側に**literal な期待集合**を書き、production 定数との一致を assert する |
| FA-14 | `queue_wait_included_in_parent_duration=True` が無条件の真偽値でテストも恒真 | rev_a 恒真 3 件目 | 実時間関係を検査するか、この field を落とす |

## FIX-B の担当 (guard_bash / coverage gate)

| ID | 所見 | 出所 | 対応 |
|---|---|---|---|
| FB-1 | **`python3 -m tools.pegasus.exec_calibrate` が exact-path 拒否を迂回**する。同 module は JSON の任意 argv を `os.execv` する | rev_a MF5 | `python -m <module>` の module 名を repo path へ解決して判定する。sanctioned は exact path 列挙のみなので、解決先が列挙外なら重量判定へ回す。`-m pytest` の既存判定は維持する |
| FB-2 | **`env -S 'pytest -q'` と `exec -a harmless pytest -q` が迂回**する | rev_a MF6 | `env -S` の split-string 内を再 tokenize する。`exec -a <name>` の `-a` を値付き option として正しく飛ばし、実 head を取る |
| FB-3 | **M11 の kill が部分無効**。coverage 各モジュールの configure 直前 gate を削除しても新テストが赤にならない | rev_a MF7 | coverage 4 モジュールの **configure 直前 gate と build 直前 gate を独立に赤くする**テストを置く。期待赤 node を明示する |
| FB-4 | production 配線 (`main()` が live site を注入する) の回帰を検出できない (F21 型) | rev_a SF1 | `main()` を stdin JSON で叩き、`site_policy.current_site` を LOGIN に差し替えた状態で exit 2 になることを検査する (直接注入テストの代替ではなく追加) |
| FB-5 | `ninja -t clean` を許可し、`ctest --show-only=json-v1` を拒否する | rev_a SF3 | introspection の許可を**読み取り専用 tool に限定** (`targets` / `graph` / `query` / `deps` 等、`clean` は拒否)。`--show-only=<fmt>` 形を許可形として認識する |

## 親が直す docs (fix 子は触らない)

| ID | 所見 | 対応 |
|---|---|---|
| P-1 | `AGENTS.md` が login node での極小 pytest を例外許可し runbook §7 と衝突 (rev_a MF8) | 例外を削除する |
| P-2 | runbook §8 の「build は `-j` を割り当てコア数に合わせる」が実装 (`jobs` 既定 16) と D102 決定 4 に矛盾 (rev_a MF9) | build は「計算ノードでのみ実行」に統一し、並列度は coverage 経路だけが site 由来だと書く |
| P-3 | D102 が login の rc を 2 通り主張 (rev_a MF10) | 正常 dispatch は子 rc を返し、rc=16 は infra 失敗と SUSPECT のみ、と直す |
| P-4 | `-n 16` 未測定のまま「最大並列コストゼロ」と断定 (rev_a MF11) | 受入で `-n 16` を測るまで断定を外し、測定後に結果を書く |

## 裁定パッケージへ送る (本 wave では直さない)

- SIGKILL / OOM / ホスト切断に対する scheduler-side lease と heartbeat (rev_b M2 後半)
- `task_run` 記録の best-effort 性 (rev_a SF5。既存 convention なので本 wave では変えない)
- receipt へ実 worker 数を構造的に持たせる (rev_a SF4)
