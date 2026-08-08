# [T-657] + [T-660] — pegasus 第 2 世代の活性化と head=2 検出力

wave: `dev-wave-t657-t660-g2-activation` / 2026-08-09 / 由来: ユーザー裁定 2026-08-08 §44

**この wave は land していない。** 前提 (b) floor protocol の再発行が人間手番であり、活性化だけを
取り込むと floor live admission と prediction seal が壊れた窓を main に作るため。

## ユーザー手番 (ここから再開する)

`reissue_floor_protocol.sh` を **この worktree の中で対話 shell から** 実行する。
script は tty・cwd・clean tree・HEAD の activation record と head 定数・T-080 receipt・
旧 bytes の golden をすべて停止条件として検査し、失敗・中断のどの経路でも
`output/s8b-freeze/floor_protocol.json` を HEAD (または検証済み backup) へ復元する。
既に再発行済みなら何もせず終わる。

再発行後に残る作業 (script は行わない): pin 3 件の更新 → 受入全走 → 変異本走 → land。
詳細は `s4-adjudication.md` の §5 / §6。

## 実測 (親)

| 対象 | 結果 |
|---|---|
| 活性化前の committed silo evidence の `verify-result` | **rc=1** (`current binding mismatch: driver` + `raw attestation binding/ordinal set mismatch`)。contract 検査に到達しない |
| 編集面 4 file (計算ノード、request 896505) | **333 passed** / 22.21 秒 / 非受入形 |
| floor 系 subset (`test_s8b_floor_campaign.py` + `test_frozen_artifacts.py`) | **211 passed / 2 skipped / 1 failed**。赤は `test_real_seal_protocol_to_floor_official_core_e2e` の 1 件だけで、floor 未再発行による期待赤 |
| 再発行後 bytes の独立検算 | 旧 774 bytes / 旧 sha256 `261cec1c…` / g1 hash 出現 1 回 → 期待新 sha256 `c0eeed87…` (長さ不変)。レンズ A の独立計算と一致 |
| provenance | 全履歴 1845 件 + incoming 15 件 + 10 件、いずれも新規違反なし |
| `check_docs.py` / spool fold dry-run | rc=0 |

**受入全走と変異本走は実施していない** (floor 未再発行の tree では構造的に赤が出るため)。

## 逐語

| ファイル | 内容 |
|---|---|
| `s1-brief.md` | 段 1 brief (P1〜P5 は攻撃対象として明記) |
| `s2-plan.md` | 段 2 プラン (sol/max/read-only) |
| `s3-lensA.md` / `s3-lensB.md` | 段 3 敵対相談 (sol / luna)。両者 NO-GO |
| `s4-adjudication.md` | 段 4 裁定 + §4b 段 6 所見の裁定 + §4c 焦点再レビューの裁定。**変異事前登録 5 件はここ** |
| `s5-a.md` | 段 5 実装子 (sol/high/workspace-write) |
| `s6-lensC.md` / `s6-lensD.md` | 段 6 敵対レビュー (sol / luna)。両者 NO-GO |
| `s6-fix1.md` / `s6-fix2.md` | fix 1・2 巡目 (再発行 script の作成と堅牢化) |
| `s6-refocus.md` | 焦点再レビュー (所見対応表つき)。R-4 は親が実測で refuted |
| `reissue_floor_protocol.sh` | **ユーザーが実行する再発行 script** |

## 裁定パッケージ (本 wave で実装せず返すもの)

1. **committed silo evidence の完全な historical 再検証 lane。** 現在 `verify-result` は contract 以前に
   driver / policy / verifier_module / runtime_modules / raw bundle を current bytes と比較するため、
   committed evidence に対して恒常的に赤で誰も再検証に使えない (親が実測)。記録 hash から歴史 blob を
   検証する独立経路を作るか、この CLI を新規生成 evidence 専用と明示して committed 再検証の主張を
   撤回するかの択一。
2. **T126 の series identity 回転を受入成果物で固定するか。** protocol admission は contract hash
   非依存で不変だが、`env_contract.py` が code identity に入るため series は回る。旧 series の
   継続・再利用を拒否する named acceptance node が無い (段 6 D-6)。
