# [T-529] 契約世代の活性化権限 — 実装 wave (実装しないで終端)

wave branch: `worktree-dev-wave-t529-activation-impl`
基準 commit: 364c6067 (段 1〜4 を通じて worktree は clean)

**段 4 で本 wave では実装しないと裁定した。** 実装差分がないため変異 matrix と受入全走は対象外である。
設計の正本は前 wave の凍結 `output/insights/2026-08-06_t529-activation-authority/` (6 択一表) で、
本ディレクトリはその後の**依存解消と、実装できない理由の更新**を持つ。

## ファイル

| ファイル | 中身 |
|---|---|
| `s1-brief.md` | 親 brief。段 1 の前提実測 6 点と provisional 裁定 P1〜P5 |
| `s2-plan.md` | 段 2 codex プラン起草 (`gpt-5.6-sol`、`reasoning=max`、`sandbox=read-only`、rc=0) |
| `s3-lensA.md` | 段 3 レンズ A — 正しさ境界と不変条件 (must-fix 4 / should-fix 3) |
| `s3-lensB.md` | 段 3 レンズ B — scope 被覆・整合・実効性 (must-fix 6 / should-fix 3 / nit 1) |
| `s4-adjudication.md` | **段 4 裁定 (正本)**。親の裏取り 3 点と、ユーザーへ返す択一 5 件 |

## この wave で確定したこと

### 依存 [T-574] は D196 の理由 (a) を充足させた (親が実 artifact で確認)

合法な後継世代 g2 (calibration path/sha のみ差分) を current に据えたうえで committed
`output/s8b-freeze/floor_protocol.json` を通すと:

- historical 経路 (`s8b_ratified_freeze._resolve_historical_contract_sha256`) は **ACCEPT** し、
  記録 hash `e576e9cd1369` へ解決した。
- current 経路 (`_resolve_current_contract_sha256`) は REJECT した。これは D202 が意図した
  live admission の current 束縛であり、proof chain の破壊ではない。

すなわち設計凍結の実測 2 (「g2 を活性化すると既存 frozen proof chain が壊れる」) は、
T-574 の配線後は成立しない。**依存 wave (277) の「blocker は外れていない」という総括のうち、
配線に関する部分はこの実測で狭められる。**

### しかし D196 の理由 (b) は充足していない — 正例は依然として永久 fuse と区別できない

`DW-G04` が要求する発火 artifact path も計測 ID も書けない。module 属性 patch による
2 世代注入は既存慣行だが、それは import 時の初期化経路
(`_build_registry` → `validate_generations` → `REGISTRY`) を駆動しないため、
複数世代を import 時に拒否する実装でも同じ正例が通る。

### 裁定された設計が 2 入口で実現できない (裁定時点で未見。親が裏取り)

| # | 事実 | file:line |
|---|---|---|
| 1 | floor の公式経路は driver の stdout / stderr / launch marker を書いた**後**に `--mode official` を起動する | `tools/pegasus/floor_campaign.sh:882-894` |
| 2 | 適格性 driver は `.git` を持たない git-archive 済み source stage から起動され、authority root は CLI 解析後にしか判らない | `tools/pegasus/t126_qualification.sh:736-738` |
| 3 | `env_attestation` は module 冒頭で `env_contract` を import するため、`env_contract` 初期化中に較正検査を呼ぶと部分初期化中の module へ到達する | `orchestrator/campaign/env_attestation.py:25` |

1 と 2 により、裁定 (2) の「6 入口が最初の書込み前に検査する process-local gate」は
この 2 入口では Python 層に立てられない。

## 親の実測のうち覆ったもの (段 3 が 2 レンズ独立に指摘)

- **R1 と T-529 裁定 (1) は別の問いである。** 裁定 (1) は *activation record* の trust root、
  R1 は *記録 hash だけで当時 active だった証明なしに世代を選んでよいか*。
  親は前者を後者の回答と読んだ。**R1 は未裁定のままである。**
- **「正例は書ける」は主張しすぎだった。** 上記のとおり import 時経路を駆動しない。
  親自身の probe が import に成功したのは registry が 1 世代だったからである。

**親の一般化が段 3 で覆るのはこれで 3 wave 連続である。**

## ユーザー裁定待ちの択一 5 件

`s4-adjudication.md` の表が正本。骨格を決めるのは A (R1) と B (`DW-G04` を上書きするか) で、
この 2 つが決まらない限り実装を再開しても land できない。

| # | 択一 | 親の推奨 |
|---|---|---|
| A | R1 — 記録 hash を、当時 active だった証明なしに世代選択の権威としてよいか | (b) historical authority を activation chain 上で ever-active な hash に限定する |
| B | `DW-G04` を T-529 に限り上書きするか | (a) 上書きせず、正規 g2 を取得できるまで設計メモに留める |
| C | shell wrapper の pre-write をどう扱うか | (a) certified writer 閉包の新規タスクへ送る |
| D | activation record 間の世代遷移規則 (現案は skip / downgrade / no-op を無制約に受理) | 「各 env は据置または +1」を置く |
| E | authority loader の起動点 (import 時 HEAD 読取りは成立しない) | 述語を共有 leaf へ抽出し、load は CLI 解析後へ遅延する |

## 実装を再開する wave へ引き継ぐ scope 内 real 所見

いずれも実装したら直ちに効くもので、本 wave では実装していない。

- 入口の例外境界の翻訳が未定義 (`ActivationStateError` と `EnvContractError` の対応) — lensB #8
- 新 authority module が env-neutral AST 閉包に入っていない — lensB #9
- S8c condition 12 は新 API を知らないため、activation receipt を C12 証拠と混同しない — lensB #7
- identity 閉包へ加えると新規 T-126 `code_identity` と silo `runtime_modules_sha256` は
  必ず動く。「成果物 bytes は 1 byte も変わらない」は既存 committed file に限った主張である — lensA #5
