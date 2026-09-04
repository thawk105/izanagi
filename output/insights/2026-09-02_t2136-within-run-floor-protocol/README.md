# [T-2136] within-run 較正の protocol 記録と層 3 の認定較正接続

wave: `dev-wave-t2136-within-run-floor-protocol` / branch:
`worktree-dev-wave-t2136-within-run-floor-protocol`
実装 commit `053ddb273`、main 取り込み merge `813c66033` とその後続。

本 README は実施記録と裁定パッケージ。設計判断の正本は `docs/decisions.md`、
経緯の正本は `docs/worklog.md` の該当エントリ。

## 何を閉じたか

1. **生産側:** certify 経路の producer が canonical genome を成果物へ記録する。
   導出は受入証の実行済み build argv からで、自己申告の引数は作らない。
2. **消費側:** 層 3 が環境契約の pin した content-addressed 認定較正を候補に採る。

## 何を閉じていないか (過大主張しないための明記)

**非 silo の within-run floor が公式材料レポートへ入るようになったわけではない。**
認定用 launcher `tools/pegasus/certify_calibration.sh` が `CCBENCH_*` と `ycsb_silo.exe` を
直書きしており、非 silo の較正を生産できない。実投入には次が残る。

1. 認定用 launcher の protocol / 軸の一般化
2. 非 silo within-run floor の取得と genome 付き登録成果物の生産
3. その成果物を指す環境契約世代の登録と活性化 (D1377 の手続きに従う)
4. その契約 hash を authority に持つ v2 campaign の実生産と admission
5. 当該 campaign からの層 3 レポート生成

起票文の「この 2 つが残る限り入らない」は必要条件の主張であり、本 wave が閉じたのは
その必要条件である。

## 実データでの挙動 (差分適用後)

| 環境・lock・動作点 | within-run の出力 |
|---|---|
| pegasus v2 (有効な g1 pin)、silo、48、1M、skew 0.9 / rr50 | g1 の CV `0.011705837968885854`、根拠 `genome-absent-legacy-record` |
| pegasus v2、非 silo | 一致なし (g1 は genome 不在で silo 扱い) |
| pegasus v1 | 一致なし (直下に within-run kind が 0 件) |
| pegasus g2 | 現行活性化では never-active のため候補にならない |
| linux-baremetal v2、skew 0.9 | pin の CV `0.02280630204206476` |
| linux-baremetal v2、skew 0 | 直下 record の CV `0.004726195977018071` |
| linux-baremetal v1 | 従来どおり直下 2 件を動作点で分離 |

skew 0 の行は、親が段 4 で一度採用しかけた「pin 1 件だけを候補にする」案が失わせていた値である。
段 3 のレンズが実データで示し、和集合へ差し替えた。変異 M8 がこの回帰を常設で検出する。

## ユーザー裁定へ返す 3 件

### 裁定 1 — 自己整合しない有効較正を層 3 の within-run floor に使ってよいか

有効な環境契約が pin する g1 (`calibration-753f535a8d024727.json`) は、自分の
effective-clock 述語を 48 本中 1 本で通らない既知例外として
`orchestrator/tests/test_env_contract.py` の `KNOWN_SELF_INCONSISTENT_CALIBRATIONS` に載る。
健全な g2 は never-active で、活性化は D437 により人間 lockstep 待ち。
本 wave の接続は、v2 pegasus campaign に対してこの g1 の値を層 3 へ**新規に**入れる。

- **既存成果物の値は 1 件も変わらない。** 現存する層 3 レポートは全て別環境の v1 lock である。
  影響は将来生産される v2 pegasus campaign だけ。
- 親は「有効な契約が何を pin しているかは本 wave の裁定事項ではなく現行契約の帰結」と判断し、
  自己整合性の再検査を新設しなかった (新 gate の追加は scope 外)。
- 選択肢: (a) このまま使う (現状の実装)。(b) g2 が活性化されるまで pegasus v2 の
  within-run を一致なしに保つ。(c) 自己整合性を層 3 で再検査する gate を新設する。

### 裁定 2 — 認定を通らない経路の今後の record をどう扱うか

層 3 は genome 不在の within-run record を作成時期に関係なく silo と仮定する。
D1374 はこれを「歴史的 record」の扱いとして認めたが、限定が効いていない。
非 certify 経路は今後も genome 不在の record を書ける。

- 閉じるには (a) 既存 2 件の内容 hash を allowlist に固定して新規の genome 不在 record を
  層 3 で拒否する、(b) 非 certify 経路にも bytes から導ける provenance 経路を作る、
  のいずれかが要る。(a) は台帳の新設に当たり、ユーザーが scope 外と指定した追加物である。
- 現状の実装は従来どおり silo 仮定 + 根拠表示のままにしてある。

### 裁定 3 — 後続タスクの順序と主体

上の「何を閉じていないか」の 1〜5 の順序と、どれを AI が実施してよいかの境界。
とくに 3 の活性化は D1377 と D437 により人間 lockstep の所有である。

## 検査の実測

| 検査 | 結果 |
|---|---|
| 焦点走 (編集 3 test file、merge 後) | 377 passed |
| 凍結 bytes 回帰・内容走査・AST 走査・qualification・oracle | 480 passed / 7 skipped |
| 一度 65 赤だった consumer 群 (fix 後) | 633 passed |
| 変異 matrix (merge commit 束縛) | baseline PASSED / KILLED 10 / SURVIVED 0 / MISMATCH 0 / 期待 node 29 件完全一致 |
| merge 合成監査 (独立 context) | real 所見 0 件 |
| AI provenance 全史監査 | rc=0 |
| 受入全走 | land の受領証を正本とする |

凍結済みの登録済み較正 2 件の SHA-256 は `753f535a…` / `94a4b79f…` のまま不変である。

## 成果物

- `verbatim/` — 子 8 本の逐語 (plan 1、consult 2、author 1、review 3、fix 1)
- `mutation-spec-final.json` — 変異 10 点の事前登録 (期待 node は probe の観測から機械生成)
- `mutation-ledger-probe.json` — 全件 SURVIVED 期待の probe (観測 node 収集用)
- `mutation-ledger-impl-commit.json` — 実装 commit `053ddb273` 束縛の本走
- `mutation-ledger-merge-commit.json` — main 取り込み後の最終 commit 束縛の再走
