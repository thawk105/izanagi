## 所見

### 1. SHAPES consumer — refuted

取り残し consumer は見つからなかった。production の `SHAPES` 読み取りは、定義を除いて次の 10 行で尽きる。

- 派生 map: [b10_backoff_shape_sweep.py:92](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1905-b10-shape-prereg-v2/orchestrator/campaign/b10_backoff_shape_sweep.py:92)、`:93`
- factorial / block: `:524`、`:547`
- spec: `:836`、`:841`
- residual: `:1022`
- probe build / validator / execution: `:1793`、`:2010`、`:2622`

`("symmetric-modulo", "binary")` の直書きも production では `:921` と `:1927` の正確に 2 箇所。別形式は `expected_supports` の `:831-835`、name regex の `:2401`、意図的に残す C++ / `exact_model()` の `:122`、`:572-573` だけである。

test 側の `B.SHAPES` reader は [test_b10_backoff_shape_sweep.py:91](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1905-b10-shape-prereg-v2/orchestrator/tests/test_b10_backoff_shape_sweep.py:91)、`:116`、`:273`、`:906`、`:909`、`:1121`。test 内の直書き tuple は `:177`、`:1132`。プランはすべて扱っている。

`b10` 名を持たない [test_condition_meaning_gate.py:248](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1905-b10-shape-prereg-v2/orchestrator/tests/test_condition_meaning_gate.py:248) は `EXPECTED_HOLE_LINE` だけの consumer で、shape cardinality には依存しない。

成果物影響: 追加の production / test file 編集は不要。

### 2. 21→15 と三形算術 — refuted

21 の変更対象は production で次の全件。

- unique genomes: `b10_backoff_shape_sweep.py:530-531`
- block order: `:552-553`
- `spec_content`: `:1375`
- block filename range: `:2217`
- verify 完了数: `:2752`
- perf 完了数: `:2904`

test は `test_b10_backoff_shape_sweep.py:928`、`:974`。関連する三形算術も次で尽きる。

- residual 18→12: `:564`、`:713`
- probe cells 18→12 / differences 12→6: `:808-809`
- encodings 18→12: `:905-909`
- cell effects 54→36: `:1094-1096`
- production の probe error literal: `b10_backoff_shape_sweep.py:1827`、`:2012`
- Holm 6→3: `:921-934`、`:991`
- docs の run order、families、residual rows: `docs/b10-backoff-shape-preregistration.md:168-478`

`pairs_per_family = 18`、`all-2^18`、`construct-all-18...` は変更対象ではない。

成果物影響: プランの cardinality 置換は網羅している。

### 3. 機構の数式と probe の帰属 — real

brief の `symmetric-modulo` 導出は条件付き分布を落としている。[brief.md:44](</home/SFC/tanab/.claude/jobs/11513787/tmp/t1905-b10-prereg-v2/brief.md:44) の式は `R` と high bit が同じ分布を持つ仮定が必要である。実コード `b10_backoff_shape_sweep.py:570-577` からは、正確には

`E[X]-mu = mu(p-1/2) + ((1-p)E[R|H=0] - pE[R|H=1])/2`

となる。条件付き平均が共通の `m` の場合に限り `(p-1/2)(mu-m)` へ縮む。brief `:45` はさらに実待ち量に対する係数 `1/2` を落としている。

また probe harness は elapsed cycle だけを保存しており、high-bit 件数を記録していない (`b10_backoff_shape_sweep.py:1741-1747`、`:1897-1915`)。したがって「probe が p != 1/2 を直接反証した」とは言えない。証明されたのは binary の realized mean が 1% gate を超えたことまでである。

R1 は同じ受理集合のまま、例えば「high-bit だけに依存する形を除外し、low63 modulo residue と相補結合する形だけを残す」という後付けの式構造規則として書ける。ただし p 不変の定理とは書けない。

成果物影響: このままでは decision / preregistration が、測っていない high-bit 偏りを原因として認証する。

### 4. exact 1.0 と exclusive 境界 — real

現行 parser は正の有限値をすべて受理する (`b10_backoff_shape_sweep.py:1010-1017`)。exact `1.0` 化で赤になる既存 test は 0 件。既存 M18 は limit を変えず、観測値を 2% にする runtime test である (`test_b10_backoff_shape_sweep.py:730-742`)。

parser で `maximum_absolute_deviation != 1.0` を拒否すれば、formal path については上限を緩めない機械保証になる。runtime で同じ limit を再確認する部分は、formal path が必ず parser を通る限り防御的な恒真である。一方、`>=` は exclusive の本体であり正しい (`b10_backoff_shape_sweep.py:1184-1189`)。exact 1.0% は拒否される。

不足しているのは境界 test。M18 の 2% は `>=` を `>` に変える変異を殺せない。実体を呼ぶ代案は、canonical spec の 1 cell を `commanded=4200`、`realized=4242`、`deviation_pct=1.0` にし、`parse_preregistration()` 後の `validate_runtime_physical_residual()` が `physical-residual` で拒否することを検査するもの。

成果物影響: 境界 test がないと `>=`→`>` 変異により exact 1.0% cell が formal run へ入る。

### 5. 新設負例 4 件 — 1 件だけ real

1. `test_v4_spec_including_binary_shape_is_rejected` — refuted  
   実際の `parse_preregistration()` の shape 閉集合を呼ぶため、binary 受理への production 変異を殺せる。

2. `test_physical_residual_limit_other_than_exact_one_is_rejected` — refuted  
   `0.5` と `2.0` は現行の「正なら受理」predicate を殺せる。上限緩和防止を直接示すのは `2.0`、`0.5` は exact policy の検査である。

3. `test_spec_has_no_observed_deviation_based_cell_exclusion_surface` — real  
   提案した未知 key は既存の汎用 `_exact_object()` だけで既に拒否される (`b10_backoff_shape_sweep.py:770-776`、`:1000-1005`、`:1029-1035`)。新設 `registration_rules` の R4 validation を stub 化・削除しても、この test は通る。

   代案は実在する surface を変異すること。

   - `registration_rules.shape_eligibility_evidence` を observed-deviation 型の値へ変えて parser 拒否。
   - `registration_rules.physical_residual_cell_policy` を exclusion 型の値へ変えて parser 拒否。
   - 実在する `physical_residual.values` の 1 行を削り、parser または runtime closure で拒否。

4. `test_schema_v3_document_is_rejected_after_v4_positive_control` — refuted  
   `_SPEC_SCHEMA` の v4-only 判定 (`b10_backoff_shape_sweep.py:809-810`) を直接検査し、v3 併用受理を殺せる。

成果物影響: 3 件目を置換しないと、R4 を実装せず説明文字列だけ保持する変異が生存する。

### 6. dormant code 2 — refuted

code 2 test の維持は妥当。formula SHA は code 2 branch を含む一行全体を束縛し (`b10_backoff_shape_sweep.py:122-123`、`:629-636`)、`exact_model()` もその branch の oracle である (`:557-577`)。M14 と alternate-mixer test は「登録 grid」ではなく「保存した patch formula」の変異帰属を検査している。

誤読防止には次の名前・コメントが適切。

- `test_m14_dormant_cpp_code2_mixer_must_match_registered_symmetric_mixer`
- `test_dormant_cpp_code2_pair_average_is_exact_for_alternate_odd_mixer`
- コメント: 「code 2 は v4 grid / Holm family / throughput report には含まれず、byte-pinned formula compatibility だけを検査する」

`test_exact_finite_models_have_mean_exactly_mu_for_all_shapes` と binary-arms test にも同じ `registered` / `dormant-code2` 区別が必要。

成果物影響: 数値や受理集合は変わらないが、mutation ledger が code 2 を登録 shape の保証と誤帰属するのを防ぐ。

### 7. PROBE_SCHEMA v2 — real

`/v2` への版上げ自体は妥当。新形式は cells 18→12、differences 12→6 なので、同じ `/v1` のままでは非互換な二形式を schema_version で区別できない。

既存 `/v1` を読む production 経路はない。repo 内の読取 validator は `_validate_probe_result()` だけ (`b10_backoff_shape_sweep.py:1938-2057`) で、`run_probe()` の create-only 出力検証に使われる。歴史的 artifact は docs への開示元であり、新 validator へ渡されない。

ただし planned test は fixture と assertion の双方が `B.PROBE_SCHEMA` を参照する (`test_b10_backoff_shape_sweep.py:297`、`:803`)。定数を `/v1` に戻す変異でも緑になる。既存 test を、literal `/v2` 正例と literal `/v1` 負例に直す必要がある。

成果物影響: test を補強しないと、新しい 12-cell artifact が誤って `/v1` と発行され、schema-based consumer が歴史的 18-cell artifact と区別できない。

### 8. WAL / lock / block record resume — refuted

v4 は旧 campaign を resume しない。

- search config に spec 全体・binding・shape codes が入る: `b10_backoff_shape_sweep.py:1322-1367`
- trial に spec SHA が入る: `:1380`
- campaign identity は search config と trial を hash する: `orchestrator/campaign/ident.py:169-190`
- 同じ layout を誤って指しても binding mismatch で拒否: `b10_backoff_shape_sweep.py:1427-1447`

`_block_record_filename()` を `<15` にすると、新 driver を手動で旧 root に向けた場合は旧 index 15-20 を拒否する。しかし formal path は新 campaign ID の root しか読まない (`:2734-2736`、`:2871-2879`)。block record 自体も spec SHA と完全な binding を持つ (`:2243-2263`)。

既存成果物を変更する経路もない。probe と block records は `O_EXCL` (`:2060-2077`、`:2145-2169`)、report root は `exist_ok=False` (`:2494-2498`)。

成果物影響: 過去 bytes・台帳参照・v4 内 resume への破壊はない。

### 9. check_docs / dispatch — refuted

`docs/b10-backoff-shape-preregistration.md` を構造検査する checker はない。`tools/check_docs.py` の living-doc 列挙 (`:128-164`) に対象文書はなく、対象 path / spec marker の専用検査も存在しない。

Pegasus submitter は文書が source commit に存在することだけを確認する (`tools/pegasus/submit_b10_backoff_shape.sh:90-97`)。process/materializer inventory test は関数名と call site 数の検査であり、shape cardinality や文書節構成には依存しない。

成果物影響: §構成変更や v4 JSON 化による docs checker / dispatch contract の赤は予想されない。

### 10. plan / brief 自身 — real 2 件、refuted 1 件

- real: brief の「12 対 / 3 族」は誤り (`brief.md:88-90`)。`judge()` は各 family について 3 blocks × 6 means を列挙する (`b10_backoff_shape_sweep.py:1611-1622`)。従って 18 対、3 族が正しい。plan `:323-325` の訂正を採るべき。
  
  成果物影響: 12 を採ると family completion と permutation 登録が実装の 18 effects と不一致になる。

- real、裁定パッケージ候補: plan は「符号化空間が不変」と述べる一方 (`plan.md:25`、`:357`)、同じ plan で `encode("binary")` と `decode(2000+mu)` を拒否するとしている (`:21-22`)。C++ の数値式は不変だが、driver の受理 encoding space は `{0,1,2}` から `{0,1}` へ変わる。
  
  成果物影響: `SPACE_VERSION=v2` が三形版と二形版の両方を指す。ただし full spec SHA / search config が identity を分離するため、現行 campaign の衝突はない。

- refuted: plan が挙げる対象 file の行番号 range に実体との重大なずれはない。「直接 reader 10 箇所」は cluster 表現であり、`encode/decode` は派生 map reader、`_shape_differences` は literal readerという用語上の粗さだけである。

  成果物影響: なし。

### nit

test 名を改名すると `orchestrator/tests/acceptance_duration_ledger.json:831`、`:859` などの旧 nodeid が残る。ledger loader は stale key を許容するため赤にはならず、新 nodeid が unknown-duration 扱いになるだけである。認証結果・report・台帳値は変わらない。

## 総括

real 所見は 6 件。

最重要 3 件は次のとおり。

1. symmetric-modulo の formula-only 不変性と high-bit 偏りの「probe による反証」は、現在の数式・計測項目では成立しない。
2. exact 1.0% 境界を拒否する `>=` の変異 test がなく、`>` への退行が生存する。
3. cell-exclusion 負例は既存 generic key closure の恒真で、新設 R4 production validation を検査しない。

プランはそのまま採るべきではない。機構の記述を条件付き期待値に直し、R4 test を実在 field / cell closure へ差し替え、exact 1.0 境界と probe `/v1` 負例を追加すれば採用可能。`pairs_per_family=18` は維持が正しい。

pytest・build・check_docs は指示どおり実行していない。