## 攻撃した箇所

- **D1060 を「その wave 限定」とする読み** — 半分成立。`本 wave で 1 セルも埋めない` は時点限定だが、「以後は自由に埋めてよい」は導けない。各欄の解除条件充足が必要。
- **model snapshot の拘束力** — 半分成立。事前宣言値との実行時照合には実効的な拒否力がある。ただし、値の選定権限と宣言源は未定義。
- **§5 セルの記入権限** — 攻撃成立。段 2 が置いた「人間の実行責任者が承認」という権限主体は、射影資料から導けない。
- **閉包 hash の更新順序** — 攻撃不成立。段 2 は最終 tree で再計算し、閉包変更時に手順を戻すことを明記している。
- **gate の scope** — 一部成立。production の選択 driver は閉じるが、3 driver 全件の鮮度は任意実行の test にしか置かれていない。
- **凍結物の再発行不要という結論** — 現時点については概ね成立。ただし、本 wave で draft record を発行した瞬間から、後続の文書編集ごとに再発行が必要になる。

## 所見

### 1. D1060 は永久凍結ではないが、条件未充足を無視する許可でもない

- **根拠となる逐語または file:line**  
  D1060:3-5 は「本 wave で 1 セルも埋めない」「全 10 欄が §5.1 の解除条件を満たさない」とする。現文書では n が記入済みで、実行責任者も部分記入済みである。[事前登録文書:160](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2005-b4-projection-registration/docs/phase3-b4-reflux-ablation-preregistration.md:160)、[同:167](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2005-b4-projection-registration/docs/phase3-b4-reflux-ablation-preregistration.md:167)

- **なぜ問題か**  
  後続 wave で解除条件を満たした欄まで永久に禁止する読みは誤りである。一方、D1060 の理由は wave 名ではなく解除条件の未充足なので、親 brief の「以後 n 欄が埋まった」から対象セルも記入可能とは推論できない。

- **成果物の値・受理集合がどう変わるか**  
  対象セルは、独立した解除条件が満たされるまで `未記入` のままとなる。projection grammar と照合機構だけは実装できるが、それだけでは T-2005 の「§5 と record への登録」は完了しない。

### 2. model snapshot は機械的には拘束するが、宣言源が空いている

- **根拠となる逐語または file:line**  
  D998:20-22 は model を「期待値の宣言」とし、controller が実測と照合すると定める。実装も provider 応答後に exact model を照合する。[p3_b4_closed_critic.py:928](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2005-b4-projection-registration/orchestrator/campaign/p3_b4_closed_critic.py:928)、[同:932](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2005-b4-projection-registration/orchestrator/campaign/p3_b4_closed_critic.py:932)  
  一方、verifier 自身が、mismatch 後に値を書き換えて新 invocation を開始する行為を機械的には防げないと明記する。[p3_b4_admission_record.py:11](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2005-b4-projection-registration/orchestrator/campaign/p3_b4_admission_record.py:11)

- **なぜ問題か**  
  「宣言と照合なので拘束力がある」という親の主張は、受理される receipt の集合については成立する。しかし、誰が何を根拠に exact slug を選ぶか、mismatch 後の再宣言をどの実験境界で許すかは閉じない。AI が fixture、alias、試し打ちの結果から値を選べば、D1060 がいう空洞化に近づく。

- **成果物の値・受理集合がどう変わるか**  
  人間が事前に承認した外部実行契約など、結果非依存の宣言源があれば、その exact slug と一致する invocation だけを受理できる。宣言源が無ければ model 値は書けず、§0 の原子性により同じセルの prompt と projection も登録できない。

### 3. 段 2 は存在しない権限主体を補っている

- **根拠となる逐語または file:line**  
  対象 driver 欄は「記入者とレビュー者」を人間の指名を含む別 commit で先行 freeze する。[事前登録文書:171](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2005-b4-projection-registration/docs/phase3-b4-reflux-ablation-preregistration.md:171)、[同:185](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2005-b4-projection-registration/docs/phase3-b4-reflux-ablation-preregistration.md:185)  
  対象セルには「両アームで同一であることを確認して記入する」しかない。[同:218](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2005-b4-projection-registration/docs/phase3-b4-reflux-ablation-preregistration.md:218)  
  段 2:44 は「人間の実行責任者が承認」を新たに要求するが、その主体は既存規範にない。

- **なぜ問題か**  
  同一性確認は値の選択権限を与えない。特に model は repo bytes から一意に決まらず、選択自体が実験条件である。この非対称を「意図的」と認定できる逐語もない。D1060 が env_tag などで採ったのと同様、まず §5.1 に宣言源、承認者、時点、mismatch 後の扱いを足すべきである。

- **成果物の値・受理集合がどう変わるか**  
  規範追加前は対象セルを埋めない。追加後は、承認された exact model、最終 tree 由来の prompt、driver 別 projection の完全な組だけが受理候補になる。

### 4. §0 の原子性により projection だけを先行登録できない

- **根拠となる逐語または file:line**  
  部分記入例外は「実行責任者・開始時刻」だけで、他 9 欄へ広げない。[事前登録文書:37](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2005-b4-projection-registration/docs/phase3-b4-reflux-ablation-preregistration.md:37)  
  現行 verifier も対象セルを model、prompt、projection の完全な組として読む。[p3_b4_admission_record.py:75](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2005-b4-projection-registration/orchestrator/campaign/p3_b4_admission_record.py:75)

- **なぜ問題か**  
  projection は repo bytes から確定できても、model が未確定なら同じセル全体が未解除である。T-2005 の目的だけを理由に projection を先に書くと、明示された部分記入禁止を破る。

- **成果物の値・受理集合がどう変わるか**  
  model の正当な宣言が得られない分岐では、段 2 がいう grammar、driver binding、鮮度検査までを準備し、値セルと record 発行を見送る。T-2005 は未完了として裁定へ戻る。

### 5. 更新順序は書かれているが、「登録済み」は継続的不変条件である

- **根拠となる逐語または file:line**  
  閉包には編集対象 2 module 自身が入る。[p3_b4_closed_critic.py:624](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2005-b4-projection-registration/orchestrator/campaign/p3_b4_closed_critic.py:624)、[同:637](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2005-b4-projection-registration/orchestrator/campaign/p3_b4_closed_critic.py:637)  
  段 2:67-77 は閉包コード確定、3 hash 再計算、文書 commit、record 発行の順と、1 byte 変更時の巻戻しを明記する。

- **なぜ問題か**  
  段 2 の手順自体は正しい。ただし段 6 の fix が閉包 member を触れば、既存の文書値と 3 record は成果物ではなく stale artifact になる。「一度登録したから完了」という完了条件は成立しない。

- **成果物の値・受理集合がどう変わるか**  
  最終 review と fix の後に再計算し、その後は閉包 member、文書、record の変更禁止または再発行を完了検査に含める必要がある。最終 tree と一致しない旧 hash は文書と record が互いに一致しても拒否される。

### 6. 3 driver 全件の鮮度検査が必須経路に入っていない

- **根拠となる逐語または file:line**  
  runtime は選択 driver の closure だけを照合する。[p3_b4_closed_critic.py:1157](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2005-b4-projection-registration/orchestrator/campaign/p3_b4_closed_critic.py:1157)  
  段 2:63、230、253 は、未選択 2 driver の鮮度を repository test が担当するとするが、その test が必須 checker に接続される計画はない。

- **なぜ問題か**  
  test を任意に走らせるだけでは、文書に登録した 3 値すべての継続的な gate とはいえない。base 実走は base の stale を拒否しても、同じ文書の sort と trigger が stale のまま merge される可能性が残る。

- **成果物の値・受理集合がどう変わるか**  
  必須 checker へ接続しない場合、機械的受理集合は「選択 driver だけ最新」であり、「登録 3 driver が全件最新」ではない。必須化が本 wave の scope 外なら、checker の所有層と導入 wave を裁定パッケージへ返すべきである。

### 7. draft record は直ちに使えず、後続 §5 編集で必ず失効する

- **根拠となる逐語または file:line**  
  verifier は §5 全欄の sentinel を拒否する。[p3_b4_admission_record.py:600](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2005-b4-projection-registration/orchestrator/campaign/p3_b4_admission_record.py:600)、[同:707](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2005-b4-projection-registration/orchestrator/campaign/p3_b4_admission_record.py:707)  
  また HEAD の文書 bytes が record の宣言対象と異なれば拒否する。[同:690](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2005-b4-projection-registration/orchestrator/campaign/p3_b4_admission_record.py:690)、[同:702](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2005-b4-projection-registration/orchestrator/campaign/p3_b4_admission_record.py:702)

- **なぜ問題か**  
  段 2 が提案する draft 文書向け 3 record は現時点では verifier を通らず、残りの §5 欄が埋まるたびに文書 binding が失効する。これを「admission record 登録完了」と呼ぶと、実走可能な record と誤認される。

- **成果物の値・受理集合がどう変わるか**  
  draft record を作っても production の受理集合は増えない。作るなら「非 admissible な登録候補」と明記し、最終発効版での全件再発行を必須とする。無効 record を残さない方針なら、発効版まで発行を待つ。

### 8. 既存凍結物の再発行不要という限定結論は反証できない

- **根拠となる逐語または file:line**  
  §5.1.1 の raw pin は独立した定数である。[p3_b4_analysis_prereg_consumer.py:47](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2005-b4-projection-registration/orchestrator/campaign/p3_b4_analysis_prereg_consumer.py:47)  
  consumer は見出し `5.1.1` から次の同格以上の見出しまでを切り出す。[同:301](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2005-b4-projection-registration/orchestrator/campaign/p3_b4_analysis_prereg_consumer.py:301)  
  文書は発効前 draft と明記する。[事前登録文書:34](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2005-b4-projection-registration/docs/phase3-b4-reflux-ablation-preregistration.md:34)

- **なぜ問題か**  
  §5 表と §5.1 の対象行だけの編集が §5.1.1 raw bytes を変えないという根拠には穴を構成できなかった。commit 済み admission record が無いという親の実測が正しければ、今回の最初の発行前に再発行対象はない。

- **成果物の値・受理集合がどう変わるか**  
  既存 §5.1.1 pin は維持できる。ただし新しい record 発行後は所見 7 の再発行義務が始まるため、「再発行不要」は発行前の一時点に限定して記述すべきである。

## 裁定へ返すべき択一

1. `expected_claude_model_snapshot` の exact 値を誰が、どの結果非依存資料に基づいて承認するか。  
   推奨は、人間の承認者、外部実行契約、承認時点、mismatch 後の扱いを §5.1 に先行追加すること。

2. 規範追加後に本 wave で対象セルを埋めるか、model 宣言源が提供されるまで `未記入` のまま T-2005 を未完了とするか。  
   現資料だけなら後者。

3. draft 文書に束縛した非 admissible record を T-2005 の成果物として残すか、§5 全欄が揃う発効 commit まで発行を待つか。  
   推奨は後者。前者を採るなら「後続編集で必ず再発行」と明示する。

4. 3 driver 全件の freshness tripwire を必須 checker に接続するか。接続先が本 wave の scope 外なら、所有層と後続 task を裁定で固定する。

## 反証できなかった懸念

- D1060 が将来の全 wave に対して §5 全セルを永久に禁止した、という読みは構成できなかった。
- 宣言済み model snapshot が実行時照合によって受理集合を狭めない、という攻撃は成立しなかった。
- 段 2 が閉包 hash の最終 tree 再計算順序を落としている、という攻撃は成立しなかった。
- §5 表の編集だけで §5.1.1 raw pin が変わる、という攻撃は成立しなかった。
- 現時点ですでに再発行必須の commit 済み admission record がある、という反証材料は射影資料内に無かった。

## 総括

D1060 は永久禁止ではないが、対象セルを今埋める権限も与えていない。  
model の実行時照合には拘束力がある一方、値の宣言源と承認主体が欠けている。  
先に §5.1 の規範を足し、人間裁定が無ければセルと record は未発行にすべきである。  
hash 更新順序は妥当だが、3 driver 全件検査の必須化と draft record の扱いは裁定が要る。  
pytest は実行しておらず、本所見は指定資料による静的検査だけに基づく。