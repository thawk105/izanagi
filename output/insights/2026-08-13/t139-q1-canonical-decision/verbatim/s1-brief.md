# 段 1 brief — dev-wave-t139-q1-canonical-decision

```text
wave: dev-wave-t139-q1-canonical-decision / branch worktree-dev-wave-t139-q1-canonical-decision
作成: 2026-08-13 07:4x JST
種別: docs-only (canonical decision fragment 1 本の起草)
親: dev-wave manager (Claude)
```

## 1. scope

**第 7 束 Q1 (a) が命じた「1 本の canonical decision」を起草し、`docs/spool/` の decisions
fragment として land する。** 実装差分ゼロ。

**この decision が閉じるもの (canonical worklog エントリ 516 の逐語に従う):**

- **Q1 (a):** 承認済み文書だけでは受理述語が一意に決まらない 4 件 (B1〜B4) を 1 本で閉じる。
- **Q2 (a):** approval manifest の表現 = 固定 envelope + role 別 namespaced projection。
  `alpha_reservation` は manifest の exact 閉包に**含めない**。

**scope 外 (手を出さない):**

- pilot 投入前提 #4〜#6 の実装 (`PreregBinding` / `resolve_effective_preregistration` /
  receipt writer / semantic validator / conformance vectors)
- `submit_pilot` / `submit_main` / PBS driver / collector
- **D292 の投入禁止の解除** (K3 (a) により投入経路 wave と同一 land に据え置き。本 wave は開けない)
- D264 のテスト期待値の変更 (「実 binding の正例が通るまで変えない」)
- 承認済み blob (`record-items-v2.md` / `receipt-schema-v1.json` ほか) の bytes 変更

## 2. 確定済みユーザー裁定 (根拠)

| 出所 | 内容 |
|---|---|
| 第 7 束 (user、2026-08-13 00:0x〜00:1x JST) | T-139 Q1〜Q6 全問を親推奨どおり確定。Q1 = (a) / Q2 = (a) |
| canonical worklog エントリ 516 | 上を canonical 化。「次は Q1 の canonical decision 起草 → 投入経路 session」 |
| 一括裁定 (2026-08-12) | Q3 = 解禁側 (投入禁止の解除自体は別 decision を要する = D292) |

**依頼文との差 (F31 を適用した):** 依頼文は Q1 (a) を「固定 envelope + namespaced projection」と
要約したが、それは **Q2 (a)** の内容である。canonical 本文 (エントリ 516) が定める Q1 (a) は
**受理述語の穴 4 件**である。本文を優先し、両方を 1 本に収める — Q1 (a) の理由自身が
「4 件は同じ承認 payload に触れるので 1 本にまとめるのが最も壊すものが少ない」と書いており、
Q2 はその payload の表現を決める問いだからである。

## 3. 不変条件 (破ったら停止)

1. **承認済み bytes を 1 bit も変えない。** D282 の `approved_blobs` 6 件と D291 の 2 件は
   exact bytes 承認済み。本 decision は**文書上の契約だけ**を定める。
2. **D292 の投入禁止を解除しない。** 本 decision は解除 decision ではない。その旨を本文へ明記する。
3. **D234 の (i)〜(vii) を 1 つも落とさない。** 落とすこと自体が受理集合を広げる。
4. **恒真な gate を書かない (規律 2)。** 「受理集合が空のまま『実装済み』と記録する」ことを
   本文で明示的に禁じる。D234 の実装境界と同型の文を置く。
5. **保証の上限を誇張しない (規律 3)。** validator が保証できるのは「記録された窓・間隔・時刻が
   相互に整合すること」までで、「実際に他の作業が無かったこと」は保証しない。
6. 台帳 3 本 (worklog / decisions / failures) は直接編集せず `docs/spool/` の fragment で書く。

## 4. `DW-O13` — gate 入力の実在 (実成果物で確認済み)

`output/insights/2026-08-11_t139-manifest-land1/receipt-schema-v1.json` (43,106 bytes) を
機械的に読んで確認した結果:

| ID | 主張 | 実測 |
|---|---|---|
| B1 | `CMakeCache.txt` の raw pointer が無い | **確認。** `cmake_cache_raw` = 0 件。`performanceCompileStock.required` は `configure_argv` / `compile_commands` / `cmake_cache` を持つが、`performanceCmakeCache` は `{trace, add_analysis}` の 2 boolean だけの値 object で `fileRecord` ではない |
| B2 | attempt ごとの `intent_ref` は実在、母集合 authority が無い | **確認。** `intent_ref` = 2 件実在。index / namespace / `O_EXCL` 発行履歴を表す定義は無い |
| B3 | receipt-set の discovery 契約が未定義 | **確認。** `peer_receipt` = 0 件、`receipt_set` = 0 件 |
| B4 | transcript の raw pointer は実在、grammar と authority binding が無い | **確認。** `admissionTelemetry.kind` に `j_derivation` があり `receipt: fileRecord` を持つ。canonical byte grammar を定める field は無い |

## 5. 親の provisional 裁定 (P1〜P5) — **攻撃対象**

以下は親の暫定判断であり、段 2・段 3 はこれを攻撃してよい。

- **(P1) Q1 と Q2 を 1 本の decision に収める。** 根拠は §2 の末尾。
  → 攻撃点: 「1 本にすると Q2 の envelope 契約が Q1 の 4 件の未決部分に人質を取られる」型の反論。
- **(P2) K1 の残余確認の結論 = D320 の見送り既定は本 decision にかからない。**
  文書照合の根拠は 2 つ。(i) 第 7 束 (2026-08-13) は D320 (2026-08-12) より**後発**で、
  T-139 について名指しで (a) を選んだ**個別裁定**である。D320 自身が「既定で見送り」と書き、
  「既存機構の撤去・緩和は個別裁定で行う」として既定が個別裁定に優先しないことを明記している。
  (ii) 本 decision は**文書上の契約だけ**を定め、D320 が列挙する見送り対象 (凍結 pin の保全、
  承認への署名と外部 trust root、commit への束縛、公表台帳の原子性・予約 writer、
  bytes 同一性の恒久証明) を**1 つも新設しない**。
  → 攻撃点: 「approval manifest そのものが『commit への束縛』に該当し、D320 が見送ったもの」
  という読み。これが成立するなら実装差分ゼロの precheck として裁定へ返す。
- **(P3) 本 decision は契約だけを定め、実装境界を D234 と同型に明記する。**
  「本決定をもって semantic validator を実装した / 投入 gate を機械配線したと記録してはならない。」
- **(P4) B1〜B4 の手当ての型は同じでない。** decision は型ごとに別々の契約を書く。
  - **B1** = 承認済み schema に無い raw pointer の追加。承認済み bytes は変えられないので、
    **新 schema 版 + 新しい承認 payload** という経路になる (旧版を書き換える経路は禁じる)。
  - **B2** = producer 権限外の intent 母集合 authority と canonical namespace の新設。
  - **B3** = receipt-set の discovery / consumer 契約の確定 (schema 変更を伴うとは限らない)。
  - **B4** = `j_derivation` transcript の canonical byte grammar と authority binding の確定。
  → 攻撃点: B1 の「新 schema 版」経路が D282 の `forward_supersedes` 機構と整合するか。
- **(P5) `alpha_reservation` は manifest の exact 閉包に含めず、resolver が D282 payload から
  直読する** (第 7 束が明示。RP-1 の裁定と整合)。

## 6. `DW-G05` — 成果物影響 (これを実装しないと何がどう変わるか)

**この decision が台帳に無い限り、`submit_pilot` の受理述語は承認済み文書だけからは一意に
決まらない。** 結果として semantic validator の §7.1(12) (申告値と実体の 3 者一致)、
§7.1(16) (`intent_ref` / marker の create-only 性)、§6.1 (stage 間整合)、§4.12 / §6.8
(transcript 再計算と `J` の一致) が実装不能のまま残り、**paired study の適格 verdict が
1 件も生成されない** (D234「研究状態への影響」)。すなわち T-139 の RF study の
certified 選択結果・レポート・試行台帳がいずれも空のままになる。

## 7. 分割方針と成果物

**実装面がゼロなので Codex 実装子は起動しない。** ただし本 decision は**受理述語 (受理集合) を
定める**ので、`DW-C00` により敵対検証子は省かない。

| 段 | 子 | 役割 |
|---|---|---|
| 2 | codex read-only 1 本 | decision 本文の骨格を file:line 粒度で起草 |
| 3 | codex read-only 2 本 (sol / luna) | 異なるレンズで plan と本 brief を攻撃 |
| 4 | 親 | real/refuted 裁定、plan v2 |
| 5・6 | — | 実装面ゼロ。親が docs 本文を執筆 (docs-only 本文は親が編集してよい) |
| 7 | 親 | spool fragment (decisions 1 + worklog 1)、insights 逐語 |
| 9 | 親 | 受入全走 → land |

**成果物:**
- `docs/spool/` の decisions fragment 1 本 (本 decision)
- `docs/spool/` の worklog fragment 1 本
- `output/insights/2026-08-13_t139-q1-canonical-decision/` に逐語と裁定パッケージ
- 変異 matrix は**免除** (`DW-S04`: 実装差分ゼロ)。**受入全走は免除しない。**

## 8. 環境

- 受入・検査は Pegasus login node の worktree 内で行う (docs-only なので計算ノード不要)。
- 受入 lease は `tools/dev_wave_wait.py acceptance` で claim する。

## 9. 段 1 で判明した scope 外の real 所見 (裁定へ返す)

- **main が全 background job wave の起動 gate を恒久的に赤にしている。**
  `docs/handoff/2026-08-13-known-red-octopus.md` は commit `aedc04ec` (2026-08-13 05:18 JST) で
  main に tracked のまま復元された — land が `docs/handoff/` 直下を control-plane path として
  守り、削除を含む tip を rc=21 で拒否するためである。一方 `DW-O20` が背景 job に必須とする
  `check_wave_startup.py --external-handoff <path>` は、`--external-handoff` を渡すと
  `--forbid-worktree-handoff` を含意し (`tools/check_wave_startup.py:350`)、
  `docs/handoff/` 直下に README.md 以外があると `NG: worktree-local handoff remains` で rc=1 になる。
  **main 単独で再現する** (main checkout で同 command を実行して確認済み)。
  本 wave は untracked handoff を 1 件も作っていない (`git status --short docs/handoff/` = 0 行) ため、
  `DW-O20` の趣旨 (自分の untracked 残置を持ち込まない) は満たしている。
