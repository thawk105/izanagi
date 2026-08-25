# 段 4 裁定 — [T-360] / D842 / D895

親が段 2 プランと段 3 レンズ A / B の所見を real/refuted、採用/不採用、scope 内/外へ裁定する。
一次資料は brief.md、s2/plan.md、s3/lensA.md、s3/lensB.md、s4-parent-measurements.md、
s4-parent-measurements-2.md、および本文中の親の再実測。

## 0. 裁定で覆った親自身の前提

- **(P1) は refuted。** 「任意 argv の汎用 task は作らない」は **D895 (2026-08-25 ユーザー裁定)**
  に反する。D895 は「投入表の仕事種別に、任意のコマンドを計算ノードで実行する汎用 task を足す」と
  明記し、理由に「変異本走の transport を投入表の task として実装する決定と同じ面であり、
  まとめて設計できる」と書く。D842 の「同じ wave で扱う」が指す相手はこれである。
  親も段 2 プランも D895 を見落としていた。**裁定済みの方針を親が不採用にしない** (DW-S04)。
- **(P2) は refuted。** 束ね単位は shard ではなく **wrapper invocation 1 本 = job 1 本**。
  実測で `mutation_fanout.py` を走らせている process は 1 本も無く、fanout は D433 で
  この機体では実行不能と裁定済みである。
- **(P3) は採用。** env_allowlist の子側強制は同じ変更単位で入れる。
- **(P4) は採用。** 研究状態 (certified 選択・proof chain・凍結 bytes・campaign 受理集合) は不変。
- **M6 の qdel 記述は過大だった** (lensB 所見 8、real)。正しくは
  「fresh snapshot が RUN なら qdel を発行しない。qstat と qdel の間の遷移は保証外」である
  (`dispatch_compute.py:1803-1808` の docstring と D142 が明記)。**コード変更は不要**、
  記述だけ是正する。

## 1. 汎用 task (D895) — 実装する

**裁定: 実装する。** ただし「任意コマンド」は次の閉じた契約の内側に限る。

| 項目 | 契約 |
|---|---|
| argv | 非空の string list。`shell=False`。shell 文字列を受け取らない |
| env | request からの環境値を一切受け取らない (`env_allowlist=frozenset()` + clean 強制) |
| stdin | `DEVNULL` |
| cwd | repo root 固定 |
| 実行場所 | compute 限定。`_job_script` と `_job_run` の二重 bnode gate を経由する |
| rc | 子 rc をそのまま伝播。`INFRA_RC=16` と混ぜない |

**D103 決定 5 との関係 (lensB 所見 3 を採用、lensA 所見 9 を部分採用):**
D103 が守る性質は「**login で任意 argv を実行しない**」である。`exec_calibrate.py` は
呼ばれた process 上で直ちに `os.execv` するため login で任意実行になる。汎用 task は
二重 bnode gate により compute でしか子を起動しない。したがって汎用 task は D103 の
守る性質を壊さない。**ただし D103 決定 5 の「exact path に任意 trampoline を載せない」という
文言は、汎用 task によって射程が変わる。** これは新 D として記録し、D895 が D103 決定 5 の
どの範囲を supersede するかを明記する (D96 手続: 受理集合を変える改修は decision 記録 +
境界テストを同じ変更単位で)。

**hook の手当て (lensB 所見 2、親が再実測して確認):**
実 site (`PEGASUS_LOGIN`) で `guard_bash.decide` を直接呼んで測った結果:

```
--task generic -- python3.10 -m pytest -q  -> 拒否 (interpreter argv の python3 -m pytest)
--task generic -- pytest -q                -> 許可
--task generic -- cmake --build b -j 48    -> 許可
--task generic -- perf stat ls             -> 許可
```

`_interpreter_residual_violation()` が sanctioned 判定より先に argv 全域を走査するため、
**綴りによって通ったり通らなかったりする**。この状態では D895 の汎用 task は
正規の書き方 (`python -m pytest`) で使えない。**hook が dispatch gateway の exact CLI 形を
認識し、その内側 argv を login 側重量判定の対象外にする**変更を同じ scope に入れる。
これは受理集合を広げる方向なので、正例 (`pytest` と `python -m pytest` の双方) と
負例 (未知 task、直接 trampoline、gateway 以外の綴り) を同じ変更単位で固定する。

**「11/13 が無効化される」は数え方を採らない。** lensB は歴史的 13 経路のうち 11 本が
許可へ反転すると算定したが、その 13 本は D103 当時の算定であり、hook はその後綴りを増やしている。
**古い母集合に対する比を成果物へ書かない。** 記録するのは「汎用 task は compute 限定であり、
login 側の重量拒否は汎用 task 経由でも login では実行しないという性質で保たれる」だけとする。

## 2. mutation task — direct wrapper 1 invocation = 1 job

**裁定:**

- `child_script = ("tools", "mutation_worktree.py")` とする。wrapper が共有 `<out>.lock`、
  disposable checkout、teardown、wrapper receipt を所有するため、D131 #1 の lock 面はここで閉じる。
- **wrapper 固定を「harness 直接起動の禁止」へ拡張しない** (プラン #1 の変更案を不採用)。
  実測では harness 直接起動が実運用の主要形である (3 本中 2 本)。task 経路の外の
  harness 直接起動は現行どおり許す。禁止は受理集合の縮小であり、現行の変異 matrix を壊す。
- **fanout は scope 外** (D433)。`mutation_fanout.py` / `mutation_fanout_contract.py` を変更しない。
  local per-attempt sidecar、merger の request-count v2 も scope 外。
  プランの実装順序 5 と fanout 系テストを落とす。

## 3. 内側 runner mode と DW-M07 — 並存させる

**裁定:** 計算ノード内では inner は `--runner-mode local` **でしかありえない**。
compute から nested qsub は成立せず、harness の dispatch mode は収集段に
`dispatch_compute.py --task tests` を組み立てる (`mutation_harness.py:1386`) ためである。

したがって bundled 経路は、`DW-M07` が dispatch mode に与えていた性質
(**収集段を「変異させられた runner」から隔離する**) を持たない。
`DW-M07` 逐語:「runner の実行経路を変異させる local は runner が自壊し収集段が rc=16 になる。」

**裁定内容:**

- `mutation` task は既存 dispatch mode を**置き換えない。並存させる**。
- bundled 経路の適用条件を `DW-M07` へ 1 条追加する:
  **変異対象が runner 実行経路 (`tools/run_tests.py` / `tools/pegasus/dispatch_compute.py`) を
  含む場合は bundled 経路を使わない。** 含まない変異では bundled 経路を使ってよい。
- この条件付けにより `DW-M07` の既存 3 行 (dispatch 既定、local 自壊、attempt-out は dispatch 専用)
  は**受理集合を変えずに残る**。bundled 経路は「task 経路の内側」という別文脈で
  `--attempt-out` を許す。プランの「local mode 一般で attempt sidecar を許可する」は**不採用**。
- **本 wave 自身の変異 matrix は runner 経路 (`dispatch_compute.py`) を変異させるので、
  従来どおり dispatch mode で走らせる。** bundled 経路を自分の matrix に使わない。

**成果物影響 (DW-G05) の正直な射程:**
bundled 経路が queue 回数を減らすのは、変異対象が runner 経路を含まない場合だけである。
含む場合は従来どおり変異ごとに job が立つ。**「変異本走を 1 ジョブへ束ねた」と無条件には書かない。**
削減の実測値を段 6 の live dogfood で取り、取れた範囲だけを worklog へ書く。

## 4. D117 決定 4 の 4 契約

- **(a) D105 決定 3 の supersede** — 新 D で明記する。閉集合を `{tests, provenance}` から
  `{tests, provenance, mutation, generic}` へ広げる。
- **(b) `env_allowlist` の全キー強制** — 採用。`child_env.update(requested_env)` の前に
  `set(requested_env) - spec.env_allowlist` を拒否する。
  **v1 互換の過剰拒否 (lensA 所見 3、real)** に手当てする: 歴史的 v1 の正規 allowlist には
  `IZANAGI_TEST_ALLOW_UNSTAGED_DELETIONS` が含まれていた。v1 経路用の凍結 legacy allowlist を
  別に持ち、v1 の受理集合を縮小しない。
  **lensA 所見 4 は scope 外**: `env_allowlist` は「request overlay の契約」であって
  「最終 child env 全体」ではない。契約名の意味をコメントとテストで明示するに留め、
  tests / provenance の最終 env を clean 化する変更は受理集合を変えるので裁定へ返す。
  ただし `mutation` / `generic` は新規 task なので、最初から clean env で作る。
- **(c) stdin / cwd / artifact 可視性** — stdin を `DEVNULL` にする。cwd は現行どおり repo root。
  artifact は既存 split artifact root 機構を使う。
- **(d) 子 rc の意味** — dispatcher の rc 体系は変更しない。harness 0/1/2、wrapper 125、
  dispatcher 16 は衝突しない (lensA 所見 7 で裏取り済み、`INFRA_RC` を KILLED と読む経路は無い)。
  衝突するのは fanout の `INFRA_RC=2` だが fanout は scope 外。テストで非衝突を固定する。

## 5. request bytes の queue 越し束縛 (lensA 所見 1) — 採用 (縮小版)

**real。** 親が書いた `request.json` の hash はどこにも束縛されず、queue 待ち中に差し替えても
親子の task 名照合は両方通り、receipt は元の内容を記録する。

**裁定: 採用するが最小形にする。** 親が canonical request の SHA-256 を job script へ埋め込み、
`_job_run` が実際に読んだ bytes の hash と照合し、result へ同 hash を返す。
親は receipt へ結ぶ。**全 task 共通で入れる** — 汎用 task では request 差し替えが
実行コマンドの差し替えそのものになるため、汎用 task を足す wave でこれを開けたままにしない。

`--job-run <任意 path>` の公開 CLI 分岐については、束縛が無い request を拒否する。

## 6. `check_docs.py` の穴 (lensB 所見 4・5)

- **所見 5 は real で、親も再現を要求する。** alias 判定は assignment RHS が直接
  `Name("TASKS")` の場合だけを見るため、`(alias,) = (TASKS,)` の container unpack を通す。
  **採用**: subtree に `TASKS` load を含む alias 束縛・container unpack・function default capture を
  拒否し、負例を足す。
- **所見 4 は部分採用。** drift 検査を `{child_script, env_mode, argv_policy}` まで広げるのは
  **不採用** — 検査が validator の実発火を保証しないという D117 決定 6 の否定文は task 追加後も
  正しく、比較対象を増やしても恒真性は解消しない。**採用するのは「親と `_job_run` の双方へ
  同じ不正 argv を入れる負例テスト」**である。これが実発火を直接に固定する。
- runbook の「2 task だけ」「第 3 task 未実装」という prose は D842/D895 後の状態へ更新する。

## 7. site gate (lensA 所見 8) — 採用

task 由来の local 経路は `current_site(require_evidence=True) == PEGASUS_COMPUTE` だけを許す。
既定呼び出しでは NQSV 証拠を読めない Pegasus login が `OTHER` に落ち、local を許してしまう。
一般の非 Pegasus local 利用は task 外で維持する。

D131 #3 (login での `--runner-mode local` 直起動を機械的に閉じる) は、
`mutation_harness.py` と `mutation_worktree.py` の双方で `PEGASUS_LOGIN` / `PEGASUS_SUSPECT` の
local を rc=2 で拒否して閉じる。`OTHER` と `PEGASUS_COMPUTE` は維持する。

## 8. D131 #4 canonical argv — exact full-suite は採らない

**プランの exact full-suite 固定を不採用**とする。親の実測 (s4-parent-measurements.md §B) では
実在する変異走行はいずれも対象 file を絞った走行であり、exact full-suite を強制すると
**実在する変異 matrix はどれ 1 つとして新経路を通れない**。D433 決定 3 が禁じた
「実データで 1 回も通らない gate」の再演になる。

**採用する argv policy:** tracked な test file 引数は許す。拒否するのは
selector (`-k` / `-m` / `::nodeid`)、`--deselect`、`--ignore*`、任意 `-p`、
`PYTEST_ADDOPTS` / `PYTEST_PLUGINS`、`--force-dispatch`。
親と `_job_run` の双方で同じ validator を通す。

## 9. live dogfood (D433 決定 3 の一般化) — 必須

`mutation` task と `generic` task のそれぞれについて、**親が実データで 1 回通す**。
通らないものを「完成」と記録しない。段 6 で行い、結果を worklog へ書く。

## 10. scope 外 (裁定パッケージへ返す候補)

- fanout の admission schema v2 と D433 の再裁定。
- `env_allowlist` を「最終 child env 全体」の契約へ広げること (tests / provenance の受理集合変更)。
- hook が任意 script 内部まで解析する仕組み。
- 変異 task を経由しない direct harness 全般の legacy node-local lock 廃止。
- qdel の atomic な非 RUN 保証。

## 11. 段 5 の所有分割 (排他)

| 実装子 | 所有 file |
|---|---|
| A | `tools/pegasus/dispatch_compute.py`、`orchestrator/tests/test_pegasus_dispatch_compute.py` |
| B | `tools/mutation_harness.py`、`tools/mutation_worktree.py`、`orchestrator/tests/test_mutation_harness.py`、`orchestrator/tests/test_mutation_worktree.py` |
| C | `tools/check_docs.py`、`hooks/guard_bash.py`、`orchestrator/tests/test_check_docs.py`、`orchestrator/tests/test_hooks.py` |

docs (`docs/pegasus-runbook.md`、`docs/dev-wave/mutation.md`) は親が編集する。

## 12. 変異事前登録 (DW-M01)

実装前に登録する変異の位置と単一理由性。実装後に anchor 逐語を確定する (DW-M07)。

| # | 位置 | 無効化する不変条件 | 単一理由性の確認 |
|---|---|---|---|
| M1 | `_job_run` の env allowlist 拒否 | request の allowlist 外キーを子へ通さない | 前後に同じ入力を拒否する層が無いこと (親射影は別 process、forged request では発火しない) を確認する |
| M2 | `_job_run` の request hash 照合 | queue 越しの request 差し替えを拒否 | job script 側は hash を渡すだけで判定しないことを確認する |
| M3 | argv policy の selector 拒否 (親側) | selector 付き argv を qsub しない | 子側 validator は別変異 M4 で覆う |
| M4 | argv policy の selector 拒否 (子側) | forged request の selector を実行しない | 親側を通さない経路で発火することを確認する |
| M5 | `child_env` の stdin DEVNULL | 子が TTY を掴まない | 他に stdin を閉じる層が無いことを確認する |
| M6 | site gate (`require_evidence=True`) | login/suspect での task 由来 local を拒否 | harness と wrapper で別々に登録する |
| M7 | `check_docs.py` の alias/unpack 拒否 | container unpack で TASKS を書き換える経路を拒否 | 既存の直接 alias 負例とは別の入力で発火することを確認する |

いずれも「無効化したときに赤になる理由が 1 つに絞れる」ことをコードで確認してから登録を確定する。
確認できないものは登録せず実効 gate へ再照準する (F28)。
