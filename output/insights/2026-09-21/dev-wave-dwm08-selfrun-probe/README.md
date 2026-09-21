# 変異 probe の login self-run 手順を DW-M08 へ収容する依頼 — 中核は D2195 (entry 1774) として着地済み、未被覆 3 要素と skip の名指しを純増として収め、同節の詰め書きで L1.5 予算内に収容 (dev-wave、2026-09-21)

authority: none / default_effect: no-state-change (可変状態の正本は worklog 末尾と現行 phase doc)。

台帳 ID 未起票 (依頼文は /dev-wave の引数、逐語は `verbatim/origin.md`)。軽量版 (段 2・3 省略、段 6 独立 read-only レビュー 1 本 + 焦点再レビュー 1 本、docs-only、Codex author なし = D95 の docs-only 例外、変異 matrix 免除 = DW-S04、受入全走は免除しない)。
branch `worktree-dev-wave-dwm08-selfrun-probe`、起点 local main `5efd69367` (開始 gate rc 0 = job dir `startup-gate.log`、mtime 2026-09-21 07:35:55 JST、背景 job 57f119fa)、job dir `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-dwm08-selfrun-probe` (brief `brief.md` / `brief-v2.md`、対応表 `s6-fix-table.md`、codex の prompt / 報告 `codex/`、一次資料の写し `verbatim/`、予算実測・差し替え script `*.py` と受入 / land / 撤去 script `*.sh` — script は実装面 (D95) なので repo へ入れず `verbatim/scripts.sha256` で束縛)。

## 1. 依頼 (逐語は `verbatim/origin.md`)

変異 matrix の probe 走 (dispatch、全件 SURVIVED で期待 node を観測) を login self-run に置き換える手順を DW-M08 へ収容する (docs + pin 追随、着手直前の local main から fresh worktree)。手順 = 各変異を登録 worktree の生成器へ注入 → 新 test file の `__main__` harness を `PYTHONPATH=. python3` で自走 → 原 bytes へ復元し sha256 一致を assert → git status clean を確認 → 観測 node (`\S+?::[A-Za-z0-9_]+` で抽出し `orchestrator/tests/` を前置) で dispatch final を 1 回。実測 = 2026-09-20 fig13 wave。parametrize / skip を持つ test や node 食い違いの疑い 1 件でも dispatch probe へ戻す条件を残す。byte 予算は D782 手順 1 段目 (既存記述の削減) で収容し上限は動かさない、pin 追随は Codex author (D95)。完全一致要件 (DW-M08、F33) と KILLED 判定は変えない。規律 2 を緩めない。手順の収容だけ。gate・台帳・一般化の追加は scope 外。

## 2. 段 1 — 承認前提を覆す新事実: 依頼の中核は着地済み

- `grep -n "login self-run" docs/decisions.md` → **D2195** (2026-09-21)「変異の期待 node は login self-run で観測し、dispatch probe は適用条件を満たさない test の fallback にする」。実装 commit `993d2fc5f` (01:40 JST) + fix 1 `6d600f0a6` (01:55) + fix 2 `618fb8501` (02:18)、記録 `33de1a3ea` (02:24)、worklog entry 1774 (`docs/archive/worklog-phase3-0921-1774.md`)、fold receipt `docs/spool/FOLDED.md` 5133〜5134 行 (tested_tip `4566c64b4`)。一次資料 = `output/insights/2026-09-21/dev-wave-wall-decomp/README.md`。
- 依頼文は先行 wave の依頼 (`dev-wave-wall-decomp/verbatim/origin.md`: 「(a) 変異 probe の dispatch 走を login self-run に置き換える手順を DW-M08 へ収容 … parametrize / skip で node が食い違いうる test は dispatch probe へ戻す条件を残す、byte 予算は D782 手順 1 段目で収容し上限不変、pin 追随は Codex author = D95」) と同型で、着地前に起票された写しと判断した。起票時点は証明していない。
- **実測値の出所は食い違う:** 依頼文「20 変異 1 分」、D2195 理由「20 変異で 2 分」。fig13 job dir の mtime (`verbatim/fig13-probe-mtimes.txt`) は `login_probe.py` 20:19:35、`login-probe-2.log` / `mutation-spec-v3-final.observed.json` 20:21:05 で差 90 秒、初回 `login-probe.log` 20:19:03 (2026-09-20)。これは file 更新時刻の差であり、20 変異全体の実行時間の上限や「1 分」「2 分」の算出由来は確認できない。両記述は統一しない (焦点再レビュー A 所見 1)。
- **既存被覆表** (依頼の手順要素 → 既存の所在。段 1 の表を段 6 レビュー A 所見 1 で訂正した版):

| 依頼の要素 | 所在 | 判定 |
|---|---|---|
| 変異ごとに注入 → 自走 harness の FAIL / ERROR を観測・正規化 | DW-M08 第 3 文 | 被覆 |
| 原 bytes へ復元し sha256 一致 | DW-M08 第 3 文「`DW-O19` で復元し sha256 も照合」+ DW-O19 (復元 = `git checkout --`、復元 bytes は commit と照合) | 被覆 (assert 構文までは固定しない) |
| 注入先 = 登録 worktree の生成器 | DW-M07「source-repo は D1009 の独立 clone (main=対象commit)」は本走の木、DW-O19 は統合 commit 後・使い捨て worktree。**self-run をどの木・どの commit で観測するかの束縛はなかった** | **部分被覆 → 収容** |
| `PYTHONPATH=. python3` で自走 | DW-M08 / D2195 は「自走 harness」としか書かず、起動方法・import 解決条件は未記載 (`orchestrator/tests/README.md` 二重 runner は `python3 orchestrator/tests/test_*.py`) | **未被覆 → 収容** |
| git status clean の確認 | DW-O19「変異前は `--porcelain` 空確認」は**変異前**、「復元 bytes は commit と照合」は対象 file だけで、harness が作った untracked や別 tracked file の変更を見ない | **未被覆 → 収容** |
| node 抽出 regex + `orchestrator/tests/` 前置 | DW-M08「自走の全 node が `--collect-only` と同形式で照合でき」+ F71 (抽出規約、抽出 0 件は fail-closed) | 一般契約は被覆。regex は**意図的に固定しない** (§3) |
| dispatch final を 1 回 | DW-M08「erratum・再登録後に dispatch final を走らせる」、D2195「dispatch final を 1 回走らせる」 | 被覆 |
| fig13 の実測値 | D2195 理由 | 被覆 (docs leaf には日付付き逸話を置かない = skill-self-improvement routing) |
| parametrize / fixture / 環境変数 / import 副作用 / 対応不明 → dispatch probe | DW-M08 第 4 文 | 被覆 |
| **skip を持つ test → dispatch probe** | 「対応不明」に含意される (レビュー A 所見 4)。名指しは**具体例の明示**であり新しい防壁ではない | **純増 (具体例) → 収容** |
| 完全一致要件 (F33) と KILLED 判定を変えない | DW-M08 第 2 文 | 不変 |
| pin 追随 (Codex author) | `tools/check_docs.py` / `orchestrator/tests/test_check_docs.py` は mutation.md を節 ID 在庫 (856〜858、923、935〜936、971)・dispatch 配置・層予算 (359〜361、5292〜5395) で束縛し、DW-M08 本文の literal pin なし。`test_check_docs.py:3351` の 3_750 と `:3496` の 25_200 は `_build_min_repo()` の合成 fixture への assert | 追随対象なし → 実装面差分ゼロ (レビュー A 所見 8、焦点 A で追認) |

- 先行 wave の一次資料で skip が落ちた経緯: 依頼と改訂草稿 (`dev-wave-wall-decomp/verbatim/draft-edits.md` 27〜28 行「parametrize / fixture / skip で自走と pytest の node が食い違う test は dispatch probe へ戻す」) には skip があり、段 3 所見 10 (「Skip は失敗に数えず」) を観測集合 = FAIL + ERROR の形で裁定 (s4-ruling 行 10)、段 6 レビュー A の置換案 (`s6-review-A.md` 132 行) の列挙が skip を含まず、fix 1 でその列挙が採用された。意図的な除外の記録はない。
- skip が乖離を生む機序 (harness 依存): `orchestrator/tests/skiputil.py` の `skip()` は pytest 配下では `pytest.skip`、素の runner では `Skip(Exception)` を投げる。`except Skip` を持つ harness (`test_plot_b10_waiting_grid_forest.py::_run` 673〜700 行、fig13 の file) では SKIP に数え pytest と一致する。持たない harness (`test_check_docs.py::_run` 12836〜12872 行、`except AssertionError` / `except Exception` のみ) では `Skip` が ERROR に数えられて期待 node に入り、pytest では SKIPPED になる。`@pytest.mark.skipif` は mark を無視して実行される。`pytest.skip()` 直呼びの `Skipped` (BaseException) は捕まらず自走が中断する。`--collect-only` の node 集合一致ではいずれも検出できない (skip は collection でなく実行時の結果)。帰結は final の MISMATCH (fail-closed、final 1 回分の空振り) であって偽 KILLED ではない。**空振りの回数は未実測** (レビュー A 所見 9)。利用件数: skiputil 23 file、`pytest.skip` / `mark.skip` 直書き 37 file (2026-09-21 grep)。
- 予算実測 (`measure_budget.py`、read-only、check_docs の関数を再利用): 起点 L1 10623 / 10625 (残 2)、L1.5 9681 / 9696 (残 15)、DW-M08 1170 bytes (L1.5、単節上限なし)。check_docs 基線 rc 0。

## 3. 段 4 裁定 (親) と段 6 後の改訂

- P1 採用 (commit `002f926f4`): DW-M08 第 4 文の列挙 `parametrize・fixture（conftest / autouse）` → `parametrize・skip・fixture（conftest / autouse）` (+7 bytes)。self-run の適用集合を狭める方向のみ。
- P2 不採用 (収容しない): 抽出 regex と `orchestrator/tests/` 前置。harness ごとに FAIL 行の形が違う (fig13 は `FAIL <basename>::<fn>`、test_check_docs は `FAIL <fn>[label]` で `::` なし、依頼の regex は後者に 0 件一致) ため leaf に固定せず「正規化 → `--collect-only` と同形式で照合」で足りる。誤りは final の MISMATCH で fail-closed (レビュー A 所見 5 で妥当と判定)。
- 収容しない: 実測値 (D2195 理由が持つ)。gate・台帳・新 D は起票しない (D2195 の適用条件の明確化に留まる、レビュー A 所見 10)。
- **段 6 レビュー A の must-fix 1 を受けた改訂 (commit `956cce1c9`):** DW-M08 第 3 文に (a)「対象commitの木へ」(DW-M07 の source-repo と同じ commit へ self-run の観測を束縛)、(b)「`PYTHONPATH=. python3`の自走harness」、(c)「sha256と`--porcelain`空も照合」を足す。
- 条件表: O08 / O09 / O10 / O11 / O13 / O19 いずれも不成立。O12 不成立 (裁定と実行は一致、改訂は段 6 の fix として追加)。O16 成立 (焦点再レビュー前に読了)。

## 4. 実装 (docs のみ、2 commit)

- `002f926f4`: `docs/dev-wave/mutation.md` の 1 行に `・skip` を挿入。L1.5 9681 → 9688 / 9696。
- `956cce1c9`: DW-M08 の本文を差し替え。**収容 65 bytes は D782 手順 1 段目 (既存記述の削減) として、DW-M08 内の CJK 隣接空白 58 bytes と段落内改行 6 bytes を同 file の M05〜M07 と同じ詰め書きへ揃えて捻出し、純増 1 byte** (DW-M08 1177 → 1178、焦点再レビュー A の独立検算と一致)。空白・改行を除いた 002f926f4 → 956cce1c9 の差分は追加 3 (`対象commitの木へ`、`` `PYTHONPATH=.python3`の ``、`` と`--porcelain`空 ``) + 置換 1 (`の` → `で`) だけ (`verbatim/semantic_diff_002f926f4_to_956cce1c9.txt`、焦点 A が diff から独立に再構成して一致)。F71 / F33 / DW-O19 の参照、停止条件、完全一致、fallback 列挙、diagnostic 別枠、新旧両走の義務は全部残る。
- 累計: DW-M08 1170 → 1178 (+8)、L1.5 9681 → 9689 / 9696 (残 7)、L1 10623 / 10625 不変、上限 3 定数 (`check_docs.py` 359〜361 行) 不変。`verbatim/layer_bytes_956cce1c9.txt`。
- 検査: check_docs 違反なし (基線・002f926f4・956cce1c9 の 3 回)、message-file 検査 rc 0 (2 回)、commit 後の全史 provenance 監査 12262 / 12263 件・新規違反なし (login)。pin 追随なし (§2 の表)。

## 5. 改訂後の DW-M08 (第 3〜4 文、`956cce1c9`)

> 期待nodeはlogin self-run（対象commitの木へ変異ごとに注入→`PYTHONPATH=. python3`の自走harnessでFAIL / ERRORを観測・正規化→`DW-O19`で復元しsha256と`--porcelain`空も照合）か初回と明記したdispatch probeで集め、erratum・再登録後にdispatch finalを走らせる。適用は自走の全nodeが`--collect-only`と同形式で照合できlogin実行が許されるfileに限り、pytest専用allowlist・parametrize・skip・fixture（conftest / autouse）・環境変数・import副作用への依存や対応不明はdispatch probeへ戻す。

## 6. 段 6 — レビューと焦点再レビュー (逐語は `verbatim/s6-review-A.md`、`verbatim/s6-focus-A.md`、対応表 `verbatim/s6-fix-table.md`)

- 独立レビュー A (codex read-only、gpt-6-astra、07:48〜07:51 JST): 所見 12 = real must-fix 2 / should 2 / nit 2 / refuted 5 / 判定不能 1。**NO-GO** (「依頼は被覆済み、純増は skip だけ」という完了判断に対して)。must-fix 1 = 注入先 (部分被覆)・起動方法 (未被覆)・復元後 clean (未被覆)、must-fix 2 = brief の「実測値同一」は誤り (1 分 ≠ 2 分)。should = 「final 1 回空振り」は可能性で実測ではない (9)、D2195 本文は fix 1 前の条件を保持 (12)。nit = skip 名指しは規範上冗長 (4)、「節 ID と予算だけ」は粗い (8)。refuted = collect-only が skip を検出する (3、親の主張を追認)、regex 固定 (5、妥当)、語形・緩和 (6)、+7 bytes (7)、literal pin (8)、scope 外 (10)。
- fix (親、docs-only、`956cce1c9`) + brief v2 + 対応表 12 行 → **焦点再レビュー A (08:00〜08:03 JST): GO (手順の収容として)。** 対応表 closed 11 / partial 1 (所見 2 = brief の mtime の書き方)。新規所見: real should 1 (mtime 差を実行時間の上限としない → brief v2 の訂正節で採用)、real nit 1 (改行削減は 9 でなく 6、追加 65 bytes → 同上)、refuted nit 1 (詰め書きの節間不揃いは欠陥と数えない)。DW-M08 への追加訂正なし、残 7 bytes を消費しない。
- 巡数: 2 巡 (3 巡上限内)。親の実機 blocker なし。

## 7. D2195 本文との差 (レビュー A 所見 12)

D2195 は fix 1 前の条件「自走の node 集合 (FAIL + ERROR) が `--collect-only` と一致し」を保持し、着地した DW-M08 (fix 1 `6d600f0a6` 以降) は「全 node の照合可能性」(適用条件) と「変異ごとの失敗観測」(観測) を分ける。canonical は追記のみで、D2195 は直さず worklog に相違を記す。D2195 を適用根拠に読む場合は DW-M08 本文を正とする。

## 8. 検査・受入・land

- check_docs / provenance は §4。受入全走は記録 commit を含む最終 tip に land 前に 1 回投入し (門番付き script `run-acceptance-gated.sh`、`IZANAGI_ACCEPTANCE_SHARDS=3`)、受領証は job dir (`acceptance-receipt-green.json`) と land の記録 (`land-N.json`) が持つ。本 README はその結果を持たない (F36: 自己 hash を含む tip の結果を自分に書かない)。
- 変異 matrix: 免除 (実装面差分ゼロ、DW-S04)。

## 9. 言わないこと

- skip の名指しが final の空振りを何回防ぐかは未実測。
- self-run の所要「1 分」「2 分」はどちらも出所が別で、どちらかを正としない。fig13 の mtime 差 90 秒は file 更新時刻の差であって実行時間ではない。
- 「着地前の写し」は依頼文と先行 wave の依頼の同型性からの判断で、起票時点は証明していない。
- 12 wave の 19〜24% は entry 1774 の記録値の照合で、本 wave で再解析していない。

## 10. 観察 (scope 外、記録のみ) と改善候補

- `orchestrator/tests/README.md` 二重 runner は「`_run()` は skiputil.Skip (SKIP) を分けて数える」と書くが、`test_check_docs.py::_run` は `except Skip` を持たない (規約と実体の差、機械強制なし)。self-run の適用判定を per-file の目視に頼る理由の一つ。gate 追加は本 wave scope 外 → worklog の次の一手へ (P3)。
- 依頼の起票が着地済みを検出できていない (依頼文は D2195 の理由と同型の実測値を持つ)。next-tasks の発火条件 (母集合の取りこぼし) は本 wave で実測していないため候補の記録のみ (段 8)。
- 隔離 worktree の Bash guard は `$(...)`・変数を含む sed・複合 command を拒否する。1 command 1 値に分け、script は file に書いてから実行する (DW-C01 の detach 2 枚と同じ形)。
