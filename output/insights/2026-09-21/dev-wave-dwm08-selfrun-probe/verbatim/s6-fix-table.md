# 段 6 レビュー A の所見 → fix 対応表 (DW-O16、親が作成、2026-09-21 07:58 JST)

| # | 判定 (レビュー A) | 親の裁定 | 対応 | 状態 (親の自己申告、焦点再レビューで判定) |
|---|---|---|---|---|
| 1 | real / must-fix — 純増ゼロは成立しない (注入先 部分被覆、起動方法 未被覆、復元後 clean 未被覆、実測値 不一致) | real / 採用 | commit 956cce1c9: DW-M08 に (a)「対象commitの木へ」(b)「`PYTHONPATH=. python3`の自走harness」(c)「sha256と`--porcelain`空も照合」を収容。regex は意図的に固定しない (所見 5 と同じ理由)。実測値は所見 2 で処理 | closed (申告) |
| 2 | real / must-fix — 「実測値同一」は誤り (1 分 ≠ 2 分) | real / 採用 | brief-v2.md 項 1: 撤回し、依頼文 = 1 分、D2195 = 2 分、fig13 job dir の mtime (20:19:35 → 20:21:05、≤ 90 秒) を出所付きで併記、統一しない。「着地前の写し」の根拠を限定 | closed (申告) |
| 3 | refuted — collect-only は skip を検出しない (親の主張を追認) | — | 変更なし | n/a |
| 4 | real / nit — skip 名指しは規範上冗長、削除候補 | real / 不採用 (削除しない) | 依頼が名指しを明示し、レビューも「見落とし防止として有用」。brief-v2 項 4 で「具体例の明示、新しい防壁ではない」と位置づけを訂正 | closed (申告、文面は不変) |
| 5 | refuted — regex を固定しない判断は妥当。brief は「被覆済み」でなく「意図的に固定しない」と書くべき | real (brief の書き方) / 採用 | brief-v2 項 3「意図的に固定しない」へ | closed (申告) |
| 6 | refuted (緩和なし) / nit (明瞭さ) | — | 変更なし (位置・語形は維持) | n/a |
| 7 | refuted (+7 bytes 正しい) / 判定不能 (9681 の独立再集計) | — | `verbatim/layer_bytes_956cce1c9.txt` に script 出力を写し、`measure_budget.py` を job dir へ置いた (再集計可能) | closed (申告) |
| 8 | refuted — 本文 literal pin なし (追認)。「節 ID と予算だけ」は粗い | real (表現) / 採用 | brief-v2 項 6「節 ID 在庫・dispatch 配置・層予算で束縛」へ | closed (申告) |
| 9 | real / should — 「final 1 回空振り」は可能性、実測ではない | real / 採用 | brief-v2 項 4「空振りの回数は未実測」、README でも可能性として書く | closed (申告) |
| 10 | refuted — scope 外ではない、新 D なしも整合 | — | 変更なし | n/a |
| 11 | 判定不能 — entry 1774 / FOLDED 行 / tested_tip は射影外 | — | 親が一次資料で確認済み (archive file・FOLDED.md 5133–5134 行・commit 33de1a3ea)。焦点再レビューには読めるよう path を射影に入れる | partial (子の検証は焦点再レビューで) |
| 12 | real / should — D2195 本文は fix 1 前の条件を保持 | real / 採用 | brief-v2 項 7、worklog fragment で相違を明記 (canonical は追記のみ) | closed (申告) |

fix の commit: 956cce1c9 (docs のみ、`verbatim/commit-956cce1c9.txt`)。空白・改行を除いた差分: `verbatim/semantic_diff_002f926f4_to_956cce1c9.txt` (追加語 3 + 助詞 1 字)。
