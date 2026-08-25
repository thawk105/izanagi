---
schema: izanagi-spool-v1
ledger: decisions
authored: 2026-08-26
wave: dev-wave-t1176-t1230-role-diagnosability
seq: 1
---

## {{D:role-invalid-failure-phase}}. invalid role event に失敗分類と生応答 pointer を必須化する

**決定:** 8c 自律 trial の invalid role event について、`error_artifacts` の受理集合を狭める。
D96 の手続 (新しい設計判断の記録 + 境界テストの同時更新) に従う。

1. `failure_phase` を必須にし、値を閉じた 6 値
   (`pre-raw-write`, `raw-write`, `json-syntax`, `json-shape`, `role-schema`, `parser-error`)
   に限る。producer 側と consumer 側の列挙が一致することを meta-test で固定する。
2. `failure_phase` が raw write より後の分類なら、生応答の path と sha256 を必須にする。
3. 宣言された path は、その run の権威 root と invocation id から導出した期待 path と
   **完全一致**でなければならない。無関係な file や cwd 相対 path は受理しない。
4. 期待 path の file が実在するなら、`failure_phase` は raw write より後の分類でなければならない。
   自己申告でなく実物から再導出する検査であり、生応答を消して
   「消す前に失敗した」と偽る経路を塞ぐ。
5. 読取りは権威 root から各階層を `O_NOFOLLOW` で降り、**同一 file descriptor** で
   `fstat` と読取りを行う。検査と読取りの間の差し替えを受理しない。
6. 生応答の path と sha256 は**両方が確定した場合だけ**記録する。片方だけの状態は
   `failure_phase` 側で表現する。

**理由:**

- role の parse 失敗時、生応答はディスクに保存されているのに report からその所在を
  指せなかった。実測すると `error_artifacts` は「生応答だけ無い」のではなく**空**であり、
  台帳の記述より defect が広かった。失敗した世代の一次資料に到達できないことは、
  材料レポートと試行台帳の証拠価値を直接損なう。
- 「生応答が実在するのに pointer が無い event を拒否する」という素朴な述語は**恒真化する**。
  生応答を削除して `error_artifacts` を空にすると条件の両辺が偽になり検査へ入らない。
  段 3 の敵対相談がこれを構成して示した。構造化した `failure_phase` で
  「生応答が期待される段階か」を pin することで初めて発火する。
- 分類を型で判別できることが前提になる。実測では JSON 構文の失敗と schema 違反が
  同一の例外型になり、区別できるのは診断文字列だけだった。文字列一致による判別は
  脆く、恒真な保証になりうるため採らない。
- 影響を受ける既存成果物は 0 件であることを実測した (走査した journal 5 件、
  invalid role event 0 件、trial report 0 件)。schema bump と移行は不要である。

**却下した選択肢:**

- **生応答 pointer だけを足す (分類なし)。** 上記の恒真化を塞げない。
  段 3 の敵対相談が具体的な回避経路を構成した。
- **診断文字列で失敗を分類する。** 文字列は実装の都合で変わる。
  分類を将来の裁定材料にする以上、機械可読な閉じた値である必要がある。
- **`lstat` した後に path を開き直す。** 検査と読取りが別の path 解決になるため、
  同じ bytes の symlink へ差し替えると symlink を辿って読み、hash も一致して通る。
  段 6 の敵対レビューが指摘した。
- **schema version を上げて旧成果物を失効させる。** 影響を受ける既存成果物が
  実測で 0 件だったため、版を分ける費用に見合わない。

## {{D:role-retry-deferred}}. role 応答の再試行は入れず、先に失敗分類の実測を取る

**決定:** role 応答の JSON parse 失敗に対する再試行は実装しない。
`{{D:role-invalid-failure-phase}}` が入れる失敗分類の記録を先に運用へ流し、
実測を得てから再試行の是非を裁定する。

再試行を入れる場合に同時に満たすべき条件を、段 3 の敵対相談 2 本が実測で列挙した。

1. 再試行対象を **JSON 構文の失敗のみ**とする。正常な JSON だが object でない場合と
   duplicate key は「内容の問題」であり対象に含めない。含めると不正な提案に
   無料の引き直しを与えることになり、絶対規律 2 に抵触する。
2. chain の検査は記録された分類を信じず、**生応答を再 parse して照合する**。
3. 失敗した attempt を journal に残すと journal と report の 1 対 1 対応が壊れる。
   最終 attempt だけを report へ置く形に変えるなら、payload validation receipt・
   provider artifact の bytes 検査・session isolation 証拠を
   **report ではなく全 journal attempt** に対して適用し直す。これが最も重い。
4. 2 回目が `skipped` である履歴を明示的に拒否する。
5. 再試行の直前に wall deadline を検査する。現在は世代開始前にしか検査していない。
6. 外部提供者との payload / envelope の名前衝突を、生応答と同様に解く。
7. cross-binding が全 role event に top-level の生応答 path を要求する点へ fallback を足す。
8. 予算を明示する。承認済み上限のもとで最大 invoke 数が 24 から 48 へ倍増する。
9. 実提供者を 2 回 invoke する test を足す。既存の実提供者 test はすべて 1 回しか呼んでいない。
10. attempt policy は LLM に渡す入力に載るため、値を変えると**全 invocation で
    入力 bytes が変わる**。「非 JSON のときだけ挙動が変わる」とは書けない。

**理由:**

- ユーザー指示は「再試行を足す場合は、正しさゲートを緩めない範囲に限る」という
  **条件付き**であった。段 3 の 2 レンズが独立に、素朴な実装が既存ゲートを
  4 系統で緩めると示した。条件が満たされない。
- 再試行の効果が未測定である。実提供者の応答が試行間で独立に揺れる証拠は、
  コードにも実測にも無い。既存の実提供者 test はすべて 1 回しか invoke していない。
  大型機構の本格実装前に最安の生死確認を求める `DW-G01` の要求を満たしていない。
- 会計は全 invoke を数えるが**制限はしていない**。C06 budget は bench 秒だけを予約し
  query を制限しない。倍増した上限を受け止める機構が無い。

**却下した選択肢:**

- **段 3 の所見を採用したうえで再試行も同 wave で実装する。** 上記条件 3 が
  certified 成果物の証明鎖 (cross-binding、arm binding、session isolation) に触る。
  効果が未測定の機構のために証明鎖へ穴を開ける順序は採らない。
- **分類だけ入れて再試行の裁定材料が揃うと主張する。** これは言い過ぎである。
  段 6 の敵対レビューが正しく指摘したとおり、分類記録から得られるのは
  **失敗分類ごとの発生率**であって、同一 payload の次試行が成功する**救済率**ではない。
  発生率は必要条件だが十分ではない。救済率は実提供者を複数回叩く実験でしか得られない。
