指定の 5 ファイルを全文確認した。判定は静的検査のみで、pytest・probe・`check_docs.py` は実行していない。`git diff --check` のみ成功。

T-730 は裁定逸脱なし。`_safe_path` と `read_blob_at` の 2 層だけに NUL 拒否を追加し、TAB 正例で C0 一般化も拒否している。

### 所見

**D1 — §7.3 は実行可能な待ち手手順として未閉鎖で、既存待ち手も glob 判定のまま残る。**  
file: `docs/pegasus-runbook.md:771`、`/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t683-caller-closure/run_acceptance.sh:18`。実測なし。  
成果物影響: `acquired` を見落とすと受入集合から wave が消え、誤検出すると stale base のレポート・台帳が land 拒否される。  
深刻度: **must-fix**  
推奨: B3 の canonical script 新設はしないまま、§7.3 に stdout、rc、JSON の `state`、固定 literal `acquired` の個別判定を明示する。`case *acquired*`、pipeline、`|| true` は禁止する。

**D2 — merge の provenance preflight・commit rc・監査失敗時の fail-closed 分岐が明文化されていない。**  
file: `docs/pegasus-runbook.md:792`、`docs/dev-wave/operations.md:92`、`run_acceptance.sh:51`。実測なし。  
成果物影響: provenance 不備の受入走を消費し、land 監査で拒否されるため certified 選択・レポート・台帳が main に反映されない。  
深刻度: **must-fix**  
推奨: `git rev-parse`、`rev-list`、merge、`git commit --dry-run -F`、commit、full-history 監査を各 rc で判定し、非 0 は merge abort → release → 受入投入なしとする。

**D3 — 段 4 が採用した B8 の F196 superseded 注記が実装されていない。**  
file: `/work/1/SFC/tanab/dev-wave-jobs/t730-t732-nul-lease/s4_ruling.md:34`、`docs/failures.md:4809`。実測なし。  
成果物影響: certified 値は直接変わらないが、T-732 の裁定・受入契約への参照が台帳上不明確になり、後続 report の重複・延期を招く。  
深刻度: **must-fix**  
推奨: F196 本文を履歴として残し、「F197 および T-732(a) により superseded」と 1 行追記する。

**D4 — B9 の worklog 訂正も patch に現れていない。**  
file: `/work/1/SFC/tanab/dev-wave-jobs/t730-t732-nul-lease/s4_ruling.md:35`、`docs/worklog.md:2610`。実測なし。  
成果物影響: 実験成果物の値は変わらないが、文書予算に関する reviewer の参照解釈が不統一になる。  
深刻度: **should-fix**  
推奨: runbook に byte 予算 cap がないことを worklog に明記する。

**D5 — §7.3 は queue degraded 時の飢餓非保証を残している。**  
file: `docs/pegasus-runbook.md:821`。実測なし。  
成果物影響: 受入の遅延・未実施は起こり得るが、certified 選択値そのものは変えない。  
深刻度: **nit / backlog**  
推奨: 「飢餓せず到達」とは表現せず、既知の公平性非保証として明示する。これは T-732 の scope 外。

### B1〜B9 対応表

| ID | 段 4 処置 | 判定 | 根拠 |
|---|---|---|---|
| B1 | post-`acquired` に `git rev-parse main` | **closed** | `docs/pegasus-runbook.md:786-790` |
| B2 | refuted、不採用 | **closed（refuted）** | D239 は受入・land 終端で release と明記。`docs/decisions.md:11172` |
| B3 | canonical script は scope 外 | **closed（裁定上不採用）** | 新 script は追加されていない。ただし実行可能性は D1 |
| B4 | `state` と `acquired` の exact 比較 | **closed（文言）** | `docs/pegasus-runbook.md:773-777`。既存待ち手は D1 |
| B5 | `DW-O17` と AI-Agent trailer | **closed（参照）** | `docs/pegasus-runbook.md:794-796`。実行分岐は D2 |
| B6 | 2 走目の前に再 claim | **closed** | `docs/pegasus-runbook.md:815-817` |
| B7 | 残余 race を明記 | **closed** | `docs/pegasus-runbook.md:799-804` |
| B8 | F196 superseded 注記 | **regressed** | F196:4809 に旧「scope 外」が残り、注記なし |
| B9 | 予算表現の訂正 | **partial** | s4 処置に対応する worklog 訂正が確認できない |

### 新設 8 node の検出力

8 node はすべて既存 CR/LF node の単なる重複ではない。

- `core::test_read_blob_at_rejects_nul_alias[trailing-nul]`
- `core::test_read_blob_at_rejects_nul_alias[embedded-nul]`  
  → NUL による prefix blob alias。
- `core::test_read_blob_at_accepts_embedded_tab_path`  
  → 層 2 の C0 一般拒否変異。
- `predicates::test_contract_loader_rejects_embedded_path_control_chars[required-nul]`
- `predicates::test_contract_loader_rejects_embedded_path_control_chars[consumer-nul]`
- `predicates::test_contract_loader_reports_explicit_path_reason_for_trailing_controls[trailing-nul]`  
  → 層 1 の NUL 拒否と reason 固定。
- `predicates::test_contract_loader_accepts_embedded_tab_path`  
  → 層 1 の C0 一般拒否変異。
- `predicates::test_safe_path_rejects_membership_spoofing_str_subclass`  
  → `str.__contains__` 偽装回避。

### 正本の一意性

grep の結果、`docs/dev-wave/operations.md:92-96` と `.claude/commands/dev-wave.md:57` は §7.3 と整合している。`tools/wave_land_window.py:909-928` も claim JSON / status key=value の実装と一致する。

食い違いは `docs/failures.md:4809` の F196 が旧契約を「scope 外」と記録したまま残っている点で、D3 に該当する。

## 総括

**NO-GO**。must-fix は **3 件**（D1〜D3）。