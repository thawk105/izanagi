## 親の決定的事実の検証

Layer3 の accepted-report 経路については、親の核心は正しい。

- production で `certifying_input=True` を作るのは [layer3_report.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2139-b4-certified-connection/orchestrator/campaign/layer3_report.py:768) だけ。
- その前に `verified.certifying is True` が必須。
- production の `VerifiedAcceptanceReceipt` は [s8c_acceptance_receipt.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2139-b4-certified-connection/orchestrator/campaign/s8c_acceptance_receipt.py:420) で `certifying=False` に構造固定される。
- `report.complete` は 0 件で、B-4 material report を読む production consumer も 0 件だった。

ただし、二点訂正が要る。

第一に、テストの数え方は不正確である。親が挙げた六箇所は verifier を差し替えて後段へ進むテストだが、すべてが最終的に accepted report を成功生成するテストではない。また現 tree には [test_layer3_report.py:3219](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2139-b4-certified-connection/orchestrator/tests/test_layer3_report.py:3219) にも同じ差し替えがある。とはいえ、実 receipt のまま receipt gate を越えるテストがない、という結論は変わらない。

第二に、「certified 側の受け口はすべて構造的に発火しない」は広すぎる。D1236 は B-4 の certified sink を WAL の COMMIT 合流点に置いており、[wal.py:636](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2139-b4-certified-connection/orchestrator/campaign/wal.py:636) から [p3_b4_launcher.py:456](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2139-b4-certified-connection/orchestrator/campaign/p3_b4_launcher.py:456) の実関門が発火する。これは material report 生成より前の sink なので、今回の「report → certified selection」には使えないが、親の全称命題への反例ではある。

正確な決定的事実は、次である。

> Layer3 の正方向は構造的に閉じており、別に存在する B-4 WAL sink は material report の consumer ではない。さらに、現 checkout には post-report の sanctioned selection callsite と実 report artifact がない。

したがって、「正方向を開くには certifying authority が必要」は正しいが、「現行 report を拒否する接続にも certifying 化が必要」は誤りである。拒否接続は規律 2 を緩めず作れる。ただし今は接続先と発火実体がない。

## 案 1 への検査

案 1 の「今は実装しない」は妥当だが、「現プランを再利用可能な設計として上流待ちにする」は危うい。

- certified 選択、材料レポート、台帳上の decision reference は変わらない。変わるのは設計記録だけである。
- floor 発効と approval authority 解消だけでは再開条件が足りない。実 `report.complete`、post-report callsite、sink owner、durable decision の参照先も必要である。
- 現プランは v1 の evidence-only wire、floor 不在、`Literal[False]`、現在の exact field 群を前提とする。T-2140 後には、その前提こそが変わるため、public API・schema・reason taxonomy の多くは陳腐化する。
- 再利用できるのは、fail-closed、caller-authored report を権威にしない、subject/issuer/path を束縛する、sink の必須入力にする、durable reference と E2E 変異を持つ、という設計条件である。350 行規模の具体案ではない。
- task owner と再開トリガーを台帳に固定しない「上流待ち」は、実質無期限になる可能性が高い。

したがって案 1 は、そのままでは推奨しない。

## 案 2 への検査

validator 単体が変えるのは、その新 API 自身の入力受理集合だけである。破損した三ファイルを例外へ写す価値はあるが、certified 選択、material report、既存台帳の値・参照は変わらない。

将来再利用できるのは strict reader、commit-marker hash 検証などの一部である。しかし、実接続にはさらに subject/issuer、campaign identity、D1378 の配置、authority、durable decision、sink の必須入力が必要になる。floor 発効に伴い wire が変われば、exact v1 validator は作り直しに近くなる。

また、tmp の CLI test ID は実 artifact path や measurement ID ではないため、案 2 は `DW-G04` を満たさない。呼出元のない public API を先置きする根拠にはならず、案 2 は不採用とする。

## 案 3 への検査

実在する post-report selection callsite があれば、現行 report を必ず拒否する decision を sink の必須入力にすること自体は、規律 2を緩めず完成できる。正方向を実装する必要はない。

しかし現状は、その callsite、実 material report、durable decision の参照先がすべてない。新しい sink を発火証明のためだけに作れば、仮想経路向けの gate 追加になる。また指定された別 wave 所有 file は編集できない。

したがって現在の案 3 は完成不能である。意味のある部分切出しは、実 callsite が着地した wave で validator・required input・durable reference を同時実装することだけであり、本 wave に先置きできる production slice はない。

## 案 4 の提案 (あれば)

案 4として、**T-2139 を曖昧な「上流待ち」ではなく、再開条件付きの見送りとして終端する**ことを提案する。

- production/test code は追加しない。
- T-2139 の既存台帳項目を、5 語目は未実装のままであること、再開条件が次の論理積であることへ更新する。

  - stable な実 `report.complete` path または measurement ID
  - sanctioned な post-report selection callsite と owner
  - durable decision の保存先と sink からの参照
  - 正方向を含める場合のみ、T-2140 と発行可能な approval authority
  - 対象 file の別 wave 所有解除

- 現プランは「将来そのまま実装する設計」ではなく、却下済み案と threat-model checklist として保存する。再開時は当時の wire から再計画する。
- material report wire は変更しない。既に [p3_b4_material_report.py:728](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2139-b4-certified-connection/orchestrator/campaign/p3_b4_material_report.py:728) が `certifying=False` と `certified_selection_connection` 非保証を機械可読に記録している。別の closure field や独自台帳を足すのは重複である。

これは runtime の受理集合を変えないが、台帳の状態・参照・再開契約を変え、「接続済み」という誤記と無期限 carry を防ぐ。

## 推奨と根拠

**案 4を推奨する。**

実装しないという結果は案 1 と同じだが、案 1が暗黙に期待する「上流解消後に現プランを再利用できる」という前提を採らない。現プランは現在の閉鎖状態を詳細に実装する validator 設計であり、上流解消後の接続設計ではないためである。

また、親の Layer3 閉鎖の実測は正しいものの、全 certified sink への一般化は誤っている。この誤りは今すぐ実装する理由にはならず、再開時に callsite を改めて特定すべき理由になる。

## 推奨を採ったとき本 wave が残すもの

- production/test 差分: 0
- 事前登録・別 wave 所有 file・material-report wireの変更: 0
- Layer3 receipt 経路の構造的閉鎖、WAL sink との区別、実 report/callsite 不在の実測記録
- 却下済み設計メモと、将来使える threat-model checklist
- 「5 語目は未実装」と明記した decision/worklog
- T-2139 の具体的な再開条件と依存先

pytest は実走しておらず、以上は静的読解に基づく。

## 総括

親の「本 wave では実装しない」は支持する。ただし根拠は「certified side が全面的に発火不能」ではなく、**post-report の実 callsite・artifact・durable reference が存在しない**ことである。

案 2 は孤立 API、案 3 は現時点では仮想 sink になる。ゆえに、現プランを上流待ちの実装候補として抱え続ける案 1ではなく、再開条件を固定して現 wave を終端する案 4が最も正確である。