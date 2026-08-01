# 段 2 プラン — parallel-dev (S1〜S4)

起草 = Claude `opus`、sandbox 相当 read-only、`DW-S02`/`DW-O05` に従いテスト実測なし。
行番号は HEAD `5544794` 時点。**採否は段 4 で親が裁定する。**

> 注 (規律 6): 本プランの出力は harness の instruction-shaped パターン検査 (settings-json) に
> 一致した。実体は `[pytest]` ini ブロックであり、指示文ではなく設定データである。
> 指示として解釈せず、データとして扱った。

---

## S1 — `tools/dev_wave_land.py`: handoff の内容検証を外し保護を広げる

### consumer 全数監査 (grep 実施済み) — (P1) の実装上の裏付け

`control.handoffs` の consumer は **ちょうど 2 箇所**。

1. `_verify_main_clean:777` — untracked の受理判定
2. `_verify_target_collisions:909` — `protected` の構成要素

`_validate_handoff_at` の戻り値は `(_identity, sha256)` のみで、**解析した目的・状態・基準コミット・
見出しは 587-590 で捨てられている**。`identities` は `_ControlSnapshot` の等値比較経由で
767 (status 前後) と 1343 (main 変更直前) の mid-flight 検知にだけ使われる。
**schema 検証の結果を読む消費者はゼロ** → (P1)「内容は ff-only merge の安全性に因果を持たない」は
実装上も真。外部呼出しもゼロ (定義 538 と使用 619 のみ)。

### 変更前の拒否集合 (brief の想定より広い)

`_handoff_snapshot` 615-620 が `README.md` 以外の**全エントリ**を検証するため、schema 不備だけでなく
**`.md` 以外の stray (`.swp` / `NOTES.txt` / `.DS_Store`)、サブディレクトリ、非 ASCII 名
(`2026-08-01_引き継ぎ.md`)、symlink、FIFO も全部 land 全体を落とす**。
加えて `_verify_main_clean` 776-782 がネストした untracked (`docs/handoff/sub/a.md`) を落とす。

### 編集箇所

1. **538-590 `_validate_handoff_at` → `_handoff_identity_at` へ置換**。
   `os.stat(..., follow_symlinks=False)` を先に取り、regular かつ `_MAX_HANDOFF_BYTES` 以内のときだけ
   `_read_regular_at` で読んで `(_identity, sha256)` を返す。非 regular は `(_identity, b"")`。
   symlink は `os.readlink` の bytes を第 2 要素へ入れると mid-flight 検知が強まる (推奨)。
   541-546 の name-shape 拒否と 555-586 の schema 検証を全削除。読取失敗は `_Reject` にせず
   `(_identity, b"<unreadable>")` へ倒す (保護は identity 側で成立する)。
2. **45 `_HANDOFF_STATES` を削除** (他 consumer なし)。`_SHA_RE` (39) は 418/428 で使うので残す。
   `_MAX_HANDOFF_BYTES` (38) は読取上限として残す。
3. **619**: 呼び先を差し替える。**616 の `README.md` skip は必ず維持** (tracked で正当な land target)。
4. **776-782 `_verify_main_clean`**: 「`after.handoffs` に無ければ `RC_CONTROL_PLANE`」を削除し、
   `if relative.startswith(b"docs/handoff/") and relative in after.handoffs: continue` にする。
   **非メンバは 783 以降の通常 untracked 経路へ落とす** (= land 対象と衝突するときだけ `RC_DIRT`)。
5. **909-911 `protected` は無改造**。`control.handoffs` が自動的に広がる。

### 変更後 — 拒否は狭まり、保護は広がる

- 拒否 (狭まる): handoff の内容・名前・型を理由に land が落ちなくなる。残るのは
  「target が `docs/handoff/` の既存直下エントリと衝突」「mid-flight で identity/hash が変わった」だけ
- 保護 (広がる): `README.md` を除く全直下エントリ
- 不変: ff-only / lock / stale / audited closure / postcondition / mid-flight identity+hash

### 境界テスト (`orchestrator/tests/test_dev_wave_land.py`、既存 36 test)

既存被覆: 280-288 = 状態 3 値と古い日付の受理、344-361 = malformed/symlink/fifo の**拒否**、
461-484 = schema-valid handoff への target 衝突拒否、1088-1112/1114- = inode 差し替えの mid-flight 検知。
以下は**純増の検出力**だけを書く。

- **344-361 を反転改修** (`..._do_not_block_land`): 6 kind (malformed / symlink / fifo /
  stray `NOTES.txt` / サブディレクトリ / 非 ASCII 名) で `rc==0 landed` かつ foreign 成果物不変。
  → 型・名前・schema のどれかを拒否として再導入した回帰を赤にする
- **[純増] `test_foreign_handoff_of_any_shape_is_protected_from_target_collision`**: 同 6 kind で
  wave が `docs/handoff/<その名前>` を commit → `RC_CONTROL_PLANE` かつ foreign 不変。
  → 「拒否をやめたついでに保護も落ちた」を赤にする (461-484 は schema-valid 1 形しか見ておらず現在の検出力はゼロ)
- **[純増] `test_handoff_readme_remains_a_landable_target`**: wave が `docs/handoff/README.md` を
  変更して land → `landed`。→ README を除外し忘れた過剰拒否を赤にする
- **[純増] `test_nested_untracked_under_handoff_is_untracked_not_control_plane`**:
  `docs/handoff/sub/a.md` で (a) 無関係 target なら `landed`、(b) target = 同パスなら `RC_DIRT`。
  → 776-782 の書き換えが衝突検知まで消した場合を赤にする
- **[純増] `test_content_only_handoff_mutation_around_status_is_rejected`**: 同一 inode・bytes 変更で
  `RC_CONTROL_PLANE`。→ **hash を `identities` から落とす**リファクタを赤にする
  (既存 1088/1114 は inode 差し替えのみで、hash 削除では赤にならない = 現在の検出力ゼロ)

---

## S2 — `tools/check_docs.py`: 48h stale 検査を他人の commit から外す

### 変更前

2167-2188。(a) `状態:` 行なし → finding、(b) `作業中|計測中` かつ mtime > `HANDOFF_STALE_SECONDS`
(79 = 48h) → finding。findings があれば 2190-2194 で rc=1。**所有者判定なし。**
consumer (`tools/task_run_check.py:16`、`tools/dev_waves/checker.py:349-358`/`590-592`、
`daemon.py:231-236`) は **いずれも rc しか見ない** → rc=0 化は下流互換。
`REPO` は `__file__` 由来 (24) なので **worktree で走らせると自分の checkout の handoff しか見えない** —
被害は main checkout 共有セッションに限定される。

### 案 A — findings と warnings の 2 層化

(b) だけを `warnings` へ移し stdout に出す。rc には算入しない。(a) は finding のまま。
受理集合は広がる。検出は毎回可視で、CLAUDE.md 起動導線が「handoff を全部読む」を既に義務づけている。
弱点 = 強制力ゼロ。

### 案 B — 検出を起動側ゲートへ移設

2185-2188 を削除し、`tools/check_wave_startup.py` に `_check_stale_handoff` を新設する。
`check_docs` は広がり、`check_wave_startup` は狭まる。
**止まる相手が正しくなる** — 新しい wave を始めるセッションであり、無関係な commit ではない。
弱点 = wave 起動時にしか走らない。

### 案 C — handoff に所有者欄を足して所有者限定で赤にする

最も精密だが、正本 (`docs/handoff/README.md`) と既存 4 本の移行が要り、変更単位が S1/S2 を跨ぐ。
所有者文字列は自己申告なので偽装耐性なし。**scope 超過 → 裁定へ。**

**プランの推奨 = A+B 併用** (検出は常時可視、強制は起動点に一本化)。

### 境界テスト (`orchestrator/tests/test_check_docs.py`)

既存被覆: **ゼロ** (`handoff|48h|稼働中|HANDOFF_STALE` は test 側ヒットなし)。全て純増。
既存の `_build_min_repo` が `check_docs.py` を tmp へ複製し `REPO` を付け替える仕組みを使い、
`os.utime` で mtime を偽装する。

- **[純増] `test_stale_active_handoff_does_not_make_check_docs_red`**: 作業中・49h → rc==0、
  ただし stdout に警告。→ finding 復帰を赤にする
- **[純増・正例] `test_stale_handoff_warning_is_actually_emitted`**: 47h なら警告が**出ない**。
  → 恒真に出続ける / 常に出ない死んだ実装を赤にする (規律 3)
- **[純増] `test_handoff_without_status_header_is_still_a_finding`**: `状態:` 行なし → rc==1。
  → (a) を巻き添えで消した過剰緩和を赤にする
- **[純増・案 B 採用時] `test_check_wave_startup_rejects_stale_active_handoff`**。
  → 移設先で判定が蒸発したのを赤にする

### 波及

`tools/codex_reasoning_ab.py:99-100` が `check_docs.py` / `test_check_docs.py` の sha256 を pin するが、
**現ファイルの実 sha256 は既に不一致** (履歴 snapshot 再現用で作業ツリーを読まない) → S2 は pin を壊さない。

---

## S3 — pytest 設定の新設

### (P3) の確認結果 — 破壊経路が 1 点ある (最優先)

**`addopts` を ini に書くと `run_tests.py` の 4 ゲートが静かに盲目になる。**
`_is_full_suite` (314)、`_is_acceptance_run` (403)、`_has_no_execution_flag` (375)、
`_has_dispatch_exempt_flag` (390) は **すべて環境変数 `PYTEST_ADDOPTS` しか読まず ini の
`addopts` を見ない**。ini に `-k` / `--collect-only` / `-n auto` 相当を書くと、acceptance 形と
判定されたまま実際には選択・非実行・並列度が変わり、preflight 3 本 (489/543/616) と
`_suite_identity` (700) の前提が崩れる。
→ **決定: `addopts` を書かない。境界テストで機械固定する。**

### 壊れない側の確認

- `_build_pytest_command` 301-302: `has_target` は `_positional_tokens(args)` だけで決まり ini を見ない。
  **明示 target が常に付くので `testpaths` は runner 経路では発火しない** = 既存起動形は不変
- `_is_acceptance_run` 405/423-431: 位置引数を `Path(token).resolve()` で `_DEFAULT_TARGET` と比較。
  `_normalize_args` (916) が cwd 基準で絶対化済み。ini 導入は無関係
- rootdir は `orchestrator/tests` → `<REPO>` へ移動。影響は (1) 相対表示、(2) `.pytest_cache` の位置
  (`.gitignore` が既にカバー)、(3) `confcutdir` 既定が `<REPO>` になり `<REPO>/conftest.py` と
  `<REPO>/orchestrator/conftest.py` が探索対象に入る — **どちらも存在しないので挙動不変**
- conftest 探索: `orchestrator/tests/conftest.py` は test file と同階層なので rootdir に依らず必ず読まれる
- import: `__init__.py` が無く importmode=prepend なので sys.path 先頭は test file の dirname。rootdir 非依存

### 設定内容

`<REPO>/pytest.ini` を新設 (`pyproject.toml` は packaging 意味を持ち込むので不採用。
`collect_ignore` は `<REPO>/conftest.py` の新設を要求し全 run に import を挟むので不採用)。

    [pytest]
    testpaths = orchestrator/tests
    norecursedirs = *.egg .* _darcs build CVS dist node_modules venv {arch} output external

- `testpaths`: 引数なし起動でのみ発火 → F41 の 1253 errors を直接消す。runner 経路は挙動不変
- `norecursedirs`: pytest は既定を**置換**するため既定値を明示再掲した上で `output external` を足す。
  `.*` を落とすと `.claude/worktrees/` が収集対象に戻る
- `addopts` / `filterwarnings` / `xfail_strict` は書かない (赤の有無を変えるため)

### 境界テスト

既存被覆: `test_run_tests_preflight.py:168-233` が `_is_acceptance_run` を `PYTEST_ADDOPTS` 込みで
固定しているが、**ini 由来 addopts は 1 件も見ていない**。全て純増。

- **[純増] `test_repo_pytest_ini_has_no_addopts_and_pins_testpaths`** (新規
  `orchestrator/tests/test_pytest_collection_config.py`): `configparser` で `[pytest]` に
  `addopts` キーが無いこと、`testpaths == "orchestrator/tests"`、`norecursedirs` が `.*` と
  `output` を含むことを assert。→ **唯一の破壊経路**を赤にする
- **[純増] `test_bare_pytest_collection_is_scoped_by_testpaths`**: tmp に ini をコピーし
  `output/s1-build-cache/x/foo_test.py` (import 時 raise) と `orchestrator/tests/test_ok.py` を置き
  `--collect-only` を subprocess 実行 → `test_ok` のみ・rc==0。**正例**として ini を消すと rc!=0。
  → `testpaths` の消失・綴り誤り・`norecursedirs` の既定落としを赤にする
- **[純増] `test_runner_default_target_survives_ini`**: `_build_pytest_command([], ..., has_target=False)`
  が `_DEFAULT_TARGET` を含み `_is_acceptance_run([_DEFAULT_TARGET])` が True。
  → 「ini があるから target を落としてよい」という将来の簡略化を赤にする

### 波及

`orchestrator/tests/README.md` の「受入全走の作法」節が「repo には `addopts` を持つ設定ファイルが
無いため…範囲を省くと rootdir 以下を無指定収集する」と明記しており、**同じ変更単位で更新が必要**。
`docs/failures.md` F41 の「恒久対応は T-129 へ集約」も追記対象。

---

## S4 — worktree 置き場の除外

### (P4) の確認結果 — land の受理集合は変わらない

- `_ignored_paths_for_target` (811-831) と呼び側 918-922: `.claude/**` `.codex/**` が `!!` で返るのは
  target がその配下/祖先のときだけ。**912-917 の `protected` に `_CONTROL_CONTAINERS` (46) が
  無条件で入っているため、その形の target は先に `RC_CONTROL_PLANE` で落ちる** → 到達不能、不変
- `_existing_ignored_target_or_ancestor` (864-898): 先頭成分から stat し、最初の非 dir か最終成分で
  1 回だけ `check-ignore`。`.claude/settings.json` は `.claude` を dir で通過し `settings.json` で
  判定 → 新パターンに一致せず `None`。この wave の target `.gitignore` も `None` → 不変
- `_worktree_snapshot` (663-730) は `openat`/`listdir` で走り ignore 判定を使わない → 不変

### ただし land 以外で受理集合が動く consumer が 3 つある

1. `tools/dev_waves/git_state.py:47` は `--untracked-files=all` (ignored なし)、`_parse_status` 240-243 が
   `?` を `main_entries` に入れる → `daemon.py:847-850` と `checker.py:454-455` (`MAIN_DIRTY`) が
   発火しなくなる
2. `tools/check_wave_startup.py:127-133 _check_clean_tree` は status 非空で赤 → worktree 内に
   `.codex/worktrees/` がある場合を受理するようになる
3. `orchestrator/campaign/s8b_ratified_freeze.py:352` は `-- FREEZE_DIR` に pathspec 限定 → 無影響

### 手続上の最重要点

**D102 の却下案 (a) が「`.gitignore` を広げる — 他の strict cleanliness consumer まで受理集合を
変える」を名指しで却下している。** S4 はその却下を覆す変更であり、新 D は「新規判断」ではなく
**D102 却下案 (a) の明示的な取り消し**として書く必要がある。

### 境界テスト

既存被覆: `.gitignore` を検査するテストは repo 内に**存在しない**。全て純増。

- **[純増] `test_gitignore_covers_both_worktree_containers`**: tmp の空 repo へ `.gitignore` だけを
  コピーし `git check-ignore -q` で 2 container が rc==0、`.claude/settings.json` /
  `.claude/agents/coder.md` が rc==1。→ `.git/info/exclude` の影響を排して
  **tracked ファイル自身の効力**を固定する (exclude 依存だと恒真になる)
- **[純増] `test_land_acceptance_is_unchanged_by_gitignored_containers`**: (a) 登録済み child ありの
  正例 → `landed`、(b) 未登録 alias → `RC_CONTROL_PLANE`、(c) target =
  `.claude/worktrees/foreign/payload.txt` → `RC_CONTROL_PLANE`。
  → 「ignore したせいで control-plane 検査が空振りする」を赤にする
- **[純増] `test_wave_startup_and_git_state_treat_ignored_containers_as_clean`**:
  受理集合が動いた事実そのものを台帳化し、意図しない再狭化を赤にする

---

## 総括

### (a) 各 S の受理集合が動く向き

- **S1**: land の**拒否は狭まる**、**保護は広がる**。ff-only / lock / stale / audited closure /
  postcondition / mid-flight identity+hash は不変
- **S2**: `check_docs` は**広がる**。案 B 併用なら `check_wave_startup` が**狭まる**
- **S3**: 引数なし `pytest` の収集集合が**狭まる**。runner 経路は**不変** —
  ただし ini に `addopts` を書かない場合に限る
- **S4**: land は**不変**。`dev_waves` の `main_dirty` と `check_wave_startup._check_clean_tree` は**広がる**

### (b) 最も危険な箇所

1. **S3 の ini `addopts`** — preflight 3 本が「全走のつもりで実は選択走」を通す。
   規律 2 に直接触れる唯一の経路。テストで機械固定すること
2. **S1 で `_verify_main_clean` 776-782 を直さないと目的を達しない** — `_handoff_snapshot` だけ
   緩めても stray が今度は 776-782 で落ちる。逆に無条件 `continue` にすると衝突検知が消える。
   **783 以降の通常 untracked 経路へ落とす**のが正解
3. **S4 は D102 却下案 (a) の明示的取り消し** — land 以外で受理集合が広がる consumer が 3 箇所
4. **S1 で `identities` から hash を落とす риск** — 既存 mid-flight テストは inode 差し替えしか
   見ないため hash を落としても緑のまま通る。content-only 変異テストが必須

### (c) 段 4 で親が裁定すべき択一

1. **S1 の `_SAFE_HANDOFF_RE`**: brief (P1) は維持を書いたが、維持すると非 ASCII 名 handoff で
   land が落ち続け目的を部分的にしか達さない。**プランの推奨は削除**
2. **S1 の `require_one_link=True`**: hard link handoff を拒否し続けるか、保護対象に含めるか。
   プランの推奨は「拒否をやめて保護する」
3. **S2 の移設先**: A / B / **A+B (推奨)** / C (scope 拡大)
4. **S2 の malformed 検査 (2182-2184)**: `状態:` 行欠落も他人の commit を止める。
   stale と一緒に緩めるか、finding のまま残すか。プランの推奨は残す
5. **S4 のパターン形**: `**/` 付きか root anchored か。プランの推奨は `**/` 付き
6. **S4 の D 記録**: 「D102 却下案 (a) の取り消し」として書くか、S1〜S4 を 1 本の D にまとめるか
