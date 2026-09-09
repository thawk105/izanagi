---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-09-10
wave: dev-wave-t2028-axis3-live-preflight
seq: 1
title: [T-2028] 軸 3 live 経路の pacing と登録どおりの再試行を実装した — 走行の可否は費用判断としてユーザー裁定へ返す (コード + テスト + 変異、branch worktree-dev-wave-t2028-axis3-live-preflight、変異 10/10 KILLED・期待 node 完全一致)
---

## 本文

- 依頼は「§13.1 blocking 5 件を解いたうえで軸 3 の登録済み検索を走らせる」だった。一次資料で
  照合したところ、**5 件のうち走行前に閉じられるのは 1 件もなかった** — B4 は 2026-09-01 に閉じ済み、
  B3 は D1206 で裁定済み、B2 と B5 は live preflight を走らせること自体が閉じ方、B1 は取得後にしか
  閉じない。したがって本 wave の実行対象は live preflight に確定した。
- **U11 は既に裁定済みだった (D1623、2026-09-04、ユーザー裁定)。** 軸 3 の
  `2026-09-01-axis3-search-amendment.md` §6 は「この扱いを維持するかは人間裁定に属し、裁定が付くまで
  軸 3 の live 本走は開始できない」と書いているが、その裁定は軸 1 側の文脈で既に下りていた。
  凍結物だけを読むと未裁定に見える。**凍結物の「裁定待ち」は decisions.md で照合しないと古い。**
- **走行前に塞ぐ必要のある実装欠陥を 3 段階で見つけた。**
  1. 親が段 1 で: 実行器に pacing が無く、live preflight の 1929 本を無遅延で連射する。
     旧登録 §8.4 は 429 を受けた query を `未完走` にすると定めるので、自分で起こした 429 が
     行を潰す。被害は最大で残り全行に及びうる (loop は非 200 で止まらない)。
  2. 段 6 レビュー 2 本が計 10 件の must-fix を返した。最重要は **transport 例外が再試行対象に
     なっておらず、DBLP の接続切断 1 回で 19.5 時間の走行ごと落ち、取得束が再開不能になる**こと。
     軸 1 は同一索引で「15 秒間隔でも 7 リクエスト程度で `RemoteDisconnected`」を実測している。
  3. レビュー A が最小再現で、**親の裁定が生んだ欠陥**を示した。親が 429 / 503 を再試行対象に
     入れたため、evidence が `[429, 200]` の行の status が `ready` になっていた。§8.4 の潜脱である。
- **親の裁定を 2 件、自分で訂正した。** (a) 再試行するのは transport 例外だけとし、HTTP 非 200 は
  その場で `unavailable` にする ({{D:axis3-retry-transport-only}})。(b) 「同一 stream の 4 回目を
  拒否」は登録より 1 回厳しかった。旧登録 §8.3 の逐語は「その各ページが最大 4 回 (初回 + 再試行 3)
  送られる」であり、4 受理・5 拒否が正しい。
- **live preflight を発火させるかは費用判断としてユーザー裁定へ返す。** 実装で確かめた構造:
  preflight report と bundle は seal に exact 束縛され (`registration_seal_sha256` の一致要求)、
  resolver を実装すると blocked 193 行の `request_factory.state` が変わって catalog bytes と seal が
  変わる。**その瞬間、今回の preflight bundle は本走に使えなくなる。** さらに `run_ready` は
  preflight report から `first_external_request_at` を継承するので、**preflight の 1 本目で軸全体の
  30 暦日締切が動き出す。** 一方で走らせる価値もある — B5 の予算総和が 20 万 request を超えるなら
  軸は `未完走` で resolver 実装は無駄になるので、**先に測るのが安い**。
  1929 本の外部 request と約 1 日を、後で supersede されると分かっている成果物へ使うかを諮る。
- 段 3 相談 2 本と段 6 レビュー 2 本、段 2 プラン、段 5 実装、段 6 fix の計 7 子。すべて
  `gpt-5.6-sol` / effort xhigh、rc=0、`check_codex_output.py` 緑。
- **受入所要台帳は A-1 論文証明の no-touch manifest に載っている。** 新しい test node を足すと
  `test_paper_story_a1_headline.py::test_existing_a1_non_touch_manifest_is_empty_from_base` が
  作業ツリー検査で赤になり、commit すると通る (F283 の再発として記録した)。
- 変異 10 件は probe で観測 node を集めてから本走し、**10/10 KILLED・期待 node 完全一致**。
  m04 / m05 / m08 / m09 / m10 はそれぞれ 1 node だけを落とし、狙った機構を単一の検査が守っている。
  fix 2 巡目の後、land 対象 tip に対して再走しても同じ結果だった。
- **段 6 の fix 1 巡目が既存テストを 1 件、報告なしに削除していた** ({{F:child-deleted-existing-test-undetected}})。
  親の通常検算 (変更面比較と焦点走) はどちらも検出しない — 前者は file 単位、後者はテストが
  消えれば赤にならない。**見つかったのは受入が `owned-path-overlap` で止まったためで偶然である。**
  基底と現行の関数名集合を突き合わせると削除 1・追加 14 だった。fix 2 巡目へ差し戻し、
  子は原文復元で赤を確認したうえで、同名・同性質のまま失敗種別だけ現行契約へ合わせた。

## 次の一手差分

### 完了

- [T-2029] 文献索引の API 版番号の代用可否は **D1206 (2026-08-28) で裁定済み**だった。
  「接続先・応答の field 名・応答 header・生データの digest」を組にして版の代わりに固定してよく、
  ただし「版番号」と呼ばず「版が取得不能な場合の代替来歴」と明記する条件付き。
  本 wave が一次資料で照合した。
  remaining: none
  base: a690ead7108a7ecf2ec193ca030adc02697b379a0ea778597ecdb8a95b779181

### 更新

- [T-2028] **P2・一部完了**: 軸 3 live 経路の pacing・再試行・冷却・N3 記録を実装し、変異 10/10 KILLED
  まで到達した。残るのは live preflight の発火判断 (1929 本の外部 request、約 19.5 時間、
  後で supersede される成果物) で、**ユーザー裁定待ち**。裁定が「走る」なら
  `preflight --live` を login node で実走し、新日付の実行記録で B2 と B5 を閉じる。
  base: 20dc821047fa3964b538551c6ed43d47edd0a21a59c70e525c48ab18fc94d65a

### 新規

- {{T:axis3-resolver-and-control-evaluator}} **P2・新規**: 軸 3 の resolver と control 評価器を実装する。
  DBLP venue 経路 168 本と OpenAlex author / work ID 経路 20 本の request factory が未解決で
  `blocked` のまま残り、control の採点器も無い。**契約 §3 は `blocked` を母集合から消さないので、
  この 193 行を抱えたままでは軸はどう走らせても `未完走` である。** 実装すると catalog bytes と
  seal が変わるため、その時点で再登録が要る。
- {{T:axis3-dblp-title-lookup-amendment}} **P3・新規**: DBLP 題名 lookup 5 本の意味的 amendment。
  凍結登録に DBLP 題名 query の完全 bytes が無いため resolver では閉じない。§8.5 に従い
  新日付・新 ID の後継登録が要る。B2 の anchor 到達性のうち DBLP 題名経路だけがこれで塞がれている。
- {{T:axis3-pending-intent-recovery}} **P3・ユーザー裁定待ち**: 取得束の未確定 attempt intent を
  回復可能にするかの裁定。process が request の途中 (intent 後、commit 前) で死ぬと
  `resume` は `unconfirmed_attempt_intent` で止まり、raw 応答が耐久化済みでも再開できない。
  塞ぐには one-shot receipt・重複送信・予算会計の契約判断が要る。
- {{T:axis3-transport-ceilings}} **P3・ユーザー裁定待ち**: 軸 3 transport に本体 byte 上限と
  attempt 全体の wall-clock 上限を入れるかの裁定。軸 1 は 16 MiB 上限を持つが軸 3 は無く、
  socket timeout 30 秒だけが停滞を縛る。入れると失敗分類と受理集合が変わりうる。
