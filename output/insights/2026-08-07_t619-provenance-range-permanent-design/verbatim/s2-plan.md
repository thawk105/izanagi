# 恒久形設計

基準は `HEAD = main = bb824d8b7fff427eb61d09cf3d9354359914c99c`。read-only の段2契約に従い、実装・pytest・履歴 checker 本走は行っていない。以下はコード精読と Git plumbing による静的結論であり、緑は主張しない。

用語を二義化しないため、以下では次を分ける。

- `S` = checker が選ぶ commit 集合。
- `G` = checker が rc=0 とする履歴集合。
- 規律2の要請は `S_old ⊆ S_new` かつ `G_new ⊆ G_old`、すなわち監査対象を減らさず、新しく green になる履歴を作らないこと。
- brief 35行目の「受理集合を広げる」と63行目の「commit gate の受理集合が広がる」は、前者を `S`、後者を `G` と読まないと向きが矛盾する。

`Anc(X)` は `X` 自身を含む祖先集合とする。

## brief M1〜M9 の再検証

| 項目 | 結論 |
|---|---|
| M1 | 正しい。base `50c1ef4e5078ba54e0d00cee18eb01ddb6c2149a` について、`--ancestry-path` あり・なしとも `policy..HEAD` は 1701件。 |
| M2 | 数値は正しい。`f85e16e2416197adc2c24b1af7784db9bb807b87` で 62対79、差17件。 |
| M3 | 正しい。implementation epoch `8c6d3f3bdc716c1ede8febb83ced1b0351a99118` で 1238対1240、差は `333605d6…` と `6a9c97c4…`。 |
| M4 | 正しい。両commitは base の子孫かつ HEAD の祖先だが、implementation epoch の子孫ではない。 |
| M5 | 正しい。`333605d6…` は `.py` 2本を含み、Codex は researcher/reviewer だけで author がない。`6a9c97c4…` は docs-only。 |
| M6 | verdict について正しい。ただし出力順まで順序非依存ではない。[テスト4558行](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t619-provenance-range/orchestrator/tests/test_check_ai_provenance.py:4558) は findings が入力順、4723行は最初に表出する例外も入力順と固定する。したがって `--reverse` は保存すべき。 |
| M7 | 正しい。テストから `_commit_range()` の直接呼出しは0件で、`--ancestry-path` の文字列も production 824行だけ。 |
| M8 | 正しい。[入口4–5行](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t619-provenance-range/tools/check_ai_provenance.py:4)、[PR-A02 15–16行](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t619-provenance-range/docs/provenance/audit.md:15)、[契約84行](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t619-provenance-range/docs/ai-provenance.md:84) は plain reachability 寄り。 |
| M9 | 正しい。6287 + 1361 + 1346 = 8994 bytes。entry上限6300の余り13 bytes、family上限9000の余り6 bytes。 |

補足が二点ある。

- P4 の「D221台帳が将来の全 legacy 違反の受け皿」は広すぎる。[checker 132–134行](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t619-provenance-range/tools/check_ai_provenance.py:132) が許す種別は `missing-ai-agent` と `missing-codex-author` だけで、scope/CAB/形式違反は台帳へ移せない。これらを受けるには D221 の schema 拡張と別のユーザー裁定が必要。
- T-618 は「裁定済み」だが未実装。現行テストは台帳6件を固定し、`3f2c43d7…` が未登録であることを明記している（[1323–1367行](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t619-provenance-range/orchestrator/tests/test_check_ai_provenance.py:1323)）。

## (A) 選択集合の恒久形

### 変更点

[checker 808–827行](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t619-provenance-range/tools/check_ai_provenance.py:808) を次の契約にする。

1. `_policy_commit()` は canonical Git DAG 上の base policy 導入commitを一意に解決する。
2. `_commit_range(None)` の集合を次で固定する。

   `S_reach(P,H) = {P} ∪ (Anc(H) \ Anc(P))`

3. 実際の変更面は824行から `--ancestry-path` だけを除く。
4. 826行の `[policy, *descendants]` は必ず残す。素の `policy..HEAD` は `policy` 自身を含まず、[契約6–7行](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t619-provenance-range/docs/ai-provenance.md:6) の「導入commit自身にも適用」を破るため。
5. `--reverse` は残す。`policy` は常に index 0、その後ろは Git の `rev-list --reverse policy..HEAD` の順とする。pre-policy fork上のcommitがpolicyより古い日時でも、policy前置を優先する。
6. 明示 `--range` の827行は変更しない。

現在の集合は

`S_line(P,H) = {P} ∪ {C | P ≺ C かつ C ∈ Anc(H)}`

であり、canonical DAG で `P ∈ Anc(H)` なら常に `S_line ⊆ S_reach` である。

### `_build_ancestry` の閉包

[846–902行](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t619-provenance-range/tools/check_ai_provenance.py:846) の構造は変更不要。

- `_build_ancestry()` は選択commitを exclusion なしの positive tip として `rev-list --parents --stdin` に渡すため、各tipの祖先閉包を再構築する。
- 通常の既定監査では `HEAD` 自身が `policy..HEAD` に入る。したがって閉包は `Anc(HEAD)` 全体であり、pre-policy side branchを選択集合へ足しても閉包穴は生じない。
- 890行の「閉包外は shallow / graft 境界だけ」という主張は、canonicalかつ完全な DAG ならさらに強く「閉包外parentはない」。shallow/graftを許す非権威経路だけ境界が残る、とdocstringを直す。
- `--topo-order` は親bitが子より先に確定するため必須で、変更しない。

### edge case

| 状態 | 恒久挙動 |
|---|---|
| `HEAD == policy` | `policy..HEAD` は空、返却は `[policy]`。 |
| HEADがpolicyの子孫でない | 通常は起こらない。`_policy_commit()` 自体がHEADから到達するcommitを検索するため。HEAD race、monkeypatch、replace/graftによる不整合なら rc=2 で停止し、無関係なHEAD履歴をpolicy下として監査しない。 |
| policy addが複数 | 現行の `commits[-1]` はDAGの一意な「最古」を保証しない。add hitのうち他の全add hitの祖先であるcommitがexact 1件ならそれを初回導入とする。削除後の直系re-addはこれで初回addへ畳める。独立lineage上のaddが複数なら時刻で選ばず rc=2。 |
| shallow clone | 権威ある既定 full-history と名乗れないため rc=2。baseが見えてもscope/implementation/CAB導入hitが境界下に隠れ、現行resolverが `None` でfail-openし得るため、単に「policyが見える」だけでは不十分。明示rangeは従来どおり非権威な可視部分の監査。 |
| graft / replace | `rev-list`、pickaxe、merge-baseが局所的に書き換えたeffective DAGを見るため、既定監査は rc=2。authoritative auditで元object DAGと置換DAGを混在させない。現行repoにはgraft・replaceとも0件。 |

これらのfail-closed preflightは `_commit_range(None)` の直前、すなわち808–827行の責務に置く。`--message-file` 分岐には入れず、その受理集合は変えない。

### 規律2の単調性

canonical完全DAG、一意policy、固定forward-correctionという上記前提では、緩む経路はない。

- 選択集合は厳密に追加方向。
- 既存選択commitのbase/scope/implementation/CAB判定は変わらない。
- forward correctionのtarget `6b64d217…` とcarrier `6d7141dc…` はともにbase policyの子孫で、targetはcarrierの祖先。旧集合ですでに両方選択済み。新集合追加により初めてtargetが現れて赤を相殺する経路はない。
- side branch上の余分な correction candidate が加わる場合はexact-one違反が増えるだけ。
- D221台帳は追加commitのfindingだけを既知へ分け、既存の新規findingを消さない。
- 826行のpolicy前置を落とす場合だけ、導入commit自身の監査が消える明確な緩和になるため禁止。

replace/graftや非一意policyを黙認すると上記証明が崩れるので、恒久形ではそこで停止する。

## (B) epoch 適用述語の恒久形

権威ある既定監査について、epoch `E` のreachability述語を次で統一する。

`R_E(C,H) := C = E または (C ∈ Anc(H) かつ C ∉ Anc(E))`

現行lineage述語は `L_E(C) := E ∈ Anc(C)`。両者の差は「EともCともHEADから到達するが、EとCが相互に祖先でない」commitである。

明示 `--range` は一意な権威tipを持たないため、既存のlineage述語を残す。`main` の[2043–2044行](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t619-provenance-range/tools/check_ai_provenance.py:2043) で、`rev_range is None` の場合だけ `HEAD` を権威tipとして `_audit_history()` に渡す設計にする。

### 4 epoch の現状と差分

| epoch | current SHA / 現行述語 | reachability差分 | 現行mainでの新規違反 |
|---|---|---:|---:|
| base | `50c1ef4e5078ba54e0d00cee18eb01ddb6c2149a`。`_commit_range` の選択自体がlineage。 | 1701対1701、差0 | 0 |
| scope | `2f0245c196f82dddef91a9966e19b78a4b3f62e9`。[626–631行](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t619-provenance-range/tools/check_ai_provenance.py:626) で解決し、942–947行で `E ≤ C` のときだけscope findingを採用。 | 1579対1579、差0 | 0 |
| implementation | `8c6d3f3bdc716c1ede8febb83ced1b0351a99118`。634–640行で解決、951–965行でlineage適用。 | 1238対1240、差2 | 1 |
| CAB | 現行repoの導入hitは `9b26b3bd3acc10df95ef6ef6684a91d2ff3fa2ec`。643–649行と893–902行でcommitごとの祖先hitを検出。 | 1182対1206、差24 | 0 |

implementation差分は次の2件。

- `333605d680ec15f3f74b00e9e2746ae317b85dc5` — `.py` 2本、Codex authorなし。新規違反。
- `6a9c97c46a4e6812c8966437a6b62b6a31b64521` — `docs/failures.md` のみ。implementation gate非該当。

CAB差分24件は次のとおり。

```text
0993115320b4f3a63dcfbab14a8e147c0d146e61
16e418bcc26b6a2c62668efd84a18f949d86a69a
17f1235d60a8052be99f761d50c68978cba14111
180d3c150b7d78f9e32323519d341655ba090690
3fa691b30b1007dedbcfdc64744cd41533254d21
43c4ec4c7ff658582f0584f104ce59f388552cc5
4a420b9b549a2732a53773adf178e6cfeafce3fd
4bcbc2c10f97d86369fd37332c63439316ff9bd1
5b650727ee653d1a60a7add4daa87c86cc7f24cd
6289711a40c7af909cfba368ea0c91f8d6590b2c
777744c351c729a9a613bf0d1ebea6963ca1bebf
82aa9576fccb51e6433a36a9d63035a4cc951951
8976c14aa585bc47278ec5d6637edbb105bfe6e5
8dab530d5c3f786da71ae62c2579d6f227b1f24a
ac03b29976659fc1873b5cafed75a5edc23ab9b7
bf0bb771de0054049392f161640dfa35b9f05945
c47a01a44ac7f773007f081630d8e03766b334ce
d8b017e14c7be39b69e581b5c64b5f63c3f93d07
d8ce273f8a3878f4dff52267b42c028dd13e45ad
eaa2dd2ae806983e186672c94faa738992c77ce4
efa3786833b41cb5c1ed6cd579063cfc7f8cbbb7
f214e3306cbe889b0b7d91b9dedf0f2c399a3447
fa4774cd5de5b81840984168d1ac12a15a3d16a6
fb9e9830eeb445027914ced71cb554d0d119273f
```

全24件について raw `Co-Authored-By` 数と隔離相当のcanonical parse数は一致した。したがってCAB新規違反は0件。

親が再測するmembershipコマンドは、epochを差し替えて次の形になる。

```bash
E=8c6d3f3bdc716c1ede8febb83ced1b0351a99118
git rev-list --count --ancestry-path "$E"..HEAD
git rev-list --count "$E"..HEAD
comm -13 \
  <(git rev-list --ancestry-path "$E"..HEAD | sort) \
  <(git rev-list "$E"..HEAD | sort)
```

個別commitの実装面とtrailerは次で確認できる。

```bash
git diff-tree --no-commit-id --name-only -r 333605d680ec15f3f74b00e9e2746ae317b85dc5
git show -s --format=%B 333605d680ec15f3f74b00e9e2746ae317b85dc5 |
  git interpret-trailers --parse
```

### file:line の設計面

- [846–866行](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t619-provenance-range/tools/check_ai_provenance.py:846): `_Ancestry` に権威tipを使う `R_E` 判定を追加する。既存 `is_descendant()` はlineage oracleとして残す。
- 626–649行: scope/implementation/CABのepoch resolverを共通化し、pickaxe hit群のうち他hitすべての祖先である一意rootをepochにする。時刻順は使わない。
- [905–973行](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t619-provenance-range/tools/check_ai_provenance.py:905): `_normal_commit_audit()` は既定監査だけscope/implementation/CABへ `R_E` を使い、明示range・逐次oracleは現在のlineageを保持する。
- [1019–1033行](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t619-provenance-range/tools/check_ai_provenance.py:1019): `_ledger_policy_is_visible()` も同じmode/tipを受ける。strict defaultでdetectorが壊れた際、`333605d6…` を誤って `policy-epoch-not-visible` と診断しない。
- [1040–1179行](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t619-provenance-range/tools/check_ai_provenance.py:1040): `_audit_history()` に権威tip/modeを渡し、normal audit・stale診断を同じ述語へ束縛する。
- [310–317行](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t619-provenance-range/tools/check_ai_provenance.py:310): `HistoryAudit` に、findingとは別の `epoch_lineage_gaps` をdefault空で追加する。空rangeの既存positional constructionは壊さない。
- 2054–2067行: gapをstdoutへ `epoch`, full SHA, `reachability-applied`, `lineage-not-descendant`, hypothetical finding数付きで公開してからrc分岐へ入る。gap自体はfindingに入れずrcを変えない。

現行mainのgap公開数は、base 0 + scope 0 + implementation 2 + CAB 24 = 26件になる。

### 3案比較

| 案 | `G`の変化 | 偽陽性 | 偽陰性 | D221 |
|---|---|---|---|---|
| lineage維持 | 現状維持。`333605d6…` もgreen側 | 真のlegacyを遡及拒否しない | policyを知って作られたside commitでもlineageにepochが無ければ見逃す。現にimplementation 1件 | T619由来の追加0 |
| reachability統一 | ledgerなしなら現行mainに新規1件。将来side branch違反も拒否 | epoch前に作られ後日mergeされた真のlegacyを拒否し得る。`333605d6…` が実例候補 | canonical完全DAG内のlineage-gapは解消 | `333605d6…` をgreenへ戻すなら1件追加・新規ユーザー裁定 |
| lineage + 診断のみ | rcは現状維持、gap 26件を公開 | rc上の偽陽性なし | gateの偽陰性は残る。consumerが無ければ警告だけになる | 追加0。ただし新しいstdout契約の決定が必要 |

恒久形としては2案目を推奨し、診断を併設する。3案目は裁定待ち期間の安全な暫定形にはなるが、`333605d6…` を既知のまま受理し続けるため恒久閉鎖ではない。

### Gitだけでepoch拘束を決める限界

同じDAGは、次の二つを区別できない。

- side commitがepoch導入前に作られ、長期間後にmergeされた。
- branchはepoch前にforkしたが、commit自体はepoch導入後に作られた。

author/committer dateは任意に設定・改変でき、信頼根拠にならない。reflogやbranch作成時刻もcommit objectに束縛されず、失効・非共有である。署名はobjectの同一性を認証しても、作者がどのpolicyを認識したかを証明しない。

厳密な時点拘束には、信頼できるtimestampまたはmerge時attestationが必要になる。これはP5/D205のプロトタイプ基準では過剰なので、新trailer機構は本設計に含めない。reachabilityは「HEADへ取り込まれた時点で現行policy下として扱う」という運用上の保守的近似である。

## (C) 一回性コストと移行

### 現行mainで新たに赤になるcommit

reachabilityを4 epochへ適用した場合、新規は次の1件だけ。

```text
333605d680ec15f3f74b00e9e2746ae317b85dc5
missing-codex-author
paths=
  output/insights/2026-07-28_t142-review-verbatim/count_abort_reasons.py
  output/insights/2026-07-28_t142-review-verbatim/count_frontier.py
```

commit messageには以下があるが、Codex authorはない。

- Claude author
- Codex researcher
- Codex reviewer

`6a9c97c46a4e6812c8966437a6b62b6a31b64521` はdocs-only。CAB差24件はすべて配置正常。base/scope差は0。

なお現行mainには、T619とは別に `3f2c43d7580b8c26724d90278589862057508965` が既存の新規違反として残る。

### D221台帳件数

- 現行コード: 6件。
- T-618: `3f2c43d7…` を追加する裁定済み・未実装。実装後は7件。追加ユーザー裁定は不要。
- T-619 strict: `333605d6…` をgreenへ戻すならさらに1件。現在からの最終形は6→8件。
- T619由来の増分は1件であり、`333605d6…` について新しいユーザー裁定が必要。
- ユーザーが台帳追加を拒む場合、台帳はT-618後の7件のままで、既定監査は `333605d6…` によりrc=1となる。
- PR-C01〜C03はtarget固定かつ消費済みなので、このcommitの救済には使えない。

### land順序

一時的な緩みを作らない順序は次。

1. T-618の裁定済み `3f2c43d7…` entryを先にlandしてよい。これは既裁定の独立変更。
2. base選択集合のplain化を、合成DAGテスト・edge preflight・decisionと同一commitでlandする。現行mainではmembership差0だが、将来に対してstrict。
3. reachability epoch変更は、`333605d6…` の裁定後に行う。
4. greenを保つ裁定なら、epoch述語・gap診断・`333605d6…` 台帳entry・台帳exact-countテスト・decisionを同一commitにする。
5. `333605d6…` entryだけを先にlandしてはならない。現行lineageでは期待findingが生成されず、stale `policy-epoch-not-visible` のrc=2になる。
6. epoch述語だけを先にlandすると既定監査が追加で赤になる。緩みではないが通常のland gateを通せないため、裁定済みentryとの原子化が必要。

`--message-file` の[2016–2041行](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t619-provenance-range/tools/check_ai_provenance.py:2016) とforward correctionはこの順序・変更面から外す。

## (D) テスト設計

### 既存被覆の境界

次の既存テストは本変更を検出しない。

- [762行](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t619-provenance-range/orchestrator/tests/test_check_ai_provenance.py:762): 既定監査だが直線履歴。
- [779・800行](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t619-provenance-range/orchestrator/tests/test_check_ai_provenance.py:779): 明示rangeのCAB非遡及。
- [862行](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t619-provenance-range/orchestrator/tests/test_check_ai_provenance.py:862): separate lineageだがmergeせず、明示singleton range。
- 1691行: range外known entryのstale判定。
- 2128行: correctionのselected-set要件。
- 3468行: default operation名とleaseだけでauditをmock。
- 4366行: 明示range helperのsite pin。
- 4701行: 空の明示range。

[4611行](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t619-provenance-range/orchestrator/tests/test_check_ai_provenance.py:4611) と4660行はbitset/oracle等価性を既に固定しているため、そこを新規検出力とは数えない。

### 新規 default membership テスト

[ヘルパ71–84行](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t619-provenance-range/orchestrator/tests/test_check_ai_provenance.py:71) の `_init_repo` / `_commit` をそのまま使い、現在の762行付近へ追加する。

合成DAGは次。

1. root commit `R` を作る。まだpolicy pathは追加しない。
2. `R` からside branchを作り、`AI-Agent` のない違反commit `S` を置く。
3. mainへ戻り、`docs/ai-provenance.md` を初めて追加するpolicy commit `P` をvalid messageで作る。
4. main上にclean commit `M` を置く。
5. sideを `--no-ff --no-commit` でmergeし、valid messageのmerge commit `H` を作る。
6. 前提として `P` は `S` の祖先でなく、`S` は `H` の祖先であることを固定する。
7. `_commit_range(None)` が、先頭 `P`、残りは正確に `rev-list --reverse P..HEAD`、かつ `S` を含むことをassertする。
8. default `main([])` が `S` のmissing-ai-agentでrc=1になることをassertする。

862–885行のbranch作成・switch形と、[4620–4634行](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t619-provenance-range/orchestrator/tests/test_check_ai_provenance.py:4620) のmerge作法を再利用できる。

この1 nodeには純増で三つの検出力がある。

- policy前置を落とす変異。
- `--reverse` を落とす変異。
- `--ancestry-path` を戻す変異。

`--ancestry-path` を戻すと `S` がmembershipから消え、membership assertで必ず赤になる。仮にそのassertを迂回してもend-to-endが期待rc=1に対しrc=0となるため、変異は二重にkillされる。

### epoch reachability テスト

base policy後・各sub-epoch前にbranchを分ける合成repoを追加する。これによりbase selectionにはside commitが既に入るので、選択集合変更とepoch述語変更を分離できる。

- implementation: sideで `tools/side.py` をClaude authorだけで変更し、mainでimplementation needleを導入してmerge。strict defaultはmissing-codex-author、明示singleton rangeは従来lineageのまま。
- scope: sideを同一role複数・scopeなし、mainで`scope=`を導入してmerge。strict defaultだけscope違反。
- CAB: sideを `SPLIT_CAB_NONE`、mainでCAB needleを導入してmerge。strict defaultだけCAB配置違反。
- 各nodeで `epoch-lineage-gap` のepoch名・full SHAも固定し、gapをfindingへ混ぜていないことをrcと別assertにする。

lineageへ戻す変異は各default nodeが期待rc=1に対してrc=0となりkillされる。

### 台帳・edgeテスト

- [1323–1367行](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t619-provenance-range/orchestrator/tests/test_check_ai_provenance.py:1323) は、T-618後7件、T-619裁定後8件へ段階的に更新する。
- 1370行のreal finding照合には、`333605d6…` が権威tip付きreachability modeでのみexpected findingを生むことを固定する。
- 複数addは「直系re-addなら最初のadd」「独立addならrc=2」の対を置く。
- shallow、replace、graftの既定監査rc=2を各1 nodeで固定する。明示rangeとmessage-fileが影響を受けないpositive controlも置く。

これらは設計であり未実装・未実走である。

## (E) 文書の所在

[check_docs 188–202行](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t619-provenance-range/tools/check_docs.py:188) の上限と現サイズは次。

| file | 現在 | 個別上限 | 余り |
|---|---:|---:|---:|
| `docs/ai-provenance.md` | 6287 | 6300 | 13 |
| `docs/provenance/correction.md` | 1361 | 1600 | 239 |
| `docs/provenance/audit.md` | 1346 | 1600 | 254 |
| family合計 | 8994 | 9000 | 6 |

したがって、この3文書は0 byte変更とする。現行本文は既に「導入commitからHEAD」「既定full-history」を述べており、plain化に必要な意味は欠けていない。

恒久記録の住所は次。

- 詳細な証拠・4 epoch差分・コマンド・偽陽性/偽陰性: `output/insights/2026-08-07_t619-provenance-range-permanent-design.md:1`
- 採用方針・D221移行・明示rangeをlineageのまま残す理由: [decisions末尾10661行後](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t619-provenance-range/docs/decisions.md:10661) に新Dをspool経由で追加。D221本文は書き換えず、後続決定から参照する。
- 実行契約の局所説明: `tools/check_ai_provenance.py` のmodule docstring 2–7行、`_commit_range` 820行、`_Ancestry` 846行、`_build_ancestry` 869行のdocstring。
- 仕様の実効pin: `orchestrator/tests/test_check_ai_provenance.py`。

family内の等価縮約は提案しない。6 bytesでは意味のあるreachability契約を書けず、安全義務を削って捻出する根拠もないため、削除対象・削減bytesは0である。

## 総括

推奨する恒久形は、**権威ある既定監査について4 epochすべてをreachabilityへ統一し、lineage-incomparable適用を非fatal診断として公開する形**である。

理由:

- baseだけplain、後続3 epochだけlineageという非対称を解消する。
- canonical DAG上のside-branch盲点を、selection層と適用層の両方で閉じる。
- 現行mainの一回性コストは新規違反1件に限定され、CAB 24件・scope・baseには新規違反がない。
- 真のlegacyを拒否し得る原理的限界を、gap診断とSHA単位のユーザー裁定で公開できる。
- message-file、forward correction、明示rangeの既存受理集合は動かさない。

ユーザー裁定が必要な項目:

- `333605d680ec15f3f74b00e9e2746ae317b85dc5` をD221へ追加して既知化するか、既定監査のrc=1を維持するか。
- 既定監査だけreachability、明示 `--range` はlineageのままとする境界を採用するか。
- `epoch-lineage-gap` はstdout公開・rc不変とするか。
- shallow / graft / replace / 非一意policyを権威ある既定監査ではrc=2とするfail-closed境界を採用するか。