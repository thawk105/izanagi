---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-08-05
wave: dev-wave-t420-wall1-driver
seq: 1
title: [T-420] 壁 1 の着手条件は成立していないと実測した — 阻んでいるのは較正の自己不整合ではなく probe の観測者効果で、親の当初因果説明は敵対検証で撤回した (docs のみ、branch worktree-dev-wave-t420-wall1-driver)
---

## 本文

- **依頼の前提を実測が覆した。** 依頼引数は「attestation の裁定 ((208) R-0/R-1) が付いたので
  着手条件成立。壁 1 の使い捨て driver を正規経路へ」であった。DW-S01 に従い brief 前に前提を
  実測したところ、**着手条件は成立していない**。(208) で付いたのは*方式の選択* (α) であって、
  その方式で取り直した較正はまだ存在しない。現行 probe 方式のままでは attestation を通れず、
  driver を再走させても 2026-08-04 と同一地点で落ちる。**本 wave は「実装しない」と裁定し
  `4→7→8→9` を採った。** 実装差分が無いため変異 matrix と受入全走は対象外である。
- **親の当初の因果説明は誤っており、敵対検証で撤回した。** 親は段 1 で「登録済み較正が自分自身の
  述語を通らないから必敗」と述べた。しかし述語は expected の**中央値**から帯を作り
  **observed の全標本**だけを検査するため、expected 側の外れ値は無害である。実行時と同じ射影で
  測り直すと、**静穏な機械 (48 標本すべて 2101.0) なら現在の登録済み較正のままでも受理される
  (True)**。gate は構造的に壊れていない。
- **親が誤った理由も記録に残す。** `effective_clock` mapping は `governor` / `method` を含む
  4 key を持つが、述語は expected に `{samples_mhz, tolerance_pct}` の**ちょうど 2 key** を要求する。
  親は mapping をそのまま渡したため、3 回の測定がすべて**値ではなく形で** False を返していた。
  形の検査と値の検査を分離せずに測ると、gate が「必ず落ちる」ように見える。
- **真の阻害要因は probe の観測者効果である。** production probe は `/proc/cpuinfo` の `cpu MHz` を
  読むが、[T-419] の実機因果実験が「帯外化の原因はそのコアが busy であること」を確定させている
  (走行 CPU の帯外率 240/240、sham 0/40 に対し busy 40/40)。**probe の走行 CPU は定義上必ず
  busy なので、必ず 1 個以上の帯外標本が出る。** 2026-08-04 の失敗は observed 側 (idx 34 =
  3076.13) が帯外だったためであり、expected 側の外れ値のせいではない。
  なお「Pegasus 全ノードで物理的に不可能」は未証明であり、外的妥当性は実験機の構成に限られる。
- **別の較正へ向ける seam は無い。** 較正は contract に hash pin され、registry は静的で
  register API を持たず、D125 は環境変数 override を作らないと明記し、`run_campaign` は Pegasus
  compute で登録済み契約との完全一致を要求する。敵対検証も同結論であった。
- **[T-422] / F98 はもう blocker ではない。** `IZANAGI_EXPLORATION_OUTPUT_ROOT` が landed
  しており、[T-420] の障害は attestation ただ 1 点に絞られた。
- **本 wave の作業中に land した裁定が独立に同じ運用結論を与えた。** [T-506] は
  「再較正まで certified campaign を開かない」の運用宣言の維持を明記し、[T-507] も実施を
  較正チェーン ([T-419] U-2) 後と定めた。
- **敵対検証の所見 1 件は scope 外だが既出のため重複起票しなかった。**
  `env_contract=None` の legacy driver が attestation を素通りし Pegasus 実行を
  `linux-baremetal` と記録しうる件は real だが、**[T-331] が既に裁定済み (択 (a)) で実装待ち**
  である。機序の裏取り (`loop.py` の `_authorize_measurement` が `env_contract is None` で
  即 return する) だけを insight に残した。
- 一次資料 = `output/insights/2026-08-05_t420-wall1-precondition/README.md`

## 次の一手差分

### 更新

- [T-420] **P2・着手条件は未成立 (2026-08-05 実測) → [T-419] U-2 の下流へ繋ぎ直す**:
  旧本文の「attestation の裁定が付いた後、driver をそのまま再走させれば完了。追加実装は要らない」
  は陳腐化した。(208) が選んだのは方式 α であって、その方式で取り直した較正はまだ無い。
  阻んでいるのは較正の自己不整合ではなく **probe の観測者効果**である — 述語は observed の全標本
  だけを検査し、probe の走行 CPU は定義上必ず busy なので必ず帯外標本が出る ([T-419] 240/240)。
  静穏な機械なら現行較正のままでも受理される (実測) ため、gate ではなく probe が原因である。
  較正は contract に hash pin され、通す道は (a) gate を緩める = 規律 2 違反で不可、
  (b) 方式 α で取り直して再登録し pin を更新する = **U-2 の所有作業**、の 2 つしかない。
  したがって **[T-420] は U-2 着地後に初めて着手できる**。U-2 後に driver を再走させ、
  build → verify → bench の 1 周を確かめる。**それまで計算ノードジョブを投げてはならない**
  (投げても attestation で落ちるだけで答えは得られない)。
  なお [T-422] / F98 は解消済みで、もはや障害ではない。
  一次資料 = `output/insights/2026-08-05_t420-wall1-precondition/README.md`
  base: 3fba5c2e92127622d0fa0bf8fc4ee598278b5ca28964815ef704d9b1253898b1

### 新規

- {{T:transport-probe-lane}} **P3・ユーザー裁定待ち**: 壁 1 が問うているのは *transport*
  (build → verify → bench が 1 周繋がるか) であって*認証*ではない。しかし現状その死活確認は
  attestation の背後にあり、較正チェーンが直るまで観測できない。そこで **gate を緩めるのでは
  なく lane を分ける**案を裁定へ返す — certified 材料・proof chain へ構造的に流れ込まないことを
  保証したうえで transport だけを確かめる非認証 probe lane を設けるか。
  **敵対検証で判明した必須条件**: 型分離だけでは足りない。`ExplorationCampaignLayout` は official
  layout と継承関係を持たないと宣言しているが、`artifact_admission` が文字列 path を
  `CampaignLayout` に包み直せるため、**consumer / admission 側で exploration marker を明示拒否する
  防壁**が要る。危険は「認証を通らない実行経路」を増やすこと自体が攻撃面であり、しかも同型の
  無防壁経路が既に 7 本あり [T-331] で閉じ待ちであること — 閉じる前に足すのは順序が逆になりうる。
  **親の推奨は「設計として起票するが実装しない」** (DW-G01 が「確認前の専用機構構築」を却下する)。
  一次資料 = `output/insights/2026-08-05_t420-wall1-precondition/README.md` §軸 2
