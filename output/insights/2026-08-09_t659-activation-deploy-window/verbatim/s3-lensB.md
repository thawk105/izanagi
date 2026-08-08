### B-1 durable 識別子の訂正が DW-G05 へ届いていない

攻撃対象: `stage1-brief.md:22,26-27,41`、`stage2v3-plan.md:7-17,102-109,233`

なぜ問題か (根拠): `activation_serial` は process-local で、durable receipt の環境識別子は限定付きの `contract_sha256` です。にもかかわらず brief の成果物影響は「receipt の serial でしか追えない」と残り、plan もこの行を訂正対象にしていません。

実害経路: receipt のない書込み口や据置 env の成果物まで世代帰属できると誤記録し、混在 evidence の受理・再走判断を誤る。`docs/failures.md` の F89/F122 型。

確度: 高

### B-2 P3 の確定事実と未裁定の順序が混在している

攻撃対象: `stage1-brief.md:29-33`、`stage2v3-plan.md:111-125,211-240`

なぜ問題か (根拠): 追補 2 が確定するのは「serial 2 は T-657 の手動活性化、T-659 は serial ≥ 3 対象」です。一方 plan は「serial ≥ 3 は T-659 land まで許可しない」と本文・総括で先に固定し、同じ問いを R3 で再裁定に返しています。

実害経路: 段 4 がユーザー裁定前に activation 順序を既成事実化し、serial 3 の許可集合・実施時期を誤る。

確度: 高

### B-3 P1-D が研究優先・防御的堅牢化見送りを事実上迂回する

攻撃対象: `stage2v3-plan.md:50-69,146-177`、`docs/decisions.md:D205`

なぜ問題か (根拠): 現行 probe は両方向の split を fail-closed で拒否しており、P1-D 自身も runtime の受理集合・値を変えないと記載しています。それでも checker 約 130–200 行、land 改修、テスト約 160–240 行を推奨しています。T-658 の全 receipt 配線を直接復活させてはいませんが、新たな防御的 land hardening です。

実害経路: certified 値を改善しない機構が研究実装帯域と逼迫した docs 予算を消費し、D205 の「科学的妥当性に直接効かない堅牢化は見送り」を迂回する。

確度: 高

### B-4 手順型 quiesce は検査可能性も fail-closed 帰結も未定義

攻撃対象: `stage2v3-plan.md:71-109`、`tools/issue_env_contract_activation.py:143-151,179-213`

なぜ問題か (根拠): 提案手順には lease token、取得状態、証跡、失敗時の abort 条件がありません。既存の受入 lease は campaign process/job を排除しないため再利用不可と正しく指摘していますが、代替の maintenance window は単なる人手確認です。issuer 自体は window を受け取らず、record を発行できます。

実害経路: qstat/pgrep 後に旧 job が開始・fork しても発行が止まらず、fresh process は拒否される一方、cache 済み旧 process は続走する (`env_contract.py:519-586`)。F3/F21/F72/F130 型。

確度: 高

### B-5 SIGKILL 後の回復経路がなく、fail-closed が永久停止へ転ぶ

攻撃対象: `stage2v3-plan.md:27-28,80-91`、`tools/issue_env_contract_activation.py:95-134,179-215`

なぜ問題か (根拠): record publish 後に SIGKILL されると record-only 状態が残り得ます。次回 issuer は `current_activation_state()` で head 不一致になり、再発行できません。plan は「手動 recovery」とだけ書き、手順・権限・安全条件を定義していません。

実害経路: serial 3 の活性化が詰まり、復旧担当が record 削除や head 手編集という未定義操作へ誘導される。F92 型。

確度: 高

### B-6 deployment domain と consumer 被覆が矛盾する

攻撃対象: `stage1-brief.md:17`、`stage2v3-plan.md:42-48,82-109,127-140,181-188`

なぜ問題か (根拠): R0-A は全 worktree/source-stage の official writer を対象にする一方、手順 4 は official root を一つに限定します。さらに generic dispatch には source commit がなく、receipt-free writer・据置 env は `contract_sha256` でも分類不能です。

実害経路: 旧 worktree、queued generic job、receipt-free consumer が対象外のまま旧 head で書込み、混在を検出できない。T-658 の「全書込み口を配線しない」制約を守るなら、その未被覆範囲と certified 対象外の帰結を明示すべきです。F142 型。

確度: 高

### B-7 裁定設問が独立択一になっていない

攻撃対象: `stage2v3-plan.md:80-89,190-219`

なぜ問題か (根拠): R2-A の手順 5 は P1 gate を必須扱いしますが、R1 は runbook-only を選べます。R3-A も P1/P2 land を前提にします。また R3-B の「新材料」が具体的 artifact path・判定者・発火条件を持ちません。

実害経路: ユーザーが各問を個別に裁定すると、P1を不採用にしたのにP2手順だけがP1 gateを要求するなど、実行手順が未裁定の組合せになる。F146/F154 型。

確度: 高

### B-8 runbook の置き場と docs byte 予算が未確定

攻撃対象: `stage2v3-plan.md:166-177`、`docs/pegasus-runbook.md:739-783`

なぜ問題か (根拠): plan は `739–810` を activation 手順の置き場としますが、そこには既存の受入 lease、mutation runner、投入チェックリストがあります。新しい節名・既存節との境界・renumbering がありません。さらに docs/dev-wave は既存記録上 aggregate 残 16 bytes、`operations.md` 残 13 bytes です。

実害経路: runbook の既存契約を重複・誤配置し、将来実装時に `check_docs.py` の byte ceiling を超えるか、必要な手順を削る。F90/F122 型。

確度: 高

### B-9 co-commit gate を atomic deployment と呼び過ぎている

攻撃対象: `stage1-brief.md:16`、`stage2v3-plan.md:40-69`、`tools/dev_wave_land.py:1921-1933`

なぜ問題か (根拠): P1-D が保証するのは Git 履歴上の record/head 同一 commit だけです。plan 自身も main land 中の cross-file reader lock 不在を認めています。`env_contract.py:519-529` は record と head を別入力として読むため、checkout 更新中の deployment barrier と旧 process の lineage barrier は閉じません。

実害経路: fresh reader は split を拒否できますが、既存 cache process は旧版で続走します。「atomic deployment」と記録すると、未解決の配備窓を閉じたと誤認する。F73/F130 型。

確度: 高

### B-10 推奨案の根拠が実測と静的推論を区別していない

攻撃対象: `stage2v3-plan.md:54-61,205-209,221-229`

なぜ問題か (根拠): plan は race probe 未実走、PBS wrapper 未分類、差分見積り ±30% と明記しています。それにもかかわらず P1-D/P2-A の推奨は、混在頻度・回復費用・実際の手順漏れの測定値なしに提示されています。

実害経路: 未測定の運用リスクを根拠に、runtime 受理集合を変えない大型 hardening を選ぶ。現行成果物への直接影響はないため nit 寄りです。

確度: 中

## 総括

must-fix:

- B-1: durable 識別子と DW-G05 の訂正漏れ
- B-2: P3 の確定事項・再裁定事項の分離
- B-3: P1-D の D205/T-658 境界の明示
- B-4〜B-6: 手順の検査可能性、回復、consumer/domain の閉包
- B-7: R1〜R3 の依存関係と発火条件
- B-8〜B-9: runbook/byte 予算と atomicity の主張範囲

nit:

- B-10: 推奨根拠を「実測」ではなく静的推論として表示すること

pytest・実測は行っていません。