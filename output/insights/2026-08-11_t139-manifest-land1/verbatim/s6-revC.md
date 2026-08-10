NO-GO。承認前に解消すべき blocker が 9 件ある。特に schema は正当な pilot 受領証を構造的に拒否し、同時に複数の不正受領証を受理する。

## 所見

### 1. [blocker] 旧版の受理条件 16 件が v2 に再掲されていない

「原子的な規範 1 件」を 1 件として数えた。うち一部は意図的変更だが、§0 の「前 2 版の受理条件を緩めず再掲」という主張とは両立しない。

1. 「`predecessor_arm` は block 先頭で `START`」という逆向き含意。v2/schema は `START ⇒ position=1` だけで、`position=1 ⇒ START` を落とした。[旧版:97](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-manifest-land1/output/insights/2026-08-08_t139-addendum-a/record-items.md:97>)、[v2:296](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-manifest-land1/output/insights/2026-08-11_t139-manifest-land1/record-items-v2.md:296>)、[schema:639](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-manifest-land1/output/insights/2026-08-11_t139-manifest-land1/receipt-schema-v1.json:639>)
2. 性能 build の申告値を「argv 中の macro 定義および `CMakeCache.txt`」と照合する条件。[旧版:111](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-manifest-land1/output/insights/2026-08-08_t139-addendum-a/record-items.md:111>)
3. `admission_telemetry[].returncode` を受理入力に使う consumer を kill する否定検査。field 自体は旧版内でも未定義だが、明示されたテスト義務ではある。[旧版:142](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-manifest-land1/output/insights/2026-08-08_t139-addendum-a/record-items.md:142>)、[v2:55](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-manifest-land1/output/insights/2026-08-11_t139-manifest-land1/record-items-v2.md:55>)
4. submission intent の `create-only` 条件。[旧版:148](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-manifest-land1/output/insights/2026-08-08_t139-addendum-a/record-items.md:148>)
5. job-side preflight reject collector を同じ実装単位へ含める条件。[旧版:149](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-manifest-land1/output/insights/2026-08-08_t139-addendum-a/record-items.md:149>)
6. `performance_started_marker` の `create-only` 条件。[旧版:168](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-manifest-land1/output/insights/2026-08-08_t139-addendum-a/record-items.md:168>)
7. 各 run log の `#FLAGS_` と `ShowOptParameters()` を exact map と照合する条件。[旧版:170](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-manifest-land1/output/insights/2026-08-08_t139-addendum-a/record-items.md:170>)、[追補A:393](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-manifest-land1/output/insights/2026-08-08_t139-r4-env-probe/addendum-a-reissue.md:393>)
8. `J` 導出 receipt の必須性。
9. `q` 導出 receipt の必須性。
10. simulation receipt の必須性。8〜10 の根拠は [旧版:173](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-manifest-land1/output/insights/2026-08-08_t139-addendum-a/record-items.md:173>)。現 schema は `admission_telemetry: []` を受理する。[schema:1250](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-manifest-land1/output/insights/2026-08-11_t139-manifest-land1/receipt-schema-v1.json:1250>)
11. alpha reservation evidence を少なくとも 1 要素として必須にする条件。[旧版:174](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-manifest-land1/output/insights/2026-08-08_t139-addendum-a/record-items.md:174>)。v2 は「その kind が存在すれば非 null」としか定めない。[v2:375](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-manifest-land1/output/insights/2026-08-11_t139-manifest-land1/record-items-v2.md:375>)
12. `actual_runs[].argv_raw` を計画 argv と exact 比較する条件。[旧版:176](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-manifest-land1/output/insights/2026-08-08_t139-addendum-a/record-items.md:176>)
13. schema を pilot 前に発行し、その digest を `PreregBinding` へ固定する条件。[旧版:195](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-manifest-land1/output/insights/2026-08-08_t139-addendum-a/record-items.md:195>)。v2 は receipt 側の自己申告 `receipt_schema` を置くが、承認 manifest が schema digest を pin する、とは明記しない。[v2:138](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-manifest-land1/output/insights/2026-08-11_t139-manifest-land1/record-items-v2.md:138>)
14. `binary_rehash[]` の旧 predicate「3 要素固定」。v2 は 9 要素へ置換した。[旧版:193](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-manifest-land1/output/insights/2026-08-08_t139-addendum-a/record-items.md:193>)、[v2:255](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-manifest-land1/output/insights/2026-08-11_t139-manifest-land1/record-items-v2.md:255>)
15. `liveness[].probe` の旧閉集合 `{allocation_alive, driver_heartbeat, filesystem_writable}`。v2 は `liveness_run` を追加した。[旧版:202](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-manifest-land1/output/insights/2026-08-08_t139-addendum-a/record-items.md:202>)、[v2:353](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-manifest-land1/output/insights/2026-08-11_t139-manifest-land1/record-items-v2.md:353>)
16. telemetry enum の `calibration_simulation`。v2 は未承認 erratum を先取りして `stress_check_simulation` へ置換した。[旧版:212](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-manifest-land1/output/insights/2026-08-08_t139-addendum-a/record-items.md:212>)、[v2:369](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-manifest-land1/output/insights/2026-08-11_t139-manifest-land1/record-items-v2.md:369>)

失敗シナリオ: overwrite 可能な intent、実 compile flags と申告が食い違う build、admission receipt が空の受領証が v2 下で通る。  
影響: 適格 cluster 集合、trial ledger の完全性、certified 選択が旧版とは別集合になる。

### 2. [blocker] schema の `runs[] == 36` は正当な pilot 288 run を全拒否する

要件は stage receipt の pilot について `36 × 8 = 288` を要求する。[v2:38](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-manifest-land1/output/insights/2026-08-11_t139-manifest-land1/record-items-v2.md:38>)、[v2:294](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-manifest-land1/output/insights/2026-08-11_t139-manifest-land1/record-items-v2.md:294>)。schema は常に `minItems=maxItems=36`。[schema:691](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-manifest-land1/output/insights/2026-08-11_t139-manifest-land1/receipt-schema-v1.json:691>)

静的検査でも 36 件は ACCEPT、288 件は REJECT になった。

失敗シナリオ: 8 pilot cluster を完全記録した正当な受領証が schema 検査で落ちる。  
影響: pilot の受理集合が空になり、`J` 導出・本走・certified 選択へ進めない。

### 3. [blocker] stage 単位の粒度と main-run slot／検証割当ての規定が両立しない

`pilot_cluster_slots` は schema で stage に関係なく `[1..8]` 固定。[schema:671](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-manifest-land1/output/insights/2026-08-11_t139-manifest-land1/receipt-schema-v1.json:671>)。一方、本文は main run に別の「消費 slot 集合」があると書くが、その key は存在しない。[v2:294](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-manifest-land1/output/insights/2026-08-11_t139-manifest-land1/record-items-v2.md:294>)。main の `J` は 4〜13。[追補A:621](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-manifest-land1/output/insights/2026-08-08_t139-r4-env-probe/addendum-a-reissue.md:621>)

さらに各 stage receipt は verification allocation をちょうど 1 件要求する。[v2:509](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-manifest-land1/output/insights/2026-08-11_t139-manifest-land1/record-items-v2.md:509>)。追補 A は study 全体で 1 本だけと凍結している。[追補A:81](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-manifest-land1/output/insights/2026-08-08_t139-r4-env-probe/addendum-a-reissue.md:81>)、[追補A:105](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-manifest-land1/output/insights/2026-08-08_t139-r4-env-probe/addendum-a-reissue.md:105>)

失敗シナリオ: `main_run, J=13` は slot 9〜13を表せない。検証割当てを pilot にだけ置けば main receipt が拒否され、両方へ複製すれば「study で1本」と矛盾する。  
影響: main-run ledger の allocation 集合と correctness 参照が一意に定まらない。

### 4. [blocker] 成功した verification attempt を表す `reason_code` が存在しない

verification attempt は `cluster_slot_or_null == null` とされる。[v2:390](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-manifest-land1/output/insights/2026-08-11_t139-manifest-land1/record-items-v2.md:390>)。しかし `completed` は「その attempt の cluster slot の 36 planned run」と完全双射を要求する。[v2:438](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-manifest-land1/output/insights/2026-08-11_t139-manifest-land1/record-items-v2.md:438>)。残る値はすべて失敗・anomaly である。

qsub 失敗した verification attempt では allocation は存在しないのに、receipt は verification allocation 1 件、correctness evidence 6 件も必須になる。

失敗シナリオ: 正常終了した唯一の検証割当てを `completed` にすると null slot の 36 run を要求され、他の reason にすると偽の失敗になる。  
影響: 全 attempt 台帳を正直に構成できず、producer が行を落とすか理由を捏造する。

### 5. [blocker] verification allocation に性能用 phase／rehash を強制している

全 allocation は performance 用の 6 phase を各 1 件持つ。[v2:248](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-manifest-land1/output/insights/2026-08-11_t139-manifest-land1/record-items-v2.md:248>)、[schema:437](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-manifest-land1/output/insights/2026-08-11_t139-manifest-land1/receipt-schema-v1.json:437>)。しかし追補 A の verification 予算は source staging、6 build、manifest 抽出、correctness/liveness、evidence、cleanup で、特に build と build 後処理を分離する。[追補A:105](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-manifest-land1/output/insights/2026-08-08_t139-r4-env-probe/addendum-a-reissue.md:105>)、[追補A:121](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-manifest-land1/output/insights/2026-08-08_t139-r4-env-probe/addendum-a-reissue.md:121>)

また全 allocation に performance executable の `(point,arm)` 9 組を要求する。[schema:455](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-manifest-land1/output/insights/2026-08-11_t139-manifest-land1/receipt-schema-v1.json:455>)。verification allocation には性能 executable の「staging 後／最初の性能 run 前／最後の性能 run 後」という時点が存在しない。

失敗シナリオ: 正当な verification allocation は phase と rehash を表現できず拒否される。通すには架空の marker/run phase を記録する必要がある。  
影響: accounting・時間予算・binary identity の試行台帳が偽になる。

### 6. [blocker] schema と要件文書の不一致は 10 系統あり、§7.1 は不足を列挙し切れていない

key 集合自体は §4 の shape と一致し、`type: object` を持つ全 53 definition/top-level に `additionalProperties:false` がある。外部 `$ref` と禁止 keyword も 0 件だった。draft-07 metaschema 検査も通る。

不一致は次の 10 系統。

1. `runs[]` の 36 固定対 stage-wide 288／動的件数。
2. `pilot_cluster_slots` を main_run にも無条件固定。
3. performance/verification attempt の `cluster_slot_or_null` 条件を schema が一切検査しない。[schema:1069](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-manifest-land1/output/insights/2026-08-11_t139-manifest-land1/receipt-schema-v1.json:1069>)
4. 正常 8 列、実列数、`malformed_reason` の非 null 一致を検査しない。9 列＋null が静的検査で ACCEPT された。[v2:428](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-manifest-land1/output/insights/2026-08-11_t139-manifest-land1/record-items-v2.md:428>)、[schema:1017](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-manifest-land1/output/insights/2026-08-11_t139-manifest-land1/receipt-schema-v1.json:1017>)
5. `pre_performance_infra_failure` の actual=0／a03不成立なし条件がない。[schema:1114](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-manifest-land1/output/insights/2026-08-11_t139-manifest-land1/receipt-schema-v1.json:1114>)
6. `post_performance_failure` の 3 経路を一つも要求しない。marker=null、observation=[]、actual=0 でも静的検査で ACCEPT された。[schema:1127](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-manifest-land1/output/insights/2026-08-11_t139-manifest-land1/receipt-schema-v1.json:1127>)
7. 置換可能 reason と同一 slot 条件がない。[v2:467](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-manifest-land1/output/insights/2026-08-11_t139-manifest-land1/record-items-v2.md:467>)
8. TU key の POSIX 再正規化と `base_tree_sha` 再導出を schema が担わず、§7.1 にも列挙されない。[v2:206](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-manifest-land1/output/insights/2026-08-11_t139-manifest-land1/record-items-v2.md:206>)、[schema:84](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-manifest-land1/output/insights/2026-08-11_t139-manifest-land1/receipt-schema-v1.json:84>)
9. pointer の実在、size/hash 一致、同一 fd/snapshot、symlink 拒否を schema は検査できないが、§7.1 の委譲一覧にない。[v2:65](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-manifest-land1/output/insights/2026-08-11_t139-manifest-land1/record-items-v2.md:65>)、[schema:17](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-manifest-land1/output/insights/2026-08-11_t139-manifest-land1/receipt-schema-v1.json:17>)
10. 同一 allocation 内の monotonic ordering を検査しないうえ、§7.1 にない。[v2:112](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-manifest-land1/output/insights/2026-08-11_t139-manifest-land1/record-items-v2.md:112>)、[schema:433](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-manifest-land1/output/insights/2026-08-11_t139-manifest-land1/receipt-schema-v1.json:433>)

§7.1 は一部の cross-field 制約だけを列挙するため、上記 3〜10 を schema が保証するかのような恒真保証になる。[v2:616](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-manifest-land1/output/insights/2026-08-11_t139-manifest-land1/record-items-v2.md:616>)

失敗シナリオ: 3 経路を一つも持たない post failure、9 列/null observation、差し替え可能な pointer が schema 適合になる。  
影響: validator 実装ごとに受理集合が分岐し、材料 report と certified 選択が再現不能になる。

### 7. [blocker] 承認済み文書から一意に導けない predicate を新設している

特に以下は単なる key 名ではなく、受理集合を変える新しい選択である。

- `pilot_cluster_slots == [1..8]`。追補 A は「適格 pilot 8 本」を固定するだけで、どの slot を消費するかは固定していない。[追補A:611](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-manifest-land1/output/insights/2026-08-08_t139-r4-env-probe/addendum-a-reissue.md:611>)。a09 の prefix 均衡から「必ず先頭 8 本」までは導けない。
- `exclusivity.method ∈ {node_local_process_scan, scheduler_accounting}`。core は単独性検査結果を要求するだけで、この 2 手法への閉包を承認していない。[core:292](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-manifest-land1/output/insights/2026-08-07_t139-mainrun-design/preregistration.md:292>)、[v2:246](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-manifest-land1/output/insights/2026-08-11_t139-manifest-land1/record-items-v2.md:246>)
- performance 用 phase enum 6 値。追補 A の verification phase 表とは一致しない。
- schedule-table の header・TAB・157 行という canonical byte grammar。追補 A は canonical bytes の発行を要求するが、その serialization 自体は固定していない。[追補A:603](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-manifest-land1/output/insights/2026-08-08_t139-r4-env-probe/addendum-a-reissue.md:603>)、[v2:542](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-manifest-land1/output/insights/2026-08-11_t139-manifest-land1/record-items-v2.md:542>)
- `schema_version const "t139-receipt/v1"`、`scheduler_request_id`、`qsub_result`、`failure_evidence.kind` の細分類。これらの literal/閉集合を D162・core §12・a01〜a13・D262〜D264から一意には導けない。

一方、`approval_manifest`、`erratum_id`、`composed_core_sha256` は D262/D263 に根拠があるため捏造 key とは判定しない。

失敗シナリオ: 同等に正当な別 serialization や exclusivity 証拠が未知 enum として拒否される一方、producer が選んだ 2 手法だけが凍結される。  
影響: allocation 適格集合と schedule 参照 digest が承認済み科学設計ではなく v2 起草者の選択で変わる。

### 8. [blocker] 絶対規律 1・2 を自己申告で代替できる

性能/correctness の `trace_enabled` と cache 値は schema の const にすぎず、実 `compile_commands.json`、configure argv、`CMakeCache.txt` との照合条件が落ちている。[schema:128](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-manifest-land1/output/insights/2026-08-11_t139-manifest-land1/receipt-schema-v1.json:128>)、[schema:785](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-manifest-land1/output/insights/2026-08-11_t139-manifest-land1/receipt-schema-v1.json:785>)。これは規律 1 の compile-time 分離を producer の boolean 申告へ縮退させる。

また `correctness_evidence[].outputs` は空配列を許す。[schema:820](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-manifest-land1/output/insights/2026-08-11_t139-manifest-land1/receipt-schema-v1.json:820>)。6 個の evidence object があっても、再実行・anomaly 検出のための output pointer が 0 件でよい。

失敗シナリオ: 実 binary は trace-enabled だが receipt は false/0、correctness output は空、reason は `completed` とする。shape schema はこれを拒否できない。  
影響: 観測者効果を混入した TPS または correctness 未検証 variant が certified 候補へ入る。

規律 3 の「iteration ごとの構造化理由」については、`failure_evidence.kind=correctness` と raw pointer しか強制されない。ただし本 receipt の study-stage と synthesis iteration の対応が正本から確定できないため、これは `[suspicion]` に留める。

### 9. [blocker] erratum の 7 検査は置換内容を pin していない

検査 1〜7 は operation 数、old hash、`較正` 件数、1 行性、非重複、a12 表形式しか検査しない。[erratum-v2:122](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-manifest-land1/output/insights/2026-08-11_t139-manifest-land1/erratum-core-s7-stresscheck-v2.md:122>)。期待 `new_text` の完全一致も、期待 composed digest も固有受理述語に入っていない。しかも §3 は他節を受理述語へ使うな、と明記する。[erratum-v2:133](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-manifest-land1/output/insights/2026-08-11_t139-manifest-land1/erratum-core-s7-stresscheck-v2.md:133>)

例えば次の置換でも 7 条件を満たせる。

```text
結果を見て q を選び直す。
| a12 | 結果を見て q を選び直す事前 simulation の仕様 |
```

2 行とも `較正` を含まず、各1行、index 2 は `| a12 |` で始まり列数も維持できる。

さらに operation/locator object の exact key、index が exact `{1,2}`、`old_text` と対象 bytes の一致、YAML duplicate-key 拒否も規定されていない。

失敗シナリオ: 同じ erratum ID で科学的に逆方向の `new_text` を持つ文書が固有検査を通り、その digest を誤って manifest が承認すると適用される。  
影響: 凍結 core の科学的主張と受理述語を、既知 ID のまま任意に変更できる。

## erratum 再計算結果

候補 bytes そのものの計算値は正しい。

- core SHA-256: `ac939af4de87dff0cd3964e37cef975d57919a709d57f4e9523c8b6a9fcd60e9`
- 221 / 333 / 404 / 424 行の LF 込み digest は、両 erratum 記載値と全一致。
- 第1 erratum のみ: `d1782b04ceb7cd56a3d10e2e6efb4eb7f90e6a89506a74bba727d34a5f79de82`
- 4 operation 合成: `e0b0caeaca9300acffbb5cd6b81db7b6fb7fa8f9eeab81219affb4e2f94a8e0c`
- 適用順を逆転しても同値。
- 置換前の `較正`: 2 件（221、333）。置換後: 0 件。

したがって問題は候補 digest の誤算ではなく、「固有 validator がこの exact replacement を一意に保証しない」ことである。

## 承認状態

[ nit ] record-items-v2 と erratum-v2 の authority header は、承認済み先例と同じ `authority:none / default_effect:no-state-change` であり、承認直後に偽になる `approval_status:draft_unapproved` は持たない。[record-v2:3](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-manifest-land1/output/insights/2026-08-11_t139-manifest-land1/record-items-v2.md:3>)、[erratum-v2:3](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-manifest-land1/output/insights/2026-08-11_t139-manifest-land1/erratum-core-s7-stresscheck-v2.md:3>)

先例の第1 erratum は承認後も「現時点では未承認」と書いたままで、D262 の承認事実と矛盾する。[先例:180](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-manifest-land1/output/insights/2026-08-08_t139-addendum-a/erratum-core-s15.md:180>)、[D262:12121](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-manifest-land1/docs/decisions.md:12121>)。候補2文書はこの失敗を概ね避けている。

`receipt-schema-v1.json` には authority header 自体がない。approval manifest が blob digest を pin するなら直ちに欠陥ではないが、record-items-v2 にその pin 契約が明記されていない点は所見1の脱落13に含めた。

ファイル変更は行っていない。pytest も実行していない。行ったのは read-only の JSON parse、draft-07 metaschema 検査、部分 schema の静的反例検査、SHA-256 再計算だけである。`git status --short` は空だった。

## 総括

GO/NO-GO: **NO-GO**  
blocker 件数: **9**  
前版から落ちた受理条件の件数: **16**  
schema と要件文書の不一致の件数: **10**