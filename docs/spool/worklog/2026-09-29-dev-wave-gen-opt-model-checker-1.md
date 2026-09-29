---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-09-29
wave: dev-wave-gen-opt-model-checker
seq: 1
title: [T-2887] 仕組みごとの小さいモデルでの全場面検査の共通部品を VHash の小モデルから切り出した — 探索・閉路判定・場面の全列挙・閉じた反例 schema、VHash の S8 の途中状態からの探索を共通部品で再現し結果が一致 (コード + test + insight、branch dev-wave-gen-opt-model-checker)
---

## 本文

- 依頼: gen-opt 第 2 陣 md_7 (`/work/1/SFC/tanab/tmp/gen-opt-2026-09-29/md_7.txt`、repo 外)。一次資料 `output/insights/2026-09-29/gen-opt-model-checker/README.md`。`tools/vhash_forwarding_model/` は編集していない。
- 段 4 の裁定: 生きた VHash の実装との照合を常設 test にしない (並走中の VHash wave が model.py を変えるとこちらの test が赤になり帰属が混ざる、相談 B1)。照合は repo 外の使い捨て probe で 1 回だけ行い、結果を insight の raw に置いた。閉路判定の入力は「版の並び = 論理順」を adapter の契約にし、不正な履歴は判定の違反とも不変条件とも別の `ModelInputError` にした (相談 A1・A2)。
- 段 6 のレビュー 2 本はどちらも NO-GO。real として fix したもの: 同じ key に同じ取引の確定版が 2 つある履歴を受理していた、反例 schema に件数上限が無く命令めいた原子文字列も通る (件数上限と任意の語彙照合を足し、語彙を渡して文字列をデータとして扱う義務は U5 側と記録)、時間上限の NaN。MC9 (rw 辺を作らない変異) が 4 test を赤にする指摘は変異の欠陥でなく登録の書き方として、4 node の完全集合で登録した。焦点再レビューは GO (nit 2 件は insight に記録)。一次資料の read-only レビュー 1 本と焦点再レビュー 1 本で、生死確認の範囲・証拠の限界・観測値の型・所要の実測場所・J1 への限定を直した。
- 変異: 19 本 (対照 1 + 1 本 1 条件の 18 本) を login の自走 (repo 外の複製) と計算ノードの束ね経路 1 job で確かめた。結果は insight §4。
- 受入所要台帳 `orchestrator/tests/acceptance_duration_ledger.json` に新 test 9 件を `--add-only` で追記した (共有の登録簿は追記だけ)。
- セッション異常: `EnterWorktree(name)` が "Could not read the repository git config to neutralize filter drivers" で失敗し、`git worktree add` の手動作成 (約 17 分) に切り替えた。続く `EnterWorktree(path)` も `git worktree list` の 10 秒上限で失敗し、cd で代替した (本日の md_2・md_11 と同型)。子木の作成にも約 18 分かかった。
- 工数: Codex は plan 1・相談 2・author 1・review 2・fix 1・焦点再レビュー 1 (いずれも gpt-6-sol)。

## 次の一手差分

### 完了

- [T-2887] 共通部品 `tools/cc_model_checker/` (探索・閉路判定・L3 の場面記述子・閉じた反例 schema) と test を入れ、VHash の S8 の途中状態 (18 手後の prefix) からの探索を共通部品で再現し、訪問数・J1 反例の有無・最短長の一致を確かめた。検査器への変異 19 本は事前登録どおり。一次資料 `output/insights/2026-09-29/gen-opt-model-checker/README.md`。
  remaining: none
  base: 9f9d7c16be6a689d8322d6e45b16a42de2a9be356c2261adc38991b7c7f6b60a
