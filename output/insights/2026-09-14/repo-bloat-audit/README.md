# リポジトリ膨張の実測と、削除可否の確定

- authority: none
- default_effect: no-state-change
- 作成: 2026-09-14 / wave `dev-wave-repo-bloat-cleanup`
- 基準: 実測は main `30efab0c48fd9b1a0ec9716e8468e3f42961ce2f` の作業ツリー。
  wave は途中で `640e5d431f30a7aa15e3601a1b81a4cf5d220b32` へ ff 追従した。
- 可変状態の正本ではない。裁定パッケージを含む。

ユーザー依頼: 「izanagi のお掃除。リポジトリが大きく膨らんできてしまったと思う。あってもなくても
研究に影響がほとんどないテスト・記録というものが膨れ上がっているはずだ。慎重に調査し、慎重に
掃除してください。」

## 結論

**tracked file の削除確定は 0 件・0 bytes。** 独立した 3 経路 (親の実測、段 2 plan、段 3 の敵対
相談 2 レンズ) が一致した。依頼の仮説は、記録側については**概ね成立しない**。テスト側は
「増えている」は真だが「不要な増分」は**証明されていない**。

膨張の実体は「捨てられる不要物」ではなく、**現役の pin 閉包に入った証拠と、契約を検査する
テスト**である。削れるものが無いこと自体が、この監査の成果物である。

## 1. 規模の実測

| 対象 | bytes | 件数 |
|---|---:|---:|
| tracked 合計 | 約 690,000,000 | 24,684 |
| `output/` | 601,392,319 | 21,965 |
| `output/insights` | 396,269,908 | 18,205 |
| `output/env` | 195,405,078 | 3,246 |
| `docs/` | 41,482,073 | 1,354 |
| `orchestrator/` | 38,569,275 | 1,029 |
| `.git` | 約 1,800,000,000 | — |

種別内訳: `.json` 313 MB / 5,317、`.log` 120 MB / 300、`.md` 111 MB / 8,341、
`.gz` 66 MB / 1,744、`.jsonl` 11.7 MB / 414。

最大 file は correctness trace 4 本 (計 119.6 MB、
`output/env/pegasus/silo_ladder_rung1/job-staging/0_873920.nqsv/raw-bundle-attempt-1/correctness/traces/trace_0..3.log`)。

**「ビルド生成物の混入」仮説は否定された。** tracked な `CMakeCache.txt` は 4 件 121,111 bytes だけで、
`.o` / `.a` / `.so` / `CMakeFiles/` は 0 件。ignored 側も `__pycache__` 群と
`output/campaign-locks` / `output/pegasus-dispatch` / `output/runs` / `.pytest_cache` の 28 entry だけである。

ディスク容量は制約ではない。filesystem は 85T 中 3.0T 使用 (4%)、83T 空き。

## 2. 記録側 — なぜ削れないか

### 2.1 重複は「余分なコピー」ではない

同一 blob が 2 か所以上にある tracked file は、余分分だけで 6,761 件 / 50,265,692 bytes ある。
しかし現物で pin を確認した結果、大きい群はすべて拘束されていた。

| 群 | 規模 | 現物の拘束 |
|---|---|---|
| `output/s6-rounds/frozen/payloads/main-00..19.json` | 20 本 × 63,795 bytes | `hash_ledger.json` が slot 別 hash を持ち、`orchestrator/campaign/s6_proposal_rounds.py:244` が全 round・全 arm の path を構成して読み、hash 照合する |
| 同 `c5-00..19.json` | 20 本 × 61,055 bytes | 同じ reader。`:361` の入口が verify を先に呼び `:375` で slot payload を読む |
| 同 `c4-{05,06,07,08,11,16}.json` | 6 本 × 63,849 bytes | 同じ slot→path→hash 拘束 |
| `output/insights/2026-08-29_t2033-axis1-retake/bundle/ledgers/` の pass1/pass2 | 5 組 × 各 254〜297 KB | bundle manifest が両 path と hash を個別に記録 (manifest:3058 / :3083 等) |

**`frozen` という語が path にあることは pin の証拠ではないので、現物で pin を探した結果である。**
「両 path とも非 pin」の組は 1 つも得られなかった。

### 2.2 job-staging は複製ではなく唯一の証拠

`job-staging` 配下は 1,206 件 / 123,987,396 bytes。**他所に同一 blob はゼロ**である。
docs 44 か所と、`orchestrator/campaign/silo_ladder_rung1.py`、
`orchestrator/qualification/collector.py`、`orchestrator/campaign/floor_liveness.py`、
`orchestrator/qualification/t126_driver.py` から参照される。
D430 は calibration の job-staging 族を実機 `PBS_JOBID` の根拠として扱う。

ただし「他所に同一 blob が無い」は「価値がある」を含意しない (段 3 luna の指摘、real)。
本監査は job-staging 全 1,206 件の研究価値を個別に判定していない。

### 2.3 0 byte も不要の証拠にならない

tracked blob の 0 byte は 2,838 件ある。例:

- `orchestrator/tests/fixtures/paper_story_a1/qstat-f-absent-900001.stderr` は
  `test_paper_story_a1_job_contract.py:1250` が実際に読む fixture。
- `output/registry/t139-publication-reservations.jsonl` は
  `orchestrator/publication/ledger.py:31` が束縛する台帳。
- 多数の空 `stderr` は実行記録に属する。

### 2.4 削除判定の基準を是正した

親の初期基準「repo 内のどこからも参照されない」は過剰だった。D1941 は
「歴史的な名前の観測だけを現役 pin と同一視しない」と定めている。是正後の 4 分類:

| 分類 | 判定 | 削除への意味 |
|---|---|---|
| 現役の拘束的 consumer | 実行コードが読む / manifest が path・hash を要求する / 現行 docs が内容を根拠として必要とする | 破損・値の変化を解消できなければ不可 |
| 非拘束の参照 | 現行コードが名前を保持するが対象の実在を要求せず、消しても残存対象の処理が変わらない | 名前の存在だけでは阻却しない |
| 歴史的言及 | 過去の commit・試験実行・分類結果の記録。現在の実在を要求しない | 現行対象の存続理由にはならない。記録自体は保存する |
| 未解決 | key→path、glob、hash、動的ロードが未確認 | 「pin あり」「削除可能」のどちらにも断定しない |

**この是正を適用しても、記録側で削除可能側へ移ったものは 0 件だった。**

## 3. テスト側 — 増分は本物の契約検査だった

| 指標 | 2026-08-24 (D747) | 2026-09-14 | 倍率 |
|---|---:|---:|---:|
| 受入台帳 nodeid | 14,467 | 23,105 | 1.60 |
| 直列総和 (秒) | 5,364.9 | 15,306.6 | 2.85 |

`orchestrator/tests` は同期間に正味 +265,519 行 (+286,904 / -21,385)。test file 378、
test 関数 15,666、行数 563,371。本体は orchestrator 288,443 行 / tools 151,664 行。

費用の分布 (受入所要台帳):

| 帯 | 件数 | 直列秒 | 全 work 比 |
|---|---:|---:|---:|
| < 0.01 秒 | 12,223 | 25.8 | 0.2% |
| < 0.1 秒 | 16,374 | 198.4 | 1.3% |
| >= 1 秒 | 2,303 | 13,528.4 | 88.4% |
| >= 10 秒 | 372 | 8,256.0 | 53.9% |

**D747 の結論は母数 2.85 倍でも成立する。** 件数の 53% を消しても直列で 25.8 秒しか減らない。

### 3.1 「不要なテストが増えた」は証明されなかった

本体 AST 一致で拾い上げた群は 22〜23 群あるが、そのうち現物で検分した 10 群はすべて**非重複**だった。

| 群 | 非重複の理由 |
|---|---|
| `test_s1_measurement_freeze.py:286` ↔ `test_s1_verify_extime_calibration.py:243` | `M` が別ソース。別ソースの禁止 import を検査 |
| `test_b10_extended_figure_provenance.py:891` ↔ `test_plot_b10_extended_backoff.py:354` | 前者は `HASHES`、後者は provenance JSON の `external_inputs` を読む |
| `test_env_contract.py:161` ↔ `:167` | 非正整数 `[0,-1,-1800]` と型違反 `[1800.0,"1800",True,False]` で入力が違う |
| `test_p3_b4_analysis_prereg_consumer.py:129` ↔ `:138` | analysis invalid reason 12 種と registry violation reason 5 種で変異対象が違う |
| `test_s8a_trigger_sweep.py:86` ↔ `test_s6_sort_sweep.py:79` | `W.run_sweep` の `W` が別モジュール |
| ほか 5 群 | 同様に入力・module・呼出先が異なる |

**AST 一致は削除数ではなく調査入口である。**

8 月 24 日以降に新設されたテストを実際に開くと、送信間隔と状態永続化、証拠 body 改変の拒否、
事前登録 literal の改変拒否 (`A_min=0.60→0.61`)、生成器と別 verifier を使う自己実行入口など、
具体的な契約逸脱を検査していた。**+265,519 行の大半が不要だと一般化する材料は得られなかった。**

### 3.2 唯一の真の重複 (実施しない)

- 削除候補: `orchestrator/tests/test_related_work_search.py:1978`
  `test_postprocessing_tier_api_remains_outside_executor_scope`
- 残す同値検査: 同 file:1581 `test_tier_enforcement_remains_outside_registration_executor_scope`
- 両者とも引数・decorator なし。同じ `:19` の `search` import に対する
  `assert not hasattr(search, "validate_tier_analysis")` のみ。定義・本体 2 行で実際に 124 bytes。
- `orchestrator/tests/conftest.py:1502-1539` の台帳 validator は
  `nodeid_count == len(durations)` を要求するので、台帳の行だけを消す操作は採れない。
  行と件数を整合させれば validator の条件は満たせる。
- 過去の変異台帳 (`output/insights/**/mut*-ledger.json`) への nodeid 掲載は、過去の
  `repo_head` に束縛された歴史記録であり、現行テストの保持義務ではない。

**本 wave では実施しない。** 124 bytes の削除は成果物 (certified 選択・レポート・台帳) の値・
受理集合・参照を 1 つも変えず、`DW-G05` の意味で must-fix ではない。実装面の差分を作れば
Codex 実装子・敵対レビュー 2 本・変異 matrix・dispatch 本走が必須になり、割に合わない。
次にテスト整理を主目的にする wave が、この節をそのまま着手点にできる。

## 4. 実際に大きい無駄 — worktree の残置

削除可能な tracked file は無かったが、**作業コピーの残置**は実在する。

- `git worktree list` = 42 本。1 本の実測 774 MB。
- local branch 44 本。うち main へ取り込み済み 27 本、未取り込み 17 本。
- branch が取り込み済みの worktree = 26 本。
  - `tools/check_worktree_occupancy.py` rc=0 (非占有) = 23 本、rc=1 (占有) = 3 本、rc=2 = 0 本。
  - lock 状態は locked 7 / unlocked 19。
  - **`git status --porcelain` が空なのは 3 本だけで、23 本は未 commit 差分を持つ。**

したがって「取り込み済み × 非占有 × 非 lock × clean」を満たすのは **1 本だけ**である。

| worktree | 判定 |
|---|---|
| `.claude/worktrees/dev-wave-t1875-delta-min-gate` | 取り込み済み・clean・非占有・非 lock。**撤去候補** |
| `.claude/worktrees/dev-wave-t2267-exec-site-class` | 同条件だが locked。cleanup-branches §2 により報告限定 |
| 残り 23 本 | 未 commit 差分あり。Codex 実装子の編集が残っている。撤去不可 |

未 commit 差分の中身は `orchestrator/campaign/*.py` と `orchestrator/tests/*.py` の実編集である
(例: `.codex/worktrees/t1994-s3` は 13 file、`.claude/worktrees/dev-wave-t1994-readonly-snapshot` は
21 file)。main の現物と blob hash を照合すると、83 件中 68 件が main と一致しない。
一致しない理由は「未着地」とは限らず、main がその後進んだ可能性もあるため、**着地判定は
できていない**。

### 4.1 残置の構造的原因

**「lock が撤去不能を作る」は refuted。** `tools/dev_wave_cleanup.py:943` は事前検査後に自対象の
lock を解除して撤去を進める。実際の残置経路は次である。

1. land と cleanup は別工程である (D702 がその分離と理由を明記)。
2. 親が land 後に対象外へ移り、cleanup を明示実行する設計になっている。
3. 親の終了・中断、cwd 固定、占有・dirty による停止では worktree が残る。
4. 次 wave は他者の残置物を自動回収できず、`/cleanup-branches` も locked・所有不明を触らない。

**親の生存と終端処理に依存し、残置後の回収権限が狭いこと**が滞留を許している。
ただし 23 本すべてをこの機序へ帰属させるログは無い。原因未確定の 23 本を一括して新しい
failure 型にはしない。

## 5. 外部からの寄与 — 受入 fixture の全件複製

別 session (受入 5 分の律速を調査中) から実測が届き、親が現物で検算した。

- `orchestrator/tests/test_s8b_oracle_driver.py:1003` は
  `shutil.copytree(ROOT / "orchestrator", ...)` で orchestrator 全体を複製する。
- `:1006` の `_copy_git_visible_output` (`:819`) は `_git_visible_output_paths` の全件から
  `migration.RECEIPT_REL` と `DRAFT_REL` の 2 件だけを除いて複製する。
- `:873` の docstring は「36MB / 2300 ファイルの copytree で 1 回 15〜22 秒」と書く。
  これは 2026-07-26 の commit `6d3f2d21a` 時点の実測である。
- **今日のコピー元は tracked だけで 22,994 件 / 639,961,594 bytes** (`output/` 21,965 +
  `orchestrator/` 1,029)。件数 10.0 倍、bytes 17.8 倍。

**`output/` が削れないことは、この経路の解を「fixture のコピー対象を絞る」側へ確定させる。**
ただし `:1302` と `:1328` が `_copy_git_visible_output` の**全件性そのもの**を検査しているので、
絞る変更はその 2 つを正しく赤にする。`:1000` のコメント (subprocess が import closure を host から
補えないようにする) が全件性を要求する理由なので、先に読む必要がある。

なお、その session は「最遅 shard は shard-0」と報告したが、D1918 は 2026-09-09 の 9 走を根拠に
「最遅 shard は shard-2、9 走中 8 走」と記録している。**どちらが現行かは本 wave では判定していない。**

## 6. 裁定パッケージ (ユーザー手番)

1. **worktree 撤去。** 撤去候補は `dev-wave-t1875-delta-min-gate` の 1 本。
   `dev-wave-t2267-exec-site-class` は locked のため報告限定。実行には対象を限定した
   ユーザー指示と `/cleanup-branches` の起動が要る (D204 / D854 / cleanup-branches §0)。
   本 wave は D854 が破壊系に分類した操作を行わない。
2. **残置の恒久対応。** 親の生存に依存しない回収経路を作るか、残置を許容するかの裁定。
3. **重複 test 1 件の削除。** §3.2 の形で着手可能。本 wave では実施しない。
4. **受入 fixture の全件複製。** §5。別 session の系列が扱う。

## 7. 膨張が研究を止めた実例 — 受入 attempt 1 の setup error

本 wave の受入全走そのものが、膨張の実害を実演した。

- 受入 attempt 1 (docs のみの tip `741e27283`) は
  **23,308 passed / 68 skipped / 6 error**、子 rc=1、受領証未発行 (待ち手 rc=70)。
- 6 件はすべて `test_t1259_qsub_env_delivery_probe.py` の setup error で、traceback の Git argv は
  `git -C <wave worktree> ls-files --others --exclude-standard -z` の **30.0 秒 TimeoutExpired**。
- 同 tip・同 file の単独再走 (996322.nqsv) は **51 passed / 16.67 秒、rc=0** で非再現。
- **親が同じ worktree で同 argv を 3 連続実行した wall は 34.60 / 24.96 / 15.90 秒**
  (load average 68.35〜88.49)。**30 秒の timeout を跨いでいる。**

つまり「24,684 件 / 約 690 MB の作業ツリーに対する未追跡走査」が、テスト側が置いた 30 秒の境界に
届いてしまっている。F945 が同型を既に記録しており、本 wave は 3 度目の観測である。

**ただし遅延の I/O 要因は分離していない。** 新規 worktree の cold cache と login node 負荷が
交絡しており、どちらがどれだけ効くかは測っていない。走査時間の分布を与えただけである。
恒久対応は F945 のまま変えない (timeout 拡大・fixture の stub 化・除外・汎用 gate の新設はしない)。

この観測は §1 の「ディスク容量は制約でない」と矛盾しない。**制約になっているのは容量ではなく
file 件数に対する metadata 走査の所要**である。§5 の fixture 全件複製と同じ層の話であり、
削除ではなく「走査・複製の対象を減らすか、境界を実測に合わせるか」が打ち手になる。

## 8. 本監査が確かめていないこと

- `output/` 全件の `FROZEN_MANIFEST` / generator source hash / key→canonical path /
  role・xdist group pin の完全閉包。任意 path を引数で受ける汎用 reader の全呼出経路。
- 同一 blob 重複 6,761 件、0 byte 2,838 件の個別判定。
- AST 一致群の残り全群の意味論的検分。
- checkout・検索・fold の現在の所要、個人 quota・inode 制約。
- 23 本の worktree それぞれの残置原因と、未 commit 差分の着地判定。
- `.git` 1.8 GB の内訳。履歴の書き換えは行わないので本 wave の対象外である。

## 逐語

段 2 plan と段 3 敵対相談 2 レンズの出力は `verbatim/` に凍結してある。
