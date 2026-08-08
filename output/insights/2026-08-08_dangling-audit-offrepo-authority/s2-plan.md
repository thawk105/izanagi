# 実装プラン

対象は [tools/audit_dangling_commits.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-dangling-audit-offrepo-authority/tools/audit_dangling_commits.py:1) と [test_audit_dangling_commits.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-dangling-audit-offrepo-authority/orchestrator/tests/test_audit_dangling_commits.py:1) のみとする。`audit()` の現行三条件はそのまま残し、その結果に repo 外正本による第四の抑止を適用する新しいラッパーを追加する。

## 1. `tools/audit_dangling_commits.py`

### 1.1 import・型・定数

現在の 12–16 行へ次を追加する。

- `hashlib`
- `stat`
- `dataclasses.dataclass`
- `collections.abc.Sequence`

19–25 行の後へ追加する。

```python
OFFREPO_ROOT_ENV = "IZANAGI_DEV_WAVE_JOBS_DIR"

Suppression = tuple[str, str, Path]  # commit, repo path, authority absolute path
RootRejection = tuple[Path, str]

@dataclass(frozen=True)
class AuditReport:
    findings: list[Finding]
    suppressions: list[Suppression]
    requested_roots: tuple[Path, ...]
    accepted_roots: tuple[Path, ...]
    rejected_roots: tuple[RootRejection, ...]
    scan_performed: bool
    blob_failures: int
    scan_failures: int
```

内部照合用として、同じ位置へ次も追加する。

```python
@dataclass(frozen=True)
class _BlobCandidate:
    commit: str
    path: str
    basename: str
    content: bytes
    digest: bytes
```

`LIMITATION_NOTICE` は変更しない。今回変わるのは既存検出範囲ではなく、その検出結果から「repo 外に同一 bytes の正本がある」ものを透明に抑止する処理だからである。新条件は `--offrepo-root` の help と実行時の探索状況出力で別に開示する。

### 1.2 raw bytes 用 Git helper

現在の `_git()` 28–47 行は text command 用として挙動を変えない。その直後へ追加する。

```python
def _git_bytes(repo: Path, *args: str) -> subprocess.CompletedProcess[bytes]:
```

処理は `_git()` と同じく以下を満たす。

- `GIT_DIR` など 5 変数を除去する。
- `GIT_OPTIONAL_LOCKS=0`、`LC_ALL=C` を設定する。
- `stdout` / `stderr` は `PIPE`、`check=False`。
- `text=True` を指定せず raw bytes を返す。
- 書き込み Git command は使わない。

### 1.3 commit 側 regular blob の取得

現在の `commit_subject()` 117–118 行の後へ追加する。

```python
def _commit_regular_blob(
    repo: Path,
    commit: str,
    path: str,
) -> tuple[bytes | None, bool]:
```

戻り値の第 2 要素は Git command・形式解析の失敗を示す。具体手順は次のとおり。

1. 次を raw bytes で実行する。

   ```text
   git -C <repo> --literal-pathspecs ls-tree -z --full-tree <commit> -- <path>
   ```

2. NUL 区切り record を 1 件だけ受理し、record の path が `os.fsencode(path)` と完全一致することを確認する。
3. mode/type は `100644 blob` または `100755 blob` だけを受理する。

   - record なし、mode `120000` の symlink、`160000 commit` の gitlink、tree は `(None, False)`。
   - したがって削除・symlink・gitlink は抑止候補にならない。

4. 得た object ID に対して次を実行する。

   ```text
   git -C <repo> cat-file blob <object-id>
   ```

5. 成功時だけ stdout bytes を返す。`ls-tree` / `cat-file` の rc 非 0、複数・不正 record、object 不在は `(None, True)` とする。

この optional な照合経路の失敗では監査全体を rc=2 にしない。該当 `(commit,path)` を findings に残し、`blob_failures` を増やす。

### 1.4 探索根の正規化と P5

同じく `commit_subject()` 後へ追加する。

```python
def _validate_offrepo_roots(
    repo: Path,
    roots: Sequence[Path | str],
) -> tuple[tuple[Path, ...], tuple[RootRejection, ...]]:
```

手順は次のとおり。

- roots が空なら Git command も実行せず空を返す。
- work tree は次で取得して `resolve()` する。

  ```text
  git -C <repo> rev-parse --show-toplevel
  ```

- 各 root も `resolve(strict=False)` し、重複を除いて絶対 path 化する。
- root が work tree と同一、または work tree の子孫なら拒否する。拒否 root は走査せず、理由を出力対象に残す。
- 安全上は「root が work tree の祖先で、走査すると repo を内包する」場合も拒否することを推奨する。これにより broad root 経由で repo 内 untracked copy を正本扱いする経路も閉じる。
- root 不在・directory 読取不能はここでは fatal にせず、走査時の `scan_failures` とする。
- 相対 root は起動 cwd 基準で絶対化する。runbook が与える本番値は絶対 path とする。

拒否は「その root を抑止根拠に使わない」という意味にし、監査自体は続行する。rc は残存 findings だけで決め、拒否した事実は必ず表示する。

### 1.5 repo 外 regular file の読み取り

新規 helper を追加する。

```python
def _read_regular_candidate(
    path: Path,
    expected_size: int,
) -> tuple[bytes | None, bool]:
```

- 事前の `lstat()` で symlink と非 regular file を除外する。
- size が `expected_size` と違えば open しない。
- Linux では `os.open(O_RDONLY | O_CLOEXEC | O_NOFOLLOW)` を使い、open 後も `fstat()` で regular file と size を再確認する。
- `O_NOFOLLOW` が利用できない環境では symlink-follow fallback を行わず、その候補を不採用にする。
- open/read/stat の `OSError` は `(None, True)`。候補を抑止根拠にせず、監査は継続する。
- read 後の長さが size と違う場合も race として不採用にする。

### 1.6 一回だけ行う走査と照合述語

新規関数を追加する。

```python
def _find_offrepo_matches(
    roots: Sequence[Path],
    candidates: Sequence[_BlobCandidate],
) -> tuple[dict[tuple[str, str], Path], int]:
```

具体手順は以下とする。

1. candidates が空なら即座に `{}`, `0` を返し、`os.walk` を呼ばない。
2. candidates を `basename -> size -> candidates` へ索引する。
3. root、`dirnames`、`filenames` を sort し、各 root を一度だけ次で走査する。

   ```python
   os.walk(root, topdown=True, followlinks=False, onerror=...)
   ```

4. filename が候補 basename に無ければ `lstat()` もしない。
5. basename 一致後の順序を厳守する。

   1. `lstat()` で regular file
   2. `st_size` 一致
   3. `_read_regular_candidate()`
   4. `hashlib.sha256(candidate_bytes)` 一致
   5. 最後に `candidate_bytes == commit_blob_bytes`

   hash は prefilter にすぎず、抑止の最終根拠は bytes の直接比較とする。

6. symlink directory は `followlinks=False` で辿らない。symlink file、FIFO、socket、device、読めない file は候補から外す。
7. directory の `onerror`、`lstat/open/read` 失敗は `scan_failures` に加算し、その file/root では抑止しない。
8. 同一 `(commit,path)` に複数の完全一致実体がある場合、sort 済み走査で最初の絶対 path だけを根拠として採用する。
9. 全 candidate の根拠が得られた場合は早期終了してよい。

### 1.7 `audit()` は現状維持、新規ラッパーを追加

`audit()` 121–152 行は signature・戻り値を含めて変更しない。特に 143–149 行の次の三条件をそのまま維持する。

- excluded prefix なら除外
- main tree に同一 path があれば除外
- 他 local branch tip tree に同一 path があれば除外

152 行の後へ追加する。

```python
def audit_with_offrepo(
    repo: Path | str,
    main_ref: str = "main",
    excluded_prefixes: tuple[str, ...] = DEFAULT_EXCLUDED_PREFIXES,
    *,
    offrepo_roots: Sequence[Path | str] = (),
) -> AuditReport:
```

処理順は次のとおり。

1. `audit(repo, main_ref, excluded_prefixes)` を一度だけ呼び、既存三条件の findings を得る。
2. 探索根を正規化・検査する。
3. root 未指定または valid root 0 件なら findings をそのまま返す。
4. findings の各 path について `_commit_regular_blob()` を呼ぶ。
5. regular blob を取得できたものだけ `_BlobCandidate` にする。
6. candidate basename が 0 件なら `scan_performed=False` のまま返す。
7. 全 candidate をまとめて `_find_offrepo_matches()` へ一度だけ渡す。
8. 完全一致が得られた path を findings から外し、`Suppression(commit,path,authority)` に移す。
9. 同じ commit に未一致 path が残れば、その commit は残存 path だけで findings に残す。
10. findings / suppressions は commit、path 順を維持する。

これにより `audit()` の既存 API と既存単体テストを保ったまま、CLI のみ第四条件込みの report を使える。

### 1.8 CLI root の選択

`main()` の argparse では、現在の `--ref` 167 行の直後、`--include-fold-trees` 168 行の前へ追加する。

```python
parser.add_argument(
    "--offrepo-root",
    type=Path,
    action="append",
    default=None,
    metavar="PATH",
    help=(
        "repo 外正本の探索根。複数指定可。指定時は "
        f"{OFFREPO_ROOT_ENV} より優先する"
    ),
)
```

`parse_args()` 173 行の直後で次の規則により roots を決める。

- `args.offrepo_root is not None`: CLI で指定された全 root を使い、環境変数は完全に無視する。
- CLI 未指定かつ `IZANAGI_DEV_WAVE_JOBS_DIR` が非空: その値 1 個を root とする。
- CLI 未指定かつ環境変数が unset/空: `()` とし、探索しない。
- コードには `/work/1/.../dev-wave-jobs` を焼き込まない。

177 行の `audit(...)` を `audit_with_offrepo(..., offrepo_roots=roots)` に置き換える。

### 1.9 出力と rc

`main()` 182–191 行の findings 出力より前に、次を出す helper を追加する。

```python
def _print_offrepo_report(report: AuditReport) -> None:
```

出力形式は次とする。

```text
audit_dangling_commits: repo 外正本の探索根 1 件
  探索根: /absolute/root
audit_dangling_commits: repo 外正本で抑止 13 (commit, path) 対
  commit <sha>: <repo/path>
    正本: /absolute/root/wave/file
```

- 抑止 1 件ごとに commit、repo 内 path、根拠となった絶対 path を必ず出す。
- 抑止 0 件でも `repo 外正本で抑止 0 (commit, path) 対` を出す。
- root 未指定時は次を出す。

  ```text
  audit_dangling_commits: repo 外正本の探索を未実施
    --offrepo-root / IZANAGI_DEV_WAVE_JOBS_DIR が未指定
  ```

- candidate basename 0 により走査しなかった場合は「照合可能な basename 0 件のため走査省略」と出す。
- P5 で拒否した root、blob 検証失敗数、走査不能数も「抑止せず」と明記する。
- この report を出してから、既存の「要確認 0 件」または findings 節を出す。したがって rc=0 のときも抑止内容は消えない。
- rc=0/1 は `report.findings` の残存 commit 数だけで決める。全 path が抑止されれば rc=0、一部でも残れば rc=1。
- 基礎監査の Git command 失敗だけは従来どおり rc=2。repo 外の unreadable file/root は findings を残す側へ倒し、rc=2 にしない。

## 2. テスト変更

### 2.1 既存 test の保持

静的には既存 test は指定の「6 本」ではなく 8 本ある。8 本すべてを保持する。

| 現在の nodeid / 行 | 固定している契約 |
|---|---|
| `test_positive_control_deleted_branch_work_is_reported` 76–96 | 消えた branch の新規 path を findings に残し、CLI rc=1、commit/path を表示する |
| `test_negative_main_reachable_commit_is_not_reported` 99–114 | main reachable commit は対象外で、0 件出力に `LIMITATION_NOTICE` がある |
| `test_help_discloses_detection_limitations` 117–122 | help に既存 limitation が出る |
| `test_decode_error_is_execution_failure` 125–136 | 基礎 Git 経路の decode failure は rc=2 と stderr |
| `test_negative_path_already_in_main_is_not_reported` 139–149 | 同一 path が main tree にあれば除外する第二条件 |
| `test_negative_path_on_live_branch_tip_is_not_reported` 152–162 | 同一 path が生存 branch tip にあれば除外する第三条件 |
| `test_negative_main_side_of_unreachable_merge_is_not_reported` 165–194 | merge は combined diff で評価し、main 側を誤報しない F119 防壁 |
| `test_negative_fold_managed_paths_are_excluded_by_default` 197–216 | spool/archive の既定除外と明示 include の両方 |

`audit()` を変更しないため、72–73 行の `_audit()` helper と上記の直接 `audit()` assertions は変更不要である。

ただし環境依存を防ぐため、`ADC.main()` を呼ぶ既存 test では `monkeypatch.delenv(ADC.OFFREPO_ROOT_ENV, raising=False)` を明示する。対象は少なくとも 76、99、125 行開始の三 node とする。これは [T-593] 事項 6(a) の別 fixture 隔離ではなく、新規 CLI 入力の test-local 初期化である。

### 2.2 新規 nodeid

216 行の後、`_run()` の前へ追加する。

#### Positive controls

- `test_positive_offrepo_same_basename_same_bytes_is_suppressed_and_disclosed`

  repo 内を `output/insights/2026-08-06_t574-historical-resolver/probe_g2_consumers.py`、repo 外を `dev-wave-jobs/t574-historical-resolver/probe_g2_consumers.py` とし、directory 名が違っても basename と bytes が一致すれば抑止する。`AuditReport.findings == []`、抑止 triple、CLI rc=0、抑止節の三 path 情報、既存「要確認 0 件」を固定する。

- `test_positive_offrepo_environment_default_is_used`

  `IZANAGI_DEV_WAVE_JOBS_DIR` だけを設定し、CLI option なしで同じ抑止になることを固定する。

- `test_positive_repeated_cli_roots_override_environment`

  環境変数側にも一致物を置く一方、`--offrepo-root` を 2 回指定し、2 番目の CLI root にも一致物を置く。出力された根拠が CLI root 側で、環境変数側 path が根拠に選ばれないことを固定する。

- `test_partial_offrepo_suppression_keeps_remaining_finding_and_rc1`

  同一 commit の 2 path の片方だけに正本を作る。抑止節に 1 path、findings 節に残り 1 path、rc=1 を固定する。

#### Content negative controls

- `test_negative_offrepo_same_basename_same_size_different_bytes_is_reported`

  basename・size は同じだが bytes を変え、hash/content 比較を通らず findings に残ることを固定する。

- `test_negative_offrepo_same_basename_different_size_is_reported`

  basename だけ同じで size が違う file を置き、size prefilter の段階で不採用になることを固定する。

- `test_negative_offrepo_same_bytes_different_basename_is_reported`

  bytes が同じでも basename が違えば候補列挙されないことを固定し、述語が「basename か bytes」ではなく連言であることを示す。

#### Root/configuration negative controls

- `test_negative_offrepo_root_unspecified_does_not_suppress_and_discloses_skip`

  repo 外に完全一致物を作るが、CLI root を渡さず env も削除する。finding、rc=1、「探索を未実施」、抑止 0 を固定する。

- `test_negative_offrepo_root_inside_worktree_is_rejected_without_suppression`

  repo 内 untracked file を探索根配下に置く。root 拒否表示、抑止 0、finding 維持、rc=1 を固定する。

- 祖先 root も拒否する案を段 4 で採用した場合は、`test_negative_offrepo_root_containing_worktree_is_rejected` も追加する。

#### File-kind/error/lazy controls

- `test_negative_offrepo_candidate_kind_is_not_authority[symlink]`
- `test_negative_offrepo_candidate_kind_is_not_authority[fifo]`

  同名候補が symlink / FIFO でも open・追跡せず、finding を残す。

- `test_negative_offrepo_read_error_keeps_finding_and_is_not_rc2`

  `_read_regular_candidate()` の read failure を test-local に注入し、抑止なし、scan failure 表示、rc=1 を固定する。実 file の mode だけに依存する permission test にはしない。

- `test_negative_unreachable_symlink_is_not_suppressed_by_regular_file`

  commit 側 mode `120000` の symlink と、同 basename・同 payload の repo 外 regular file を用意しても抑止しない。

- `test_offrepo_scan_is_skipped_without_candidate_basenames`

  findings が空の repo と有効 root を渡し、`_find_offrepo_matches()` を「呼ばれたら失敗」に置換する。`scan_performed=False` と rc=0 を固定する。

## 3. 性能設計と受入目標

- root 未指定時は blob 取得も filesystem scan も行わないため、現行 wall 9.7 秒への増分は argparse・空 report 出力程度。
- root 指定済みでも、既存三条件後の path が 0、または regular blob 候補 basename が 0 なら `os.walk` を呼ばない。
- 走査は root ごとに一回であり、commit/path ごとに 20,544 file を再走査しない。
- `cat-file` 結果は object ID 単位で cache し、同一 blob を重複取得しない。
- file hash は basename と size の双方が一致した候補にだけ計算する。
- 現行 24 対では、実測済み全走査 2.0 秒に blob 取得・限定 hash が加わるため、暫定見積りは約 `+2〜3 秒`、総 wall 約 `12〜13 秒`。これは見積りであり、親が Pegasus 受入で再測定する。
- 実 repo 受入の期待値は brief の実測どおり、抑止 13 `(commit,path)` 対、残存 6 commit / 15 path。件数が違えば実装完了としない。

## 4. 実装子と親の境界

実装子は上記 Python tool と test file だけを編集する。次は親の所有とする。

- `docs/pegasus-runbook.md` §7.2 への `IZANAGI_DEV_WAVE_JOBS_DIR` 所在・設定例
- spool fragment、worklog、failure/decision 記録
- 関連 test の実走、実 repo 受入、wall 再測定
- commit

本プラン作成時点では pytest を実走しておらず、テスト通過は主張しない。

## 5. やらないこと

- 裁定 (a) の ack 台帳、SHA allowlist、既知 commit を黙らせる機構は追加しない。
- 裁定 (d) の `git gc --prune=now`、object 削除、branch 削除は行わない。
- 裁定 (c) は自然な git gc 回収に任せ、コードを追加しない。
- [T-593] 事項 1(c) の「path は同じだが blob が異なる」第二警告カテゴリは実装しない。
- [T-593] 事項 4 の refs snapshot 比較・再試行・上限超過 rc=2 は実装しない。
- [T-593] 事項 6(a) の `test_s8c_preregistration_invariant.py` 用隔離 repo は実装しない。
- relative path、directory 名断片、mtime、size 単独、hash 単独では抑止しない。
- repo 外 file を実行・import・解釈せず、basename・metadata・bytes だけをデータとして読む。
- `.claude/commands/cleanup-branches.md` や docs は実装子から変更しない。

## 総括

- 現行 `audit()` の三条件と list APIを一切変えず、`audit_with_offrepo()` で第四の抑止を後段適用する。
- 探索根は反復可能な `--offrepo-root` が環境変数を上書きし、両方未指定なら明示的に探索しない。
- 抑止は regular blob/file の basename・size・SHA-256・最終 bytes 比較を順に通った場合だけ行う。
- 抑止した全 `(commit,path)` と絶対 authority path を rc=0/1 の双方で表示し、rc は残存 findings だけで決める。
- 走査は全候補をまとめて一回、候補 basename 0 なら完全に省略する。

最も壊れやすい箇所は、Git tree mode を含む blob 取得と filesystem の symlink/race 境界である。単なる `git show <commit>:<path>` や `Path.is_file()/read_bytes()` に縮めると、symlink・gitlink・TOCTOU が抑止根拠へ混入する。

段 4 で親が裁定すべき残り論点は、P5 を「work tree 内 root の拒否」だけに留めるか、work tree を内包する祖先 root も拒否するか、および拒否 root を非 fatal にして残存 findings の rc を返す本案を採るかである。併せて、brief の「既存 6 test」と実ファイルの 8 node の不一致は、受入 matrix を 8 本基準に直すべきである。