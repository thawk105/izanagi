## 総括

プランはそのままでは承認できない。主な blocker は次の 2 点である。

- `git worktree list --porcelain` の非 `-z` 出力は、path 中の改行を record-safe に符号化しない。`raw.split(b"\n\n")` と `splitlines()` の組合せにより、実在 worktree を偽の `prunable` record として除外できる。
- 一覧取得が `/tmp` 隔離ディレクトリ作成より先であるため、「観測時に path 不在なら新しい隔離 dir と重ならない」という中心推論は偽である。

したがって、少なくとも NUL 区切り porcelain の採用と、prunable 観測から隔離 dir 作成までの TOCTOU の扱いを再設計する必要がある。pytest および Git probe は実走していない。

## 所見 (real 候補)

1. **非 `-z` porcelain と `splitlines()` により、実在 worktree を prunable と偽装できる。**

Git の非 `-z` porcelain は worktree path を `worktree ` の後へ raw に出す。例えば実在 path が bytes で `b"/tmp/live\nprunable accidental"` なら、出力上は概念的に次の形になる。

```text
worktree /tmp/live
prunable accidental
HEAD <sha>
detached

```

プランの `is_prunable` は path の継続部分を正規 field と区別できず、この実在 record を除外する。不変条件1の直接的な穴である。さらに `bytes.splitlines()` は LF 以外の CR、VT、FF 等も境界とみなすため、Git の record delimiter より広い入力を field 化する。

**判定・成果物:** real — 非 `-z` の raw path と [`splitlines()` を field parser に使う計画](</home/SFC/tanab/.claude/jobs/b550caea/tmp/wave-t2347/artifacts/t2347-scr-worktree-land/plan.md>) が根拠; 放置時は本来 RC31 となる実在登録との重なりが fold gate を通過し、最終的に `landed` になりうる。

2. **空行を含む path は `raw.split(b"\n\n")` の record 境界そのものを破壊する。**

実在 path が `b"/tmp/live\n\nprunable accidental"` なら、最初の偽 record は `b"worktree /tmp/live"`、続きは別 record になる。

- `/tmp/live` が存在しなければ、切り詰められた偽 path の `resolve(strict=True)` が失敗するため拒否側へ倒れる。
- 偶然 `/tmp/live` という別ディレクトリが存在すれば、それを登録 path として返して実物を失う。これは受理側の穴にもなる。
- path の改行後に `worktree `、`prunable ` 等を置けば、偽 field・偽 record を注入できる。

**判定・成果物:** real — raw LF と同じ `b"\n\n"` を record delimiter にしており文法が非一意; 放置時は状態により誤 RC31 または実在登録を見落とした `landed` の両方へ倒れる。

3. **「観測時に path 不在なら、後で作る隔離 dir と重ならない」は反証できる。**

[`_execute_fold_gate`](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2347-scr-worktree-land/tools/dev_wave_land.py:3804>) は登録一覧を先に取得し、その後で `/tmp/izanagi-fold-gate-*` を作る。具体的には、登録 path が `/tmp/izanagi-fold-gate-XYZ` だがそのディレクトリがまだ存在しない状態で Git が prunable と判定し、その直後の `TemporaryDirectory` が同じ未使用名を選べる。filesystem 上に存在しないことは、Git registry に予約されていないことを意味しない。

同様に、観測後に broken symlink が修復される、`/scr` が mount される、登録 path が作成される、といった遷移でも prunable 判定は陳腐化する。提案実装は prunable record を `resolve` 前に捨てるため再確認しない。

**判定・成果物:** real — 登録取得が temp dir 作成より前というコード順と、registry が tempfile の名前衝突検査対象外であることが根拠; 放置時は本来 overlap RC31 の状態が通過し、隔離 tree の書込み・削除が登録 path に作用しうる。

4. **path 不在でも `prunable` が出ない状態は残る。**

少なくとも次がある。

- admin の `locked` file が存在する linked worktree。Git は `locked` を優先し、missing path を prunable としない。
- Git が live と判定した直後、Python の `resolve` 前に path が消える race。
- admin の `gitdir` file 欠落など、`--expire` の期限までは prune 対象にしない不完全登録。実装は `list` に明示的な `--expire` を渡さない。
- stat・automount・権限エラー。Git コマンド自体が失敗すれば `_require_git`、record が出れば `resolve(strict=True)` が失敗する。

`worktree ` 行が得られる限り、これらは prunable exemption に入らず従来どおり `_FoldGateFailure`、最終的に RC31 となる。Git が破損 admin entry を一覧から完全に省略する形では、可視 record が別にあれば helper はその登録を検出できない。

**判定・成果物:** real — marker は単なる「path 不在」ではなく Git の prune eligibility である; 放置時は locked・expiry-graced・race 型 F851 は引き続き `fold-gate-failed` RC31 となる。

## 反証した懸念 (refuted)

5. **安定した通常の F851 状態では `/scr/...` と `/tmp/izanagi-fold-gate-*` は lexical overlap しない。**

mount、symlink、rename、race がなく、`/scr` と `/tmp` が独立した名前空間で固定されているという狭い条件なら、等号・親子関係は成立しない。ただし、この狭い命題しか反証できず、親の一般命題は所見3により偽である。

**判定・成果物:** refuted — 安定した絶対 path 同士について [`_paths_overlap_absolute`](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2347-scr-worktree-land/tools/dev_wave_land.py:3474>) は `/scr` と `/tmp` を非重複とする; この限定状態では RC31 から fold gate 続行へ変わるのが意図した一点である。

6. **正規 field 名や通常の branch 名だけから `prunable` marker が生じる懸念は反証できる。**

現行 porcelain の `HEAD`、`branch`、`detached`、`bare`、`locked` は `prunable` と field 名が衝突しない。branch 値は必ず `branch ` の後にあり、ref 名自体も改行等の制御文字を許さない。`branch refs/heads/prunable-*` は marker にならない。問題は field 名ではなく、所見1の raw path 継続行である。

**判定・成果物:** refuted — 正規 record 文法では `prunable` は固有 label; 通常 branch/path substring だけでは land 判定は変わらない。

7. **fold gate 以外の dirt / no-touch / ff-only / provenance / lock の受理述語が直接変わる懸念は反証できる。**

変更対象の helper の consumer は [`_execute_fold_gate`](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2347-scr-worktree-land/tools/dev_wave_land.py:3804>) だけである。初回 locked preflight、provenance、fold gate 後の lock 再取得と fingerprint/preflight 再検証、target collision、`merge --ff-only` は同じ経路に残る。noop fold は helper 自体を通らない。

ただし、所見1・3の誤分類は fold gate 自身の受理集合を「真正な prunable record 一種類」より広くする。また、従来 RC31 が先に出ていた入力が後段の別 RC へ変わる可能性はあるが、その後段 gate の受理集合変更ではない。

**判定・成果物:** refuted — 他 gate の関数・引数・再検証順は不変; 放置時も dirt/provenance/lock/ff-only を破る入力が `landed` へ変わる直接経路はないが、fold overlap の穴は残る。

8. **不変条件3の計画どおりのテストは、文字どおり `if not paths:` のままなら緑にならない。**

prunable record「だけ」を stdout に渡し、期待値を `()` とする前半が実装されれば、`if not paths:` は必ず `_FoldGateFailure` を投げて赤になる。ここは親プランの説明どおりである。

**判定・成果物:** refuted — all-prunable 入力の期待値 `()` と `if not paths:` は両立しない; その変異を放置すれば対象テストが赤となり、land 本体は全-prunable を RC31 のまま拒否する。

## テストの恒真化リスク

9. **テスト1は「既知の main/wave だけを返す」実装でも緑になる。**

例えば `_registered_worktree_paths` が registry を列挙せず、常に `repository.main` と `repository.wave` の resolved path だけを返す実装でも、両 path の包含確認と wave 配下への人工的 overlap は通る。第三の実在 linked worktree を無視する不変条件1違反を検出できない。

**判定・成果物:** real — fixture の実在登録集合が main＋wave の二本だけ; 放置時は第三の実在登録との overlap が RC31 にならず fold gate を通過しうる。

10. **テスト2は monkeypatch 対象だけ fail-closed にする実装でも緑になる。**

実在 main 登録の特定 bytes/path にだけ `PermissionError`・`UnicodeError` を伝播させ、その他の非 prunable record の `FileNotFoundError`、broken symlink、権限エラーを無視する実装でも書ける。人工例外は exception translation を検査するが、全 record 量化を証明しない。

**判定・成果物:** real — 実 filesystem 上の第三の非 prunable 解決不能登録を含まない; 放置時は未検査 record の解決不能が RC31 でなく受理へ倒れうる。

11. **テスト3は marker-only の「worktree record ゼロ」を含めないと恒真化できる。**

次の誤実装は計画された二刺激を通る。

```python
if not paths and b"prunable" not in raw:
    raise _FoldGateFailure("registered worktree list is empty")
```

prunable recordだけなら `()`、空または通常 field だけなら例外になる一方、`b"prunable fake\n\n"` のように `worktree ` 行ゼロでも marker がある入力を受理する。`saw_worktree_record` を本当に検査した証拠にならない。

**判定・成果物:** real — 「marker はあるが worktree 行ゼロ」の負例がない; 放置時は壊れた一覧が RC31 でなく空登録として fold gate を通過する。

12. **テスト4は単純 path しか作らず、raw path からの marker 注入を検出しない。**

`branch refs/heads/prunable-not-a-marker` は label 境界の弱い positive control にすぎない。実在 worktree path に `\nprunable reason`、`\rprunable reason`、または `\n\n` を含めるケースがなく、所見1・2の実装でも緑になる。

**判定・成果物:** real — 本物の Git を使っていても helper の path 名が `"job-repo"` 固定; 放置時は実在 newline-path worktree が除外され、overlap RC31 が `landed` に変わりうる。

13. **テスト5は `LAND._git` を通らない prune を検出しない。**

例えば `_registered_worktree_paths` が直接 `subprocess.run([...,"worktree","prune","--dry-run"])` を実行してから、一覧取得だけを `LAND._git` で行えば、spy は list 一回だけを観測し、admin path と prunable record も残る。文字どおり「prune を実行しない」という不変条件5を破っても緑になる。

**判定・成果物:** real — spy の観測面が `LAND._git` に限定され、`--dry-run` は registry の後状態を変えない; 放置時はこの例では land の合否は変わらないが、禁止した prune 機構の導入を成果物が見逃す。

## 変異帰属の検査

14. **列挙された8変異を、新テストより先に落とす既存テストは静的には見当たらない。**

| 変異 | 計画上の kill | 既存テストによる先行赤 |
|---|---|---|
| 1. 行分割へ退行 | 条件3・4 | なし |
| 2. prunable 無効 | 条件3・4 | なし |
| 3. prunable を record 数に数えない | 条件3 | なし |
| 4. `if not paths:` | 条件3 | なし |
| 5. `UnicodeError` 捕捉除去 | 条件2 | なし |
| 6. `strict=False` | 条件2・4 | なし |
| 7. overlap 拒否無効 | 条件1 | なし |
| 8. prune 追加 | 条件5 | なし |

既存の `_execute_fold_gate` 実走テストは通常の実在 main/wave しか持たないため変異1〜6を踏まない。変異7では `/tmp` と登録 path が重ならない。変異8の prune は健全な登録を消さない。`test_git_operation_surface_is_read_only_except_sha_ff_merge` は `_land()` が `_run_fold_gate` を monkeypatch するため、この helper の `worktree` 呼出しを観測しない。

**判定・成果物:** real — 既存テストの入力と monkeypatch 境界を追った結果、8本すべて先行 kill なし; 各 kill は本 wave の新テストの効果として帰属できるが、所見9〜13の未検査変異は別途残る。

## 裁定パッケージ候補 (scope 外の所見)

15. **locked かつ path 不在を将来 exemption に含めるかは別裁定に分離すべきである。**

現行 a5 発生源は lock しないため、本 wave の F851 解消には不要である。`locked` を「安全な missing path」とみなすと、不変条件2を追加で緩める。

**判定・成果物:** real・scope外 — Git の locked 登録には prunable marker がない; 現状維持ならその状態は RC31、一般的 missing-path exemption に広げれば新たな受理集合になる。

16. **bind mount・同一 inode alias の検出は、今回の path-level 一点緩和とは別問題である。**

`Path.resolve()` は symlink は解決するが、異なる mount path が同じ inode/tree を指す関係までは表現しない。このため、実在登録でも `/scr/x` と `/tmp/y` が bind alias なら `_paths_overlap_absolute` は非重複と判定する。これは今回新設される問題ではなく、既存 gate の限界である。

**判定・成果物:** real・scope外 — overlap が resolved path の等号・親子関係だけで inode/mount identity を見ない; 放置時は bind alias 状態で既存実装から overlap RC31 を出せず、今回の prunable 差分とは独立する。