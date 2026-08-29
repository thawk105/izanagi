# 段 4 裁定 — [T-2005] B-4 projection closure hash の事前登録

## 所見の裁定

### sol レンズ

- **S1 「選択されなかった 2 driver の stale 値を production 関門が受理する」— real・採用。**
  これが本 wave の核心である。3 値を宣言しても production が 1 値しか照合しないなら、
  事前登録は「driver を選んだ後に残り 2 つの閉包が動いても実走できる」ことを許す。
  T-2005 の「旧 hash を受理する緩和はしない」に正面から反する。
- **S2 「v1 record に driver 身元が無い」— real・採用 (ただし対処は S1 に吸収)。**
  段 2 が置いた `expected_driver_kind` の受け渡しは採らない。record に driver 身元を
  主張させない。S1 を入れれば、文書 3 値 = live 3 値 かつ record 値 = live(選択 driver) から
  record 値 = 文書[選択 driver] が導かれる。**照合を 2 箇所で実装する必要が無い** (F625 の型を避ける)。
  記録の身元を path から推定しないことを module の限界として明記する。
- **S3 「D1060 を supersede する根拠なくセルを埋めている」— real・採用。**
  §5 の値セルは本 wave でも埋めない。luna 所見 1・3 と同じ結論。
- **S4 「full verifier が必ず拒否する JSON を admission record と呼ぶな」— real・採用。**
  draft record は 1 件も発行しない。

### luna レンズ

- **L1 「D1060 は永久禁止ではないが今埋める権限も与えていない」— real・採用。**
  親 brief の「以後 n 欄が埋まったから本セルも可」は推論として成立しない。撤回する。
- **L2 / L3 「model snapshot の宣言源と承認主体が §5.1 に無い」— real・採用。**
  段 2 が置いた「人間の実行責任者が承認」という主体は既存規範から導けない。
  **埋めるのではなく §5.1 に規範を足す。** これは D1060 が env_tag・実行責任者・開始時刻の
  3 欄で採ったのと同じ形であり、新しい権限主体を作らない。
- **L5 「登録は一度きりの行為でなく継続的な不変条件」— real・採用。** §10 と decisions へ書く。
- **L6 「3 driver 全件の鮮度検査が必須経路に無い」— real・採用。** S1 と同一の穴。
  段 2 が提案した任意実行の repository test ではなく、**production 経路へ入れる。**
- **L7 「draft record は直ちに使えず後続編集で必ず失効する」— real・採用。** S4 と同じ。
- **L8 「凍結物の再発行不要という結論は反証できなかった」— 親の実測を維持。**
  ただし「発行前の一時点に限定した結論」と書く。

## 確定した scope

**本 wave は「登録の器と規範」を閉じ、「登録する値」は閉じない。** 値のうち
`expected_claude_model_snapshot` だけが repo bytes から導出できず、その宣言源と承認主体が
文書に存在しない。§0 の原子性によりセルは全部埋めるか未記入かの二択なので、
projection と prompt だけを先に書くこともできない。ユーザーが指示した停止条件
「閉じないなら不足を記録して停止する (新しい権限主体を作らない)」に該当する。

### 実装する (実装面)

1. `_EXPECTATION_ROW_RE` を、base / sort / trigger の固定順・固定 tag の 3 projection を要求する
   形へ**置換**する (`fullmatch` を維持)。旧 1 値形・欠落・重複・順序違い・末尾余剰は拒否する。
2. `VerifiedB4AdmissionRecord` に、文書から読み取った 3 値の写像を持たせる。
   record schema `p3-b4-prerun-admission/v1` と record 側の単一 projection field は変えない。
3. `p3_b4_closed_critic.py` の pair 生成点で、**文書の 3 値すべてを live
   `projection_sha256(kind)` と照合する。** 1 つでも不一致なら provider 作成前に停止する。
   既存の「record 値 vs 選択 driver の live 値」照合はそのまま残す。
4. 上記の負例・正例テスト。

`expected_driver_kind` の受け渡し、record schema 昇格、sidecar 変更、任意実行の tripwire、
新規 CLI、環境変数、汎用 hash 台帳は**採らない**。

### 編集する (docs)

5. §5.1 の当該欄へ、D1060 の形で解除条件を足す — 3 driver の exact grammar、
   model の宣言源・承認者・宣言時点・不一致後の扱い、prompt と projection の導出元。
6. §10 へ不足を記録する — model snapshot の宣言源が無いこと、登録が継続的不変条件であること、
   「再発行不要」は最初の発行前に限った結論であること。

### 実装しない・書かない

- §5 の値セル (10 欄すべて現状維持)。
- admission record の JSON artifact (0 件)。
- 「§6 を満たす」「登録完了」と読める名前・文言 (D1000)。

## 成果物影響 (DW-G05)

放置すると、将来 §5 を埋める作業が 1 driver 分の hash だけを書いて済ませられ、driver の選択を
結果を見た後に行える経路と、未選択 driver の閉包が陳腐化したまま実走できる経路が残る。
本 wave はその 2 経路を機械的に塞ぐ。値そのものは埋まらないので実走関門は開かない (開かないのが正しい)。

## 順序制約

`projection_closure_manifest()` の閉包は本 wave が編集する `p3_b4_admission_record.py` と
`p3_b4_closed_critic.py` を含む。したがって **live 値を pin するテスト・fixture は、
閉包コードが最終形になってから確定させる。** 段 6 の fix が閉包 member を触ったら再計算する。
テストは literal hash を pin せず `projection_sha256(kind)` を呼んで比較する形にし、
この treadmill をテスト側に持ち込まない。

## 変異事前登録 (DW-M01)

|#|変異位置|無効化する保護|赤の単一理由|前後に同じ入力を拒否する層|
|---|---|---|---|---|
|M1|pair 生成点の全 3 件照合ループを削除|未選択 driver の陳腐化拒否|stale な非選択 driver を持つ文書が受理される|無し (この層だけが非選択 driver を見る)|
|M2|同ループの反復対象を選択 driver 1 件へ縮小|同上 (部分)|非選択 2 driver のいずれかが stale でも通る|無し|
|M3|同照合の右辺を live から文書の他 tag へ差替え|恒真化の防止|全 3 値が同時に stale でも通る|無し|
|M4|`_EXPECTATION_ROW_RE` を旧 1 値形へ戻す|3 driver 完全性|1 driver だけ書いた行が受理される|無し (sentinel 検査は全欄記入 fixture を止めない)|
|M5|同 regex の tag を順不同・重複許容へ緩める|固定順・一意性|重複 tag・順序違いの行が受理される|無し|
|M6|`fullmatch` を `search` へ緩める|行全体の exact 一致|末尾に余剰を持つ行が受理される|無し|

正例 (過剰拒否の検出): 最終 tree の live 3 値を固定順で持つ完全な行と、選択 driver の live 値を
持つ record の組は、pair 生成点まで到達する。この正例が赤になる変異は過剰拒否である。

## 裁定パッケージ (ユーザーへ返す)

1. **`expected_claude_model_snapshot` の exact 値と、その結果非依存の宣言源。**
   実測: 実 CLI 応答の `modelUsage` key は `claude-opus-5[1m]` (2026-08-21 の probe raw)、
   古い成果物 125 件は `claude-opus-4-8`。repo からは導出できず、走らせる時期で変わる。
   §5.1 に承認者・宣言時点・不一致後の扱いを足すところまでは本 wave で行う。
   **値の指名は実行責任者の手番である。**
2. **指名後に §5 のセルを埋める wave を起こしてよいか。** D1060 の明示的な取り扱いを含む。
