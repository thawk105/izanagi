# wave2 — protocol JSON 実凍結 + selector 予測封印の実行可能化 (2026-07-22)

科学レーン第 2 手 ([T-083] (a) の順序どおり、worklog 2026-07-22 (10) 次の一手 1)。
/dev-wave 標準ループ 1 回。branch worktree-dev-wave-ruling-ac、基準 fcf0533。

本書は逐語台帳 (F20 恒久対応 — scratchpad 消失対策の repo 内凍結)。掲載順:

1. §1 親 brief (P1..P7) と前提実測
2. §2 codex プラン起草 (逐語)
3. §3 敵対相談 A (正しさ境界、逐語)
4. §4 敵対相談 B (整合・実効性、逐語)
5. §5 段 4 裁定 (親)
6. §6 敵対レビュー 1 (正しさ境界、逐語)
7. §7 敵対レビュー 2 (裁定整合・完全性、逐語)
8. §8 段 6 裁定と fix
9. §9 焦点再レビュー (逐語)
10. §10 変異台帳 (事前登録・1 巡目・erratum・最終)
11. §11 親の実測記録 (G1 / envelope / isatty live / 全走)

正本の分担: 設計判断 = docs/decisions.md D79、可変状態 = worklog 末尾、
手順パッケージ = worklog 2026-07-22 (11)。

---

## §1 親 brief と前提実測

brief 全文と前提実測は handoff から凍結 (worklog (11) にも要約):

- scope = (i) selector 予測封印の実走配線 + テスト、(ii) protocol JSON 実凍結のユーザー
  引き渡しパッケージ、(iii) 予測封印実走の手順パッケージ。実凍結の実行と予測封印の実走は
  wave 外 (ユーザー手番 receipt → protocol commit が先行)
- P1..P7 の provisional 裁定を攻撃対象として明記 (P4 の FROZEN_MANIFEST「実在 8 ファイル」、
  P5 の receipt 非依存は親実測で確認済みで維持、P2/P3/P7 は相談で条件付き採用、P6 は狭義
  G1 のみ成立と裁定)
- 前提実測 (実 API read-only、模擬なし): v1 freeze bytes == V1 pin (315b1eb8…)、ccbench
  gitlink == 承認定数 (d706650…)、build_protocol_document in-memory dry-run → canonical
  774 bytes / sha256 261cec1c7f423b3eebff41ee716d2bfe2c6fa9a10a9dd86d91eaf71612e74aac、
  selector plan 6 セル、PRODUCTION_PROVIDER = unwired sentinel が唯一の実走残欠
- G1 生死確認 (P6): `claude -p --agent selector-8b` に合成 payload (read 50%/skew 0.5/
  records 12345 — 実在 holdout と非同値、本番 payload 不使用) → rc=0・strict 出力
- envelope 実測: `--output-format json` の top-level 20 keys (codex 想定 7 + 運用 13)。
  modelUsage = [claude-haiku-4-5-20251001 (補助), claude-opus-4-8]
- G1 拡張実測 (文脈隔離): inline agents (--agents JSON) + neutral cwd (repo 外) +
  --setting-sources "" + --strict-mcp-config + --mcp-config <file> + stdin → rc=0・
  strict 出力。罠 = --mcp-config は可変長引数で直後の positional を巻き込む

---


---

## §2 codex プラン起草 (逐語)

## 結論と provisional 裁定

実装は、所有ファイルが交差しない 2 単位が最小です。実凍結・selector 実走は含めず、完了時の期待赤はゼロとします。

| 裁定 | 結論 |
|---|---|
| P1 | 維持。ただし「provider が唯一の残欠」は happy path に限る。production CLI には同時起動ロックが必要。 |
| P2 | 条件付き採用。subprocess provider は妥当だが、固定 argv・canonical stdin・厳格 envelope・単一駆動ロックを加える。`PRODUCTION_PROVIDER` は sentinel のまま。 |
| P3 | 条件付き採用。現行 writer は実凍結領域を拒否するため、通常 API の拒否を保ったまま、正規 path 限定の人間 opt-in 経路が必要。 |
| P4 | 維持。現行 manifest は実在 8 ファイルを検査するため、本 wave では変更しない。 |
| P5 | 維持。builder は receipt を参照しない。receipt 先行はユーザー手順で強制する。 |
| P6 | 完了扱い。handoff に合成 payload での G1 成功が記録済み。 |
| P7 | 維持。ただし commit 対象は JSON 単体でなく、参照 raw・payload・journal を含む証拠集合とする。 |

重要な残存限界があります。[runner:463-470](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/campaign/s8b_prediction_runner.py:463) は claim 後 crash の `missing` を prediction freeze にできず拒否します。一方、R3 設計は `choice_id=null` で凍結するとしています。この wave では既存テストの受理集合を変えず、claim-crash は「selector 実験全体が判定不能、prediction file なし、floor へ進まない」という終端に固定します。missing row を JSON に残すことまで必須なら、別途 schema/journal 拡張が必要です。

## 実装単位 1 — production selector provider と seal CLI

所有ファイル:

- `orchestrator/campaign/s8b_prediction_runner.py`
- `orchestrator/tests/test_s8b_prediction_runner.py`

変更点:

1. [s8b_prediction_runner.py:29-39](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/campaign/s8b_prediction_runner.py:29)

   `argparse`、`contextlib`、`fcntl`、`subprocess`、`sys`、`uuid` を追加し、repo root、固定 journal/artifact/prediction path、timeout、Claude result-envelope の許容 field を定義する。

2. [s8b_prediction_runner.py:100-125](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/campaign/s8b_prediction_runner.py:100)

   `ClaudeHeadlessProvider` callable を追加する。`PRODUCTION_PROVIDER = unwired_provider` は変更しない。constructor/preflight で次を claim 前に検査する。

   - `claude` executable が解決可能
   - `.claude/agents/selector-8b.md` が通常ファイル
   - frontmatter が `name=selector-8b / model=opus / effort=high / tools=[]`
   - role bytes の SHA-256 を一度固定
   - production source 5 ファイルが存在し root 配下である

3. [s8b_prediction_runner.py:144-159](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/campaign/s8b_prediction_runner.py:144)

   Claude CLI の outer JSON envelope 専用 strict parser を追加する。duplicate key、非有限数、未知 field、非 object を拒否し、次を要求する。

   - `type=="result"`
   - `subtype=="success"`
   - `is_error is False`
   - `num_turns==1`
   - `permission_denials==[]`
   - `result` が `str`
   - `session_id` が正しい UUID。ただし永続 provenance には記録しない

   `result` の中身は解釈・修復・fence 除去をせず、そのまま `ProviderResponse.raw_response` にする。inner response の受理は引き続き [record_agent_attempt:370-395](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/campaign/s8b_selector_freeze.py:370) だけが行う。

4. [s8b_prediction_runner.py:330-340](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/campaign/s8b_prediction_runner.py:330)

   canonical payload bytes helper を置き、payload artifact と subprocess stdin が同一 bytes を使うよう統一する。`selector_payload_sha256(payload)` と送信 bytes の SHA-256 も照合する。`target_holdout` や `arm` は prompt に加えない。

5. subprocess 呼び出しは shell なし、1 セル 1 process、再試行なしで固定する。

```python
[
    "claude", "-p",
    "--agent", "selector-8b",
    "--model", "opus",
    "--effort", "high",
    "--tools", "",
    "--input-format", "text",
    "--output-format", "json",
    "--permission-mode", "dontAsk",
    "--setting-sources", "project",
    "--disable-slash-commands",
    "--strict-mcp-config",
    "--mcp-config", '{"mcpServers":{}}',
    "--no-session-persistence",
]
```

   `subprocess.run(..., input=canonical_payload_bytes, stdout=PIPE, stderr=PIPE, cwd=ROOT, timeout=1200, check=False)` とする。stdout は UTF-8 strict、最大 1 MiB。nonzero rc、timeout、OS error、invalid envelope は `PredictionRunnerError` とし、既に durable な claim は permanent missing のまま残す。

6. provenance 8 field は次のように埋める。

| field | 値 |
|---|---|
| `child_id` | subprocess 前に生成する公開安全なローカル UUID。Claude `session_id` は保存しない |
| `role_file_sha256` | preflight で読んだ selector role bytes の SHA-256 |
| `model` | CLI/frontmatter pin の `"opus"` |
| `started_at` | subprocess 直前の UTC ISO-8601 |
| `finished_at` | success envelope 取得直後の UTC ISO-8601 |
| `fresh_context` | `True`。新 process、resume/continue なし |
| `declared_tools` | `[]` |
| `observed_tool_events` | `[]`。tool surface が空で、permission denial も空である場合だけ |

7. [PredictionJournal:161-233](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/campaign/s8b_prediction_runner.py:161)

   production CLI が journal inode に `flock(LOCK_EX|LOCK_NB)` を保持する context manager を追加する。現行は二プロセスが同じ空 journal を読んだ後、両方が claim・provider call できるため、O_APPEND だけでは at-most-once を満たさない。crash 時は OS が lock を解放し、journal claim に基づく再開は可能。

8. [s8b_prediction_runner.py:535-560](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/campaign/s8b_prediction_runner.py:535) の後に `seal` CLI を追加する。

   - サブコマンド: `seal`
   - `--provider` は `unwired|claude-headless`、default は `unwired`
   - `--pre-oracle-head` は必須、現在の `HEAD` と完全一致を要求
   - journal/artifact/prediction の path override は提供せず、正規 namespace に固定
   - `HEAD` に `output/s8b-freeze/floor_protocol.json` が blob として存在することを claim 前に確認
   - predictions が既存なら claim 前に拒否
   - source records と execution policy を固定値から構成
   - lock 内で `drive_journal` → `materialize_predictions`
   - `HEAD` と source hashes の不変を materialize 前に再確認
   - 書込み後、`verify_prediction_freeze` を即時実行してから成功 JSON を出す

   `seal` だけを指定しても sentinel が claim 前に拒否し、`--provider claude-headless` が唯一の opt-in になる。

P2 代案比較は次の 3 行で足ります。

- subprocess 案は承認済み role/frontmatter と既存 Claude 認証を再利用でき、最小変更。
- 二相 journal API は既に `claim → provider → receipt` として存在し、provider の代替ではなく併用対象。
- Anthropic API 直呼びは role・tool 遮断・model/effort・認証を再実装するため、未承認面が広い。

## 実装単位 2 — protocol 人間凍結 CLI

所有ファイル:

- `orchestrator/campaign/s8b_floor_campaign.py`
- `orchestrator/tests/test_s8b_protocol_builder.py`

変更点:

1. [s8b_floor_campaign.py:292-421](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/campaign/s8b_floor_campaign.py:292)

   builder は変更しない。新 CLI も必ず `build_protocol_document` を通し、承認値、v1 bytes、gitlink、env contract、holdout conjunction gate を共用する。

2. [s8b_floor_campaign.py:424-481](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/campaign/s8b_floor_campaign.py:424)

   現行の public `write_protocol_document()` は既定の凍結領域拒否を維持する。内部 user-freeze capability を追加し、次をすべて満たす場合だけ例外的に許可する。

   - CLI の `--confirm-user-freeze` が明示されている
   - destination が正確に `ROOT/output/s8b-freeze/floor_protocol.json`
   - root/path override なし
   - 通常 API 呼び出しから capability を得られない

   これは人間認証ではなく誤操作防壁である、とコメントにも明記する。

3. exclusive-create は必須。現行の temporary file + `fsync` + `os.link` + directory `fsync` を再利用し、既存 destination は上書きしない。

4. [s8b_floor_campaign.py:2947-3006](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/campaign/s8b_floor_campaign.py:2947)

   `freeze-protocol` を先頭 argv で dispatch する。既存の `--mode ... --protocol ...` grammar はそのまま残し、official rejection 集合を変えない。

   引数:

```text
freeze-protocol
  --master-seed TEXT               required
  --env-tag TEXT                   required
  --stock-configuration TEXT       required
  --extime-s INT                   required
  --wired-min-rel-floor FLOAT      required
  --out PATH                       required、正規 path 完全一致
  --confirm-user-freeze            required opt-in
```

5. write 後に同じ process で次を再確認する。

   - raw bytes == `BuiltProtocol.canonical_bytes`
   - byte SHA-256 == `BuiltProtocol.sha256`
   - `load_protocol` の strict parse 成功
   - `validate_protocol(parsed) == BuiltProtocol.document`

   成功出力は `{status,path,byte_length,sha256}` の JSON。post-write 検査失敗時は自動削除せず停止し、人間に commit 禁止を伝える。

## 新規テスト

既存テストは書き換えず、新規追加だけにします。

| 新規テスト | 検査内容／受理集合の変化 |
|---|---|
| `test_claude_provider_uses_pinned_argv_and_canonical_stdin` | 上記 argv、shell なし、1200 秒、canonical stdin だけを新たに受理 |
| `test_claude_provider_emits_exact_eight_field_provenance_without_session_id` | 正しい success envelope から exact 8 field を生成。CLI session ID の永続化は拒否 |
| `test_claude_provider_rejects_failed_or_malformed_envelope` | rc、timeout、duplicate、unknown field、error subtype、複数 turn、permission denial を新規拒否 |
| `test_claude_result_reaches_strict_parser_unmodified` | fenced inner result を provider が修復せず、既存 strict parser が invalid/null にする |
| `test_claude_timeout_after_durable_claim_is_not_retried` | timeout 後の claim が permanent missing、invocation なし、再 drive でも同セル非呼出 |
| `test_seal_cli_requires_explicit_headless_provider_before_claim` | opt-in なしでは subprocess・claim ともゼロ |
| `test_seal_cli_rejects_second_concurrent_driver` | 同一 journal の二つ目の production driver を provider call 前に拒否 |
| `test_seal_cli_drives_four_agent_and_two_static_cells_then_verifies` | mocked provider で 4 独立 call、off 2 static c06、prediction exclusive-create、全体 verifier 通過 |
| `test_seal_cli_requires_protocol_blob_at_exact_pre_oracle_head` | 任意の実在 commit ではなく、現在 HEAD と protocol blob の組を新 CLI だけが受理 |
| `test_freeze_protocol_cli_real_values_match_expected_receipt` | 確定 5 値から 774 bytes、`261cec…aac`、正規 path を生成 |
| `test_freeze_protocol_cli_requires_confirmation_and_exact_path` | confirm 欠落・別 path は write 前拒否 |
| `test_freeze_protocol_cli_preserves_existing_destination` | 二度目は exclusive-create 拒否、既存 bytes 不変 |

既存の [official CLI test:846-853](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/tests/test_s8b_floor_campaign.py:846)、[prediction exclusive-create test:500-508](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/tests/test_s8b_selector_freeze.py:500)、[generic crash test:117-157](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/tests/test_s8b_prediction_runner.py:117) は非変更の回帰 gate として使います。

## 変異テスト事前登録

| ID | 変異位置 | 手前に同じ拒否がない確認 | 一意に赤くなる理由 |
|---|---|---|---|
| M1 | runner:403-407 の sentinel pre-claim 判定を削除 | job/payload gate は provider identity を見ない | default provider で claim が 1 件生じる |
| M2 | 新 provider argv から `--agent selector-8b` を削除 | frontmatter 検査はファイルを検査するだけで、実 command への適用を保証しない | argv capture の named-agent assertion だけが落ちる |
| M3 | canonical bytes でなく pretty JSON/argv で payload を渡す | `_payload_for_job` は Mapping hash だけで実送信 bytes を見ない | stdin SHA/bytes assertion が落ちる |
| M4 | rc=0 の `subtype!=success` または `is_error=True` を受理 | subprocess rc gate は rc=0 を通す | malformed-envelope 負例が ProviderResponse 化して落ちる |
| M5 | `seal` の default provider を headless にする | downstream sentinel 判定は headless callable を sentinel と認識しない | opt-in 無しで subprocess/claim が発生 |
| M6 | journal flock を外す | O_APPEND は二重 claim を防がず、snapshot resolve も一度だけ | 二重 driver fixture で provider call が 2 回になる |
| M7 | runner:441-445 の `record_agent_attempt` を直接 decode に置換 | outer envelope parser は inner response を受理判定しない | fenced output が invalid でなく受理され、strict-path test が落ちる |
| M8 | protocol writer の `os.link` を overwrite 書込みへ置換 | link より前に destination existence gate はない | 二度目が成功し、existing-destination test が落ちる |

## ユーザー引き渡し骨子 — protocol 実凍結

親が worklog に転記する内容です。実行者はユーザーです。

```bash
# 0. T-080 receipt と clean state
python3 orchestrator/campaign/t080_freeze_migration.py verify \
  --path output/t080-migration/legacy-freeze-repin.receipt.json
git status --short

# 1. 人間 opt-in の protocol 実凍結
PYTHONPATH=orchestrator python3 -m campaign.s8b_floor_campaign freeze-protocol \
  --master-seed '2026-07-18T17:16:12+09:00' \
  --env-tag pegasus \
  --stock-configuration stock_common \
  --extime-s 5 \
  --wired-min-rel-floor 0.03 \
  --out output/s8b-freeze/floor_protocol.json \
  --confirm-user-freeze

# 2. 独立照合
test "$(wc -c < output/s8b-freeze/floor_protocol.json)" -eq 774
printf '%s  %s\n' \
  '261cec1c7f423b3eebff41ee716d2bfe2c6fa9a10a9dd86d91eaf71612e74aac' \
  'output/s8b-freeze/floor_protocol.json' | sha256sum -c -
python3 -m json.tool output/s8b-freeze/floor_protocol.json >/dev/null
```

その後、ユーザーが staged path がこの 1 ファイルだけであることを確認し、`AI-Agent: none` で commit します。既存 file、hash 不一致、post-write error のいずれかが出たら上書き・削除・再生成をせず停止します。

## 親 AI 実行骨子 — selector 予測封印

protocol commit 後、floor データを閲覧する前だけ実行します。

```bash
PROTOCOL_HEAD="$(git rev-parse HEAD)"
git status --short

PYTHONPATH=orchestrator python3 -m campaign.s8b_selector_freeze plan

PYTHONPATH=orchestrator python3 -m campaign.s8b_prediction_runner seal \
  --provider claude-headless \
  --pre-oracle-head "$PROTOCOL_HEAD"

PYTHONPATH=orchestrator python3 -m campaign.s8b_selector_freeze verify \
  --path output/s8b-freeze/selector_predictions.json \
  --freeze output/s8b-freeze/holdout_freeze.json \
  --root .
```

成功時に commit する証拠集合は次です。

- `output/s8b-freeze/selector_predictions.json`
- `output/s8b-freeze/selector-runs/journal.jsonl`
- agent 4 セル分の `payload_*.json`
- agent 4 セル分の `raw_*.txt`

prediction commit は `AI-Agent: none` ではなく、実際の product/model/reasoning を記録した AI trailer を付けます。invalid raw は `choice_id=null` の正当な封印結果なので再試行しません。claim のみ残った場合は削除・別 journal・再呼出をせず、selector 実験全体を判定不能として floor を止めます。

protocol と prediction の実ファイルが commit された後、別の後続 commit で初めて `FROZEN_MANIFEST` に両 hash を追加します。

## 検証と期待赤

期待赤ゼロです。artifact 未存在を理由とする xfail や manifest 先行追加は置きません。

この sandbox では pytest を実行していないため、green は主張しません。親実装後の対象は少なくとも次です。

```bash
python3 -m pytest \
  orchestrator/tests/test_s8b_prediction_runner.py \
  orchestrator/tests/test_s8b_protocol_builder.py \
  orchestrator/tests/test_s8b_selector_freeze.py \
  orchestrator/tests/test_s8b_floor_campaign.py
python3 tools/run_tests.py
python3 tools/check_codex_agents.py
python3 tools/check_docs.py
```

commit 後に `python3 tools/check_ai_provenance.py` を実行します。


---

## §3 敵対相談 A — 正しさ境界レンズ (逐語)

判定は **REJECT**。静的検査のみで、pytest は実行していない。

Refuted は、P1 / P2 / P3 / P5 / P6 / P7。P4 は「今は追加しない」部分ではなく、「後で protocol/prediction 2 ファイルだけを加える」という証拠閉包が refuted。

## BLOCKER

1. **承認済み R3 の missing 意味論を逆転している**  
   Refuted: **P1、実装単位1、残存限界、既存テスト非変更**。承認済み契約は claim 後 crash を `choice_id=null` の missing row として凍結するものだが、プランは prediction file 自体を作らない。[R3 裁定](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/output/insights/2026-07-16_s8b-ruling-package.md:221) は明記済みで、現実装の拒否は [build_rows_from_journal](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/campaign/s8b_prediction_runner.py:463)、その誤動作を固定する既存テストは [test_s8b_prediction_runner.py:155](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/tests/test_s8b_prediction_runner.py:155)。missing schema 修正には、所有外とされた [s8b_selector_freeze.py:482](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/campaign/s8b_selector_freeze.py:482) も必要になる。  
   **影響:** 承認済みなら「6-row prediction + 該当条件 indeterminate」となる入力が、「prediction 不在・レポート不能・floor 停止」へ変わる。

2. **確定済み自由値を CLI が pin せず、自己整合だけで誤 protocol を凍結する**  
   Refuted: **P3、P5、protocol CLI 項目4/5、seal の protocol blob gate**。現 validator は `env_tag` を登録済みに限定するだけで、`stock_configuration` と `master_seed` は非空なら通し、`wired_min_rel_floor` は `(0,1]` 全域を通す。[s8b_floor_contract.py:138](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/campaign/s8b_floor_contract.py:138)、[同:153](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/campaign/s8b_floor_contract.py:153)、[同:192](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/campaign/s8b_floor_contract.py:192)。プランの post-write 検査は writer と builder と validator の相互自己一致であり、固定値 `774 bytes / 261cec…aac` との独立照合ではない。shell の hash 検査は create-only 書込み後なので、失敗時には正規 path が既に焼けている。  
   **影響:** `master_seed` は schedule、`env_tag` は環境契約、`stock_configuration` はセル集合、`wired_min_rel_floor` は floor 値を変え、最終レポートと certified 判定を別実験の値へ変える。

3. **既存 journal を別時点の `pre_oracle_head` へ洗浄できる**  
   Refuted: **P2、P4、P7、seal 項目7/8**。journal に header/run identity がなく、`JOURNAL_SCHEMA_VERSION` も記録されない。[runner:78](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/campaign/s8b_prediction_runner.py:78)。公開 `drive_journal` へ fake provider を注入して4セルを先に resolved にすれば、後の `seal --provider claude-headless` は [status があるセルを無条件 skip](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/campaign/s8b_prediction_runner.py:398) し、Claude を一度も呼ばず現在の `pre_oracle_head` で materialize する。journal は protocol HEAD、source 集合、CLI identity、provider 種別に束縛されていない。payload path も final row から消える。[runner:506](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/campaign/s8b_prediction_runner.py:506)。  
   **影響:** fake/旧 invocation の任意 `c01..c06` が headless 実走結果として受理され、certified 選択値とレポートの実行参照が改変される。

4. **「人間だけが protocol を凍結」と receipt 先行は機械境界でなく規律だけ**  
   Refuted: **P3、P5、字義どおりなら P7**。現 writer は実凍結領域を明示拒否する [第二防壁](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/campaign/s8b_floor_campaign.py:432) だが、プランは同じ Python module にその bypass capability を追加する。`--confirm-user-freeze` は boolean であり actor 認証ではない。さらに hook は script 内書込みを見ず、s8b-freeze の Bash 書込みも保護外、Codex には未配線である。[hooks/README.md:15](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/hooks/README.md:15)、[同:169](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/hooks/README.md:169)、[同:183](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/hooks/README.md:183)。handoff も receipt verify と次工程を `&&`/`set -e` で結ばず、`git status --short` は表示だけである。  
   **影響:** 受理集合に「receipt 不成立・順序違反・AI 実行」の protocol が入り、protocol 値または user-authorization 参照が偽装される。

5. **生成する証拠集合が既存 floor clean-scan に必ず拒否される**  
   Refuted: **P1、P4、P7**。floor preflight は `output/s8b-freeze/` の全 file を exact allowlist で検査し、未知 file を拒否する。[s8b_floor_campaign.py:1197](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/campaign/s8b_floor_campaign.py:1197)。ところが呼出側の allowlist は現在 holdout freeze 1件だけである。[同:2439](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/campaign/s8b_floor_campaign.py:2439)。protocol、prediction、journal、payload、raw はすべて拒否対象になり、`FROZEN_MANIFEST` はこの runtime allowlist に使われない。  
   **影響:** public official gate を開いても floor は preflight refusal のままで、floor 値・実測レポート・certified 結論はいずれも生成されない。

6. **`pre_oracle_head` は issuer-only の恒真ゲートで、late forge を consumer が見抜けない**  
   Refuted: **P2、P6、P7、seal の HEAD gate**。authoritative verifier が確認するのは commit の存在だけで、prediction 導入 commit の parent、exact diff、protocol blob 内容、oracle marker 不在を検査しない。[s8b_selector_freeze.py:617](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/campaign/s8b_selector_freeze.py:617)。公開 builder で oracle 観測後に文書を作り、任意の古い実在 commit を `pre_oracle_head` にすれば、[verdict consumer](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/campaign/s8b_verdict.py:199) は seal CLI を通ったか識別できない。seal 自身についても v1 bytes を read-once trust root へ照合する計画・負例テストがない。  
   **影響:** oracle 観測後に cherry-pick した choice を「予測封印済み」として受理でき、三条件と certified 結論を任意方向へ変えられる。

## MUST-FIX

7. **journal inode の `flock` は at-most-once の境界になっていない**  
   Refuted: **P2 項目7、M6**。lock は production CLI にしかなく、公開 `drive_journal` は従わない。さらに append は locked fd ではなく毎回 path を開き直す。[runner:207](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/campaign/s8b_prediction_runner.py:207)。lock 中に journal path を rename/recreate すれば別 inode を lock できる。claim 自体を lower layer で atomic にしない限り、advisory lock は協調 driver の事故しか防がない。  
   **影響:** 同一セルに複数 Claude 呼出しが発生し、journal は二重 claim で汚染、prediction 不在または cherry-pick 可能な複数 raw が残る。

8. **8-field provenance の大半が実測でなく宣言・推定**  
   Refuted: **P2 項目6、P7**。`child_id` は CLI session と無関係な UUID、`model="opus"` は要求 alias、`observed_tool_events=[]` は empty denial からの推定である。実測 envelope には Opus と Haiku の両方が現れるのに `modelUsage` を捨てる。現 verifier は model を非空文字列として見るだけで、fresh/tools も固定値一致しか確認しない。[s8b_selector_freeze.py:223](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/campaign/s8b_selector_freeze.py:223)。outer envelope/session の sanitized digest も永続化されない。  
   **影響:** ledger/report の child・model・tool provenance が実呼出しと乖離したまま、意図しないモデルが選んだ choice を certified 入力として受理する。

9. **P6 は production argv の生死確認になっていない**  
   Refuted: **P6、constructor preflight、期待赤ゼロ**。G1 は単純な `claude -p --agent ...` であり、固定 argv 全体、空 tools、strict MCP、project settings、stdin bytes、cwd、envelope parser の組合せを走らせていない。[handoff:20](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/docs/handoff/2026-07-22-protocol-freeze-prediction-seal.md:20)。`--help` に flag が存在することは実効性検査ではない。最初の exact command は durable claim 後になる。  
   **影響:** flag interaction・version drift・tool遮断不発が最初の本番セルを permanent missing にするか、汚染された choice を provenance 上 toolsなしとして受理させる。

10. **outer envelope の未知 field 全拒否は false red、既知 field 放置は false green**  
    Refuted: **P2 項目3、malformed-envelope test**。CLI version を pin せず観測一回の exact field set を凍結すると、無害な metadata 追加だけで rc=0 の正当応答を失う。既存の別 consumer ですら compatibility field set を別に持つ。[tools/dev_waves/receipt.py:20](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/tools/dev_waves/receipt.py:20)。一方、許容する `modelUsage`、`api_error_status`、terminal fields を意味照合しないなら、相互矛盾 envelope を success と扱える。  
    **影響:** 正当応答が missing へ落ちて prediction 不在になる一方、不正 envelope の `result` が choice として受理される方向も残る。

11. **executable・role・環境の TOCTOU で実呼出し identity を差替えられる**  
    Refuted: **P2 項目2/5/6**。preflight で executable を resolve しても、固定 argv は再び文字列 `"claude"` を PATH 解決する。role hash も一度読むだけで、subprocess が `--agent` を解決するまでに差替え・復元できる。`subprocess.run` に sanitized `env` もなく、endpoint/model/settings に効く環境を丸ごと継承する。materialize 前の再hashは一時差替えを検出しない。  
    **影響:** fake executable または別 role が返した choice を、元 role SHA・model opus の選択として ledger と prediction に記録できる。

12. **payload/raw の writer と post-write 検査に洗浄経路がある**  
    Refuted: **P2 項目4/5、P7、selector post-write verify**。現 `_write_bytes_bound` は `O_TRUNC` で symlink を追い、単一 `os.write` 後に「意図した data」の hash を返すだけで実 file を読まない。[runner:343](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/campaign/s8b_prediction_runner.py:343)。payload path/hash は final prediction verifier に届かない。selector の「書込み後 verify」も destination を strict reload する記述がなく、返された in-memory document を検証すれば恒真になる。protocol 側も複数回 read ではなく read-once parse が必要。  
    **影響:** stdin と payload artifact、raw reference、disk 上 prediction のいずれかを差替えても成功表示または後続受理が残り、レポートが参照する入力・choice が実呼出しと異なる。

13. **source closure が実際の strict parser を含まない**  
    Refuted: **P2 の production source 5 files、P7 証拠集合**。`sources.output_schema` は JSON schema を指すが、再検証に使う実装は `s8b_selector_output.py` であり source 集合にない。[source 定義](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/tests/test_s8b_prediction_runner.py:332)、[実 parser 呼出し](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/campaign/s8b_selector_freeze.py:180)。runner/envelope parser/settings も evidence closure 外である。  
    **影響:** source hash が不変なまま parser drift で同じ raw の `valid/invalid` が変わり、choice と判定不能集合が変化する。

14. **M1..M8 は単一理由性・発火性を満たさない**  
    Refuted: **変異事前登録全体**。M3 は pretty JSON と argv 送信を混在、M4 は subtype と is_error の二変異、M6 は snapshot→claim 間の deterministic barrier がなく mutant が偶然一回呼出しで通り得る。M7 の「直接 decode」は通常の `json.loads` なら fence を依然拒否するため、記載した赤にならない。[strict decoder](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/campaign/s8b_selector_output.py:52)。M2 は mocked argv assertion だけで、成果物受理/fail-closed の差を観測しない。固定5値、stale journal、late forge、modelUsage、v1 trust root、artifact swap の mutants もない。  
    **影響:** strict-path・at-most-once・protocol pin を壊した実装が変異 gate を緑で通り、certified choice または missing 受理集合を変えたまま出荷される。

## SHOULD-FIX

15. **journal の「strict」は field set 以外が未検証**  
    `seq` の型・連続性・一意性、SHA/path/timestamp、invocation tagged-union を journal layer で検査せず、blank line も無視する。[runner:182](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/campaign/s8b_prediction_runner.py:182)、[同:236](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/campaign/s8b_prediction_runner.py:236)。`os.write` の short write 処理もない。  
    **影響:** prediction が同じでも committed 台帳の seq・時刻・path 参照を改変でき、レポートの試行順・帰属監査値が変わる。

16. **固定 production path の happy-path tests に hermetic seam がない**  
    `freeze-protocol` と `seal` は path override を禁止する一方、成功テストは正規 path への実書込みを要求する。private test root/temp Git repo の設計がなく、mock すれば exclusive-create・fsync・readback が発火しない。既存 writer テストは実 repo 不変を明示している。[test_s8b_protocol_builder.py:238](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/tests/test_s8b_protocol_builder.py:238)。  
    **影響:** 実テストが user-only artifact を先に生成して protocol 参照を汚すか、mock-only テストが不正 writer を受理して実凍結時の値を保証しない。


---

## §4 敵対相談 B — 整合・実効性レンズ (逐語)

判定は **NO-GO**。承認済み受理集合・証拠束縛・実行手順の三面で止まる。

## BLOCKER

1. **claim-crash を「prediction file なし」にするのは明示的な裁定違反**  
   **refuted: P1、プラン「重要な残存限界」、test_claude_timeout...**  
   §9 項5は不正・欠測セルを `choice_id=null` で凍結し、R3 は claim 後 crash も同じ missing 行にすると明記している。[§9 項5](</home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/docs/phase3-8b-descriptor-design.md:304>)、[R3](</home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/output/insights/2026-07-16_s8b-ruling-package.md:221>)。現 schema はすでに `status="missing"` を受理し、verdict も null を三値伝播する。[schema](</home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/campaign/s8b_selector_freeze.py:463>)、[consumer](</home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/campaign/s8b_verdict.py:43>)。障害は schema 不在ではなく、runner が意図的に materialize を拒否する箇所と、agent provenance を missing にも要求する実装である。[runner](</home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/campaign/s8b_prediction_runner.py:463>)。しかも既存テストがこの誤動作を固定しており、「既存テストは書き換えない」と両立しない。[既存テスト](</home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/tests/test_s8b_prediction_runner.py:155>)。  
   **影響:** 承認済みの「6 行中 missing 行が null」という受理集合が「予測ファイル不在」に変わり、swapped 期待値・判定不能レポート・台帳参照が生成不能になる。

2. **確定済み protocol 5 値を CLI も seal も固定していない**  
   **refuted: P3、seal CLI 項目、protocol 新規テスト項目**  
   builder 自身が master seed、env tag、stock、wired floor を「自由値」として扱い、validator も文字列・登録 env・範囲しか検査しない。[builder](</home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/campaign/s8b_floor_campaign.py:330>)、[validator](</home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/campaign/s8b_floor_contract.py:138>)、[wired floor](</home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/campaign/s8b_floor_contract.py:192>)。seal 側は HEAD に同名 blob があることしか要求せず、774 bytes、承認 hash、strict protocol 内容、`AI-Agent: none` 導入 commit を検査しない。正例テスト一件では誤値の受理を殺せない。  
   **影響:** seed・環境・stock baseline・floor 閾値が承認値と異なる protocol でも予測封印へ進み、測定順、floor 値、最終 certified 判定が変わる。

3. **T-083 の receipt → protocol 順序は手順上も強制されない**  
   **refuted: P5**  
   T-083 は明確に receipt → protocol → prediction の順序を凍結している。[T-083](</home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/docs/worklog.md:58>)。ところが `freeze-protocol` は receipt を検査せず、handoff の `verify` と後続コマンドは `set -e` や `&&` で接続されていない。実際、現状態の verify は `state=never-issued`、rc=2 であるが、通常の shell は次行を実行する。[verify rc 契約](</home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/campaign/t080_freeze_migration.py:2062>)。`git status --short` も表示するだけで dirty を拒否しない。  
   **影響:** Git 履歴が protocol → receipt → prediction の逆順でも通り、prediction の `pre_oracle_head` と後続レポートが承認順序を証明しない参照になる。

4. **Claude 呼出しは「payload だけ」の隔離になっていない**  
   **refuted: P2、provider 項目 2/5/6**  
   role 契約は filesystem 等を遮断し、入力 JSON 一個だけをデータにすると定める。[role](</home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/.claude/agents/selector-8b.md:19>)。しかし argv は `cwd=ROOT`、`--setting-sources project` で、`--bare` を使わない。実 `claude --help` は、通常モードが CLAUDE.md auto-discovery、auto-memory、cwd/env/git-status 等の dynamic system context を持つことを示している。さらに runner は各 call 前に payload/journal を repo に作るため、後続セルの git status も変わる。[書込み順](</home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/campaign/s8b_prediction_runner.py:409>)。frontmatter の事前 read と CLI の `--agent` による再読込も同一 bytes ではなく、A→B→A の一時差替えを終端 hash 再確認では捕捉できない。  
   **影響:** 同じ payload hash でも CLAUDE.md、memory、git status、差し替わった role によって choice が変わり、予測ファイルは「payload のみで選んだ」と虚偽認証される。

5. **journal・protocol HEAD・最終 prediction の証拠鎖が切れている**  
   **refuted: P2 項目7/8、P7**  
   journal claim には payload とセルしかなく、`pre_oracle_head`、protocol hash、source 集合がない。[claim schema](</home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/campaign/s8b_prediction_runner.py:82>)。一方 `pre_oracle_head` は materialize 時に外から後付けされる。[materialize](</home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/campaign/s8b_prediction_runner.py:535>)。したがって head A で解決済み journal を、protocol だけ変更した head B で再開して B を pin できる。最終 prediction schema も journal hash/path を持たず、verifier は commit の実在と現在の source file しか検査しない。[document keys](</home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/campaign/s8b_selector_freeze.py:73>)、[commit 検査](</home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/campaign/s8b_selector_freeze.py:618>)。  
   **影響:** 別 protocol 下の呼出結果や、at-most-once journal を伴わない手組み prediction が同じ verifier 受理集合に入り、certified choice と proof-chain の HEAD 参照を付け替えられる。

## MUST-FIX

6. **P3 は承認済み C4-7 防壁の公開 bypass である**  
   **refuted: P3**  
   現 writer は実 `output/s8b-freeze/` を拒否し、既存テストもその受理集合を固定する。[writer](</home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/campaign/s8b_floor_campaign.py:432>)、[test](</home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/tests/test_s8b_protocol_builder.py:238>)。hook も同 namespace の直接 Write を誤操作防壁として拒否する。[hook](</home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/hooks/guard_write.py:86>)。公開 CLI flag は人間認証ではなく、AI も同じコマンドを Bash から実行できる。これは実装詳細でなく、C4-7 の受理集合変更なので再裁定が要る。  
   **影響:** AI または誤操作が protocol を先に exclusive-createし、後から `AI-Agent: none` commit に載せると、protocol の人間生成 provenance 参照が偽になり、正しい再生成も塞がれる。

7. **invocation provenance は実 invocation に束縛されない**  
   **refuted: provider 項目6、P7**  
   `child_id` はローカル UUIDだが CLI の `session_id` と一致させず、実 session との相関がない。outer envelope は検査後に捨てられ、journal には `modelUsage`、permission 情報、argv、Claude version の証拠が残らない。`model="opus"` も実 envelope が表示した concrete slug ではない。現 verifier は8 fieldの自己申告形状しか検査しない。[provenance validator](</home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/campaign/s8b_selector_freeze.py:223>)。commit trailer 規約は実行面が示す slug と、実質寄与した全構成を要求する。[規約](</home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/docs/ai-provenance.md:18>)。実測された haiku 補助の寄与判定も、envelope を捨てれば後からできない。  
   **影響:** 台帳の child/model/tools/fresh-context 値と commit の AI-Agent cohort が実走と食い違い、prediction の選択値が同じでも監査・レポートの provenance 参照が変わる。

8. **G1 は production argv の生死確認になっておらず、mock テストも穴を埋めない**  
   **refuted: P2 の実走可能性主張。P6 は狭い G1 としてのみ成立**  
   記録された G1 は `claude -p --agent selector-8b "<payload>"` だけで、stdin、JSON envelope、empty tools、dontAsk、strict MCP、no persistence の組合せを踏んでいない。[handoff](</home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/docs/handoff/2026-07-22-protocol-freeze-prediction-seal.md:28>)。argv capture の mocked `subprocess.run` は、実 CLI の option 相互作用・認証・cwd context・process fresh 性を検査しない。さらに未知 top-level field 拒否は CLI update の telemetry 追加だけで claim 後 failure になる。  
   **影響:** テストが全緑でも本番最初の call が claim 後に失敗し、当該セルが永久 missing、現プランでは prediction file 全体が不在になる。

9. **P4 の「現行8ファイル」は正しいが、後続一括 pin は遅すぎる**  
   **refuted: P4 の延期方針。事実部分は非反証**  
   実 `FROZEN_MANIFEST` は8 entryすべて実在し、全 sha256 も literal と一致した。[manifest](</home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/tests/test_frozen_artifacts.py:33>)。しかし検査は列挙済み path だけなので、protocol commit から prediction 後の別 commitまで protocol は無 pin のままになる。しかも追加予定は2 JSONだけで、at-most-once の根拠である journal は最終 prediction にも manifest にも束縛されない。これは既知の F30 再発形である。[F30](</home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/docs/failures.md:377>)。  
   **影響:** 中間 commitで protocol や journal が差し替わっても manifest gate は赤くならず、protocol SHA、prediction HEAD、試行台帳参照が後から変わる。

10. **「所有ファイルが交差しない2単位」は必要閉包を落としている**  
    **refuted: P1、結論「2単位が最小」、所有ファイル表**  
    R3準拠には少なくとも `s8b_selector_freeze.py` とそのテスト、確定値 pin には承認値の単一源、凍結 pin には `test_frozen_artifacts.py` が必要になる。さらに seal は単位2の protocol を内容検証せず存在だけで消費するので、単位1のテストは偽 blob でしか独立化できない。現在列挙された4ファイルは依存閉包でも素集合でもない。  
    **影響:** 所有表どおり実装すると必要 gate が未実装のまま緑になるか、統合時に未所有ファイルへ場当たり編集が入り、prediction/protocol の受理集合が計画外に変わる。

11. **新規12テストでは謳った保証を検査できず、「期待赤ゼロ」は誤誘導**  
    **refuted: 新規テスト節、検証と期待赤**  
    mocked provider の4 callは4 fresh OS processを証明せず、protocol blob testは内容・hash・trailerを見ず、固定値の負例、receipt 不在、dirty source、journalの別HEAD再利用、missing行のmaterialize、prediction導入commit topologyが欠落している。正しいR3動作へ直すなら、現在「missing は freeze不能」を期待する既存テストを書き換える必要があり、「既存テスト非変更」と「期待赤ゼロ」は同時に成立しない。  
    **影響:** 全テスト緑でも、承認外 protocol、二重文脈 call、誤 HEAD、missing file 不在が受理され、certified 選択・レポート・台帳のいずれも誤った集合になる。

12. **変異事前登録 M1..M8 は少なくとも M3/M4/M6/M7/M8 が有効な単一変異になっていない**  
    **refuted: 変異テスト事前登録節**  

    - M3 は「pretty JSON/argv」という複数の変更を一IDに混ぜている。
    - M4 は `subtype` と `is_error` の別変異を一IDにしている。
    - M6 は lock 除去だけでは、二 driver が双方とも初回 snapshot を読むとは限らない。snapshot直後の barrier がなければ1 callにも2 callにもなり、killが非決定的になる。[snapshot位置](</home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/campaign/s8b_prediction_runner.py:376>)
    - M7 の「direct decode」が具体的パッチでない。単純な `json.loads` なら fenced入力は例外のままで、受理集合が変わらない。
    - M8 は既存 writer テストがすでに二回目拒否を検査しており、新テスト固有の検出力ではない。[既存 detector](</home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/tests/test_s8b_protocol_builder.py:224>)。M1/M7にも同様の既存 detector がある。

    **影響:** matrix が KILLED を報告しても、二重 provider callやstrict-parser迂回が生存し得て、journal呼出回数や accepted choice が変わる。

裏取り上、774 bytes / `261cec…aac`、`PYTHONPATH=orchestrator` の selector plan、現行 manifest 8件の実在・hash一致は確認できた。pytest は制約どおり実行していない。P6は狭義のG1生死確認としてのみ非反証であり、production package の実効性証明にはならない。


---

## §5 段 4 裁定 (親)

相談 A (REJECT・16 所見) / B (NO-GO・12 所見) を受けた裁定の正本は handoff「段 4 裁定」節
から凍結:

- 採用 (scope 内): 単位 S (missing row = provenance null 固定、SCHEMA_VERSION bump なし —
  v1 文書は実走前で不存在)、単位 A (自由値 4 種の承認定数化)、単位 R (journal run_header /
  ClaudeHeadlessProvider = inline agents + neutral cwd + env allowlist / envelope 未知 field
  許容 + 必須 field 意味検証 / envelope raw 保存 / model = modelUsage 実 slug / child_id =
  session_id / flock 内蔵 / writer O_EXCL+read-back / seal CLI)、単位 F (freeze-protocol
  引数レス CLI + isatty + receipt gate / preflight allowlist 拡張)
- C4-7 論点 (相談 B-6/A-4): isatty + receipt + confirm で「人間・受領後・明示確認」に狭める
  = C4-7 の意図の実装であり緩和ではない — 再裁定に送らず D79 に記録
- claim-crash missing: R3 裁定 (ruling-package §R3「missing セルは choice_id=null で凍結され
  §6 の該当条件が判定不能へ倒れる」) が承認済みであることを一次確認 — 実装の freeze 全体
  拒否は承認乖離であり是正を scope 内へ (相談 2 本が独立に BLOCKER)
- scope 外: A-6 late forge の verifier 拡張 = oracle 結線 wave の blocking 前提へ / advisory
  lock 超の排他 = 脅威モデル外の残存限界 / prediction schema への journal hash = §9 承認
  schema を変えず FROZEN_MANIFEST 逐次 pin + oracle 側検証で代替

実装単位: S → A (並列) → R → F (並列)。ファイル所有は素集合。実装子拘束 = monkeypatch
禁止・xfail 禁止・緑主張に実走範囲併記・テスト緩和禁止・docs/commit 禁止。

---


---

## §6 敵対レビュー 1 — 正しさ境界 (逐語)

結論: **REJECT**。BLOCKER 2件、MUST-FIX 4件、SHOULD-FIX 1件。指定 range の `orchestrator/` 全 diff と親ハンクを静的に確認した。

## BLOCKER

### 1. claim-crash の production 再開経路が成立せず、削除すれば at-most-once も破れる

`seal()` は既存 journal を読む前に worktree 全体の clean を要求する一方、`drive_journal()` は claim・payload・envelope 等を未追跡ファイルとして作る。[runner:980](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/campaign/s8b_prediction_runner.py:980) [runner:599](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/campaign/s8b_prediction_runner.py:599) claim 後に provider が落ちると materialize へ到達せず、次の CLI 実行は dirty 拒否になる。[runner:1030](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/campaign/s8b_prediction_runner.py:1030)

実測した ignore 状態でも `selector-runs/` は無視対象でない。既存テストは `seal()` を再起動せず、同一プロセスで `drive_journal()` を直に再呼出しているため、この矛盾を通らない。[test:210](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/tests/test_s8b_prediction_runner.py:210)

さらに partial `selector-runs/` を削除すれば clean に戻り、同一セルを再呼出できる。逆に payload 書込み後・claim 前に crash すると、再開時は create-only payload が衝突して永久停止する。

**放置時の成果物影響:** 本来1セルだけ `missing` となる事象が prediction 全体不在へ変わり、cleanup 後の再走では同一セルの二度目の `choice_id` が採用され、certified 判定・selected/tie と試行台帳件数が変わる。

### 2. `claude-headless` は名前だけで、任意 executable が certified choice を偽造できる

実行体は ambient `PATH` の `shutil.which("claude")` で解決するだけで、path/hash/version の trust pin が header・prediction のどこにもない。[runner:781](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/campaign/s8b_prediction_runner.py:781) repo 外の fake executable を `PATH` 先頭に置けば clean gate に触れず、任意の strict JSON と自己申告 `session_id` / `modelUsage` を返せる。

加えて public callable は `provider_runner` と `claude_executable` を注入可能である。[runner:966](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/campaign/s8b_prediction_runner.py:966) 実際、成功 E2E テスト自身が fake runner/executable だけで封印成功を作っている。[test:954](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/tests/test_s8b_prediction_runner.py:954)

**放置時の成果物影響:** 攻撃者が `rows[].choice_id`、`binding_key`、`agent_provenance.model/child_id` を任意化でき、それらを使う combined verdict の条件値と最終 status が変わる。[verdict:621](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/campaign/s8b_verdict.py:621)

## MUST-FIX

### 3. `isatty` は人間認証でなく、receipt/test seam も Bash から直呼びできる

argv 経由では seam を渡していない点は確認した。[floor:3120](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/campaign/s8b_floor_campaign.py:3120) しかし AI は PTY を割り当てれば production CLI の `sys.stdin.isatty()` を通せる。さらに module import からは、実 `ROOT` を既定にしたまま `isatty_fn=lambda: True` と偽 `receipt_verify_fn` を渡せる。[floor:497](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/campaign/s8b_floor_campaign.py:497) guard を持たない `_write_protocol_document_create_only()` の直接呼出しでも同じ path に書ける。[floor:437](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/campaign/s8b_floor_campaign.py:437)

**放置時の成果物影響:** `floor_protocol.json` の受理集合に「人間操作なし・active receipt なし」が入り、同じ SHA のためレポート／台帳は人間凍結と AI 凍結を識別できない。

### 4. journal/header/payload/envelope が最終 prediction に束縛されていない

header は実走中の `JournalBinding` との一致しか検査せず、prediction schema に journal hash/path/header digest は残らない。[runner:317](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/campaign/s8b_prediction_runner.py:317) [selector:73](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/campaign/s8b_selector_freeze.py:73)

`verify_prediction_freeze()` は journal・claim payload・envelope を一切読まない。[selector:598](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/campaign/s8b_selector_freeze.py:598) `payload_path` は書いた直後の比較以降使われず、envelope は journal に path/hash すら記録されない。journal 自体を削除しても prediction の検証は通り、preflight も「存在するファイルだけ」を自己 hash するため削除を拒否しない。

また `resolve_journal()` は未知 target の追加 claim/invocation を受理し、`build_rows_from_journal()` は既知6 job だけを射影して余分な試行を捨てる。[runner:386](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/campaign/s8b_prediction_runner.py:386) [runner:642](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/campaign/s8b_prediction_runner.py:642)

**放置時の成果物影響:** 同じ `prediction_body_sha256` のまま journal を削除・再生成したり、第7試行や別 payload/envelope を台帳へ混入でき、レポートの選択値と試行台帳の回数・参照先が乖離する。

### 5. role/freeze 以外の source は read-once でなく、未実行コードの hash を記録できる

clean 検査は開始時の一度だけで、builder/input/output schema は全 invocation 後に live filesystem から読む。[runner:936](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/campaign/s8b_prediction_runner.py:936) [runner:1035](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/campaign/s8b_prediction_runner.py:1035) Python 実体は既に import 済みなので、実走後にファイルを差し替えると「実行した A、sources が指す B」が成立する。

parser SHA は header にだけ入り、prediction へ伝播しない。後日の verifier も source が `pre_oracle_head` の blob と一致するかは見ず、現在の path/hash を自己一致検査するだけである。[selector:630](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/campaign/s8b_selector_freeze.py:630)

**放置時の成果物影響:** `sources.builder/input_schema/output_schema.sha256` と parser proof 参照が、実際に payload 構築・応答解釈へ使った bytes とは別の値へ変わる。

### 6. envelope/provenance の意味検証が不足している

具体的に次が受理される。

- `num_turns: 1.0`。bool だけ排除し `!= 1` で比較しているため float が通る。[runner:875](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/campaign/s8b_prediction_runner.py:875)
- `modelUsage: {"claude-opus-forged": null}`。key prefix と件数しか見ず、usage record の型・token 実績を見ない。[runner:886](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/campaign/s8b_prediction_runner.py:886)
- 4セルすべて同じ `session_id`。行横断の一意性検査なしで `fresh_context=True` を固定記録する。[runner:904](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/campaign/s8b_prediction_runner.py:904)
- neutral cwd の空検査は provider 構築時の一度だけで、4 invocation 間には再検査しない。[runner:808](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/campaign/s8b_prediction_runner.py:808)

**放置時の成果物影響:** 実在しない model slug、再利用された child session、非 fresh context の結果が正規 provenance として受理され、その `choice_id` が certified 判定へ入る。

## SHOULD-FIX

### 7. official preflight の selector allowlist は恒真で、certificate は内容を束縛しない

prediction/runs は期待 hash ではなく、検査直前に読んだ現在値をそのまま allowlist にする。[floor:1271](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/campaign/s8b_floor_campaign.py:1271) 不在ファイルも黙って省略する。さらに `clean_scan_digest` はファイル名集合だけで、allowlist の path→hash を certificate に含めない。[floor:1352](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/campaign/s8b_floor_campaign.py:1352)

現時点では public official が無条件拒否のため、G2 に従い **初回 E2E の1 cycle後送り**とする。ただし official 解禁前には MUST-FIX へ昇格が必要。

**放置時の成果物影響:** official 解禁後、異なる／欠落した prediction・journal・payload・envelope が同じ `clean_scan_digest` と launch certificate で受理され、レポートの proof 参照が内容改変を表現しない。

## NIT

なし。

## Refuted

- **48e3e0f / `seal()` 親ハンク1:** read-once した `freeze_bytes` 自体を `V1_FREEZE_SHA256` と照合し、その同じ bytes を parse しているため、ゲートは恒真ではない。[runner:1000](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/campaign/s8b_prediction_runner.py:1000) 負例の過剰決定も明記どおりで、現コードの TOCTOU gate 自体は有効。
- **e0fedd8 親ハンク2:** non-TTY + active receipt のテストは M2 の False 分岐を正しく単独拘束し、tampered-freeze fixture の executable 化も両層変異時に封印経路へ到達させている。ただし MUST-FIX 3 の PTY／直呼び経路は拘束しない。
- **`ClaudeHeadlessProvider` role read-once:** seal 側 bytes と inline-agent 構築側 SHA を比較しており、role→inline の差替え穴は refuted。[runner:1015](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/campaign/s8b_prediction_runner.py:1015)
- **前 wave 不変条件:** 凍結3 JSON と `test_frozen_artifacts.py` は base/HEAD の blob ID が同一。public official 拒否、`PRODUCTION_PROVIDER=unwired_provider`、strict parser の実応答・再検証経路も維持されている。既存テストの意味変更は R3 missing 誤固定の是正1点で、それ以外の削除は run-header/binding 引数への追随だった。


---

## §7 敵対レビュー 2 — 裁定整合・完全性 (逐語)

判定は **NO-GO**。`fcf0533..HEAD` の `orchestrator/` 全 2,977 diff 行を確認した。所見は BLOCKER 4、SHOULD-FIX 1。pytest は制約どおり未実行。

## BLOCKER

1. **`neutral cwd` は実際には repo 内で、payload-only 隔離が成立しない**

production の `artifact_root` は repo 配下の `output/s8b-freeze/selector-runs` であり、`neutral-cwd` もその子に作られる。[provider](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/campaign/s8b_prediction_runner.py:778) [seal](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/campaign/s8b_prediction_runner.py:1014)  
さらに argv は `--setting-sources ""` だけで `--bare` / `--safe-mode` がない。[argv](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/campaign/s8b_prediction_runner.py:821) ローカル実体 `claude 2.1.217 --help` は、通常モードが CLAUDE.md auto-discovery、auto-memory、cwd/env/git-status の dynamic context を持ち、これらを止めるのは `--bare` と明記する。これは「入力 JSON だけ」を要求する role と衝突する。[role](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/.claude/agents/selector-8b.md:19) テストは fake runner に空 directory を渡した事実しか検査していない。[test](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/tests/test_s8b_prediction_runner.py:491)

**成果物影響:** CLAUDE.md・memory・セルごとに変化する git status が同じ payload の選択を変え、`choice_id`、swapped 追従、最終 certified 判定が payload-only 実験とは別値になる。

2. **R3 missing は生成できても、production `seal` からは crash 後に到達不能**

claim 後の timeout・nonzero・起動失敗は例外で `drive_journal` 全体を抜けるため、その走行では残セルも materialize も行われない。[claim/call](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/campaign/s8b_prediction_runner.py:598) [provider failure](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/campaign/s8b_prediction_runner.py:849)  
再度 `seal` すると、残った journal/payload は非 ignore の untracked file なので先頭の clean-worktree gate が拒否する。[clean gate](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/campaign/s8b_prediction_runner.py:975) 現テストは `seal` を通さず `drive_journal` を直接二回呼ぶため、この拒否を迂回している。[crash test](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/tests/test_s8b_prediction_runner.py:210)  
加えて payload は claim より先に create-only で作られるため、その間の crash は「未 claim + 再作成不能」という別の停止状態を作る。

**成果物影響:** 本来は「1 セル `choice_id=null` を含む6行 prediction → §6 indeterminate」となる障害が、`selector_predictions.json` 不在・残りの独立試行欠落・レポート不能へ変わる。

3. **floor preflight は sealed prediction を必須にも検証済みにもしていない**

`selector_predictions.json` は `add_if_file` なので不存在を許容し、存在しても現在 bytes の自己 hash を採るだけで verifier を通さない。`selector-runs/` も全ファイルを `rglob` して自己 allowlist 化する。[allowlist](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/campaign/s8b_floor_campaign.py:1259)  
新テスト自身が `b"selector-predictions"` という不正 JSON を正例としているうえ、不存在を「optional」と固定している。[test](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/tests/test_s8b_floor_campaign.py:2328) これは裁定済み順序 `protocol → prediction → floor` と衝突する。[handoff](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/docs/handoff/2026-07-22-protocol-freeze-prediction-seal.md:104)

**成果物影響:** prediction 不在・任意 bytes・手組み runs の状態で floor 実測が受理され、floor 閲覧後に選択を作れるため certified `choice_id` と proof-chain の受理集合が変わる。

4. **拡張 allowlist が downstream `launch_validate` に伝播せず、strict-valid raw が oracle を止める**

`launch_validate` の exact exemption は active-chain 4 path だけで、selector prediction/runs を含まない。[exemption](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/campaign/s8b_ratified_freeze.py:2415) その状態で repo 全体を走査し、closure 外 hit を拒否する。[scan](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/campaign/s8b_ratified_freeze.py:2795)  
例えば rationale が `ycsb_rratio=20 ycsb_zipf_skew=0.9 ycsb_rmw=0` の応答は strict parser 上 valid だが、raw artifact は rr20 conjunction hit になる。oracle driver は `launch_validate` 失敗を marker/WAL 作成前の refusal にする。[oracle consumer](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/campaign/s8b_oracle_driver.py:1059)

**成果物影響:** 正当に `status=valid` で凍結された selector 応答の内容次第で oracle 全試行が欠落し、oracle 台帳・結合レポート・certified 判定が生成されない。

## SHOULD-FIX

5. **変異の「12/12 すべて受理集合帰属」は成立しない（G2 に従い初回 E2E の1 cycle後送り）**

- M1 は `pytest.raises(..., match="未解禁")` に対し、mutant が後段で `"未配線"` を投げるため、claim 0 件 assertionへ到達する前に診断文字列差で赤になる。[test](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/tests/test_s8b_prediction_runner.py:286)
- M6 は事前登録上 `pre_oracle_head` 一項の除去だが、実 harness は header 全6 binding の loop を空にしている。[harness](/home/SFC/tanab/.claude/jobs/9b2bec65/tmp/wave-protocol-seal/mutation_harness.py:48)
- M13 は登録上 protocol/predictions/runs の除去だが、実置換は protocol/predictions だけで、runs 列挙は残る。[harness](/home/SFC/tanab/.claude/jobs/9b2bec65/tmp/wave-protocol-seal/mutation_harness.py:75)

**成果物影響:** `KILLED=12` という raw 集計は残るが、台帳の M1/M6/M13 の検出対象・単一理由・保証参照が実測と異なり、「12件すべて受理集合に帰属」という監査値は撤回が必要になる。

## 明示的に refuted

- missing 行の `agent_provenance=null`、swapped期待値の null、`s8b_verdict` の三値伝播自体は整合している。[freeze](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/campaign/s8b_selector_freeze.py:482) [verdict](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/campaign/s8b_verdict.py:356)
- 親ハンク1の read-once freeze と v1 trust root 照合コードは正しい。単独テストが先行層に遮られる点も明記され、M8 は両層変異として成立している。
- 親ハンク2の M2 fixture は active receipt と非TTY以外を成立させており、診断だけでなく凍結の受理可否を反転させる。M2 の帰属変更は妥当。
- 手順 (ii) の CLI、`PYTHONPATH`、receipt 前提、774 bytes、SHA-256 値は実装と一致する。


---

## §8 段 6 裁定と fix

レビュー 1 = REJECT (BLOCKER 2 / MUST 4 / SHOULD 1)、レビュー 2 = NO-GO (BLOCKER 4 /
SHOULD 1)。裁定と fix の対応 (正本 = handoff「段 6 レビュー裁定」節):

- FIX-1 (R2-1): claude が触る面 (cwd / mcp config) を repo 外 tempfile へ。--bare は不採用
  (claude --help 上 --agents/--settings ごと skip の可能性があり inline agents が無効化される
  リスク — G1 実測済み構成を維持)
- FIX-2 (R2-2/R1-1): seal clean gate を「selector-runs 配下の untracked のみ許容」へ +
  payload 再開 idempotent (同一 bytes 受理・不一致拒否)。claim-crash 後の R3 missing 封印が
  production 経路で到達可能に
- FIX-3 (R1-4): JournalBinding.known_cells で 6 セル外 record を protocol violation 化
- FIX-4 (R1-5): sources 5 本を seal 冒頭で read-once (実行後差し替えの「実行 A・記録 B」封鎖)
- FIX-5 (R1-6): num_turns 厳密 int / modelUsage record 型 + token 実績 / session_id セル間
  重複拒否 / cwd 毎回検査
- FIX-6 (R1-2): run_header に claude executable 絶対 path + bytes sha256 を記録 (pin でなく
  監査記録。同一 journal の再開は同一実行体を要求する意味論)
- FIX-7 (R2-3): official preflight で prediction 実在 + v1 freeze への verify_prediction_freeze
  通過 + journal 実在を必須化 (protocol → prediction → floor の裁定順序の機構強制)。恒真
  fixture (b"selector-predictions") を実 API 文書へ是正
- R1-3 (isatty は認証でない): 性格付けを「誤操作防壁 + 明示迂回を要する障壁」へ修正して記録。
  実効の正本 = 規律 + guard_write hook + AI provenance 監査。コード変更なし
- R2-5 (変異帰属): M1 = テストをメッセージ非依存 2 段検査へ (d7ed08f)、M6 = 台帳 erratum
  (§10)、M13 = ハーネス置換拡大 + 再実測

**fix の波及と親ハンク 4 (f6f2d32):** FIX-7 の必須化が下流 72 テスト (ratified_freeze 3 /
ratified_verify 58 / oracle_driver 11 — いずれも official `_run_campaign_core` を prediction
なし fixture で回す共有 builder 経由) を赤にした。実装子の限定実走 (対象 4 ファイル) では
捕捉されず親の全走が検出 — 「実装子の実走は親の全走を代替しない」の再実例。是正 = 共有
builder `_prepare_emitter_base` を seed → prediction 注入 → base の 2 段 commit 化し、
all-missing 6 行文書 (実 API 組立て) + journal を base commit に含める。**この過程で判明した
運用制約: `_assert_namespace_clean` (s8b_ratified_freeze.py:342) は output/s8b-freeze 配下の
untracked を dirty 拒否する — production でも seal 直後・commit 前の状態では ratified 系
検査 (resolve_active_generation 等) が拒否する。予測封印の手順は「seal → 即 AI commit」を
一体で行うこと** (手順パッケージに反映)。

scope 外 (backlog、正本 = worklog (11) 次の一手):
- launch_validate の exact exemption に selector 系が無い + 正当な rationale/payload の三軸語
  hit で oracle が止まりうる (R2-4) — oracle 結線 wave の blocking 前提 (証拠 artifact の
  置き場所再設計を含む)
- preflight allowlist の certificate 束縛 (R1-7) — official 解禁前に MUST 昇格
- verifier の pre_oracle_head blob 照合・prediction への journal 束縛 (R1-4/5 の残余) —
  FROZEN_MANIFEST 逐次 pin + oracle 側 execution_guard 検証で代替、oracle 結線 wave で再評価

---


---

## §9 焦点再レビュー (逐語) と fix2

結論は **NO-GO**。6 件は closed、4 件は partial。新規に BLOCKER 1 件、MUST-FIX 2 件を認める。提示された全走・変異結果は否定しないが、下記経路はその検査集合に含まれていない。

| 元所見 | 判定 | 1 行根拠 |
|---|---|---|
| R2-1 | closed | neutral root を repo 外 `mkdtemp` に限定し、invocation ごとに空の cwd を新設している。([s8b_prediction_runner.py:848](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/campaign/s8b_prediction_runner.py:848)) |
| R2-2 | closed | clean gate は tracked 変更と selector-runs 外 untracked を拒否し、同配下だけを再開用に許容する。([s8b_prediction_runner.py:1026](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/campaign/s8b_prediction_runner.py:1026)) |
| R1-1 | closed | 既存 payload は通常 file・同一 bytes の場合だけ受理され、claim 済みセルは missing のまま再呼出しされない。([s8b_prediction_runner.py:540](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/campaign/s8b_prediction_runner.py:540)) |
| R2-3 | partial | prediction 必須・verify・journal 実在は入ったが、verify した bytes と allowlist に束縛する bytes が同一でない。([s8b_floor_campaign.py:1281](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/campaign/s8b_floor_campaign.py:1281), [同:1321](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/campaign/s8b_floor_campaign.py:1321)) |
| R1-2 | closed | 解決済み executable の path と bytes SHA-256 が run header に記録・再開照合される。([s8b_prediction_runner.py:826](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/campaign/s8b_prediction_runner.py:826), [同:1124](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/campaign/s8b_prediction_runner.py:1124)) |
| R1-4 | closed | 全 journal record を `binding.known_cells` と照合し、6 セル外を protocol violation にする。([s8b_prediction_runner.py:440](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/campaign/s8b_prediction_runner.py:440)) |
| R1-5 | closed | 5 source は provider 構築・実行前に一括 read-once され、その捕捉 bytes だけから sources record を作る。([s8b_prediction_runner.py:1079](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/campaign/s8b_prediction_runner.py:1079)) |
| R1-6 | partial | 型・token・同一 provider 内 session 重複は閉じたが、resume で provider を再生成すると session 集合が空へ戻る。([s8b_prediction_runner.py:866](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/campaign/s8b_prediction_runner.py:866), [同:1110](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/campaign/s8b_prediction_runner.py:1110)) |
| R2-5 | partial | M1 は message 非依存の拒否＋claim 0 検査になり、M13 再実測も受領したが、M6 erratum は未 commit で台帳は依然「単一 field 除去」と記す。([test_s8b_prediction_runner.py:301](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/tests/test_s8b_prediction_runner.py:301), [handoff:222](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/docs/handoff/2026-07-22-protocol-freeze-prediction-seal.md:222)) |
| R1-3 | partial | HEAD の docstring はなお `isatty` を「人間の対話 shell 専用」と性格付けしており、非認証の誤操作防壁という記録は未 commit。([s8b_floor_campaign.py:498](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/campaign/s8b_floor_campaign.py:498)) |

## 新規所見

1. **BLOCKER — verify 済み prediction と launch 対象 bytes が切れている。**  
   `prediction_bytes` を verify した後、`add_if_file()` が path を再読してその時点の SHA を allowlist に採る。間で A→B に差し替えると、未検証 B が exact allowlist を通る。([s8b_floor_campaign.py:1293](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/campaign/s8b_floor_campaign.py:1293), [同:1312](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/campaign/s8b_floor_campaign.py:1312))  
   **影響:** 未検証・破損 prediction のまま official launch certificate を発行して floor を開始でき、初回 E2E の裁定順序保証を無効化する。

2. **MUST-FIX — crash resume を跨ぐ session ID 重複を受理する。**  
   重複集合は provider instance 内だけで、既存 journal の invocation receipts から復元されない。([s8b_prediction_runner.py:971](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/campaign/s8b_prediction_runner.py:971), [同:603](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/campaign/s8b_prediction_runner.py:603))  
   **影響:** 再開前後の二セルが同じ context を共有しても `fresh_context: true` の prediction として封印され、セル独立性が虚偽になる。

3. **MUST-FIX — f6f2d32 の「封印一式」は production runner から導出不能。**  
   seed は prediction 注入前に切られる一方、実際の floor protocol は base 作成後に構成されるため、seed tree に `floor_protocol.json` がない。しかし production `seal()` は `pre_oracle_head` の同 blob を必須とする。また fixture journal は `{}` 一行で、all-missing を導く run header・4 claim・2 static を持たない。([test_s8b_ratified_freeze.py:443](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/tests/test_s8b_ratified_freeze.py:443), [同:544](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/tests/test_s8b_ratified_freeze.py:544), [同:514](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/tests/test_s8b_ratified_freeze.py:514), [s8b_prediction_runner.py:1087](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/campaign/s8b_prediction_runner.py:1087))  
   **影響:** 下流 72 テストが緑でも、実際の protocol→seal→commit→floor topology が成立する証拠にならず、統合破断を偽緑化する。

all-missing 文書そのものは正当である。`missing` は schema が明示受理し、各 agent cell が claim-crash した journal から生成可能である。([s8b_selector_freeze.py:482](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/campaign/s8b_selector_freeze.py:482), [s8b_prediction_runner.py:716](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/campaign/s8b_prediction_runner.py:716)) 問題は f6f2d32 の `{}` journal と protocol を含まない seed が、その文書の由来を表していない点にある。seed commit を一段増やしたこと自体は G/C/A の topology・履歴導出を壊していない。

G2 適用上、R2-5 の台帳 erratum と R1-3 の性格付け記録は初回 E2E を止めず、SHOULD として 1 cycle 後送り可能。上記 BLOCKER/MUST-FIX はそれぞれ preflight 本体、明示された crash-resume、不正な受入 fixture に直結するため後送り対象ではない。

**親裁定 (fix2、FIX2-1..4 全採用):** N1 = verify した bytes の sha を直接 allowlist へ (BLOCKER)。
N2 = journal receipt から session 観測集合を復元。N3 = fixture journal を実 API 生成へ +
production seal 由来でない旨の明記 (完全同型 E2E は実 protocol JSON が存在しない現状では
構造的に作れない — oracle 結線 wave の blocking 前提へ)。R1-3 partial = isatty docstring の
性格付け追記。R2-5 partial (M6 erratum) = 本書 §10 で close。fix2 = commit d4b6271
(410 passed / 2 skipped で受入)。


---

## §10 変異台帳 (B-057)

### 事前登録 (実装後・実測前に凍結、handoff から)

| ID | 変異位置 (単一置換) | kill 期待テスト | 単一理由確認 |
|---|---|---|---|
| M1 | runner drive_journal の sentinel pre-claim raise 除去 | test_production_provider_refuses_before_claiming | 手前に provider identity 検査なし。理由 = claim 汚染 |
| M2 | freeze_protocol の isatty 検査除去 | test_freeze_protocol_non_tty_is_refused_even_with_active_receipt | 他前提全成立 fixture — destination 出現で赤 |
| M3 | freeze_protocol の receipt 状態検査除去 | test_freeze_protocol_rejects_inactive_t080_receipt | 手前 = isatty (seam True で通過) |
| M4 | freeze_protocol の builder master_seed を別 literal へ | test_freeze_protocol_success_writes_only_fixed_tmp_repo_path | canonical sha 不一致の 1 理由 |
| M5 | seal の protocol blob 照合 raise 除去 | test_seal_rejects_protocol_blob_not_equal_to_rederived_bytes | 手前は protocol 内容を見ない |
| M6 | runner _validate_header の束縛照合ループ除去 | test_run_header_mismatch_is_rejected (全 param) | parametrize 単一 field fixture 群 |
| M7 | runner envelope の is_error 判定除去 | test_claude_headless_rejects_invalid_envelope[is_error] | parametrize 単一 override fixture |
| M8 | 両層同時: builder v1 bytes 照合 + seal V1 照合の同時除去 | test_seal_rejects_tampered_freeze_before_any_claim | 単層は他層が落とす過剰決定 (docstring 明記)。実行可能 fake executable で封印進行を検出 |
| M9 | freeze_protocol の post-write problems 検査除去 | test_freeze_protocol_detects_post_write_readback_tamper_without_deleting | after_write seam の改変検出 |
| M11 | runner _acquire_drive_lock の flock 除去 | test_drive_journal_rejects_second_concurrent_driver | lock 保持中に 2 本目を呼ぶ決定論形 |
| M12 | selector_freeze の missing provenance null 検査除去 | test_missing_agent_row_rejects_provenance_in_build_and_verify | 手前に missing provenance 検査なし |
| M13 | floor の allowlist 拡張 (protocol/predictions/runs) 除去 | test_floor_preflight_allowlist_hashes_verified_prediction_and_selector_run_files | 理由 1 つ |

**M10 (seal 内部 reload verify 除去) は登録見送り**: 成功経路テストが外部
verify_prediction_freeze を独立に呼び、正しく書かれた文書では内部 verify 除去が観測不能
(等価変異)。冗長ゲートと明記。改変検出 seam の追加は 1 cycle 後の判断。

### 1 巡目 (fix 前コード、12/12 KILLED) と erratum

1 巡目は 12/12 KILLED・survived 0・injection failed 0。ただし焦点はレビュー R2-5 が指摘した
帰属 3 件:

- **M1 (erratum)**: kill は成立していたが、赤の第一理由は pytest.raises(match="未解禁") の
  診断文字列差 (mutant は「未配線」を claim 後に投げる) — claim 0 件 assert に到達しない。
  受理集合帰属が不成立のため、テストを「拒否の有無 (メッセージ非固定)」と「claim ゼロ」の
  独立 2 段検査へ修正 (d7ed08f) して 2 巡目で kill 再確認
- **M6 (erratum)**: 事前登録の文言「pre_oracle_head 照合除去」に対し実置換は束縛照合ループ
  全体の除去 (単一 field の照合行はループ共通実装のため構造上存在しない)。登録文言を
  「束縛照合ループ除去 (期待 = 全 param 赤)」へ訂正。kill 自体は成立
- **M13 (erratum)**: 1 巡目の置換は protocol/predictions の 2 行のみで runs 列挙が残存 —
  登録文言との乖離。置換を runs 列挙ブロックまで拡大して 2 巡目で再実測

### 最終 (fix 後コード、全 12 件再実測): **12/12 KILLED・survived 0・injection failed 0**

- M1 = 修正後テストで kill (受理集合帰属成立)。M6 = 8 param 全赤 (executable 2 field 追加後)。
  M13 = 改名後テスト単独 kill・unexpected 0
- unexpected fail は 2 件のみで変異内容から説明可能: M2 → CLI pipe テスト (診断依存の補助)、
  M8 → builder v1 不一致負例 (両層変異の当然の副次)
- 結果 JSON = 本 wave tmp の mutation-results.json (以下に転記)

### 最終結果 JSON (転記)



### fix2 後の最終再走 (確定)

FIX2-1 で allowlist 実装が変わり M13 の置換が期待どおり INJECTION_FAILED → 置換を fix2 実装へ
追随させて全 12 件を最終再走: **12/12 KILLED・survived 0・injection failed 0** (unexpected は
M2/M8 の既知 2 件のみ)。最終結果 JSON は下記転記のとおり (mutation-results.json)。


```json
{
  "results": [
    {
      "id": "M1",
      "status": "KILLED",
      "rc": 1,
      "expected_hits": [
        "orchestrator/tests/test_s8b_prediction_runner.py::test_production_provider_refuses_before_claiming"
      ],
      "unexpected_fails": [],
      "mutated_files": [
        "s8b_prediction_runner.py"
      ]
    },
    {
      "id": "M2",
      "status": "KILLED",
      "rc": 1,
      "expected_hits": [
        "orchestrator/tests/test_s8b_protocol_builder.py::test_freeze_protocol_non_tty_is_refused_even_with_active_receipt"
      ],
      "unexpected_fails": [
        "orchestrator/tests/test_s8b_protocol_builder.py::test_freeze_protocol_cli_rejects_pipe_stdin"
      ],
      "mutated_files": [
        "s8b_floor_campaign.py"
      ]
    },
    {
      "id": "M3",
      "status": "KILLED",
      "rc": 1,
      "expected_hits": [
        "orchestrator/tests/test_s8b_protocol_builder.py::test_freeze_protocol_rejects_inactive_t080_receipt"
      ],
      "unexpected_fails": [],
      "mutated_files": [
        "s8b_floor_campaign.py"
      ]
    },
    {
      "id": "M4",
      "status": "KILLED",
      "rc": 1,
      "expected_hits": [
        "orchestrator/tests/test_s8b_protocol_builder.py::test_freeze_protocol_success_writes_only_fixed_tmp_repo_path"
      ],
      "unexpected_fails": [],
      "mutated_files": [
        "s8b_floor_campaign.py"
      ]
    },
    {
      "id": "M5",
      "status": "KILLED",
      "rc": 1,
      "expected_hits": [
        "orchestrator/tests/test_s8b_prediction_runner.py::test_seal_rejects_protocol_blob_not_equal_to_rederived_bytes"
      ],
      "unexpected_fails": [],
      "mutated_files": [
        "s8b_prediction_runner.py"
      ]
    },
    {
      "id": "M6",
      "status": "KILLED",
      "rc": 1,
      "expected_hits": [
        "orchestrator/tests/test_s8b_prediction_runner.py::test_run_header_mismatch_is_rejected[claude_executable_path-/fixture/other-claude]",
        "orchestrator/tests/test_s8b_prediction_runner.py::test_run_header_mismatch_is_rejected[claude_executable_sha256-8888888888888888888888888888888888888888888888888888888888888888]",
        "orchestrator/tests/test_s8b_prediction_runner.py::test_run_header_mismatch_is_rejected[freeze_sha256-4444444444444444444444444444444444444444444444444444444444444444]",
        "orchestrator/tests/test_s8b_prediction_runner.py::test_run_header_mismatch_is_rejected[parser_module_sha256-6666666666666666666666666666666666666666666666666666666666666666]",
        "orchestrator/tests/test_s8b_prediction_runner.py::test_run_header_mismatch_is_rejected[pre_oracle_head-3333333333333333333333333333333333333333]",
        "orchestrator/tests/test_s8b_prediction_runner.py::test_run_header_mismatch_is_rejected[protocol_sha256-3333333333333333333333333333333333333333333333333333333333333333]",
        "orchestrator/tests/test_s8b_prediction_runner.py::test_run_header_mismatch_is_rejected[provider_kind-other-provider]",
        "orchestrator/tests/test_s8b_prediction_runner.py::test_run_header_mismatch_is_rejected[role_file_sha256-5555555555555555555555555555555555555555555555555555555555555555]"
      ],
      "unexpected_fails": [],
      "mutated_files": [
        "s8b_prediction_runner.py"
      ]
    },
    {
      "id": "M7",
      "status": "KILLED",
      "rc": 1,
      "expected_hits": [
        "orchestrator/tests/test_s8b_prediction_runner.py::test_claude_headless_rejects_invalid_envelope[overrides0-is_error]"
      ],
      "unexpected_fails": [],
      "mutated_files": [
        "s8b_prediction_runner.py"
      ]
    },
    {
      "id": "M8",
      "status": "KILLED",
      "rc": 1,
      "expected_hits": [
        "orchestrator/tests/test_s8b_prediction_runner.py::test_seal_rejects_tampered_freeze_before_any_claim"
      ],
      "unexpected_fails": [
        "orchestrator/tests/test_s8b_protocol_builder.py::test_builder_rejects_v1_bytes_mismatch"
      ],
      "mutated_files": [
        "s8b_floor_campaign.py",
        "s8b_prediction_runner.py"
      ]
    },
    {
      "id": "M9",
      "status": "KILLED",
      "rc": 1,
      "expected_hits": [
        "orchestrator/tests/test_s8b_protocol_builder.py::test_freeze_protocol_detects_post_write_readback_tamper_without_deleting"
      ],
      "unexpected_fails": [],
      "mutated_files": [
        "s8b_floor_campaign.py"
      ]
    },
    {
      "id": "M11",
      "status": "KILLED",
      "rc": 1,
      "expected_hits": [
        "orchestrator/tests/test_s8b_prediction_runner.py::test_drive_journal_rejects_second_concurrent_driver"
      ],
      "unexpected_fails": [],
      "mutated_files": [
        "s8b_prediction_runner.py"
      ]
    },
    {
      "id": "M12",
      "status": "KILLED",
      "rc": 1,
      "expected_hits": [
        "orchestrator/tests/test_s8b_selector_freeze.py::test_missing_agent_row_rejects_provenance_in_build_and_verify"
      ],
      "unexpected_fails": [],
      "mutated_files": [
        "s8b_selector_freeze.py"
      ]
    },
    {
      "id": "M13",
      "status": "KILLED",
      "rc": 1,
      "expected_hits": [
        "orchestrator/tests/test_s8b_floor_campaign.py::test_floor_preflight_allowlist_hashes_verified_prediction_and_selector_run_files"
      ],
      "unexpected_fails": [],
      "mutated_files": [
        "s8b_floor_campaign.py"
      ]
    }
  ],
  "summary": {
    "killed": [
      "M1",
      "M2",
      "M3",
      "M4",
      "M5",
      "M6",
      "M7",
      "M8",
      "M9",
      "M11",
      "M12",
      "M13"
    ],
    "survived": [],
    "injection_failed": []
  }
}
```


---

## §11 親の実測記録

- **G1 生死確認**: `claude -p --agent selector-8b "<合成payload>"` → rc=0、strict 出力
  (8b-selector-output/v1、fence なし、c06)。合成 payload = read 50%/skew 0.5/records 12345
  (実在 holdout rr20/rr80 と非同値 — 本番 payload 不使用で cherry-pick 汚染なし)
- **envelope 実測** (`--output-format json --no-session-persistence`): top-level 20 keys =
  api_error_status / duration_api_ms / duration_ms / fast_mode_state / is_error / modelUsage /
  num_turns / permission_denials / result / session_id / stop_reason / subtype /
  terminal_reason / time_to_request_ms / total_cost_usd / ttft_ms / ttft_stream_ms / type /
  usage / uuid。type=result / subtype=success / is_error=False / num_turns=1 /
  permission_denials=[] / result=inner JSON 文字列。modelUsage keys =
  [claude-haiku-4-5-20251001, claude-opus-4-8] — **haiku 補助が混ざるため「1 model のみ」検査は
  false red、主 slug 検査 + record 型検査を採用** (FIX-5)
- **G1 拡張実測 (production 構成)**: inline agents (--agents JSON、role bytes から構成) +
  --agent selector-8b-inline + neutral cwd (repo 外) + --setting-sources "" +
  --disable-slash-commands + --strict-mcp-config + --mcp-config <空file> +
  --no-session-persistence + --input-format text (stdin) → rc=0・strict 出力・
  usage.server_tool_use 全 0。**罠: --mcp-config は可変長引数 — 直後に positional を置くと
  巻き込んで「mcpServers: expected record, received undefined」で落ちる** (ファイル渡し +
  後続オプション挟みで回避)
- **isatty 防壁の live 発火**: 非 tty (AI Bash、< /dev/null) から
  `python3 -m campaign.s8b_floor_campaign freeze-protocol --confirm-user-freeze` → rc=1
  「実凍結は人間の対話 shell から実行する (stdin が tty でないため拒否)」、
  output/s8b-freeze への書き込みゼロを確認
- **受入全走 (最終)**: 2763 passed / 18 skipped / 0 failed (tools/run_tests.py)。
  collected-node 三点比較 = base (fcf0533) 2715 → head 2781 (+66)、**消失 0**。
  check_docs / check_codex_agents / check_ai_provenance (287 commits) 全緑
- **task-run 台帳**: start は「pilot は final report により凍結済み」で拒否 (fail-closed
  仕様どおり、上限は触らず台帳なしで進行)
