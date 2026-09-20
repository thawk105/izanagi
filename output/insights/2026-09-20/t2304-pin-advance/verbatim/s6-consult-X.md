## 成立した攻撃

1. **重大度：高 — 「⑤＋旧 binary 再 admission＋③」は、新 main での再開条件として不足する。**

   policy が campaign identity に入るため、binary の再 admission と旧 lock の継続は別問題である。`ident.py:139–142` は旧 lock の policy preimage を拒否する。**② 登録・identity の扱いが注記から欠けている。**

   また、新 pin の successor protocol に旧 binary を接続するなら、policy 以外に source pin の一致も必要になる。`s8b_binary_admission.py:434–435` は外部期待 pin と receipt の source commit の不一致を拒否する。再 admission は旧 source を新 source に変換しない。

   したがって、帰結は「旧系列の再開」と「新系列への移行」に分ける必要がある。前者は旧 superproject・対応 submodule・旧契約の組で行い、後者は②③⑤と source／admission の整合を系列ごとに扱う。「旧 binary を再 admission すれば移行可能」とはまだ言えない。

   根拠：[ident.py:139](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2304-pin-advance/orchestrator/campaign/ident.py:139)、[s8b_binary_admission.py:434](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2304-pin-advance/orchestrator/campaign/s8b_binary_admission.py:434)、材料逐語 `t2756-s4.1.md:6`。

2. **重大度：高 — epoch golden の追随だけでは、既に観測された受入の赤を解消できない。**

   `test_s8b_floor_campaign.py:15749–15759` は実 repo の HEAD を clone する。versioned 正例では gitlink を旧 protocol に合わせず、`:15783` で resolver を呼ぶ。そのため、新 gitlink・旧 protocol 2 件の組では証明したい certificate 検査に届かない。正例だけでなく、byte drift 負例の単一理由性も失われている。

   **具体的に止まるのは本 wave の受入全走であり、未修復の差分を取り込めば他 wave の同テストも止まる。** T-2724 を先に land させても、この原因は解消しない。

   ただし O2 は「tested tip まで完成」が前提なので、これは O2 全体への決定打ではない。既存テストの旧 protocol 正例を正しい fixture 条件で成立させ、負例の検査到達性を保つ修復は⑦として検討できる。新 main の resolver が成功するように見せるための assert 削除・一括 xfail は不可。

   根拠：[test_s8b_floor_campaign.py:15749](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2304-pin-advance/orchestrator/tests/test_s8b_floor_campaign.py:15749)、同 `:15921,15935,15957`、焦点集計 `set1-classified.txt:35–42`。修復後の緑は本相談では未確認。

3. **重大度：高〔承認根拠〕— D2150 の説明訂正だけで、新事実の採否判断まで済ませてはならない。**

   最強の O3 論拠は、承認された推奨の理由に「主経路は影響を受けない」が明記され、その事実認識が誤っていたことである。`DW-S04:101–102` は未見事実による承認前提の崩れをユーザー再裁定へ戻すと定め、`DW-STOP:39` も正式停止理由に挙げる。これは仮想リスクではなく、live 受理集合の変化である。

   「②③⑤は新系列着手時」という反論への再反論は、**今回分かったのは、新系列の準備だけでなく、旧 full OID 系列を新コードで継続する際にも policy が変わること**である。既知の③だけに還元できない。

   ただし、ユーザーの「相談して親が決める」という恒久指示が本件にも適用される以上、**ユーザー再裁定待ちで停止する義務までは成立しない**。必要なのは、親が新事実を real と認めた上で、承認範囲を維持して続行する理由を明示すること。「D2150 がこの波及も承認済みだった」と遡及して記録してはならない。

   根拠：[D2150:67627](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2304-pin-advance/docs/decisions.md:67627)、同 `:67637`、[DW-S04:101](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2304-pin-advance/docs/dev-wave/core.md:101)。

4. **重大度：中 — T-2724 待ちは、policy 問題の解決にも統合後の受入保証にもならない。**

   T-2724 は token 付き実 repo 6 node の真値更新と P1〜P4 を残している。pin 前進後には、g1 launch 検証で旧 policy が拒否され、既知の lineage 拒否より先に別理由が現れ得る。T-2724 単独の緑から、合成後の緑は導けない。

   待つなら意味は「T-2724 が旧環境で成果を確定できる」「A/X を含む pin 前進前 commit が残る」である。**取り込んだ後の tested tip を作るところまでが O2**であり、待機そのものを安全性の根拠にしてはいけない。

   根拠：T-2724 `HANDOFF.md:20,26–27`、[s8b_ratified_freeze.py:3261](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2304-pin-advance/orchestrator/campaign/s8b_ratified_freeze.py:3261)。

## 成立しなかった攻撃

- **稼働中 K2・A-1 sized attempt の即時停止：不成立。** 固定 submit-tree が新 main を読まないという提示事実を覆す経路は確認できない。K2 round 4／A-1 再走を新 main から作れば拒否や identity 変更が起こるが、その投入予定・再作成元を名指しする資料はない。

- **B-4 の窓 job・finalize が必ず止まる：不成立。** `submit_floor_pair.sh:120–136,186` は detached checkout の HEAD を束縛し、`floor_pair_campaign.sh:224–225` が投入時 HEAD を照合する。s8b の現行 policy 拒否を、そのまま別 driver の床値 pair job に転用できない。新 main から submit-tree を再作成する具体的予定も確認できない。

- **W-4 が今日止まる：不成立。** 提示事実と T-2724 handoff により、full launch validation は既存 lineage 矛盾で未達。pin 前進が将来の追加障害になることと、今日動けた作業を止めることは異なる。

- **mocc 隔離実証 T-2772/T-2773 の停止：不成立。** D2150 自身が旧 pin のまま可能と明記する。今回の変更を読む必須経路は確認できない。

- **rulings／next-tasks 自動走の直接停止：未立証。** admission／floor resolver を必須とする接続根拠がない。submodule 未同期による作業入口の停止は別問題。

- **check_docs・provenance・land が新 pin で恒久的に壊れる：不成立。** literal 追随と D16 同期は既知の修復事項。`dev_wave_land.py:5464` の postcondition failure と `:6155–6172` の同期後再試行経路は存在する。本相談では各検査を実行していない。

- **規律 2／7 が pin 前進自体を禁じる：不成立。** 現行 gate の拒否を保持し、旧測定を取消し・改竄しない O2 は両規律と両立する。規律 7 は旧証拠を新契約で live 消費できる保証ではない。検査を緩めたり旧 receipt を張り替えたりするなら、そこで違反が成立する。

## O1 / O2 / O3 の比較表

| 選択 | 止まる作業・影響 | 復旧手順 | 規律との関係 |
|---|---|---|---|
| **O1：T-2724 を待たず land** | 新 main の旧系列 live 消費が拒否。T-2724 が取り込む場合、その受入・拒否理由の再確認が同 wave に移る。稼働中 attempt の停止は未立証 | 自 wave の受入修復、submodule 同期。旧系列は旧 commit、新系列は契約整合 | 受入完了後なら直ちに禁止とは言えない。他 wave の受入を自 wave の検証の代用にはできない |
| **O2：完成し、T-2724 を取り込んで land** | T-2724 の先行完了を待つ。land 後の policy／resolver 障害は残る | 合成した tip で受入。旧 pin＋A/X の commit を歴史再開の起点として保持。新系列は②③⑤等を整理 | 恒久指示と明示 scope に最も合わせやすい。新事実の親判断と帰結の訂正が必要 |
| **O3：停止・再裁定** | pin 前進が止まり、新 pin を必要とする後続系列が遅れる。既存 main の動作は維持 | 新事実について判断を確定後、同じ wave を再開 | DW-S04／STOP の文面上は最強。ただし本件の恒久指示を超えてユーザー待ちにする根拠は不足 |

O1 の最強の利点は、待ち時間をなくし、T-2724 自身が新 main を取り込んだ状態で受入できることである。ただし「後続が気づける」は欠陥を残す理由にはならない。また O2 は、**A/X を含む旧 pin の commit を先に確定できる**点で、単なる衝突回避以上の意味がある。順序は land 機構が自動保証するものではなく、親が取り込み後の ancestry と tested tip で満たす条件である。

## 推奨

**O2 の方針は通す。ただし、帰結と完了条件を訂正した O2 にする。O3 のユーザー待ちは推奨しない。**

必要な修正は次の範囲で足りる。

1. epoch golden 以外の実 repo 由来の赤も⑦として処理し、T-2724 を含む tip で既存受入を完了する。⑤を受入のために先行発行する結論には飛ばない。
2. 帰結を「旧系列は pin 前進前の superproject と対応 submodule・旧契約で継続」「新 main への移行は②③⑤と source／admission の整合が必要」と書く。旧 binary の再利用可否は系列別で、再 admission だけの復旧を約束しない。
3. T-2724 待ちを policy 問題の解決と説明しない。旧 pin＋A/X の保存点を確定し、合成後を受け入れるための順序とする。

記録の最小配置は、**insight に波及と親判断、既存 worklog 本文に結果と参照、runbook の既存 P1 行に歴史再開／新系列移行の注意**である。新しい gate、チェックリスト、専用台帳は不要。

決定台帳への事実追記は、既存 D2150 の明白な誤説明を訂正する目的なら過剰ではない。ただし「原承認の変更なし／当時未認識だった policy 波及／今回の続行は親判断」を区別し、既存 spool 経路で短く記録する。D2150 の逐語を置換しない。根拠は `core.md:107–110` と D2150 冒頭の「付随する gate・台帳・汎用化を足さない」である。

## 総括

最強の攻撃は、**復旧説明から② identity が抜け、旧 binary の source 束縛も未解決なこと、そして epoch golden 以外にも受入の実測赤があること**である。

一方、稼働中測定や今日の W-4 を止める証拠はなく、恒久指示を押しのけて O3 のユーザー待ちを要求するところまでは成立しない。**帰結を訂正し、T-2724 を含む受入済み tip を作る O2 を推奨する。**