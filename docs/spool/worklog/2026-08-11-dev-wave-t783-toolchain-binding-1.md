---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-08-11
wave: dev-wave-t783-toolchain-binding
seq: 1
title: toolchain 束縛を receipt 側へ実装し、環境・世代をまたぐ床値の混用を機械的に閉じた — [T-783] S-1〜S-4 と [T-747] (B) を同一 land で実装、attempt 脚と成果物 schema は新事実つきで裁定へ返す (コード + docs、branch worktree-dev-wave-t783-toolchain-binding)
---

## 本文

- **[T-783] S-1〜S-4 (worklog 412 で全問推奨どおり裁定) と [T-747] (B) を実装した。**
  一次控えは `rulings-inbox/2026-08-04-rulings-session-5rulings.md` §84。
- **S-4 の裁定 (「束縛検査は W-1 の実装 wave に含める」) は実行不能になっていた。**
  W-1 = [T-781] が worklog 413 で「実装なしで保留終端」と裁定され、W-1 の実装 wave が
  存在しなくなったためである。本 wave の command 引数がこれを上書きし、
  A-1 (site 解決化) と A-2 (束縛検査) を**同一 land に含める**ことで
  S-4 の目的 (「解禁したが束縛が無い」窓を作らない) を満たした。
- **「混用」の定義を一次資料で確定した。** worklog 383 の [T-747] 初回裁定 (a) は
  「**既存 `linux-baremetal` 床値との混用は不可** (環境束縛量として Pegasus で新規取得)」であり、
  403 の再裁定 (B) も「toolchain 混用不可の趣旨は不変」と明記している。
  **つまり cc/cxx の対の混用ではなく、環境・世代をまたぐ床値の混用である。**
  親 brief の provisional 裁定 (P6) はこれを誤解していたので撤回した。
- **親 brief の主張 2 件が段 3 で refuted された。** (1)「A-2 の gate は pilot 床値 campaign で
  runnable today」— `tools/pegasus/submit_floor.sh` に pilot 切替は無く、投入 shell は
  `--mode official` 固定であるため、**今日走る床値 build の経路は存在しない**。
  (2) P6「cc と cxx が同一 toolchain 由来であることを固定する」— 固定できるのは
  「登録済み cc/cxx 対と一致すること」までである。
- **`DW-G04` (発火経路が無ければ設計メモに留める) は本項目についてユーザー裁定で上書き済みと
  判断し、再度返さなかった。** 残余 wave の裁定パッケージ §4 S-4 が選択肢 (a)
  「W-1 が開くまで設計メモに留める (`DW-G04` の既定)」を明示提示したうえで、
  ユーザーは (c) を選び、さらに本 wave の command 引数で実装を指示している。
- **裁定時点で未見の新事実 2 件により、S-3 (a) と S-2 の成果物側は実装せず再裁定へ返す**
  (`DW-S04`。親が不採用にはしていない)。詳細は {{D:toolchain-binding-scope-narrowed}}。
- **段 6 レビュー 2 本はいずれも NO-GO**、real 所見 3 件。fix は 3 巡 (`DW-O16` の上限) で閉じた。
  さらに変異結果を受けて単一理由テストを 1 本追加した。
- **変異 M03 が SURVIVED し、冗長ゲートによる mask と判明した** ({{F:redundant-gate-masks-authority-mutation}})。
  `DW-M02` に従い初回結果を erratum として残し、両層同時変異で裏取りし、
  単一理由テスト追加後に単独で KILLED になることを再測した。
- **[T-748] の W-2 (床値実測・第 1 世代) は投入できない。** 実測 3 点が独立に塞ぐ。
  本 wave はキュー投入 (計測) を行っていない。検査系の dispatch は行った。
- **AI 工数**: codex 子 9 本 (plan 1 / consult 2 / author 2 / fix 4)。
  うち段 6 review の初回 2 本は引数契約違反で即死し成果物ゼロ (下記 §改善)。
- **ユーザー手番**: 裁定 4 件 (下記「新規」)。push は行わない。

### 実測 (すべて親が取得)

| # | 内容 | 値 |
|---|---|---|
| M-1 | `_assert_official_permitted` の official 無条件拒否 | 実在 (`s8b_floor_campaign.py:207-217`) |
| M-2 | `eligible_for_refreeze` は official 限定 | `:2453` / `:3174`。**pilot は再凍結に使えない** |
| M-3 | 投入 shell の mode | `floor_campaign.sh:962` が `--mode official` 固定 |
| M-4 | driver CLI | `choices=["pilot","official"]`。pilot は直接起動でのみ到達可 |
| M-5 | login の `gcc-13` / `g++-13` | 不在。compute (bnode005 probe) でも不在 |
| M-6 | `_tool_version('gcc','cc')` の version 先頭行 | `x86_64-linux-gnu-gcc-11 (Ubuntu 11.4.0-1ubuntu1~22.04.3) 11.4.0` |
| M-6b | calibration の `compiler_version` 先頭行 | `gcc (Ubuntu 11.4.0-1ubuntu1~22.04.3) 11.4.0` |
| M-6c | 逐語一致 / argv0 除去後の一致 | **False / True**。逐語比較にすると恒真な赤 |
| M-7 | receipt の `toolchain` key (exact) | `cmake_version` / `compiler_path` / `compiler_version` / `module_list` |
| M-8 | login の cmake | `3.22.1`。**登録値は 3.25.0** |
| M-8b | compute (bnode005) の cmake | **`3.25.0`** = 登録値と一致。M-8 は login 限定の現象 |
| M-9 | `floor_protocol.json` の `env_tag` | `pegasus`。linux-baremetal を指す凍結 protocol は不在 |
| M-10 | linux-baremetal の calibration | `acquisition_receipt` を持たない (`schema_version` = None) |
| M-11 | 全文どうしの version body 一致 (login) | 登録値 = live cc = live cxx で **True** |

### 検査結果

- 焦点 10 file = **494 passed / 2 skipped / rc=0** (計算ノード)
- provenance 全史監査 = rc=0 (2463 件、新規違反なし)
- 変異 = 登録 14 件。**12 KILLED / 1 SURVIVED (M03) / 1 MISMATCH (M07)**。
  M07 は「gate 呼び出しの消去」で、予測 1 node に対し実測 63 node。予測が狭すぎただけで
  殺されたことは決定的。M03 は下記の erratum を経て **KILLED** へ確定。
- 変異 erratum (両層同時) = M03X **KILLED** (実測 3 node)。
- 変異 再照準 = M03 単独 **KILLED**、実測 node は新設した単一理由テスト 1 件のみで期待と完全一致。

### 親が切り分けた波及 (real だが本 wave が新たに壊したものではない)

`toolchain_binding.py` を silo の `_runtime_module_paths()` 閉包へ加えたため
`runtime_modules_sha256` が変わる。既存 silo evidence (job 873920) の保存値
`6327347600d1…` は、**本 wave 着手前の閉包 (22 path) の算出値 `c9b65f4b6951…` とも一致しない**。
既に別要因で drift 済みであり、本 wave が新規に拒否を生むわけではない。

### dev-wave 改善候補 (段 8 で裁定)

- 段 6 review の初回 2 本を `--lane` + `--reasoning` 付きで投入し、両方 rc=2 で即死した
  (`--lane` は consult 専用、`--reasoning` は review/focus で指定不可)。
  **どちらも `DW-O01` に明記されており読み落としは親の過失**だが、`DW-O01` は
  「prompt 非空を先に検査し」までしか事前検査を要求していない。
  同日に別 wave も同型で 2 本空費しており (memory に記録済み)、`DW-G03` の独立 2 例が成立する。

## 次の一手差分

### 更新

- [T-783] **P1・S-1〜S-4 を実装済み。残るのは S-3 (a) の attempt 脚と、S-2 の成果物側 (B 系)**:
  S-1 (c) 共通 pure helper (`orchestrator/campaign/toolchain_binding.py`、floor 用と silo 用で
  API を分離) / S-2 (a) 現行 calibration の範囲 / S-4 = [T-747] (B) と同一 land、を実装した。
  **未実装は 2 点で、いずれも裁定時点で未見の新事実による** —
  (i) S-3 (a) の attempt 脚 ({{D:toolchain-binding-scope-narrowed}} の 1)、
  (ii) 成果物 (manifest / result) への binding report 追記 (同 2)。
  S-2 の「手順書へ穴を明記」は `docs/phase3-8b-restart-runbook.md` §5 R-4 で果たした。
  base: a193805da2f295faa9ae225b24e55ae58d3cabd32984f022d48923d4bb1d447c
- [T-747] **P1・(B) の toolchain 束縛を実装済み。混用不可を機械検査で固定した (B 系)**:
  `contract.calibration_ref` の calibration の `acquisition_receipt` を derived authority とし、
  床値 build の前に fail-closed で照合する。**`acquisition_receipt` を持たない契約
  (= legacy の `linux-baremetal`) は receipt 不在で拒否**されるため、
  環境・世代をまたぐ床値の混用は build 前に止まる。env contract に field を足していないので
  `contract_sha256` は不変で、発効記録・floor protocol・selector 予測封印の 3 pin は生きている。
  残る非束縛量 (cxx version / cmake path / module_list / bytes hash) は手順書 §5 R-4 に明記した。
  base: 08015aa92bc508f76bb7869510c7d073c03a61ba69335ad69c94e04eb06a0fbf
- [T-748] **P1・W-2 (床値実測) は投入不可を実測で確定。W-1 の再裁定待ちで停止 (B 系)**:
  [T-747] (B) の束縛検査は実装済みだが、W-2 は次の 3 点が独立に塞いでおり投入できない。
  (1) `_assert_official_permitted` (`s8b_floor_campaign.py:207-217`) が official を無条件拒否、
  (2) `assemble_result` (`:2453`) と `:3174` により **pilot は `eligible_for_refreeze=False`** で
  再凍結に使えない、(3) `tools/pegasus/floor_campaign.sh:962` は `--mode official` 固定で
  pilot 経路が無い。W-1 = [T-781] は worklog 413 で「official は空集合のまま維持・保留終端」と
  裁定済みであり、**第 1 世代で実測する方針は維持したまま W-1 の再裁定を待つ**。
  base: 923e6902ba7062b0baa20971c6809d873b1f62c0cbd47a089269510ea58daee2

### 新規

- {{T:floor-attempt-toolchain-provenance}} **P1・ユーザー裁定待ち (B 系)**:
  S-3 (a) の attempt 実測値の脚を実装するか。新事実 2 件つき。
  材料 = `output/insights/2026-08-11_t783-toolchain-binding/package.md`。
- {{T:floor-artifact-toolchain-report-schema}} **P1・ユーザー裁定待ち (B 系)**:
  成果物 (manifest / result) へ binding report を載せるか。exact-key consumer の改修を伴う。
- {{T:toolchain-authority-completeness}} **P2・ユーザー裁定待ち (B 系)**:
  cxx version / cmake path / module_list / bytes hash を authority へ加えるか (calibration 再発行)。
- {{T:toolchain-binding-other-producers}} **P2・ユーザー裁定待ち (B 系)**:
  floor と silo ladder 以外の producer へ束縛を広げるか。
