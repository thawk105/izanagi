---
schema: izanagi-spool-v1
ledger: failures
authored: 2026-08-26
wave: dev-wave-t1690-hole-literal-only
seq: 3
---

## 新規

### {{F:codex-cannot-write-dot-codex}}. codex 実装子は `.codex/` 配下を構造的に書けず、子は原因を誤って申告した [権限逸脱] [手順漏れ]

- 事象: 段 5 の実装子へ role adapter 2 件の再描画を割り当てたところ、`apply_patch` と通常書込みの
  双方が拒否された。子は完了報告で「`.codex/role-adapters/` が Lustre の `ro` mount」と申告したが、
  親が同じ directory へ `touch` して**書き込み可能**であることを実測した。子の stderr の実体は
  `patch rejected: writing outside of the project; rejected by user approval settings` で、
  codex sandbox が `.codex/` を「プロジェクト外」として扱っていた。
- 根本原因: 凍結境界は「機械設定は実装子が書く」とするが、`.codex/` は codex 自身の設定 directory 名と
  衝突し、sandbox の書込み許可範囲から構造的に外れる。割り当ての前提が実行環境で成立していなかった。
- 誘発要因: 子は拒否の文言を読まずに mount の性質へ帰属した。親も「子が書けない」を額面どおり
  受け取ると、書ける親が書かない理由を誤って引き継ぐ。
- 恒久対応: role adapter の再描画は親が repository 自身の renderer 出力を byte-exact に書き戻す
  **生成操作**として行い、逸脱として記録する。子の prompt には「`.codex/` を触らない。親が描画する」と
  明記する。子の環境申告は根拠にせず、親が実際に書けるかを測る。
- 再発検知: adapter を子へ割り当てた wave で `tools/check_codex_agents.py` が
  `rendered adapter byte parity drift` を返すこと。

## 再発

### F37

- **再発: 2026-08-26** — `check_ai_provenance.py 2>&1 | tail -2` の形で走らせ、`tail` の rc=0 を
  緑と読んだ。実際は commit の `AI-Agent` trailer 3 行が形式違反
  (`model=claude-opus-5[1m]` の角括弧、`scope` に `,` と `/`) で赤だった。既存の恒久対応
  (検査の rc をパイプに通さず単独で取る) をそのまま守れていなかった。未共有 commit 2 本を
  作り直して回復した。trailer を書く前に `docs/ai-provenance.md` の許可文字集合
  (`[a-z0-9][a-z0-9._-]*`) と role の許可値を読む、を運用側の追加規律とする。

### F558

- **再発: 2026-08-26** — 変異 probe の走行中に、記録 fragment の base digest を現行 main の実体で
  採るため親が `merge main` を commit した。harness は `run 中に HEAD が変化:
  expected=70aa7830..., actual=af12562f...` で fail-closed 停止し、6 変異 + baseline が失われた。
  F558 の恒久対応 (HEAD を動かす操作も禁止) が既にあるにもかかわらず、親が「台帳 digest の取得」を
  別系統の作業と見なして同時に進めた。**main 取り込みは変異の前に済ませる** — そうすれば
  base digest も同時に確定するため、順序としても自然である。今回は orphan hold も一時的に張られたが
  harness 自身が撤去していた。

### F57

- **再発: 2026-08-26** — 受入全走 attempt 2 (16657 passed / 1 failed / 60 skipped) で
  `test_sigterm_ignoring_child_is_killed` が 1 件落ちた。assertion 本文は
  `child.pid was not registered before deadline; stderr=''` で、launcher の子が
  **2 秒の deadline 内に child.pid を登録しなかった**という時間依存の主張である。
  同一 tree の単独走は 202 passed / 8.27 秒で再現しない。当該 wave の差分 20 file に
  `tools/` は 1 つも含まれないため帰属しない。**落ちる node がまた移動した** (attempt 1 は
  `test_s8b_floor_campaign.py` の `output/` snapshot 系 11 件 +
  `test_s8b_oracle_driver.py` 1 件で、attempt 2 では全て緑)。
  `orchestrator/tests/flaky_test_holds.py` への登録は、検証器が
  「evidence F の本文が test 関数名と failure_signature を逐語で含むこと」を要求するため、
  本再発が canonical へ fold されるまで**構造的に不可能**である。この 2 段依存
  (hold は既 land の証拠を要求し、証拠の land は受入 green を要求する) 自体が
  非帰属 flake で塞がれた wave を land 不能にする経路であり、裁定パッケージへ送る。
