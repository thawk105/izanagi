---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-09-26
wave: worktree-dev-wave-t2865-silo-policy-stage-e
seq: 1
title: [T-2865] silo-function-policy 軸を段階 E へ進めた — planner なしの兄弟 driver が C++ 形と IR 形の proposal を共有検疫・型付き構文検査・単独 TU compile・auditor の digest 照合の順に通し、coder の入力は偵察の二値と射程文と自系列の履歴だけから組む。coder role 2 本と auditor 改訂はユーザーの明示承認の後に入れた。計算ノードでの実走と投入用 job body は段階 F の前提へ送った (コード + test + role + runbook + insight、branch worktree-dev-wave-t2865-silo-policy-stage-e)
---

## 本文

- 依頼 (ユーザー直接起動の `/dev-wave`、逐語 = insight `output/insights/2026-09-26/t2865-silo-policy-stage-e/verbatim/request.md`): D2243 項 1 に従い段階 E (兄弟 driver・tool なし coder role の C++ 版と IR 版・runbook・firewall の機械化) へ進める。記録 = 同 insight の README、設計判断 = {{D:silo-policy-stage-e}}。
- 起点 = local main `6d198ca8a` (fresh worktree、開始 gate rc=0)。wave 中に local main を 3 回取り込んだ (`7c1b53a4b` を `1be932610`、`25655d808` を `1187c5a98`、`299aa022e` を `42b84ed0c` で。3 回目の `test_campaign.py` は両親と異なるので、3 版から Codex に独立に合成させ自動 merge の blob と sha256 一致を確かめた)。正しさ防壁 (検疫・auditor gate・verify 構成) と受理集合を新設するので、軽量版にせず段 2・3 (3 レンズ) と段 6 のレビュー 2 本を回した。
- **ユーザー承認:** `.claude/agents/` の具体差分 (coder role 2 本の新設と auditor 改訂) を 19:5x JST に提示し、回答は「承認する (推奨)」。role 登録簿を 14 → 16 件に追随した。
- **段 4 の主な裁定:** 親の暫定案 (共有 `quarantine()` に本軸の分岐を足す) を段 3 の 3 本の一致した指摘で撤回し、driver 側で共有検疫の後に構文検査・単独 TU を掛ける。`prior_critic_reverse` を proposal から除き停止は予算だけ。手書き 2 形の計算ノード実走と job body は E の完了条件から外した (相談 C)。
- **段 6:** レビュー 2 本とも NO-GO、焦点再レビュー 1・2 も NO-GO、fix 4 本の後の焦点再レビュー 3 で GO。親が runbook を起草して見つけた欠落 3 件 (auditor 前の preview ができない、critic 診断の入口が無い、preview で拒否された候補が履歴に載らず次の coder が自分の拒否理由を受け取れない) を fix に入れた。焦点再レビュー 2 の「anomaly の辺の key の検証」は仮想リスクとして不採用 (焦点再レビュー 3 が妥当と判定)。
- **既存 test の束縛の変更:** MOCC template proof の test が auditor.md の whole-file sha256 を proof (2026-09-19 記録) と照合しており、承認済みの auditor 改訂で赤になった。束縛を記録した MOCC 用 auditor 項目と現行項目の一致に置き換え、proof は取り直していない (規律 7)。
- 焦点走 4 回 (計算ノード、Elapse 計 466 秒)。最終 (`650b9b80c`、39 file) は 4417 passed / 0 failed / 12 skipped。途中の非帰属の赤 1 件は、焦点走の待機中に親が runbook を未 commit で編集したことによる (走行時点の作業ツリーを見る既知の型)。
- 変異 matrix: final 16 / 16 KILLED。M-E5 の最初の形は `parse_auditor_dict` 自身の既定値を外した照準漏れで probe が SURVIVED、照準し直して検出を確認した (erratum は insight §5)。runner 時間の合計 2,544 秒 (待ち行列込み)。
- 計算: E の計算は焦点走・変異・受入だけで、図は作らない。受入の値は land の受領証に残る。
- **受入 1 回目 (22:18〜22:37 JST、post-claim merge で main `6c3913bc5` を取り込み) は 27,706 passed / 5 failed。** 本 wave 起因 2 件: 新 test file が pytest 専用 allowlist に無い (`test_plain_runner_coverage`、F42 の再発) と、reflux の wave 前基準が auditor.md の sha を持っていた (`test_reflux_originless_compatibility`、F30 の再発の 2 件目)。前者は allowlist に 1 行、後者は過去の role 改訂 wave と同じ型の追随関数 (Codex fix 5) で閉じた。残る 3 件 (`test_t810_coordinator` の「worktree registration が読めない」) は本 wave の差分 (tools/pegasus・git 識別に未接触) から到達しないので、単独再走で再現の有無を確かめてから受入を取り直す。
- 実行上の事実: Codex の実装子は sandbox から qstat を呼べず、login の直接 pytest は hook が拒否するため、どの子も pytest を実走できなかった。role の子は `.codex/` への書込みも拒否され、生成した adapter の bytes を親が配置して `tools/check_codex_agents.py` で期待 bytes との一致を確かめた。親が短縮 SHA を推測で延ばして branch 作成に 1 回失敗した (rev-parse で取り直した)。
- 工数: Codex 子 = plan 1、consult 3、author 2 (core・role)、review 2、fix 4、focus review 3、merge 合成 1 の計 16 本。

## 次の一手差分

### 更新

- [T-2865] **P1・段階 E 完了 → 段階 F (別 session、実 LLM の 1 iteration E2E)**: silo-function-policy 軸 (D2214) の段階 E を {{D:silo-policy-stage-e}} で実装した (driver `orchestrator/campaign/p3_s4_loop_policy.py`、coder role `coder-v4-autonomous-policy` / `-ir`、runbook `docs/phase3-silo-policy-runbook.md`、記録 `output/insights/2026-09-26/t2865-silo-policy-stage-e/README.md`)。F の前に要るもの (AI 側): (1) 本 driver 用の計算ノード投入経路 (`tools/pegasus/p3_s4_loop_pegasus.sh` は `p3_s4_loop` 固定。driver 選択か兄弟 job body と契約 test・投入許可台帳)、(2) fresh session、(3) 同じ動作点の stock baseline の測り方、(4) 投入前に job Elapse の実測単価で見積もり、検査込みのタスク合計が 2 node 時間以上ならユーザー確認 (D2212 項 4)。coder・planner の入力へは段階 D の projection.json の二値と射程文だけを渡し、偵察・小比較・再測 (D2240・D2250) の点 ID・因子・比・順位は流さない (手順書 §3 D)。越えた 3 点の別 job 再測は D2250 で済んでいる。
  base: a27cd7ba66e35a12afdcfdc80d8679515bdb43e5394f40e0b4f8c1700d86a454
