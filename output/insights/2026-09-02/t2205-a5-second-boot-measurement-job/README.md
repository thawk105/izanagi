# A-5 (D1100) 別 boot 再取得 — 測定 job を作り、実測が着地待ちであることを確定した

- 日付: 2026-09-02
- wave: `worktree-dev-wave-t2205-a5-second-boot`
- 対象 commit: `86579ee01` (機構) / `8c3481144` (段 6 fix)
- authority: none — 本書は設計判断と検査結果の索引であって、性能の測定原典ではない。
  **性能値は 1 つも含まない。**

## 何を求められていたか

D1100 (2026-08-27 ユーザー裁定) が、論文へ採用した 2 つの性能改善値を
**計算機を別に起動し直して取り直す**と定めた。既存の走査手順
(`orchestrator/campaign/backoff_sweep.py`) をそのまま 1 回回す形でよい。
対外主張を「1 回の起動でのみ確認」へ狭める案は明示的に却下されている。

| workload | ycsb_rratio | 採用した静的 backoff | 論文値 (旧 linux-baremetal) |
|---|---:|---|---:|
| write-heavy | 5 | fixed 10µs | +38.3288% |
| balanced | 50 | fixed 5µs | +11.2682% |

分母は同一 sweep 内の無 backoff 対照 (`BACK_OFF=0`, `BACKOFF_FIXED=-1`)、
集約は各側 TPS の median 比で、式は `100 * (variant_median / baseline_median - 1)`。
一次資料は `output/insights/2026-08-25_paper-story-a3-gain-unification/README.md`。

## 何ができて、何ができなかったか

**できたこと:** 上の測定を Pegasus 計算ノードで 1 回回すための投入器と job body を作り、
敵対レビュー 2 本と変異 matrix を通した。

**できなかったこと:** **測定そのものは走っていない。** 値は 1 つも取れていない。
理由は F660 である (下記)。

## どの計算機のどの起動で回すか — 裁定と、その根拠の訂正

**Pegasus の計算ノードで回す。**

- **却下した根拠 (誤り):** 「元の機体に到達できないから」。
  段 1 brief はこう書いたが、**これは誤りだった。**
  `/home/tanab/github/izanagi` がこの機体に無いことと hostname が `pegasus02` であることは、
  いま居る shell が元の機体でないことしか示さない。
- **採る根拠 (ユーザー裁定):** 元の値の env-tag `linux-baremetal` は
  **研究室の共有 Dell R760、ホスト名 cygnus** である (D59)。
  **2026-08-05 のユーザー裁定 (P3 U-7)** が
  「linux-baremetal (cygnus) は**使えるが使わない** — cygnus 依存の研究はしない方針 (ユーザー明言)。
  よって evidence は Pegasus で新規に測る」と定めている
  (archive worklog 2026-08-05 (237))。
  **cygnus は到達できないのではなく、使わないと決まっている。**

### この選択で分離できないこと

**「別の起動」と「別の環境」が交絡する。** Pegasus は元の機体と別の起動であると同時に別の環境
であり、得られる結果は起動単独の効果を分離しない。この限定は成果物から外れない。

### 「2 job を別ノードへ投げれば内部対照が取れる」は成立しない

段 1 brief はこう書いたが、**これも誤りだった。** A-2 の正式走は既に
`bnode141` と `bnode064` という**異なる 2 boot** で走っている
(`output/insights/2026-08-24_paper-story-a2-certification/raw-manifest.json` の
`boot_id` = `64ca394f-dd77-4ecf-ac4c-532f99a4b4f4` と
`bb47a198-17c1-40f4-9cf3-c57970b44061`)。
fan-out の形そのものは新しい対照ではない。**node と boot の記録は provenance であって
内部対照ではない。**

## 成果物に書いてよい主張・書いてはいけない主張

測定が走ったときに備えて、受理規則を先に固定する。

**書いてよい:**
1. 「`pegasus`、host X、boot ID Y、CCBench pin `511c953` の当該 sweep で、同一 job 内の
   無 backoff 対照に対し fixed 10µs / fixed 5µs はそれぞれ X% / Y% だった。」
2. 数値が近い場合: 「旧 linux-baremetal 値と数値的に近かった。ただし異なる環境・source での
   一致であり、D1100 の cross-boot 再現とは扱わない。」
3. 数値が違う場合: 「旧 linux-baremetal 値とは数値的に一致しなかった。ただし環境・source・
   toolchain が異なるため、旧値の無効化・反証・同一環境での再現失敗を意味しない。」

**書いてはいけない:**
1. 「論文採用値を別 boot で再現した / 再現しなかった。」
2. 「測定環境に起因する見かけの改善を否定した」「旧値を反証した。」
3. 「2 job が異なる node / boot に落ちたので、独立な cross-boot 対照を得た。」

## 旧走との条件差 (隠さず全部並べる)

旧走は 2026-06-22 22:58–23:14 JST、env_tag `linux-baremetal`、CCBench `6656e93`、
gcc/g++-13、`clocks_per_us=1800`、`numactl --interleave=all`、`perf stat` 下。
今回の走で変わる項目は次のとおり。

| 項目 | 旧 | 今回 | 比への効き方の見立て |
|---|---|---|---|
| 起動 | R760 の当時の起動 (boot 証拠なし) | Pegasus allocation 時の host / boot ID / btime | 熱・firmware・背景負荷を通じて効きうる |
| 機体 | 研究室共有 Dell R760 (cygnus) | Pegasus bnode (Xeon Platinum 8468) | CPU / cache / memory 特性が違い大きく効きうる |
| scheduler | 管理なしの共有機 | NQSV `gen_S`、専有保証なし | 同居負荷と周波数制御が効きうる |
| env tag | `linux-baremetal` | `pegasus` | 異なる環境の記述値。統合不可 |
| calibration | 1800 clocks/µs | active Pegasus G1、2100 clocks/µs | **固定 backoff の実時間を直接変える。比へ強く効く** |
| CCBench commit | `6656e93` | `511c953` | 被測定物が異なり比へ直接効きうる |
| compiler | `gcc-13` / `g++-13` | `gcc` / `g++` (実 path と version は job が記録) | codegen が変わる。最重要交絡の一つ |
| NUMA | `numactl --interleave=all` | launch prefix なし | memory placement が変わる |
| perf | `perf stat` 下 | Pegasus では無 perf になりうる | wrapper overhead が消える分だけ効きうる |

維持するもの: workload 座標、`records=1,000,000`、`threads=48`、`extime=3`、`reps=5`、
8 genome 集合と順序 (`none → adaptive → 2 → 5 → 10 → 25 → 50 → 100µs`)。
`orchestrator/campaign/backoff_sweep.py` は 1 byte も変更していない。

## 作ったもの

- `tools/pegasus/submit_a5_second_boot_backoff_sweep.sh` — login 側 fan-out 投入器。
  workload は `write-heavy` と `balanced` のちょうど 2 件。
- `tools/pegasus/a5_second_boot_backoff_sweep.sh` — 計算ノードの job body。
  job ごとに superproject と CCBench の scratch worktree を作り、`backoff_sweep.py` を
  追加 option なしで 1 回起動する。8 genome 全 commit・abort 0・各 5 反復を WAL replay で
  確かめてから `result.json` を書く。分母は exact `BACK_OFF=0, BACKOFF_FIXED=-1`。
- `orchestrator/tests/test_a5_second_boot_job_contract.py` — 契約テスト 7 件。
- `tools/pegasus/admission_registry.json` と `docs/pegasus-runbook.md` の投影表に 2 件登録。

## 敵対レビューが見つけた欠陥 (すべて修正済み)

- **空配線。** job body は `IZANAGI_PEGASUS_THIRDPARTY_CACHE` を export して存在検査までしていたが、
  この変数は `orchestrator/campaign/buildcache.py` の `FETCHCONTENT_SOURCE_DIR_*` 生成経路から
  読まれない。実際の取得は `http_proxy` / `https_proxy` 経由である
  (`tools/pegasus/b10_backoff_grid.sh` と同じ経路)。export と検査を削った。
- **投入器が repo root へ移動せず `qsub` していた。** job body は `PBS_O_WORKDIR` を repo root として
  HEAD を照合するので、別ディレクトリからの投入は計算ノード上で必ず失敗する。
- `result.json` を最終名で作ってから書いていた。一時 file → fsync → `os.link` で
  create-only publish → 親 directory を fsync へ変えた。
- 失敗・強制 timeout 時に `git worktree prune` が無かった。追加し、rc を receipt へ書く。
- **契約テストが行の見た目しか見ておらず、事前登録した変異 4 件が意味上は生き残っていた。**
  とくに呼び出し直前の `BASELINE_FLAGS["BACK_OFF"] = 1` は全テストを通したうえで
  分母を stock 適応へすり替えていた。AST による意味検査へ作り直した。

## 変異 matrix (段 4 で事前登録、段 6 fix 後に本走)

baseline は 464 passed / 1 skipped で緑。

| ID | 変異 | 結果 |
|---|---|---|
| M1 | 登録簿から job body の entry を削除 | KILLED (契約 1 件 + hook 登録簿 2 件) |
| M2 | runbook 投影表から行を削除 | pytest 層では SURVIVED → 実効 gate へ再照準 (下記) |
| M3 | 投入器の workload に `read-heavy` を追加 | KILLED (workload 集合検査 + 正例) |
| M4 | job body に `read-heavy` 枝を追加 | KILLED (受理 workload 検査 + 正例) |
| M5 | 分母を stock 適応へすり替え | KILLED (分母検査 + 正例) |
| M6 | 完備条件を `False and` で恒真化 | KILLED (完備検査 + 正例) |
| M7 | PBS walltime を内側 cap より短く | KILLED (時間予算検査 + 正例) |

M1・M3〜M7 の本走は 6/6 が `matches_expectation=true` で KILLED。
成果物は `mutation-final-report.json` (job dir、repo 外)。

**M2 の再照準 (erratum)。** M2 は pytest 層では生存した。registry と runbook 投影表の
集合完全一致を守っているのは pytest ではなく `tools/check_docs.py` であり、
`orchestrator/tests/test_check_docs.py` は合成 fixture 上で動くため実 repo の行削除を見ない。
実効 gate へ照準し直し、`DW-O19` の一時変異で直接測った。

- 変異前: `check_docs: 違反なし` (rc=0)
- 投影表の 1 行を削除: `Pegasus admission drift — runbook §7.0 投影表が registry と
  集合完全一致しない — registry_only=[('tools/pegasus/a5_second_boot_backoff_sweep.sh',
  'dispatch-required', 'static job-body classification')]` (rc=1)
- 復元後: rc=0、作業ツリーも clean

**単一理由で赤くなることを実測した。**

## 実測が走れない理由 — F660

投入器を走らせようとして、bash の機械防壁が
`未登録 Pegasus 実行体 (tools/pegasus/submit_a5_second_boot_backoff_sweep.sh)` で拒否した。

`hooks/guard_bash.py` は `__file__` 基準で **main の checkout** の登録簿を読む。
wave の worktree で登録しても防壁からは見えない。これは F660 が既に記録した型であり、
同 F は次を定めている。

- **迂回してはいけない道:** 絶対 path で呼ぶと管轄外と判定されて素通りする。**行ってはならない。**
- **恒久対応:** 新しい Pegasus 実行体を要する実測は、機構を着地させる wave と実測を行う wave に
  分ける。段 1 の brief で「この wave の実測が新規 Pegasus 実行体を要するか」を先に判定する。
- **再発検知:** 実測を含む wave の brief 時点で、投入経路が既登録かを
  `tools/pegasus/admission_registry.json` の **main 側の現物**に対して確認する。

**本 wave はこの再発検知を段 1 で行わず、段 6 まで進んでから当たった。**
迂回はしていない。

## 次の一手 — 着地後に 1 コマンド

この wave が main へ着地すると防壁の登録簿に entry が入るので、次で走る。

```
bash tools/pegasus/submit_a5_second_boot_backoff_sweep.sh \
  --output-parent <repo 外の既存 directory>
```

- 投入前に作業ツリーが clean で、`git rev-parse HEAD` が投入時の HEAD と一致している必要がある。
  **job は開始時に `PBS_O_WORKDIR` の HEAD が投入時の SHA と一致することを検査する。**
  したがって **2 job が終わるまでその branch へ commit してはならない。**
- 投入器は repo root へ移動してから `qsub` する。
- 各 job は `<output-parent>/<group-id>-<workload>/` へ official 出力を書き、
  同 directory 直下に `result.json` を create-only で publish する。
- 完了後は `git worktree list` を見て、job が作った scratch worktree の残骸が無いことを確かめる。
  残骸は全 wave の land を止める。

## 一次資料

- D1100 / D59、archive worklog 2026-08-05 (237)
- `docs/paper-story/2026-09-02.md` §2 (論文採用値) と §8 (A-2 / A-5)
- `output/insights/2026-08-25_paper-story-a3-gain-unification/README.md` (算出規則)
- `output/insights/2026-08-24_paper-story-a2-certification/raw-manifest.json` (A-2 の host / boot)
- `docs/failures.md` F660
