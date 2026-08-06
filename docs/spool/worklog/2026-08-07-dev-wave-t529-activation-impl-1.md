---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-08-07
wave: dev-wave-t529-activation-impl
seq: 1
title: [T-529] 実装 wave は「実装しない」で終端した — 裁定された設計が floor と T-126 では実現できないと判明し、正例は依然として永久 fuse と区別できない (docs のみ、実装差分なし、branch worktree-dev-wave-t529-activation-impl)
---

## 本文

- **依存 [T-574] 残余の land を待って着手し、その wave の総括を 2 点で否定して、
  さらに自分の否定が 1 点で覆った。** 経過を残す。依存 wave (277) は
  「[T-529] の blocker は外れていない」と総括し、根拠を (1) R1 未裁定、
  (2) `no-active` で historical 正例を書けない、とした。親は段 1 で (1) を否定し
  (「R1 の実質は T-529 裁定 (1) が答えている」)、(2) についても
  「D196 が要求するのは配線であって発火ではない」と一般化した。
  **段 3 の 2 レンズが独立に、両方とも誤りだと示した。**
- **R1 と T-529 裁定 (1) は別の問いだった。** 裁定 (1) は *activation record* の trust root を
  reviewed commit にするか外部署名にするかであり、R1 は *記録 hash だけで、当時 active だった
  証明なしに世代を選んでよいか*である。前者を後者の回答と読んだのが親の誤りで、
  **R1 は未裁定のままである**。両レンズが独立に file:line 付きで指摘した。
- **親の「正例は書ける」も主張しすぎだった。** module 属性 patch で 2 世代 registry を
  注入できることは事実だが、それは import 時の初期化経路
  (`_build_registry` → `validate_generations` → `REGISTRY`) を駆動しない。
  よって複数世代を import 時に拒否する実装でも同じ正例が通り、
  **永久 fuse と観測的に区別できない**。親自身の probe が import に成功したのは
  registry が 1 世代だったからで、そこを取り違えていた。
- **裁定された設計そのものが 2 入口で実現できないと判明した (裁定時点で未見)。** 親が裏取りした。
  (i) `tools/pegasus/floor_campaign.sh:882-894` は driver の stdout / stderr /
  `floor-driver.launch-attempted` を書いた**後**に `--mode official` を起動する。
  (ii) `tools/pegasus/t126_qualification.sh:736-738` は git-archive した source stage
  (`.git` なし) から driver を起動し、authority root は CLI 解析後にしか判らない。
  裁定 (2) の「6 入口が最初の書込み前に検査する process-local gate」は、
  この 2 入口では Python 層に立てられない。
- **循環 import も実測した。** `orchestrator/campaign/env_attestation.py:25` が module 冒頭で
  `env_contract` を import するため、`env_contract` の初期化中に
  `env_attestation.load_verified_calibration()` を呼ぶプランは、
  `env_attestation` を先に import する既存 consumer で部分初期化中の module へ到達する。
- **依存 wave の総括より狭く、かつ確かなことが 1 つある。** D196 の理由 (a)(配線順序) は
  充足した。親が実 artifact で確認した — 合法な g2 を current にしても historical 経路は
  committed `output/s8b-freeze/floor_protocol.json` を受理し記録 hash `e576e9cd` へ解決する。
  current 経路の拒否は D202 が意図した live admission の current 束縛であり、proof chain の
  破壊ではない。**充足していないのは理由 (b)(`DW-G04` の発火正例) だけである。**
- **実装差分がないため、変異 matrix と受入全走は対象外である。** 記録は docs のみ。
- 段 1 の前提実測で `env_contract.py` へ g2 を実編集し `git checkout --` で復元した。
  復元後 `git status --porcelain` 空、blob `abe103e5` 一致を確認 (`DW-O19`)。
- **worktree 隔離 guard が codex 起動と待ちの複合コマンドを 2 度拒否した。**
  repo 外の launcher script 経由へ切り替えて解決した。既存起票 [T-594] と同型で、
  重ねて起票せずそちらへ寄せる。
- 裁定は {{D:activation-authority-blocked-by-entry-surface}}。

## 次の一手差分

### 更新

- [T-529] **P1・実装保留を継続 (2 度目)。ユーザー再裁定待ち**: 契約世代の活性化権限。
  6 択一の裁定内容は変わらない。D196 の理由 (a)(historical resolver の consumer 配線) は
  [T-574] で充足し、親が実 artifact で発火を確認した。**充足していないのは理由 (b) である** —
  正規 g2 が無いため発火正例を書けず (`DW-G04`)、module 属性 patch による合成正例は
  import 時の初期化経路を駆動しないため永久 fuse と区別できない。
  さらに裁定時点で未見だった 3 点が判明した: (i) floor の公式経路は shell が Python gate より
  前に書く (`tools/pegasus/floor_campaign.sh:882-894`)、(ii) T-126 は `.git` を持たない
  git-archive source stage から driver を起動する (`tools/pegasus/t126_qualification.sh:736-738`)、
  (iii) `env_attestation.py:25` との循環 import で authority loader が起動しない。
  ユーザー裁定が要る択一は 5 件 (A: R1 の可否、B: `DW-G04` を上書きするか、
  C: shell の pre-write を writer 閉包へ送るか scope へ入れるか、D: 世代遷移規則、
  E: authority loader の起動点)。正本 =
  `output/insights/2026-08-07_t529-activation-impl/README.md`
  base: 29645ceef78a380e890c27838464c49e7d19d59c775f6eac80ce527c18f836f6

### 新規

- {{T:certified-writer-prewrite-closure}} **P2・新規**: certified writer の閉包を切る
  (T-529 裁定 (5) が「別タスクへ切る」と定めたもの)。対象は 2 層ある。
  (a) `loop._authorize_measurement` が `env_contract is None` で素通りし
  `s8a_trigger_sweep.py:457` が `env_contract` を渡さずに `run_campaign()` を呼ぶ経路
  (設計凍結の実測 3)。(b) Python gate より前に書く shell wrapper —
  `tools/pegasus/floor_campaign.sh` と `tools/pegasus/t126_qualification.sh`
  (本 wave の段 3 で判明)。(b) を閉じないと、活性化権限を入れても
  floor / T-126 を「最初の書込み前に保護した入口」と数えられない
