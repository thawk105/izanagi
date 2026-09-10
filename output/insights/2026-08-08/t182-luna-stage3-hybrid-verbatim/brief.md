# 段 1 brief — dev-wave-t182-luna-stage3

起点 main: `6cc3e59a` / wave branch: `worktree-dev-wave-t182-luna-stage3`

## scope

段 3 敵対相談 (`DW-S03`) の codex model を `gpt-5.6-sol` から `gpt-5.6-luna` へ置換する。
`reasoning=max` と `sandbox=read-only` は変えない。段 2 (`DW-S02`)、段 5 (`DW-S05-A`)、
段 6 の model は変えない。あわせて置換によって生じる `DW-O01` との precedence 不整合を閉じ、
model slug の drift を機械 pin で検出できるようにする。

## 確定済みユーザー裁定 (逐語)

> 段3敵対相談をsol@maxでやってると思う。[T-182] luna が 91%の能力を発揮し、
> トークン効率を30%よくしているならば、luna maxに置き換えてほしい

置換は**この裁定を根拠とする**。[T-182] の被覆率 (11 件中 10 件、token −31.6%) は
同 ID 自身が「循環・非盲検・事前登録なし・n=1 のため policy 根拠にしない」と記録しており、
**証拠に基づく採用として docs に書いてはならない**。[T-184] (証拠に基づく既定 policy 採用) と
[T-189] (妥当な比較実験の設計) は open のまま据え置く。

## 段 1 実測 (2026-08-08、本 worktree、ログインノード)

- `codex exec -m gpt-5.6-luna -c model_reasoning_effort="max" -s read-only` は **rc=0**、
  CLI reported **13,017 token**。F56 (b) の「消費 0 の見せかけ成功」ではない。
  指定 2 節を実読して 3 問に正答した。逐語 = `s1-probe/luna.md`
- **served identity は attest できない** (F56 (c))。receipt の model は要求 slug のままである。
  これは sol でも同じであり本 wave で閉じない。[T-189] の所有のまま
- dev-wave reference 4 ファイルの visible bytes 実測 = **25,196 / ceiling 25,200 (残り 4 バイト)**。
  個別 free は core 954 / workers 425 / mutation 76 / operations 99

## 不変条件

1. `reasoning=max` を変えない。D207 の機械 pin (`check_docs` の DW-S02/DW-S03 exact pin) を維持する
2. 段 3 のレンズ本数と read-only sandbox を変えない。検出力を下げる他の変更を同梱しない
3. **byte 予算の上限を上げない。** 安全義務の prose を削って byte を捻出しない
   (`check_docs.py` 冒頭が明示的に禁じている手段目的の逆転)
4. 置換の根拠を「ユーザー裁定」以外に書かない。T-182 の数値を採用根拠として引用しない
5. 旧 policy (`gpt-5.6-sol`) への rollback 手順を decisions fragment に明記する

## 成果物

- `docs/dev-wave/workers.md` `DW-S03` の model 差し替え
- `DW-O01` との precedence 不整合の解消 (方式は段 2 が提案し段 4 で裁定)
- `tools/check_docs.py` に model の exact pin (D207 の reasoning pin と同型、DW-S02=sol / DW-S03=luna)
- `docs/spool/` に worklog fragment + decisions fragment (新 D = 段 3 model のユーザー裁定採用と rollback)
- 新 T-ID (段 3 だけの部分採用である旨と、T-184 が残りを所有し続ける旨)

## 成果物影響 (DW-G05)

段 3 は certified 選択・材料レポート・試行台帳の値を直接作らない。効くのは dev-wave の所見検出力で、
段 3 の見落としが増えれば must-fix の取りこぼしが増え、land する実装の欠陥率が上がる。
機械 pin を入れない場合の影響は、model slug が誰にも気づかれず drift し、
どの model で敵対相談したかが worklog と食い違いうること。

## 親の provisional 裁定 (攻撃対象)

- **(P1)** 段 3 だけを置換し、段 2・段 5・段 6 は `gpt-5.6-sol` のままにする。
  ユーザーが 段 3 と明示したため
- **(P2)** 段 3 の並列レンズを**全て** luna にする。sol と luna の混成 (片肺だけ置換) にしない。
  「置き換えてほしい」の素直な読みだが、混成なら sol の検出力を保ったまま token を減らせる
- **(P3)** precedence は `DW-O01` の model を placeholder 化して解決する。
  ただし `DW-S05-A` / `DW-S06-A` は現在 model を書いておらず `DW-O01` に依存しているため、
  placeholder 化は両節への model 追記を要求し、残り 4 バイトでは収まらない。
  **byte 制約下で成立する方式を段 2 が file:line で示すこと**
- **(P4)** 実装面は `tools/check_docs.py` の 1 関数追加で足りる

## 分割方針

実装単位は 1 つ (docs 1 ファイル + `tools/check_docs.py` + test)。並列分割しない。
docs 本文編集は親、`tools/check_docs.py` と test は Codex `role=author` の実装子が書く。

## 環境

受入全走は Pegasus 計算ノードへ dispatch (`docs/pegasus-runbook.md` §7)。段 1 の probe と
`check_docs.py` 単体はログインノードで実行済み / 実行可。
