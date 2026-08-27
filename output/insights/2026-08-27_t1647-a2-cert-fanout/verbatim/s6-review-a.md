静的レビューの結論は **must-fix 2 件、nit 1 件**です。pytest は実行しておらず、以下の「落ちる／通る」はコード上の変異追跡による判定です。

## 所見 1 — certification result v2 の受理経路が残る

- file:line: `orchestrator/campaign/paper_story_a2_certification.py:2825-2853`
- 裏突破経路: `materialize()` は `report["schema_version"] == CERTIFICATION_SCHEMA` を検査せず、`request_ids` が無ければ照合自体を skip します。したがって、現行 `protocol_sha256` と `attempt_id` を持つ v2 形式の `request_id` scalar report、または schema 欠落 report をそのまま `certification.json` として publish できます。`orchestrator/tests/test_paper_story_a2_certification.py:1078-1097` も、極端に小さい report を正例として受理しています。
- **成果物影響:** accepted artifact 集合に v2／不完全 report が残り、`certification.json` が group request ID を束縛しないまま `COMPLETE.json` と artifact manifest から参照され得ます。
- 推奨: **must-fix**。materialize の stage 作成前に certification result v3 の exact schema、`request_ids` の policy 順序・相異、必須フィールドを検証する専用 validator を置き、v2 負例を追加してください。

## 所見 2 — M4 は atomic create-only 行を殺しても落ちない

- file:line: `orchestrator/campaign/paper_story_a2_certification.py:2955-2962`、`orchestrator/tests/test_paper_story_a2_job_contract.py:307-334`
- 退化経路: `stale-raw` 負例は事前に raw を作るため、常に `requested_raw.exists()` の行で落ちます。`requested_raw.mkdir(..., exist_ok=False)` を `exist_ok=True` に一行変更しても同じ負例はその前段で落ち、M4 の標的行を検出できません。実際の差は existence check と mkdir の間の競合でのみ現れます。
- **成果物影響:** `exist_ok=True` へ退化すると競合した別 worker が check 後に作った raw subtree を受け入れ、manifest／report の raw cell 集合が一意な compute-preflight owner に由来する保証を失います。
- 推奨: **must-fix**。`Path.mkdir` 相当を差し替え、check 後・mkdir 直前に競合 directory を作る負例にしてください。`exist_ok=False` なら `FileExistsError`、`True` なら通る形で atomic 行そのものを殺す必要があります。

## 所見 3 — group helper の workload／log-path 述語は production 経路では恒真

- file:line: `orchestrator/campaign/paper_story_a2_certification.py:784-799,843-905,973-979`、`orchestrator/tests/test_paper_story_a2_certification.py:749-767`
- 退化経路: production validator は policy 順で loop し、先に `job["workload"] == workload_id` と各 workload の canonical log path を検査してから、policy 由来の workload と正規化済み path で `bindings` を再構成します。そのため `_validate_group_coordinates()` 到達時には workload 順と log-path 相異は自動的に成立します。request ID 相異だけは恒真ではありません。順序負例は helper 直呼びなので helper 行は殺せますが、production receipt 経路の独立防壁ではありません。log-path 相異の負例はありません。
- **成果物影響:** 現状の受理集合は変わりません。前段の workload・canonical-path 検査が同じ不正 receipt を拒否します。
- 推奨: **nit**。独立な group 防壁として数えるなら raw job fields を helper に渡して receipt 経路で変異させるか、冗長検査であることを明記してください。

## R1〜R10 実装照合

| 裁定 | 判定 | file:line と実効性 |
|---|---|---|
| R1 | 実装済み | job subtree 作成は `paper_story_a2_certification.py:657-663`、campaign/cache 分離は `2482-2505`、raw exact-open は `2568-2575`。 |
| R2 | 実装済み | preregister は raw を作らず `657-663`、唯一の mkdir は compute-preflight の `2961`。shell の `233-258` も作成せず freshness check 後に preflight を呼びます。 |
| R3 | 実装済み | policy 規則は `.v2.json:119-121`、exact validation は Python `294-296`、protocol preimage への包含は `268-279`。 |
| R4 | **一部不足** | 7 定数は `41-49` で bump 済み。submission/completion/acquisition/compute/raw/policy は旧版拒否。ただし certification result consumer は所見 1。 |
| R5 | 実装済み | claim・reservation・submission の交差照合は `2591-2648`、loader 再検算は `2740-2796`。 |
| R6 | 実装済み | completion job は submission の workload/request/log path と照合される `1038-1157,1186-1194`。job swap は拒否されます。 |
| R7 | 実装済み | canonical producer `finish_group()` は `1407-1492`、login-side mode は submitter `91-110`。completion/acquisition は create-only recorder を通ります。 |
| R8 | 実装済み | entry point 冒頭 precheck は submitter `12-14`、各 qsub も `158-162` から `ratified_qsub()` の Python `1388-1394` を通過。rc は `163-166` で検査されます。 |
| R9 | 実装済み | `s6/implementation.diff:1-3043` の全 diff header に `docs/failures.md` または他 docs の変更なし。 |
| R10 | **一部不足** | M1〜M3・M5〜M8 は帰属成立。M4 は所見 2 のとおり atomic 行を殺しません。 |

## M1〜M8 の変異帰属

| 変異 | 判定 | 静的な帰属 |
|---|---|---|
| M1 | 成立 | test `515-528` は `_protocol_preimage` 直呼び。composition 行 `278` を外すと `original_sha != changed_sha` だけが失敗します。 |
| M2 | 成立 | test `762-765` は canonical coordinates の request ID 一件だけを重複。相異検査 `791-792` を外すと raise が消えます。 |
| M3 | 成立 | test `766-767` は coordinates の順序だけを反転。順序検査 `786-788` を外すと raise が消えます。ただし production では前段 workload guard と冗長です。 |
| M4 | **不成立** | test `315-334` は `2956` で先に落ち、atomic `exist_ok=False` 行 `2961` の退化を検出しません。 |
| M5 | 成立 | test `1281-1288` は余分な workload directory を置いた後、finalizer を直接呼びます。jobs 親走査へ戻せばこの assert が失敗し、loader は介在しません。 |
| M6 | 成立 | test `1317-1323` は claim の job ID だけを変えて helper を直呼び。`2558` の claim job ID 条件を外すと raise が消えます。 |
| M7 | 成立 | test `769-788` は未批准 precheck 時の runner 呼出回数を固定。`ratified_qsub()` の `1390` を外すと qsub stub に到達して負例が失敗します。 |
| M8 | 成立 | test `1325-1344` は `7/0` group に decoy manifest を付与。`all()` を `any()` にすると manifest error が非致命として捕捉され、期待した `failed group` raise が消えます。 |

## P1〜P3 と過剰拒否

| 正例 | 判定 | 検出範囲 |
|---|---|---|
| P1 | 実装済み・未実走 | `test_paper_story_a2_certification.py:725-739` が canonical 2-job receipt を acquisition validator まで通します。 |
| P2 | 実装済み・未実走 | `769-788` の批准済み分岐が qsub runner に一度到達。submitter の precheck→ratified-qsub 順序は job-contract test `82-92` でも固定されています。 |
| P3 | 実装済み・未実走 | `test_paper_story_a2_job_contract.py:273-300` は rr50 subtree が存在する状態で rr5 preflight を受理します。 |

## 旧 layout・旧 schema

- policy v1: `paper_story_a2_certification.py:291-296` で拒否。
- submission v3: `805-821` の exact fields と v4 比較で拒否。
- completion v2: `1164-1179` で拒否。
- acquisition v2: `1239-1257` で拒否。
- compute result v1: `1087-1095` で拒否。
- raw manifest v2: `2676-2686` で拒否。旧 `attempt/raw` も `2568-2575,2688-2690` の nested exact path に一致しません。
- certification result v2: **拒否されない**。`2827-2853` が schema を見ず、旧 scalar request report を受理します。

## 反証

- **反証:** policy 論理積規則は `_protocol_preimage` に実際に入っており、変更で protocol hash が動きます。
- **反証:** 批准失敗を `|| true` や rc 無視で越える qsub 経路はありません。
- **反証:** `finalize-raw` は policy 由来の四つの raw pathを直接 open し、親 directory を列挙しません。
- **反証:** production における `raw/$workload` directory の create owner は compute-preflight の一管所だけです。

## 総括

- must-fix: **2 件**。
- 最重: certification result v2／不完全 report が materialize 可能。
- 次点: M4 が atomic `exist_ok=False` の退化を検出しない。
- 3番目: group helper の workload/log-path 検査は production では恒真（nit）。
- pytest 実走 0 件であり、緑の主張はありません。