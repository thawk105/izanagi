# 2026-08-16 freeze 由来 holdout の実測境界に admission と一回性台帳を置く — 材料

dev-wave (branch `worktree-dev-wave-t523-holdout-admission`) の一次資料。
可変状態の正本は worklog 末尾エントリであり、本ディレクトリは逐語と実測値を保持する。

## 構成

| path | 内容 |
|---|---|
| `brief.md` | 段 1 brief (親の実測と provisional 裁定 P1-P5) |
| `s4-adjudication.md` | 段 4 裁定 + プラン v2 (採用 13 / scope 外 5 / 変異事前登録) |
| `s6-adjudication.md` | 焦点再レビュー後の親裁定 (残 5 所見の real/refuted と保証の縮小) |
| `verbatim/s2-plan-v1.md` | 段 2 プラン起草 (親 brief の誤り 6 点を含む) |
| `verbatim/s3-consult-a-sol.md` | 段 3 敵対相談 レンズ A (NO-GO) |
| `verbatim/s3-consult-b-luna.md` | 段 3 敵対相談 レンズ B (NO-GO) |
| `verbatim/s5-author-unit1.md` | 段 5 実装 Unit 1 報告 |
| `verbatim/s5-author-unit2.md` | 段 5 実装 Unit 2 報告 |
| `verbatim/s6-review-a.md` | 段 6 敵対レビュー レンズ A (NO-GO) |
| `verbatim/s6-review-b.md` | 段 6 敵対レビュー レンズ B (NO-GO) |
| `verbatim/s6-fix-unit-{a,b,c,d,e}.md` | 段 6 fix 各巡の報告 |
| `verbatim/s6-focus-rereview.md` | 段 6 焦点再レビュー (16 件の対応表と新規 5 所見) |
| `verbatim/s9-merge-reapply.md` | main 取り込み時の合成再適用と合成監査 |
| `verbatim/s6-author-oracle-wiring.md` | 第 3 producer (oracle driver) の結線 |
| `verbatim/s6-fix-unit-j.md` | oracle 結線が残した赤 2 件の是正 |
| `mutation/mutation-spec.json` | 本走の変異 spec (期待 node は完全集合) |
| `mutation/mutation-result.json` | 本走の変異台帳 (8/8 KILLED) |
| `mutation/mutation-spec-round1-probe.json` | 第 1 走 (probe) の spec |
| `mutation/mutation-result-round1-probe.json` | 第 1 走 (probe) の台帳 — erratum として保持 |

## 変異台帳の trim について

`mutation-result*.json` は原本が 5.7-5.9 MB あり、その大半は各 mutant の runner stdout 全文である。
**巨大な stdout 全文だけを sha256 + byte 数へ置換して保存した。**
`status` / `rc` / `failed_nodes` / 各種 hash は無改変であり、原本の sha256 と byte 数は
各ファイルの `_trimmed_from_original` に記録してある。

## 変異結果 (本走)

固定 HEAD `2c4fef9bcf5915f22fcc378aca99fbfd232ee9ba`、runner-mode=dispatch、
8 変異 + baseline の 9 走。**KILLED 8 / SURVIVED 0 / MISMATCH 0 / TIMEOUT 0。**

| id | 変異 | 検出 node 数 |
|---|---|---|
| M1 | 保護 signature の導出を空集合にする | 147 |
| M2 | 実行 gateway の許可検査を削除する | 24 |
| M3 | `--flagfile` を間接入力の拒否対象から外す | 4 |
| M4 | cell 確保の `O_EXCL` を外す | 5 |
| M5 | attempt ticket の二重消費を許す | 2 |
| M6 | freeze 由来集合と中立表の exact 一致検査を削除する | 1 |
| M7 | 許可証の同一性検査を型検査へ緩める | 5 |
| P1 | 正例 — 許可証なしの実測をすべて拒否する (過剰拒否) | 5 |

**生存はどの走行でも一貫してゼロだった。** 到達までに 4 走を要したのは、期待 node の
完全集合を確定する probe と、実行時にサフィックスが付く real-repo 変種の除外のためである。

- 第 1 走 (probe、別 HEAD): 8 件とも rc=1 で検出側へ倒れたが node 集合が MISMATCH。
  実測集合で再登録した。`mutation-*-round1-probe.json` として保持している。
- その後、第 3 producer (oracle driver) の結線でコードが変わったため、**最終 commit で
  走らせ直した。** oracle のテストも対象に加えたので M1 の検出 node は 101 → 147 へ増えた
  (関門を壊すと 3 producer すべてのテストが落ちる)。
- 本走の runner からは、実行時にサフィックスが付く real-repo 変種を 2 件 `--deselect` した
  (`test_real_seal_protocol_to_floor_official_core_e2e` と
  `test_v2_standalone_gate_check_requires_full_floor_validation`)。
  collection 時 ID と実行時 ID が異なり事前登録できない。**両 test は受入全走で担保される。**

## erratum — 逐語 1 本の可逆 defang (2026-08-16)

`verbatim/s6-review-a.md` を repo へ記録した時点で、**この逐語が holdout 三軸 conjunction の
1 hit を作り**、launch certificate の clean scan が拒否に倒れた (受入前の実測で検出)。
段 6 レビューが攻撃例として workload dict を引用したことによる。

段 7 契約に従い**可逆 defang + erratum**とした。

- 対象: `verbatim/s6-review-a.md` の所見 6 の攻撃シナリオ行 (物理 38 行目)
- 置換: 偏り軸と rmw 軸の 2 つの値を、それぞれ literal `<<DEFANG>>` へ置換した。
  比率軸は同ファイル内の他行にも現れるため触れていない (三軸のうち 2 軸を落とせば
  conjunction は成立しない)。
- 可視文字以外の変更はしていない。復元は `<<DEFANG>>` を元の値へ戻すだけでよい。
  元の値は、偏り軸が floor protocol の holdout に記録された値、rmw 軸が同じく 0 である。
- defang 前の file sha256 = `0c143a402a787d246b8a68e1d32f3f1ce3625aa9d3c31f0ac382551b4ee426a3`
  (9,599 bytes)、defang 後 = `3a0cdda2782f96a54fc76c525ec881ddc87ff75bf20c6eed80f092980557e387`
  (9,615 bytes)。defang 前の当該行 sha256 =
  `7ea4185da10c52abfd3dcc109650fd18062aad4f4cacde43f047f46dc4abaa9d` (272 bytes)。
- defang 後に repo 全体を再走査し、全 holdout の conjunction hit が 0 件であることを実測した。
