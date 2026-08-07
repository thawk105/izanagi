# 段 4 裁定 — [T-614] provenance 既知違反台帳 (案 3)

段 3 の 3 レンズ (検出力の保存 / 整合と実効性 / 裁定の忠実性) の所見を real / refuted に裁定し、
plan v2 と変異事前登録を確定する。逐語は `s3/out-lens1.md`, `out-lens2.md`, `out-lens3.md`。

## 決定的な新事実 — 7 件目はユーザーが裁定済みだった

レンズ 3 が worklog (285) を掘り当てた。`3f2c43d7` は 2026-08-07 に**ユーザー本人が見て裁定している**。

> 段 9 の incoming 監査赤を、ユーザーが今回の land に限り明示的に免除した。(中略)
> 親は停止を提案し、ユーザーが「今回だけ免除して land する」を選択した。
> **防壁の恒久的な緩和はしない** — 次回以降は従来どおり停止する。

原因も判明している — trailer 自体は在るが `AI-Agent:` と `Co-Authored-By:` の間に空行が入り、
Git が trailer block と認識していない。

**台帳への追加は「防壁の恒久的な緩和」そのものである。** ユーザーはそれを明示的に拒んだ。
よって親の provisional 裁定 (P1) を維持する — 台帳は裁定どおり 6 SHA だけとし、
`3f2c43d7` は新規のまま rc=1 に寄与させる。恒久的な処置は裁定パッケージで返す。

## 所見の裁定

| # | レンズ | 所見 | 裁定 | 処置 |
|---|---|---|---|---|
| 1 | 1-1 | 既定範囲の `--ancestry-path` に列挙盲点 (policy 導入前 fork → 後日 merge) | **real** | **scope 外** → 裁定パッケージ。本 wave では現に no-op (実測 1659 = 1659) |
| 2 | 1-2 / 2-1 / 3-2 | P1 のままでは既定監査が rc=1 のまま残る | **real** | **P1 維持**。上記の新事実により、台帳追加は不可。残余は裁定パッケージ |
| 3 | 1-3 / 2-7 / 3-6 | finding と kind の平行 tuple が fail-closed でない | **real** | **採用** (D-2) |
| 4 | 1-4 | SHA 以外の一致・全 finding 吸収 | refuted | negative test を追加 |
| 5 | 1-5 | correction / waiver との二重抑止 | refuted | composition test を追加 |
| 6 | 1-6 | stale と部分 range の両立 | refuted | `main --range` の end-to-end test を追加 |
| 7 | 1-7 | pin テストは裁定を機械的に強制しない | **real** | **採用** (D-10)。主張を訂正し、entry に裁定 ID を持たせる |
| 8 | 1-8 | 自動 dev-wave 層は stdout を捨てるので既知一覧が残らない | **real** | rc=1 経路の公開 test は採用。receipt 保存は **scope 外** → 裁定パッケージ |
| 9 | 1-9 | land 本体は full-history を消費しない | **real、scope 外** | 裁定パッケージ (insight で既知) |
| 10 | 2-2 / 2-3 | (B) の警告が dispatch の tail 切り捨てで手元に届かない / 位置が契約と不整合 | **real** | **採用** (D-5)。plan の実行子側配置を却下し親側へ変更 |
| 11 | 2-4 / 3-8 | DW-G05 の「値は不変」が広すぎる | **real** | **採用** (D-8) |
| 12 | 2-5 / 2-9 | 既存テストの破壊 / exact pin の実装不能 | refuted | 親が実測で確認する |
| 13 | 2-6 | 台帳 validator の実行時点が未確定 (import 時 raise で rc=2 契約が壊れる) | **real** | **採用** (D-3) |
| 14 | 2-8 | 短縮 SHA test が validator 契約と衝突、negative 単独では恒真 | **real** | **採用**。rc=2 test と正負対、空 registry の mutation control |
| 15 | 2-11 | 段 5 の 2 並列に編集競合なし | refuted | 所有分割はそのまま。統合実測は親が直列で行う |
| 16 | 3-1 | 「6 違反を報告」の受入判定が不正確 | **real** | **採用** (D-6)。言い方を訂正する |
| 17 | 3-3 | T-300 が既定範囲計算を変えたという退行説 | **refuted** (blame 証拠あり) | 範囲計算は本 wave で触らない |
| 18 | 3-4 | rc=0 の発生原因を「再現しない」で閉じている | **real** | **採用** (D-7)。退行 refuted、観測原因 unresolved と記録する |
| 19 | 3-5 | stale-red は未裁定の gate 拡張 | **real** | **部分採用** (D-4)。新規違反に数えず rc=2 とし、裁定パッケージにも載せる |
| 20 | 3-7 | 一般 allowlist / CLI 免除 / correction 拡張への抵触 | refuted | 内部固定 6 件の境界を維持する |

## plan v2 — 段 2 プランからの変更点

- **D-2 単一構造**: `normal_findings` / `normal_finding_kinds` の平行 tuple を廃し、
  `NormalFinding(text, ledger_kind: str | None)` の単一列にする。台帳照合可能な 2 種以外は
  明示的に `None`。長さ不一致という失敗モードを構造的に消す。
- **D-3 lazy validator**: 台帳の妥当性検査 (40 桁小文字 hex / SHA 重複なし / kind が閉集合内 /
  裁定 ID 非空) は **import 時ではなく history 分岐内の既存 `try` の内側**で行い、
  破損時は `RuntimeError` → **rc=2**。`--message-file` は台帳破損の影響を受けない。
- **D-4 stale の定義と rc**: stale = 「台帳 SHA が selected set 内、かつ**期待種別の finding が 0 件**」
  (plan の「全 finding が 0 件」を修正 — 別種 finding が残ると stale を見逃すため)。
  stale は**新規違反に数えず rc=2** とする。裁定は「rc は新規のみで決める」であり、
  台帳の整合性破綻は provenance 違反ではなく監査機構自身の破綻だからである。
  範囲外 entry は stale にしない。
- **D-5 (B) の警告位置**: plan の「実行子側 (`use_xdist` 直前)」を**却下**する。
  dispatch 成功時の stderr は末尾 4 KiB しか親へ戻らず、警告が消える (レンズ 2 の実測根拠)。
  警告は **`main()` の最も早い時点** — site 判定・dispatch・bounded 再実行より前 — で、
  非受入形なら stderr へ 1 行出す。再実行された子側では出さない
  (子であることを示す既存 marker を使う。marker が無ければ**不可視より二重表示を選ぶ**)。
  pytest argv・受理集合・rc は変えない。
- **D-10 裁定 ID**: `KnownViolationSpec` に `ruling` field (例 `worklog(284) 2026-08-07 /rulings`) を
  必須で持たせる。pin テストは「片側 drift を検出する tripwire」であって
  「ユーザー裁定を機械的に強制する機構ではない」— 主張をそう訂正する。
- 追加テスト: 期待種別 + 別種 finding の同居、cardinality 破壊、短縮 registry entry の **rc=2**、
  正負対 (有効 full entry は既知 / 同一 finding の別 full SHA は新規)、
  **空 registry で 6 件が新規へ戻る mutation control**、`main --range` の
  selected-stale / outside-range、既知 + 新規の rc=1 経路で既知一覧が stdout に出ること。

## 実測の訂正 (D-6 / D-7)

- 受入条件は「**指定 6 SHA がすべて既定の全走で報告されること**」として充足した。
  実測は 7 違反であり、「厳密に 6 件」という読みでは不成立である。7 件目は裁定済みの `3f2c43d7`。
- T-300 の退行は **refuted** — 範囲式は初出 commit `50c1ef4e` のまま、T-300 系 5 commit は
  範囲式を変えていない (レンズ 3 の blame 実測)。本 wave の実測でも
  既定 (1660 件) と `--range 50c1ef4e..HEAD` (1659 件、差は policy commit 自身のみ) が
  **同一の 7 違反・同一 rc=1** を返した。
- ただし rulings session が rc=0 を見た**原因は unresolved** である。当時の cwd・HEAD・
  実行経路・生コマンドが保存されていない。「解消済み」とは記録しない。

## 成果物影響の訂正 (D-8)

- **研究成果物 (certified 選択・材料レポート・試行台帳・proof chain) の値と参照は不変。**
  レンズ 3 が selector / layer3_report / trial_registry / layout を実読して確認した。
- **変わるのは**: 開発 commit gate の受理集合 (既知 6 は緑扱い、新規は赤)、
  task-run 台帳に残る exit status、Pegasus dispatch receipt の stderr tail (警告 1 行ぶん)。

## 変異事前登録 (DW-M01)

実装前に登録する。各変異は単一理由で赤になることを実装後に確認する。

| ID | 変異 | 期待赤 (単一理由) |
|---|---|---|
| M1 | 台帳 lookup を full SHA exact から前方一致へ | 正負対テスト (別 full SHA が既知にならない) |
| M2 | finding 種別の一致検査を外し SHA 一致だけで抑止 | 期待種別 + 別種 finding 同居テスト |
| M3 | entry あたり 1 件制限を外し同 SHA の全 finding を吸収 | 同種重複テスト |
| M4 | 台帳を空 tuple にする | 実 6 件が新規へ戻る control |
| M5 | rc 判定を「既知 + 新規」で行う (旧挙動) | 既知のみ range で rc=0 を pin するテスト |
| M6 | 既知の stdout 公開を削る | 公開 pin テスト (rc=0 経路と rc=1 経路) |
| M7 | stale 検出を外す | selected-stale rc=2 テスト |
| M8 | (B) の警告を削る | 非受入形の警告 exact 1 行テスト |
| M9 | (B) の警告を受入形でも出す | 受入形で出ないことの pin テスト |

**正例 (承認外の過剰拒否の検出)**: (i) 既知のみを含む range が rc=0 になる、
(ii) 台帳に無い commit の違反が正しく新規として残る (`3f2c43d7`)、
(iii) 台帳を含まない部分 range が stale で赤にならない。

## 段 5 の所有分割

- **実装子 A**: `tools/check_ai_provenance.py`, `orchestrator/tests/test_check_ai_provenance.py`
- **実装子 B**: `tools/run_tests.py`, `orchestrator/tests/test_run_tests_preflight.py`
- **親**: `docs/provenance/audit.md` (`PR-A02` の意味等価な再構成。family 予算 8,981/9,000 bytes のため
  単純追記は不可)、統合、変異 matrix、受入全走、記録、commit。

## 裁定パッケージ (ユーザーへ返す — 本 wave では実装しない)

1. **`3f2c43d7` の恒久的処置。** 台帳追加は「防壁の恒久的な緩和」であり、ユーザーが 2026-08-07 に
   明示的に拒んでいる。よって本 wave では入れない。結果として既定監査は実装後も
   **既知 6 / 新規 1 / rc=1** のまま残る。選択肢: (a) 現状維持 (1 件の手作業帰属が残る)、
   (b) 台帳へ追加 (恒久緩和を撤回する再裁定)、(c) 別経路 (correction の再開放等 — `PR-C01` が禁止)。
2. **既定範囲の `--ancestry-path` 盲点。** policy 導入前から分岐した branch 上の違反 commit を
   後日 merge すると、素の range には入るが既定監査からは落ちる。本 wave の実測では現に no-op
   (1659 = 1659) だが、将来の穴である。素の `policy..HEAD` へ変えるのは strict な強化だが裁定外。
3. **land が full-history 監査を強制していない。** `dev_wave_land.py` は `--message-file` preflight
   だけを呼ぶ。手動 full-history を省けば新規違反が main へ入る経路が残る。
4. **自動 dev-wave 層が stdout を捨てる。** `tools/dev_waves/cli.py` は stdout/stderr を
   `DEVNULL` に捨て rc だけ保持するため、既知 SHA と件数が receipt に残らない。
   「公開が唯一の抑止」という契約がこの層では成立しない。
5. **stale → rc=2 の是非 (D-4)。** 裁定は rc semantics を「新規のみ」と定めた。台帳整合性の破綻を
   rc=2 で赤にするのは、裁定の文言を超えない範囲で入れた fail-closed 不変条件である。
   不要と判断するなら外す。
