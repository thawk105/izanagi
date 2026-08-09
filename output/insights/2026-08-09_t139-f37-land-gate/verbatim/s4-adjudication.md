# 段 4 裁定 + プラン v2 + 変異事前登録

親が各所見を real/refuted・採用/不採用・scope 内/外に裁定する。base `bcda1c02`。

## 0. 総論 — 両レンズの推奨 (B: 止めて immutable trust root を別 scope) を採らない理由

レンズ A・B は独立に「blocker あり、B を選ぶべき」と結論した。**blocker の実在は real と認める。**
しかし両レンズは共通して **「関門が tip 側コードの実行という新しい信頼面を作る」** ことを
前提に B を推している。親が実測でこの前提を反証した。

**実測 (親、独立):** `docs/pegasus-runbook.md:780` の land 手順は
`python3 tools/dev_wave_land.py ...` を**相対 path**で起動する。wave session の cwd は worktree なので、
**親は既に tip 側の `dev_wave_land.py` を実行している。** レンズ A 自身も
「実行する dev_wave_land.py 自体も `__file__` 起点であり、tip 側 helper を実行すれば
関門呼び出しそのものを削除できる」(`s3-lensA.md:17` 相当) と書いており、これは
**関門の有無に関わらず成立する既存の境界**である。`tools/dev_wave_land.py:2-7` も
自らを「悪意ある writer に対する sandbox ではない」と宣言している。

したがって:

- **関門は新しい信頼面を作らない。** tip の任意コード実行は land 時点で既に起きている。
- **関門が閉じるのは「親が rc を読み違える事故」である。** F37 の 3 例はすべて事故であり、
  悪意ではない。裁定文の「親の習慣に依存しない」もこの射程を指す。
- **immutable trust root の不在は関門より大きい既存問題**であり、land helper 全体に及ぶ。
  これは `DW-S04` の「scope 外の real 所見」に該当するので、実装せず**裁定パッケージでユーザーへ返す。**

**結論: 実装する。ただし blocker 3 (lock) と must-fix 群は全部直す。**
両レンズの B 推奨は「本 wave を止める理由」としては refuted、
「別 scope の設計課題」としては real として上げる。

## 1. 所見の裁定

| # | レンズ | 所見 | 判定 | 処置 |
|---|---|---|---|---|
| A1 | A | tip checker は `return 1`→`return 0` の一文字で自己無効化できる | **real / scope 外** | 既存の cooperative 境界と同一。裁定パッケージ (i) |
| A2 | A | tip checker は無 sandbox で、`_verify_target_collisions` より前に ignored 衝突 file を消せる = 受理集合の拡大 | **real / 部分採用** | 拡大は事実。ただし tip helper 自体が既に同じことをできるので**関門による新規拡大ではない**。緩和として監査を lock 前へ出し、**lock 内の既存検査を監査後に必ず通す**順序を保つ。残余は裁定パッケージ (i) |
| A2b | A | leaf symlink 検査では `tools/` 自体が symlink の場合を防げない | **real / 採用** | checker path は全 component を `O_NOFOLLOW` 相当で束縛する |
| A3/B2 | A+B | lock 内 full audit は最悪 queue 900s + walltime 2400s + grace 300s を global lock 内に入れる | **real / blocker / 採用** | **監査を lock 取得の前へ出す。** lock 内は SHA 再照合だけ |
| A4 | A | `subprocess.run` に timeout が無く、hang で lock を保持し続ける。`TimeoutExpired` は `_Reject` のみ捕捉する最上位を素通りする | **real / 採用** | timeout 必須 + `OSError`/`TimeoutExpired`/想定外例外を `RC_PROVENANCE` へ畳む |
| A5 | A | pre-FF 配置は active fold recovery を凍結する (`:2041` の既存テストが保証する挙動) | **real / 採用** | 下記 2 の「recovery 経路の扱い」で解決 |
| A6/B4 | A+B | fixture stub 案では既存 64 テストが関門削除を検出しない。plan のテスト 2 は「lock 内監査」を正例として凍結してしまう | **real / 採用** | 変異事前登録で削除変異を kill。テスト 2 は「監査中は lock が**取得可能**」へ反転 |
| A7/B6 | A+B | 親 brief の「既存 2 本と同型」「pipefail hit ゼロ」は誤り | **real / 採用 (親の誤り)** | 下記 4 で撤回・訂正 |
| A8/B7 | A+B | W2 は文言追加だけでは儀式化しうる | **nit / 部分採用** | W2 を「F37 の防壁」に数えない。brief への必須欄化は `DW-S01` の予算内に収まらないため**提案せず**、裁定パッケージ (ii) |
| B1 | B | land 経路外 (直接 commit、hook 外、supervisor の rc 無視) を覆えない | **real / scope 外** | 保証範囲を明記して裁定パッケージ (i) |
| B3 | B | 関門を `already-landed` 分岐より前に置くと `already-landed` が `rejected` へ変わる。fold commit は監査対象外 | **real / 採用** | 下記 2 で解決 |
| B5 | B | 順序制約は停止依存であり、tip checker は自己免除の穴でもある | **real / 一部 scope 外** | 順序は明示的な停止条件にする。自己免除は裁定パッケージ (i) |

## 2. プラン v2 (段 5 の実装契約)

### (a) 監査の位置 — lock の**外**

`land()` の冒頭、`_verify_repository(request)` の直後・`_open_lock()` の**前**で
`_audit_provenance_history(repository)` を実行し、**receipt** を得る。

receipt は次を束縛する。

- `tip_sha` — 監査を開始する直前に wave repo で解決した `HEAD` の 40 桁 SHA
- `checker_blob_sha` — 監査に使った `tools/check_ai_provenance.py` の blob SHA
  (`git rev-parse HEAD:tools/check_ai_provenance.py` を wave repo で解決)
- `returncode` — 子の rc

**正しさの根拠**: 監査対象は commit SHA で固定される。同じ commit SHA は同じ tree を表すので、
lock 内で `tip_sha == tested_tip` かつ `checker_blob_sha` が `tested_tip` の同 path の blob と
一致すれば、**監査した木と land する木が同一である**と言える。

### (b) lock 内の再照合

`_verify_heads()` (`:1722`) の直後、`if active_plan is not None:` (`:1735`) の直前で
`_verify_provenance_receipt(repository, receipt, tested_tip)` を呼ぶ。ここは既存の
cheap reject をすべて通過した後であり、**すべての main mutation と fold apply より前**である。

照合内容:

1. `receipt.tip_sha == tested_tip`
2. `receipt.checker_blob_sha` == wave repo で `tested_tip:tools/check_ai_provenance.py` の blob SHA
3. `receipt.returncode == 0`

いずれか不成立なら `_Reject(RC_PROVENANCE, ...)`。**git 操作だけなので lock 保持時間は既存並み。**

### (c) active fold recovery 経路の扱い (A5 / B3 の解決)

`active_plan is not None` の recovery 経路は、**関門の対象外**とする。

**escape hatch ではない理由 (署名で書く):** recovery 経路へ入る前提は
`locked_main == tested_tip` である (`:1736` が不成立なら `RC_FOLD_RECOVERY_FAILED` で拒否)。
すなわち **commit は既に main に入っており、recovery は新しい commit を 1 つも admit しない。**
関門の目的は「新規 admit の阻止」なので、admit をしない経路を止める理由がない。逆に止めると
台帳が before/after 混在で固着する (`:2041` の既存テストが保証する recovery が壊れる)。

**通る正例 (DW-S04 の要求):** active fold transaction があり main が既に tip に到達している
request は、provenance が赤でも `landed` / fold 完了へ進む。**新規 admit を伴う経路
(`active_plan is None` かつ `locked_main != tested_tip`) では、赤なら必ず `RC_PROVENANCE`。**

これにより `already-landed` の idempotency も保たれる (B3)。

### (d) 実行体と argv

- checker = wave 側 `tools/check_ai_provenance.py`。**理由は自己弱体化の受容ではなく、
  main 側では機能しないから** — checker は repo root を cwd でなく
  `Path(__file__).resolve().parent.parent` から決める (`check_ai_provenance.py:29-31`) ため、
  main 側実行体は **ff-only 前に main の履歴しか監査せず tip を一切見ない**。
  加えて `_known_violation_registry()` は実行体のソース内定数を読む (`:148`, `:1070`) ので、
  main 側は登録 wave を恒久 deadlock させる。
- path 束縛: 全 component を `O_NOFOLLOW` 相当で開き、symlink を拒否する (A2b)。
- argv は厳密に `[sys.executable, str(checker)]`。`--range` も `--message-file` も渡さない
  (`DW-O17` の「full 監査だけが権威」)。
- `cwd=repository.wave`、`env=_git_env()` + `PYTHONDONTWRITEBYTECODE=1`、
  `stdin=DEVNULL`、`stdout=PIPE`、`stderr=PIPE`、`check=False`、`shell=False`、`close_fds=True`。
- **`timeout=` を必ず付ける** (A4)。値は dispatch 既定 (queue 900 + walltime 2400 + grace 300) を
  包含する 3900 秒とし、超過は `RC_PROVENANCE`。lock 外なので他 wave を止めない。
- `OSError` / `subprocess.TimeoutExpired` / 想定外例外はすべて `_Reject(RC_PROVENANCE, ...)` へ畳む。

### (e) rc

`RC_PROVENANCE = 29` を新設 (P4 採用、両レンズとも妥当と判定)。`RC_AUDIT = 23` は再利用しない。

### (f) テスト方針

- 合成 repo fixture (`test_dev_wave_land.py:119-123`) へ tracked な checker stub を追加する。
  `_audit_provenance_history` / `_verify_provenance_receipt` は **monkeypatch しない**
  (すると関門削除の変異まで緑になる)。
- **plan のテスト 2 を反転する**: 「監査中に global lock が**取得可能**である」ことを固定する
  (= 監査が lock の外にある)。lock 内監査へ戻す変異が赤になる。
- checker 削除 / symlink の負例は **clean な commit tip** として作る
  (未 commit だと `:1708` の `RC_DIRT` が先に出て関門を検査しない — A6)。
- 既存 64 テストの期待値は 1 つも変更しない。

## 3. 変異事前登録 (`DW-M01`)

各変異は「同じ入力を拒否する層が前後に無い」「無効化時の赤理由が一つに絞れる」ことを
実装後にコードで確認してから本走する (`DW-M07`)。

| ID | 変異 | 期待 kill |
|---|---|---|
| M1 | `land()` から `_verify_provenance_receipt(...)` 呼び出しを削除 | 赤で拒否する負例テスト |
| M2 | `receipt.returncode == 0` を `receipt.returncode in (0, 1)` へ緩める | 同上 |
| M3 | checker を wave 側から main 側 (`repository.main`) へ変更 | tip-only 違反を見逃す負例 |
| M4 | lock 内の `receipt.tip_sha == tested_tip` 照合を削除 | 監査後に tip が動く負例 |
| M5 | `checker_blob_sha` 照合を削除 | 監査後に checker が差し替わる負例 |
| M6 | `timeout=` 引数を削除 | timeout 負例 |
| M7 | `shell=False` を `shell=True` + 文字列 command へ変更 | subprocess 契約テスト |
| M8 | recovery 例外条件を反転 (`active_plan is None` のときだけ関門) | 新規 admit の負例が通ってしまう |
| M9 | 監査を lock の内側へ戻す | 「監査中に lock 取得可能」テスト |

**正例 (受理集合を縮小する wave なので `DW-M01` が要求)**: (i) provenance 緑の通常 land が
`landed` を返す、(ii) active fold recovery が provenance 赤でも完了する。

## 4. 親自身の誤りの訂正 (A7 / B6、両レンズが独立に指摘)

`parent-brief-v2.md` の次の 2 つを**撤回する**。

1. **「`pipefail`・「パイプ」で hit ゼロ、純増検出力 100%」は誤り。**
   親は `tools/*.py` しか検索しておらず `tools/**/*.sh` を落としていた。実際には
   `tools/strip_claude_session_trailers.sh:39`、`tools/pegasus/*.sh` 多数に `set -euo pipefail` がある。
   **訂正後の主張**: これらは各 script 内部の fail-fast であり、
   「親が対話 Bash で検査 rc をパイプへ流す」F37 の vector は覆わない。
   純増検出力は「land 経路における全史 provenance 赤の阻止」に限定する。
2. **「既存 2 本 (`_validate_generated_docs` / `_preflight_fold_message`) と同型だから足せる」は誤り。**
   共通なのは `subprocess.run` + `returncode` を直読みする構文だけである。既存 2 本は
   短時間・login 完結・手元入力の検査で、`_fold_main_locked()` の広い例外捕捉と rollback の
   内側にある (`:1533`)。`--message-file` 経路は checker の site/dispatch gate を通らない
   (`check_ai_provenance.py:1935`)。全史監査だけが admission・bounded scope・dispatch・queue を通る。
   **訂正後の主張**: 構文の先例があるだけで、latency・例外・transaction 境界は別物として設計する。

**38.3 秒**は `time` で実測した値だが `prov-baseline.txt` には含まれない (A3 の指摘は正しい)。
かつ **上限ではない** ので、lock 予算の根拠に使わない。lock 外設計により上限依存を解消した。

## 5. ユーザーへ返す裁定パッケージ (scope 外、実装しない)

- **(i) immutable trust root。** land helper・checker・known-violation registry のいずれも
  tip 側にあり、land 対象の wave が自分を裁く実行体を変更できる。本関門はこれを悪化させないが
  解消もしない。**両レンズが独立に最優先課題として挙げた。** 別 scope・別裁定で設計するか、
  「協調境界として受容する」と明文化するかの択一。
- **(ii) 前提実測の記録欄。** W2 の文言追加は儀式化しうる。brief に
  「検索した性質 / 対象範囲 / hit / 既存被覆で足りない理由」の必須欄を置く案があるが、
  `DW-S01` の byte 予算に収まらない。予算を上げる変更は自己改善の範囲外
  (`skill-self-improvement.md:51`) なので裁定へ返す。

## 6. 順序 (停止条件、B5)

並行 wave (`worktree-dev-wave-t682-provenance-known-violations`) の known-violation 登録が
local main へ land するまで、本 wave は段 9 へ進まない。段 9 直前に親が**単独 rc**で
`python3 tools/check_ai_provenance.py` の緑を実測し、緑でなければ `DW-STOP` に従って停止する。
逃がし道は作らない。
