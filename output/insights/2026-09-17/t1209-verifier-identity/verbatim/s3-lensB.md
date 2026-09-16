## 所見

**B1 — consumer の実装変更は不要だが、plan の棚卸しは不完全。**

- **主張:** production／test の直接参照は網羅している。文書参照と間接 consumer の一部、shell の独立列挙が抜けている。
- **根拠:** 現物の直接参照は次のとおり。production／test の20出現という計数は正しい。

| ファイル | 行と用途 |
|---|---|
| `orchestrator/qualification/contract.py` | 39 定義、530 exact key set 検査 |
| `orchestrator/qualification/identity.py` | 27 import、140 required 集合生成 |
| `orchestrator/qualification/t126_driver.py` | 63 import、359 `tuple(sorted(REQUIRED_CODE_IDENTITY_PATHS))` |
| `orchestrator/tests/test_t126_pegasus_tools.py` | 704 import、980 fixture 生成、1026 コメント、1085 blob 読取り、1486・1487・1519・1522 包含／除外、1534 等価比較、1547 parameter 生成 |
| `orchestrator/tests/test_t126_qualification_contract.py` | 21 import、76 `path: "4" * 64 for path in REQUIRED_CODE_IDENTITY_PATHS` |
| `orchestrator/tests/test_t419_probe_causality.py` | 38 import、42 `set(_ENV_CONTRACT_IMPORT_CLOSURE_ADDITIONS) <= REQUIRED_CODE_IDENTITY_PATHS` |
| `docs/decisions.md` | 5478 集合整理についての決定記録 |
| `docs/archive/worklog-phase3-0801-100.md` | 94 同上 |
| `docs/archive/worklog-phase3-0810-377.md` | 41 変更集合との共通部分についての記録 |
| `docs/archive/worklog-phase3-0812-496.md` | 9 `submission.py` 自身を含むという記録 |
| `docs/archive/worklog-phase3-0816-587.md` | 21 集合についての記録 |

shell の識別子直接参照はない。ただし、plan が記載した `submit_t126_qualification.sh:124` の5 path追跡検査に加え、**同:149には7 pathの独立列挙**があり、:157で `cat-file blob "$SOURCE_COMMIT:$tracked"` とdisk hashを比較する。どちらも identity 全集合の複製ではなく、追加不要。

さらに `submission.py:216–217` の `build_series_preimage(...)` → `series_identity(preimage)` が取得入口。`collect_t126_qualification.py:33–44` は collector への委譲で独立集合なし。`t126_qualification.sh:495` はcommit全体をarchiveし、:787付近の個別hash列挙はprologue evidence用であり、37／40件依存ではない。

- **重さ:** should
- **是正案:** 上記の省略箇所を「確認済み・修正不要」と追記する。歴史文書を新しい件数へ書き換える必要はない。

**B2 — fixture 追加対応不要は成立する。ただし別の固定列挙fixtureも確認対象に含めるべき。**

- **主張:** `_attempt` の新3 pathについてblob欠落は起きない構造。別fixtureの固定列挙も今回の変更とは衝突しない。
- **根拠:** `test_t126_pegasus_tools.py:980` はrequired集合全体を走査し、新3 pathは:1024–1025の `path.write_text(f"fixture {relative}\n", encoding="utf-8")` に入る。:1050–1051の `git add .`／commit後、:1085–1088で各blobを読む。`_dependency` は:963の `source.txt` だけを持つgflags／glog用repoで、verifier集合を複製していない。
  
  一方、`test_t126_qualification_driver.py:98–114` の `_prologue_value` は `code_identity` を3 keyに固定する。これはprologue照合用の部分fixtureで、`t126_driver.py:881` の `identities = {**series_preimage["code_identity"], ...}` に渡すものであり、完全な `series_identity()` 検証用ではない。
- **重さ:** should
- **是正案:** `_dependency` と `_prologue_value` を棚卸しに追加し、後者を「完全preimageではないため純増の影響なし」と明記する。fixtureの実装修正は不要。

**B3 — loader drift の説明は正しいが、焦点走全体をcommit後に限定する必要はない。**

- **主張:** 未commit変更で赤になる実repo依存testと、fixture内で完結するtestを区別する。
- **根拠:** `contract_loader_binding.py:524–529` はHEAD blobとdiskを比較し、差異に `"contract-loader-drift: disk bytes が HEAD blob と不一致"` を返す。`test_p3_b4_raw_record_producer.py:111` の `_writer_authority()` がこれを直接呼ぶ。具体例は同:2207の `test_m09_stable_nonterminal_wal_is_not_classified_as_executed`。:2210の `_evidence_scope` → :387の `_copy_precursor_with_writers` → :158の `_writer_authority` に到達する。
  
  `test_t671_source_binding.py:321–325,443–459` は生成・commitしたfixture repoへ `_REPO_ROOT` を差し替える。新包含testも実repo bindingを取得しない。`test_t126_pegasus_tools.py:24` が指定する `ratified_enforcement_source` は `conftest.py:154–155` で `"Compatibility fixture: closure ratification has been retired."` とされた空fixture。
- **重さ:** should
- **是正案:** 親はcommit前に新包含testとT126焦点走を実施できる。実repo loader比較を含む受入は実装commit後に新プロセスで実施する。commitでこの差分由来のdriftは解消するが、他の失敗まで緑になる保証とはしない。

## 親 brief への指摘

**B4 — 「series identity が反応しない」と「path pin はloaderのみ」は範囲が広すぎる。**

- **主張:** 欠けているのは新3 fileの個別hashによる束縛。series identity全体が変更に反応しないとはいえない。
- **根拠:** `s1-brief.md:6` は「変更に series identity が反応しない」とするが、`identity.py:124–134` は `superproject_commit` とtree／gitlinkを検査する。commitした変更はcommit／tree経由でもidentityに影響する。また `contract.py:43` は `"orchestrator/qualification/contract.py"` 自身をrequired集合に含むため、brief:10の「path pin は…のみ」も字義どおりには誤り。
  
  `campaign_lock.py:107` は現行閉包、:204は `T733_EXACT62_CONTRACT_LOADER_RELATIVE_PATHS` 側であり、両方を現行閉包の同じ説明にまとめるのも不正確。
- **重さ:** should
- **是正案:** 「dsg/model/parseの個別code hashを記録・照合しない」に限定する。pin棚卸しはT126自己包含、現行loader閉包、歴史exact62閉包を区別する。

**B5 — 件数・fixture・DW-O10判断は支持できるが、不在証拠の一般化を抑えるべき。**

- **主張:** 主要な実測値は再確認できた。「live未実施」「壊れる成果物なし」の全域断定には資料の射程が足りない。
- **根拠:** AST計数はcode **37→40**、script **3のまま**、和集合 **40→43**。`core.py` は実際に `contract.py:75`、policyは:76、集合末尾は:77。変更前sha256／blobはbriefと一致し、完全hash文字列のtracked検索はともにhitなし。
  
  tracked JSONの文字列検索には7ファイルがhitしたが、JSONを解析すると**正確な `code_identity` keyは0件**だった。一方、`docs/phase3.md:1313` の記述は「live qualification は本項の scope 外」であり、これ単独ではrepo外も含む未実施証明にならない。
  
  `docs/dev-wave/operations.md:76–77` はDW-O10を「対象 producer の出力 bytes が変わりうるとき」「非凍結 producer 一般へ拡張しない」とする。今回の調査から凍結成果物再発行が必要になる証拠はなく、非適用判断を覆す材料はない。
- **重さ:** should
- **是正案:** 「tracked JSONに該当keyなし、調査範囲で既存qualification成果物を確認せず」と限定する。P4とDW-O10非適用は維持してよい。

## 変異 matrix への提案

**B6 — N1–N6の設計は有効。既存testとの差と実測集合を明記する。**

- **主張:** 新testの期待値はproduction集合から独立しており、要求された変異を検出する。N7はtest反転の確認、E1は等価対照として分離する。
- **根拠:** `s2-plan.md:87` のV名は同planの追加コードと一致する。変更前の現物にはまだ存在しない予定nodeである。既存node名は `test_t126_pegasus_tools.py:1527,1549` の定義と一致する。

| 変異 | 既存testでの検出 | 新test V | 期待 |
|---|---|---|---|
| N1／N2／N3：新3 pathを各1個削除 | 集合由来fixture・parameterも減るため、照合した既存testでは検出できない | 対応する包含assertが失敗 | KILLED |
| N4：core削除 | 同上 | core assertが失敗 | KILLED |
| N5：`parse.py` → `par se.py` | `test_every_required_identity_path_is_tracked_in_this_repo[orchestrator/verifier/par se.py]` が失敗 | 正しいparseの包含assertも失敗 | KILLED |
| N6：model行をcore行へ置換 | frozensetが39件になってもfixture・期待集合が追随する | model assertが失敗 | KILLED |
| N7：dsg assertを`not in`へ反転 | production欠落検出の証拠にはならない | 正常集合に対して失敗 | KILLED |
| E1：新test定義行末にコメント追加 | 意味の変更なし | 同じassertが通る | SURVIVED |

`test_every_required_identity_path_is_tracked_in_this_repo` は:1560–1562で実repoの `git ls-files --error-unmatch` を呼ぶ。新3 pathは今回のworktreeで実際にrc=0を確認した。同じcommitから作る通常の隔離worktreeでもtrackedであり、変異で集合を編集してもindex上の3 fileは失われない。

- **重さ:** should
- **是正案:** 変異走は次の焦点集合を同じ条件でbaseline／各変異に適用する。assert失敗とloader drift／実行環境エラーを分けて記録する。

`test_t126_pegasus_tools.py` に対する `-k` 候補:

```text
required_code_identity
or every_required_identity_path_is_tracked_in_this_repo
or series_preimage_exact_code_identity_set_tracks_activation_closure
```

関連回帰は `test_t126_pegasus_tools.py`、`test_t126_qualification_contract.py`、`test_t126_qualification_driver.py`、`test_t419_probe_causality.py` を対象とする。受入**全走**にはこの `-k` を持ち込まず、brief指定のacceptance経路で実施する。

## 総括

実装案の **3 path追加＋独立包含test 1本**は妥当。実装修正を要求するmust-fixは見つからなかった。

親が補うべき点はconsumer棚卸し、identityの効き方についての表現、loader依存testの実行順、変異結果の分類である。ファイル変更・pytest・変異実行は行っておらず、KILLED／SURVIVEDは静的な期待判定である。