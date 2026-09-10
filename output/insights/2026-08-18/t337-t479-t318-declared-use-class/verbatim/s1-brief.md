# 段 1 brief — [T-337]/[T-479]/[T-318] 種別宣言の producer 実装

wave: `dev-wave-t337-t479-t318-use-class` / branch: `worktree-dev-wave-t337-t479-t318-use-class`
起点 main: 38f173cb / 2026-08-18 18:1x JST / 環境: Pegasus login (実測は login 内で完結、計算ノード不要)

## 確定済みユーザー裁定 (正本)

- D162 決定 (1)(2)(3): producer が宣言できるのは利用意図の閉集合の種別と raw 事実だけ。
  適格性状態・受理状態・validator identity/result は closed schema で reject。
- D162 決定 (10): 機械化は発火条件が揃うまで行わない。実装被覆 0/9 層。**本 wave で変えない (ユーザー指定)。**
- D162 決定 (11): 種別 field 名は未確定。「名前が決まるまで種別 field を持つ新しい producer を land しない」。
- [T-479] 択 (b): `artifact_role` を使わず別名。第一候補 `declared_use_class`。
  (a) oracle 側改名と (c) 同名二義 (D75 抵触) は不採用。
- [T-318] (116) 択 (a): producer ごとに種別 `{official,exploration,qualification,dry}` を宣言させ閉表化。
  新規 producer は宣言なしでは通らない。族の外延をファイル名列挙から切り離す。

## 前提を覆す新事実 (段 4 で再裁定する)

- **新事実 A — 名前は既に実成果物へ pin 済み。** `declared_use_class` は D282 pin 済み receipt schema
  (`output/insights/2026-08-11_t139-manifest-land1/receipt-schema-v1.json:1248`) に
  enum `["official","exploration","qualification","dry"]` として存在し、D500 決定 (4) が
  「`declared_use_class` は利用意図であって受理入力にしてはならない」と本文で使っている。
  したがって新 D は「候補から確定へ」ではなく「既に pin された名前の条文化 + supersede」である。
- **新事実 B — RF producer は D500 で実装しないと裁定済み。** 依頼文の「残っているのは producer 側の
  実装」は、RF 受領証 producer を指す読みでは既に閉じている。D500 決定 (2) が閂を投入 gate
  (`PreregBinding` 非 export、D264/D282) と同定し、決定 (3) が残余 (attempt registry + 純粋な組立て +
  否定検査) を「producer 実装済み」として land することを名指しで禁じた。
- **新事実 C — production の実装被覆はゼロ。** `declared_use_class` を出力する production Python は
  `orchestrator/ tools/ hooks/` 全件検索で 0 件。

## scope (親の provisional 裁定 — すべて攻撃対象)

- **(P1) 本 wave の producer 軸は D123 決定 (2) の campaign namespace 軸であり、RF 受領証 producer ではない。**
  根拠: [T-318] の「族の外延をファイル名列挙から切り離す」は D123 決定 (2) の
  「**この線引きがファイル名列挙である点は本 D の弱点**であり、producer ごとの `artifact_role` 閉表化は
  別裁定へ送った」と逐語対応する。新事実 B により RF 軸は閉じているため、実装可能な残余はこちらだけ。
- **(P2) 宣言の所在は producer module の module-level 宣言とし、`run_campaign` 呼出し kwarg を増やさない。**
  根拠: `run_campaign(` 呼出しは repo 全体で 195 箇所 (大半が test)。「producer ごとに宣言」という
  [T-318] の文言は module 単位の宣言と整合する。
- **(P3) `declared_use_class` は D282 receipt schema と同一名・同一閉表・同一意味の単一軸に統一する。**
  別実体として二重定義すれば D75 二義化になる。
- **(P4) namespace は宣言から導出する。** `official`→`campaign_layout`、`exploration`→`exploration_campaign_layout`。
  `qualification` / `dry` を campaign producer が宣言したときの扱い (拒否か別 layout か) は段 2 で決める。
- **(P5) 「通らない形」の強度**: `run_campaign` 到達時の fail-closed だけで足りるか、producer module の
  網羅を固定するメタテストが要るか。段 2/3 で決める。

### scope 内

1. 新 D: 種別 field 名を `declared_use_class` に確定し、[T-318]/[T-337] 裁定文の literal `artifact_role`
   指定を**明示 supersede**、D162 決定 (11) の land 禁止を解除する。
2. 実装: campaign producer の種別宣言を必須化し、宣言なしを fail-closed で拒否する。
3. docs: 9 層の所在を実測した被覆計画 (現状被覆と D162 決定 (10) 発火条件の対応)。

### scope 外 (根拠つき)

- RF/qualification 機械化 9 層の実装 — D162 決定 (10)、D500 決定 (1)(2)(3)。被覆計画は書くが実装しない。
- `artifact_role` (探索 oracle 文書種別、production 3 file) の改名 — [T-479] が (a) を不採用と裁定。
- 投入 gate / `PreregBinding` の解除 — D264/D292 の解除権威は本 wave にない。
- 凍結 artifact・campaign-id・canonical preimage の改訂。

## 不変条件

- **既存 producer の出力 path と凍結 bytes を 1 byte も変えない** (D123 決定 (1))。
  `s1_known_axes_freeze.py` が `output/campaigns/...` を glob/join し、凍結 3 artifact が同 path 文字列を
  本文に持つ。pin 閉包の実測: `output/campaigns` は py 194 hit / 16 file、`output/exploration` は 6 file
  (production 2 + hooks 2 + test 2)。
- 宣言を campaign-id・`CampaignConfig`・canonical preimage に入れない (D123 決定 (3))。
- 規律 2: 宣言なしを既定 official にしない。既定値の削除は fail-closed 方向にだけ動かす。
- D162 決定 (1)(2): 宣言できるのは利用意図だけ。適格性・受理状態を宣言させない。
- 観測者効果・trace 分離には触れない (本 wave は計測経路を変えない)。

## 既存被覆と純増検出力 (性質で検索)

対象 vector = 「種別を宣言しない producer が official 成果物を書ける」。

- `loop.py:132` の `campaign_namespace: str = "official"` が既定値であり、宣言しない caller は黙って
  official になる。`loop.py:167` の `ValueError` は**明示的な誤値のみ**を捕らえ、省略は捕らえない。
- この vector を突くテストは `orchestrator/tests/` に 0 件 (`campaign_namespace` を default/既定/official の
  性質で検索した hit は `test_campaign.py:8313` の明示指定 1 件のみで、省略経路を固定していない)。
- したがって本 wave の検査は**純増**であり、既存検査の言い換えではない。

## 成果物影響 (DW-G05)

実装しない場合、族の外延はファイル名列挙のまま残り、新規 campaign driver が宣言なしで official
namespace へ書ける。official namespace は certified 選択と材料レポートの入力であり、D123 決定 (5) の
marker 防壁は「marker が無い root は受理する」blocklist 設計であるため、探索由来の campaign が
official として受理集合へ入る経路が開いたままになる。実装すれば受理集合は狭まる方向にだけ動き、
既存 6 driver の出力 path・凍結 bytes・certified 選択の値は不変である。

## 成果物の形

- コード: `orchestrator/campaign/` の宣言機構 + 5 producer への宣言付与 + `loop.run_campaign` の導出。
- テスト: 宣言省略の拒否、閉表外の拒否、既存 5 producer の path 不変、族網羅のメタテスト。
- docs: 新 D 1 本 (spool fragment)、worklog fragment、被覆計画 (insights)。

## 分割方針

受理集合が変わり正しさ防壁 (official namespace) に触るため軽量版にしない。
段 2 プラン 1 本、段 3 敵対 2 レンズ、段 5 実装 1 本 (編集面は `orchestrator/campaign/` に閉じる)、
段 6 敵対レビュー 2 本 + fix + 変異 matrix + 受入全走。
