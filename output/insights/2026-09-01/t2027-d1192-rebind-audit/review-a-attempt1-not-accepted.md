判定は must-fix 1 件です。D1192 の主設計に受理拡大は見つかりませんでしたが、v1 が扱えた path で未捕捉例外になる退行があります。

## Must-fix

### 1. 先頭が正確に `//` の絶対入力で、v2 collector が未捕捉 `ValueError` を漏らす

- 要約: POSIX/Linux で有効な `//path` を filesystem root 相対へ変換できず、構造化拒否にもならない。
- 失敗シナリオ: depfile が `//work/.../masstree-src/include/x.hh` を入力として持つ。`abspath` と `normpath` は先頭の `//` を保存するため、`Path("//...").relative_to(Path("/"))` が `ValueError` を投げる。
- 根拠:
  - `//` を保存する正規化: [s8b_compiler_input.py:1032](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t2027-d1192-rebind/orchestrator/campaign/s8b_compiler_input.py:1032)
  - 未捕捉の filesystem 相対化: [s8b_compiler_input.py:1058](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t2027-d1192-rebind/orchestrator/campaign/s8b_compiler_input.py:1058)、origin root がない場合は [s8b_compiler_input.py:1062](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t2027-d1192-rebind/orchestrator/campaign/s8b_compiler_input.py:1062)
  - 呼び手は `CompilerInputError` だけを変換: [buildcache.py:2660](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t2027-d1192-rebind/orchestrator/campaign/buildcache.py:2660)
  - v1 は `resolve(strict=True)` により `/...` へ正規化していた: [s8b_compiler_input.py:435](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t2027-d1192-rebind/orchestrator/campaign/s8b_compiler_input.py:435)
- 成果物への影響: 該当 cell は compiler-input anomaly として記録されず fresh build が異常終了し、binary admission receipt と certified 選択が欠落する。
- scope: D1192 が変更する collector の path 正規化そのものであり、親裁定の scope 内。
- 補足: 読み取り専用 probe でも `//etc/hosts` は v1 側で `/etc/hosts` になり、v2 の相対化では `ValueError` になった。pytest は実走していない。

## v1 拒否条件との 1 対 1 対応

| v1 の条件 | v2 の対応 | 判定 |
|---|---|---|
| 空 path、NUL、非正規 path | `_normalized_relative_posix()` の exact `str`、非空、NUL、`PurePosixPath` 一致検査 | `//` collector 経路を除き維持 |
| snapshot root 自体を入力にしない | `not pure.parts`。`"."` もここで拒否 | 修正 A で維持 |
| snapshot 外を policy 無しで拒否 | collector の snapshot 分類失敗後、`allow_external_inputs=False` なら拒否 | 維持 |
| 欠落 component を拒否 | 各 component の `stat`、`open` の `OSError` を `CompilerInputError` へ変換 | 維持 |
| ancestor/leaf symlink を拒否 | held fd、`follow_symlinks=False`、`O_NOFOLLOW` | v1 より強い |
| leaf が通常ファイルでない場合を拒否 | open 前後とも `S_ISREG` | 維持 |
| hash 中の size/time/inode 変化を拒否 | `st_dev`、`st_ino`、size、mtime、ctime を再照合 | 維持 |
| external は絶対かつ正規 path | manifest では `filesystem` + `/` 相対 path、collector が絶対化 | `//` だけ対応欠落 |
| external が snapshot へ解決された場合は snapshot 扱い | collector は snapshot を先に分類、validator は filesystem tag の snapshot 着地を拒否 | 維持 |
| external の欠落、symlink、非通常ファイルを拒否 | `/` からの no-follow component 走査 | 維持または強化 |
| 重複、非昇順を拒否 | `(root, path)` の strict 昇順 | 維持 |
| absolute、`..`、末尾 slash、反復 slash | `is_absolute`、parts、`as_posix() == value` | 拒否 |
| `\` | POSIX では区切りでなく通常の filename 文字 | v1 と同じ |

関連実装は [s8b_compiler_input.py:574](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t2027-d1192-rebind/orchestrator/campaign/s8b_compiler_input.py:574) と [s8b_compiler_input.py:776](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t2027-d1192-rebind/orchestrator/campaign/s8b_compiler_input.py:776) です。

## Nit / backlog

- `_strict_root()` は `os.fspath()` の `TypeError` しか包まないため、許容型である独自 `PathLike` が `OSError` や `ValueError` を投げると `CompilerInputError` 外へ漏れる。[s8b_compiler_input.py:530](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t2027-d1192-rebind/orchestrator/campaign/s8b_compiler_input.py:530)。実 production の `str` / `Path` 経路での成果物影響を示せないため nit。
- root 検査 fd は `_strict_root()` の return 前に閉じられ、hash 時に path 名で開き直される。[s8b_compiler_input.py:564](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t2027-d1192-rebind/orchestrator/campaign/s8b_compiler_input.py:564)、[s8b_compiler_input.py:601](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t2027-d1192-rebind/orchestrator/campaign/s8b_compiler_input.py:601)。symlink 交換は拒否されるが、通常 directory への rename 交換では root inode の連続性を証明しない。これは親裁定が明示的に scope 外とした fd lifetime / TOCTOU である。[s4-adjudication.md:25](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2027-d1192-rebind/s4-adjudication.md:25)
- `_roots_overlap()` は canonical path の字句的包含であり、bind mount など異なる path 名の同一 directory は検出しない。[s8b_compiler_input.py:661](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t2027-d1192-rebind/orchestrator/campaign/s8b_compiler_input.py:661)。通常の symlink alias は `realpath` で解消される。物理 alias を含む保証拡張は仮想リスク側の backlog。
- schema/preimage の実装検査は有効だが、選択済み v2 entry の manifest を v1 に reseal して一致検査を直接発火させるテストはない。[buildcache.py:1707](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t2027-d1192-rebind/orchestrator/campaign/buildcache.py:1707)。現テストは旧 digest と新 digest の namespace 分離を検査する形である。[test_buildcache_v2.py:2680](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t2027-d1192-rebind/orchestrator/tests/test_buildcache_v2.py:2680)

## 検査したが問題を見つけなかった観点

- 認められる受理拡大は、消えた origin A の代わりに同じ relative path/hash を持つ current B を受理する D1192 本体だけだった。
- `fetchcontent-masstree` は current root が `None` なら必ず拒否する。[s8b_compiler_input.py:916](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t2027-d1192-rebind/orchestrator/campaign/s8b_compiler_input.py:916)
- filesystem tag による snapshot/current root の字句的な詐称は拒否される。[s8b_compiler_input.py:925](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t2027-d1192-rebind/orchestrator/campaign/s8b_compiler_input.py:925)
- schema と cache preimage の一致検査は fresh/hit の双方にあり、恒真ではない。
- v1 は exact schema dispatch 後、旧 `_normalized_hashed_entries()`、`_compiler_input_entry()`、`_file_sha256()` をそのまま通る。current root は v1 分岐へ影響せず、暗黙の v2 変換や cache-miss 救済もない。
- leaf/component symlink、open 前後 inode、hash 中 metadata は fd 上で再照合される。根より下の no-follow 走査は壊れていない。
- 既存テストの skip、xfail、削除、拒否期待の反転は見つからなかった。cache-hit 正例は collector を stub するが、production collector の分類・再束縛は別の実体テストで通している。

## 親 brief・裁定への反証

親の「修正 A/B/C で監査済み欠陥を尽くした」という前提には、上記 `//` path の第 4 の未捕捉例外が反証となる。これは scope 外リスクではない。

一方、P4 の「v1 read-only 受理条件と bytes 検査は不変」、修正 C の「manifest 受理集合は広がらない」、および残る 7 件クラスが scope 外という裁定には反証を見つけなかった。