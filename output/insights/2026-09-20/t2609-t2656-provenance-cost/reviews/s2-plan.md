## 変更一覧

**(a)〜(d) を採用候補、(e) は今回見送りとする。** 実装順は指定どおり (a)(b)(c)(d)(e)。ただし subprocess 累積時間は (c) 235.7 秒が (b) 210.6 秒を上回るため、この順は「親表→non-merge→merge」と検証を積み上げる順でもある。累積時間を wall の短縮予測として加算しない。

以下の行番号は現行ファイルのアンカー。`checker` は `tools/check_ai_provenance.py`、`tests` は `orchestrator/tests/test_check_ai_provenance.py` を指す。

| 候補 | 変更箇所 | 変更内容 |
|---|---|---|
| (a) | `checker:1848,1883,1904,1927` | `_Ancestry` の末尾へ既定 `None` の親表 `parents: dict[str, tuple[str, ...]] \| None` を追加。既存の positional construction を維持する。既存 `rev-list` 出力から検証済み親表を作る。 |
| (a) | `checker:1696,1938,2011` | `_commit_paths(commit, *, parents=None)` とする。`None` のときだけ既存 `_commit_parents(commit)` を呼ぶ。正常 authoritative 経路から親表の値を渡す。空 tuple は root を意味し、未取得と区別する。 |
| (b) | `checker:1632` 付近、`1696,1938,2490` | `_batch_nonmerge_paths` を追加。最終 `selected` 確定後、pool 起動前に対象 non-merge を一括取得。検証済み path 列だけを worker に渡す。 |
| (c) | `checker:1640` 付近、`1696,1938,2490` | `_batch_merge_parent_paths` を追加。親別の変更集合を一括取得し、`_intersection_path_set` 以下へ注入する。`_combined_diff_paths` は変更しない。 |
| (d) | `checker:1470,1481,1599,1611,1976,2011` | 両 validator に keyword-only `values=None` を追加。正常経路では `_normal_commit_audit` が一度取得した値を両方へ渡す。 |
| (e) | `checker:1262,2423,2450,2502` | 今回変更しない。監査単位の private dir 共有は別採用可能な設計として後述する。 |

**(a) は `_Ancestry` 案を選ぶ。** `%P` を message format に足す案は、`checker:1209` の三フィールド契約、`_CommitMessage`、破損出力 fixture をまとめて変更する。親情報を既に持つ `_Ancestry` 案なら、`tests:7312` の `%s`／`%B` 計数、`_batch_commit_messages(selected)`、`_commit_paths(commit)`／`_commit_parents(commit)` の既存呼出しを維持できる。

初回実装では **(a)(b)(c) の高速経路を authoritative に限定**する。非 authoritative の `--range` には repository guards の成立を仮定せず、従来の親・path 取得を残す。新しい拒否条件は足さない。`ancestry is None` の oracle も従来どおりとする。

(b)(c) の取得位置は `checker:2489` の後、`audit_one` 定義前。受領証の correction 判定で全史へ戻る可能性がなくなった後の `selected` を使い、初出順で重複だけ除く。取得対象は選択集合内の全 non-merge／merge とし、epoch 判定は従来の worker 内に残す。少量の余分な取得より、適用条件の二重実装を避ける。結果は監査一走内だけで共有し、保存しない。

親表構築は共通部品だが、(a) の `%P` 省略、(b) の non-merge 一括取得、(c) の merge 一括取得はそれぞれ独立に有効化・撤回できる。公開 CLI flag は作らない。

## git 呼び出しの exact argv と parse 規則

**(a) 親表**

新しい subprocess は不要。既存呼出しをそのまま利用する。

```python
["git", "rev-list", "--topo-order", "--parents", "--stdin"]
```

stdin も現行どおり、authoritative では固定 HEAD 一行。各行を `commit parent...` として読み、親順を tuple に保存する。

親表の検証条件は次のとおり。

- 非空出力の終端 LF、空行なし、各 token が完全長小文字 OID。
- commit OID の重複なし。40／64 桁の混在なし。
- 要求した根をすべて含む。
- 親表の key 集合と既存 ancestry index の key 集合が一致する。
- authoritative の完全閉包として、全親が index 内にあり、逆順走査で子より先に現れる。
- 親列は sort／deduplicate しない。

ここで検査するのは既存 ancestry の出力から作る**追加キャッシュ**。検査失敗は親キャッシュを `None` にし、既存 ancestry の成否や公開例外を別のものに置き換えない。

**(b) non-merge**

採用 argv は次とする。

```python
[
    "git", "diff-tree", "--stdin", "--root", "--no-renames",
    "-r", "--name-only", "-z", "--always",
]
```

stdin は対象 OID を初出順に一行ずつ、終端 LF 付きで渡す。`--no-commit-id` は付けない。

**実験 (1) への追加は `--always`。** 空差分でも見出しを必ず出すために必要である。指定実験だけでは空差分の見出し契約が確認できないため、実装段で root-empty／empty-commit fixture により Git 2.34.1 上の出力を固定する。成立しなければ本候補は採用しない。

parse は既存 `_git` と同じ text-mode decode／改行変換を通した後、NUL だけで分割する。

1. 終端 NUL を一個だけ除き、内部の空 token は拒否する。
2. 40／64 桁の小文字 hex token をすべて見出し候補とする。
3. 見出し候補列が要求 OID 列と**順序・件数込みで完全一致**することを要求する。
4. 見出し間の非 OID token を path 列として、出力順のまま保存する。
5. 最終結果の key 集合も要求集合と照合する。

`--always` によって各要求の本物の見出しが存在する条件では、OID と同形の path は見出し候補を余分に一個増やすため、要求件数に一致せず全体 fallback になる。**「次に期待する SHA だから見出し」とだけ判断する parser は採らない。**

要求ゼロ件は subprocess なしで `{}`。非空要求に対する空 stdout は失敗であり、全 commit の空差分とは解釈しない。

**(c) merge の親別集合**

```python
[
    "git", "diff-tree", "--stdin", "--no-renames",
    "-r", "--name-only", "-z", "--diff-filter=ACMRDTUXB",
    "--always",
]
```

stdin の各行は完全 commit OID を使う。

```text
<merge-commit> <parent-commit>\n
```

ここで二つの token は **tree OID ではなく commit OID**。文書上、後続 commit は先頭 commit の仮の親として扱われるため、これは現行の `diff parent commit` と同じ向きである。[git-diff-tree の `--stdin`](https://git-scm.com/docs/git-diff-tree#Documentation/git-diff-tree.txt---stdin)

同じ merge OID を一出力内で何度も見出しにしないため、**親番号ごとに batch を分ける**。

- batch 0：各 merge と第 1 親。
- batch 1：各 merge と第 2 親。
- 以下、octopus の最大親数まで。空 batch は起動しない。

各 batch 内では merge OID が一意なので、(b) と同じ見出し検証が使える。検証済み結果を、その batch の要求表 `merge → parent` に従い `(merge, parent_index, parent)` へ格納する。出力見出しには親 OID がないため、**出力だけで親 OID を再確認できるとは主張しない**。親対応は検証済み親表と exact stdin が担保し、実 Git 等価テストで確認する。

全 batch が成功してから結果を公開する。典型的な二親 merge 群なら 8,502 回をおおむね 2 回に置換する設計であり、「必ず 1 回」とはしない。

**(d) trailer 値の共有**

argv は変更しない。

```python
["git", "interpret-trailers", "--parse"]
```

`cwd=REPO`、継承環境、stdin の message、`splitlines()` と value の `strip()` をすべて維持する。

両 validator は次の判定にする。

```python
if values is None:
    values = _ai_agent_values(message)
```

`if not values` は不可。取得済みの空 list を再 parse してしまう。

正常 ancestry 経路では `checker:1976` の直前に一度だけ取得し、両 validator へ渡す。oracle では既存の呼出しを残す。`validate_implementation_author` の docs-only 早期 return は parse より前のままとする。

**(e) 見送り案の argv**

再検討する場合も現行の次の argv を維持する。

```python
["git", "-c", "trailer.separators=:", "interpret-trailers", "--parse"]
# no_divider=True の場合だけ "--no-divider" を追加
```

## fail-closed 検査と fallback

「一括取得の失敗」は新しい監査 finding にしない。**失敗した一括単位の部分結果を捨て、既存取得を本来の worker 内の位置で再実行する。**

| 候補 | fallback 条件 | 戻り先 |
|---|---|---|
| (a) | 親表の形・終端・OID・閉包・重複検査が不成立、親表なし、非 authoritative、oracle | `_commit_paths(commit)` → `_commit_parents(commit)` |
| (b) | git 非ゼロ終了、spawn／decode 例外、終端不正、空 token、見出しの不足・余剰・重複・順序違い・未知 OID、OID 型 path の衝突 | 全対象 non-merge の既存 `diff-tree` |
| (c) | (b) と同じ、親別 batch のいずれかが失敗、要求 pair の被覆不足 | **全親別 batch を廃棄**し、既存 `_paths_changed_from` × 全親 |
| (d) | `values is None` | 各 validator が従来どおり parse |

(b) と (c) は独立した取得単位とする。(b) 失敗で正常な (c) まで捨てる必要はないが、(c) 内で成功した一部の親だけを利用してはならない。

投機的取得が捕捉する例外は D2033 に合わせて `RuntimeError, OSError, UnicodeError`。実行中断を捕捉する広い `BaseException` は使わない。失敗理由を stdout／stderr に追加しない。

(d) の parser 失敗は値の欠落へ変換せず、従来と同様に例外を伝播させる。(d) は取得結果の共有であり、別 parser への fallback は設けない。

注入値は `None` と空結果を区別する。欠落した cache key を `[]` に置き換える実装は禁止する。取得成功の場合も findings の生成順、`pool.map` の selected 順、重複 selected の監査回数は変えない。

## 判定不変の論証

**(a)** `rev-list --parents` は親 OID を出し、`%P` も親 OID を表す。ただし履歴簡約・親書換えの条件を無視して同一とは言えない。今回利用するのは pathspec、除外 revision、履歴限定 option のない固定 HEAD からの完全閉包で、authoritative guards が grafts／replace／shallow を拒否した経路である。親順も保存する。[git-rev-list](https://git-scm.com/docs/git-rev-list)、[pretty-formats の `%P`](https://git-scm.com/docs/pretty-formats)

非 authoritative の `--range` では同じ guard を仮定できない。ここで等価性を拡張せず、(a)(b)(c) を従来経路へ戻す。`--range` の受理集合を変更しない。

**(b)** 指定実験 (1)(2) が、通常 non-merge における一括 name list と現行取得の対応を支持する。root は `--root`、rename 無効化・再帰・NUL 区切りは現行と同じ。`--always` は空差分の見出しを保持するためだけに追加する。path は sort せず、現行の出力順を保存する。root／空差分の補完検証は採用条件として残る。[git-diff-tree](https://git-scm.com/docs/git-diff-tree)

**(c)** 指定実験 (4)(4b) と commit-list の文書仕様により、`commit parent` は親→merge の比較として設計できる。tree pair と混同して行を反転しない。

仮に差分方向を反転した場合、A と D は入れ替わるが両方 filter に含まれる。rename/copy は `--no-renames` で無効。ただしこの対称性に実装を依存させず、現行と同方向を使う。将来 A／D の片側だけに filter を変更しても向きが保たれる。[diff-filter の定義](https://git-scm.com/docs/git-diff-tree#Documentation/git-diff-tree.txt---diff-filterACDMRTUXB82308203)

各親の name set が同じなら、その共通部分と sorted 順も同じになる。以後の `_combined_diff_paths` は argv、raw bytes、path ごとの実行、非空判定を含めて完全に維持する。D721 の pure-union 免除は導入しない。

**(d)** 現行でも同じ message を同じ repo cwd・環境・argv で二回 parse している。監査中の設定が不変という既存前提の下では、同じ値列を読み取り専用で共有して結果は変わらない。parse 位置は従来の `validate_message` 冒頭と同じ位置に保ち、CAB／waiver／path 取得より前という失敗順も維持する。

**監査全体**では、D2045 の受領証選択・correction fallback・canary・prefix 合成と、D908 の監査実行箇所を変更しない。新キャッシュは最終 `selected` の取得方法だけを変える。

なお、指定実験は出力の先頭を省略表示している箇所があり、全史 path の完全一致を既に証明した資料とは扱わない。また、D2045 と同様、資源障害による終了まで同一とする主張はしない。

## テスト計画

追加位置は主に `tests:7312` 前後。merge fixture は `tests:1577–1889`、生 commit fixture は `tests:7142`、受領証 fixture は `tests:7460` 前後を再利用する。

**(a)**

- `test_ancestry_parent_rows_match_show_parents`
  root、通常 commit、二親 merge、四親 octopus、HEAD 外の根、重複 selected で、親 tuple と `_commit_parents(oid)` の順序込み一致。
- `test_parent_cache_invalid_rows_fall_back`
  終端 LF 欠落、重複行、不正 OID、根欠落、閉包外親を注入。親 cache が全破棄され、従来 `%P` が実際に呼ばれることを確認。
- `test_range_and_oracle_keep_legacy_parent_acquisition`
  `--range` の shallow／graft／replace fixture と oracle で、新しい拒否や親表注入がないことを確認。

**(b)**

- `test_batch_nonmerge_paths_equal_legacy_in_order`
  通常・root・空 tree の root・empty commit、追加／削除／変更／type change／rename 相当、改行・tab・CR・非 ASCII を含む path。list の完全一致を比較する。
- `test_batch_nonmerge_always_emits_empty_headers`
  空差分を先頭・中間・末尾に配置。実 Git の完全 stdout と見出し件数を pin。
- `test_batch_nonmerge_hex_paths_discard_entire_batch`
  40／64 hex の path、次の要求 OID と同名の path、未知 OID と同名の path。fallback の subprocess 発火まで確認。
- `test_batch_nonmerge_invalid_output_restores_public_result`
  終端、余分 NUL、見出し欠落・重複・交換・未知 OID、非ゼロ終了、decode／spawn 例外を parameterize。先頭の違反 commit の path を偽って空にし、後続 record を破損させる。部分結果が使われず、finding・rc・stdout・stderr が旧版と一致することを確認。

**(c)**

- `test_batch_merge_parent_sets_equal_legacy`
  二親／四親、親別に異なる集合、一親との空差分、追加・削除・type change を含め、各親集合を `_paths_changed_from` と比較。
- `test_batch_merge_keeps_combined_diff_contract`
  side-only、離れた行の自動 merge、手動競合解消、invalid UTF-8 本文を既存 fixture で比較。候補列と `--cc` の exact argv・回数も旧版と一致させる。
- `test_batch_merge_late_failure_discards_all_parent_batches`
  最後の親 batch を破損させる。先に成功した親集合も捨て、全親を従来取得することを確認。
- `test_batch_merge_parent_slots_and_headers`
  同じ親を共有する複数 merge、octopus、selected 重複で、batch ごとの要求対応と件数を固定する。

**(d)**

- `test_normal_audit_reuses_agent_values_once`
  実装 commit で二回→一回、docs-only で一回のまま。
- `test_agent_values_none_and_empty_are_distinct`
  `values=[]` では再 parse しない。省略時は現行どおり。
- `test_shared_agent_values_preserve_validator_results`
  trailer 欠落、`none`、混在、重複、scope 違反、Codex author、Claude author、waiver、divider、ambient `trailer.*`／`core.commentChar` を parameterize。旧 validator の結果と完全一致。
- message-file、`_waiver_audit`、oracle の既存呼出し形と parser 失敗順を維持する回帰を追加。

**既存 pin と横断検証**

- `tests:7312` の `test_batch_subprocess_counts_and_selected_order` は**変更しない**。message の取得契約は今回変わらない。
- 新規 `test_path_batch_subprocess_counts_and_selected_order` に `%P`、non-merge batch、親番号 batch、従来 diff、`--cc`、repo parser を別々に計数する。
- 正常 authoritative の pin は `%P=0`、non-merge batch は対象ありなら 1、merge batch は非空親番号数、従来親別 diff は 0。fallback／oracle は旧取得回数を明示する。
- `tests:7295,7350,7390` 付近の比較 fixture は、message batch を無効化しただけで「全取得の旧版」と呼ばない。親・path cache と共有 values も無効化した比較を別途追加する。
- `tests:7510` 付近の warm receipt は、追加 path batch がゼロで canary が残ることを確認。correction による全史 fallback では、確定後の selected 全体だけを一括取得する。
- 小 fixture の全組合せと、固定全史の旧版／新版で `HistoryAudit`、rc、公開 stdout／stderr を比較する。既知 56 件、post-baseline 3 件は件数だけでなく OID・finding kind/value で照合する。

今回は静的確認のみ。実装後の実走では対象テスト、既存 checker テスト、全史等価確認を行い、その後に親 brief の改善前後比較へ進む。

## 変異候補

行は現行の挿入・変更アンカー。**以下は期待 kill であり、実行済みの結果ではない。**

| 対象 | 変異 | 期待 kill 理由 |
|---|---|---|
| (a) `checker:1698` | `parents is None` を falsy 判定へ変更 | root の `%P=0` pin が破れる |
| (a) `checker:1904` 付近 | 親を第 1 親だけ保存 | octopus の親列一致、手動解消の finding が破れる |
| (a) `checker:2011` | cache miss を空親列として注入 | fallback 発火と merge 違反検出が破れる |
| (b) 新 helper | `--always` を削除 | empty-commit 見出しと正常 batch 回数 pin が破れる |
| (b) 新 parser | 終端・件数・OID 順序検査を各々削除 | 対応する破損 fixture が fallback 不発を検出 |
| (b) 新 parser | OID 型 path を通常 path／期待見出しとして無条件受理 | hash-name 衝突 fixture が kill |
| (b) 新 helper | 後半失敗時に前半辞書を返す | 先頭の既知違反を隠した fixture が結果差を検出 |
| (b) `checker:1704` 付近 | path を sort／set 化 | 順序込み等価テストが kill |
| (c) 新 helper | 一親を省略、別親の集合を複製 | 親別 exact set と手動解消 fixture が kill |
| (c) 新 helper | 最終 batch 失敗でも先行結果を使う | 全親の legacy 呼出し pin、違反検出比較が kill |
| (c) `checker:1693` | intersection を union に変更 | side-only merge が偽陽性になる |
| (c) `checker:1710` | `--cc` を省略、または常に空を返す | 自動 merge／手動解消／D721 関連の既知違反比較が kill |
| (d) `checker:1481,1611` | `is None` を falsy 判定へ変更 | 空 values の parser 回数 pin が kill |
| (d) `checker:1976` | 別 commit の values を共有、または `["none"]` を注入 | 異なる message の混在 fixture と既知違反検出が kill |
| (d) `checker:1325` | cwd を隔離 dir に変更 | repo-local config の等価 fixture が kill |
| 共通 `checker:2490` | receipt 再選択前の集合を注入 | correction による全史 fallback の被覆比較が kill |

方向反転だけは、現在の全 status filter と name set では等価変異になりうる。判定差による kill を捏造せず、exact stdin 契約のテスト対象とする。

## 見送りと理由

**(e) private dir の監査単位共有は今回は見送る。** 74 秒は tempdir 等を含む関数累積差であり、32 worker の wall 短縮量ではない。(a)〜(d) より先に監査 context の伝播と寿命管理を増やす根拠が弱い。

再採用する場合の設計は次とする。

- `_audit_history` が監査専用 holder を所有し、最初の parse 時だけ lock 下で `TemporaryDirectory(dir=TRAILER_PARSE_TEMP_ROOT)` と子 `cwd` を作る。
- authoritative canary も同じ holder を使い、warm receipt でも省略しない。
- worker には holder を明示的に渡す。監査間で共有する module-global cache や、親 thread から自動伝播すると仮定した context は使わない。
- `cwd` は常に `private_dir/cwd`、`GIT_CEILING_DIRECTORIES` は現行どおり親の `private_dir`。両者を同じ path に変更しない。
- stdin→stdout の `interpret-trailers --parse` を維持し、in-place option・入力ファイルを渡さない。空 cwd が維持されることを並行 fixture で確認する。
- pool の終了・全 worker join 後に finally で削除する。失敗時も同じ寿命とする。
- message-file と holder のない直接呼出しは同じ `_isolated_parsed_trailers` の per-call dir 経路を使う。`TRAILER_PARSE_TEMP_ROOT` は lazy 作成時に参照し、テスト差替え契約を維持する。

再採用時は dir 作成回数、複数監査の分離、例外時 cleanup、canary、temp root 差替えを試験し、ceiling 削除・早期 cleanup・global 化を変異対象にする。

**`%(trailers)` 置換と `_ai_agent_values` の cwd 変更も見送る。** micro 実験は提示された message で出力が一致した証拠であり、repo-local `trailer.*`／`core.commentChar` 全体の等価性ではない。P1 に反論する根拠はない。

**dispatch と受領証仕様は変更しない。** `main:3391–3520`、`login_headroom.grant_budget`、authoritative 述語、受領証の束縛・失効規則は T-2656 の変更対象外。

資料上、`D2148-item8.md` の実体は T-2547 の B-4 裁定であり、brief が述べる timeout 裁定とは一致しない。この資料から timeout 方針を補完・推定しない。

## 総括

(a) は親表再利用、(b)(c) は検証済み path 一括取得、(d) は同一 parse 結果の共有として採用を提案する。(e) は見送る。

採用上の主要条件は、**空差分にも見出しを保証すること、OID 型 path の衝突で全体 fallback すること、merge の全親集合と `--cc` 判定を保持すること**。非 authoritative と oracle の親・path 取得は従来経路を残す。

指定資料を読んだ静的計画であり、実装・pytest・変異・性能測定は未実施。判定等価と 480 秒以内の達成は、実装後の検証結果として確定する。
