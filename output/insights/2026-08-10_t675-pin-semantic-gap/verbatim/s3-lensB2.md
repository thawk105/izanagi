親案は現状のままでは **NO-GO** です。M3/M4 は親台帳の記録を参照しただけで、pytest・`check_docs` は再実行していません。ファイル変更はなく、`git status --short` は空です。

## 所見

### 1. 発火条件

- 確度: high／判定: **refuted**（「発火条件がない」）
- 根拠: `docs/dev-wave/core.md:60`、`.claude/commands/cleanup-branches.md:17`、`:38`、`:44`。対象 artifact、pin、F26/F51 は実在する。親台帳 M3/M4 も削除＋再 pin の経路を記録している（`measurements.md:30`、`:40`）。
- 親の裁定: DW-G04 不成立を理由に棄却してはならない。ただし次項の費用判断は別に行う。

### 2. 実運用での価値

- 確度: medium／判定: **real**
- 根拠: 実害は F173 の1件で、`docs/failures.md:4382` は焦点再レビューが既に捕捉したと記録する。機械検査が追加で捕捉するのは、同レビューを通り抜けた残余だけである。
- 親の裁定: D205 と DW-G05 の下では、恒久機構を必須化せず、DW-O16 手順＋明確な再訪条件を既定にすべき。

### 3. pin 閉包の不整合

- 確度: high／判定: **real**
- 根拠: brief は command の3箇所だけを M1 とする（`s1-brief.md:29`）が、実測台帳は Skill 側3箇所を追加して合計6箇所としている（`measurements.md:6`、`:13`）。実コードも Skill pin が `tools/check_docs.py:378`、command pin が `:389` にある。
- 親の裁定: brief・コスト・実装対象を「6箇所」に訂正してから裁定する。

### 4. path 検査のスコープ漂移

- 確度: high／判定: **real**
- 根拠: brief P4 は path 到達性を採らない（`s1-brief.md:71`）一方、plan は `PATH_REF` と path 実在性を実装に含める（`s2b-plan.md:41`、`:154`）。path レンズは親 M4 の実測対象でもない。
- 親の裁定: path を削除するか、path 専用の正例・負例を事前登録してから採用する。未測定のまま最小修復と呼ばない。

### 5. 正当編集を殺す具体例

1. **helper の移動・改名**  
   `tools/audit_dangling_commits.py` を同等の別 path へ移すと、動作は維持されても exact literal が赤くなる。  
   確度: high／判定: **real**。根拠: `s2b-plan.md:28`、`.claude/commands/cleanup-branches.md:17`。  
   親の裁定: path literal は alias/移行契約なしに固定しない。

2. **F26/F51 の archive 移動・統合**  
   現在は `docs/failures.md:402` と `:1294` にあるが、archive の墓標様式は filename ベースで `### F<n>.` ではない（`docs/archive/README.md:16`、`:18`）。  
   確度: medium／判定: **real（将来条件付き）**。現 tree に failures archive はないが、移動時の exact heading 検査は壊れる。  
   親の裁定: failures の非ローテーションを正本化するか、archive 側の F-ID 到達契約を先に作る。

3. **参照を shell の fenced code block へ移す**  
   実行手順としては自然でも、plan の可視本文抽出が fence を除外するため literal 不在扱いになる（`s2b-plan.md:37` 付近）。  
   確度: medium／判定: **real**。  
   親の裁定: layout ではなく意味を表す短い address token だけを固定し、fence を一律不可視にしない。

長い日本語句（例:「正本は…」）の exact pin は、縮約・言い換えで赤くなる。これは現行の address-only 方針なら refuted だが、(b) を literal 化するなら real である（`s2b-plan.md:87`、`:115`）。

### 6. a1 / a2 のコスト段差

- 確度: high／判定: **a1 は限定的に refuted、a2 は real**
- 根拠: 合成 command は全文逐語コピー（`orchestrator/tests/test_check_docs.py:318`）なので、必須 literal だけなら baseline fixture の内容追加は不要。だが負例テストと再 pin helper の追加は必要（`s2b-plan.md:61`、`:78`）。
- 根拠: F-ID 検査では `_build_min_repo` が `docs/failures.md` を作らない（`orchestrator/tests/test_check_docs.py:710`）。既存 helper は違反件数をちょうど1件に固定する（`orchestrator/tests/test_check_docs.py:6599`）。
- 親の裁定: 「a1 は fixture 無改修」は baseline data に限定し、テスト無改修とは書かない。a2 は fixture 拡張込みの別コストとして扱う。

### 7. 非対称な適用範囲

- 確度: high／判定: **real**
- 根拠: `docs/failures.md` は合成 repo の列挙対象外（`measurements.md:82`）。`docs/dev-wave/**` は構造・予算検査はあるが、提案 guard の対象外（`tools/check_docs.py:3918`、`:4129`）。一方、pin 済み cleanup command は既に frontmatter と self-improvement pointer を検査されている（`tools/check_docs.py:4104`）。
- 親の裁定: 「2 artifact が優先」と一般化してはならない。F173 の局所修復として限定するか、active な dev-wave/failures の正本ポインタを手順で守るべき。

### 8. 安い代替策

- **pin 定数変更時の警告** — 確度 medium／**refuted**。警告は無視でき、F173 の削除＋再 pin を止めない（`tools/check_docs.py:378`、`:389`）。親の裁定: 補助通知に限定。
- **予算超過メッセージ** — 確度 high／**refuted**。既存文は「安全義務を削らず reference へ統合」と出すが（`tools/check_docs.py:4020`）、F173 は予算内に縮めたため発火しない（`measurements.md:20`）。親の裁定: 代替防壁と数えない。
- **(b) の明記だけ** — 確度 high／**refuted**。M3 の再 pin 攻撃には検査効果がない（`s1-brief.md:38`）。親の裁定: 文書説明としては採用可だが、F173対策とは呼ばない。
- **DW-O16 の手順** — 確度 high／**real**。F173 は実際にこの焦点再レビューで捕捉されている（`docs/dev-wave/operations.md:84`、`docs/failures.md:4382`）。親の裁定: D205 下の第一選択にする。

### 9. 24 bytes の扱い

- 確度: high／判定: **real**
- 根拠: command の上限は `tools/check_docs.py:170`、既存 helper は違反1件を強制する（`orchestrator/tests/test_check_docs.py:6599`）。17 bytes の既存変異を考慮した headroom 24 は実質的制約であり、plan の「checker が強制する値ではない」（`s2b-plan.md:16`）は不正確。
- 親の裁定: command へ説明文を足してはならない。既存安全文を削って捻出する案は F173 再演になる。

### 10. P5 の先送り

- 確度: high／判定: **real**
- 根拠: F26 の同型改善は「pin 定数更新が必要」を理由に未実施・次の一手へ登録された（`docs/failures.md:415`、`:417`）。その後、F173 で同じ cleanup command の参照欠落が発生した（`docs/failures.md:4370`）。
- 親の裁定: 「次の cleanup wave へ相乗り」だけでは不十分。今ここで手順を正本化するか、所有 wave・発火条件・期限を明記したユーザー裁定にする。

### 11. T-659 / DW-G05 との比較

- 確度: high／判定: **real、ただし完全同型ではない**
- 根拠: T-659 は certified 値・レポート・台帳・受理集合を変えないため機構を作らず手順を推奨した（`output/insights/2026-08-09_t659-activation-deploy-window/README.md:13`、`verbatim/s4-adjudication.md:36`）。T-675 は同じく科学成果の値を変えないが、変えるのは AI 作業手順の受理集合（`s2b-plan.md:140`）。
- 親の裁定: T-659 と同じく D205 の手順優先を基本にする。ただし「受理集合を守る防壁」として機構を採るなら、a1だけに限定し、a2・path・archive 対応は別裁定にする。

## 総括

**NO-GO。** 発火経路は実在するが、既知の1件はDW-O16で捕捉済みで、成果物値は変わらない。  
a1のbaseline fixture無改修は成立するが、a2のF-ID検査とpath検査は保守・archive契約が未成熟。  
P5の相乗り先送りには実再発例があるため、手順化または明示的な再訪条件を今決めるべき。