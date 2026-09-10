# 段 4 裁定 — [T-244] D121 P5 U-1

親が段 3 所見 (レンズ A: BLOCKER 2 / MAJOR 5 / MINOR 1、レンズ B: BLOCKER 1 / MAJOR 4 / MINOR 3) を
裁定し plan v2 を確定する。

## 1. 中核の裁定 — 名乗りを「public `run_trial` の explicit keyword admission の縮小」に固定する

A-1 (BLOCKER) と B-MAJOR1 は独立に同じ急所を突いた。**real、採用。** 移行先 seam (module 属性) は
拒否対象と同じ能力を同一 process 内で持ち、sentinel も introspection (`__kwdefaults__`) で持ち出せる。
同一 process の private-module 操作は Python では構造的に防げず (gate 自体を書き換えられる)、
D114 (直接反復)・D148 (process 境界) の先例どおり**保証外として正直に列挙する**方針を採る。

- 実装するのは「正式経路 (`provider_kind == "claude-headless"`) での **explicit keyword 注入の拒否**」だけ
- **非保証を新 D と runbook に明記する**: module 属性の再束縛、private sentinel の持込み
  (introspection 経由)、sentinel を束縛した `partial` / wrapper、同一 process 並行実行中の差替え
  (A-6)、保存済み artifact からの事後判定 (B: schema に driver identity field が無いことを実測済み)
- 「caller 差し替えを閉じた」「P5 第 1 要件を閉じた」とは**名乗らない** (D148 決定 (4) と同型)
- runbook の文言は「fixture と直接入口だけが対象外」とせず、残存経路を全列挙する (B-MAJOR4 採用)

## 2. `type(provider_kind) is str` を gate 前に要求する (A-2 BLOCKER、採用)

状態付き `str` subclass が membership 検査と gate 比較を選別的に通せる。D114 の
`int` subclass → exact 型の先例に従い、`:1548` の検査を `type(provider_kind) is not str` で
先頭固定する。これは既存 P5-1 gate の受理集合にも効くため新 D の射程へ含める。
境界: 負例 = `str` subclass (`"claude-headless"` 基底)、正例 = plain `str` の fixture / claude-headless。

## 3. sentinel 設計の確定 (A-5・A-7・B-MAJOR2、採用 + 一部具体化)

- sentinel 2 個・kwargs 温存・**gate 直後に一様な早期解決** (provider 分岐なし)。B-MAJOR2 の
  provider 別 resolver 案は**不採用** — 分岐が増えるだけで omitted-fixture の意味変更は
  どのみち観測可能であり、変更として新 D に記録し回帰テストで固定する方が単純
- 解決位置の検査: `_finish_trial` (または `_run_workload`) capture で、**入口時点で両値が
  sentinel でなく期待 callable に解決済み**であることを固定する (A-5)
- omitted-fixture 回帰テスト: fixture + kwargs 省略で module 現在値へ解決されることを固定 (B-MAJOR2)
- claude-headless + 省略 + module 属性未差替えの解決検査 (capture 方式、実走なし) で
  「省略時は `trigger.drive_iteration` / `_preview` へ解決」を固定する (A-6 の「production default の
  証拠」はこのテストが担い、移行後の P1/P2 は「claude-headless + 省略が gate を通る」証拠とだけ数える)
- signature 既定値が opaque object へ変わる観測可能変更は新 D に記録する (A-7)

## 4. 境界テストの拡張 (A-3・A-4、採用)

- 負例値域: 各 seam × {現在の既定関数そのもの、別 fake callable} + 非 callable 1 件、
  transport opt-in 構成 (P2 相当) への明示注入 1 件
- 順序固定: (i) providers 拒否が drive/preview 拒否に先行、(ii) U-1 拒否が
  generation 予算・wall・build-site 検査に先行 (`generations` 不正 + 注入で U-1 エラーを期待)
- 無副作用: 負例は `run_root` 非存在に加え、`AttemptJournal` / `ensure_exploration_namespace` /
  `_provider_set` / `_assert_build_site_opted_in` を fail-loud 差替えして非到達を証明する
  (P1 テストの `forbidden()` 既存様式を踏襲)

## 5. scope の確定 (B-BLOCKER1、採用 — 親の scope 拡大として明記)

編集対象: production 1 (`p3_autonomous_workload_trial.py`)、テスト 2
(`test_claude_transport.py`、`test_role_session_isolation.py`)。docs は親が編集:
`docs/phase3-s8c-autonomous-trial-runbook.md`、`docs/phase3.md` (§1 の全列挙文言)、
新 D fragment、worklog fragment。対象走へ `test_role_session_isolation.py` と
`test_autonomous_trial_completeness.py` を含める。brief の訂正 (段 2 で判明):
P5-1 境界テストの実所在 = `test_role_session_isolation.py:120` (brief の test_p3:698/718 は
build-site 境界)。

## 6. 新 D fragment の骨子 (B-MAJOR3、採用)

新規拒否 / 不変 / 非保証 / 却下案 (kwargs 撤去、関数同一性判定、新 opt-in flag、自己申告
receipt+consumer、provider 別 resolver) / 旧成功形 (`_dry_drive` kwargs 注入) が拒否へ移る境界と
exact default 明示が拒否になる境界 / D148 決定 (2) の drive/preview 部分だけの supersede /
既存 providers gate への `type is str` 前提追加。token / receipt / reservation の語は使わない
(B-MINOR2 採用 — P3 wave の `EventReceipt` を U-2 の証拠として扱わない)。

## 7. 実測の訂正 (A-8・B-MINOR3、採用)

- 「fixture 24+ 箇所」→ **public `run_trial` の fixture 注入 12 call / keyword 22 個** (AST 集計)
- 「成功期待の claude-headless 注入 2 件」は public `run_trial` に限る条件付きで正確
  (internal `_finish_trial` 注入は多数あり、P4 のとおり保証外)
- 移行後、repo 内 production 経路で新 gate は発火しない。防御対象は外部 programmatic caller で
  あり、境界テストの負例が発火を固定する。D148 の恒真 token gate と異なり負例が実在することを
  worklog へ正直に書く

## 8. refuted / 不採用

- A-6 の「P1 の I/O 検出力が落ちる」懸念はレンズ自身が反証 (fail-loud + artifact 同一性は維持)
- B-MAJOR2 の provider 別 resolver 案: 上記 §3 のとおり不採用 (理由も記録)
- 同一 process 並行 thread の差替え (A-6) への機械対策: 不採用、非保証として列挙
  (tracker と同じ process 境界の限界。D148 決定 (4) 先例)

## 9. 変異事前登録 v2 (DW-M01。実装後に old 逐語を確定し DW-M07 で再検証)

plan の M1〜M8, M10, M12 は維持。M9 / M11 を単一 patch・単一期待 node へ再登録 (B-MINOR1):

| ID | 変異 (単一 patch) | 期待 |
|---|---|---|
| M1 | U-1 gate 全体を `if False` | KILLED: 負例 3 件 (drive/preview/両方) |
| M2 | drive 検出項だけ `False` | KILLED: `[drive]` |
| M3 | preview 検出項だけ `False` | KILLED: `[preview]` |
| M4 | 検出の `or` → `and` | KILLED: `[drive]`・`[preview]` |
| M5 | drive の既定解決を `if False` | KILLED: sentinel 到達検査 (解決位置テスト) |
| M6 | preview の既定解決を `if False` | KILLED: 同上 |
| M7 | 既存 providers gate を `if False` | KILLED: providers-only 境界 (既存)。冗長 transport 条件 :1565 は credit 外 (DW-M03) |
| M8 | provider 限定を外し全 provider へ適用 | KILLED: fixture 注入正例 (過剰拒否検出) |
| M9 | drive 比較 1 箇所だけ `is not _DRIVE_NOT_PROVIDED` → `is not trigger.drive_iteration` | KILLED: omitted 正例 (過剰拒否) — 単一 node で登録 |
| M10 | U-1 gate を `run_root.mkdir()` 後へ移動 | KILLED: 無副作用検査 (fail-loud 非到達) |
| M11 | 早期解決を `_run_workload` 冒頭へ遅延 | KILLED: 解決位置テスト (入口 sentinel 非残存) |
| M12 | U-1 gate を P5-1 providers gate より前へ | KILLED: precedence テスト |
| M13 | `type(...) is not str` → `not isinstance(..., str)` | KILLED: str subclass 負例 |

各変異は実装後の統合 commit 上で anchor (old 逐語) を確定し、手前 mask 検査 (単一理由性) を
`tools/mutation_harness.py` の spec に書く。受入正例 (過剰拒否検出) は M8 / M9 が担う。

## 10. plan v2 = 段 2 plan + 本裁定 §1〜§9 の差分。実装子への指示は s5/prompt.txt が正本。
