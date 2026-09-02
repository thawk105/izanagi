---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-09-02
wave: dev-wave-t2102-b4-reference-tps-domain
seq: 1
title: [T-2102] B-4 registry の reference_tps を有限十進有理数へ狭めた — 防壁を守る側の must-fix は回避不能で、probe が期待変異を 2 件訂正した (コード + テスト + insight、branch worktree-dev-wave-t2102-b4-reference-tps-domain、変異 6/6 KILLED)
---

## 本文

- **ユーザー裁定 (worklog 1184) の択 α を実装した。** 根拠は D1344 充足ではなく周辺実測に基づく
  上書き裁定であり、D1424 決定 4 の拘束はすべて効かせた。配置の択一は {{D:b4-finite-decimal-registry-only}}。
- **D1424 が名指しした must-fix (M12 の再定義) は、回避不能であることを実コードで確認した。**
  現行 M12 の fixture は `issue_b4_prerun_publication` 経由で registry の `_validate_attempt` を
  2 経路で通る。述語を registry へ置くと `(1,3)` は publication が作られる前に落ち、producer の
  十進 token 化に到達しなくなる。registry 拒否期待へ移せば丸め禁止の分岐が無検査になり、
  恒真な保証になる。詳細は {{D:m12-producer-side-redefinition}}。
- **段 6 の敵対レビューが、再定義の穴を 1 件見つけた。** 差し替えた `_fraction_token` が実際に
  呼ばれたことを固定しておらず、production 側の呼出しそのものを例外送出へ置き換える変異が
  素通りする状態だった。正例対照も失われていた。fix で両方を閉じた。
- **述語の射程は「完全一致」と書かない。** 巨大な有限十進 `(1, 2**6200)` は新述語を通って封印
  できるが、producer では桁数上限により `EVIDENCE_SCHEMA` になる。D1424 が述語を名指ししており、
  該当値を生む producer も存在しないため本 wave では埋めず、残差として記録した。
- **probe 走が親の解析を 2 件訂正した。** 「2 除去ループ削除」「5 除去ループ削除」の期待赤を
  親は正例 1 件と解析で導いたが、実測では M12 も赤になった。M12 の fixture の `reference_tps` の
  既約分母が 10 だったためである。本走の spec は probe の観測 node から再構成した。
- **事前登録した 7 変異のうち 1 件を DW-M03 に従って外した。** 述語の恒偽化は registry test が
  ほぼ全件赤になり過剰決定で、単独変異の証拠にならない。同じ保証は単一理由の 2 件が担う。
- **親 brief と段 4 裁定の記述誤りを 7 件、子の指摘で訂正した。** 特に「201 試行後に
  `EVIDENCE_SCHEMA` で失う」は誤りで実際は `DECIMAL_NOT_TERMINATING`、
  「production の既存 artifact では発火しない」は production registry が 0 件なので恒真だった。
- 実装子と fix 子はいずれも codex sandbox の制約で pytest を開始できず、正しく「実装済み・未実走」と
  申告した。実測はすべて親が行った。
- `tools/dev_wave_submodule_init.py` の 1 回目失敗は F810 の型だった。本 wave では根本原因の
  候補 (tool 内部の 30 秒 deadline) を特定し、同 F への再発として記録した。

## 次の一手差分

### 完了

- [T-2102] registry の受理値域を有限十進有理数へ狭める実装を land した。述語は
  `_validate_attempt` のみ (択 A)、M12 は producer 側の直接検査へ再定義済み。
  remaining: none
  base: 0969a47cd44e1aad7915a72025047d9222c76b43e9de2c940f236fa6f0cc4c8e
