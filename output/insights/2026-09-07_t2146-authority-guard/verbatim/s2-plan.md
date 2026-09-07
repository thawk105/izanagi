## 変更表

行番号は現状のファイルに対するもの。挿入後は後続行がずれる。

| file:line | 何を変更するか | なぜ | 受理集合への影響 |
|---|---|---|---|
| `hooks/guard_write.py:3-30` | module docstring の管轄へ発行主体 root を追加し、書込みだけを閉じる旨を記載 | 現状は成果物・ccbench・hooks の 3 面しか列挙していない | 文書のみ |
| `hooks/guard_write.py:34-37` | `re` を import | 内部例外時にも兄弟を巻き込まない exact literal 判定が必要 | なし |
| `hooks/guard_write.py:39-43` | argv/env 上書き不能な `_AUTHORITY_ROOT = "/work/1/SFC/tanab/dev-wave-authority"` と、path 境界付き `_AUTHORITY_LITERAL_RE` を定義 | (P1-a) に同意。既存の公開鍵・秘密鍵定数と同じ固定形にする | なし |
| `hooks/guard_write.py:71-72` 直後 | lexical/canonical の候補を `_inside(candidate, authority_root)` で照合する `_protected_authority(...)` を追加 | root 自身と子孫だけを判定し、symlink alias も canonical 側で捕える | なし |
| `hooks/guard_write.py:223-244` | `classify_path()` の説明を更新し、既存 `_protected_hooks()` 判定と同列の deny union として authority 判定を挿入 | Write/Edit/MultiEdit/NotebookEdit と apply_patch の全 directive は最終的にここへ到達する | authority root の lexical/canonical subtree だけ新規拒否 |
| `hooks/guard_write.py:378-400` | `main()` の例外処理へ `_AUTHORITY_LITERAL_RE` による raw/decoded 判定を追加 | `classify_path()` 内部例外時に authority 呼出しだけが rc=0 へ落ちる穴を防ぐ。単純 substring は兄弟を巻き込むため不可 | 内部例外時の authority mention を新規 fail-closed。兄弟は従来どおり |
| `hooks/guard_bash.py:3-45` | module docstring の leaf/tree と既知限界へ authority root を追加 | 現状の記述には authority がない | 文書のみ |
| `hooks/guard_bash.py:78-107` | 固定 `_AUTHORITY_ROOT` と、左右を shell/path 境界で囲った `_AUTHORITY_LITERAL_RE` を追加。既存 `_MENTION_RE` / `_TREE_LITERAL_RE` は変更しない | 既存 fast path の意味を変えず、authority 専用の単調な trigger を足す | authority exact root/子孫候補だけ精査へ送る |
| `hooks/guard_bash.py:2217-2243` 直後 | shell cwd から絶対 lexical path を作る helper、lexical/canonical を `_inside` で判定する `_authority_tree_violation()`、option/inline fragment 用 `_argument_hits_authority()` を追加 | `_repo_relative*` は repo 外 authority に使えない。`cd` 後も絶対 cwd を別状態として追う必要がある | なし |
| `hooks/guard_bash.py:2305-2323` | `_hooks_tree_violation()` 自体は変更しない | authority は hooks inode index や repo-local root と別の固定 subtree。関数名・責務を混ぜない | なし |
| `hooks/guard_bash.py:2381-2406` | `_tree_violation()` に authority cwd を受ける引数を追加し、行2396の `_hooks_tree_violation()` と並ぶ authority OR を追加 | `_hooks_tree_violation()` の第1呼出し箇所。rm/mv/install/tar展開等の tree 操作を捕える | authority tree の破壊だけ新規拒否 |
| `hooks/guard_bash.py:2409-2426` | 現行判定を `_argument_hits_existing()` として保ち、authority OR を加えた `_argument_hits_protected()` に分ける | `_hooks_tree_violation()` の第2呼出し箇所。conditional reader の出力 option にも authority 判定を伝播しつつ、builder の旧例外と分離する | authority を引数・option 出力先に取る writer を新規拒否 |
| `hooks/guard_bash.py:2458-2489` | `_destroys_protected_tree()` から `_tree_violation()` へ authority cwd を渡す | git/find/tar/rsync/tree mutator の全分岐で外部 cwd を失わないため | authority を destination/破壊対象にする操作だけ新規拒否 |
| `hooks/guard_bash.py:2492-2507` | `_redirect_hits_protected()` に authority cwd を渡し、行2501の `_hooks_tree_violation()` と並ぶ authority OR を追加 | `_hooks_tree_violation()` の第3呼出し箇所。pure reader head でも出力 redirect は書込みになる | authority への `>`, `>>`, `>&`, `&>` を新規拒否 |
| `hooks/guard_bash.py:2509` 直前 | tokenized segment を順にたどり、`cd` を絶対 cwd として追跡する `_authority_command_hot()` を追加 | `cd /tmp && cd ../work/…/dev-wave-authority && …` や canonical alias は raw substring では検出できない | authority に解決するコマンドだけ fast path を外れる |
| `hooks/guard_bash.py:2520-2534` | `authority_hot` を別変数で算出し、fast path と `hot` へ OR。既存 `_MENTION_RE` / `_TREE_LITERAL_RE` / `hooks_hot` はそのまま | 既存 fast-path 条件を緩和・置換しないため | 既存 bit は不変。authority 候補だけ精査へ移る |
| `hooks/guard_bash.py:2536-2550` | opaque/解析不能の理由文へ authority を追加。tokenize 失敗時は境界付き literal の場合だけ fail-closed | authority を含む malformed/opaque writer の素通りを防ぎ、prefix sibling は拒否しない | authority exact mention の解析不能形だけ新規拒否 |
| `hooks/guard_bash.py:2552-2563` | 既存 `marker_cwd` は変更せず、別の絶対 `authority_cwd` を初期化・各 `cd` で更新 | `_repo_relative_path()` の戻り方を変えると既存受理集合が動くため | 既存判定は不変。authority の相対後続 path だけ追跡可能になる |
| `hooks/guard_bash.py:2554` | redirect 判定呼出しへ `authority_cwd` を渡す | `cd authority && cat x > key` を捕える | 新規拒否のみ |
| `hooks/guard_bash.py:2564-2580` | `perf -o/--output` へ authority 出力先判定を追加し、perf 同居判定にも authority cwd を渡す | この専用分岐は `_hooks_tree_violation()` の3呼出しを経ず、`--` 後に head を差し替えるため、4点案のままでは素通りする | `perf ... -o <authority> -- ...` を新規拒否 |
| `hooks/guard_bash.py:2583-2586` | `_destroys_protected_tree()` 呼出しへ authority cwd を渡す | 外部 root の delete/move/rsync destination を捕える | 新規拒否のみ |
| `hooks/guard_bash.py:2597-2620` | legacy leaf hit と authority hit を分離して判定。authority hit は authority cwd で `_read_only_check()` し、builder 例外を適用しない | `cmake --build <authority>/build-variants` が既存 `all("build-variants" in t)` 例外で通るのを防ぐ。cat/grep等は維持 | authority writer は拒否、pure reader は許可。既存 builder 受理は不変 |
| `hooks/guard_bash.py:2633-2649` | `main()` の raw/decoded 内部例外判定へ exact authority literal を追加 | 正常時だけ閉じても、rule exception 時に rc=0 なら防壁にならない | 内部例外時の authority mention だけ新規拒否 |
| `orchestrator/tests/test_hooks.py:1281` | guard_write/apply_patch の authority test 群を追加 | `_mk_fixture_repo`、`_edit`、`_patch` の既存様式に合わせる | テストのみ |
| `orchestrator/tests/test_hooks.py:1363` 直後 | authority path 定数と guard_bash detector matrix を追加 | `_WAL` 等と同じ test-local fixture 定数の置き場 | テストのみ |
| `orchestrator/tests/test_hooks.py:4218` | 両 guard の内部例外 exact-boundary test を追加 | `_guard_main()` と `patch.object(..., "decide", side_effect=...)` の既存様式を再利用 | テストのみ |
| `orchestrator/tests/test_hooks.py:4607-4645` | subprocess smoke matrix に authority deny、authority read allow、prefix sibling allow を追加 | `decide()` 直叩きだけでなく stdin JSON→exit code も固定する | テストのみ |
| `hooks/README.md:132-184` | hook 1/2 の対象集合へ固定 authority root と exact surface を追加 | 利用者が機械面を把握できるようにする | 文書のみ |
| `hooks/README.md:297-364` | authority 書込み防護の残余を独立 bullet で追加 | 「完全ロック」「署名偽造不能」という過大主張を防ぐ | 文書のみ |

`_hooks_tree_violation()` の実呼出しは、定義を除けば現状ちょうど **3箇所**、`2396`, `2423`, `2501` である。fast path の `2523-2534` は同関数の呼出しではなく正規表現と `_argument_hits_protected()` による別面である。

したがって (P1-c) の「同じ4箇所だけで足りる」には反対する。最低でも上記3呼出し、fast path、`main()` 例外面、`perf -o`、builder 例外を個別に扱う必要がある。

## 境界判定

用いる本判定は両 guard とも次の deny union とする。

```python
_inside(os.path.abspath(candidate), os.path.abspath(_AUTHORITY_ROOT))
or _inside(os.path.realpath(candidate), os.path.realpath(_AUTHORITY_ROOT))
```

`_inside(path, tree)` は両ファイルとも「`path == tree` または `path.startswith(tree + os.sep)`」なので、次を区別できる。

- 拒否: `/work/1/SFC/tanab/dev-wave-authority`
- 拒否: `/work/1/SFC/tanab/dev-wave-authority/key.pem`
- 許可: `/work/1/SFC/tanab/dev-wave-authority-copy/key.pem`
- 許可: `/work/1/SFC/tanab/dev-wave-authority2/key.pem`
- 許可: `/work/1/SFC/tanab/other/key.pem`

lexical と canonical の両側を取るため、root 内の symlink entry と、repo/tmp 側から authority 内を指す symlink alias の両方を拒否できる。

各既存述語の適否は以下のとおり。

- `_inside`: 使用可能。絶対化・正規化モードを揃えることが前提。
- `_hooks_tree_violation`: absolute lexical/canonical の作り方は参考にできる。ただし hooks 固有 root と `_HooksInodeIndex` を内包するため、そのまま authority 関数へ流用しない。
- `_repo_relative` / `_repo_relative_path`: 使用不可。repo 外絶対 path の絶対性を失う。
- `_LEAF_RE`: 使用不可。`search()` による leaf 名・部分 path 検査であり、固定 subtree の component boundary 述語ではない。
- `_TREE_LITERAL_RE`: 現行 alternative の一部は substring に近い。authority の bare文字列を追加すると `dev-wave-authority-copy` を hot にし得るため変更しない。
- `_MENTION_RE`: 同じ理由で変更しない。authority 専用の exact-boundary regex/token predicateを追加して OR する。

(P1-b) は lexical/canonical の二面には同意する。authority 全体の inode index を張らない判断も今回の限定 scope では妥当だが、「0700だから同一 uid の alias 攻撃に安全」という根拠には同意しない。同一 uid の既存 hardlink alias は lexical/canonical だけでは検出できないため、README の残余に明記する必要がある。

## repo 外 path の扱い

`guard_bash.py:2217-2228` の実装上、repo 外絶対 path は次のようになる。

```text
_repo_relative_path(
  "/work/1/SFC/tanab/dev-wave-authority/key.pem", repo
)
→ "work/1/SFC/tanab/dev-wave-authority/key.pem"
```

`2227` の `ap.strip("/")` により先頭 `/` が消える。`_repo_relative()` は `2239` でこれをそのまま呼ぶため同じ結果になる。

このため次は authority 判定へ転用できない。

- `_repo_relative_path()` / `_repo_relative()`
- それを前提にする `_campaign_tree_violation()`
- `_namespace_marker_violation()`
- `_tree_violation()` の ccbench/campaign 部分
- `_redirect_hits_protected()` の exploration 判定
- `decide():2562` の `marker_cwd`。repo 外 `cd` は絶対性を失い、その後の相対 path が repo 下として解釈され得る

さらに `/output/campaigns` のような repo 外絶対 path は strip 後に repo-relative protected path と同形になり得るため、単にこの戻り値と authority の相対文字列を比較する設計は誤拒否も起こす。

`guard_write.py` は候補を repo-relative 化せず、`classify_path():230-235` で absolute/realpath を保持する。この流儀と `_inside()` は repo 外 authority にも使用できる。

(P1-a) には同意する。固定 absolute module constant とし、argv・環境変数・repo root から導出しない。

## 受理集合の変化

変更前の受理集合を `A0`、追加拒否集合を `N` とすると、変更後は厳密に `A1 = A0 \ N` とする。

`N` は次の集合である。

- Write/Edit/MultiEdit/NotebookEdit の実書込 path が、lexical または canonical に authority root 自身・子孫となる呼出し。
- apply_patch の `Add File`、`Update File`、`Delete File`、`Move to` のいずれかが同 subtree に入る呼出し。move は source/destination の両方向を含む。
- Bash の redirect、delete、move、install、archive展開、rsync destination、未知 writer、conditional reader の書込み option が authority に入る呼出し。
- `perf -o/--output` が authority に入る呼出し。
- authority path と opaque構文・bare interpreter が同居する、既存方針に従った保守的拒否。
- guard 内部例外時に exact authority path が raw/decoded payload に存在する呼出し。

通常の `cat`, `grep`, `sha256sum`, `stat`, `git diff -- <authority path>` など、既存 allowlist が pure read と判定する形は精査へ入った後も許可される。

既存受理を増やさない根拠は以下。

- `_MENTION_RE`, `_TREE_LITERAL_RE`, reader allowlist、既存 deny 条件を削除・変更しない。
- authority 判定はすべて既存条件への OR、または独立した authority-only deny。
- 既存 `marker_cwd` は変更せず、authority 専用の絶対 cwd を並走させる。
- builder 例外は legacy leaf にだけ残し、authority へ拡張しない。
- sibling/prefix path は component-boundary predicate が false なので、従来の fast path/許可へ戻る。

(P1-d) の4変異だけでは不足する。少なくとも fast trigger、tree、argument、redirect、`main()` exception、`perf -o`、builder exception、lexical/canonical・cwd の独立 detector が必要である。

## production への影響

repo 全体を固定 root で検索した結果、実行コードの参照は2件だけだった。

- `tools/acceptance_receipt_signature.py:47-49`: 公開鍵固定 path
- `tools/acceptance_issuer_reference.py:92-94`: 秘密鍵固定 path

ほかは archive worklog と T-1984 の設計資料であり、production writer ではない。発行主体 root を固定 destination として作成・更新・削除する production 経路は repo 内に見つからない。

公開鍵は `tools/acceptance_receipt_signature.py:262-303` で `lstat`、`os.open(O_RDONLY | O_NOFOLLOW)`、`os.read`、`fstat` により読むだけである。Write系toolでもBash書込みでもないため影響しない。Bashで `cat` する場合も pure reader として通す。

秘密鍵も `tools/acceptance_issuer_reference.py:399-434` で `O_RDONLY` 読取りだけである。`_write_new():539-550` が書くのは caller 指定の receipt output で、authority 固定 path ではない。CLI の `--output` に authority を明示すれば別だが、それは現存する固定 production 経路ではなく、script/subprocess 内部書込みは元来 hook の観測外でもある。

したがって acceptance の現行受理集合を壊す固定 writer はない。ただし `acceptance_issuer_reference.py:4` 自身が production waiter/lander から未接続と明記しているため、「production issuer 全体を検査済み」とまでは主張しない。

## テスト設計

既存 helper に合わせ、guard_write は `_mk_fixture_repo()`、`_edit()`、`_patch()`、Bash は `GB.decide()`、entry point は `_guard_main()` を使う。authority 本体へは書き込まず、判定結果だけを見る。

**拒否の発火自体を固定するテスト**

- `test_t2146_guard_write_authority_all_surfaces_denied`
  - Write/Edit/MultiEdit/NotebookEdit × root自身/子孫。
  - `assert not ok` と authority 用 reason を確認。
- `test_t2146_apply_patch_authority_all_directives_and_moves_denied`
  - Add/Update/Delete/Move-to の全 directive。
  - authority→outside、outside→authority の move 双方向。
  - `assert not ok`、拒否 path が reason に含まれることを確認。
- `test_t2146_guard_write_authority_canonical_alias_denied`
  - temp symlink から authority を指す path を使用。
  - lexical が外でも canonical detector が発火することを確認。
- `test_t2146_guard_bash_authority_detector_matrix_denied`
  - fast: `printf x > <authority>/key`
  - tree: `rm -rf <authority>`
  - argument: `cp /tmp/x <authority>/key`
  - redirect単独: `cat /tmp/x > <authority>/key`
  - move: `mv <authority>/key /tmp/`
  - cwd: `cd <authority> && rm key`
  - canonical alias: alias pathだけを名指す writer
  - perf: `perf stat -o <authority>/perf.data -- true`
  - builder: `cmake --build <authority>/build-variants`
  - 各 case で `assert not ok`。それぞれ該当 detector を無効化すると少なくとも1件が赤になる形にする。
- `test_t2146_main_internal_errors_fail_closed_for_authority`
  - `GW.classify_path` または両 guard の `decide` を例外化し、authority payload が rc=2 になることを確認。

**特定条件で通ることを守るテスト**

- `test_t2146_guard_write_authority_component_boundaries_allowed`
  - `dev-wave-authority-copy`, `dev-wave-authority2`, 同じ親の `other` に対する Write/apply_patch。
  - `assert ok`。substring 判定への退行を捕える。
- `test_t2146_guard_bash_authority_reads_and_boundaries_allowed`
  - `cat`, `grep`, `sha256sum`, `stat` による authority 内読取り。
  - `cd <authority> && cat acceptance-issuer-public-key.pem`。
  - sibling/prefix path への `printf >`、`rm`。
  - いずれも `assert ok`。
- `test_t2146_main_internal_error_boundary_is_exact`
  - `dev-wave-authority-copy` を含む payload で synthetic exception を起こし rc=0 を確認。
  - 例外 fallback の regex だけが substring 化する退行を捕える。
- `test_hook_scripts_run_as_subprocess`
  - authority Write/apply_patch/Bash write は rc=2。
  - authority `cat` と sibling writer は rc=0。
  - 実配線と同じ stdin JSON→exit code を固定。

pytest は本段では実行していない。上記は静的設計であり、実測は親が行う。

## D374 手順との整合

現状では、D374 の「テスト先行 → guard_bash → guard_writeを最後に1回」はそのまま成立しない。

- テスト先行は可能。`orchestrator/tests/test_hooks.py` は hooks subtree 外。
- README は `guard_write.py:133-171` の exact README 例外が成立する限り Write/Edit系で更新可能。
- しかし現在の `guard_write.py:239-243` は `hooks/` subtree を既に拒否し、apply_patch も `310-325` で各 directive を `classify_path()` へ通す。
- したがって `*** Update File: hooks/guard_bash.py` は、guard_bash 自身をまだ変更していなくても現行 guard_write に拒否される。
- 同じ理由で、完成済み guard_write を最後に1回 apply_patch する操作も拒否される。

D374:5 の「有効化前の commit から作り直す」か、人間管理の一度きりの外部適用手順が必要である。一時無効化 flag、env、argv 上書き、pathを隠すGit操作を代替案にしてはならない。親 brief の N1 は初回 self-protection 導入時の手順を現在にも適用できると仮定しており、この点は修正が必要である。

## README の残余記述

README には次の上限を明記する。

- 閉じる面:
  - 信頼済み PreToolUse が観測する Write/Edit/MultiEdit/NotebookEdit。
  - apply_patch の全 exact directive。
  - Bash の path literal、token、redirect、既知optionとして観測できる直接書込み・削除・移動。
  - lexical/canonical に authority root へ入る path。
- 閉じない面:
  - `bash script.sh`、`python3 script.py`、`python3 -c` の内部。
  - 変数展開、persistent shell、IDE、cron、別process。
  - MCP/apps/plugins/子エージェントの別書込み面。
  - hook有効化前から存在する hardlink alias。
  - 同一uidそのものの権限。
- 特に、これは**読取り防護ではない**。
  - 公開鍵読取りは意図どおり継続する。
  - 秘密鍵読取りも `guard_write` / `guard_bash` では閉じない。
  - `guard_read` は repo内 docs/output の大容量読取りを抑える衛生層で、authority root や秘密鍵を守る正しさ防壁ではない。
  - よって「AIが署名を偽造できない」「発行主体を完全ロックした」とは書かない。
  - 言える上限は「観測可能な直接書込み面から authority subtree を追加で除外した」まで。

## 総括

(P1-a) は採用、(P1-b) は lexical/canonical 部分のみ採用し hardlink residual を明記する。(P1-c) と (P1-d) はコード実物と一致せず、3つの `_hooks_tree_violation` 呼出しに加えて fast path、例外fallback、`perf`、builder例外、repo外cwdを独立に扱う必要がある。

設計上は既存受理を増やさず authority への拒否だけを純増できる。一方、現行 self-guard 下では D374 の patch 順序そのものが実行不能なので、実装開始前に一度きりの適用経路を親側で確定する必要がある。ファイル変更とpytest実行は行っていない。