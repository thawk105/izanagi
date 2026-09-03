---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-09-03
wave: dev-wave-t2183-knowledge-provenance
seq: 1
title: [T-2183] 知識水準と 2 段の知識源を材料レポートへ記録した — 台帳と identity への束縛は着手前から landed で、純増はレポート側だけだった (コード + テスト + docs + insight、branch worktree-dev-wave-t2183-knowledge-provenance、変異 6/6 KILLED + 等価変異 1)
---

## 本文

タスクが最初に要求した測定 (既存 `policy_hint` の記録経路へ相乗りできるか) の答えは
**「機構は相乗りできる、欄は相乗りできない」**である。campaign lock を出所として材料レポートの
top-level へ名前付き欄を置く経路はそのまま再利用でき、schema 版も上げずに済んだ。一方
`policy_hint` の欄そのものは単一スカラで、2 段の source 集合を載せられない。したがって新しい欄を
1 個だけ設計した。判断は {{D:knowledge-provenance-rides-policy-hint-path}}。

**着手前の実測で scope が大きく縮んだ。** 知識 manifest の parser / producer、受領証、
campaign identity への束縛、試行台帳 BUILD_START の provenance とその双方向検査は、いずれも
着手時点で landed だった。実成果物の lock にも知識水準と manifest digest が入っており、受領証の
digest と一致していた。純増は材料レポート側だけで、着手時点で当該 3 file に "knowledge" の
出現は 0 件だった。

**親 brief の一般化が段 3 で 1 件訂正された (棄却)。** 親は「材料レポートに記録経路が無い」と
書いたが、レポート生成器は台帳 record を丸ごと変異体の event 配列へ入れるため、BUILD_START の
provenance payload は既に逐語で載っていた。純増は「名前が付き schema で拘束され受領証まで
束縛された射影」であって、データの新規搬入ではない。

**2 段の関係は既存検査が決めていた。** 試行台帳の受領証読み出しは、検証済み source 集合と宣言
source 集合の不一致を既に fail-closed で拒否している。したがって 2 段は現行 producer では必ず
一致する。この一致を新しい述語で確かめても恒真になるため足さず、受領証の既存 2 欄から
それぞれ独立に射影する形にした。判断は
{{D:two-tier-knowledge-record-projects-existing-receipt-fields}}。**一致は等価変異が生き残った
ことで実測した。**

**段 2 プランと段 3・6 のレンズが出した提案のうち 7 件を scope 外として不採用にした。** 受領証の
新世代、実行経路の新しい停止条件、投入集合の独立 digest による identity 変更、lock の 3 状態分岐、
payload 本文の再 hash、schema 後段の semantic validator、知識対応 legacy レポートの比較補正。
最後の 1 件は発火する成果物が 1 件も存在せず、提案された是正が provenance を欠いたレポートを
黙って通す向きだったため棄却した ({{D:legacy-knowledge-report-comparison-not-patched}})。

**段 6 レビューの must-fix 6 件のうち 4 件を採用した。** 2 段が同じ配列の複製だった件、
一致検査を守る負例が無かった件、受領証を検証した read と参照一覧の read が束縛されていなかった件、
事前登録した変異 2 件が単一理由性を満たしていなかった件。残る 2 件は上記のとおり棄却した。

**変異手法の制約を実測した。** `contract_loader_blob_sha256s` の member へ打つ変異は、変異注入
そのものが drift を作るため前段で全赤になり帰属できない。probe 1 で 109 node / 111 node を観測し、
2 件を閉包外の file へ再照準して probe 2 で単一 node を確認してから本走した。F357 へ再発として
記録した。

**エージェント工数と異常。** Codex 子は段 2 プラン 1 本、段 3 敵対相談 2 本、段 5 実装 1 本、
段 6 敵対レビュー 2 本、段 6 fix 1 本の計 7 本。実装子と fix 子はいずれも sandbox から pytest
child を起動できず (`rc=16`、`qstat` の socket error)、**テストの実走はすべて親が行った。**
子の非実走を緑として数えていない。`tools/dev_wave_submodule_init.py` の新規 worktree 初回初期化が
既定 timeout を超えて 1 回赤になり、手動初期化後の再走で緑になった。

**主張の境界。** 記録するのは harness が解決・検証して role 入力へ投影した知識源であって、
モデルが実際にそれを読んだ証明ではない。K2 を条件とする certified な最終選択を主張してよいかは
本 wave では判断していない。Web 由来の取得内容 digest による再検証も成立していない — manifest
schema は全 kind に digest 欄を必須とするが live 解決は未配線のままで、本 wave は受理 kind を
repo 内成果物に固定した。

一次資料は `output/insights/2026-09-03_t2183-knowledge-provenance/`。段 2・3・5・6 の子出力の
逐語、変異 spec、本走台帳、probe 2 本の結果を凍結した。

## 次の一手差分

### 完了

- [T-2183] 材料レポートへ知識水準と 2 段の知識源を記録する名前付き欄を足し、campaign identity・
  試行台帳・受領証の三者へ束縛した。試行台帳と identity への束縛は着手前から landed であり、
  純増はレポート側だけだった。変異 6/6 KILLED + 等価変異 1 件、受入全走緑。
  remaining: none
  base: 5542c2981e2c346b32a650573c6b8e48043cbd45aea031648078c3eee1a3720f
