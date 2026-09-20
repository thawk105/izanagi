## must-fix

なし。数値の転記ずれ、pair 成立への誤った昇格、停止規則違反は確認しませんでした。

## should

- **real —「fresh tree が claim でも必然」は断定が強すぎる。**
  [insight README:98](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2795-k2-pair/output/insights/2026-09-20/t2795-k2-pair-attempt/README.md:98)、`reviews/diagnosis-pair-0001.md:38`。コードが示すのは、**既存 claim を残した同 out_root・同 identity の再起動が拒否されること**です。claim の所在は output root に従うため、fresh なソース tree 自体の必要性までは導けません（`loop.py:215`、`layout.py:389`、`campaign_claim.py:427`）。記述をこの拒否条件までに限定するのが適切です。
  **成果物影響（DW-G05）:** 過去の fresh-tree 運用を、機構上唯一の選択肢だったと誤読させる。今回の停止判断・測定値への影響はありません。

## nit

- **real — 診断メモに TL の訂正前の説明が残る。**
  [diagnosis-pair-0001.md:35](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2795-k2-pair/output/insights/2026-09-20/t2795-k2-pair-attempt/reviews/diagnosis-pair-0001.md:35) は TL を「stub `run_campaign`」と要約していますが、実関数を戻す test もあります（`orchestrator/tests/test_p3_s4_loop.py:10107`、`:10171`）。本体 README:94 と段4裁定:9 は正しく訂正済みです。診断メモにも訂正注記があると明瞭です。
  **成果物影響（DW-G05）:** 診断メモ単独で読むと、テストの不足範囲を広く解釈する余地が残ります。

## 照合した数値 (一致)

[insight README:51](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2795-k2-pair/output/insights/2026-09-20/t2795-k2-pair-attempt/README.md:51) の表を原本と照合しました。

| 対象 | 一致した値 |
|---|---|
| job | `13339.nqsv`、`0:13339.nqsv`、`bnode032`、Created 19:12:26／Started 19:12:36／Ended 19:13:45 JST |
| 終了情報 | Elapse 74秒、残10,726秒、候補 rc=0／stock rc=1、集約 `driver_rc=1` |
| identity | campaign `b24749ae`、候補 `002642c7ac96`、genome全文、stock期待ID `602b4ce9c788` |
| admission | `coder-authored`／`cli-opt-in`、policy `db6bc9ea…`、receipt `d3a481b7…`、src_token `fec064b1…` |
| build | trace `6c87eb2ecf19686e…`／perf `7a60310d588b89c7…`。**binaryも sha256sum で一致**。両方非cache、19:13:10→19:13:25 |
| verify | serializable／certified、commits 522,868、aborts 121,826、anomalies 0、witness `{522868,0}`、X/P present・I absent、19:13:38 |
| bench | median 811,956、反復 `[817565,806347]`、CV 0.976940…%、settled=true、wall 2.129355…秒 |
| abort率 | perf `0.09155×100=9.155%`、verify `121826÷644694×100=18.896716…%→18.9%` |
| claim | pid 2080612、proc_starttime 50445791、作成UTC、boot/job/host/identity/protocol_digest が一致 |
| 終端 | WAL 5 record、1 committed／0 aborted／0 skipped、iteration=1、continue。stock recordなし |

`sha256sum` 再計算は全桁一致しました。

| campaign資料 | SHA-256先頭 | bytes |
|---|---|---:|
| WAL | `b5754f98…` | 7,062 |
| lock | `962ef7d7…` | 8,307 |
| loop_state | `a8c6a8b6…` | 255 |
| digest | `8bde66fa…` | 1,939 |
| knowledge receipt | `c42dc712…` | 1,317 |

- **refuted — 正規化で内容が変わった疑い。** README:153 の記録どおり、stdout は `84b63d00…`／12,567 B → `f0a96ab5…`／12,563 B、consult-a は `2838aa60…`／8,055 B → `63e9711f…`／8,047 B。変更はそれぞれ2行・4行の末尾空白だけで、両方 `diff -w -B` rc=0。他の保存 evidence 4ファイルも原本とハッシュ一致。
  **成果物影響:** 証拠内容の変質なし。

- **refuted — 停止理由・主張限定の逸脱。** README:19、`:32`、段4裁定:19、逐語依頼:9 が整合。STOCK未確認、pair不成立、再投入なし、4巡目未投入、非同時刻の追加評価、claim削除・退避なしを明記。禁止表現は否定・却下の文脈です。qsub出力と evidence は各1件でした。
  **成果物影響:** 対照成立・性能優劣・診断効果への昇格なし。

- **refuted — claim機構の主要説明の誤り。** `campaign_claim.py:356`／`:411`／`:421`、`loop.py:205`／`:236`、`layout.py:599`、`env_contract.py:260`／`:300`、test:9676 が説明を支持。condition gate 正常復帰は `p3_s4_loop.py:1969`→`:1986` と traceback から確認できます。ログの終端原因はclaim衝突のみです。
  **成果物影響:** 停止点とテスト不足範囲の主要判断は妥当。

- **refuted — fragment形式違反・凍結稿変更・禁止成果物の複製。** worklog:10／:40／:42／:52、failures:9／:11／:13、decisions:9 は各書式に適合。base digest `f52cdc40…` は読取専用lookupと一致し、placeholderも3 fragmentで一致。paper-story:64／:69／:208 の件数・追補は整合。実装・凍結稿の差分なし、round3は末尾16行追加のみ、launcherは3行追加のみ。新規ファイル一覧に保護対象campaign成果物の複製なし。
  **成果物影響:** 台帳形式・凍結境界を維持。指定一次資料の欠落なし。

## 総括

**GO（記録レビューとして）。** 数値・ハッシュ・正式停止の主張限定は一次資料と一致しています。
非阻害の文言所見が should 1件、nit 1件あります。
書込み・テスト実行は行っていません。