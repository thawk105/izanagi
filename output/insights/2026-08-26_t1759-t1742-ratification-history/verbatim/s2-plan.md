## 現行の受理・拒否挙動

`orchestrator/campaign/enforcement_source_ratification.py:265-328` は次の処理です。

- `git log --format=%H --reverse --full-history HEAD -- <ledger>` の各 commit を、台帳が改版された commit とみなします。
- 列挙順で blob を比較し、初回は最大 1 行、以後は直前 blob の厳密な byte 前置拡張かつ行数 `+1` を要求します。
- このため、一方の親だけが台帳を持つ merge は、結果の台帳が byte 不変でも新しい版として列挙され、`ratification history is not a strict prefix extension` で拒否されます。
- 分岐した 2 branch の追記も、DAG の親子関係ではなく列挙上の隣接 commit と比較するため拒否されます。
- 現行の否定例は以下の理由で拒否されます。

  - 行の置換: byte 前置条件違反。
  - 行の並べ替え: byte 前置条件違反。
  - 1 commit で複数行追加: 行数差が 1 でない。
  - 台帳削除: `cat-file blob commit:path` が失敗する。

- shallow 判定はなく、観測できない祖先を「存在しなかった」と扱える穴があります。
- replace object は `orchestrator/campaign/enforcement_source_ratification.py:31-39,171-176,197-203` で無効化されていますが、replace ref の存在自体と legacy graft は拒否していません。

## 新しい規則の定義

P1 はそのまま採りません。1 親 commit に「0 または 1 行増」を許す部分を「ちょうど 1 行増」に強めます。

具体的な反例は、親 `p` と子 `c` の台帳 blob が同一で、tree mode だけを `100644` から `100755` に変えた履歴です。この commit は path history に列挙され、現行検査は同一 blob のため拒否します。しかし P1 は `rows(c) == rows(p)` を許すため受理し、検出力が落ちます。通常の無関係な 1 親 commit は path history に列挙されないので、0 行増を許す必要はありません。

定義は以下とします。

1. `H` を検査開始時に捕捉した exact HEAD、`C` を現行と同じ `--reverse --full-history` path log の commit 集合とする。順序は安定出力のため残すが、判定は順序に依存しない。
2. 各 `c in C` について、path 制限なしの `git log -1 --format=%P <c>` から commit object の実親 `P(c)` を取得する。
3. 各 `c`、各実親、`H` の台帳 tree entry を取得する。存在する entry は mode、blob OID、`_load_rows(blob)` の行 tuple を持つ。存在しない entry は `None` とする。
4. `c` 自身の entry が存在しなければ、台帳削除として常に拒否する。
5. 台帳を持つ親が 0 個なら導入 commit とし、`len(rows(c)) <= 1` のみ受理する。root commit、通常 commit、全親が台帳を持たない merge のいずれも同じである。
6. 実親が 1 個で、その親が台帳を持つ場合:

   - tree mode は親と同一。
   - `rows(c)` は `rows(p)` の末尾に、ちょうど 1 行を追加したもの。
   - 0 行増、削除、置換、並べ替え、2 行以上の追加を拒否する。

7. 実親が 2 個以上で、少なくとも 1 親が台帳を持つ場合:

   - 台帳を持つ全親と子の tree mode は同一。
   - 各 `rows(p)` は `rows(c)` の部分列である。したがって親内の順序を保存する。
   - `set(rows(c))` は、台帳を持つ全親の行集合の和集合と完全一致する。
   - したがって merge での行追加、親の行の欠落、親内順序の変更をすべて拒否する。
   - 台帳を持たない親は空列として扱い、F600 型の merge を妨げない。

8. 検査結果は列挙末尾ではなく、捕捉済み `H` の行 tuple から `frozenset` を作る。これにより path log の表示順に依存しない。

既存否定例はすべて残ります。

- 置換と並べ替えは、1 親規則の厳密な末尾追記条件に違反します。
- 複数行追加は増分が 1 でないため拒否されます。
- 削除 commit は子 entry が `None` なので拒否されます。
- merge で片方の親の行を落とす場合も、親 tuple が子の部分列にならず拒否されます。

`_load_rows()` の出力と blob bytes の 1 対 1 性は、blob に限れば成立します。各行は固定 schema、canonical JSON、ASCII、改行終端であり、digest tuple から元 bytes を一意に再構成できます。ただし tree mode は blob bytes の外にあるため、この等価性だけでは P1 の 0 行増を正当化できません。tree entry の mode も比較対象に含めます。

## 実装計画 (file:line)

`orchestrator/campaign/enforcement_source_ratification.py` を次のように分割します。

- `:180-218` `_git`

  - `input_bytes: bytes | None = None` を keyword 引数として追加し、既存の `subprocess.run` に `input=input_bytes` を渡します。
  - subprocess 起動箇所は現在の `:197` の 1 か所だけです。`Popen` や別 helper の `subprocess.run` は追加しません。

- `:221-229` `_require_git`

  - 同じ `input_bytes` を `_git` へ伝播できるようにします。
  - 既存の失敗メッセージは変更しません。

- `:264` 直後に `_assert_full_history_repository(root)` を追加

  - `_committed_ratification_digests()` が `_validated_root()` を終えた直後、HEAD や履歴を読む前に呼びます。
  - `git rev-parse --is-shallow-repository` の出力が exact `false\n` でなければ拒否します。
  - `git rev-parse --git-path info/grafts` で graft path を取得し、存在または symlink なら拒否します。
  - `git for-each-ref --format=%(refname) refs/replace/` が 1 行でも返せば拒否します。
  - replace object は既存の `_GIT_HARDEN` と `GIT_NO_REPLACE_OBJECTS` でも無効化したままにします。graft は同じ方法では無効化できないため、存在拒否が必須です。
  - 新規メッセージ案:

    - `ratification history requires a non-shallow repository`
    - `ratification history cannot use Git grafts`
    - `ratification history cannot use Git replace refs`
    - 判定出力が exact でない場合は `ratification shallow-repository state is not exact`

- 現行 `:278-301` を `_history_commits(root, head)` に分離

  - 現行の `git log --format=%H --reverse --full-history` を維持します。
  - ASCII、40 桁 lowercase hex、重複なしを検査して tuple を返します。
  - 現行の commit ID 関連メッセージは維持します。

- 新規 `_real_parents(root, commit)`

  - `git log -1 --format=%P <exact-commit>` を pathspec なしで呼びます。
  - 出力を exact 1 行として検査し、各親が 40 桁 lowercase hex であることを確認します。
  - 新規失敗メッセージは `ratification parent query returned malformed output` と `ratification parent query returned an invalid commit ID` に固定します。

- 新規 `_ledger_entries_at_commits(root, commits)`

  - `H`、全 `c`、全実親を重複除去します。
  - 各 commit に `git ls-tree -z --full-tree <commit> -- <ledger-path>` を 1 回呼び、entry 不在と Git 障害を区別します。
  - entry がある場合は mode、type、blob OID、path を exact に検査します。type が `blob` でなければ `ratification ledger is not a blob in committed history` で拒否します。
  - blob OID を重複除去し、`git cat-file --batch` を既存 `_git` の `input_bytes` 経由で 1 回だけ呼びます。header、size、separator、EOF を厳密に解析します。
  - blob ごとに `_load_rows()` を 1 回実行し、同一 blob を持つ多数の merge では結果を再利用します。
  - batch 異常は `ratification git batch output is malformed` とします。

- 新規 `_is_subsequence(parent_rows, child_rows)`

  - 親 tuple の各要素を順番に子 tuple から消費する線形走査にします。
  - set 包含だけでは並べ替えを見逃すため、必ず順序検査と併用します。

- 新規 `_validate_history_node(commit, parents, entries)`

  - 上記の導入、1 親、merge 規則を実装します。
  - 既存メッセージを次の条件でそのまま使います。

    - 1 親で前置列違反または 0 行増:
      `ratification history is not a strict prefix extension`
    - 1 親で 2 行以上追加:
      `ratification history added more than one row`
    - 導入時に 2 行以上:
      `ratification history introduced more than one row`
    - 子 entry 不在:
      `ratification ledger was deleted in committed history`

  - merge 用の新規メッセージ:

    - 新規行あり:
      `ratification merge introduced a new row`
    - 親の行欠落または親内順序違反:
      `ratification merge did not preserve every parent row sequence`
    - mode 不一致:
      `ratification ledger mode changed in committed history`

- 現行 `:265-328` `_committed_ratification_digests`

  - root 検証、full-history 前提検査、HEAD 捕捉、history 列挙、実親取得、entry/blob 一括取得、各 node 検査、HEAD rows 返却だけを統括する関数にします。
  - `history` が空で HEAD に台帳がなければ空集合を返します。
  - history があるのに HEAD entry がなければ削除として拒否します。
  - 台帳 bytes、`_load_rows()`、closure digest、公開関数 `require_ratified_closure()` は変更しません。

spawn site pin は維持できます。`orchestrator/tests/test_ccbench_spawn_sites.py:81` の

`("campaign/enforcement_source_ratification.py", "<module>._git"): 1`

は変更しません。`cat-file --batch` は `_git` の既存 `subprocess.run` に stdin を渡して実行し、別 process 起動口を作らないためです。

性能は、`V` を path history の commit 数、`S` を `{HEAD} + history commits + 全実親` の重複除去後 commit 数とすると、

`N_git = 6 + V + S + I(blob が 1 個以上)`

です。固定 6 回は top-level、shallow、graft path、replace refs、HEAD、path history です。`V` 回は実親取得、`S` 回は単一 commit・単一路の `ls-tree`、最後の 1 回は重複 blob の batch 読みです。

base main は `V=17`。最初の導入が 0 または 1 親、残り 16 件が通常の 2 親 merge なので `S <= 51`、したがって最大 75 回です。各呼出しはローカル object store の単一 commit・単一路照会で、全史走査は 17 件の path log 1 回、batch 本文は現状 1 個の小さい blob だけです。静的には各呼出しの 10 秒 timeout を圧迫する形ではありません。ただし実測値ではなく、テスト実測は親が行う前提です。

将来 k 親 merge が 1 件増えると、process 数は最大 `k+2` 回増え、入力データ量は DAG の node/edge 数に線形に増えます。

## テスト計画

対象は `orchestrator/tests/test_enforcement_source_ratification.py` です。

`test_enforcement_source_ratification.py:94-117` の fixture helper 群へ、次を追加します。

- exact HEAD を返す helper。
- ledger と無関係な commit を作る helper。
- 指定した複数親と解決済み ledger rows から、`write-tree` と `commit-tree -p ...` で deterministic な merge commit を作る helper。通常 merge の conflict 挙動に依存させません。

追加 nodeid 案は以下です。

- `(a)` `test_enforcement_source_ratification.py::test_unchanged_ledger_merge_commit_is_not_counted_as_an_append`

  台帳導入前から分岐した side branch を、導入後の main に merge し、結果 blob が byte 不変であることと批准集合が維持されることを確認します。現行の T-1759 strict-prefix 誤拒否を殺します。

- `(b)` `test_enforcement_source_ratification.py::test_concurrent_branch_appends_are_accepted_after_merge`

  共通台帳から左右 branch がそれぞれ 1 行追記し、merge 結果を両行の共通 supersequence にします。返却集合が base、left、right の全 digest と一致することを確認し、列挙順を線形履歴として扱う T-1742 欠陥を殺します。

- `(c)` `test_enforcement_source_ratification.py::test_merge_omitting_one_parent_row_is_rejected`

  左右 branch の片方の追記を merge 結果から落とし、`merge did not preserve every parent row sequence` を要求します。最終 HEAD だけ、または親集合の片方だけを見る実装を殺します。

- `(d)` `test_enforcement_source_ratification.py::test_merge_adding_a_new_row_is_rejected`

  両親の和集合にない行を merge commit で追加し、`merge introduced a new row` を要求します。merge をレビューなしの追記口として使える実装を殺します。

- `(e)` `test_enforcement_source_ratification.py::test_shallow_repository_is_rejected`

  `file://` による `--depth=1` clone を作り、`non-shallow repository` を要求します。切断された祖先を不存在として扱う恒真化を殺します。

検出力後退用として、さらに次を追加します。

- `test_enforcement_source_ratification.py::test_single_parent_zero_row_path_change_is_rejected`

  `git update-index --chmod=+x` で同一 blob の mode-only commit を作り、従来の `not a strict prefix extension` 拒否を維持します。P1 の 0 行増をそのまま採る実装を殺します。

- `test_enforcement_source_ratification.py::test_history_rewrite_inputs_are_rejected[graft]`
- `test_enforcement_source_ratification.py::test_history_rewrite_inputs_are_rejected[replace-ref]`

  shallow だけを閉じ、実親を変更できる別経路を残す実装を殺します。

既存テストの期待値は変更しません。

- 削除: 現行 `:256-259`
- 置換: 現行 `:273-276`
- 並べ替え: 現行 `:291-294`
- 複数行追加: 現行 `:313-316`

既存メッセージをそのまま残すため、これらの `match=` 修正は不要です。

## 波及

- `orchestrator/campaign/contract_loader_binding.py:14,387-402`

  直接 consumer です。公開 API と例外 wrapper は変更なしです。履歴の構造的誤拒否が消えた後、未批准 closure は従来どおり `enforcement-source-ratification: enforcement-source-closure-unratified...` になります。

- `orchestrator/campaign/campaign_lock.py:29-55`

  `enforcement_source_ratification.py` 自身が closure path の `:49` に含まれるため、実装変更で closure digest は必ず変わります。既存批准行とは一致せず、manifest 再発行ではなく正直な unratified 拒否になります。codec 挙動への直接影響はありません。

- `orchestrator/tests/test_enforcement_source_ratification.py`

  直接 unit test です。新規 DAG、shallow、history override テストを追加します。既存期待値は維持します。

- `orchestrator/tests/conftest.py:158-232`

  `ratified_enforcement_source` fixture が一時 repo に 1 行の導入 commit を作ります。新規則の導入条件を満たすため、fixture 契約の変更は不要です。追加の read-only Git 検査だけが走ります。

- `orchestrator/tests/test_ccbench_spawn_sites.py:76-82,397-404`

  subprocess site の構造 pin です。`_git` の 1 site を維持するため影響なし、期待値変更なしです。

- `orchestrator/campaign/s8b_ratified_freeze.py:303-359` と `orchestrator/campaign/trial_registry.py:1144-1179`

  consumer ではなく shallow、graft、replace 拒否の先例です。コード変更はありません。

## 未解決・親へ返す論点

- P1 の「1 親で 0 行増」は採用不可です。mode-only path commit という具体的な検出力後退があるため、1 親はちょうど 1 行、merge のみ 0 行追加を許す規則へ変更するのが妥当です。
- blob bytes と行 tuple の 1 対 1 性自体は成立しますが、tree mode を含む tree entry との 1 対 1 性ではありません。mode を別途取得して親子間で固定する必要があります。
- graft、replace、shallow の存在確認は先行 module と同じ check-then-use 型です。検査中に graft を一瞬だけ作成して除去する並行攻撃まで脅威モデルへ入れるなら、repository state の排他または履歴 object の完全な plumbing 読みが別 wave で必要です。通常の安定した checkout を対象とする本 scope では、開始時拒否と replace の常時無効化で既存家法と同等です。

## 総括

P1 を一部強化し、実親ごとの DAG 遷移として検査します。1 親は従来どおり厳密な 1 行追記、merge は全親の順序を保存した正確な和集合のみ、導入は最大 1 行、削除と shallow、graft、replace は fail-closed です。

変更対象は production 1 file と test 1 fileで、台帳 bytes、`_load_rows()`、closure digest 定義、批准執行経路には触れません。subprocess spawn site も `_git` 1 か所を維持します。sandbox 条件に従い pytest は実行しておらず、本回答は指定資料の静的検査に基づく計画です。