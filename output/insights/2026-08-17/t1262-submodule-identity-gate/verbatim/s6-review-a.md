## 所見

**RA1 主張:** `_submodule_non_directory_files` は走査エラーを黙って無視するため、読取不能ディレクトリ配下の追加 bytes を見落として fail-open になる。  
**根拠:** `tools/codex_reasoning_ab.py:1444-1463` の `os.walk(..., onerror=None)` は子ディレクトリの `EACCES` を通知せず、そのディレクトリ自体も集合へ加えない。再現手順は、initialized child に `hidden/payload` を追加し `chmod 000 hidden`、`.gitmodules` を `ignore=all`、`enforce_closure=False` とするもの。この場合 tracked file の検査は通り、walk は `payload` を列挙できない。  
**深刻度:** must-fix  
**これを直さないと成果物のどの値・受理集合・参照がどう変わるか:** `verify_snapshot` の受理集合へ、canonical checkout に存在しない追加 bytes を持つ submodule が入る。

通常の FIFO、device、symlink-to-directory は現在の walk では `files` または `directories` の symlink 分岐で検出される。深い `.git` も root 以外は走査され、gitlink directory は親で飛ばしても initialized repository として再帰検査される。見つかった実効回避は、走査不能を理由化しない経路である。

**RA2 主張:** snapshot の config preflight は最初の repository Git 呼び出しより後なので、「config を内容検査より前に拒否する」という防壁を実装していない。  
**根拠:** `verify_snapshot` は `tools/codex_reasoning_ab.py:2060` で `_submodule_inventory` を先に呼び、同 helper は `:1094` の `ls-files`、`:1100` の `.gitmodules` config、`:1114` の worktree state を実行してから、`:2061-2069` の allowlist に到達する。裁定は `ruling.md:93-97` で object format、config、内容検査の順序を固定している。  
**深刻度:** must-fix  
**これを直さないと成果物のどの値・受理集合・参照がどう変わるか:** forbidden config は最終的に拒否されても、config 由来の外部 program が preflight 前に動けるため、snapshot・台帳入力・後続参照へ副作用を与えられる。

**RA3 主張:** source 側 allowlist は initialized child だけに掛かり、source root repository の forbidden local config を受理する。  
**根拠:** `_init_submodules_from_local_source` は `tools/codex_reasoning_ab.py:717-720` で source root を使用する一方、allowlist へ渡すのは `:738-740` の `local` child だけである。source root に `core.fsmonitor`、`filter.*`、`include.path` などを追加しても、この関数自身の allowlist では拒否されない。新設 source test も child config だけを変更している (`orchestrator/tests/test_codex_reasoning_ab.py:3169` 以降)。  
**深刻度:** must-fix  
**これを直さないと成果物のどの値・受理集合・参照がどう変わるか:** `_init_submodules_from_local_source` の source 受理集合が裁定より広くなり、禁止 config を持つ source が destination の初期化元参照として使われる。

`require_admin_within_snapshot=False` による dirty source の full 内容非検査自体は裁定どおりで、destination は後段の raw hash gate を通る。問題は、この緩和と同時に要求された source config 条件が root へ適用されていない点である。

**RA4 主張:** preflight の即時 `raise` は後続の既存理由を到達不能にし、従来の理由集合を単一の preflight 集合へ切り詰める。  
**根拠:** `tools/codex_reasoning_ab.py:2066-2069` で直ちに `ValidationError` を投げるため、`:2070-2156` の HEAD、branch、dirty、hash、closure、未初期化、manifest pin の理由は収集されない。親の 603 passed から現行 test の期待値破壊は観測されていないが、複合不整合時の診断集合は変わる。  
**深刻度:** nit  
**これを直さないと成果物のどの値・受理集合・参照がどう変わるか:** snapshot の受理集合は変わらないが、`ValidationError.reasons` とそれを記録する診断・台帳値が欠落する。

`_one_submodule_content_identity_reasons` の各 `return [...]` も後続理由を隠すが、最初の非空理由が必ず最終 rejection に入るため安全側であり、単独では内容改変を受理させない。`except Exception` も `_local_config_allowlist_reasons`、preflight、content helper のいずれも非空理由へ変換され、caller が raise または最終 raise する。例外関連の fail-open は RA1 の `os.walk` が例外を通知しない点だけである。

## 恒真判定

**RA5 主張:** RA1 と RA3 の拒否述語には新設 test がなく、該当防壁を追加または削除しても現在の新設 test 集合は差を検出できない。  
**根拠:** file-set test は通常の追加 regular file だけ (`orchestrator/tests/test_codex_reasoning_ab.py:2498-2530`) で、walk error、FIFO/device、symlink directory、深い `.git` を個別に固定しない。source config test は child のみで、root allowlist test は snapshot content helper に限られる (`:3020-3060`)。  
**深刻度:** must-fix  
**これを直さないと成果物のどの値・受理集合・参照がどう変わるか:** 変異 matrix が file-set と source allowlist を closed と誤認し、実際には広い受理集合を proof chain に載せる。

**RA6 主張:** verify-level preflight と「single reason」assert は謳う性質を test が固定していない。  
**根拠:** `verify_snapshot` の `:2061-2069` を削除しても、closure 有効・無効の両経路が後で `_submodule_content_identity_reasons` を呼び、config/object-format 拒否 test は緑のままになる。また `_assert_snapshot_rejected_with_single_reason` は名前に反して tuple equality ではなく membership だけを検査する (`orchestrator/tests/test_codex_reasoning_ab.py:2160-2168`)。  
**深刻度:** nit  
**これを直さないと成果物のどの値・受理集合・参照がどう変わるか:** 現在の受理集合は変わらないが、順序防壁と単一理由性の変異帰属が実装されていない状態でも受入証拠が成立する。

N1、N2、N3、N5、N6、N7、N8、N10、N11、N12 の主要述語は helper 直呼びの exact-list test がある。`snapshot not in repository.parents` も escaped-repository test (`orchestrator/tests/test_codex_reasoning_ab.py:3093-3108`) で固定されている。

## 裁定との不一致

**RA7 主張:** 「全 Git 呼び出しへ `--no-replace-objects`」という裁定は字義どおりには実装されていないが、内容を replace ref で差し替える実効経路は `diff-index` で閉じている。  
**根拠:** gate 経路の列挙は次のとおり。

- inventory: `ls-files --stage` は指定あり (`tools/codex_reasoning_ab.py:1305-1311`)、`.gitmodules` の `git config -f` はなし (`:864-875`)、`_git_dir` の `rev-parse --absolute-git-dir` はなし (`:771-773`)。
- worktree state: `show-toplevel`、`rev-parse HEAD`、absolute gitdir、common-dir は指定あり (`:964-975`, `:1032-1050`)。
- preflight/content: local config、object format、diff-index は指定あり (`:1384-1396`, `:1595-1604`, `:1470-1483`)。
- verify/既存 closure: root HEAD、symbolic-ref、status/diff、for-each-ref、remote、commit-graph、fsck、closure HEAD、cat-file、log、hash-object は指定なし (`:1736-1860`, `:2012-2082`)。
- source builder: destination config と `submodule update` は指定なし (`:746-765`)。

replace object の tree を実際に参照する新 gate は `diff-index HEAD` で、ここには指定がある。N4 test 自身も指定なしの `rev-parse HEAD` が original ID を返すことを assert しており (`orchestrator/tests/test_codex_reasoning_ab.py:2579`)、HEAD 表示側の option を外しても test は緑のままである。  
**深刻度:** nit  
**これを直さないと成果物のどの値・受理集合・参照がどう変わるか:** 現実の CCBench 内容受理集合は変わらないが、`ruling.md` §3 の「全呼び出し」という監査可能な契約と実装一覧が一致しない。

裁定 §3 との実質的不一致は、RA2 の検査順、RA3 の source root allowlist、RA1 の file-set fail-closed 性である。raw SHA-1、index/HEAD、tracked bytes、recursive repository、closure 無効枝、oracle field 不変は実装と裁定が一致している。

## 総括

NO-GO。raw tracked bytes と index/HEAD の中心 gate に直接の通過策は見つからず、早期 return と例外理由化も安全側である。  
ただし `os.walk` の無通知エラーにより、非 directory file 集合の完全性は保証できていない。  
さらに config preflight の順序と source root allowlist が裁定どおりではない。  
新設 test はこの 2 系統を検出せず、一部の「single reason」「preflight order」assert は恒真に近い。  
親の 603 passed / 21 skipped / failure 0 は参照したが、このレビュー自身は test を実走していない。