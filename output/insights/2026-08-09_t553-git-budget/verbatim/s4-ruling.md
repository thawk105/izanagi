# 段 4 裁定 — [T-553] s8c 事前登録の git wall-clock 予算化

- 親 (Claude) による裁定。base: main `2169a06c` (段 3 後に ff-only で取り込み済み)
- 入力: `s2-plan.md` (codex sol/max)、`s3-lensA.md` (sol/max)、`s3-lensB.md` (luna/max)
- 両レンズとも **NO-GO**。Critical 2 / Major 9 / Minor 3。以下で全件を裁定する。

## 0. 段 3 で判明した「未見の新事実」

1. **`GIT_TIMEOUT_CAP_SECONDS = BASE + MAX_BATCH_REQUESTS × RATE` は絶対 cap ではない**
   (B-06、Critical)。RATE を過大に見積もれば cap も比例して伸び、数十分〜数時間になる。
   条件③ が要求する「絶対時間 cap」を字面でしか満たさない。
2. **本 wave の scope だけでは依頼 (受入全走を安定な緑) を達成しない** (B-12、Critical)。
   同じ F57 族の兄弟が `tools/ruleops.py` に実在し、独立に受入を赤にしている。
3. **実際の要求数は 7,002 ではなく 7,005** (A-06 / B-02 / B-11)。invariant fixture が
   `commit-tree -p HEAD` で候補 commit を 1 件足すため。
4. **`DW-G03` の「独立 2 例」は既に満たされている。** 親 brief §1 は「達しない」と書いたが誤り。
   実測: `docs/failures.md` の F57 に `test_ruleops.py::
   test_real_checkout_independent_maximum_package_and_runner_preflight@real_repo` が
   `ruleops: git-timeout: git log timeout` で落ちた記録が **[T-639] 2026-08-08 と
   [T-648] 2026-08-09 と red-suite wave の 2 走目**の 3 回ある。producer は同じ git、
   欠陥の型も同じ「履歴長に依らない固定 wall-clock」である。

## 1. 所見の裁定 (real / refuted、採用 / 不採用、scope 内 / 外)

| # | 判定 | 採否 | 根拠と処置 |
|---|---|---|---|
| A-01 単一 RATE へ byte 支配 cell を畳むと CAP が過大 | **real** | 採用 | B-06 の独立 CAP で構造的に解消する。RATE は request 数支配の `--batch-check` から決め、byte 支配の `--batch` は「独立 CAP + 既存 16 MiB/64 MiB 上限」で bound する。probe には秒/要求と秒/byte を**別々に**出させる (M3 の F3) |
| A-02 stdin が command に束縛されず予算を増幅できる | **real** | 部分採用 | 予算算出を `R = min(実要求行数, MAX_BATCH_REQUESTS)` にし、**どの経路から来ても予算が CAP を超えられない**構造にする。`read_blob_at` の LF 拒否**新設はしない** — 受理集合を狭める変更で裁定範囲外、かつ `min` 導入で予算面の帰結は消える。残余は裁定パッケージへ記録 |
| A-03 history-log の contended 測定が land 前提条件 | **real** | 採用 | `_history_namespace_paths` の `log --format= --name-only` を本測定の必須 cell にする。**15 秒に対して十分な余裕が観測できなければ、cat-file だけ直して land せず段 4 へ戻して scope を再裁定する** |
| A-04 RATE の根拠を durable に束ねる層が無い | **real** | 採用 | 実測 JSON を `output/insights/2026-08-09_t553-git-budget/` へ凍結し、HEAD・host・PBS_JOBID・R/S・並列度・除外件数を含めて記録する。定数の導出手順を worklog と module コメントから参照する |
| A-05 / B-07 下流 digest 波及 (`core_module_blob_sha256`) | **real** | 記録のみ | `CORE_MODULE_PATH` は編集対象自身。literal golden pin は**存在しない**ことを両レンズが独立に確認 (`FROZEN_MANIFEST` 23 key に s8c なし、g1 raw SHA / `protected_sha256` の外部 pin なし)。コード変更なし。裁定パッケージと worklog へ記録する |
| A-06 / B-02 / B-11 実要求数は 7,005 | **real** | 採用 | probe cell・テスト名・brief を訂正する |
| B-01 / B-04 代表性と過適合 | **real** | 部分採用 | **RATE に明示の安全係数を掛ける** (独立 CAP があるので係数を上げても天井は動かない)。多ノード・多混雑度の反復は本 wave では取らず、**再較正条件を worklog へ書く**。並列度の実行順を降順にして warm 偏りを減らす (M3 の F4) |
| B-03 probe が失敗を成功として記録しうる | **real** | 採用 | 本測定の前に必ず直す (M3 の F1)。除外件数を 0 でも出させる |
| B-05 時間受理集合は確実に広がる | **real** | 記録のみ | R2=(b) により受理する。広がりの数値を worklog へ記録する |
| B-06 cap が RATE に従属している | **real (Critical)** | 採用 | **CAP を独立の絶対定数にする** (下記 §2) |
| B-08 / B-10 閉包根拠と write surface の記述 | **real** | 記録のみ | symbolic key・実 SHA 側からも検索した事実、および「永続成果物は 1 種だが tempfile と mkdir はある」ことを記録する |
| B-09 provenance rc=0 が再現できない | **refuted (子の環境要因)** | 不採用 | 子は read-only sandbox で `output/pegasus-dispatch/` を作れず **rc=16 = dispatch setup failure** になった。監査結果ではない (`DW-O05`: 子の非実走を緑にも赤にもしない)。親は同 worktree で 2 回実測した — merge 前 `--range HEAD..main` が **rc=0 / 13 件、違反なし**、merge 後の全史監査が **rc=0 / 2008 件、新規違反なし / known-violations=30** |
| B-12 本 wave だけでは依頼を達成しない | **real (Critical)** | 採用 (正直に scope を切る) | 下記 §3 |

## 2. 確定した設計 (プラン v2)

```text
R      = min(stdin の LF 要求行数, MAX_BATCH_REQUESTS)      # stdin なし / 空なら 0
B(R)   = min(GIT_TIMEOUT_SECONDS + R × GIT_TIMEOUT_RATE_SECONDS_PER_REQUEST,
             GIT_TIMEOUT_CAP_SECONDS)
```

- `GIT_TIMEOUT_SECONDS = 15.0` — BASE。**据え置き** (下げれば受理集合を狭める)。名前も残す。
- `GIT_TIMEOUT_RATE_SECONDS_PER_REQUEST` — 秒/要求。
  **= (contended 計算ノードで観測した最大 `wall_seconds / requests`) × 安全係数 4、上向き丸め。**
  安全係数を式へ明示するのは B-04 (一機体・少反復の最大値は上界保証ではない) への対応である。
- `GIT_TIMEOUT_CAP_SECONDS = 300.0` — **RATE から独立した絶対 wall-clock 上限。**
  根拠は 2 つ。(i) 受入全走 1 走の実測所要は 1055〜1408 秒であり、1 回の git 呼び出しが
  その 1/4 を超えて占有するのは運用上不能とみなす。(ii) 計算ノードの既定 walltime 30 分 (F167)
  に対しても 1 呼び出しが 1/6 を超えない。**この定数は RATE を変えても動かない。**
- `R` に `min` を掛けるのは A-02 への構造的対応である。`MAX_BATCH_REQUESTS` の検査を
  通らない経路から `_git` へ到達しても、**予算は CAP を超えられない**。

### 変えないもの (不変条件の再確認)

- `_git` / `_git_text` / `validate_condition_freeze_at` / `prepare_revision` / CLI の
  **signature は 1 文字も変えない**。timeout / budget / deadline の caller 引数を出さない (①)。
- `subprocess.run` は 1 回のまま。chunk 分割しない (②)。
- `git-input-limit` の検査は**予算計算より前**に置いたままにする (発火順序の保存)。
- `git-output-limit` / `git-timeout` / `git-failed` / `cat-file-count` / `path-not-blob` /
  `blob-byte-limit` / `batch-request-limit` の発火条件を変えない。
- invariant テストは引数を渡さず production と同じ式を通す (⑤)。xdist group を変えない。
- `MAX_COMMITS` / `MAX_BATCH_REQUESTS` / blob byte 上限は触らない。

## 3. scope の確定 — 依頼を達成しない部分を正直に切る (B-12)

**本 wave が閉じるのは s8c の `_git` 予算だけである。** 受入全走を安定な緑へ戻す依頼は、
本 wave**単独では達成されない**。残る既知の赤を以下に明示し、別タスクとして起票する。

1. **`tools/ruleops.py` の同型欠陥 (F57 兄弟)。** `GIT_TIMEOUT_SECONDS = 20` (`:42`) が
   `_git_read` (`:321-360`) の全 subcommand に固定で掛かり、`git log` が全走負荷下で超過する。
   **`DW-G03` の独立 2 例は満たされたので族一般化は許される。** ただし ruleops の重い呼び出しは
   stdin を持たず、s8c の「stdin 行数」という work proxy が使えない — **設計が別物**になる。
   R1 の裁定文言も `s8c_preregistration.GIT_TIMEOUT_SECONDS` を名指ししている。
   よって**本 wave では実装せず、新規タスクとして起票**し裁定パッケージへ入れる。
2. **[T-698]** (`test_exploration_external_root_keeps_wave_clean` が両ノードで別理由の赤)。
   既に起票済み。本 wave の scope 外。受入全走を赤にしうる。
3. **[T-697] は [T-553] の重複**である (同一 nodeid・同一機序)。別 wave が独立に起票した。
   記録時に重複と明記して片方へ寄せる。
4. R3 = xdist group 統合 (案 F) の別起票。ユーザー裁定どおり本 wave では実装しない。

## 4. land 前提条件 (A-03)

本測定で次を確認できなければ、**実装を land せず段 4 へ戻して scope を再裁定する**。

- `log --format= --name-only --diff-merges=separate <commit> -- <FREEZE_DIR>` の
  contended 実測が 15 秒に対して十分な余裕を持つこと。
- `rev-list` / `ls-tree` も同様。
- 余裕が無ければ「cat-file だけ直して赤を `_history_namespace_paths` へ移す」ことになるため、
  その場合は無 stdin 呼び出しの予算化も同じ wave の scope に入れるか、
  実装せず裁定へ返すかをユーザーへ諮る。

## 5. 変異事前登録 (`DW-M01`)

実装前に登録する。各変異は単一理由性 (無効化時の赤理由が一つに絞れること) を実装子が確認する。

| # | 変異 | 落ちるべき nodeid |
|---:|---|---|
| 1 | `GIT_TIMEOUT_RATE_SECONDS_PER_REQUEST` を 1/10 にする | 定数 pin テスト |
| 2 | `GIT_TIMEOUT_SECONDS` (BASE) を 15.0 未満にする | 定数 pin テスト |
| 3 | `GIT_TIMEOUT_CAP_SECONDS` を `BASE + MAX_BATCH_REQUESTS × RATE` の従属式へ戻す | 定数 pin テスト |
| 4 | `min(..., GIT_TIMEOUT_CAP_SECONDS)` を外して無界線形にする | 予算式テスト `[above-cap]` |
| 5 | `R = min(lines, MAX_BATCH_REQUESTS)` の `min` を外す | 予算式テスト `[amplified-stdin]` |
| 6 | R を LF 行数でなく `len(stdin)` から算出する | 予算式テスト `[real-invariant-r]` |
| 7 | 末尾 LF のない fragment を数え落とす | 予算式テスト `[no-trailing-lf]` |
| 8 | `_git` が helper 値でなく固定 15 秒を subprocess へ渡す | 単一予算テスト |
| 9 | stdin を chunk 分割して subprocess を複数回起動する | 単一予算テストの call-count assert |
| 10 | `_git` または public API に caller timeout override を足す | caller-override 不在テスト |
| 11 | `except subprocess.TimeoutExpired` を削除する | 既存 `test_git_timeout_generation_commit_and_blob_limits_fail_closed` |
| 12 | `git-input-limit` の検査を予算計算の後ろへ移す | 既存 `test_git_input_limit_stops_before_subprocess` |

受理集合を**縮小**する変異 (2、5) の正例として、`R = MAX_BATCH_REQUESTS` でちょうど
`min` が効く境界と、合法な 7,005 要求が通る例を登録する。

## 6. 段 5 の分割

- **単位 A (単一)**: `orchestrator/campaign/s8c_preregistration.py` +
  `orchestrator/tests/test_s8c_preregistration_core.py`。編集面 2 ファイル、Codex 1 子で足りる。
- 定数の実値は本測定の後に確定するため、**測定完了まで段 5 を開始しない**。
