# 段 1 brief — dev-wave 段 2 (plan) の codex model を luna へ

wave = `dev-wave-t1132-stage2-luna` / branch = `worktree-dev-wave-t1132-stage2-luna`
親 = background job 43f88b61 / 起票 2026-08-18 13:20 JST

## scope

dev-wave 段 2 (プラン起草) の codex model を `gpt-5.6-sol` から `gpt-5.6-luna` へ変える。
`reasoning=max` と `sandbox=read-only` は現行のまま。**動かす変数は model ひとつだけ。**
段 3 / 段 5 / 段 6 の model・effort、lane 名 (`sol` / `luna`) は変えない。

## 確定済みユーザー裁定

2026-08-18 ユーザー指示「gpt5.6sol を使っているところを一箇所 luna max に置き換えろ。
claude よりも codex のトークン消費が激しすぎる」。
D423 は「段 2/5 の sol→luna は親の段 4 裁定の権限外で、ユーザー裁定にだけ属する」と定め、
択 (b) (証拠なし・段 2/5 限定・effort 維持の model-only swap) を明示的に残していた。
本指示はその supersede 権限の行使であり、対象を「一箇所」へ絞ったもの。

「一箇所 = 段 2」の一意性:
現行の sol 使用箇所は 段 2 (max) / 段 3 レンズ 1 (max) / 段 5 (high) / 段 6 review・fix・focus (high)。
`max` かつ sol は段 2 と段 3 レンズ 1 の 2 つだけで、段 3 レンズ 1 を luna にすると 2 レンズとも
luna になり D241 が明示的に不採用とした「全 luna」へ戻る。よって「luna max 一箇所」は段 2 に一意。

## 段 1 実測 (親が測った)

- **M1** dev-wave receipt 170 本 (`/work/1/SFC/tanab/dev-wave-jobs`, maxdepth 3) の集計。
  段 2 = CLI reported 5,696,376 token / 20 走 (全体 34,405,404 の 16.6%、1 走平均 284,818)。
  20 走すべて `recorded_model=gpt-5.6-sol` / `recorded_effort=max`。sol 系で最大の消費。
- **M2 (前提を覆す新事実)** 段 3 の同一 wave 内 paired 比較 15 wave で luna/sol の CLI reported 比は
  中央値 **1.05 倍**・合計 **+7.2%**・luna が安いのは **7/15 wave**。
  **「sol→luna で token が減る」は本 repo の運用実績では支持されない。**
  レンズが違うため model 純差ではない。T-182 の −31.6% は n=1・同一 prompt で、
  D241 自身が policy 根拠から除外している。→ 段 4 で扱い、ユーザーへ報告する。
- **M3** `docs/dev-wave/**` L1.5 層予算の余裕は **20 bytes**
  (padding 25 bytes で `L1.5 unique footprint 9572 > 予算 9566` が発火。実測後復元、tree clean)。
  T-1132 段 2 プランが想定した「`、段 2 \`gpt-5.6-luna\`` を挿入」形は **+23 bytes で入らない**。
  slug 出現を 3 → 2 に減らす書き換えなら −7〜−13 bytes で収まる。
- **M4** コード側不変条件 (親が file:line を直接読んで確認)。
  - I1 `tools/dev_waves/launch_authority.py:396-397` — 他段 model と consult sol model の一致を
    runtime raise で要求。段 2 を分けるには解く必要がある。
  - I2 `orchestrator/tests/test_dev_wave_launch_authority.py:98-101` — 段 3 の 2 レンズは異 model 必須。
  - I3 `tools/codex_worker_launch.py:3497` の legacy receipt 監査が
    `snapshot_authority(commit=<過去 commit>)` で過去 commit の権威行を再解釈する。
    新文法だけを受理すると**過去 receipt の監査が全部落ちる**。旧文法の受理が要る。
- **M5** lane 名は反転しない (lane `luna`→luna、lane `sol`→sol のまま)。
  D423 が挙げた「flip trick の 145 箇所 footgun」は本案では発火しない。

## 不変条件

- 段 3 の 2 レンズは異 model のまま (I2)。段 3 / 5 / 6 の model・effort は不変 (D241/D243/D266)。
- model 権威は `DW-O01` の 1 行だけ (D242)。他 surface に slug を置かない。pin は「不在」検査のまま。
- 過去 receipt の再構成監査が通り続ける (I3)。
- `docs/dev-wave/**` の層予算を超えない (M3)。

## (P) 親の provisional 裁定 — 攻撃対象

- **(P1)** 「luna max 一箇所 = 段 2」の同定。上の一意性論証で足りるか。
- **(P2)** 権威行を slug 2 個の形へ書き換える案。意味が一意か、D242 の decoy 耐性を落とさないか。
- **(P3)** 旧文法 (v1) と新文法 (v2) の両受理。DW-O13 の「受理形を増やす = 新設」に当たるため、
  v1 は過去 commit の再構成専用で live 起動には使えないことを機械で担保する。

## 成果物影響 (DW-G05)

本変更は開発ループの資源配分であり、campaign 成果物 (certified 選択・レポート・台帳) の
値・受理集合・参照を変えない。実装しない場合もこれらは変わらない。変わるのは
段 2 receipt の `requested_model` (sol→luna) と `DW-O01` の権威行だけ。

## 成果物の形

`docs/dev-wave/operations.md` の権威行 1 行 + `tools/dev_waves/launch_authority.py` の文法・導出 +
`tools/check_docs.py` の pin literal + 既存テスト更新 + 新規回帰テスト + decisions の D 記録
(D241/D423 の段 2 部分を supersede)。

## 並列分割方針

実装面は 1 単位。`launch_authority.py` / `check_docs.py` / テストは同一 literal に強く依存し、
分割すると必ず衝突する。codex `role=author` 1 本。段 6 は敵対レビュー 2 本 + fix + 変異 matrix + 受入全走。

## 段 2・3 の流用 (入口「読み込み契約」の再開型)

本 wave は D423 の裁定後に別 context が段 4 から再開する型。変更面の骨格 (権威文法の分割・
legacy 互換・pin 更新・変異登録) は T-1132 の段 2 プラン / 段 3 レンズ 2 本と同一で、scope は
その真部分集合 (段 5 を含まない)。よって
`output/insights/2026-08-16_t1132-model-routing-luna/{s2-plan,s3-lensA-correctness,s3-lensB-scope}.md`
を流用し、再検査は段 6 レビューへ寄せる。M2 (paired 実績) と M3 (byte 予算) は T-1132 に無い
新事実なので段 4 で裁定する。
