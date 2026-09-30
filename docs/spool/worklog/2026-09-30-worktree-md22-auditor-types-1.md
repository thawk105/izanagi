---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-09-30
wave: worktree-md22-auditor-types
seq: 1
title: [T-2890] auditor に gen-opt の入力 3 つと型 27〜30 を足す — 役割本文・pin 追随・生死確認 16 call (gen-opt md_22、branch worktree-md22-auditor-types)
---

## 本文

- 一次資料: `output/insights/2026-09-30/gen-opt-auditor-types/README.md`。役割本文は追記だけ (既存の文・frontmatter・出力契約は不変)。
- 承認の根拠: D2214 / `docs/axis-onboarding.md` §5 の「`.claude/agents/` の変更はユーザー明示承認」は、ユーザーが自ら起動した md_22 が対象 file・入力 3 つ・型 27〜30 を名指ししたことで満たすと段 1 で仮裁定し、段 3 の 2 レンズとも妥当と判定。差分は gen-opt-correctness-gate §6 の範囲に限った。D2256 項 7 (T-2865 の具体差分の承認) は流用していない。
- 段 4 裁定: Codex manifest の型上限 26→30 (P4) は撤回 (runtime-blocked・型範囲の一致を検査する checker なし・従属 pin が増えるだけ)。Q の食い違いは向きを問わず型 30。gen-opt の監査の識別を入力の有無から切り離す (入力を欠いた候補の pass 経路を塞ぐ)。持ち越しを [T-2888] へ吸収する案 (B-7) は不採用 — [T-2888] は走行中の md_20 が更新・完了する item で、並行 wave の fragment が触る item に触れない (spool 規律)。
- 段 6: review 2 本が NO-GO (役割本文 R1・B3、probe の判定器 R2・R3・B1・B2・B5)。役割本文は親が 1 行修正 (16 (d))、pin を再追随、probe は Codex fix 2 巡。B4 (文の圧縮) は判定を変えないので nit として不採用。焦点再レビュー 1 本は役割本文と pin を GO、probe の判定器の甘さ 2 件 (総合判定が全行一致を要求しない、場所の語を note でも認める) を NO-GO とした。これは probe (repo 外) の判定器を直さず、親が 16 件の実応答を location 欄と Q7 の両値で直接照合して閉じた。
- 生死確認 (16 call、login の `claude -p --agent auditor`、サブスク): 記録 3 件 (series-c) の prompt は byte 一致で作り直せ、変更前後とも pass・違反 0。lock order 軸の fixture 8 件で、変更後 role は N0 pass・M/F uncertain・壊し 5 件すべて期待の型を含む reject。事前登録の判定器は判定対象 14 行中 13 行一致 (B27 は場所の語だけで外れ、location は注入式を逐語で指す)。n=1、文法を通る壊し入力は B30r だけ、fixture は人が作った。
- 変異: harness の M1 (台帳の pin を古い値へ) は `test_codex_agents.py` の import 時の `SOURCE_FILE_SHA256 drift` 例外で収集 error 48 件となり harness は PARSE_ERROR で停止した (拒否側には倒れている)。M1・M3 (役割本文の pin 後改変) は独立 clone への側走で `check_codex_agents.py` rc 0→1 を観測し復元、harness は M0 (等価) と M2 (reflux 基準) で回した。結果は一次資料 §7。
- セッション異常: 段 5 の実装子 2 本が 1 回目、依頼文の「同じ directory の common-5.txt」を job dir で探して即停止 (親が request-common-5.txt へ改名して複写していた)。段 6 の review 2 本が 1 回目、必読列挙の path 表記の曖昧さで即停止。どちらも実装なしで再投入。adapter は Codex sandbox が `.codex/` を read-only にするので親が生成器出力を適用 (D105 waiver、2 commit)。
- 工数: codex 相談 2・author 2 (+空振り 2)・fix 3・review 2 (+空振り 2)・焦点 1、Explore 1、焦点走 2 (計算ノード、各 Elapse 約 1 分)、変異 dispatch 3 本 (probe 2・final 1、final は Elapse 約 144 秒)、`claude -p` 16 call (合計 1,843 秒)。
- land 調整役の通達 (2026-10-01 00:3x、同原因の失敗を繰り返さない・自己点検) に対し、F819 型の 2 回を該当ありとして SELF-REVIEW を送った (failures fragment seq 2)。

## 次の一手差分

### 完了

- [T-2890] auditor の役割本文に gen-opt の入力 3 つ (`mechanism_spec`・`model_check_summary`・`q_declarations`) と型 27〜30・チェックリスト 16 を足し、pin 3 か所を追随し、生死確認と変異を記録した。
  remaining: none
  base: b6a8c77ebf54127be07c42127371fe881cc7e825f9dc4ac0d5cedc3197fafa39

### 新規

- {{T:gen-opt-auditor-input-assembly}} **P3・新規**: gen-opt の軸の driver が auditor を呼ぶとき、入力 3 つを `output/insights/2026-09-30/gen-opt-auditor-types/README.md` §1.2 の field 名で組み立て (`model_check_summary` は小モデル結果の要約で性能値を含めない)、`designated_sources` に骨格・呼出し経路の source を含め、spawn prompt で「gen-opt の仕組みの軸、違反型は 1〜30」と伝え、`max_violation_type=30` で読む。申告と auditor の独立回答の食い違い (型 30) を拒否として扱う。Codex adapter を実行可能にするときは manifest の入力 schema と出力の型上限 (26) を役割本文に合わせる。前提: [T-2888] (driver 接続、md_20)。根拠: 同 README §5。
