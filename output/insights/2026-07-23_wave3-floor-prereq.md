# wave3: floor 実測 blocking 前提 2 件のコード機構 — 逐語・変異台帳の凍結 (2026-07-23)

D79 (7) の blocking 前提 4 件のうち protocol JSON 非依存の 2 件 — (a) launch_validate の selector
証拠 exact exemption (§5-(ix)-9 追認方向)、(b) preflight allowlist の certificate 束縛 (official
解禁前 MUST) — の**コード機構**を実装した wave の一次資料。設計判断の正本 = D80、進行記録 =
worklog 2026-07-23 (2)。**blocking 前提の全消化ではない** — 実 pin・完全同型 E2E・lineage 照合は
oracle 結線 wave の残余 (F-07 の報告言語規律)。

- commit 系列: caf267c (基準) → 5d2be97 (親ハンク: wave2 台帳 defang) → 8835fa7 (単位 A) →
  6c89323 (単位 B) → af8ff49 (fix1 FIXW-1..7) → 437334a (fix2 N-01/N-02)
- 受入 (親環境): fix2 後の全走・三点比較・check 3 種は worklog 2026-07-23 (2) が正本
- 逐語の出自: 本文書の各節は codex (gpt-5.6-sol) の成果物ファイルからの機械的連結であり、
  三軸語 conjunction の混入検査 (defang 要否) を凍結前に実施済み (全ファイル無検出)

## G1 生死確認 (brief 前の前提実測)

emitter fixture (`_build_launch_repo`) を土台に、(i) all-null 封印一式 = launch_validate 通過、
(ii) 三軸語 conjunction (rr80 値の 3 軸を «defang 表記» では書かない生値で) を含む raw 応答
ファイルを**初回 commit で導入** = `closure-hit-mismatch` 拒否 (未申告 hit として当該 path を
名指し)、(iii) 2 軸のみ (conjunction 不成立) = 通過、を実証した。driver は job tmp
(`wave3-floor-prereq/g1_driver.py`) にあり、生値を含むため repo へは凍結しない。

副次実測 (driver v1..v3 の失敗から): worktree 上書きのみ → `namespace-dirty`、既存 bytes の
変更 commit → `history-mutated` が **scan 手前の別防壁**で拒否する (freeze namespace は
append-only)。ゆえに免除設計が扱うべきは「初回 commit 時点から三軸語を含む正当な証拠」のみで、
事後改竄系は既存層が塞ぐ — 変異の単一理由性設計の根拠。

模擬と実差分: fixture 証拠は production seal 由来でない。activation_head は commit 後 HEAD へ
差替え (production の起動時再解決の模擬)。pin 済みファイルの編集は無し。

## 変異台帳 (B-057 事前登録 → 実測)

事前登録 = 裁定 v2 の M1〜M10 (本文書の裁定 v2 節) + fix2 時の M11/M12 追加登録。実測は
fix1 後 (af8ff49) に M1-M10、fix2 後 (437334a) に M1-M12 の全数再走。結果 JSON =
本文書末尾の実測ログ節。**最終: 12/12 KILLED・survived 0・injection failed 0・復元検査全緑**。

注記 (帰属の正確さのための台帳記録):

1. **M4 は helper-leaf kill** — 事前登録では「semantic 系 launch fixture」を予定したが、実装された
   受理境界テスト (`absent_prediction_is_noop`、最小 repo で helper の空 map 返却を直接 assert)
   での kill に変更した。launch 配線側の kill は M1 が担う (launch_validate は helper を直接消費
   するため、helper 境界 = launch 受理境界)
2. **M7 の kill 基準は R4 裁定で改定** — 「副作用ゼロ」ではなく「2 回目 digest 不一致の拒否 +
   certificate 不発行」。one-shot claim の先行永続は at-most-once 設計どおりで、テストも
   `persists_claim_but_issues_no_certificate` として明示する
3. **M9 は 1 巡目登録が不成立だった** (レビュー A R3) — 非 ancestor commit が空 tree だと
   ancestry 検査を消しても source 不在で拒否され続け「mutant 通過」にならない。FIXW-5 で
   「同一 tree を持つ非 ancestor commit」へ単一理由化してから実測した (erratum として記録)
4. **M2 の kill 向きを手動裏取り** — mutant (prefix 免除化) 下で未申告孤児 envelope が免除 map に
   入ることを assert が直接捕捉 (受理集合の拡大検出であり、mutant クラッシュではない)。M2 では
   positive テストも同時に赤くなるが、これは免除集合の exact-set 検査が余剰 entry を検出したもの
5. **M11/M12 は fix2 の新ゲートに対する追加登録** — 焦点再レビューが「fix1 が journal 射影を
   弱めすぎた」(N-01/N-02) を regressed として検出したため、復元したゲートに kill 証明を付けた

## wave2 台帳 defang erratum (親ハンク 5d2be97)

`output/insights/2026-07-22_wave2-protocol-seal.md` L642 の三軸語 conjunction 逐語引用が、実際に
repo scan invariant (+oracle driver 系、計 11 テスト) を main で赤にしていた (wave2 の受入全走は
docs commit **前**に実施され未検出 — failures F34)。**642 行のみ «» で defang し、原文逐語は
git 履歴 441babc に残る**。台帳全文の他行は不変。レビュー A が defang の regex 破壊・残存なし・
erratum 記載十分を名指し検査で確認済み。

---

以下、逐語 (機械的連結)。


# §1 brief (親、段 1)

# wave3 brief — floor 実測 wave の blocking 前提 2 件の消化

## scope

- (a) launch_validate の exact exemption 拡張: selector 証拠 (selector_predictions.json / selector-runs/journal.jsonl / payload_*.json / raw_*.txt) を「既知宣言 artifact の exact path + bytes hash 免除」として scan 免除する (§5-(ix)-9 追認方向の実装)
- (b) preflight allowlist の certificate 束縛: clean_scan_digest の計算へ freeze_allowlist の path→sha256 を折り込み、検証側に独立再計算・厳密比較を実装する (D79 (7)「official 解禁前 MUST」の昇格)
- scope 外: 統合 E2E (実 protocol JSON 不在で構造的不可、D79 (7) 明記)、検証側 lineage 照合 (D79 (7) が oracle 結線 wave へ明示先送り)、official gate (_assert_official_permitted) の解禁

## 確定済みユーザー裁定 (前提)

- §5-(ix)-9 追認 (2026-07-18, output/insights/2026-07-18_s8b-c22-consultations.md): prefix 全除外は先行測定の隠し場所 → 「既知宣言 artifact の exact path + bytes hash 免除」へ移行
- D79 (7) (decisions.md L3282-3295): 上記 2 件が oracle 結線/official 解禁の blocking 前提
- [T-083]/G2: 新規作業は実走 blocker 限定 — 両件とも受理集合を実際に変える (下記 G1 実測)

## G1 生死確認 (実測済み、driver = job tmp wave3-floor-prereq/g1_driver.py)

- emitter fixture ベース: all-null 封印一式は launch_validate 通過 / 三軸語 conjunction 入り raw 応答ファイルの初回 commit 導入は closure-hit-mismatch 拒否 / 2 軸のみは通過
- 模擬と実差分: fixture 証拠 (production seal 由来でない)・activation_head は commit 後 HEAD へ差替え (production の起動時再解決の模擬)。pin 済みファイルの編集は無し
- 副次実測: worktree dirty → namespace-dirty、既存 bytes 変更 commit → history-mutated が scan 手前で拒否 (append-only)。免除が扱うのは「初回 commit から三軸語を含む正当な証拠」のみ。事後改竄は既存の別層が塞ぐ (変異の単一理由性設計に使うこと)

## 不変条件

- 規律 2: 三軸語 conjunction hit の拒否は不変。免除は exact path + bytes 一致に限る。prefix/pattern 免除の再導入禁止。cert raw hit の無条件拒否 (L2576) は不変
- FROZEN_MANIFEST の holdout v1 pin・凍結 3 JSON (0 byte)・PRODUCTION_PROVIDER sentinel・official mode の production 無条件拒否は不変
- 受入 baseline 2764 passed / 18 skipped / 0 failed を退行させない
- pin 元列挙 (Explore 実測): production 定数 = s8b_prediction_runner (4)・s8b_selector_freeze (2)・s8b_floor_campaign (3 + allowlist 構築)・s8b_holdout_freeze EXCLUDED_PATHS・s8b_ratified_freeze (V1_FREEZE_PATH + 4 dir + _GEN_RE)・hooks/guard_write・tools/task_runs/ledger banned namespace・test_frozen_artifacts FROZEN_MANIFEST。テスト 16 ファイルが s8b-freeze 参照

## 親の provisional 裁定 (攻撃対象 — 一件ずつ否認/採用を返せ)

- (P1) 置き場所は現状維持で確定 (再設計の結論 = 移動しない)。根拠: launch_validate は exempt_exact 指定で prefix 除外を無効化し repo 全体を scan するため、repo 内に「scan されない場所」は存在せず移動は問題を解決しない。exact 免除実装後は置き場所が本質でなくなる。移動は production 約 10 箇所 + テスト 16 ファイルの churn に対し利得ゼロ
- (P2) 免除の宣言源 = H から解決した selector_predictions.json を verify_prediction_freeze で検証した上で、rows が宣言する raw_response_path/raw_sha256、決定的に導出される payload path、固定パスの journal を免除集合に加える。_active_chain_exempt_exact と同型の「H tree regular blob + H bytes == worktree bytes」検査を全対象に課す
- (P3) predictions/journal 自身の外部 bytes pin は FROZEN_MANIFEST 逐次 pin (seal wave の commit、D79 (7) 第 3 項の代替方針) に委ね、launch_validate 内は H 解決 + bytes 一致で束縛する
- (P4) cert 束縛 = clean_scan_digest 計算式へ path→sha256 を canonical 折り込み + validate_launch_certificate に expected_clean_scan_digest 追加 (厳密一致) + _revalidate_issued_certificate の独立再計算。EQUALITY_CHAIN_ADJACENCY への node 追加要否はプラン側で判断し最小に
- (P5) predictions が存在しない repo (seal 未実行) では免除は空集合で従来挙動不変 — 免除拡張は fail-closed に「証拠があれば検証して免除、無ければ何も免除しない」
- (P6) payload は構造上三軸語を含まない (キー名変換・数値化を実測) が免除集合には含める (bytes 束縛が既にあり安全)

## 成果物の形・並列分割

- production: s8b_ratified_freeze.py (免除拡張) / s8b_floor_campaign.py + s8b_launch_cert.py (cert 束縛)。テスト: 正負両側 (正当証拠の通過 / 宣言外・bytes 不一致・symlink・重複宣言の拒否、cert digest の改竄検出)
- 実装単位 2 分割 (exemption / cert 束縛)。共有 fixture (test_s8b_ratified_freeze.py の emitter builder) への変更が両単位に要るなら、先行単位完了 → 所有ファイル限定 patch 展開 → 残り投入の直列化とする
- docs (D80・worklog・insights 凍結) と統合 commit・変異 matrix・受入全走は親が実施


# §2 プラン v1 (codex、段 2)

# 実装プラン v1

結論は、P1/P3/P4/P5/P6 を採用、P2 は原案のままでは否認です。`verify_prediction_freeze()` をそのまま `launch_validate()` に入れると、seal 後に trusted source が更新されただけで過去 prediction が恒久拒否されるため、I/O を伴わない declaration 検証へ分離します。

## brief の静的検証結果

主要な行番号は現 HEAD と一致しました。

- `launch_validate` は [s8b_ratified_freeze.py:2464](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/campaign/s8b_ratified_freeze.py:2464)、active exemption は [同:2415](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/campaign/s8b_ratified_freeze.py:2415)。
- `search_repository(exempt_exact=...)` は [s8b_holdout_freeze.py:297](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/campaign/s8b_holdout_freeze.py:297)。hash 不一致は拒否ではなく通常 scan へ戻る実装です。
- `verify_prediction_freeze` は [s8b_selector_freeze.py:598](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/campaign/s8b_selector_freeze.py:598)。row 正規化全体は brief の L440 ではなく [同:423](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/campaign/s8b_selector_freeze.py:423) から始まります。
- clean digest/allowlist/certificate の行番号も [s8b_floor_campaign.py:1263](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/campaign/s8b_floor_campaign.py:1263)、[同:1404](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/campaign/s8b_floor_campaign.py:1404)、[同:1492](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/campaign/s8b_floor_campaign.py:1492) で一致します。

訂正・不足は次の4点です。

1. `s8b-freeze` を文字列参照するテストは17ファイルです。汎用の `test_task_run_ledger.py` を除けば16なので、brief の「16」はこの除外を暗黙に置いた数と解釈できます。
2. `verify_prediction_freeze()` は [s8b_selector_freeze.py:630](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/campaign/s8b_selector_freeze.py:630) で `sources` 5本を現在の worktree bytes と照合します。seal 後の正当な source 更新も拒否するため、P2 の丸ごと再利用は不適切です。
3. production runner は [s8b_prediction_runner.py:963](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/campaign/s8b_prediction_runner.py:963) で `envelope_*.json` も生成します。rationale に `key=value` 三軸語があれば envelope の `result` 文字列にも残るため、brief の4種だけでは production seal 一式を覆い切れません。
4. `FROZEN_MANIFEST` は現時点で8件のみで、predictions/journal pin はまだありません。[test_frozen_artifacts.py:33](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/tests/test_frozen_artifacts.py:33)

## 変更単位A: selector exact exemption

### 1. prediction の安定な declaration 検証を分離

[s8b_selector_freeze.py:598](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/campaign/s8b_selector_freeze.py:598)

- 現行 `verify_prediction_freeze()` のうち、top-level exact schema、`body_sha256`、selector basis、derangement、execution policy、row tagged union・セル一意性、swapped expectation の再導出を private helper へ抽出します。
- 想定シグネチャ:

```python
def _validate_prediction_document(
    document: Mapping, *, freeze: Mapping
) -> tuple[dict, list[dict]]:
```

- `verify_prediction_freeze()` はこの helper を呼んだ後、従来どおり commit 実在、現在 source bytes、現在 raw file の再parseを行います。既存 public verifier の受理集合は変えません。
- `launch_validate()` はこの declaration-only helper を使い、seal 後の live source drift を exemption 判定へ持ち込みません。
- selector module は ratified module を importしているため、ratified 側からの import は関数内遅延 import とし、循環 import を避けます。

### 2. selector 証拠から exact map を作る

[s8b_ratified_freeze.py:2415](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/campaign/s8b_ratified_freeze.py:2415) の直前へ追加します。

想定シグネチャ:

```python
def _selector_evidence_exempt_exact(
    *, head: str, root: Path
) -> Dict[str, str]:
```

データフロー:

```text
H:selector_predictions.json
  → strict parse + declaration-only validation
  → rowごとの payload/raw exact path と期待shaを導出
  → fixed journal/predictions を追加
  → H tree regular blob
  → H bytes == no-follow worktree bytes
  → 宣言shaがある対象は sha256(H bytes) と比較
  → exact path → sha256(H bytes)
```

具体的な対象は次です。

- `output/s8b-freeze/selector_predictions.json`
- `output/s8b-freeze/selector-runs/journal.jsonl`
- agent 4セルの `payload_<target>_<arm>.json`
  - hash は row の `input_payload_sha256` と一致必須。
- `status in {"valid", "invalid"}` の row の `raw_<target>_<arm>.txt`
  - path は row 宣言と runner の決定的 path の双方に一致必須。
  - hash は `raw_sha256` と一致必須。
  - H bytes を parser に再投入し、status/choice/rationale/error code を照合。
- `envelope_<target>_<arm>.json`
  - brief 外なので親裁定事項。ただし production 完全性のため、H に実在する決定的 path を同じ exact/hash 条件で含めるのを推奨します。

predictions が H に存在しなければ `{}` を返します。存在する場合は journal/payload、非missing raw が1件でも欠ければ fail-closed です。

### 3. path・mode・bytes・重複拒否

同 helper 内で以下を強制します。

- raw POSIX canonical relative path。
- fixed `selector-runs` 配下・cell別 basename との完全一致。
- exemption path の重複と active-chain map との衝突を拒否。
- H tree mode は `100644`/`100755` のみ。
- component lstat + leaf `O_NOFOLLOW`。
- H bytes と worktree bytes の完全一致。
- payload/raw は宣言 SHA とも一致。

reason code は上位を `scan-exemption-invalid` に統一し、`cause` を以下に分けます。

- `selector-declaration-invalid`
- `selector-evidence-path`
- `selector-evidence-duplicate`
- `selector-evidence-missing`
- `selector-evidence-mode`
- `selector-evidence-bytes`
- `selector-evidence-hash`
- `selector-raw-invalid`

なお通常の `launch_validate()` では dirty 改変は先に `namespace-dirty`、commit 済み改変は `history-mutated` で落ちます。この優先順位は変えません。

### 4. launch_validate へ合流

[s8b_ratified_freeze.py:2776](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/campaign/s8b_ratified_freeze.py:2776)

- `_assert_no_untracked_symlink()` 後に active-chain map と selector map を別々に構築。
- key 集合が交差しないことを確認してから併合。
- [同:2797](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/campaign/s8b_ratified_freeze.py:2797) の `search_repository(root, exempt_exact=...)` は変更しません。
- selector map にない同 prefix のファイルは通常 scan され、三軸 hit なら既存 `closure-hit-mismatch` になります。
- [同:2576](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/campaign/s8b_ratified_freeze.py:2576) の certificate raw hit 無条件拒否は触りません。
- reason 優先順 docstring の段7を「active-chain + selector exact exemption」に更新します。

## 変更単位B: allowlist を certificate digest に束縛

### 1. canonical digest preimage

[s8b_floor_campaign.py:1404](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/campaign/s8b_floor_campaign.py:1404)

`clean_scan_digest()` のシグネチャは維持します。

```python
def clean_scan_digest(root: Path, *, freeze_allowlist: Mapping) -> str:
```

戻り値を、単なる改行区切り filename hash から次の versioned canonical JSON hash へ変更します。

```json
{
  "schema": "s8b-clean-scan-digest/v2",
  "repository_files": ["..."],
  "freeze_allowlist": [
    {"path": "...", "sha256": "..."}
  ]
}
```

- `repository_files` は既存の sorted enumeration。
- `freeze_allowlist` は path 順の配列。
- `json.dumps(sort_keys=True, separators=(",", ":"), allow_nan=False)` の UTF-8 bytes を SHA-256。
- `_assert_freeze_allowlist()` の filesystem/hash 検査を通過した mapping だけを preimage に入れます。
- 同じ filename 集合でも allowlisted bytes が異なれば digest が異なることを固定します。

### 2. certificate validator を identity 層と strict 層に分離

[s8b_launch_cert.py:50](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/campaign/s8b_launch_cert.py:50)

既存ロジックを identity validator へ抽出し、public strict validator に clean digest の expected 引数を追加します。

```python
def _validate_launch_certificate_identity(
    cert: Mapping, *,
    expected_v1_freeze_sha256: str,
    expected_protocol_sha256: str,
    expected_run_id: str,
) -> dict: ...

def validate_launch_certificate(
    cert: Mapping, *,
    expected_v1_freeze_sha256: str,
    expected_clean_scan_digest: str,
    expected_protocol_sha256: str,
    expected_run_id: str,
) -> dict: ...
```

strict 層は identity 検証後に

```python
cert["clean_scan_digest"] == expected_clean_scan_digest
```

を厳密比較します。不一致は `LaunchCertError` のメッセージを `launch certificate.clean_scan_digest が expected と不一致` に固定し、floor adapter では既存どおり `FloorCampaignError` へ翻訳します。

`_CERTIFICATE_KEYS` と schema v1 は変更不要です。実 certificate がまだ存在しない段階で、既存 field の意味を強化する変更だからです。

### 3. 発行前の独立再scanと、発行 bytes の再検証

[s8b_floor_campaign.py:1465](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/campaign/s8b_floor_campaign.py:1465)

```python
def _official_launch_preflight(...) -> tuple[dict, str]:
```

へ変更します。

1. `clean_scan_digest()` 1回目で certificate を構築。
2. 同じ allowlist で `clean_scan_digest()` をもう一度独立実行。
3. 2回目の値を expected として、in-memory certificate を strict 検証。
4. certificate と独立再計算値を返す。

2回目を発行後に行ってはいけません。既定 out_root は repo 内 `output/` であり、発行した certificate 自身が enumeration に追加されて digest が必ず変わるためです。

[s8b_floor_campaign.py:1492](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/campaign/s8b_floor_campaign.py:1492)

```python
def _revalidate_issued_certificate(
    cert_path: Path, *,
    expected_v1_freeze_sha256: str,
    expected_clean_scan_digest: str,
    expected_protocol_sha256: str,
    expected_run_id: str,
) -> tuple[dict, bytes]:
```

- 発行済み raw bytes を strict parse。
- 発行前2回目 scan の値を public strict validator に渡す。
- certificate 内の自己申告値を expected として使う恒真比較は禁止。

[s8b_floor_campaign.py:2621](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/campaign/s8b_floor_campaign.py:2621) は tuple を受け取り、[同:2658](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/campaign/s8b_floor_campaign.py:2658) へ expected digest を渡します。

resume と ratified verifier は元の pre-start scan snapshotを再構成できません。そのため identity validator と既存 cert raw hash chain を使用し、clean digest の歴史的独立照合は scope 外の lineage wave に残します。certificate 自身を expected にする実装は置きません。

`EQUALITY_CHAIN_ADJACENCY` には node を追加しません。clean digest は別 artifact との等値辺ではなく、発行前 scan の独立再計算との比較だからです。

## P1〜P6 の裁定

| 項目 | 裁定 | 根拠 |
|---|---|---|
| P1 | 採用 | `exempt_exact` 指定時は prefix 除外が無効になり repo 全体を scan するため、移動に安全上の利得がなく pin/test churn だけが増えます。 |
| P2 | 否認 | full `verify_prediction_freeze()` は現在 source bytes を再束縛し、seal 後の正当な source drift を拒否します。代案は declaration-only 検証 + H raw/payload の独立 exact/hash 検証です。 |
| P3 | 条件付き採用 | H/worktree/hash と append-only に加え、実 seal commit で predictions/journal を `FROZEN_MANIFEST` へ pin することを完了条件にします。現 manifest にはまだ存在しません。 |
| P4 | 採用 | canonical allowlist fold、strict expected 比較、発行前独立再scanを実装します。adjacency 追加は不要です。 |
| P5 | 採用 | H に predictions がなければ selector exemption は空。従来の active-chain exact map と scan だけを使います。 |
| P6 | 採用 | 現 payload は `read_ratio_percent`/数値化された `skew` 等で三軸 scanner のキー表現を含みません。ただし exact path + row hash があるため、artifact 束として免除に含めます。 |

## 新規・変更テスト

### Exemption 側

[test_s8b_selector_freeze.py:427](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/tests/test_s8b_selector_freeze.py:427)

- `test_prediction_declaration_validation_is_stable_across_live_source_drift` — 正。
- `test_full_prediction_verifier_still_rejects_live_source_drift` — 負。public verifier を弱めていないことを固定。

[test_s8b_selector_input.py:54](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/tests/test_s8b_selector_input.py:54)

- `test_canonical_selector_payloads_have_no_holdout_conjunction_hit` — 正、P6 の characterization。

[test_s8b_ratified_verify.py:848](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/tests/test_s8b_ratified_verify.py:848)

- `test_selector_exact_exemption_accepts_declared_three_axis_evidence` — 正。
- `test_selector_exact_exemption_absent_prediction_is_noop` — 正。
- `test_selector_exact_exemption_rejects_undeclared_selector_run_hit` — 負、`closure-hit-mismatch`。
- `test_selector_exact_exemption_rejects_invalid_prediction_declaration` — 負。
- `test_selector_exact_exemption_rejects_payload_sha_mismatch` — 負。
- `test_selector_exact_exemption_rejects_duplicate_raw_path` — 負。
- `test_selector_exact_exemption_rejects_h_worktree_bytes_mismatch` — 負、helper 直接駆動。
- `test_selector_exact_exemption_rejects_worktree_symlink` — 負、helper 直接駆動。
- `_NEGATIVE_REGISTRY` に launch-level 負例と reason/cause を追加。

### Certificate 側

[test_s8b_floor_campaign.py:2278](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/tests/test_s8b_floor_campaign.py:2278)

- 既存 `test_clean_scan_digest_returns_digest_when_clean` の期待値を canonical preimage に更新。
- 既存 `test_clean_scan_digest_accepts_exact_freeze_allowlist` の期待値を更新。
- `test_clean_scan_digest_binds_allowlist_path_and_sha256` — 正。filename が同じで allowlisted bytes のみ異なる2 repoの digest が異なることを検査。
- `test_official_preflight_rejects_digest_shift_between_independent_scans` — 負。1回目/2回目を異なる値にし、副作用前拒否。
- `test_revalidate_issued_certificate_accepts_independent_clean_digest` — 正。
- `test_revalidate_issued_certificate_rejects_tampered_clean_digest` — 負。
- `_valid_launch_certificate()`、`_validate_launch()` と resume/fresh call sites に expected 引数を追随。

[test_s8b_launch_cert.py:25](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/tests/test_s8b_launch_cert.py:25)

- `_validate()` に `expected_clean_scan_digest` を追加。
- `test_validate_launch_certificate_rejects_clean_scan_digest_mismatch` — 負。
- 既存正常系は strict expected 一致へ更新。

## 変異テスト候補

| 位置 | 変異 | 単一理由性 |
|---|---|---|
| `launch_validate` の selector map 合流 | selector map の merge を削除 | 証拠を最初のbase commitで導入するため dirty/history gateは通過。raw/prediction/journalだけが scan に戻り `closure-hit-mismatch` になる。 |
| selector exact map 構築 | fixed path列挙を `selector-runs/` prefix全免除へ変更 | 同じbase commitに未宣言三軸hitを置く。手前のhistory/modeは通り、baselineだけ full scanで拒否、mutantだけ通過。 |
| payload SHA 比較 | `sha256(H payload) == input_payload_sha256` を削除 | 誤payloadを初回導入するため dirty/history拒否なし。declarationは通り、この比較だけが拒否理由。 |
| predictions 不在分岐 | `{}` 返却を必須拒否へ変更 | selector証拠なしの既存有効fixtureは他gateを通るため、P5だけを拘束。 |
| clean digest preimage | allowlist列をpreimageから削除 | 同一filename集合・異なる正当allowlist bytesの2 repoを使い、他のscan/allowlist検査は双方通過。 |
| strict cert validator | clean digest equalityを削除 | 他5 fieldと形式を正しくしたdirect leaf testで、この比較だけが拒否理由。 |
| official preflight | 2回目scanを削除、または1回目値を再利用 | stubを `d1,d2` と返させる。baselineは副作用前拒否、mutantだけ発行へ進む。 |

次は変異候補にしません。

- H/worktree bytes guard:通常の `launch_validate()` では `namespace-dirty` が先行。
- 既存 bytes のcommit改変: `_collect_records()` の `history-mutated` が先行。
- tracked/untracked symlink: `_list_namespace()`、namespace clean、または `_assert_no_untracked_symlink()` が先行。

これらは helper 単体の防御テストは置きますが、無効化しても launch の受理集合が変わらないため変異候補には不適格です。

## 「16ファイル」への波及

literal 検索では17ファイルです。`test_task_run_ledger.py` を汎用 namespace guard として除外すると、brief の16と一致します。

直接変更:

- `test_s8b_floor_campaign.py`
- `test_s8b_ratified_freeze.py`
- `test_s8b_ratified_verify.py`
- `test_s8b_selector_freeze.py`
- `test_s8b_selector_input.py`

将来の実 seal commit でのみ変更:

- `test_frozen_artifacts.py` — predictions/journal等の実 bytes ができた時点で manifest件数・hashを追加。

変更不要:

- `test_hooks.py`
- `test_s8b_approved.py`
- `test_s8b_budget.py`
- `test_s8b_freeze_io.py`
- `test_s8b_holdout_freeze.py`
- `test_s8b_oracle_driver.py`
- `test_s8b_oracle_manifest.py`
- `test_s8b_oracle_report.py`
- `test_s8b_prediction_runner.py`
- `test_s8b_protocol_builder.py`
- `test_task_run_ledger.py`

また、literal 17には含まれない `test_s8b_launch_cert.py` が validator signature 変更の直接波及先です。

### emitter fixture

[_prepare_emitter_base:421](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/tests/test_s8b_ratified_freeze.py:421) の seed→evidence→base commit 順は維持します。

[_install_emitter_selector_prediction:460](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/tests/test_s8b_ratified_freeze.py:460) は変更必須です。

- 現在は journal に4件の `payload_path` を書くだけで payload file を作っていません。
- 4 agent cell の canonical payload bytes を実際に作り、row `input_payload_sha256` と一致させます。
- 正例用オプションとして1セルを valid にし、三軸 rationale を含む raw file・journal invocation・prediction rowを初回base commitへ同時導入できるようにします。
- all-null既定は維持し、既存 emitter tests の意味を変えません。

## 実装分割

### 単位A: exemption

所有ファイル:

- `orchestrator/campaign/s8b_ratified_freeze.py`
- `orchestrator/campaign/s8b_selector_freeze.py`
- `orchestrator/tests/test_s8b_ratified_freeze.py`
- `orchestrator/tests/test_s8b_ratified_verify.py`
- `orchestrator/tests/test_s8b_selector_freeze.py`
- `orchestrator/tests/test_s8b_selector_input.py`

### 単位B: certificate binding

所有ファイル:

- `orchestrator/campaign/s8b_floor_campaign.py`
- `orchestrator/campaign/s8b_launch_cert.py`
- `orchestrator/tests/test_s8b_floor_campaign.py`
- `orchestrator/tests/test_s8b_launch_cert.py`

この案では所有集合は素で、certificate 単位から emitter fixture の編集は不要です。もし実装中に certificate bytes変更へのfixture追随が必要になった場合は、単位Aを先に完了・patch固定し、単位Bが取り込んだ後に開始します。単位Bは共有fixtureを直接編集せず、必要な追随を単位A/親へ返してから再適用します。

## リスク・未解決点

- `envelope_*.json` は明確な brief 漏れです。推奨は同じ exact/H-hash 条件で追加。4種限定を維持するなら「production seal由来の正当な三軸 rationaleが必ず通る」とは主張できません。
- P2代案は full verifier より意図的に狭い declaration validatorです。pre-oracle blob lineage検証を同時に持ち込まないことを親裁定で明記する必要があります。
- predictions/journal の `FROZEN_MANIFEST` pin は実ファイル不在のため本実装単位では完了できません。seal commit の必須同梱条件です。
- resume/ratified側では過去のclean scan preimageを独立再構成できません。cert raw hash chainは維持しますが、歴史的 clean digest の検証は予定どおり lineage waveまで未解決です。
- 二重scanはコストが倍になりますが、official開始時だけで、発行前の受理集合変化を検出できます。同名・namespace外ファイルのcontent-only TOCTOUは既存 residualのままです。
- preflight allowlist は現在 `selector-runs` の全実在fileを列挙します。digest束縛で内容は証明されますが、「未知fileを拒否」へは変わりません。これは本scope外です。
- 実 protocol/predictionがないため統合E2Eは構造的に実行不能です。

read-only 制約に従い、コード変更・pytest 実走は行っていません。

# §3 敵対相談 A — 正しさ境界 (codex、段 3)

# 総合判定

**NO-GO。** v1 は「seal 由来の証拠」と「攻撃者が自己整合的に捏造した prediction/journal」を区別できず、certificate 側も未知 `selector-runs/**` を無上限に受理したままです。規律 2 の exact-evidence 例外として成立していません。

## 所見テーブル

| ID | 深刻度 | 対象 | file:line | 主張 | 根拠 |
|---|---|---|---|---|---|
| C01 | must-fix | brief P2 / plan A-1,A-2 | [s8b_selector_freeze.py:598](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/campaign/s8b_selector_freeze.py:598)、[s8b_prediction_runner.py:1102](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/campaign/s8b_prediction_runner.py:1102)、[test_s8b_ratified_freeze.py:460](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/tests/test_s8b_ratified_freeze.py:460) | declaration-only 文書は seal 由来を証明しない。`body_sha256`、raw hash、provenance は攻撃者が一緒に再計算できる。`pre_oracle_head` の ancestry、同 commit の source blob、journal からの row 再導出がない。しかも正例 fixture 自身が L465 で「production seal 由来ではない」と明記されている。`invalid` row なら任意の UTF-8 raw を parser error として自己整合させられる。<br>**放置時:** 捏造 prediction が最大4本の任意 raw bytes を免除し、`LaunchValidatedFreeze` とその後の certified 選択・レポート・台帳が seal 未実行の choice/provenance を受理する。 | production seal は HEAD 一致、source read-once、journal binding、実行体 hash、destination reload を L1107–1194 で課すが、提案 helper はそれを一切再構成しない。 |
| C02 | must-fix | brief P3 / plan A-2 | [test_frozen_artifacts.py:33](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/tests/test_frozen_artifacts.py:33)、[s8b_ratified_freeze.py:1059](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/campaign/s8b_ratified_freeze.py:1059) | `FROZEN_MANIFEST` はテスト側 literal であり、runtime verifier は参照しない。H の append-only 検査も「最初から捏造された bytes」を正当化するだけである。将来同じ commit で捏造 bytes と期待 hash を追加できる。<br>**放置時:** 最初に pin された捏造 prediction/journal が恒久的な正当 artifact として受理され、certified 選択の参照先が実 seal ではなく捏造 bundle になる。 | `_collect_records()` は未知 namespace file に `_immutable_introductions()` を掛けるが、seal provenance や candidate commit 制約は掛けない。 |
| C03 | must-fix | brief P2 / plan A-2 | [s8b_prediction_runner.py:423](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/campaign/s8b_prediction_runner.py:423)、[test_s8b_floor_campaign.py:2404](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/tests/test_s8b_floor_campaign.py:2404) | journal は固定 path に存在するだけで丸ごと免除される計画で、schema、run header、seq、claim/invocation、prediction rows との一致を検査しない。現行 preflight test は実際に `b"{}\n"` を有効 journal として通している。<br>**放置時:** 三軸語を含む任意 journal bytes が scan から消え、certified 選択・certificate・台帳が存在確認だけの偽 journal を参照する。 | production に既に `resolve_journal()` があるのに、提案データフローから完全に脱落している。 |
| C04 | must-fix | brief P2/P6 / plan envelope 裁定 | [s8b_prediction_runner.py:963](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/campaign/s8b_prediction_runner.py:963) | envelope は二択とも破綻する。除外すると成功 envelope の `result` に残る正当三軸 rationale が拒否される。含める案は、hash 宣言も schema/result→raw 照合もなく、単に「決定的 filename が H に存在」で免除する。さらに envelope は検証前に書かれるため、失敗 invocation の孤児 envelope も残る。<br>**放置時:** envelope 非包含では正当 seal の受理集合が欠落し、包含では孤児・捏造 envelope の任意 bytes が受理集合へ入る。 | L963 で保存後、L969–1013 で初めて意味検証する。失敗時は invocation/raw が作られず prediction row は後続 resume で `missing` になり得る。 |
| C05 | must-fix | brief P1/P4 / plan B・リスク節 | [s8b_floor_campaign.py:1339](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/campaign/s8b_floor_campaign.py:1339)、[s8b_holdout_freeze.py:312](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/campaign/s8b_holdout_freeze.py:312)、[test_s8b_floor_campaign.py:2413](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/tests/test_s8b_floor_campaign.py:2413) | official preflight は `selector-runs.rglob("*")` の全 file を現在 bytes から自動 allowlist 化する。一方 clean scan は `exempt_exact=None` なので `output/s8b-freeze/` を prefix 除外する。digest fold はこの無上限集合を「証明」するだけで、未知 file を拒否しない。既存 test は任意 payload/raw/envelope の自動追加を正例として固定している。<br>**放置時:** 任意個の未宣言三軸 file を `selector-runs/**` に置いた repo が official certificate・floor report・journal を生成でき、`clean_scan_digest` もその rogue 集合を正当値として変える。 | exact path/hash は「許可対象を trusted declaration から導出」して初めて allowlist になる。filesystem からの自己列挙は denylist 不在の自己申告である。 |
| C06 | must-fix | brief P4 / plan B-2,B-3 | [s8b_launch_cert.py:50](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/campaign/s8b_launch_cert.py:50)、[s8b_ratified_freeze.py:2606](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/campaign/s8b_ratified_freeze.py:2606)、[s8b_floor_campaign.py:3078](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/campaign/s8b_floor_campaign.py:3078) | 発行直後の expected 比較は非恒真にできるが、plan は resume/ratified を identity validator に逃がす。その二経路では `clean_scan_digest` は64hexなら任意で、cert raw hash chain は「偽値を含む同じ bytes」を束縛するだけである。<br>**放置時:** 任意の clean digest を持つ coherent cert/journal/result が ratified floor として受理され、certified 選択・レポート・台帳の certificate hash が偽 clean 証明を参照する。 | certificate に preimage/allowlist artifact が保存されないため、後続 verifier が expected を独立導出できない。これは lineage scope 外へ送ってよい付加機能ではなく、durable certificate の意味そのもの。 |
| C07 | must-fix | brief P4 / plan B-3 | [s8b_floor_campaign.py:1404](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/campaign/s8b_floor_campaign.py:1404)、[s8b_ratified_freeze.py:2479](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/campaign/s8b_ratified_freeze.py:2479) | 2回 scan は content TOCTOU を閉じない。同名 file は両 scan 時だけ無害化して直後に三軸 bytes へ戻せる。repository file content、HEAD、index mode は digest に入らず、selector artifacts も scan 後再捕捉されない。`search_repository` は exemption hash 不一致を拒否せず通常 scan に戻すため、helper 後の差替えも最終 H/worktree 不一致としては検出されない。<br>**放置時:** certificate 発行時には三軸 hit が復元済みでも、2回とも同じ clean digest を返し、official cert/report/ledger が clean として受理する。 | 同じ helper を2回呼ぶのは時間窓の観測点を増やすだけで、snapshot/seal ではない。 |
| C08 | must-fix | plan A/B 境界 | [s8b_floor_campaign.py:1297](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/campaign/s8b_floor_campaign.py:1297)、[s8b_selector_freeze.py:693](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/campaign/s8b_selector_freeze.py:693) | floor preflight は prediction raw bytes を plain `json.loads` し、duplicate key を last-wins で潰す。selector module には strict parser があるが未使用。先行 duplicate 値に三軸語、後続値に正当値を置き、collapsed object 用 `body_sha256` を与えれば full verifier を通る。<br>**放置時:** raw prediction bytes に三軸 conjunction があるのに prefix scan されず、certificate・floor report・journalが発行される。 | launch helper の strict parse が後で拒否しても、floor 成果物を既に生成した事実は消えない。 |
| C09 | should-fix | brief P4 / plan B-1 | [s8b_ratified_freeze.py:1357](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/campaign/s8b_ratified_freeze.py:1357)、[s8b_floor_campaign.py:1357](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/campaign/s8b_floor_campaign.py:1357) | versioned JSON 自体は改行・quote・backslash を曖昧なく符号化するので正しい。一方、launch 側の既存 `"\n".join(files)` は残り、`["a","b\nc"]` と `["a\nb","c"]` が衝突する。また allowlist validator は余剰・不存在 key、`//`、`./`、control を raw canonical として拒否しないため、同じ実在集合に複数 digest が作れる。 | preimage JSON の collision は閉じるが、入力 domain の canonical 化と launch enumeration digest は閉じていない。 |
| C10 | should-fix | brief P2 / plan A-3 | [s8b_prediction_runner.py:504](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/campaign/s8b_prediction_runner.py:504)、[s8b_ratified_freeze.py:2447](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/campaign/s8b_ratified_freeze.py:2447) | runner 生成 mode は0644だが計画は H の100755も受理し、worktree executable bit と H mode の一致も要求しない。bytes scan には無害でも「seal 由来 exact artifact」という主張とは不一致。 | selector 証拠は active-chain record と異なり executable mode を許す理由がない。100644固定が自然。 |

## declaration-only と full verifier の差分

| 差分 | full verifier | plan | scan 健全性への判定 |
|---|---|---|---|
| `pre_oracle_head` | repo 内の任意 commit 実在のみ確認（L627–629）。ancestry は見ない | I/O-free 化で実在確認も脱落 | **必要。** 少なくとも `pre_oracle_head ∈ ancestors(H)` が要る。ただし実在確認だけでも不十分。 |
| sources 5本 | 文書が宣言した任意 path の現在 worktree bytes と比較（L630–632） | live drift 回避のため削除 | 現在 bytes 比較は過剰拒否だが、削除は誤り。**固定 source path + `pre_oracle_head:path` blob hash** に置換すべき。 |
| row/basis/body | 再導出 | 維持 | path数・cell集合の上限には必要。ただし自己 hash なので seal authenticity にはならない。 |
| raw hash/parser | worktree raw を再parse（L639–642） | H raw を再parse | **必要で、H版は改善。** ただし `invalid` raw はほぼ任意のUTF-8 bytesを受理できるため journal provenance が不可欠。 |
| raw/payload path | root 内なら任意 raw path、payload実体は未検査 | cell別固定 basename、H mode/bytes、payload hash | **改善。** traversal・cell衝突・任意 path 拡張は閉じられる。 |
| journal | 検査しない | 検査しないまま丸ごと免除 | **scan 健全性に必須。** production `resolve_journal` と prediction row の双方向一致が必要。 |
| envelope | 検査しない | 存在ベースで任意追加案 | **必須。** 成功 envelope は `result == raw`、孤児 envelope は免除不可。 |
| prediction raw JSON | verifier API は既に parse 済み Mapping を受ける | H bytes を strict parse と記載 | launch 側では必要。floor preflight 側も同じ strict parserへ統一しないと二重受理集合になる。 |

したがって、full verifier の live-source drift 問題は実在するものの、declaration-only への単純縮退は正当化されません。必要なのは「現在 worktree」から「H/pre-oracle の歴史 blob + journal」への oracle 変更です。

## exemption 集合の上限

current freeze の2 holdoutと固定 armを用いる限り、launch selector map 自体の個数は有界です。

| 構成 | selector exemption の全対象 | selector最大 | active-chain 4件込み |
|---|---|---:|---:|
| prediction 不在 | なし | 0 | 4 |
| envelope なし | predictions、journal、`payload_{rr20,rr80}_{on,swapped}.json` 4本、`raw_{rr20,rr80}_{on,swapped}.txt` 最大4本 | 10 | 14 |
| envelope あり | 上記 + `envelope_{rr20,rr80}_{on,swapped}.json` 最大4本 | 14 | 18 |

ただし次の点で安全とはならない。

- raw path 重複は、cell別 basename 完全一致を先に課せば構造上不可能である。`selector-evidence-duplicate` は独立受理理由にならず、削除しても受理集合が変わらない防御になる。
- cell名衝突は launch が ratified freeze の固定 `rr20/rr80` を使う限り起きない。任意 freeze を helper に渡せるAPIにするなら別途禁止が必要。
- envelope なしは production completeness を満たさず、ありは未宣言 artifact を免除する。
- **certificate preflight の集合は別物で、`selector-runs/**` の filesystem 全列挙なので無上限。** v2 digest 化してもこの上限欠落は直らない。

## 規律2と拒否優先順

- cert raw conjunction の無条件拒否は [s8b_ratified_freeze.py:2576](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/campaign/s8b_ratified_freeze.py:2576) にあり、selector exemption より前なので維持される。
- active-chain map を selector mapより先に構築すれば、通常の selector namespace dirty は再度 `resolve_active_generation()` に入り `namespace-dirty`、既存 committed bytes の変異は `_collect_records()` の `history-mutated` が先行する。
- ただし stale `RatifiedFreeze` 取得後に commit すれば最初は `activation-head-moved` であり、常に `history-mutated` ではない。また ratified load 後に untracked symlinkを加えた場合、`_assert_no_untracked_symlink()` が active再解決より前なので `scan-exemption-invalid` が先行する。
- 最大の破れは優先順ではなく、**捏造 evidence が「正当 exact bytes」と誤分類されて conjunction 拒否そのものから消えること**である。

## 変異候補7件

| # | 判定 | 手前検査・単一理由性 |
|---:|---|---|
| 1. selector map merge削除 | 条件付き成立 | 初回commit導入なら dirty/history は先行しない。`closure-hit-mismatch` 一理由で赤くできる。ただし正例 fixture が非seal由来なので、merge配線は殺せても authenticity を何も証明しない。 |
| 2. fixed列挙→prefix全免除 | **未確定** | 現 API は exact mapしか受けないため「prefix全免除」が具体的な単一diffになっていない。`H namespace の prefix全pathを mapへ追加` 等、実際の mutant を固定すれば baseline=`closure-hit-mismatch`、mutant=通過にできる。現記述のまま登録不可。 |
| 3. payload SHA比較削除 | 条件付き成立 | map値を常に `sha256(H bytes)` にする実装なら、誤payloadはこの比較だけで落ち、削除後はexempt hashも一致する。map値を宣言SHAにすると downstream scanでも落ちるため過剰決定になる。実装形まで固定が必要。 |
| 4. predictions不在 `{}`→拒否 | **現 fixture では不成立** | emitter base は L445で必ず predictionsを入れ、official preflightも L1280–1310で必須化している。「証拠なしの既存有効 fixture」は存在しない。A commit後に selector bundleをcommit削除し、改めてloadする fixtureか、launch-level別builderが必要。helper単体ではP5のlaunch受理集合を証明しない。 |
| 5. allowlist列をpreimageから削除 | 成立 | 同一path集合・異なる実bytesをそれぞれ正しいallowlistで検査すれば前段は双方通り、digest不一致assertだけが赤くなる。これは出力値の単一理由変異。 |
| 6. strict clean equality削除 | 成立 | direct leafで他fieldと64hex形式を正しくすれば、この比較だけが拒否理由。ただし resume/ratified が identity validatorを使う穴はこの変異では殺せない。 |
| 7. 2回目scan削除／1回目再利用 | 成立 | `d1 != d2` の stubなら前段clean scanを迂回し、strict equalityだけでbaseline拒否、mutant通過にできる。call count `==2` も固定しないと「expectedの取り違え」を区別できない。content TOCTOUの証明にはならない。 |

したがって、7件中そのまま確定できるのは M5/M6/M7、実装形を固定すれば M1/M3、現状不成立または未定義なのは M2/M4 です。

## P1〜P6 独立判定

| 項目 | 判定 | 根拠 |
|---|---|---|
| P1 | **否認** | launch の prefix除外は消えるが、official preflightでは現配置だけが prefix scan外かつ `selector-runs/**` 自動allowlist対象になる。さらに scanner はignored file、tracked symlink/gitlink、NUL/非UTF-8を全走査しないため「repo内にscanされない場所なし」は事実でない。 |
| P2 | **否認** | full verifier のlive-source照合は歴史 artifactに不適切だが、declaration-onlyはseal provenanceを失う。H/pre-oracle source blobs、ancestry、journal→rows、成功envelope→rawを検証する別 verifier が必要。 |
| P3 | **否認** | `FROZEN_MANIFEST` はruntime rootでなく、初回捏造と期待hashの同時追加を防がない。H/worktree/history一致も初回bytesの正当性を証明しない。 |
| P4 | **否認** | versioned canonical JSON foldと発行直後expected比較は採れるが、無上限allowlist、content TOCTOU、resume/ratifiedでのidentity-only受理により certificate 束縛として未完成。 |
| P5 | **採用** | launch selector exemptionに限れば、prediction不在時 `{}` は安全側であり、同prefixの残存fileは通常scanへ戻る。official preflightは別途prediction必須なので適用範囲を混同してはならない。 |
| P6 | **否認** | canonical payloadは `read_ratio_percent`、数値`skew`等で scanner の三軸表現を持たない。scanさせても通るため免除の利益がなく、payload SHA一検査の故障時だけ新たなfail-openを作る。 |

## NO-GOを解除する最低条件

- prediction を H から strict parseし、固定 source pathの `pre_oracle_head` blob、H ancestry、journalから再導出した6 rows、raw、成功 envelopeを相互束縛する。孤児 envelopeは免除しない。
- launch と floor preflightで同じ有界な宣言集合を使い、`selector-runs.rglob("*")` 自動allowlistを廃止する。
- clean preimageまたはその exact manifestをdurable artifactとして保存し、fresh、resume、ratifiedの全経路で外部 expected と比較する。
- M2の具体的diffとM4の実在 launch fixtureを確定し、非seal fixtureは正例ではなく「捏造拒否」の負例へ反転する。

pytestは実行せず、以上は対象コードの静的読解による判定です。

# §4 敵対相談 B — 整合・実効性 (codex、段 3)

## 所見テーブル

| ID | 深刻度 | 対象 | file:line | 主張 | 根拠 |
|---|---|---|---|---|---|
| F-01 | must-fix | brief P2 / plan A-1 | [s8b_selector_freeze.py:278](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/campaign/s8b_selector_freeze.py:278), [同:423](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/campaign/s8b_selector_freeze.py:423), [s8b_selector_input.py:73](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/campaign/s8b_selector_input.py:73), [s8b_descriptor.py:46](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/campaign/s8b_descriptor.py:46) | 提案する `_validate_prediction_document()` は I/O-free でも source-drift stable でもない。 | `_normalise_rows()` は現在コードの `build_prediction_jobs()` を呼び、そこから descriptor schema と selector catalog を現 filesystem から読む。raw 再parseも現在 parser の意味論である。sources の bytes 比較だけ抜いても、semantic drift で payload SHA・status・choice の再導出が変わる。さらに `_selector_evidence_exempt_exact(head, root)` がどの V1 freeze bytes を helper に渡すか未指定。<br>**放置すると、同一の封印済み prediction/raw が後日の catalog・schema・parser 更新だけで拒否され、certified 選択・レポート・台帳参照の受理集合が空または別集合になる。** |
| F-02 | must-fix | brief scope/P2/P3 / plan A-2・リスク | [s8b_prediction_runner.py:963](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/campaign/s8b_prediction_runner.py:963), [同:697](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/campaign/s8b_prediction_runner.py:697), [同:760](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/campaign/s8b_prediction_runner.py:760) | `envelope_*.json` を「推奨・親裁定」に残したままでは exact-exemption blocker は消えない。H の自己 hash だけで免除しても §5-(ix)-9 を満たさない。 | envelope は raw より先に保存され、`result` に raw 応答が残るため、三軸 `key=value` は envelope にも残る。一方、journal invocation と prediction row は raw path/hashしか持たず、envelope path/hashを宣言しない。検証失敗時には raw/invocation のない孤児 envelope も残りうる。したがって「H にその basename があった」という自己参照 hash は「既知宣言 artifact」ではない。<br>**放置すると、envelope を免除しなければ正当な production seal が `closure-hit-mismatch` で拒否され certified 選択が作れず、自己 hash で免除すれば未宣言 envelope の三軸内容が scan 盲点となり provenance 参照が未束縛になる。** |
| F-03 | must-fix | brief P4・D79(5) 前提 / plan B-1〜B-3 | [s8b_floor_campaign.py:1319](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/campaign/s8b_floor_campaign.py:1319), [同:1353](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/campaign/s8b_floor_campaign.py:1353), [同:1404](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/campaign/s8b_floor_campaign.py:1404) | D79(5) の「実在ファイル exact 列挙」は現コードで未成立。plan は不完全な mapping を忠実に digest 化するだけである。 | `add_if_file()` は `floor_protocol.json` 不在を黙って省略する。`_assert_freeze_allowlist()` は実在 file ごとに allowlist entry を探すだけで、allowlist の余剰・不存在 entry を拒否しない。allowlist 構築後に prediction/journal を削除すると phantom entry が残り、同じ mapping を使う二重 scan は二回とも通る。<br>**放置すると `clean_scan_digest` は「実在集合」ではなく欠落 protocol または phantom prediction/journal を含む mapping の hashになり、certificate の protocol・selector 証拠参照が発行時 snapshot と一致しない。** |
| F-04 | must-fix | plan B-2/B-3・実装分割 | [s8b_launch_cert.py:50](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/campaign/s8b_launch_cert.py:50), [s8b_ratified_freeze.py:47](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/campaign/s8b_ratified_freeze.py:47), [同:2606](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/campaign/s8b_ratified_freeze.py:2606), [s8b_floor_campaign.py:3078](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/campaign/s8b_floor_campaign.py:3078) | caller の概念列挙はしているが、A/B の所有集合は素ではない。 | mandatory `expected_clean_scan_digest` を追加する leaf は B 所有だが、その identity caller への変更が必要な `s8b_ratified_freeze.py` は A 所有である。Aを先行完了すると未存在 API を参照し、Bを先行すると現 ratified caller が必須引数欠落になる。resume も strict wrapper から identity API へ切替が必要。最小形は現 public identity validatorを残し、issuer専用 strict validatorを新設すること。<br>**放置すると未追随 caller は全 certificate を `TypeError` 相当で拒否して certified 選択・レポートを作れず、自己申告 digest を expected に渡す応急処置では任意 digest の受理集合が残る。** |
| F-05 | should-fix | plan「emitter fixture」「Exemption 正例」 | [test_s8b_ratified_freeze.py:460](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/tests/test_s8b_ratified_freeze.py:460), [s8b_prediction_runner.py:583](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/campaign/s8b_prediction_runner.py:583), [同:840](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/campaign/s8b_prediction_runner.py:840) | 提案された valid option は production seal の実形を模していない。 | 現 fixture は明示的に production seal 非由来で、plan の変更記述も payload・raw・journal invocation・prediction rowまでしか要求しない。`ClaudeHeadlessProvider` が作る envelope、`.lock`、journal receipt→`agent_provenance` の同一性を通らない。fake subprocess envelope を使って `drive_journal()` まで駆動し、生成集合そのものを正例にすべき。 |
| F-06 | should-fix | plan Certificate テスト・変異計画 | [test_s8b_floor_campaign.py:2325](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/tests/test_s8b_floor_campaign.py:2325), [同:2413](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/tests/test_s8b_floor_campaign.py:2413) | `binds_allowlist_path_and_sha256` の記述は SHA しか拘束しない。 | 「同じ filename、異なる bytes」では hash値の包含しか証明しない。二 path の bytes/hashを交換して hash multisetを同じにする正例対が必要。加えて余剰 entry、allowlist 構築後の削除、必須 protocol 不在、二 scan 間削除の負例がない。 |
| F-07 | should-fix | brief scope/P3 / plan リスク | [decisions.md:3282](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/docs/decisions.md:3282), [worklog.md:271](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/docs/worklog.md:271), [test_frozen_artifacts.py:33](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/tests/test_frozen_artifacts.py:33) | この wave が閉じられるのは「protocol 非依存の2機構」だけで、floor blocking 前提全体ではない。 | D79 は完全同型 E2Eも blocking とし、現 worklog は exemption・cert binding・E2E・lineage の4件を列挙する。さらに実 `FROZEN_MANIFEST` は依然8件で、prediction/journal pinは将来の seal commit 条件である。完了報告は「2/4 のコード機構完了」とし、実 pin 前に blocker 消化済みと記録してはならない。 |
| F-08 | should-fix | plan A-2 / scope | [s8b_holdout_freeze.py:303](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/campaign/s8b_holdout_freeze.py:303), [s8b_floor_campaign.py:1279](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/campaign/s8b_floor_campaign.py:1279) | predictions があれば journal/payload/raw 全存在を新たに launch 必須とする案は、exact exemption を越えた completeness gate である。 | §5-(ix)-9 は「存在する既知宣言 artifact を exact/hash 免除する」裁定で、欠落 file の全面拒否までは定めない。official 側の prediction/journal 必須化は既に別 gate にある。launch にも課すなら G2 の blocker限定に対する必要性か追加裁定が要る。 |
| F-09 | nit | brief scope / plan A-2 | [s8b_prediction_runner.py:563](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/campaign/s8b_prediction_runner.py:563), [同:880](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/campaign/s8b_prediction_runner.py:880), [s8b_selector_freeze.py:661](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/campaign/s8b_selector_freeze.py:661) | runner の全書込み inventory が brief/plan とも不完全。 | `.lock`、prediction writer の一時 file、repo 外の empty MCP config・invocation別 cwd が落ちている。`.lock` は fresh なら空で通常 scan に残してよいが、commit対象か成功時削除かを手順で確定すべき。 |

## production seal 生成集合との照合

正常に4 agent cellが完了したとき、repo内に永続する集合は次です。

```text
{selector_predictions.json, selector-runs/journal.jsonl, selector-runs/.lock}
∪ 4セル × {payload_<t>_<a>.json, envelope_<t>_<a>.json, raw_<t>_<a>.txt}
= 15 paths
```

plan の必須免除は predictions + journal + payload 4 + raw 4 の10 pathです。envelopeを追加して14 pathになり、`.lock`だけを通常 scan に残す形なら集合としては妥当です。ただし envelope は現 schema に path/hash宣言がないため、その14件目を安全に追加できません。

また envelope は検証前に書かれるため、claim-crash/resume では `payload + journal claim + .lock + 孤児 envelope` を伴う missing rowが成立します。この形も正例・負例双方に必要です。

repo内の一時 `.selector_predictions.json.*.tmp` は正常終了時に削除されます。`/tmp/s8b-selector-*/empty-mcp-config.json` と `cwd-*` はrepo外なので launch scan対象外です。

## P1〜P6 独立判定

| 項目 | 判定 | 独立根拠 |
|---|---|---|
| P1 | 採用 | `exempt_exact` 指定時は prefix除外が消えてrepo全体をscanするため、repo内移動だけでは解決しない。ただし envelope の宣言hash問題は配置では解けない。 |
| P2 | 否認 | full verifier は現 source bytesに結合し、planの抽出案も現 catalog/schema/parserを読むため、いずれも提示された「安定な declaration 検証」になっていない。 |
| P3 | 採用 | lineageを先取りせず、実 seal後の `FROZEN_MANIFEST` pinと後続 execution_guardへ委ねる方向はD79どおり。ただし実 pin完了前、および未pin envelopeには適用できない。 |
| P4 | 否認 | canonical allowlist fold自体は採用できるが、既存 public validatorを一律strict化する形はresume/ratifiedと両立しない。identity API維持＋issuer専用strict APIが必要。 |
| P5 | 採用 | Hにpredictionsが無ければ selector mapを空にし、既存active-chain mapと通常scanだけに戻るのが最小の挙動保存。 |
| P6 | 採用 | 現payloadは `read_ratio_percent`、`skew`、`rmw`で scanner の `ycsb_*` 三軸表記を作らない。rowの決定的payload hashと一致させて免除するのは安全。 |

関数内遅延 importによる循環回避自体は静的には成立します。また `clean_scan_digest` は他artifactとの等値辺ではないため、`EQUALITY_CHAIN_ADJACENCY` にnodeを追加しない判断も妥当です。NO-GOの理由はそこではありません。

## 総合判定

**NO-GO**

最低条件は以下です。

1. declaration validatorを現 filesystemのcatalog/schema/parserに依存しない形へ再設計し、HのV1 bytes取得元を明記する。
2. envelopeを必須対象に決め、成功・invalid・孤児の全形について外部hash宣言源を設ける。
3. allowlistを実在file集合との双方向exact一致にし、`floor_protocol.json` を必須化する。
4. identity validatorを維持したissuer専用strict APIへ分離し、A/Bを直列化する。
5. production-shaped provider fixture、path/hash交換、削除race、全caller回帰をテスト計画へ加える。

pytestは実行せず、以上は対象コードと既裁定の静的照合による判定です。

# §5 親裁定 v2 (段 4)

# wave3 親裁定 — 敵対相談 A/B (両 NO-GO) の消化とプラン v2 確定

plan v1 + 本裁定が実装子への正本。矛盾時は本裁定が優先する。

## 所見裁定 (A = 正しさ境界 C01-C10、B = 整合・実効性 F-01..09)

| ID | 裁定 | 処置 |
|---|---|---|
| C01 | real・採用 (範囲調整) | launch 側検証に ancestry・sources@pre_oracle_head blob・journal↔rows 照合・envelope 宣言を追加 (下記 v2 仕様)。raw の意味的再 parse は launch では行わない (F-01 drift 対策。bytes 束縛のみ)。初回導入捏造の完全閉鎖は D79 (7) 第 3 項の既裁定どおり oracle 結線 wave へ (worklog へ残余として明記) |
| C02 | real (事実)・新規 blocker とはしない | D79 (7) 第 3 項がこの残余を「FROZEN_MANIFEST 逐次 pin + oracle 側 execution_guard で代替、oracle 結線 wave で再評価」と既に裁定済み。本 wave は表面を狭める (ancestry/journal/envelope/sources)。残余を worklog/insights に明記 (F-07) |
| C03 | real・採用 | journal を H bytes から parse し、run_header 1 件・binding 再構成・resolve_journal・rows との cell/status/raw-sha 対応を検査してから免除 |
| C04/F-02 | real・採用 | runner 変更: envelope 書き込み直後 (検証前) に journal へ attempt record (envelope path + sha256) を追記。免除は attempt/invocation record が宣言した envelope のみ (sha 一致 + H==worktree)。宣言なき envelope は免除しない (真の crash 窓のみ残る。seal 側は commit 前に未宣言ファイル検出で fail) |
| C05/F-03 | real・採用 (範囲限定) | preflight allowlist を「宣言由来の有界集合」へ: 必須 4 (protocol/v1/predictions/journal、不在 = fail-closed。add_if_file の黙殺廃止)、raw/envelope は journal 宣言から導出、**selector-runs/ 配下 + 固定 4 file の範囲で未宣言実在ファイルは拒否・phantom entry も拒否 (双方向 exact)**。chain record dirs (approvals 等) は既存 chain validator の管轄のまま |
| C06 | real・分割 | 発行時 strict 照合 + 独立再計算 = 本 wave。durable preimage artifact + resume/ratified の歴史的照合 = scope 外 → 裁定パッケージ (oracle 結線 wave、D79 (7) 第 3 項の再評価と同梱)。影響限定の根拠: official は production 無条件拒否で dormant、実行 gate (launch_validate) は cert digest を消費せず独自 full scan を持つ |
| C07 | refuted (新規 blocker として) | content TOCTOU は clean_scan_digest docstring と §5-(viii) 残存限界 ([T-011] ユーザー受諾リスト) に記載済みの既知残余。本 wave は縮小も拡大もしない |
| C08 | real・採用 | prediction bytes の読取りを duplicate-key 拒否 parser に統一 (launch helper + preflight の両方。catalog loader の _reject_duplicate_keys パターンを再利用) |
| C09 | real・採用 | digest v2 preimage (versioned JSON) + allowlist path の canonical 検証 (絶対 path・`..`・`//`・`./`・制御文字・非 UTF-8 拒否) |
| C10 | real・採用 | 証拠免除の H mode は 100644 のみ (100755 不可) |
| F-01 | real・採用 | launch 側検証は build_prediction_jobs / catalog / descriptor schema / 現在 parser を**呼ばない**。cell 集合は _freeze_axes(freeze) のみから導出、input_payload_sha256 の再導出はしない (body_sha256 で文書内束縛済み)。V1 bytes は H から読み V1_FREEZE_SHA256 定数と照合 |
| F-04 | real・採用 | validate_launch_certificate の**現行シグネチャは不変** (identity 層として維持)。新設 `validate_launch_certificate_strict` (expected_clean_scan_digest 必須) を発行/再検証経路のみが使う。resume/ratified caller は無変更 → A/B 所有素集合が回復 |
| F-05 | real・採用 | emitter fixture の valid-cell option は fake subprocess envelope + drive_journal 実走で production-shaped 集合 (envelope/journal invocation/agent_provenance 込み) を生成する |
| F-06 | real・採用 | B 側テストに hash 入替え対・余剰 entry・構築後削除・protocol 不在・scan 呼数 ==2 を追加 |
| F-07 | real・採用 | 完了報告は「D79 (7) 4 件中、protocol 非依存 2 件の**コード機構**完了」。blocking 前提の全消化と書かない。実 pin・E2E・lineage は残余として列挙 |
| F-08 | refuted | 宣言済みファイルの不在 fail-closed は _active_chain_exempt_exact の exemption-missing (L2444-2446) と同一意味論。新規 gate 類型ではない |
| F-09 | real・採用 (小) | .lock は seal 正常終了時に削除 (advisory 運転状態であり証拠でない)。宣言集合に含めない。runner の tmp file は既存どおり削除 |

## P1〜P6 最終裁定

- P1 **維持 (根拠訂正)**: 移動しない。ただし brief の「repo 内に scan されない場所は無い」は過大 (cert lane の prefix 除外・ignored/symlink 盲点が実在)。正しい根拠 =「移動はどの盲点も閉じず、exact 免除は置き場所に依存しない。cert lane の盲点は C05 処置で閉じる」
- P2 **差替え**: declaration-only でも full verifier でもなく、**H 錨定の drift-free 検証** — (i) H blob 100644 + strict parse + body_sha256 + 構造検証 (純関数)、(ii) basis = H の V1 bytes (定数 sha 照合) から導出、(iii) pre_oracle_head ∈ ancestors(H)、(iv) sources は固定 path 集合かつ `pre_oracle_head:path` の git blob と bytes 一致 (worktree 非依存)、(v) journal↔rows↔envelope の相互対応、(vi) raw/envelope は宣言 sha == sha256(H bytes) + H==worktree
- P3 **維持**: D79 (7) 第 3 項の既裁定どおり。C02 残余を明記
- P4 **改訂**: v2 canonical preimage + strict/identity 分離 (F-04) + 有界 allowlist (C05)。EQUALITY_CHAIN node 追加なし (両相談一致)
- P5 **維持** (両相談採用)。predictions 不在 → 免除空集合・従来挙動
- P6 **反転**: payload は免除**しない** (A の論拠採用: 正当 payload は構造上 hit せず、tamper された payload はむしろ scan で拒否させたい。免除は利得ゼロで故障面だけ追加)。characterization test (payload に conjunction が無いこと) は採用

## 実装単位 (直列: A → 親 patch 展開 → B)

**単位 A (exemption + 証拠鎖)** 所有: s8b_prediction_runner.py / s8b_selector_freeze.py / s8b_ratified_freeze.py / test_s8b_prediction_runner.py / test_s8b_selector_freeze.py / test_s8b_selector_input.py / test_s8b_ratified_freeze.py / test_s8b_ratified_verify.py

**単位 B (cert 束縛)** 所有: s8b_floor_campaign.py / s8b_launch_cert.py / test_s8b_floor_campaign.py / test_s8b_launch_cert.py。A の宣言集合導出 helper を import してよい (A patch 展開後に起動)

## 変異テスト事前登録 (B-057、v2 仕様基準。anchor 逐語は実装後の最終 commit で確定)

| # | 位置 | 変異 | fixture / 期待 | 単一理由性 |
|---|---|---|---|---|
| M1 | launch_validate の selector map 合流 | merge 削除 | production-shaped 正当証拠 (三軸 rationale 入り、初回 commit): base 通過 → mutant closure-hit-mismatch | 初回導入なので dirty/history 不発火。scan 一理由 |
| M2 | 証拠免除 helper | 宣言 exact map を「H の selector-runs/ 配下全 path を sha256(H bytes) で追加」する prefix 免除へ置換 | base commit に未宣言三軸 file を同梱: base 拒否 → mutant 通過 | 受理集合の拡大が唯一の差 |
| M3 | raw sha 照合 | `宣言 raw_sha256 == sha256(H bytes)` の assert 削除 (map 値は常に sha256(H bytes)) | 宣言 sha を rows/journal 両方で同一の誤値にした初回導入 fixture: base 拒否 (selector-evidence-hash) → mutant 通過 | 両宣言を揃えれば他層は不発火 |
| M4 | predictions 不在分岐 | `{}` 返却を拒否へ | build_valid_semantic_g1 系 (selector 証拠なし) fixture: base 通過 → mutant 拒否 | emitter 系でなく semantic 系 fixture を使う (A 指摘の不成立を回避)。実装時に fixture 実在を確認し、なければ最小 builder を追加 |
| M5 | digest preimage | allowlist 列削除 | 同一 path 集合・異なる正当 bytes の 2 repo: base digest 相違 → mutant 一致 | 出力値のみの単一理由 |
| M6 | strict cert validator | clean digest equality 削除 | leaf 直接: 他 field 正・digest 誤の cert: base 拒否 → mutant 受理 | leaf 単独 |
| M7 | official preflight | 2 回目 scan 削除/1 回目値再利用 | scan stub d1≠d2 + 呼数 ==2 検査: base 副作用前拒否 → mutant 進行 | stub で前段迂回 |
| M8 | journal↔rows 照合 | 対応検査削除 | 三軸なし・構造 mismatch journal (例: claim 欠落) の初回導入: base 拒否 (selector-declaration-invalid) → mutant 通過 | journal 自体は axis-free にして scan 層の重畳を排除 |
| M9 | ancestry 検査 | `pre_oracle_head ∈ ancestors(H)` 削除 | 非 ancestor の実在 commit を pre_oracle_head にした fixture: base 拒否 → mutant 通過 | 形式 (40hex/実在) は通る値を使う |
| M10 | envelope 宣言照合 | envelope sha 照合削除 | 宣言 sha 誤の envelope 初回導入: base 拒否 → mutant 通過 | 宣言は attempt record のみ = 単一宣言源 |

非候補 (相談 A の判定を採用): H/worktree bytes guard・既存 bytes 変異・symlink 系は各々 namespace-dirty / history-mutated / 先行 assert が優先し、launch 受理集合の単一理由にならない。helper 単体テストのみ置く。

## scope 外 → 裁定パッケージ (ユーザーへ)

1. durable digest preimage artifact + resume/ratified の歴史的 cert 照合 (C06 後半) — oracle 結線 wave の lineage 再評価と同梱を推奨
2. 初回導入捏造の完全閉鎖 (C02) — 同上 (D79 (7) 第 3 項の再評価そのもの)
3. content TOCTOU (C07) — [T-011] 受諾リスト記載済み。追加処置なし推奨


# §6 実装報告 — 単位 A (codex、段 5)

## 変更点

- [s8b_prediction_runner.py](/home/SFC/tanab/github/izanagi/.claude/worktrees/wave3-unit-a/orchestrator/campaign/s8b_prediction_runner.py:623)
  - envelope 書き込み直後・意味検証前の journal 宣言を追加。
  - journal の順序・重複・sha256 を検証。
  - seal 前に selector-runs の宣言集合と実在ファイルを双方向照合。
  - 正常 seal 時に `.lock` を削除。
- [s8b_selector_freeze.py](/home/SFC/tanab/github/izanagi/.claude/worktrees/wave3-unit-a/orchestrator/campaign/s8b_selector_freeze.py:667)
  - strict duplicate-key parse と純構造検証 helper を分離。
  - `_freeze_axes()` のみで cell を導出し、payload SHA 再導出・catalog・descriptor・raw parser を不使用。
  - public verifier の従来検査と受理集合を維持。
- [s8b_ratified_freeze.py](/home/SFC/tanab/github/izanagi/.claude/worktrees/wave3-unit-a/orchestrator/campaign/s8b_ratified_freeze.py:2453)
  - H 錨定の ancestry、V1 basis、sources@pre-oracle、journal↔rows↔envelope 証拠鎖を実装。
  - predictions/journal/raw/envelope の exact exemption を追加。payload は非免除。
  - H mode 100644、H/worktree bytes、宣言 SHA、重複を fail-closed 検証。
- [test_s8b_ratified_verify.py](/home/SFC/tanab/github/izanagi/.claude/worktrees/wave3-unit-a/orchestrator/tests/test_s8b_ratified_verify.py:1330) ほか所有テストへ、production-shaped 正例と指定負例を追加。
- docs・所有外ファイルは未編集。commit も作成していません。

## テスト結果

- 所有テスト5ファイル全走: **289 passed**
- s8b 系全体: **1098 passed / 3 skipped / 11 failed**
  - 11件はすべて、今回未編集の `output/insights/2026-07-22_wave2-protocol-seal.md` が既存 rr20 conjunction hit として検出される同一原因。
  - 内訳: `test_s8b_oracle_driver.py` 10件、`test_s8b_repo_scan_invariant.py` 1件。
  - xfail 化・期待値緩和はしていません。
- `check_codex_agents.py`: 成功
- `check_docs.py`: 成功
- `git diff --check`: 成功

## 波及自己申告

- 単位 B の [s8b_floor_campaign.py](/home/SFC/tanab/github/izanagi/.claude/worktrees/wave3-unit-a/orchestrator/campaign/s8b_floor_campaign.py:1299) と対応テストは、有界 allowlist 構築時に新しい envelope 宣言 record を消費する追随が必要です。
- `claude-headless` の既存 journal を外部で手組みしている consumer があれば、resolved cell に `envelope` record が必要になります。
- public 関数シグネチャの変更はありません。

## 未解決点

- 上記 s8b 全走11件の既存 repository-scan hit。
- 実 seal、FROZEN_MANIFEST pin、完全 E2E、初回導入捏造の完全閉鎖・oracle lineage は親裁定どおり後続範囲です。

# §7 実装報告 — 単位 B (codex、段 5)

## 変更点

- [s8b_floor_campaign.py:1273](/home/SFC/tanab/github/izanagi/.claude/worktrees/wave3-unit-b/orchestrator/campaign/s8b_floor_campaign.py:1273)
  - 必須4ファイルを fail-closed 化。
  - 単位Aの宣言照合 helper を再利用し、claim/raw/envelope 宣言から allowlist を導出。
  - `selector-runs/` の余剰・欠落・hash不一致を双方向 exact で拒否。
  - prediction/journal を duplicate-key 拒否で parse。
- [s8b_floor_campaign.py:1441](/home/SFC/tanab/github/izanagi/.claude/worktrees/wave3-unit-b/orchestrator/campaign/s8b_floor_campaign.py:1441)
  - allowlist path の絶対・dot component・二重slash・制御文字・非UTF-8等を拒否。
- [s8b_floor_campaign.py:1544](/home/SFC/tanab/github/izanagi/.claude/worktrees/wave3-unit-b/orchestrator/campaign/s8b_floor_campaign.py:1544)
  - `clean_scan_digest` を canonical JSON v2 preimageへ変更。path→sha256を束縛。
- [s8b_launch_cert.py:129](/home/SFC/tanab/github/izanagi/.claude/worktrees/wave3-unit-b/orchestrator/campaign/s8b_launch_cert.py:129)
  - identity APIを維持したまま `validate_launch_certificate_strict` を追加。
- [s8b_floor_campaign.py:1639](/home/SFC/tanab/github/izanagi/.claude/worktrees/wave3-unit-b/orchestrator/campaign/s8b_floor_campaign.py:1639)
  - 発行前scanを独立2回実行し、2回目をstrict expectedとして発行直後まで引き回し。resumeは従来のidentity検証のまま。
- [test_s8b_floor_campaign.py:2361](/home/SFC/tanab/github/izanagi/.claude/worktrees/wave3-unit-b/orchestrator/tests/test_s8b_floor_campaign.py:2361)、[test_s8b_launch_cert.py:50](/home/SFC/tanab/github/izanagi/.claude/worktrees/wave3-unit-b/orchestrator/tests/test_s8b_launch_cert.py:50)
  - hash入替え対、余剰ファイル、phantom、protocol不在、duplicate key、scan回数、strict再検証を追加。

既存期待値の変更理由は、digest期待値をv2 preimageへ移したこと、任意名freeze/無宣言selector artifactを許していたfixtureをC05の固定4ファイル＋journal宣言集合へ移したことだけです。

## テスト結果

実走範囲:

```text
python3 -m pytest -q \
  orchestrator/tests/test_s8b_floor_campaign.py \
  orchestrator/tests/test_s8b_launch_cert.py
```

結果: **212 passed / 2 skipped / 0 failed**。skipは既存の環境依存slow real-build canaryです。

加えて以下も緑です。

```text
python3 tools/check_codex_agents.py
python3 tools/check_docs.py
git diff --check
```

想定外の赤・xfail化はありません。

## 波及自己申告

所有外への編集はありません。変更ファイルは指定された4件のみです。

波及可能性として、旧「filename集合のみ」のdigest値を外部で固定しているconsumerがあれば値が変わります。リポジトリ検索上、所有外に直接再計算するconsumerはなく、resume/ratifiedのidentity callerも未変更です。全走確認は親工程に残します。

## 未解決点

単位Bのコード機構は完了していますが、D79(7)全体のblocking前提完了ではありません。実artifact pin、protocol→seal→commit→floor E2E、durable preimageとresume/ratifiedの歴史的lineage照合は後続waveの残余です。既知のcontent TOCTOUも従来どおり残ります。

docs更新・git commitは行っていません。

# §8 敵対レビュー A — 正しさ境界 (codex、段 6)

## 所見

| ID | 重大度 | file:line | 主張 | 根拠 |
|---|---|---|---|---|
| R1 | **must-fix** | [s8b_floor_campaign.py:1491](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/campaign/s8b_floor_campaign.py:1491), [同:1559](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/campaign/s8b_floor_campaign.py:1559), [test:2331](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/tests/test_s8b_floor_campaign.py:2331) | C05/P1/P4 の「cert lane の prefix 盲点を閉じる」は未達。`_assert_freeze_allowlist()` は固定4ファイルと `selector-runs/` しか列挙せず、その他の `output/s8b-freeze/` を無条件に無視する。 | `search_repository(..., exempt_exact=None)` も同 prefix を除外するため、`output/s8b-freeze/unlisted.json` や symlink、`approvals/` 内のファイルは scan も content hash もされない。旧 top-level `unlisted.json` 負例は `selector-runs/undeclared.json` へ書き換えられ、[chain-dir テスト:2426](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/tests/test_s8b_floor_campaign.py:2426) は「chain validator に委譲」と称しているが、その validator を一度も呼んでいない。<br>**放置すると:** 同名 `unlisted.json` の bytes を三軸 conjunction に変更しても `clean_scan_digest` は不変のまま certificate が発行され、certified clean として受理される repo 状態が拡大する。 |
| R2 | **must-fix** | [s8b_ratified_freeze.py:2587](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/campaign/s8b_ratified_freeze.py:2587), [同:2601](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/campaign/s8b_ratified_freeze.py:2601), [fixture:517](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/tests/test_s8b_ratified_freeze.py:517) | C01/C03/P2 の H 錨定 binding 再構成が部分的に恒真。`protocol_sha256`、`provider_kind`、`parser_module_sha256` を journal header 自身から `JournalBinding` の expected に戻している。 | `resolve_journal()` の header equality は自己比較になる。その後に独立照合するのは pre-oracle head、freeze、role の3項だけ。正例 fixture 自身が protocol/parser に架空 bytes の hash を入れて通している。protocol は `pre_oracle_head:output/s8b-freeze/floor_protocol.json`、parser は固定 parser path の H blob、provider は production 定数から導出可能である。<br>**放置すると:** 別 protocol/parser/provider を名乗る journal が raw/envelope とともに exact exemption を得て、誤った `run_header.protocol_sha256` 等を持つ proof-chain 参照が `launch_validate` に受理される。 |
| R3 | should-fix | [test_s8b_ratified_verify.py:1438](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/tests/test_s8b_ratified_verify.py:1438), [s8b_ratified_freeze.py:2558](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/campaign/s8b_ratified_freeze.py:2558) | M9 の現行負例は受理集合 mutation を kill しない。 | 非 ancestor commit を空 tree で作っている。ancestry assert を削除しても、直後の `pre_oracle_head:path` source 不在で拒否され続ける。cause の差でテストは赤くなり得るが、事前登録の「mutant 通過」ではない。必要なのは固定5 source を同じ bytes で持つ非 ancestor commit。 |
| R4 | should-fix | [s8b_floor_campaign.py:2789](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/campaign/s8b_floor_campaign.py:2789), [同:2819](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/campaign/s8b_floor_campaign.py:2819), [campaign_claim.py:64](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/campaign/campaign_claim.py:64) | M7 の「2回目 scan 差異を副作用前拒否」は統合経路では成立しない。 | release API のない one-shot claim を先に永続化し、その後で二重 scan を行う。現テストは `_official_launch_preflight()` leaf だけを呼ぶため、この順序を観測しない。`d1 != d2` でも claim artifact が残る。 |
| R5 | nit | [s8b_floor_campaign.py:1453](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/campaign/s8b_floor_campaign.py:1453) | C09 の「制御文字拒否」は C0＋DEL のみ。 | U+0080〜U+009F は UTF-8 encode でき、現在の `ord < 32 or == 127` を通る。公式 builder の固定名からは通常到達しないが、validator 契約の逐語とは不一致。 |

## 5d2be97 の名指し検査

5d2be97 自体には所見なし。

- `ycsb_rratio=«20»` 等は、regex が要求する `=<v>` の隣接を確実に壊している。
- 編集後の台帳全体に rr20/rr80 の各 canonical encoding は残っておらず、file-level conjunction も残存しない。
- erratum は日付、変更理由、元逐語を保持する commit `441babc` を明記しており、逐語台帳への例外編集記録として十分。参照 commit に元の三軸文字列が実在することも確認した。

## M1〜M10

| 変異 | 実コード錨 | 静的判定 |
|---|---|---|
| M1 | [selector map 合流:3047](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/campaign/s8b_ratified_freeze.py:3047) | killable |
| M2 | [exact 宣言 map:2453](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/campaign/s8b_ratified_freeze.py:2453) | killable |
| M3 | [raw 宣言 SHA:2658](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/campaign/s8b_ratified_freeze.py:2658) | helper leaf では killable |
| M4 | [predictions 不在分岐:2455](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/campaign/s8b_ratified_freeze.py:2455) | killable。ただし現テストは launch fixture ではない |
| M5 | [digest allowlist 列:1569](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/campaign/s8b_floor_campaign.py:1569) | killable |
| M6 | [strict equality:140](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/campaign/s8b_launch_cert.py:140) | killable |
| M7 | [第2 scan:1654](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/campaign/s8b_floor_campaign.py:1654) | call-count/digest mutation は killable。副作用前という帰属は R4 で不成立 |
| M8 | [journal↔row 比較:2644](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/campaign/s8b_ratified_freeze.py:2644) | helper leaf では killable |
| M9 | [ancestry:2543](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/campaign/s8b_ratified_freeze.py:2543) | **事前登録どおりには killable でない**。R3 |
| M10 | [envelope 宣言 SHA:2673](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/campaign/s8b_ratified_freeze.py:2673) | helper leaf では killable |

cert の identity/strict 分離、2回目 scan 値の strict expected 使用、発行済み cert の自己申告値非使用、payload 非免除、predictions 不在時の空集合、selector evidence の 100644 制約、cert raw hit の parse 前拒否は実装どおり。通常の launch 経路で namespace-dirty/history-mutated が scan より先行する順序も維持されている。ただし R1 により cert preflight 経路の三軸 conjunction 拒否は全経路不変ではない。

## 総合判定

**NO-GO**

R1 は固定4ファイル化に伴う失われた負例 coverage が実際の受理穴を隠しており、R2 は H 錨定証拠鎖の binding を恒真化している。少なくともこの2件の修正と、M9 fixture の単一理由化が必要。pytest・変異実測は指示どおり実行していない。

# §9 敵対レビュー B — 整合・実効性 (codex、段 6)

静的レビューでは、受理集合を壊す must-fix が3件あります。特に certificate lane の prefix 盲点は、既存の負例テストを書き換えて見えなくしており、統合不可です。

## 所見

| ID | 重要度 | file:line | 主張 | 根拠 |
|---|---|---|---|---|
| I-01 | **must-fix** | [s8b_floor_campaign.py:1468](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/campaign/s8b_floor_campaign.py:1468)、[同:1491](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/campaign/s8b_floor_campaign.py:1491)、[同:1558](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/campaign/s8b_floor_campaign.py:1558)、[s8b_holdout_freeze.py:312](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/campaign/s8b_holdout_freeze.py:312) | B の「有界 allowlist」は `output/s8b-freeze/` 全体を有界化していない。固定4ファイルと `selector-runs/` 以外の任意ファイルが scan・allowlist 双方から漏れる。 | `_assert_freeze_allowlist()` の `actual` は固定4ファイルと `selector-runs/**` だけ。対して `clean_scan_digest()` は `exempt_exact=None` の scan を使うため、`output/s8b-freeze/` prefix 全体が除外される。さらに既存の top-level 負例は、[test_s8b_floor_campaign.py:2331](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/tests/test_s8b_floor_campaign.py:2331) で `unlisted.json` から `selector-runs/undeclared.json` へ書き換えられ、回帰が隠された。P1 の「cert lane の盲点は C05 で閉じる」、D79 (5)、§5-(ix)-9 に反する。<br>**放置影響:** 同じ path の `output/s8b-freeze/prior_measurement.txt` を三軸 hit 有無の異なる bytes に交換しても `repository_files` と allowlist が同じため `clean_scan_digest` は同値になり、汚染 repo まで official preflight の受理集合へ入る。 |
| I-02 | **must-fix** | [s8b_ratified_freeze.py:2530](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/campaign/s8b_ratified_freeze.py:2530)、[s8b_selector_freeze.py:341](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/campaign/s8b_selector_freeze.py:341)、[同:637](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/campaign/s8b_selector_freeze.py:637)、[同:681](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/campaign/s8b_selector_freeze.py:681) | P2 差替えの「H 錨定・drift-free」は未達。H の V1 bytesを渡していても、検証意味論は現在 checkout の `CHOICE_TO_BINDING` と `STATIC_DEFAULT_CHOICE_ID` に依存する。 | `_validate_prediction_document()` は現在の `selector_basis_sha256()`、choice mapping、static defaultで過去文書を再検証する。pre-oracle source blob の hash を確認しても、その blob の意味論は使っていない。[drift test:501](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/tests/test_s8b_selector_freeze.py:501) は jobs/descriptor/parser と role bytesしか変えず、mapping/default drift を検査していない。F-01 の「現在意味論への非依存」に反する。<br>**放置影響:** 正当な seal 後に mapping/default が更新されると、旧 H に対する正当 prediction が `selector_basis_sha256` 不一致等で拒否され、`launch_validate` の受理集合が縮小する。その結果 oracle marker/WAL/判定成果物が生成されない。 |
| I-03 | **must-fix** | [s8b_ratified_freeze.py:2587](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/campaign/s8b_ratified_freeze.py:2587)、[同:2601](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/campaign/s8b_ratified_freeze.py:2601)、[fixture:515](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/tests/test_s8b_ratified_freeze.py:515) | C03 の run_header binding 再構成が恒真比較になっている。protocol/provider/parser/executable の期待値を header 自身からコピーして `resolve_journal()` に渡している。 | 独立照合されるのは後段の `pre_oracle_head`、freeze sha、role shaだけ。protocol shaを `pre_oracle_head:floor_protocol.json`、parser shaを固定 parser blob、providerを production定数へ結び付けていない。fixture は [protocol/parser に合成 hash:517](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/tests/test_s8b_ratified_freeze.py:517) を入れたまま、`production_valid` 正例では実 `drive_journal()` を通して受理される。C02 の初回捏造残余とは別に、C03 で採用した表面縮小が機能していない。<br>**放置影響:** 任意 protocol/parser/provider を自己申告した journal でも raw/envelope が exact exemption を得るため、production seal 由来でない証拠が `launch_validate` の受理集合へ入り、汚染 namespace から oracle 成果物を生成できる。 |
| I-04 | **should-fix** | [wave2台帳:6](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/output/insights/2026-07-22_wave2-protocol-seal.md:6)、[同:642](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/output/insights/2026-07-22_wave2-protocol-seal.md:642)、[decisions.md:3221](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/docs/decisions.md:3221)、[worklog.md:190](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/docs/worklog.md:190) | 5d2be97 の defang は履歴復元可能だが、凍結・逐語台帳としての形式が不整合。 | `441babc` に原文が残り、現行行にも erratum はある。しかし文書冒頭・D79・worklog は依然として現 HEAD のファイルを無条件に「逐語台帳」と参照する。先例の consultation 台帳のような文書レベルの編集例外がない。D80/worklog の追記で「642行のみ安全化、原文は441babc」を正本参照へ反映すべきで、過去行の再編集で直すべきではない。 |
| I-05 | **should-fix** | [source blob check:2549](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/campaign/s8b_ratified_freeze.py:2549)、[test_s8b_ratified_verify.py:705](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/tests/test_s8b_ratified_verify.py:705) | selector `sources@pre_oracle_head` の blob/hash 不一致を直接固定する負例がない。 | 現存の `test_source_blob_mismatch_rejected` は ratified generation source 用で、selector prediction の5 source loopを通らない。C01/P2の主要防壁なので専用負例が必要。加えて I-02 の mapping/default drift 負例、I-03 の protocol/parser/provider 独立束縛負例が不足している。 |

## 裁定項対応表

| 裁定項 | 判定 | 実装状況 |
|---|---|---|
| C01 | **部分** | ancestry、sources blob hash、journal/rows/envelope照合は存在。ただし現在 mapping 依存と run_header 独立束縛不足で H 錨定は未完成。 |
| C03 | **部分** | strict JSONL、run_header 1件、`resolve_journal`、cell/status/raw対応は実装。binding の一部が header 自己申告で恒真。 |
| C04 | **実装済み** | [envelope書込み直後:1028](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/campaign/s8b_prediction_runner.py:1028) に journal recordを追加し、宣言 envelopeだけを免除。 |
| C05 | **部分** | 固定4＋`selector-runs/**` は双方向 exact。その他の `output/s8b-freeze/**` が prefix盲点に残る。 |
| C06 前半 | **実装済み** | 発行時 strict照合、2回独立scan、発行bytes再検証あり。durable preimage/resume照合は裁定どおり外。 |
| C08 | **実装済み** | prediction・journal・preflightで duplicate-key拒否 parserを使用。 |
| C09 | **実装済み** | versioned canonical JSON preimageとallowlist path検査を実装。 |
| C10 | **実装済み** | selector免除対象のH modeを `100644` 固定。 |
| F-01 | **部分** | jobs/catalog/descriptor/raw parserの再呼出しは排除したが、現在の choice mapping/default に依存。 |
| F-03 | **部分** | selector-runs内の余剰・phantomは拒否。cert lane全体の未宣言ファイル拒否にはなっていない。 |
| F-04 | **実装済み** | `validate_launch_certificate` はidentity APIのまま、新規strict APIだけがclean digestを要求。既存callerへの破壊なし。 |
| F-05 | **実装済み** | fake subprocess envelopeを使い、実 `ClaudeHeadlessProvider`＋`drive_journal()` でclaim/envelope/invocation/provenanceを生成。ただし full `seal()`／protocol E2Eではない。 |
| F-06 | **実装済み** | hash入替え対、余剰entry、構築後削除、protocol不在、scan 2回を追加。なお top-level余剰負例の削除は別途 I-01。 |
| F-09 | **実装済み** | 正常sealで `.lock` を削除し、その後 declaration exact検査。残留lockは未宣言ファイルとして拒否。 |
| P2 差替え | **部分** | H bytes、ancestry、source blobs、journal/envelopeは実装したが、drift-free意味論とrun_header独立束縛が欠落。 |
| P6 反転 | **実装済み** | payloadは免除mapに入らず通常scan対象。conjunction非存在のcharacterizationとtampered-hit拒否もある。 |

## Production seal 集合との突き合わせ

| Artifact | 実生成・宣言 | launch / preflight |
|---|---|---|
| `selector_predictions.json` | seal終盤で生成 | H/worktree exact hash免除、固定allowlist |
| `selector-runs/journal.jsonl` | run_header＋claim/envelope/invocation | H/worktree exact hash免除、固定allowlist |
| `payload_*.json` | claim前に4 agent cell分生成 | **免除なし**、通常scan。preflightではclaim hashに束縛 |
| `raw_*.txt` | provider応答取得後に生成 | invocation path/hashがあるものだけ免除・allowlist |
| `envelope_*.json` | semantic検証より前に生成 | 即時envelope recordのpath/hashがあるものだけ免除・allowlist |
| `.lock` | advisory運転用 | 正常sealで削除。残ればselector-runs exact検査で拒否 |

したがって、**同一実装revisionで正常終了した実seal**なら、三軸 rationaleを含むraw/envelopeは宣言免除され、payloadはcharacterization上hitせず、`.lock` も消えるため、構造上は `launch_validate` を通せます。

しかし「production seal由来であることを持続的・独立に証明したうえで通る」という blocking 前提は成立していません。I-02では後続source driftで正例が落ち、I-03ではproductionでない自己整合bundleが通ります。

Seal側の `selector-runs/` 未宣言ファイル検出と `.lock` 削除自体は実効的です。破れているのはB側のそれ以外のfreeze namespaceです。

## 波及・テスト計画

- Aの自己申告どおり、BはAのjournal declaration helperへ追随しています。手組みjournal consumerで新envelope recordに未追随のproduction callerは見つかりませんでした。
- `s8b_oracle_driver`、tools、hooksには新しい直接consumerはありません。
- Bの旧 `clean_scan_digest` 値を外部で固定するconsumerも見つかりません。identity API維持によりresume/ratified callerも壊していません。
- v2のM8/M9/M10相当であるjournal mismatch、ancestry、envelope hash負例は追加済みです。
- 最大のテスト差は、既存top-level余剰ファイル負例をselector-runs内の負例へ置換したことです。これは不足ではなく回帰の隠蔽です。
- F-05正例は `drive_journal()` 実走であり単なる手組みではありません。ただし protocol blobもfull `seal()` も使わず、fixture自身が「production seal由来ではない」と明記しています。統合E2E完了の証拠にはできません。
- pytest・変異実測は指示どおり行っていません。

## 既裁定・完了報告

- §5-(ix)-9: Aの免除はexact path＋H/worktree bytes hashで整合。Bのprefix盲点は不整合。
- D79 (5): selector-runs内では強化されたが、freeze namespace全体では後退。
- D79 (7): 実pin、完全同型E2E、lineage照合は未完。[FROZEN_MANIFEST](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/tests/test_frozen_artifacts.py:33) も8件のまま。
- R3 missing意味論との衝突は見つかりません。
- [T-083] G2: 本waveが実受理集合を扱うこと自体は整合。ただしI-01/I-03の意図しない拡大はG2の正当化対象ではありません。
- 3コミットのmessageには「D79 (7) 4件すべて完了」という明示的主張はありません。ただしBの「allowlistの有界化」とAの「証拠鎖」は各々I-01/I-03により過大です。
- 現handoffの「blocking前提2件を消化する」という文言を最終報告へ残すのはF-07違反です。許される上限は、裁定どおり **「D79 (7) 4件中、protocol非依存2件のコード機構完了」** で、実pin・E2E・lineageに加え、本レビューのmust-fix未解消を明記する必要があります。

## 総合判定

**NO-GO**

I-01〜I-03を修正し、削除されたtop-level負例、mapping/default drift負例、run_header独立束縛負例を追加するまで統合不可です。

# §10 fix ブリーフ (親裁定、段 6)

# wave3 fix ラウンド 1 ブリーフ (親裁定 — 統合 83 失敗 + レビュー A 所見。レビュー B 所見は追補節に)

基準 = commit 6c89323。以下をすべて 1 ラウンドで修正する。

## FIXW-1 (統合 83 失敗の根本): emitter fixture へ namespace protocol を導入

- 実運用順序 (protocol commit → seal) を fixture が模倣する: `_prepare_emitter_base` の **seed commit に** `output/s8b-freeze/floor_protocol.json` (emitter の合成 protocol canonical bytes) を含める。predictions の pre_oracle_head = seed なので、seal 時に protocol が既在という実 topology と一致する
- fixture の合成 protocol が S0 (hit-0 自己検査) を満たすこと (三軸 conjunction を含まない) をテストで assert
- official preflight の protocol_sha256 照合 (s8b_floor_campaign.py L1312) と整合させる (run protocol と同一 bytes)
- 83 失敗 (ratified_verify 69 / oracle_driver 11 / ratified_freeze 3、全件同一理由) が全快することを確認

## FIXW-2 (レビュー A R2, must): journal binding 恒真の解消

- binding 再構成のうち `protocol_sha256` は `pre_oracle_head:output/s8b-freeze/floor_protocol.json` の git blob sha256 へ、`parser_module_sha256` は固定 parser module path の `pre_oracle_head:path` blob sha256 へ独立錨定する (worktree 非依存・歴史 blob = drift-free)
- `provider_kind` は独立検証源が無いため「journal 内部記録であり免除判定の load-bearing でない」ことを docstring に明記する (または predictions 側宣言と照合できるなら照合)。header 由来値の self-echo を expected に使う恒真は全 field で排除する
- FIXW-1 により fixture でも protocol blob が pre_oracle_head に実在するため錨定可能

## FIXW-3 (レビュー A R1, must): cert lane の namespace 全被覆

- official preflight は `output/s8b-freeze/` 配下の**全実在ファイル**を次の 3 集合で被覆し、どれにも属さないファイルは fail-closed 拒否する: (i) 固定 4 ファイル (bytes を digest preimage に束縛済み)、(ii) journal 宣言由来の selector-runs 集合 (同)、(iii) chain record (approvals/ revocations/ active/ active-cancellations/ と世代 file — 既存命名規則で識別し、path+bytes を preimage に含める)
- 失われた負例 coverage を復元: namespace 直下の未知ファイル (例: unlisted.json) が拒否されるテストを再追加。「chain validator へ委譲」と称して何も呼ばないテスト (test_s8b_floor_campaign.py L2426 付近) は実検査に置換
- symlink は全集合で拒否

## FIXW-4 (レビュー A R5, nit だが同時に): 制御文字拒否を C1 領域へ拡張 (ord < 32 or 127 <= ord <= 159)

## FIXW-5 (変異事前登録の訂正 — テスト側)

- M9 fixture: 非 ancestor commit に固定 5 sources を同一 bytes で持たせ、ancestry 検査だけが拒否理由になるよう単一理由化 (レビュー A R3)
- M7 の kill 基準を「digest 不一致の拒否 + certificate 不発行」へ改定 (claim の先行永続は at-most-once 設計どおりで副作用ゼロは主張しない — レビュー A R4)。必要ならテストの assert を「cert 不発行」に絞る

## 不変条件 (変わらず)

- 規律 2 の優先順 (cert raw hit / namespace-dirty / history-mutated / scan) 不変。identity API シグネチャ不変。resume/ratified caller 不変。既存受理集合の変更は本ブリーフ記載分のみ
- 単位 A/B の成果物の他の部分を壊さない。所有: fix 単位は A+B の全 12 ファイルを所有してよい (単一 fix 単位、直列)

## レビュー B 所見の追補 (親裁定済み)

- I-01 = FIXW-3 と同根 (同一修正で閉じる)。I-03 = FIXW-2 と同根
- **FIXW-6 (I-02, must): launch 側検証から現在意味定数への依存を除去** — launch 用の検証射影は「strict parse + top-level exact keys + body_sha256 + row tagged-union の null/非 null 形状規則 + cell 集合 (freeze 軸のみ) + raw/envelope 宣言の path/schema」に限定し、`selector_basis_sha256` 再導出・`CHOICE_TO_BINDING`・`STATIC_DEFAULT_CHOICE_ID`・swapped expectations 再導出を**呼ばない** (これらは body_sha256 が文書内束縛し、意味検証は seal 時の full verifier が担う)。official preflight の full verify は既存挙動 (D79 (5)) のまま変えない。ドリフト非依存を固定するテスト: 意味定数を test 内で差し替えても launch 免除の受理が不変であること
- **FIXW-7 (I-05, should): 負例 3 種を追加** — (i) selector sources の 5-source loop に対する blob/hash 不一致負例、(ii) FIXW-6 の意味定数差替えでの受理不変 (正例)、(iii) FIXW-2 の protocol/parser 独立束縛の負例 (誤 protocol sha を自称する journal の拒否)
- I-04 (should) は fix 単位の対象外 — 段 7 で親が D80/worklog に「台帳 642 行のみ defang・原文 = 441babc」を正本参照として記す (過去行の再編集はしない)
- 報告言語 (F-07 再確認): 最終報告の上限は「D79 (7) 4 件中 protocol 非依存 2 件のコード機構完了 (レビュー must-fix 解消込み)」。実 pin・E2E・lineage は残余として列挙


# §11 fix1 実装報告 (codex)

実装完了しました。FIXW-1〜FIXW-7 はすべて対応済みです。docs 編集・git commit・所有外ファイル編集はありません。

## FIXW 対応状況

- FIXW-1 実装済み  
  emitter seed に canonical protocol bytes と parser blob を追加し、S0 hit-0 を assertion。journal も実 blob hash に統一しました。  
  [test_s8b_ratified_freeze.py:422](/home/SFC/tanab/github/izanagi/.claude/worktrees/wave3-fix1/orchestrator/tests/test_s8b_ratified_freeze.py:422)  
  [test_s8b_ratified_freeze.py:525](/home/SFC/tanab/github/izanagi/.claude/worktrees/wave3-fix1/orchestrator/tests/test_s8b_ratified_freeze.py:525)

- FIXW-2 実装済み  
  protocol/parser を `pre_oracle_head:path` の100644 blobへ独立束縛。provider/executable provenance は免除判定で load-bearing でないことを明記しました。  
  [s8b_prediction_runner.py:556](/home/SFC/tanab/github/izanagi/.claude/worktrees/wave3-fix1/orchestrator/campaign/s8b_prediction_runner.py:556)  
  [s8b_ratified_freeze.py:2580](/home/SFC/tanab/github/izanagi/.claude/worktrees/wave3-fix1/orchestrator/campaign/s8b_ratified_freeze.py:2580)  
  [s8b_floor_campaign.py:1282](/home/SFC/tanab/github/izanagi/.claude/worktrees/wave3-fix1/orchestrator/campaign/s8b_floor_campaign.py:1282)

- FIXW-3 実装済み  
  freeze namespace 全ファイルを固定4件・journal由来 selector-runs・正規chain recordで被覆。未知ファイルと全symlinkを拒否し、chain path/hashをdigest v3へ束縛しました。失われていた直下 `unlisted.json` 負例も復元済みです。  
  [s8b_floor_campaign.py:1533](/home/SFC/tanab/github/izanagi/.claude/worktrees/wave3-fix1/orchestrator/campaign/s8b_floor_campaign.py:1533)  
  [test_s8b_floor_campaign.py:2332](/home/SFC/tanab/github/izanagi/.claude/worktrees/wave3-fix1/orchestrator/tests/test_s8b_floor_campaign.py:2332)  
  [test_s8b_floor_campaign.py:2428](/home/SFC/tanab/github/izanagi/.claude/worktrees/wave3-fix1/orchestrator/tests/test_s8b_floor_campaign.py:2428)

- FIXW-4 実装済み  
  制御文字拒否を C0＋DEL から C1全域（127〜159）へ拡張しました。  
  [s8b_launch_cert.py:154](/home/SFC/tanab/github/izanagi/.claude/worktrees/wave3-fix1/orchestrator/campaign/s8b_launch_cert.py:154)  
  [s8b_ratified_freeze.py:877](/home/SFC/tanab/github/izanagi/.claude/worktrees/wave3-fix1/orchestrator/campaign/s8b_ratified_freeze.py:877)  
  [s8b_floor_campaign.py:1521](/home/SFC/tanab/github/izanagi/.claude/worktrees/wave3-fix1/orchestrator/campaign/s8b_floor_campaign.py:1521)

- FIXW-5 実装済み  
  M9 は固定source/protocol/parserを同一treeに持つ非ancestor commitへ単一理由化。M7 はclaim残存を認め、digest不一致拒否＋certificate不発行を検査します。  
  [test_s8b_ratified_verify.py:1487](/home/SFC/tanab/github/izanagi/.claude/worktrees/wave3-fix1/orchestrator/tests/test_s8b_ratified_verify.py:1487)  
  [test_s8b_floor_campaign.py:3167](/home/SFC/tanab/github/izanagi/.claude/worktrees/wave3-fix1/orchestrator/tests/test_s8b_floor_campaign.py:3167)

- FIXW-6 実装済み  
  launch専用射影を分離し、current `selector_basis_sha256`、`CHOICE_TO_BINDING`、`STATIC_DEFAULT_CHOICE_ID`、swapped再導出への依存を除去。official preflight のfull意味検証は維持しました。  
  [s8b_selector_freeze.py:706](/home/SFC/tanab/github/izanagi/.claude/worktrees/wave3-fix1/orchestrator/campaign/s8b_selector_freeze.py:706)  
  [test_s8b_ratified_verify.py:1465](/home/SFC/tanab/github/izanagi/.claude/worktrees/wave3-fix1/orchestrator/tests/test_s8b_ratified_verify.py:1465)

- FIXW-7 実装済み  
  selector source blob/hash不一致、誤protocol自己申告、意味定数drift受理不変の3種を追加しました。  
  [test_s8b_ratified_verify.py:1435](/home/SFC/tanab/github/izanagi/.claude/worktrees/wave3-fix1/orchestrator/tests/test_s8b_ratified_verify.py:1435)  
  [test_s8b_ratified_verify.py:1451](/home/SFC/tanab/github/izanagi/.claude/worktrees/wave3-fix1/orchestrator/tests/test_s8b_ratified_verify.py:1451)

## テスト結果

- 所有12ファイル中、テスト7ファイル全走: `509 passed, 2 skipped`
- 所有外 `test_s8b_oracle_driver.py`: `80 passed, 1 skipped`
- 最終指定横断範囲  
  `python3 -m pytest -q orchestrator/tests -k 's8b or hooks or frozen'`  
  `1189 passed, 4 skipped, 1636 deselected, 0 failed`
- 最終helper分離後の関連再確認: `29 passed`
- `check_codex_agents.py`: OK
- `check_docs.py`: 違反なし
- `git diff --check`: OK

旧83失敗の共通原因 `floor_protocol.json` 不在は解消し、対象群は最終横断全走で失敗0です。想定外の赤、追加xfail、sandbox由来の偽赤はありません。

## 波及自己申告

変更は所有範囲内の9ファイルのみです。所有外コードへの直接変更はありません。

波及可能性として、clean scan digest preimage はv3になり、未知freeze namespace fileと不正chain名は新たにfail-closedになります。また、pre-oracle treeにprotocol/parser blobがない旧selector bundleは拒否されます。いずれもブリーフどおりの意図的な受理集合縮小です。`s8b_oracle_driver` は編集なしで全緑でした。

## 未解決点

本fix内の未解決点はありません。完了主張の上限は「D79 (7) 4件中、protocol非依存2件のコード機構完了（レビューmust-fix解消込み）」です。実pin・完全同型E2E・lineage照合は後続残余です。

# §12 焦点再レビュー (codex、closed/partial/regressed 対応表)

## 対応表

| 所見 ID | 判定 | 根拠 | 残余 |
|---|---|---|---|
| R1 | closed | namespace 全体を再帰列挙し、固定4件・selector-runs・chain record の三集合外を拒否。chain は path+hash を digest v3 に統合している。[s8b_floor_campaign.py:1533](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/campaign/s8b_floor_campaign.py:1533) [同:1635](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/campaign/s8b_floor_campaign.py:1635) [test:2332](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/tests/test_s8b_floor_campaign.py:2332) | なし |
| R2 | closed | protocol/parser は `pre_oracle_head` の100644 blobから再構成され、header self-echo は消滅。provider/executable は非 load-bearing・schema-only と明記された。[s8b_prediction_runner.py:550](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/campaign/s8b_prediction_runner.py:550) [s8b_ratified_freeze.py:2580](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/campaign/s8b_ratified_freeze.py:2580) [test:1451](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/tests/test_s8b_ratified_verify.py:1451) | 新規のheader schema回帰はN-01として分離 |
| R3 | closed | 元 `pre_oracle_head` と同一treeを持つ非ancestor commitを作り、predictionとjournalのpinも同時修復。ancestry以外のsource/protocol/parser検査は通るfixtureになった。[test_s8b_ratified_verify.py:1487](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/tests/test_s8b_ratified_verify.py:1487) | なし |
| R4 | closed | 統合経路でclaim残存を明示的に認め、2回目digest不一致の拒否とcertificate不発行だけを検査している。[test_s8b_floor_campaign.py:3167](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/tests/test_s8b_floor_campaign.py:3167) | なし |
| R5 | closed | C1全域を `127 <= ord <= 159` で拒否。official path、allowlist、ratified pathへ反映済み。[s8b_launch_cert.py:147](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/campaign/s8b_launch_cert.py:147) [s8b_floor_campaign.py:1510](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/campaign/s8b_floor_campaign.py:1510) [s8b_ratified_freeze.py:870](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/campaign/s8b_ratified_freeze.py:870) | なし |
| I-01 | closed | R1と同じ。直下 `unlisted.json`、不正chain名、namespace内symlinkの専用負例も復元された。[test_s8b_floor_campaign.py:2332](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/tests/test_s8b_floor_campaign.py:2332) [同:2428](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/tests/test_s8b_floor_campaign.py:2428) | なし |
| I-02 | regressed | 現在のbasis/choice/default/swapped再導出は除去され、body hash・row tagged-union・cell集合は残った。[s8b_selector_freeze.py:706](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/campaign/s8b_selector_freeze.py:706) [test:1465](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/tests/test_s8b_ratified_verify.py:1465) | 原所見自体は解消したが、launch journal射影を弱めすぎたN-01/N-02を新規導入 |
| I-03 | closed | R2と同じ。ratified laneとofficial preflightの双方が歴史protocol/parser blobへ独立束縛する。[s8b_floor_campaign.py:1379](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/campaign/s8b_floor_campaign.py:1379) [s8b_ratified_freeze.py:2596](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/campaign/s8b_ratified_freeze.py:2596) | なし |
| I-05 | closed | 5-source blob/hash不一致、誤protocol自己申告、意味定数drift正例の3種が追加され、各fixtureの従属hashだけが修復されている。[test_s8b_ratified_verify.py:1435](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/tests/test_s8b_ratified_verify.py:1435) [同:1451](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/tests/test_s8b_ratified_verify.py:1451) [同:1465](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/tests/test_s8b_ratified_verify.py:1465) | なし |

## 新規所見テーブル

| ID | 重大度 | 根拠 | 所見 |
|---|---|---|---|
| N-01 | must-fix | [s8b_prediction_runner.py:338](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/campaign/s8b_prediction_runner.py:338) [同:550](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/campaign/s8b_prediction_runner.py:550) [s8b_floor_campaign.py:1394](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/campaign/s8b_floor_campaign.py:1394) | `_validate_header_schema()` はkey集合を検査するが、`schema == JOURNAL_SCHEMA_VERSION` を検査しない。launch側の独立expected 5項にもschemaは含まれないため、任意のjournal schema値がratified lane・official preflight双方を通る。<br>**成果物影響:** 未対応schemaのjournalに対してlaunch certificateを発行でき、後段では `LaunchValidatedFreeze` としてoracle campaignへ進める。 |
| N-02 | must-fix | [s8b_prediction_runner.py:598](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/campaign/s8b_prediction_runner.py:598) [同:628](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/campaign/s8b_prediction_runner.py:628) [s8b_ratified_freeze.py:2639](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/campaign/s8b_ratified_freeze.py:2639) | claimの`decision_method`とstaticの`decision_method/choice_id`を非空文字列まで弱めた一方、ratified側はそれらをprediction rowの封印値と比較していない。journalだけを別の非空値へ変更しても受理される。現在定数ではなく、journal↔rowの直接等値でdrift-freeに維持できる検査である。<br>**成果物影響:** 相互矛盾するselector proof chainがlaunch検証済みとなり、残りのgateを満たせばoracle marker/WALを生成できる。 |

受理集合について、digest v3、未知ファイル拒否、正規chain recordのpath+bytes束縛、pre-oracle protocol/parser blob要求そのものはブリーフどおりです。これら四点に意図外の縮小・拡大は見つかりません。意図外の拡大はN-01/N-02です。

FIXW-1も適切です。合成protocolはseed前にcanonical bytesとして配置され、fixture docstringは引き続き「production seal由来ではない」と明記しています。[test_s8b_ratified_freeze.py:454](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/tests/test_s8b_ratified_freeze.py:454) [同:490](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/tests/test_s8b_ratified_freeze.py:490)。S0 assertも実protocol bytesを実際の三軸scannerへ渡して結果を検査しており、恒真ではありません。

新規・変更テストに過剰決定は見つかりません。M9、M7、namespace、source hash、protocol binding、drift正例はいずれも従属値を修復して対象理由を分離しています。ただしN-01/N-02の負例は未追加です。

## 総合判定

**NO-GO**

前回must/shouldの大半は解消していますが、FIXW-6がjournal構造・journal↔row対応を6c89323より弱め、二つの新規must-fixを導入しています。schema versionの固定と、claim/static値のjournal↔row直接照合を戻し、それぞれ単一理由負例を追加する必要があります。

# §13 fix2 実装報告 (codex)

実装完了しました。docs 編集・commit は行っていません。

### N-01

- [s8b_prediction_runner.py:338](/home/SFC/tanab/github/izanagi/.claude/worktrees/wave3-fix2/orchestrator/campaign/s8b_prediction_runner.py:338)
  - header の `schema` を `JOURNAL_SCHEMA_VERSION` と厳密一致で検査。
  - shared `resolve_journal_for_launch()` 経由で ratified lane と official preflight の双方を被覆。
- [test_s8b_ratified_verify.py:1465](/home/SFC/tanab/github/izanagi/.claude/worktrees/wave3-fix2/orchestrator/tests/test_s8b_ratified_verify.py:1465)
  - schema 値だけを別の非空文字列にした負例を追加。
  - `cause == "selector-declaration-invalid"` を確認。

### N-02

- [s8b_prediction_runner.py:558](/home/SFC/tanab/github/izanagi/.claude/worktrees/wave3-fix2/orchestrator/campaign/s8b_prediction_runner.py:558)
  - 封印 prediction row 対応表を shared resolver に渡し、journal と直接等値照合。
  - claim: `decision_method`
  - static: `decision_method`、`choice_id`
- [s8b_ratified_freeze.py:2611](/home/SFC/tanab/github/izanagi/.claude/worktrees/wave3-fix2/orchestrator/campaign/s8b_ratified_freeze.py:2611)、[s8b_floor_campaign.py:1394](/home/SFC/tanab/github/izanagi/.claude/worktrees/wave3-fix2/orchestrator/campaign/s8b_floor_campaign.py:1394)
  - ratified lane と official preflight の両方を同じ直接照合へ接続。
  - official 側の現在定数との重複比較を除去し、歴史 blob 同士の drift-free 照合に統一。
- [test_s8b_ratified_verify.py:1483](/home/SFC/tanab/github/izanagi/.claude/worktrees/wave3-fix2/orchestrator/tests/test_s8b_ratified_verify.py:1483)
  - claim decision method、static decision method、static choice ID の単一理由負例を追加。

### テスト結果

- 所有テスト3ファイル: `410 passed, 2 skipped`
- 指定横断 `-k "s8b or hooks or frozen" orchestrator/tests`:
  `1193 passed, 4 skipped, 1636 deselected`
- 新規負例 focused: `4 passed`
- `check_codex_agents.py`、`check_docs.py`、`py_compile`、`git diff --check`: 全て成功
- xfail/skip の追加なし。submodule `index.lock` 偽赤も発生なし。

最初の素の `pytest` は PATH 上の Python 3.9 で既存 `dataclass(kw_only=True)` を読めず collection error になりました。全実走はリポジトリ実行系の Python 3.10.12 (`python3 -m pytest`) で行っています。

所有外への波及はありません。変更は指定所有ファイル4件のみです。shared resolver の呼び出し元はリポジトリ内の上記2箇所だけで、双方更新済みです。

未解決点はありません。M11/M12 の実 mutant 計測のみ、指定どおり親側の確認対象です。

# §14 変異実測ログ (親、1 巡目 = af8ff49 M1-M10)

```
=== baseline sel ===
[32m[32m[1m14 passed[0m, [33m141 deselected[0m[32m in 6.78s[0m[0m
=== baseline floor-digest ===
[32m[32m[1m29 passed[0m, [33m190 deselected[0m[32m in 0.35s[0m[0m
=== mutations ===
{"id": "M1-selector-map-merge", "verdict": "KILLED", "failed": ["orchestrator/tests/test_s8b_ratified_verify.py::test_selector_exact_exemption_accepts_declared_three_axis_evidence"], "note": "帰属 node=['orchestrator/tests/test_s8b_ratified_verify.py::test_selector_exact_exemption_accepts_declared_three_axis_evidence']"}
{"id": "M2-prefix-exemption", "verdict": "KILLED", "failed": ["orchestrator/tests/test_s8b_ratified_verify.py::test_selector_exact_exemption_accepts_declared_three_axis_evidence", "orchestrator/tests/test_s8b_ratified_verify.py::test_selector_exact_exemption_rejects_undeclared_selector_run_hit", "orchestrator/tests/test_s8b_ratified_verify.py::test_selector_payload_is_not_exempt_and_conjunction_is_scanned"], "note": "帰属 node=['orchestrator/tests/test_s8b_ratified_verify.py::test_selector_exact_exemption_rejects_undeclared_selector_run_hit']"}
{"id": "M3-raw-declared-sha", "verdict": "KILLED", "failed": ["orchestrator/tests/test_s8b_ratified_verify.py::test_selector_exact_exemption_rejects_coherent_wrong_raw_sha"], "note": "帰属 node=['orchestrator/tests/test_s8b_ratified_verify.py::test_selector_exact_exemption_rejects_coherent_wrong_raw_sha']"}
{"id": "M4-absent-predictions", "verdict": "KILLED", "failed": ["orchestrator/tests/test_s8b_ratified_verify.py::test_selector_exact_exemption_absent_prediction_is_noop"], "note": "帰属 node=['orchestrator/tests/test_s8b_ratified_verify.py::test_selector_exact_exemption_absent_prediction_is_noop']"}
{"id": "M5-digest-allowlist-column", "verdict": "KILLED", "failed": ["orchestrator/tests/test_s8b_floor_campaign.py::test_clean_scan_digest_accepts_exact_freeze_allowlist", "orchestrator/tests/test_s8b_floor_campaign.py::test_clean_scan_digest_binds_path_to_sha_not_only_hash_multiset", "orchestrator/tests/test_s8b_floor_campaign.py::test_clean_scan_digest_binds_recognized_chain_record_path_and_bytes"], "note": "帰属 node=['orchestrator/tests/test_s8b_floor_campaign.py::test_clean_scan_digest_binds_path_to_sha_not_only_hash_multiset', 'orchestrator/tests/test_s8b_floor_campaign.py::test_clean_scan_digest_binds_recognized_chain_record_path_and_bytes']"}
{"id": "M6-strict-equality", "verdict": "KILLED", "failed": ["orchestrator/tests/test_s8b_floor_campaign.py::test_validate_launch_certificate_strict_rejects_clean_digest_mismatch", "orchestrator/tests/test_s8b_floor_campaign.py::test_revalidate_issued_certificate_rejects_tampered_clean_digest", "orchestrator/tests/test_s8b_launch_cert.py::test_validate_launch_certificate_strict_rejects_clean_scan_digest_mismatch"], "note": "帰属 node=['orchestrator/tests/test_s8b_floor_campaign.py::test_validate_launch_certificate_strict_rejects_clean_digest_mismatch', 'orchestrator/tests/test_s8b_floor_campaign.py::test_revalidate_issued_certificate_rejects_tampered_clean_digest', 'orchestrator/tests/test_s8b_launch_cert.py::test_validate_launch_certificate_strict_rejects_clean_scan_digest_mismatch']"}
{"id": "M7-second-scan-reuse", "verdict": "KILLED", "failed": ["orchestrator/tests/test_s8b_floor_campaign.py::test_official_preflight_scans_exactly_twice_and_returns_independent_expected", "orchestrator/tests/test_s8b_floor_campaign.py::test_official_preflight_rejects_digest_shift_between_independent_scans", "orchestrator/tests/test_s8b_floor_campaign.py::test_second_scan_digest_shift_persists_claim_but_issues_no_certificate"], "note": "帰属 node=['orchestrator/tests/test_s8b_floor_campaign.py::test_official_preflight_scans_exactly_twice_and_returns_independent_expected', 'orchestrator/tests/test_s8b_floor_campaign.py::test_official_preflight_rejects_digest_shift_between_independent_scans', 'orchestrator/tests/test_s8b_floor_campaign.py::test_second_scan_digest_shift_persists_claim_but_issues_no_certificate']"}
{"id": "M8-journal-rows-compare", "verdict": "KILLED", "failed": ["orchestrator/tests/test_s8b_ratified_verify.py::test_selector_exact_exemption_rejects_journal_rows_mismatch"], "note": "帰属 node=['orchestrator/tests/test_s8b_ratified_verify.py::test_selector_exact_exemption_rejects_journal_rows_mismatch']"}
{"id": "M9-ancestry", "verdict": "KILLED", "failed": ["orchestrator/tests/test_s8b_ratified_verify.py::test_selector_exact_exemption_rejects_nonancestor_pre_oracle_head"], "note": "帰属 node=['orchestrator/tests/test_s8b_ratified_verify.py::test_selector_exact_exemption_rejects_nonancestor_pre_oracle_head']"}
{"id": "M10-envelope-declared-sha", "verdict": "KILLED", "failed": ["orchestrator/tests/test_s8b_ratified_verify.py::test_selector_exact_exemption_rejects_declared_sha_mismatch"], "note": "帰属 node=['orchestrator/tests/test_s8b_ratified_verify.py::test_selector_exact_exemption_rejects_declared_sha_mismatch']"}
rc=0
```

# §15 変異実測ログ (親、最終 = 437334a M1-M12)

```
=== baseline (fix2) ===
[32m[32m[1m19 passed[0m, [33m140 deselected[0m[32m in 9.46s[0m[0m
=== mutations x12 ===
{"id": "M1-selector-map-merge", "verdict": "KILLED", "failed": ["orchestrator/tests/test_s8b_ratified_verify.py::test_selector_exact_exemption_accepts_declared_three_axis_evidence"], "note": "帰属 node=['orchestrator/tests/test_s8b_ratified_verify.py::test_selector_exact_exemption_accepts_declared_three_axis_evidence']"}
{"id": "M2-prefix-exemption", "verdict": "KILLED", "failed": ["orchestrator/tests/test_s8b_ratified_verify.py::test_selector_exact_exemption_accepts_declared_three_axis_evidence", "orchestrator/tests/test_s8b_ratified_verify.py::test_selector_exact_exemption_rejects_undeclared_selector_run_hit", "orchestrator/tests/test_s8b_ratified_verify.py::test_selector_payload_is_not_exempt_and_conjunction_is_scanned"], "note": "帰属 node=['orchestrator/tests/test_s8b_ratified_verify.py::test_selector_exact_exemption_rejects_undeclared_selector_run_hit']"}
{"id": "M3-raw-declared-sha", "verdict": "KILLED", "failed": ["orchestrator/tests/test_s8b_ratified_verify.py::test_selector_exact_exemption_rejects_coherent_wrong_raw_sha"], "note": "帰属 node=['orchestrator/tests/test_s8b_ratified_verify.py::test_selector_exact_exemption_rejects_coherent_wrong_raw_sha']"}
{"id": "M4-absent-predictions", "verdict": "KILLED", "failed": ["orchestrator/tests/test_s8b_ratified_verify.py::test_selector_exact_exemption_absent_prediction_is_noop"], "note": "帰属 node=['orchestrator/tests/test_s8b_ratified_verify.py::test_selector_exact_exemption_absent_prediction_is_noop']"}
{"id": "M5-digest-allowlist-column", "verdict": "KILLED", "failed": ["orchestrator/tests/test_s8b_floor_campaign.py::test_clean_scan_digest_accepts_exact_freeze_allowlist", "orchestrator/tests/test_s8b_floor_campaign.py::test_clean_scan_digest_binds_path_to_sha_not_only_hash_multiset", "orchestrator/tests/test_s8b_floor_campaign.py::test_clean_scan_digest_binds_recognized_chain_record_path_and_bytes"], "note": "帰属 node=['orchestrator/tests/test_s8b_floor_campaign.py::test_clean_scan_digest_binds_path_to_sha_not_only_hash_multiset', 'orchestrator/tests/test_s8b_floor_campaign.py::test_clean_scan_digest_binds_recognized_chain_record_path_and_bytes']"}
{"id": "M6-strict-equality", "verdict": "KILLED", "failed": ["orchestrator/tests/test_s8b_floor_campaign.py::test_validate_launch_certificate_strict_rejects_clean_digest_mismatch", "orchestrator/tests/test_s8b_floor_campaign.py::test_revalidate_issued_certificate_rejects_tampered_clean_digest", "orchestrator/tests/test_s8b_launch_cert.py::test_validate_launch_certificate_strict_rejects_clean_scan_digest_mismatch"], "note": "帰属 node=['orchestrator/tests/test_s8b_floor_campaign.py::test_validate_launch_certificate_strict_rejects_clean_digest_mismatch', 'orchestrator/tests/test_s8b_floor_campaign.py::test_revalidate_issued_certificate_rejects_tampered_clean_digest', 'orchestrator/tests/test_s8b_launch_cert.py::test_validate_launch_certificate_strict_rejects_clean_scan_digest_mismatch']"}
{"id": "M7-second-scan-reuse", "verdict": "KILLED", "failed": ["orchestrator/tests/test_s8b_floor_campaign.py::test_official_preflight_scans_exactly_twice_and_returns_independent_expected", "orchestrator/tests/test_s8b_floor_campaign.py::test_official_preflight_rejects_digest_shift_between_independent_scans", "orchestrator/tests/test_s8b_floor_campaign.py::test_second_scan_digest_shift_persists_claim_but_issues_no_certificate"], "note": "帰属 node=['orchestrator/tests/test_s8b_floor_campaign.py::test_official_preflight_scans_exactly_twice_and_returns_independent_expected', 'orchestrator/tests/test_s8b_floor_campaign.py::test_official_preflight_rejects_digest_shift_between_independent_scans', 'orchestrator/tests/test_s8b_floor_campaign.py::test_second_scan_digest_shift_persists_claim_but_issues_no_certificate']"}
{"id": "M8-journal-rows-compare", "verdict": "KILLED", "failed": ["orchestrator/tests/test_s8b_ratified_verify.py::test_selector_exact_exemption_rejects_journal_rows_mismatch"], "note": "帰属 node=['orchestrator/tests/test_s8b_ratified_verify.py::test_selector_exact_exemption_rejects_journal_rows_mismatch']"}
{"id": "M9-ancestry", "verdict": "KILLED", "failed": ["orchestrator/tests/test_s8b_ratified_verify.py::test_selector_exact_exemption_rejects_nonancestor_pre_oracle_head"], "note": "帰属 node=['orchestrator/tests/test_s8b_ratified_verify.py::test_selector_exact_exemption_rejects_nonancestor_pre_oracle_head']"}
{"id": "M10-envelope-declared-sha", "verdict": "KILLED", "failed": ["orchestrator/tests/test_s8b_ratified_verify.py::test_selector_exact_exemption_rejects_declared_sha_mismatch"], "note": "帰属 node=['orchestrator/tests/test_s8b_ratified_verify.py::test_selector_exact_exemption_rejects_declared_sha_mismatch']"}
{"id": "M11-journal-schema-version", "verdict": "KILLED", "failed": ["orchestrator/tests/test_s8b_ratified_verify.py::test_selector_launch_rejects_wrong_journal_schema_value"], "note": "帰属 node=['orchestrator/tests/test_s8b_ratified_verify.py::test_selector_launch_rejects_wrong_journal_schema_value']"}
{"id": "M12-decision-row-equality", "verdict": "KILLED", "failed": ["orchestrator/tests/test_s8b_ratified_verify.py::test_selector_launch_rejects_journal_row_decision_drift[claim-decision-method]", "orchestrator/tests/test_s8b_ratified_verify.py::test_selector_launch_rejects_journal_row_decision_drift[static-decision-method]", "orchestrator/tests/test_s8b_ratified_verify.py::test_selector_launch_rejects_journal_row_decision_drift[static-choice-id]"], "note": "帰属 node=['orchestrator/tests/test_s8b_ratified_verify.py::test_selector_launch_rejects_journal_row_decision_drift[claim-decision-method]', 'orchestrator/tests/test_s8b_ratified_verify.py::test_selector_launch_rejects_journal_row_decision_drift[static-decision-method]', 'orchestrator/tests/test_s8b_ratified_verify.py::test_selector_launch_rejects_journal_row_decision_drift[static-choice-id]']"}
rc=0
```
