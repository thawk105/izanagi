read-only sandbox のため、`/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t139-manifest-land2-s2/s6-revA.md` へ保存できませんでした。以下が同ファイルへ保存すべき完成内容です。テストは実行していません。

# 段 6 レビュー A — 実装差分の正しさ境界

## 1. GO / NO-GO 判定

**NO-GO。must-fix 3 件。**

in-bound の明白な fail-open は静的には見つからなかった。一方、未裁定の `/usr/bin/git` 固定による恒真 deny、Git が許す remote 名を誤って拒否する parser、`http-alternates` 分岐を殺せない test 欠落がある。

## 2. must-fix

### MF-1 — 空白を含む remote 名の `promisor=false` を誤拒否する

**所見:** `git config --type=bool --get-regexp` は boolean 値を正しく `true` / `false` へ正規化するが、key と値の区切りが空白である。Git の subsection 名には空白を使えるため、例えば有効な設定 `remote."foo bar".promisor=false` の出力は `remote.foo bar.promisor false` となる。現実装の `split(maxsplit=1)` は値を `bar.promisor false` と解釈し、「解決結果が不正」と拒否する。実装子の「`remote.*.promisor=false` は受理する」という申告は一般には偽である。

**根拠:** `orchestrator/preregistration/blobref.py:343-366`、`orchestrator/tests/test_t139_blobref_git_trust.py:23-37`、`s5-impl.md:30-34`。ローカル Git 2.34.1 でも `remote.foo bar.promisor false` という出力を確認した。

**成果物影響:** canonical repository に空白を含む非 promisor remote があるだけで、D282 の固定 blob、approval payload、erratum composition がすべて解決不能になり、certified 選択の根拠参照が空になる。

**要求:** `-z` 等の非曖昧な形式で key/value を解析すること。空白・TAB を含む subsection の `false` 正例と `true` 負例を追加し、`yes/on/1/裸 key` と `no/off/0/空値` も Git の boolean 正規化と一致することを固定する。

### MF-2 — `/usr/bin/git` は未裁定の受理集合縮小である

**所見:** RP-2 (a) の逐語は「絶対 path 起動」であって「`/usr/bin/git` 固定」ではない。D282 の `operational_boundary` にも executable path や OS layout の制約はない。`/usr/bin/git` のない distro、container、Conda/Spack 配置では、入力にかかわらず `read_pinned_blob` が恒真 deny になる。`s5-impl.md` の設計判断は実装子自身の判断であり、裁定根拠にはならない。

**根拠:** `s4-adjudication.md:102-113`、`docs/decisions.md:12933-12939`、`s5-impl.md:22-28`、`orchestrator/preregistration/blobref.py:30,204,230-241`。

**成果物影響:** `/usr/bin/git` のない許容環境では全 BlobRef の受理集合が空になり、approval payload と composed preregistration を生成できない。

**要求:** land 前に、次のいずれかを明示的に裁定すること。

- canonical operational environment の trust root を逐語で `/usr/bin/git` に限定し、計算ノードを含む全対応環境の preflight/正例を置く。
- 親 `PATH` に依存せず、trusted deployment/build configuration から絶対 path を得て、その値の絶対性を fail-closed で検査する。

複数候補の無条件探索や親 `PATH` 復帰は要求しない。

### MF-3 — `http-alternates` の拒否分岐を殺す test がない

**所見:** 実装は `objects/info/alternates` と `objects/info/http-alternates` を別 marker として拒否するが、新規 test は前者しか構成しない。tuple から `http-alternates` だけを削る変異は全 test を生存できる。

**根拠:** `orchestrator/preregistration/blobref.py:307-318`、`orchestrator/tests/test_t139_blobref_git_trust.py:143-157`、`s4-adjudication.md:104-113`。

**成果物影響:** `http-alternates` を持つ repository が将来誤って受理集合へ戻っても検査が緑のままとなり、RP-2 (a) の外部 object-store 拒否を満たしたと誤記録する。

**要求:** otherwise-valid repository に `objects/info/http-alternates` だけを置く負例を追加する。M4 は通常 alternates と HTTP alternates の2変異へ分割する。

## 3. should-fix

### SF-1 — 8項目の test 実効性

| 項目 | 外したとき赤くなる既存 test | 判定 |
|---|---|---|
| `PATH` 非継承 | `test_parent_git_variables_are_scrubbed_and_hardening_reaches_every_call` | env assert のみ。絶対 path が残るため受理集合は動かない |
| 絶対 path 起動 | 上記 + `test_missing_fixed_git_path_has_identifiable_resolution_error` | argv/fail-closed pin。偽 Git の挙動 test は PATH 復帰との二層同時変異でのみ赤 |
| 全 `GIT_*` 破棄 | 上記 + 既存 `test_blob_resolution_does_not_inherit_git_repository_overrides` | `GIT_DIR` について挙動で発火する |
| `GIT_CONFIG_NOSYSTEM` | 上記 | env assert のみ。Git が system config を読まなかったことの証拠ではない |
| commit-graph 無効 | 上記 + `test_corrupt_commit_graph_is_not_consulted` | 後者は挙動 test だが、production が呼ばない `git log` を直接 `_git` に渡している |
| alternates/promisor 拒否 | alternates、promisor remote、promisor pack、partial clone の4件 | gate-specific exception を照合し、gate 除去時は otherwise-valid blob が受理される。ただし HTTP 分岐欠落 |
| `--no-pager` | argv/env test | argv 構築しか証明しない。stdout が常に非-TTYなので現実効性は示していない |
| fsmonitor 無効 | argv/env test + `test_fsmonitor_hook_is_not_executed` | marker による挙動証拠。ただし production が呼ばない `git status` の直接 test |

pager/NOSYSTEM の argv/env assert は「指定値を子へ渡した」証拠にはなるが、「攻撃が遮断された」証拠にはならない。mutation ledger では kill でなく structural/diagnostic pin と区別すべきである。

**成果物影響:** structural pin を acceptance gate の kill と数えると、実効防壁が無い変異を KILLED と誤記録し、certified 根拠の検査台帳が false-green になる。

**要求:** mutation ledger で区分を明記する。production に存在しない `log/status` 経路の test は、「全 `_git` 呼出しへの hardening propagation」を示す test として記録し、現行 BlobRef の受理防壁を直接示すと主張しない。

### SF-2 — 正常入力の未裁定縮小を test が覆っていない

変更前に受理され、変更後に拒否される入力クラスは次のとおり。

1. `PATH` 上には Git があるが `/usr/bin/git` がない、または `/usr/bin/git` が実行不能・非互換な環境。
2. `objects/info/alternates` または `objects/info/http-alternates` が存在する repository。空・dangling symlink・directory も存在だけで拒否する。
3. `objects/pack` に名前が `.promisor` で終わる entry がある repository。
4. `extensions.partialClone` が1値でもある repository。
5. Git boolean として真の `remote.*.promisor` がある repository。
6. alternates/promisor marker や pack directory の状態を検査できない repository。
7. objects path の出力が UTF-8 でない、埋込み LF を含む、または metadata 上限を超える repository。
8. 有効な `promisor=false` でも remote subsection 名に空白/TABを含む repository（MF-1）。

正常 repo と単純名の `remote.inert.promisor=false` は `test_normal_repository_remains_accepted` の fixture で正例化されている。ただし「全 false 値」を示してはいない。

**成果物影響:** 意図しない拒否クラスが canonical main に現れると、固定 preregistration blob の全 consumer が停止する。

**要求:** 少なくとも MF-1、LFを含む objects/common-dir path、boolean alias の正例を追加し、残る拒否クラスは意図した fail-closed かを親が記録する。

### SF-3 — TOCTOU は存在するが現行 operational boundary の外

alternates、pack marker、partial-clone/promisor config の検査と、後続の `cat-file` 読取は別 process・別時点である。検査後に同一権限 actor が marker/config/`commondir` を差し替えれば迂回できる。`rev-parse --git-path objects` 自体は scrub 済み `GIT_*` と top-level equality により親環境からは汚染しにくいが、repository admin state の同時変更には束縛されていない。

D282 は「同一権限の非協調 writer」を逐語で保証外としているため、これは今回の must-fix ではない。resolver source や `_GIT_EXECUTABLE` module 値の同一権限書換えも同じ境界外である。

**成果物影響:** 境界外 actor が競合すれば、検査後に外部 object store を差し込み、固定 blob の参照元を変えられる。

**要求:** 今回コードを広げず、段7記録で「atomic snapshot を保証していない」ことを operational boundary から継承する。

### SF-4 — PATH無しの Git 子 process と config 優先順位

現行 production command は `rev-parse`、`config`、`for-each-ref`、`cat-file`、`ls-tree` で、いずれも Git builtin である。pager、fsmonitor、promisor lazy fetch も明示的に無効化され、ssh、gpg、textconv、diff driver を起動する production 経路はない。したがって現行集合では PATH 不在による helper fallback は見つからない。

一方、private `_git` は arguments を制限していない。将来 external helper を要する command を足すと、PATH 不在時の失敗または platform default path への fallback が新しい挙動になる。

Git の config precedence では repository-local config とその `include.path` / `includeIf` はその config 位置へ展開され、明示的な `git -c` はそれらより高い command scope になる。したがって local config は `core.commitGraph=false`、`core.fsmonitor=false`、`core.useReplaceRefs=false` を上書きできない。

`extensions.partialClone` の rc 処理は正しい。0=存在して拒否、1=不存在として継続、それ以外=検査不能として拒否である。boolean も `--type=bool` が `yes/on/1/裸 key` を `true`、`no/off/0/空値` を `false` に正規化するため値判定自体は正しい。問題は MF-1 の key/value 分離だけである。

**成果物影響:** 将来 `_git` の command 集合が拡大すると、外部 helper の探索結果によって blob resolver の受理可否が環境依存になる。

**要求:** `_git` の production command 集合を閉じたものとして維持するか、helper を要する command 追加時の security review gate を残す。

### SF-5 — 既存 test と caller への波及

`_require_no_alternates_or_promisor` が先頭へ移ったため、alternates/promisor と shallow/replace/grafts を同時に持つ repository は新しい理由で先に落ちる。しかし既存 shallow、replace、grafts test は単一条件 fixture で、理由文字列も固定していないため期待理由は変わらない。

所有外 caller は次のとおり。

- `approval_payload.load_approval_payload` は `BlobResolutionError` を変換せず伝播する。
- `erratum.compose_core` は core と各 erratum の読取ごとに新しい gate を通す。
- package export の `read_pinned_blob` は signature・export 名とも不変。

固定 Git 不在の通常ケースは `git executable を解決できない` で他の Git 実行失敗と識別できる。ただし `is_file()` 後の消失や実行権限不足は一般の「固定 blob の Git 解決を実行できない」に入る。前者は同一権限 race として現行境界外である。

**成果物影響:** 新しい repository-state 拒否と fixed-path 拒否は3 consumerすべてへ伝播し、approval payload または composed core の生成を停止する。

**要求:** caller 側で拒否を握り潰さない現状を維持し、MF-1/MF-2 の正例を consumer test にも1本通す。

## 4. 変異の再導出

略記せず、期待する failing nodeid の完全集合を示す。

| ID | 再判定・最初に落ちる gate | 期待 failing nodeid 完全集合 |
|---|---|---|
| M1 `PATH` 復帰 | **kill から削除し structural pin へ。** 絶対 path 起動が同じ攻撃入力を遮断し続ける。最初に落ちるのは test の env assert | `orchestrator/tests/test_t139_blobref_git_trust.py::test_parent_git_variables_are_scrubbed_and_hardening_reaches_every_call` |
| M2 `_resolve_git_executable()` を `"git"` へ置換 | **保持。ただし PATH attack でなく fixed-path fail-closed mutation。** 最初は argv assert／missing-path positive escape | `orchestrator/tests/test_t139_blobref_git_trust.py::test_parent_git_variables_are_scrubbed_and_hardening_reaches_every_call`; `orchestrator/tests/test_t139_blobref_git_trust.py::test_missing_fixed_git_path_has_identifiable_resolution_error` |
| M3 `core.commitGraph=false` 削除 | **acceptance kill から diagnostic/propagation pin へ再分類。** production に ancestry command がない。最初は argv assert と直接 `_git(log)` | `orchestrator/tests/test_t139_blobref_git_trust.py::test_parent_git_variables_are_scrubbed_and_hardening_reaches_every_call`; `orchestrator/tests/test_t139_blobref_git_trust.py::test_corrupt_commit_graph_is_not_consulted` |
| M4a 通常 alternates marker 検査削除 | **保持・M4を分割。** `_require_commit_regular_blob` が alternate store の commit/blob を読み受理する | `orchestrator/tests/test_t139_blobref_git_trust.py::test_external_alternate_object_store_is_rejected` |
| M4b HTTP alternates marker 検査削除 | **追加、現状 SURVIVED。MF-3。** test 自体が存在しない | 現状 `∅`。追加後: `orchestrator/tests/test_t139_blobref_git_trust.py::test_http_alternate_object_store_is_rejected` |
| M5a `.promisor` pack marker 検査削除 | **M5を分割して保持。** local blob 読取まで進み受理 | `orchestrator/tests/test_t139_blobref_git_trust.py::test_promisor_pack_marker_is_rejected` |
| M5b `extensions.partialClone` 検査削除 | **M5を分割して保持。** local blob 読取まで進み受理 | `orchestrator/tests/test_t139_blobref_git_trust.py::test_partial_clone_configuration_is_rejected` |
| M5c `remote.*.promisor` 検査削除 | **M5を分割して保持。** local blob 読取まで進み受理 | `orchestrator/tests/test_t139_blobref_git_trust.py::test_promisor_remote_is_rejected` |
| M6 `--no-pager` 削除 | **kill から削除し argv structural pin へ。** stdout は非-TTYで、登録理由の「pager 出力汚染」は構成されていない | `orchestrator/tests/test_t139_blobref_git_trust.py::test_parent_git_variables_are_scrubbed_and_hardening_reaches_every_call` |
| M7 `core.fsmonitor=false` 削除 | **side-effect pin として保持。acceptance kill とは数えない。** 直接 `_git(status)` で hook marker が先に発火 | `orchestrator/tests/test_t139_blobref_git_trust.py::test_parent_git_variables_are_scrubbed_and_hardening_reaches_every_call`; `orchestrator/tests/test_t139_blobref_git_trust.py::test_fsmonitor_hook_is_not_executed` |
| M8 `GIT_CONFIG_NOSYSTEM` 削除 | **kill から削除し env structural pin へ。** system config の挙動負例はない | `orchestrator/tests/test_t139_blobref_git_trust.py::test_parent_git_variables_are_scrubbed_and_hardening_reaches_every_call` |
| M9 allowlistへ `GIT_DIR` 追加 | **保持。** attacker object database を見るため正常 blob が解決不能になる。既存 test も赤くなる | `orchestrator/tests/test_t139_blobref_git_trust.py::test_parent_git_variables_are_scrubbed_and_hardening_reaches_every_call`; `orchestrator/tests/test_t139_preregistration_binding.py::test_blob_resolution_does_not_inherit_git_repository_overrides` |
| M1+M2 二層同時変異 | **追加必須。PATH attack の実効 mutation はこれ。** 偽 Git marker、env/path、missing-path の3 nodeが赤 | `orchestrator/tests/test_t139_blobref_git_trust.py::test_path_pollution_cannot_execute_fake_git`; `orchestrator/tests/test_t139_blobref_git_trust.py::test_parent_git_variables_are_scrubbed_and_hardening_reaches_every_call`; `orchestrator/tests/test_t139_blobref_git_trust.py::test_missing_fixed_git_path_has_identifiable_resolution_error` |
| M10 曖昧な空白 split へ復帰 | **MF-1 fix後に追加。** valid false remote の正例が promisor parser で拒否される | `orchestrator/tests/test_t139_blobref_git_trust.py::test_remote_promisor_false_with_whitespace_subsection_is_accepted` |
| M-正例 | **保持。failing node集合は `∅`。** 現行の専用正例は単純 remote 名の false だけ | 必須 green anchor: `orchestrator/tests/test_t139_blobref_git_trust.py::test_normal_repository_remains_accepted`; MF-1後は `orchestrator/tests/test_t139_blobref_git_trust.py::test_remote_promisor_false_with_whitespace_subsection_is_accepted` も追加 |

M4とM5は同一入力ではなく別 gate なので統合しない。M4は2 branch、M5は3 branchへ分割する方が単一理由になる。

M1とM2の単独変異は同じ偽 Git 入力の acceptance を変えない。PATH attack の kill は二層同時変異だけを用いる。単独変異は structural pin または fixed-path failure pin として残す。

## 5. nit / backlog

must/should へ昇格できない nit はなし。

補足確認:

- working tree hash 等の揮発する診断 payload は新 test の期待値に焼き込まれていない。
- 既存 test の期待値緩和、skip、xfail、削除はない。
- 偽 Git marker は単独では原因が曖昧になり得るが、この fixture の偽 Git は marker 作成以外に正しい Git 出力を返さない。偽 Git が実行され marker 作成前に失敗しても test 全体は `actual == data` へ到達せず赤になるため、green の別原因にはなりにくい。
- owner/digest 検査、resolver source identity は確定裁定どおり要求しない。

## 総括

**NO-GO。must-fix 3 件。**  
最大 risk は、未裁定の `/usr/bin/git` 固定が対応環境によって全 BlobRef を恒真 deny にすること。  
加えて、有効な `remote.*.promisor=false` を remote 名の空白だけで誤拒否する。  
`http-alternates` 分岐には、それだけを外して赤くなる test がない。  
in-bound の明白な fail-open は静的には見つからなかった。