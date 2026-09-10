# 段 4 裁定 — [T-1974] 段階 P

親が両レンズの所見を real / refuted、採用 / 不採用、scope 内 / 外へ裁定し、プラン v2 を確定する。
実測はすべて親が本 wave 中に行った。

## 0. 前提の訂正 (brief の誤りを親が自分で正す)

- 引数の `tools/dispatch_compute.py` は実在しない。実体は `tools/pegasus/dispatch_compute.py`。
- 引数の「裁定は未 land」は誤り。**D1151 は main の `docs/decisions.md` に着地済み**である。
- 引数の「4 file を触る稼働 wave は 0 本」は、編集面を確定した後の再実測では
  `docs/pegasus-runbook.md` に 1 本 (`dev-wave-t1647-a2-cert-fanout`、mtime 2026-08-27 10:33) が居る。
  `.codex/worktrees/` の 2 本 (t1447 / t1719-fix8) は mtime 08-24 / 08-26 の子の残骸。

## 1. 所見の裁定

### A-1 / B-1 (両レンズ独立、停止級) — real・採用

**申告 channel が被検査コードから書ける。** manifest の path を環境変数で運ぶと、実行器の子孫
(login collect-only 子、bounded local の pytest、compute の pytest) がすべて manifest を読み、
nonce・digest・K を得て `0..K-1` の正規申告を偽造できる。同一 uid なので mode 0700 は隔離にならない。

**裁定: プランの file 経路を却下し、launcher 所有の継承 write-fd へ置き換える。**

- launcher が `os.pipe()` を作り、`_run_blob` の `subprocess.run` へ `pass_fds=(write_fd,)` を渡す。
  fd 番号だけを環境変数 `IZANAGI_ACCEPTANCE_RUNNER_BINDING_FD` に置く。
- `subprocess` の既定 `close_fds=True` により、**実行器の子孫は fd を継承しない**。
  環境変数に fd 番号が見えても、その番号は子孫の process では別のもの (または閉じている) である。
- login 側の dispatcher は実行器と**同一 process** (`tools/run_tests.py:1319` の
  `from tools.pegasus import dispatch_compute`) なので、`os.write` で申告を書ける。
- 待ち手が既に `pass_fds=(outcome_write, completion_read)` で同じ idiom を使っている
  (`tools/dev_wave_wait.py:865`)。新しい機構ではない。
- 残余は「tip 側 dispatcher が嘘を書ける」ことだけになる。これは A-7 が指摘するとおり
  **dispatcher だけを編集した wave も偽造できる**という残余であり、段階 R が閉じる。

### A-2 (停止級) — real・採用 (ただし設計 (iv) は変えない)

**非 dispatch の authoritative 受入が落ちる。** 親が実測して確定した blast radius は次のとおり。

- 待ち手は Pegasus LOGIN かつ queue が `ENA=ENA` / `STS=ACT` のときだけ
  `IZANAGI_ACCEPTANCE_SHARDS=3` を注入する (`tools/dev_wave_wait.py:821-845`)。
- 注入されないとき、実行器は `explicit_shard_mode=False` で login admission へ入り、
  **memory headroom があれば suite をログインノードで local 実行する**
  (`tools/run_tests.py:2495-2545` の `admission_outcome is None` → `_launch_local_scope`)。
  この経路は今日 rc 0/1 を返し、v5 受領証が出る。
- P 着地後、この経路は申告 0 件で fail-closed になる。**すなわち「queue 停止 + login に余裕あり」の
  組合せで、今日通る受入が通らなくなる。**

**裁定: 設計 (iv) は確定済みユーザー裁定 (D1151 の下の 6 点) であり、親は不採用にしない。**
逃がし道 (flag・環境変数・「manifest 無しなら要求しない」) を作らない。
その代わり blast radius を worklog・decisions・`docs/pegasus-runbook.md` へ明記し、
最終報告でユーザーへ名指しで伝える。段階 R (T-1976) が bounded local を main blob 実行へ移して閉じる。

### B-3 (must-fix) — real・採用

**未設定時に K="2" を明示注入すると `explicit_shard_mode` になり、login admission と queue 可用性の
判定を飛ばす。** 到達する経路である。

**裁定: launcher は環境変数を一切注入しない。** K は launcher が自分の環境にある explicit 値
(`"1"` / `"2"` / `"3"`) からだけ確定する。未設定・空文字は **runner 起動前に fail-closed** とする
(A-2 の帰結と同じ集合であり、新たに塞ぐ経路を増やさない)。
これにより `explicit_shard_mode` の意味論も admission 経路も 1 bit も変わらない。

### B-2 (must-fix) — real・採用

**申告検査を outcome より前に置くと queue timeout の再試行分類が消える。**

**裁定: 申告検査は outcome 書き込みの後、受領証生成の前に置く。** 順序は
`config 検査 → main/tip 等値 → 実行 → 実行後 main blob 再照合 → outcome 書き込み →
申告検査 → completion 検査 → 受領証`。受領証を書く前に落ちれば land は成立しないので執行力は保たれる。

### A-5 (must-fix) — real・採用

**発火条件の 3 述語のうち 2 つが恒真。** `task == "tests"` なら `argv_policy == "passthrough"` と
`child_script == ("tools","run_tests.py")` は固定表から必ず成立する。

**裁定: 発火条件は `task == "tests" かつ manifest が完全` の 2 項だけにする。**
残り 2 項は `assert` として残してよいが、gate 述語として数えず変異 matrix にも登録しない。
単一理由性の無い fixture (A-5 が列挙した 5 本) は、単一理由になるよう入力を作り直す。

### B-10 / A-6 (must-fix) — real・採用 (設計を変更する)

**request payload へ runner の base64 source を載せる案は却下する。** `tools/run_tests.py` は
96,988 bytes、base64 で 129,320 bytes、K=3 なら 387,960 bytes になる。上限値も境界試験も未定である。

**裁定: source bytes を運ばない。manifest が運ぶのは `tested_main` の revision と nonce と K だけ。**
計算ノード側は `git -C <repo> cat-file blob <tested_main>:tools/run_tests.py` を **1 回**読んで
単一 buffer を作り、その buffer を hash し、同じ buffer を子の stdin へ渡す (同一 buffer 束縛 (ii))。
申告する digest はその buffer の hash であり、manifest の期待値を転記しない。
launcher は自分が読んだ main blob の digest と照合する。payload の size 問題は消える。

### A-4 (must-fix) — real・**scope 外**

**`result.json` の先行作成・後追い再置換。** 現行は `O_EXCL` なので先行作成は
「妨害 (fail-closed)」であって偽造ではない。プランの atomic replace 化はむしろ新しい risk を作る。

**裁定: `result.json` の書き込み意味論を変えない。** 申告は既存の result payload の中へ
optional field として載せる。残存 descendant による後追い上書きは D859 が別枠で追う既存の残余であり、
本 wave の scope 外として記録する。

### B-8 (must-fix) — real・採用 (scope 拡大)

**`orchestrator/tests/test_dev_wave_wait.py` の実 Git E2E 4 本が新契約で赤になる。**
(`test_default_wiring_with_real_git_and_lease_helper` ほか、`:8884` / `:9190` / `:9306` / `:9384`)

**裁定: scope に入れる。** これらは「非 dispatch の synthetic runner で v5 受領証が出る」という
**旧契約**を pin しており、その契約は (iv) で変わる。期待を単に失敗へ倒すのではなく、
**synthetic runner に fd へ正規申告を書かせて緑を保つ**。これで同テストが新 channel の
positive control も兼ねる。テストを甘くする変更ではない。

### B-9 (must-fix) — real・採用

**`docs/pegasus-runbook.md:929-947` の「dispatch の内側の子は pathname を読み直すため束縛外」が
P 着地後は半分偽になる。** `check_docs.py` の parser は検出しない。

**裁定: runbook を親が更新する。** 稼働 wave `dev-wave-t1647-a2-cert-fanout` も同 file を触るので、
編集は当該 2 段落に限定し、land 時の merge は親が解決する。

### A-7 / B-11 (must-fix) — real・採用 (主張を弱める)

**「24 件中 6 件」から「申告は必須」も「残余は両 file 同時編集の wave だけ」も導けない。**
main blob の実行器は tip 側の dispatcher を import するので、**dispatcher だけを編集した wave も
qsub を省いて正規申告を書ける**。

**裁定: 記録では次の 3 点だけを主張する。**
1. P は「実行器だけを編集した wave」を捕まえる。
2. **dispatcher を編集した wave は P では捕まらない。** 閉じるのは段階 R。
3. 「dispatcher 導入以降、実行器を触った 24 commit のうち 6 件が同じ commit で dispatcher も
   触っている」は観測事実として書き、必要性・確率の根拠としては使わない。

### B-4 (must-fix) — real・採用

**brief の (P4)「shard 子だけ」と K=1 の非 shard binding が不整合。**

**裁定: (P4) を訂正する。** 対象は `task == "tests"` の dispatch 子**すべて**であり、
K=1 の単一 dispatch も含む。K=1 のとき `intent_shard_index is None` を index 0 へ正規化する。

### B-5 (must-fix) — real・採用 (残余の明記)

**束縛されるのは compute の直近 runner 一層だけ。** login の tip dispatcher import、job script、
login collect-only pytest、bounded local の pathname runner、compute pytest controller、
xdist worker、grandchild は束縛外。

**裁定: 台帳では「受入全層を main へ束縛した」と書かない。**
「計算ノードで dispatch された `tests` 子の実行 bytes だけを束縛した」と書き、束縛外の層を列挙する。

### A-3 (must-fix) — real・採用

**P 自身の受入が通ることの全鎖証明が不足。** 親が段 6 で実測する。
`tested_main` に launcher が実在すること (現 main の launcher blob が存在) は親が確認済み。
stale な manifest 環境変数は、新 launcher だけが設定するので P の受入では存在しない。
**新 dispatcher は manifest 環境が無ければ現行 pathname 起動を維持する**ことをテストで pin する。

### A-6 前半 (must-fix) — real・採用

**「受理集合は一切変えない」は誤り。** P は受理集合を**狭める**。狭まるのは
(1) 申告の無い authoritative 受入、(2) `IZANAGI_ACCEPTANCE_SHARDS` 未設定・空の authoritative 受入、
(3) 不正な manifest 環境。記録にそのまま書く。

### B-6 (must-fix) — real・採用

**提案テストが実 seam を一度も通らない。** 前 wave が実測した検出力不足と同型。

**裁定: 実 Git を通す E2E を最低 2 本置く。** (1) main と tip で `tools/run_tests.py` の bytes が
異なる実 repo を作り、compute 側 helper が **main の bytes だけ**を実行したことを外部観測する。
(2) B-8 で改訂する `test_dev_wave_wait.py` の実 Git E2E を新 channel の positive control にする。

### B-7 (must-fix) — real・採用

**index authority のテストは intent と argv を食い違わせる。** `intent=1` / argv index `0` の
不一致入力を使い、argv から index を読む変異を殺す。

### B-12 (nit) — refuted されず、現状影響なし

`tools/acceptance_shards.py` は編集しない。A-1 の対案 (fd channel) も同 file を触らない。

## 2. プラン v2 (確定)

### 編集面 (これ以外を触らない)

| file | 担当 | 内容 |
|---|---|---|
| `tools/acceptance_launcher.py` | Codex 実装子 | K 所有・nonce 生成・fd channel・申告執行 |
| `tools/pegasus/dispatch_compute.py` | Codex 実装子 | manifest 消費・request field・compute 側 main blob 実行・申告 |
| `orchestrator/tests/test_acceptance_launcher.py` | Codex 実装子 | 執行側の正例・負例 |
| `orchestrator/tests/test_pegasus_dispatch_compute.py` | Codex 実装子 | 機構側の正例・負例 |
| `orchestrator/tests/test_dev_wave_wait.py` | Codex 実装子 | 既存実 Git E2E 4 本を新 channel の正例へ更新 |
| `docs/pegasus-runbook.md` | 親 | 残余記述の是正 (2 段落) |

**触らない:** `tools/run_tests.py`、`tools/dev_wave_land.py`、`tools/dev_wave_wait.py`、
`tools/acceptance_shards.py`、受領証 schema。

### 執行 (launcher、main 束縛。P 着地後に発効)

1. `_resolve_binding_shard_count(environ)`: `IZANAGI_ACCEPTANCE_SHARDS` が `"1"`/`"2"`/`"3"` なら
   その値を K とする。未設定・空・その他は `LauncherFailure` で runner 起動前に停止する。
2. `os.pipe()` で申告 channel を作り、`nonce = secrets.token_hex(32)` を生成する。
3. `_run_blob` へ `environment` (= `dict(os.environ)` + `..._FD` + `..._NONCE` + `..._TESTED_MAIN`)
   と `pass_fds=(write_fd,)` を渡す。**`IZANAGI_ACCEPTANCE_SHARDS` は書き換えない。**
4. 子の終了後に write 端を閉じ、read 端から申告を読む。
5. 既存の実行後 main blob 再照合 → outcome 書き込み → **申告執行** → completion → 受領証。
6. 申告執行は次を全部要求する。件数が exact K、index の multiset が exact `0..K-1`、
   全 nonce が一致、全 `tested_main` が一致、全 digest が launcher の main blob digest と一致。

### 機構 (dispatcher、tip 側。manifest がある走行にだけ適用)

1. login 側 `_dispatch_impl` の入口で、`os.environ` から fd・nonce・tested_main の 3 key を読む。
   3 つとも無ければ**現行動作** (P 自身の受入がここを通る)。一部だけあれば fail-closed。
2. `task == "tests"` かつ manifest 完全のときだけ、request に `runner_binding`
   (`tested_main` / `nonce` / `shard_count` / `shard_index`) を足す。source bytes は載せない。
3. 計算ノード側: `runner_binding` があれば `git cat-file blob <tested_main>:tools/run_tests.py` を
   1 回読んで `source` を作り、同じ helper 内の隣接文で `sha256(source)` と
   `subprocess.run([python, -I, -c, BOOTSTRAP, <canonical path>, *argv], input=source)` を行う。
   期待 digest を読み込まない。無ければ現行 pathname 起動。
4. 計算ノード側の申告は既存 result payload へ optional field として載せる
   (`result.json` の書き込み意味論は変えない)。
5. login 側は result を検証したあと、fd へ 1 行 1 申告の canonical JSON を書く。

## 3. 変異の事前登録 (DW-M01 / B-057)

全変異は **KILLED 期待**。baseline 緑を先に確認する。単一理由性を各行に書く。

| # | 位置 | 変異 | 単一理由 | 期待 KILLED node |
|---|---|---|---|---|
| M1 | launcher 申告執行 | 件数 exact K の要求を落とす | index multiset 検査は別変異。件数だけを落とすため K-1 件の入力は index も欠けるので、fixture は「index 0..K-1 が揃い、さらに index 0 が 2 件」= 件数だけ違反する形にする | `test_binding_reports_reject_extra_count` |
| M2 | launcher 申告執行 | digest 照合を恒真化 | 件数・index・nonce が正しく digest だけ 1 桁違う入力 | `test_binding_report_digest_mismatch_is_rejected` |
| M3 | launcher 申告執行 | nonce 照合を落とす | digest・件数・index が正しく nonce だけ違う入力 | `test_binding_report_nonce_mismatch_is_rejected` |
| M4 | launcher 申告執行 | index multiset を `set` 比較へ緩める | 件数 K で `[0,0,2]`。件数検査は通る | `test_binding_reports_require_exact_index_multiset[dup]` |
| M5 | launcher 申告執行 | 申告検査を受領証書き込みの後へ移す | 申告不備の走行で受領証が出るかどうかだけが変わる | `test_binding_enforcement_precedes_receipt` |
| M6 | launcher K 所有 | K を申告の自己申告値から取る | env が `"3"` で申告が 2 件かつ自称 `shard_count=2` の入力 | `test_launcher_owns_k_from_environment_not_reports` |
| M7 | launcher K 所有 | 未設定・空の fail-closed を落とす | env 未設定で runner が起動されるかどうかだけが変わる | `test_unset_shard_env_fails_closed_before_runner` |
| M8 | dispatcher compute 側 | main blob 実行を pathname 実行へ戻す | main と tip の bytes が異なる実 repo で、実行された bytes だけが変わる | `test_bound_child_executes_main_blob_not_worktree` |
| M9 | dispatcher compute 側 | 申告の digest を manifest 期待値の転記にする | source buffer と期待値が食い違う入力でのみ差が出る | `test_bound_child_reports_digest_of_executed_buffer` |
| M10 | dispatcher login 側 | manifest があっても binding を付けない | manifest 有りの走行で申告が出るかどうかだけが変わる | `test_manifest_present_adds_runner_binding_to_request` |
| M11 | dispatcher login 側 | manifest 一部欠落の fail-closed を落とす | 3 key のうち 1 つだけ設定した入力 | `test_partial_manifest_environment_fails_closed` |
| M12 | dispatcher login 側 | `task == "tests"` の限定を落とす | provenance / mutation task に manifest がある入力 | `test_binding_applies_only_to_tests_task` |

**正例 (過剰拒否の検出、DW-M01 の受理集合縮小 wave の義務):**

| # | 内容 | 期待 |
|---|---|---|
| P1 | K=3、申告 3 件、index `0,1,2`、nonce 一致、digest 一致 | 受領証が生成される。無変異で緑 |
| P2 | manifest 環境が 1 つも無い通常 dispatch (P 自身の受入と同形) | 現行 pathname 起動のまま緑、受領証が出る |

**gate の禁止 (署名で書く):**

- `_enforce_binding_reports(reports, expected_k, expected_nonce, expected_main, expected_digest)` は、
  `len(reports) != expected_k`、`sorted(r.shard_index for r in reports) != list(range(expected_k))`、
  `any(r.nonce != expected_nonce)`、`any(r.tested_main != expected_main)`、
  `any(r.runner_executed_sha256 != expected_digest)` のいずれかで `LauncherFailure` を送出する。
- **通る正例:** `reports = [R(0,n,m,d), R(1,n,m,d), R(2,n,m,d)]`、`expected_k=3`、
  `expected_nonce=n`、`expected_main=m`、`expected_digest=d` → 例外を送出せず戻る。

## 4. 段 5 の分割

編集面が launcher と dispatcher で相互依存 (manifest の生産者と消費者) のため、**1 単位で投入する**。
`orchestrator/tests/test_dev_wave_wait.py` の改訂も同じ単位に含める (新 channel の正例になるため)。
`docs/pegasus-runbook.md` は親が別に編集する。
