# 親の独立設計仮説 (段 2 codex と照合し、段 3 で攻撃させるための対照)

## 実測が変えた問題設定

`output/s8b-freeze/` には `floor_protocol.json` / `holdout_freeze.json` /
`selector_predictions.json` / `selector-runs/` しか無く、**ratified freeze も完走 campaign 成果物も
存在しない** (`find output -iname "*ratified*"` = 0 件)。D143 が記録したとおり pegasus の campaign は
まだ一度も build に到達していない。

したがって「既存 certified 参照」で守るべき実体は **campaign 結果ではなく事前登録 (blind seal) の
連鎖**である —

- `selector_predictions.json` (盲検予測、封印済み)
- `selector-runs/journal.jsonl` の `run_header.protocol_sha256 = 261cec1c…`
- `floor_protocol.json` (bytes `261cec1c…`、`pre_oracle_head` の git blob と byte 一致が要求される)
- `holdout_freeze.json` (`315b1eb8…`、protocol が `freeze.sha256` で参照)

**壊してはならないのは「floor データを見る前に protocol と予測が確定していた」という性質**であって、
過去の測定値ではない。

## 親の設計仮説 H1 — protocol の二層分離

現行 protocol (18 key) は **事前登録された実験設計** (formula / n_sessions / reps / master_seed /
schedule_algorithm / cell_cv_max / …) と **実行環境束縛** (`contract_sha256`、`env_tag`) を
1 つの JSON に混ぜている (`s8b_floor_contract.py:33-40` の `_PROTOCOL_KEYS`)。
較正の再登録が壊すのは後者だけなのに、bytes 一括凍結のため前者ごと壊れる。

仮説: **設計層を封印済みのまま据え置き、環境束縛層だけを世代として差し替える。**
新世代の protocol は「設計層が封印済み bytes と厳密一致し、環境束縛層だけが新 contract を指す」
ことを機械が検査したときだけ発行できる。

- 利点: 盲検性が保たれる (設計値は事後に動かせない)。旧 bytes を貼り替えない。
- 要る変更: `s8b_floor_campaign.py:138-142` の path 定数、
  `:1411-1416` の全 bytes 比較、seal の canonical 再導出、`FROZEN_MANIFEST` への追加。
  **いずれもコード変更であり、この wave の scope 外 (実装は U-2 wave)。**
- 危険: 「設計層一致」の検査が恒真化すると、事後に設計を書き換える経路になる。
  検査は key 集合の exact 分割 + 設計層の canonical bytes 一致で書く必要がある。
  分割を誤ると **受理集合が広がる** (規律 2 への直接の攻撃面)。

## 対抗仮説 H2 — 世代を切らない

較正を再登録せず、現 protocol 世代のまま campaign を開ける道があるか。
D143 決定 (3) が (b)「述語を正とし較正を取り直す」を裁定済みであり、
D155 が取得時 self gate を実装済みなので、**再登録は避けられない**。H2 は裁定に反する。
ただし「再登録の対象を registry pin だけにして artifact path を content-addressed のまま
差し替えない」道が本当に無いかは段 3 レンズ B に検証させる。

## 段 4 で照合する点

1. 段 2 の案が H1 と同型か、別の切り方をしているか。
2. 「設計層 / 環境束縛層」の分割線をどこに引くか (`env_tag` はどちら側か)。
3. 盲検性の保存を機械で検査できるか、それとも運用宣言で終わるか (恒真化の危険)。
4. 実装を U-2 wave へ渡す境界が明確か。
