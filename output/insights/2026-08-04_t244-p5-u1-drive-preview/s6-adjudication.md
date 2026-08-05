# 段 6 所見の裁定 — [T-244] D121 P5 U-1

revA (BLOCKER 2 / MAJOR 3 / MINOR 4)、revB (BLOCKER 1 / MAJOR 2 / MINOR 1) を親が裁定する。

| 所見 | 裁定 | 対応 |
|---|---|---|
| S6-A-1 `and not do_build` 生存 | real・採用 | fix: do_build=True + 注入の負例を追加 (U-1 は build-site/authority 検査に先行するため authority 不要) |
| S6-A-2 preview 非 callable 欠落 | real・採用 | fix: `preview=object()` 負例を追加 |
| S6-A-3 `!=` 弱体化が生存 | real・採用 | fix: 敵対的 `__eq__` 値 (常に True) の drive / preview 負例を追加 |
| S6-A-4 解決位置 pin 不足 | real・**must-fix にしない** | module 再束縛は s4 §1 の非保証。成果物影響を書けない (DW-G05) ため nit。記録のみ |
| S6-A-5 M10 が build-site fail-loud に mask | real・採用 | fix: build-site を fail-loud にしない専用負例 (U-1 エラー + run_root 非存在) を追加し、M10 の期待 node をそこへ再照準 |
| S6-A-6 変異期待 node の不一致 | real・採用 | 親対応: mutation spec は変異ごとに対象走 (単一 node または実在 nodeid 集合) を固定して作る |
| S6-A-7 / revB-3 wall precedence 未固定 | real・採用 | fix: `max_wall_s=0` + 注入 → U-1 エラーの負例を追加 |
| S6-A-8 regex `$` 緩さ | real・採用 | fix: `\Z` へ置換 (全 U-1 系 expected_match) |
| S6-A-9 復元 assert 無し | real・採用 | fix: module 属性を差し替える全テストの try/finally 後に identity assert を追加 |
| revB-1 D96 同一変更単位が未成立 | real・**プロセス対応** | 段 7 で新 D fragment・境界テスト・実装を同一 land 単位 (同一 wave branch) に含める。コード fix 不要 |
| revB-2 実装報告の受理集合記述が不正確 | real・採用 (記録側) | 段 7 の D fragment / worklog は revB の再構成 (新規拒否 = allowed-value str subclass + claude-headless の non-sentinel 明示、sentinel 持込みは通る = 非保証、omitted の late binding 化、signature default の opaque 化) を正とする |
| revB-4 診断の過大・混在 | 一部採用 | 採用: `type(provider_kind) is not str` の診断を「plain str 必須」へ分離 (受理集合不変、subclass テストの regex を追随 — この期待値変更は本裁定で明示承認)。不採用: U-1 エラーメッセージ変更 — 既存 P5-1 gate の兄弟文言と揃え、非保証の列挙は D / runbook が担う (D148 先例) |

fix は 1 単位 (一枚岩) とする。理由: 3 file の所有が実装子と同一で、所見が相互に同じ helper
(`_assert_claude_call_rejected_before_side_effects`) と同じ production 診断分岐に触れるため。

## 変異登録の確定 (fix 後、S6-A-6 対応)

spec = `mutation-spec.json` (sha256 f61e179be7d780ecea21a4a2449b56b80ebc3abe16a5375668e72748594a8c1b)。
runner scope は `test_role_session_isolation.py` 単独とし、期待赤集合は全変異について
実 nodeid で網羅登録した (M1=15 / M2=9 / M3=4 / M4=13 / M5=M6=2 / M7=2 / M8=1 / M9=7 /
M10=16 / M11=2 / M12=1 / M13=1)。s4 §9 の速記からの変更点:

- **M9** は「omitted 正例のみ」でなく、既定関数を注入する 6 node + omitted 解決正例 1 node =
  計 7 node が赤になる (gate の drive 項が既定関数注入を省略と誤認 → precedence 系は
  別エラー/AssertionError で赤)。全 7 node を登録
- **M10** (gate を mkdir 後へ移動) は移動後の gate が「解決済み = 非 sentinel」を注入と誤認するため、
  omitted の解決テストも赤になる (16 node)。side-effect 境界の指定 kill 証拠は
  `creates_no_run_root_without_build_site_patch` の `run_root` 非存在 assert
- **M11** は「解決を `_run_workload` へ遅延」の忠実な textual 変異が構成できないため、
  **M5+M6 同時 (両層) の解決全削除**へ再照準した (DW-M02 の両層変異登録を兼ねる)。
  期待は解決位置テスト + fixture 省略回帰の 2 node
- **M12** は providers gate と U-1 gate の連続 block 入替えで表現し、期待は precedence テスト 1 node
