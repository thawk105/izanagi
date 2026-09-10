# 親 brief — [T-529] 契約世代の活性化権限 (実装 wave)

worktree: `/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t529-activation-impl`
基準 commit: 364c6067 (branch `worktree-dev-wave-t529-activation-impl`、tree clean)
設計凍結 (正本): `output/insights/2026-08-06_t529-activation-authority/README.md` の 6 択一表

## 確定済みユーザー裁定 (2026-08-06、発話「基本的には推奨通り」。逐語は rulings-inbox §30)

6 択一とも起草者推奨どおり。(1) trust root = 「レビュー済み git commit」と明示し非偽造性の主張を
実態へ合わせる (署名済み external evidence は導入しない) / (2) 入口 receipt は本 wave では
**process-local な制御フロー gate** に限定し durable な versioned identity は別 wave /
(3) fuse 解除の前に historical resolver を consumer へ配線する / (4) `linux-baremetal` g1 は
exact contract hash で grandfather / (5) certified writer の閉包は別タスク / (6) silo 昇格入口は
「未実装」と名乗る。命名は D197 (`activation_serial` / `activation_state_sha256` /
`previous_activation_state_sha256`)。

## 依存の決着 — 段 1 で親が実測した 6 点 (すべて 364c6067、すべて攻撃対象)

1. `env_contract.py` の blob は `abe103e5` で設計凍結時と同一。前提は陳腐化していない。
2. **fuse は今も発火する。** `_build_registry()` の pegasus へ g2 を実編集で足すと import 時に
   `EnvContractError: 活性化権限 ... 2 世代目の登録を fail-closed で拒否する`。
   `git checkout --` で復元し、`git status --porcelain` 空・blob `abe103e5` 一致を確認 (DW-O19)。
3. **設計凍結の実測 2 (g2 活性化で凍結 proof chain が壊れる) は T-574 の配線後は成立しない。**
   合法な successor g2 (calibration path/sha のみ差分) を current にしたうえで committed
   `output/s8b-freeze/floor_protocol.json` を通すと、historical 経路
   (`_resolve_historical_contract_sha256`) は **ACCEPT** し記録 hash `e576e9cd` へ解決した。
   current 経路 (`_resolve_current_contract_sha256`) は REJECT だが、これは D202 が意図した
   live admission の current 束縛であり proof chain の破壊ではない。
4. `load_ratified_freeze()` は今日 `RatifiedFreezeError(no-active)`。ただしこれは v2 freeze が
   未発効なためで、世代機構とは独立の欠落 ([T-607])。
5. **[T-574] world wave が言う blocker (1) (R1 未裁定) は成立しない。** R1 の実質
   (記録 hash を世代選択の権威にしてよいか) は T-529 裁定 (1) が答えている。R1 は T-574 側 (262) で
   起票され、その後 (266) で T-529 の文脈で裁定された。別 ID で裁定された項を取りこぼした形。
6. **2 世代 registry の試験注入は可能。** module 属性 patch は既存慣行
   (`test_env_contract.py:618-632`)。親の probe はこの seam で production コード経路を実駆動した。
   設計凍結の「実装しない理由 3」(正例が永久 fuse と区別できない) はこの点で覆る。

## 親の provisional 裁定 (P1〜P5。親の暫定判断であり段 3 の攻撃対象)

- **(P1)** D196 (3) の前提は充足済み。D196 が要求するのは *配線* であり、T-574 が配線先 0 件を
  確定し、実測 3 が実 artifact 上で発火を示した。T-574 world wave の blocker (2) は D196 の
  配線要件を `DW-G04` の発火要件と混同している。**ここが本 wave 最大の争点**。
- **(P2)** `DW-G04` は T-529 自身の gate には今日も不充足 (正規 g2 が存在せず production の
  発火 artifact path を書けない)。しかしこれは設計凍結の「実装しない理由 1」として裁定時に
  ユーザーの目前にあった既知事実であり、`DW-S04` の「裁定時点で未見の新事実」に当たらない。
  よって停止理由にしない。正例は実測 6 の seam による合成 g2 で書く。
- **(P3)** fuse は撤去でなく置換する。新条件 =「activation record が活性化していない generation は
  current にできない」。世代 1 本の現状で受理集合が不変であることを positive control で示す。
- **(P4)** 本 wave は成果物 bytes を 1 byte も変えない (裁定 2 の process-local 限定の帰結)。
  よって `DW-O10` は非適用。`env_contract.py` は `REQUIRED_CODE_IDENTITY_PATHS` に入るが
  digest は実行時再計算で、code identity を byte 固定する committed 成果物は 0 件 (親が実測)。
- **(P5)** silo は入口として結線しない (裁定 6)。`loop.py` の `env_contract=None` 迂回も本 wave 外
  (裁定 5)。入口は floor=`s8b_floor_campaign.py`、oracle=`s8b_oracle_driver.py` +
  `s8b_oracle_report.py`、selector=`s8b_prediction_runner.seal()`、適格性=`t126_driver.py:899`、
  P3 を対象候補とする (設計凍結が brief 暫定案を訂正した同定)。

## 不変条件 (触らない)

- `ExecutionEnvironmentContract` の field 集合・`_canonical_obj()`・既存 2 env の
  `contract_sha256` を 1 bit も動かさない (D176)
- 既存 committed 成果物の bytes を変えない。`lookup()` signature と `REGISTRY` の公開形も現行のまま
- 正しさゲートを緩めない。受理集合を広げるならその広がりを明示し positive control を添える
- D203 の語彙禁止は生きている — `versioned predicate dispatch` をコード・docstring・テスト名・
  台帳で使わない

## 成果物影響 (DW-G05 — 実装しない場合に何が変わるか)

- 活性化権限が無いまま: fuse が残り較正の再取得が永久に不能。certified 選択が参照する env 契約
  hash が旧較正に固定され続ける (U-2 の全成果物)
- (P3) を誤り fuse を単に撤去: 正規 publish を通らない較正を source へ足すだけで current にでき、
  certified 成果物の env 契約 hash が無検査で動く
- (P4) を誤り成果物 bytes が動く: 既存 committed proof chain の参照が一斉に無効化される
- (P5) を誤り silo を結線: 入口被覆率の過大報告になる (裁定 6 が禁じたもの)

## 分割方針 (段 5)

- 単位 A: `env_contract.py` + 新 activation module + その test
- 単位 B: 入口の receipt 結線 + その test

ファイル所有を重複させない。統合事故を嫌う場合は親の裁量で単一単位へ落としてよい (T-574 の先例)。
