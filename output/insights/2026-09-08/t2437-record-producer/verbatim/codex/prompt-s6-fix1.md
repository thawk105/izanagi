単独段 dispatch: stage=fix; sandbox=workspace-write; parent=/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2385-t2437-record-producer

必読事項の射影: 次の 5 ファイルを読め。**どれか 1 つでも読めなければ即停止し、その旨だけを出力せよ。**

- 段 6 fix 裁定 (本 prompt の下部「fix 裁定」節が正本):
  `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2385-t2437-record-producer/prompt-s6-fix1.md`
- 段 4 裁定 (scope・不変条件・変異事前登録):
  `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2385-t2437-record-producer/s4-ruling.md`
- 段 5 実装子の prompt (実装子契約を全文継承する。所有・禁止・検査・報告の義務は同じ):
  `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2385-t2437-record-producer/prompt-s5-author.md`
- 段 6 レビュー B (B-1 / B-2 の根拠):
  `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2385-t2437-record-producer/s6-review-B.md`
- 段 6 レビュー A (A 側所見の根拠):
  `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2385-t2437-record-producer/s6-review-A.md`

# 段 6 — fix 1 (Codex author、workspace-write)

あなたは izanagi の dev-wave 段 6 の fix 子である。cwd は worktree
`/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2385-t2437-record-producer`。段 5 の未 commit 差分の上で作業する。
**コードとテストだけを編集せよ。docs を編集するな。commit・push・branch 操作をするな。** 所有は段 5 と同じ 4 file。触ってはいけない file も段 5 と同じ。新 file を作るな。

**既存テストの期待値を変更するな** (反転・緩和・skip・削除を禁じる)。赤なら実装側が誤り。期待値が誤りと考えるなら実装を変えず報告して止まれ。指示外の受理集合変更をするな。

## fix 裁定

### F-1 (B-1、must-fix): derive の結果を record が参照する ordered-WAL projection の digest へ束縛する

現状: `derive_physical_result(*, ordered_wal_records, ...)` は records の list だけを受け、`assemble_result_evidence_record` は `derived` と任意の `ordered_wal_ref` を独立に受ける。同じ attempt の別 projection を参照させると consumer が FC07 で落とす record を正常発行できる。

修正 (この形に固定する):

1. `derive_physical_result` の入力を **projection の raw bytes** にする: `derive_physical_result(*, ordered_wal_projection_bytes: bytes, build_attempt_id: str, ordered_verifiers: Sequence[str], verify_result: VerifyResult | None = None)`。内部で `_parse_canonical_object` → `_exact_object(..., _ORDERED_WAL_KEYS)` → `schema_version == "ordered-wal-projection/v1"` → `projection["build_attempt_id"] == build_attempt_id` → records = `projection["records"]` (非空 list、各 item は dict、各 item の attempt が `_projection_attempt_id` で一致) を検査し、不成立は `ResultEvidenceIssuanceRefused`。terminal は `records[-1]`。既存の 3 方向分岐はそのまま。
2. `DerivedPhysicalResult` に `ordered_wal_sha256: str` を足す (= `hashlib.sha256(ordered_wal_projection_bytes).hexdigest()`、consumer の `resolve_content_addressed_ref` が record の `ordered_wal_ref.sha256` と照合する digest と同じ定義。`_content_addressed_referent_sha256` を使え)。
3. `assemble_result_evidence_record` は `ordered_wal_ref["sha256"] == derived.ordered_wal_sha256` を要求し、不一致は `ResultEvidenceError` (record を返さない)。`ordered_wal_ref["path"]` は変えない。
4. 負例を足す: 同じ attempt の **別 projection** (records の terminal だけ違う、または byte_start が違う) を `ordered_wal_ref` に指定して assembler が拒否する test 1 件、`ordered_wal_projection_bytes` が非 canonical / 別 attempt / records 空で derive が拒否する test (parametrize、ASCII id)。既存の derive 系 test は helper を projection bytes 経由に書き換える (期待値は変えない)。統合 test (`test_synthetic_silo_source_producer_passes_formal_consumer_contract`) は fixture builder が作った projection の canonical bytes を derive へ渡す形にする。
5. `DerivedPhysicalResult` を test が直接構築している箇所 (`test_reflux_result_evidence.py:748` 付近) は、derive 経由へ改めるか、直接構築するなら `ordered_wal_sha256` を実 projection の digest から取れ。

### F-2 (B-2、must-fix): 統合 test の docstring

`test_synthetic_silo_source_producer_passes_formal_consumer_contract` の docstring に「synthetic Silo source 束縛の下での formal-consumer contract の検査であり、production issuer からの到達性は証明しない」「salts は不変・未行使、ledger replay は要求しない」を書け。

### F-3 (レビュー A の所見) — A 側所見の裁定

- **A-2 = B-1 (F-1 で閉じる)。** derive から issuer まで同じ resolved projection を通す。F-1 の形で実装せよ。
- **F-3a (A-1、must-fix): terminal record の外枠を production 形に閉じる。** consumer の `_wal_field()` は同名 top-level field を payload より優先する (D1715/D1768 で維持された fallback)。producer は payload しか読まないので、root shadow を持つ record で両者が乖離する。production writer (`wal.py`) は外枠 `{variant, stage, env_tag, ts, payload}` しか書かない。**producer は projection の terminal record (`records[-1]`) の外枠 key 集合が exact にこの 5 key であることを要求し、違えば `ResultEvidenceIssuanceRefused`。** consumer の判定式・`_wal_field` は変えない (D1730 の consumer 側 gate は別 wave [T-2384])。負例: top-level に `reason` / `verify_configs` / `verify` / `build_attempt_id` を足した terminal (payload は正しい) で derive が拒否する parametrize (ASCII id)。
- **F-3b (A-4、must-fix): 境界負例と実 issuer 経由の統合。** (i) accepted の `verify_configs` 負例を parametrize に広げる: `[]` (空)、正しい prefix (`ordered_verifiers[:-1]`、policy が 2 要素以上のとき)、逆順、要素重複 (`[a, a]`)。policy 側 `ordered_verifiers` は 2 要素以上の実値で組め。(ii) 統合 test `test_synthetic_silo_source_producer_passes_formal_consumer_contract` は 33 record の書込みを fixture の `write_evidence_tree()` でなく **`issue_result_evidence_record()`** で行う (projection と provenance は先に tree へ置き、issuer が resolve → create-only write)。加えて取り違え負例 1 件: 同じ attempt で anomaly の異なる projection (別 fixture、例 `r3_cycle3` の snapshot) を `ordered_wal_ref` に指定した record は assembler (F-1 の digest 照合) が拒否する。
- **F-3c (A-3、採用・comment だけ):** `reflux_result_evidence.py` の「Key/cardinality and derived booleans are drift assertions」comment を、恒真 (`anomaly_count == len(anomalies)`、key 集合、`certified`/`serializable` の派生) と実防護 (`total_cycles == anomaly_count` = 切詰め拒否、`len(anomalies) == 1` = 単一 class) を分けた 2 行に直せ。**重複検査 (typed 層と wire 層) は意図的な二重化であり統合しない** (typed 層は `Integrity.clean()` の proof surface まで見る強い条件、wire 層は consumer parity)。変異登録は親が複合形 (両層同時) に改める。
- **A-5: 対応不要。**

## 検査・報告 (段 5 と同じ義務。加えて)

- 実走: `PYTHONPATH=. python3 -m pytest orchestrator/tests/test_reflux_result_evidence.py orchestrator/tests/test_reflux_formal_consumer.py -q -p no:cacheprovider`。sandbox で走らないなら「実装済み・未実走」と書き、自走 harness (`PYTHONPATH=. python3 orchestrator/tests/<file>`) を試せ。
- `git diff --exit-code` の不変面 (段 5 と同じ 5 対象) rc=0 を報告。
- 新規・改名 nodeid を collection 名で全列挙 (親が台帳へ足す)。
- 段 4 §5 の変異 M1〜M14・M-C1 を殺す nodeid が改名後も実在することを表にせよ。新しい変異候補 (F-1 の束縛を落とす: `ordered_wal_ref["sha256"] == derived.ordered_wal_sha256` の検査削除 → 別 projection 負例で KILLED) を 1 件登録せよ。
- 所見ごとの closed / partial / regressed 対応表を書け。

## 出力形式

H2 見出しで「所見×対応表 (closed/partial/regressed)」「編集面 (file:line)」「実走結果」「不変条件」「nodeid 一覧 (新規・改名)」「変異×nodeid 表」「未完・未実走」を順に書き、最後に `## 総括` (5 行以内)。結合文字 U+0300〜U+036F を使うな。
