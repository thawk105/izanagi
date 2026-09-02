---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-09-02
wave: dev-wave-t2145-sort-oracle-ir
seq: 1
title: [T-2145] sort SWO oracle の受理言語を検証済み IR へ縮めた — 受理集合は文字列として真に縮み、行列の出所を候補実行から trusted evaluator へ移した (コード + docs + insight、branch worktree-dev-wave-t2145-sort-oracle-ir、変異 11/11 KILLED)
---

## 本文

- **着手根拠は D1451。** 台帳は「[T-2076] の裁定待ちが解けるまで着手しない」と書いていたが、
  2026-09-02 の /rulings 全件で裁定済みになっていた。現行 main の blob で逐語を照合して着手した。
  **D344 が却下理由に挙げた実験同一性の論点は supersede されていない。** したがって本 wave の
  成果物には「D39 の raw C++ 独立合成の実証点を別実験へ移す変更である」と明記し、
  D344 を supersede したとは記録していない。合成子の契約と `spec_content` にも同じ旨を書いた。
- **台帳が着手時に閉じよと定めた 4 設計点はすべて閉じた。** 受理権威の役割分離 ({{D:sort-ir-acceptance-authority}})、
  pointer 意味論の確定と contract 束縛、受理集合の包含、certified 15 組との分離である。
- **別セッションからの指摘を 1 件受け、現物照合で解決した。** /next-tasks の母集合を測っていた
  セッションが「[T-2076] は裁定待ちのはず」と警告してきた。相手のスナップショットが
  main `cab0a265f` (worklog entry 1178) 時点で、そこから一括裁定 2 本 (entry 1184 / 1188) を
  見落としていた。現行 main の blob で D1451 の実在を示して解決し、相手も自分で照合して撤回した。
- **段 3 レンズ B が親 brief の誤りを実測で覆した。** brief は「oracle test は D669 で受入全走から
  恒久除外されている」と書いていたが、`orchestrator/test_selection_contract.py` の
  `SANCTIONED_EXCLUSIONS` は空 tuple であり、当該 file は受入全走に載る。D669 は decisions に
  残るが実装側の表だけが空になっている。**現行コードを事実として扱い**、新設する 79 値の
  実 TU 照合を単一 batch TU 1 回 compile へまとめた (照合セルは 153,576 全件のまま減らしていない)。
  D669 と実装の不一致そのものは本 wave の主題ではないので追っていない。
- **段 6 は 5 巡を要した。うち 2 巡は子が 1 件もテストを走らせられなかった。** 計算ノードの
  キュー待ちタイムアウト (`rc=16`、`child_started=false`) が断続的に続き、段 5 実装子と
  fix 第 1・2・3・4 巡がいずれも pytest 0 件で終わった。`DW-O16` の 3 巡上限は
  「親の実機 blocker は別枠」としているので、実測不能だった巡を NO-GO と数えなかった。
  実走はすべて親がキューの空きを捉えて行った。
- **fix 第 2 巡は変更ゼロで正しく停止した。** campaign ID の期待値が段 4 裁定 R4 と両立しないと
  判断し、「期待値が誤りだと判断したら実装を変えずに報告して止まれ」の契約どおり親へ返した。
  親は D345 (受理集合を変える gate の契約 ID は campaign identity へ焼く) を根拠に
  「golden の更新は緩和ではなく追随」と裁定した。`081dd46f` の pin 閉包を全件検索し、
  生きた golden 1 件だけを更新、過去 insight 5 箇所の歴史記録は 1 文字も触っていない。
- **親が段 1 の pin 閉包検索を 1 件落としていた。** `.claude/agents/*.md` は
  `orchestrator/codex_roles/review_ledger.py` の `SOURCE_FILE_SHA256` で pin されている。
  brief の実アンカー表に agent file を挙げながら、それを鍵にする pin を探していなかった。
  焦点走 8 件の赤のうち 3 件がこれに起因した。role file の pin 更新は先例に従い
  **起草者と別の実装単位**が行い、親の独立レビュー証跡を insight へ置いた。
  adapter JSON は tool が `--write` を封じているため、親が renderer の期待 bytes を
  review して適用した (差分は `developer_instructions` と `semantic_digest` の 2 key のみで、
  権限・起動可否・モデル方針・I/O 契約は不変)。
- **親が main 取り込みで実害のあるミスをし、実走で検出して修正した。** 競合解消の際、
  子が clean な作業ツリー (取り込み前 HEAD) で作った解決済み file を**丸ごと**マージ結果へ
  上書きし、main 側の `knowledge_manifest` 関連 13 箇所を黙って捨てた。マージ後の実走が
  5 件の赤を出して発覚した (静的な合成監査は「問題なし」と報告していた)。マージをやり直し、
  **競合したハンクだけ**を解消して再 commit した (766 passed へ回復)。
  「自動マージが綺麗でも意味的に壊れうる」の実例が自分の手で起きた形である ({{F:merge-resolution-whole-file-overwrite}})。
- **親が直接解消した最初の試みは provenance 検査が拒否した。** 「実装面に Codex role=author が
  ない」として止まった。検査の判定が正しい。競合していない `test_p3_s4_loop.py` も指摘対象に
  含まれており、**両親と異なる実装面になった時点で著者の関与が要る**という設計だと分かった。
  迂回していない。
- **エージェント工数:** plan 1、consult 2 (並列)、author 1、review 2 (並列)、fix 5、
  merge 解消 2 (1 本は merge 途中の worktree で hook に弾かれ rc=2)。計 13 本。
- **セッション異常:** merge 途中の worktree では `tools/pegasus/admission_registry.json` が
  HEAD blob から drift するため、codex の子が stage 非依存で rc=2 になる。
  merge 解消を子にやらせる設計は、clean な作業ツリーへ材料を射影する形に組み直す必要がある。

## 次の一手差分

### 完了

- [T-2145] 受理言語を 79 値の検証済み IR へ縮め、関係行列の出所を trusted evaluator へ移した。
  焦点走 766 passed / 2 skipped、変異 11/11 KILLED (baseline 緑、識別子 churn 2 件を差し引いても
  全件が機構固有の落ち先を持つ)。
  remaining: none
  base: 4b4bb7965bd044965820b64f46dcbc32d49ff1a14ae3946645cc6b1b405b80d6

### 新規

- {{T:sort-ir-acceptance-ledger-followup}} **P2・新規**: `acceptance_duration_ledger.json` を
  本 wave の新設・改名 node へ追随させる。少なくとも 26 node が現行 ledger に無く、旧名も残る。
  値は合成せず実測 JUnit から再生成する。**ledger 未更新だけを理由に赤になる検査は現状 0 本**
  なので受入は通るが、scheduling は古い参照を使い続ける。
- {{T:d901-grammar-version-cache-binding}} **P2・新規・ユーザー裁定待ち**: D901 条項 2 が
  backoff 軸へ課している「文法の版を identity・WAL・cache の三脚へ束縛する」を、
  sort 軸へも一般化するか。sort は contract ID 経由で identity と WAL には届くが
  **build cache key には届かない**。親の推奨は **backoff 限定のまま維持**である
  — `DW-G03` の族一般化 (独立 2 例) を満たさず、certified 値・受理集合・参照が変わる具体例も
  未確認のため。一般化を選ぶ場合だけ別 task を起こす。
- {{T:d669-exclusion-table-drift}} **P3・新規**: D669 は
  `orchestrator/tests/test_sort_swo_oracle.py` の受入全走からの恒久除外を決めているが、
  実装側の `SANCTIONED_EXCLUSIONS` は空 tuple で当該 file は受入全走に載っている。
  除外を解除した裁定は見当たらない。decisions と実装のどちらが現行かを確定する。
