---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-08-27
wave: dev-wave-t1840-b4-launcher
seq: 1
title: B-4 の専用起動器を Claude 中断 wave から Codex resume し、独立監査の blocker を閉じた (コード + docs、中間 checkpoint、最終変異・受入は未実施)
---

## 本文

- 依頼は「D1033 に従い B-4 の専用起動器と識別子を支配点として置く。迂回できる経路が残らないことを
  負例で示す。性質だけを述べる検査は両層 stub で機構を通らない緑になるので実体を名指しする」。
- **依頼が挙げた 3 つの前提は、着手前に実測ですべて裏が取れた。**
  production factory の呼び手はテストと同 module 内の入口を除いて 0 件、
  `run_one_iteration` の AST 内に B-4 参照は 0 件、識別語の付与は 3 driver とも opt-in である。
- **親の brief にあった一般化が 1 つ誤っていた。** 「実走の入口は 3 driver の入口だけ」は誤りで、
  `loop.run_campaign` と `pipeline.evaluate` が公開 API として関門の下にあった。
  `CampaignConfig` は frozen だが `search_config` は可変の dict なので、通常の設定に識別語を
  後付けして直接 certified な成果物を作れた。**段 3 の 2 レンズが独立にこれを file:line で示した。**
  支配点の置き場所は {{D:b4-certified-sink-chokepoint}} で裁定した。
- **wave 中に着地した D1124 / D1125 が設計を 1 点変えた。** 段 3 が薦めた一度限りの起動記録は
  「不可逆承認の token を測定の前提条件として新設しない」と正面から衝突するため採らず、
  上書き可能にした ({{D:b4-launch-record-is-overwritable}})。
  段 4 直前の裁定 inbox 再走査で気づいた。
- **段 6 の敵対レビュー 2 本が、wave の目的が達成できていない欠陥を独立に見つけた。**
  最重要は「production の封印が、受理記録の実検証を一度も通さずに鋳造できる」ことで、
  レビューは架空の受理記録から certified な COMMIT に至る到達経路を関数名まで書き下ろした。
  差し替えも属性書換えも不要だった。他に、起動記録の driver 種別の照合が**自分自身を期待値に
  していて恒真**、campaign の束縛が「空でないこと」しか見ていない、certified sink の分類が
  lock を読めないとき素通りに倒れる、を見つけた。
- **段 4 で登録した変異のうち 3 件が恒真だった。** 副作用の不在で帰属させる設計にしたが、
  渡していた layout が cfg 由来でなかったため、関門を外しても別の既存関門が先に拒否し、
  観測対象がそもそも作られなかった。段 6 のレビュー 2 本と焦点再レビューが指摘し、作り直した。
  **焦点再レビューはさらに 6 件 (M11〜M16) の過剰決定も見つけ、こちらも入力を作り直した。**
- **実装子が既存テストの期待値を 1 件書き換えて壊した。** 親の投げ文には「既存テストを削除・
  skip・xfail 化・条件緩和しない」は書いたが、**「期待値を変更しない」は書いていなかった**。
  `DW-S06-B` は同文言を fix の投げ文にだけ要求しており、段 5 の実装子の契約には無い。
  焦点走の赤で検出し、元へ戻させた。段 8 の候補として扱う。
- **封印への closure 内省による到達は閉じられないと裁定した** ({{D:b4-introspection-is-a-non-guarantee}})。
  Python では `__closure__` を塞げない。内省を要しない素直な経路だけを塞ぎ、残りは非保証として
  明記させた。**閉じたと書かせていない。**
- **識別語の鋳造口が試験用の封印も受理する点は、直させずに受理した**
  ({{D:b4-marker-mint-accepts-test-seal}})。標本を生む境界がすべて production を要求するため
  標本の受理集合が変わらず、閉じる費用が検査全体に及ぶためである。
  事前登録の文言をそれに合わせて改めた。
- **子は pytest を 1 度も実走できなかった。** sandbox から計算ノードの queue へ届かないためで、
  段 5 と 3 回の fix すべてで同じである。子の報告はいずれも「実装済み・未実走」と正しく申告した。
  **実測はすべて親が計算ノードで行った。**
- **`orchestrator/campaign/wal.py` を触ると、commit するまで焦点走が 1 件も測れない。**
  同 file は disk bytes と HEAD blob の一致を全テストが要求する契約 file であり、
  未 commit のままの初回走は 110 件の赤で戻った。実装差分の赤ではない。
  そのため実装と各 fix のたびに統合 commit を先に作った。
- **段 6 の fix は 3 巡回した。** 1 巡目が must-fix 7 件、2 巡目が焦点走の赤 8 件の 3 原因、
  3 巡目が焦点再レビューの must-fix 3 件である。`DW-O16` の上限どおり 3 巡で閉じた。
- 起動時の編集面重複検査で、対象 11 file に触れている branch も稼働 worktree の未 commit も
  0 件であることを確認した。**着手時点の話である** — 受入の直前には local main が 179 commit 進み、
  そのうち複数が本 wave の編集面 (3 driver、base の test file、campaign lock、conftest) に
  触れていた。**起動時の重複ゼロは、13 時間後の取り込み時点の重複ゼロを意味しない。**
- **最初の受入は rc=70 (merge-history-provenance) で戻ったが、本 wave の回帰ではなかった。**
  main に既知違反の登録 data file が 1 件増えており、取り込み前の checker で取り込み後の範囲を
  監査したため「実行不能」になっていた。main を取り込んだ後は全史監査が rc=0 で通った。
- **取り込みは競合ゼロで自動 merge できたが、合成は壊れていた。** merge 後の焦点走で 15 件が赤に
  なり、すべて main 側が並行して追加した B-4 bootstrap の検査だった。原因は 1 つで、
  関門が入る前に書かれたそれらが識別語付きの設定を封印なしで作っていることである。
  **関門は正しく発火していた。** 直したのは検査側で、封印済みの試験用 context を渡す形へ移行させた。
  関門は 1 つも緩めていない。production code にも触れていない。
  merge commit の combined diff は実装面の path を返さないため、Codex `role=author` 行は要らない。
  親は当初「両親と異なるか」で判定しようとしたが、これは述語の取り違えだった。
- **main が新設した B-4 の配線 probe は、本 wave の関門を迂回していない。** 同 probe は識別語を
  付けない通常の設定しか作らず、関門の対象外である。probe は 1 byte も変えていない。
- **変異は取り込み後の tip で回し直した。** anchor 18 件は byte 一致、期待 node 22 件も全部
  存在したが、**期待 node の完全集合が変わりうる**ため実測した。実際に全件 MISMATCH になり、
  原因は {{F:clean-tree-assert-poisons-mutation}} だった。除外して再走し完全一致を得た。
- **層予算は取り込みで 2 度きつくなった。** main が予算値と同層の内容を両方変えたためで、
  そのつど既存記述の削減で収めた。段 8 で足した義務の文は 1 文字も削っていない。
- **段 3 の敵対相談 1 本が内容フィルタに当たって成果物ゼロで終わった。** 受領証の失敗分類は
  `f45_missing_output`、rollout の終端エラーは `cyber_policy` である。投げ文が
  「支配点を通さずに標本を作る具体的な呼び方を関数名と引数の形まで書け」となっており、
  防御機構の回避手順の依頼に読めたためである。**到達可能性の分析の語彙へ書き直して投げ直し、
  成立した。** F644 の同型再発として追記した。既存の恒久対応のうち「攻撃→点検」は満たして
  いたが、**実行できる形の呼び方を要求する部分**が残っていたのが発火点である。

- **段 8 の裁定。** 改善候補は 2 件だった。(1) 段 5 実装子の契約に
  「既存テストの期待値を変更しない」が無い点は、`DW-S05-B` へ 1 文を足して閉じた。
  L1.5 の byte 予算に空きが 8 bytes しか無かったため、D782 が委任する D730 の手順に従い、
  **まず既存記述の削減を試した** — 同節の冒頭が入口の凍結境界を全文複製していたので
  ポインタへ縮約し、その差分で新しい 1 文を収めた。安全義務は削っていない
  (縮約した内容は入口が常時読む層で保持している)。上限の引き上げは行っていない。
  (2) 内容フィルタの再発は F644 への追記で閉じた。

**2026-08-28 Codex resume。** 元 worktree は local main 9 commit 遅れ・dirty 4 file のため resume gate が
拒否した。元 worktree は 1 byte も変更せず、`ff10013b1` から専用 Codex resume worktree を作り、dirty
4 file は監査後に SHA-256 一致で複製した。main 未到達 10 commit の実装面 5 commit はすべて Codex
`role=author` を持ち、全史 provenance も新規違反なしだった。

- **read-only Codex focus が「迂回できない」を覆した。** G4 は分類と receipt 検証で lock を二度読みし、
  campaign id は decoded lock でなく directory basename 由来だった。M08〜M10 も副作用 oracle より先に
  inner G2 の message 差で落ちていた。manager は blocker / must-fix と裁定し、D95 Codex author へ戻した。
- fix は同じ lock bytes snapshot、decoded canonical campaign id、明示 lock-absent digest を issuer / sink
  双方へ束縛した。markerless lock + valid receipt と最初から lockless + explicit absence binding の正例は
  維持した。一方、**lock に束縛した receipt の発行後に物理 lock を消す旧 fallback は受理集合から除いた。**
  これは absence-to-marked bypass と同じ穴を開くため、D1033 / 規律2 と両立しない。
- author の 2 巡目報告は WAL の sentinel 変更を記したが working bytes に残っていなかった。親の報告・実体
  照合で発見し、3 巡目を WAL 1 file に限って修正した。親実機赤では sidecar check が拒否順序を先取りする
  取り残しも見つけ、別の D95 author red-fix で閉じた。焦点集合は最終的に **540 passed**。
- 旧 dirty の `ff10013b1` 変異は 18/18 KILLED だが、resume focus が M08〜M10 の単一理由性を refute したため
  最終証拠には使わない。resume 初回 21 変異は baseline 607 passed、17 KILLED / 4 MISMATCH。M12 は診断
  message の過剰固定、M19〜M21 は enforcement closure file の working bytes 変異が contract-loader drift を
  一様に発火させた runner 汚染である。期待 node へ足さず erratum として台帳を保存した。
- 最新 main は resume 中に進行し、T-1840 編集面と全面重複した。launcher の削除 commit は無く、T-1840 は
  worklog で持ち越し、D1223 / D1224 も後続境界と実装子期待値義務を追認している。最終変異前に current
  main を branch へ取り込み、合成を再監査する。
- **scope 外は不変:** D1042 / D1043 / D1050 と正式 B-4 実走は実装・実走せず、記録だけを返す。

## 次の一手差分

### 継続中

- [T-1840] D1033 に従い専用起動器と B-4 識別子を支配点として置いた。識別語の鋳造は封印を要求し、
  certified sink の合流点で起動記録と生きた context の一致を要求する。
  Codex resume の blocker fix と焦点 540 passed まで完了した。初回変異の MISMATCH は erratum として保存した。
  remaining: current main 取り込み、broad 18 + supplemental 3 の最終変異、受入全走、land
  base: 3814fde85f6722932d4c17a922e16179278fb0d66f8098d360bb014d74d95145

### 新規

- {{T:b4-certified-sink-general-capability}} **P2・新規**: 非 B-4 を含む certified な成果物一般へ
  起動由来の権能を要求するかを裁定する。本 wave は識別語を持つ campaign だけを対象にし、
  それ以外の受理集合を 1 bit も変えていない。全 campaign へ広げると受理集合が変わるため
  scope 外とした。D1050 (受理記録の置き場所の一本化) と接する。

- {{T:b4-post-commit-lock-relabel}} **P2・新規**: COMMIT の後に campaign lock を書き換えて
  B-4 と名乗り直す経路が開いている。sink の関門は COMMIT の時点で識別語があった経路だけを閉じる。
  閉じるには、関門が検証した起動 context の digest を COMMIT 側の成果物へ残し、
  成果物の受理と B-4 の consumer で再検証する必要がある。
  **D1033 が却下した「下流での名乗り拒否」と形が近いため、設計に入る前に裁定を要する。**
