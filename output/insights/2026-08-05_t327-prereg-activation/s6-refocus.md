## 対応表

| 所見 ID | 判定 | 根拠 `path:line` | 一言 |
|---|---|---|---|
| rev1-1 | closed | `orchestrator/campaign/s8c_preregistration.py:1479-1490,1512-1540`、`orchestrator/tests/test_s8c_preregistration_core.py:687-690` | production API の `registry=` は消え、core/evaluator の live bytes 不一致も fail-closed になった。 |
| rev1-2 | closed | `orchestrator/campaign/s8c_preregistration_evidence_contract.v1.json:42,71,114,150,191,228,264,300,332,374,427,485`、`orchestrator/campaign/s8c_preregistration_evidence.py:618-666,699-707` | 現 contract は12件すべて `machine_checkable:false`。production evaluator に `SATISFIED` 経路は0件である。 |
| rev1-3 | closed | `orchestrator/campaign/s8c_preregistration.py:35-36,1048-1059`、`output/s8c-preregistration/condition-freeze/condition-freeze.v1.g1.json:1` | freeze ledger は専用 subdirectory に分離され、運用 artifact namespace と衝突しない。 |
| rev1-4 | partial | `orchestrator/campaign/s8c_preregistration.py:1207-1228`、`orchestrator/tests/test_s8c_preregistration_core.py:571-596` | path と fence decoy は閉じたが、HTML comment 内の偽見出しを authority にできる。新規所見3。 |
| rev1-5 | partial | `orchestrator/campaign/s8c_preregistration.py:216-274`、`orchestrator/tests/test_s8c_preregistration_core.py:701-719`、`docs/phase3-8c-preregistration.md:158-161` | frozen/tuple/guard は入ったが、module-global `_construct_effective` に偽 `effective=True` report を渡す経路は残る。親裁定どおり Python 型は trust boundary ではない。 |
| rev1-6 | closed | `orchestrator/campaign/s8c_preregistration.py:706-735`、`orchestrator/tests/test_s8c_preregistration_core.py:360-382` | `null`、空文字列・空 container・placeholder 等価文字列は拒否される。欄別 schema は T-295 の scope 外。 |
| rev1-7 | partial | `orchestrator/campaign/s8c_preregistration.py:52-56,381-394,438-578,796-822`、`orchestrator/tests/test_s8c_preregistration_core.py:240-278` | standalone fence と node kind は保護したが、list-container fence で同一 hash の意味変更が残る。新規所見1・2。 |
| rev1-8 | out-of-scope | `/work/1/SFC/tanab/dev-wave-jobs/t327-prereg-activation/s6-fix-ruling.md:42-47`、`orchestrator/campaign/s8c_preregistration_evidence.py:618-666` | U-8。実装したふりはなく、12件すべて意図的に undefined のまま。U-1〜U-7も `docs/phase3-8c-preregistration.md:158-161,184-204` で未結線・残余として扱われる。 |
| rev1-9 | closed | `orchestrator/campaign/s8c_preregistration.py:1188-1204,1492-1497`、`orchestrator/tests/test_s8c_preregistration_core.py:521-527,629-647` | m01 は全12位置、m14 は merge 遷移を単独で撃つ負例になった。 |
| rev1-10 | closed | `orchestrator/tests/test_s8c_preregistration_predicates.py:376-409`、`orchestrator/campaign/s8c_preregistration_evidence.py:618-666` | 旧 no-op green fixture は充足不能へ反転した。token/no-op だけで production SAT にする経路はない。 |
| rev1-11 | closed | `/work/1/SFC/tanab/dev-wave-jobs/t327-prereg-activation/brief.md:34-55` | P3 の理由を compact canonical contract に限定し、DW-O09 の query・hit・分類を記録した。 |
| rev1-12 | closed | `orchestrator/campaign/s8c_preregistration.py:84-91,840-866,1023-1139`、`orchestrator/tests/test_s8c_preregistration_core.py:739-776` | timeout と generation/commit/blob 等の上限は実装された。ただし一部 guard は未試験。新規所見7。 |
| rev1-13* | closed | `/work/1/SFC/tanab/dev-wave-jobs/t327-prereg-activation/s6-rev1.md:3-19`、`/work/1/SFC/tanab/dev-wave-jobs/t327-prereg-activation/brief.md:49-57` | rev1 本文の所見見出しは1〜12のみ。依頼上の13はトレーサビリティ項目13「DW-O09」と解し、対応済みと判定した。 |
| rev2-1 | partial | `orchestrator/campaign/s8c_preregistration.py:264-274,1520-1532`、`orchestrator/tests/test_s8c_preregistration_core.py:701-712` | 公開注入は閉じたが、private test report と `_construct_effective` の組合せで genuine capability は作れる。F5 の明示的残余。 |
| rev2-2 | closed | `orchestrator/campaign/s8c_preregistration_evidence.py:618-666,699-707`、`orchestrator/tests/test_s8c_preregistration_predicates.py:98-104,393-409` | 現 repository に対し SAT は静的に0件。no-op/token fixture も `EVIDENCE_UNDEFINED` になる。 |
| rev2-3 | partial | `orchestrator/campaign/s8c_preregistration.py:1207-1228`、`tools/check_docs.py:3184-3199` | canonical path 制限は入ったが、双方とも HTML comment を可視見出しとして数える。新規所見3。 |
| rev2-4 | closed | `orchestrator/tests/test_s8c_preregistration_invariant.py:59-82,98-168` | helper 自体は temporary index に `add -A` して候補 commit を合成し、その commit を検査する。ただしその性質を守る負例がない。新規所見4。 |
| rev2-5 | partial | `docs/phase3-8c-preregistration.md:142-144`、`orchestrator/campaign/s8c_preregistration.py:1395-1438,1479-1490`、`orchestrator/campaign/s8c_preregistration_evidence.py:18-21` | C の blob と live file の一致は要求するが、C の隔離 evaluator を実行してはいない。旧 C の再評価と import-name による nominal type 分裂は残る。 |
| rev2-6 | closed | `orchestrator/campaign/s8c_preregistration.py:1492-1497`、`orchestrator/tests/test_s8c_preregistration_core.py:629-647` | `all→any` を全12位置の混合 status が殺す。 |
| rev2-7 | closed | `orchestrator/campaign/s8c_preregistration.py:706-735`、`orchestrator/tests/test_s8c_preregistration_core.py:360-382` | 意味的空値による §5 迂回は閉じた。 |
| rev2-8 | closed | `docs/phase3-8c-preregistration.md:27-40` | 受理には「C で発効」と「C が測定 HEAD／結果 commit の祖先」の両方を要求している。 |
| rev2-9 | closed | `docs/spool/decisions/2026-08-05-dev-wave-t327-prereg-activation-1.md:9-29` | D116(1) の supersede 境界を標準 spool fragment に記録した。land 時の fold はなお必要。 |
| rev2-10 | closed | `orchestrator/tests/test_s8c_preregistration_predicates.py:98-128` | 安全 invariant「SAT=0」と更新契約付き reason snapshot が分離された。 |

## 新規所見

### 1. 同じ normalization v2 の意味が fix2 で変更されている

**主張:** fix2 は fence parser の受理・拒否と canonical form を変更したが、`normalization_version` は `s8c-prereg-markdown/v2` のままである。同じ version を名乗る verifier が同じ bytes に異なる結果を返す。

**根拠:** `NORMALIZATION_VERSION` は単一定数であり、全世代 record に現在値との一致を要求する (`orchestrator/campaign/s8c_preregistration.py:43,937-950`)。g1 も v2 を名乗る (`output/s8c-preregistration/condition-freeze/condition-freeze.v1.g1.json:1`)。一方、fix2 は opener/closer の意味変更と g1 非再生成を明記している (`/work/1/SFC/tanab/dev-wave-jobs/t327-prereg-activation/s6-fix2.md:3-13,36`)。

**具体的な反例:** info string 付き `` ```text `` fence は fix1 の v2 では info を marker と誤認して `unclosed-fence`、fix2 の v2 では正常な fenced-code node になる。さらに将来 v3 へ定数を上げるだけでは、loader が既存 v2 g1 を拒否するため履歴互換も成立しない。

**重大度:** blocker

**成果物影響:** 同じ g1／同じ `normalization_version` の freeze 妥当性が checker commit に依存し、durable な条件契約証明にならない。

**提案修正:** land 前なら最終 parser と g1 を同一導入 commit にまとめ、version conformance corpusを固定する。履歴を残すなら v3 を発行し、record ごとの version dispatch で旧 v2 を再現可能にする。parser の意味変更時に version 更新を要求する負例も追加する。

### 2. CommonMark の list-container fence で規範 prose を code block 化しても hash が変わらない

**主張:** fence scanner は行頭から最大3 spacesの standalone fenceしか理解しない。list item 内の fence は list text として平坦化され、paired backticks が inline code delimiterとして消えるため、rendered node kind を変えても同一 `normative_body_sha256` を作れる。

**根拠:** absolute-line fence 判定 (`orchestrator/campaign/s8c_preregistration.py:52-56,381-394`)、inline backtick除去 (`:438-482`)、list continuation の平坦化 (`:556-568`)、規範 hash (`:796-822`)。§5、§6、section heading も同じ fence map を使う (`:581-590,738-795`)。テストは standalone fence のみである (`orchestrator/tests/test_s8c_preregistration_core.py:240-278`)。

**具体的な攻撃手順:** §4 の現行規範 (`docs/phase3-8c-preregistration.md:81-82`) を次へ置換する。

~~~~markdown
- ```
  停止: 固定世代数で停止する。性能目標による早期停止を置かない
  (Best-of-N と選択的報告になるため)。role 応答の schema 違反は再試行しない。
    ```
~~~~

CommonMark では list item 内の fenced code だが、実装上は元と同じ unordered `list_item` textへ正規化される。元の強調記号も正規化で消えるため、規範 hash は衝突する。

**重大度:** blocker

**成果物影響:** 停止規則を非規範のコード例へ降格しても g1 が妥当なままとなり、実走・受理が改変前契約に従ったように見える。

**提案修正:** CommonMark ASTで container 内の子 node kindまで canonicalizeする。依存追加を避けるなら、list item／continuation中の fence openerを明示拒否して fail-closed にする。上記 exact fixture と §6 内 container fence の負例を追加し、新規所見1の version処理も行う。

### 3. HTML comment 内の `## D<N>.` が人間裁定として通る

**主張:** F4 の検索は fenced codeしか不可視化せず、HTML comment 内の行を canonical decision heading と認定する。

**根拠:** ruling 検査は `not in_fence` と loose prefix regexだけである (`orchestrator/campaign/s8c_preregistration.py:1207-1228`)。`check_docs.py` も raw text regexを使う (`tools/check_docs.py:3184-3199`)。既存負例は自由文・別path・standalone fenceまでである (`orchestrator/tests/test_s8c_preregistration_core.py:571-596`)。

**具体的な攻撃手順:** g2 導入 commit の `docs/decisions.md` に次だけを加え、record の `ruling_reference` を `D404` にする。

```markdown
<!--
## D404. 実在しない裁定
-->
```

Markdown上は裁定見出しではないが、freeze validator と docs checker の双方が D404 を認識する。

**重大度:** blocker

**成果物影響:** 人間未承認の条件変更を正規 g2 として受理でき、protected contract と発効集合を無権限に変更できる。

**提案修正:** visible CommonMark AST の level-2 headingだけを authority にし、内容を exact `D<N>. <非空タイトル>` と照合する。少なくとも HTML comment/raw HTMLをmaskする共通 scannerを core と `check_docs.py` で共有し、上記負例を追加する。

### 4. F9 の候補 commit 性質はテストされておらず、`HEAD` へ戻しても既存 invariant が通る

**主張:** `_candidate_commit()` の実装は正しいが、テスト自身は候補 tree が未commit差分を含むことを観測していない。

**根拠:** 候補合成は `orchestrator/tests/test_s8c_preregistration_invariant.py:59-82`、利用側は `:98-168`。いずれも意図的な未commit deltaと `HEAD` の差を作って比較していない。

**具体的な反例:** helper 本体を `return _git_text("rev-parse", "HEAD")` に置換する。現在の HEAD は g1 と required pathsを既に持つため freeze/path検査は通る。dirty core を無視すると activation は blob mismatchで false／SAT=0となり、第二 invariantも通る。

**重大度:** must-fix

**成果物影響:** 段6で HEAD を検査した後、異なる未検査 worktreeを commitでき、受入済みと称する commitの同一性が失われる。

**提案修正:** temporary repoで「HEAD は不適合、未commit candidateだけ適合」という fixtureを作る。candidate treeが HEAD treeと異なり、そのdeltaを validation が観測したことをassertし、`candidate→HEAD` mutationを登録する。

### 5. §6 は「現 land は必ず未発効」という U-8 射程を記述していない

**主張:** 文書は12証拠が揃えば発効すると完全な evaluatorのように記述するが、現実装は全12件を意図的に永久 undefined にしている。記述済みなのは主に U-1 の「起動・受入へ未結線」であり、U-8 の能力不在ではない。

**根拠:** 親裁定は本 land を「freeze + 常に未発効の枠組み」に限定し、文書への明記を要求する (`/work/1/SFC/tanab/dev-wave-jobs/t327-prereg-activation/s6-fix-ruling.md:14-21`)。文書の iff 約束は `docs/phase3-8c-preregistration.md:130-160`。全 contract flag は false (`orchestrator/campaign/s8c_preregistration_evidence_contract.v1.json:42,71,114,150,191,228,264,300,332,374,427,485`) で、実装は必ず undefined を返す (`orchestrator/campaign/s8c_preregistration_evidence.py:618-666`)。

**具体的な反例:** §6 の12機構をすべて実装し§5を埋めても、U-8 evaluatorを別途変更しない限り結果は12件 `EVIDENCE_UNDEFINED`、`effective=False` のままである。現文書だけからはこの追加条件を読み取れない。

**重大度:** must-fix

**成果物影響:** readiness 文書は発効可能な層を出荷したように読める一方、formal trial の受理集合は実際には常に空である。

**提案修正:** phase doc と decision fragment に「現 land は12件すべて SAT不能、SAT=0、常に未発効、green化はU-8」と明記する。protected本文を変えるなら、land前に履歴・g1を整合させる。

### 6. §5 の実際の wire format と拒否条件が文書化されていない

**主張:** 文書は「placeholderでない値」とだけ約束するが、コードは単一 code span内の canonical JSONだけを受理し、追加の意味的空値規則を持つ。

**根拠:** 文書は `docs/phase3-8c-preregistration.md:138-140`。実装は `orchestrator/campaign/s8c_preregistration.py:706-735`。

**具体的な反例:** §5 に裸の `123` を記入する。文書上は非placeholderの数値だが、実装は `canonical-json-code-span-required` として拒否する。

**重大度:** should

**提案修正:** code span、UTF-8 canonical JSON、`null`／空文字列／空container／placeholder stringの扱いを発効ポリシーに記述する。同時に欄別型・単位・範囲の検証は T-295 の scope 外だと明記する。

### 7. 実装済み資源上限のうち4系統は削除しても既存テストが観測しない

**主張:** F11 の実装はあるが、git input/output、batch request総数、total blob bytesの負例がない。

**根拠:** guard は `orchestrator/campaign/s8c_preregistration.py:840-859,1062-1139`。現在の上限テストは generation、commit、単一blob、timeoutだけである (`orchestrator/tests/test_s8c_preregistration_core.py:739-776`)。

**具体的な反例:** `MAX_GIT_INPUT_BYTES`、`MAX_GIT_OUTPUT_BYTES`、`MAX_BATCH_REQUESTS`、`MAX_TOTAL_BLOB_BYTES` の各比較を削除する。既存fixtureは小さいため閾値へ到達せず、対応 reason codeをassertするテストもない。

**重大度:** should

**提案修正:** 各定数を小さく monkeypatchし、超過時の exact reasonと、超過後に後続Git処理を行わないことを個別に検査する。

## 総括

- 判定: **NO-GO**。
- 対応表23項目: `closed 16 / partial 6 / regressed 0 / out-of-scope 1`。
- 元所見単位の `regressed` は0だが、新規所見1はfix2内の normalization-version regressionである。
- 新規所見は `blocker 3 / must-fix 2 / should 2`。
- F2について、現 repository の production `SATISFIED` 経路は静的に0件であり、no-op/tokenだけの充足経路も見つからない。
- F1の公開registry注入は閉じたが、F5 capabilityの偽造耐性は親裁定どおり部分的で、trust boundaryにはできない。
- U-1〜U-8を実装済みと偽るコードは見当たらないが、U-8の「常に未発効」という出荷射程が文書から欠落している。
- 親は3 blockerを直し、F9負例・U-8明記・§5契約・全上限テストを追加し、g1/version履歴を整合させるべきである。
- その後、計算ノードで関連3テスト、変異matrix、受入全走を再実測し、decision spoolをland手順でfoldすること。
- 本レビューではテストを実行していない。`126 passed / 0 failed` は親から提示されたfix2後の実測値としてのみ扱った。