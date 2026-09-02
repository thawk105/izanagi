---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-09-03
wave: dev-wave-t2090-openalex-fetch
seq: 1
title: [T-2090] 軸 1 OpenAlex の 1 窓目を取得した — 条件 1 は通り、塞ぎは条件 5 へ移った。同じ request を同日に 2 回投げて判定が両方向に反転した (取得 + docs、branch worktree-dev-wave-t2090-openalex-fetch、実装面 0・変異 matrix 免除)
---

## 本文

- 依頼は「発行済みの再開点から無償枠の窓ごとに OpenAlex 78 leaf を継いで取り切る」だった。
  **新 epoch `AX1-20260902-E1` に再開点は存在しなかった** — 証拠 bundle が 1 つも無く、
  改訂契約 §4 が全枝の再実行と新規 bundle root を要求している。したがって本走行は
  再開ではなく新規開始である。78 leaf のうち 12 leaf を起動して 1 窓を使い切る手前で閉じた。
- **条件 1 の修正は効いた。取得した全 93 頁で条件 1 が `可`、順序を理由に落ちた頁はゼロ。**
  取得前のオフライン診断でも、旧 epoch の唯一の OpenAlex 生応答に対し旧の完全一致比較が
  `不一致`、現行の順序非依存比較が `一致` を返した (bundle 外の診断であり再包装していない)。
- **塞ぎは 1 段先の条件 5 へ移った。** 頁ごとの条件 1〜6 が全頁 `可` でも、leaf 全体の
  `distinct_work_id_total_mismatch` が落ちる。索引の申告総数と distinct な work ID 数が
  一致せず、結果集合が大きいほど頁境界の重複が増えて distinct が申告を下回る
  (Q2: 1606 に対し distinct 1605・重複 2、Q4: 4698 に対し 4694・重複 11、
  Q5: 6122 に対し 6116・重複 14)。**改訂契約 §8 の未決 U11 が実データで発火した初の記録。**
- **条件 5 は走行間で非決定的だと実測した。** 親の driver の重複除去条件が壊れており
  `Q1` と `Q2` を意図せず再走したところ、**判定が両方向に反転した** —
  `Q1` は `branch_complete` → `blocked_on_ruling`、`Q2` は `blocked_on_ruling` →
  `branch_complete`。同じ登録 request を同じ日に 2 回投げた結果である。親のミスから出た所見だが
  事実として重要で、条件 5 は現行の形では OpenAlex に対して安定した判定にならない。
  機構は再走を正しく扱い (`attempt_number=2`・別 raw file)、1 回目の証拠を上書きしていない。
  検査器は `bundle_validation_complete: true` を返し、leaf 判定は最後の attempt を採る。
- **無償枠の自己施錠は発火させずに済んだ。** 実行器は残量だけを見るので、窓を使い切った観測
  (`remaining < 40`) が持続化されたときにだけ次窓が止まる。leaf の起動と起動の間で残量を読み、
  残量 200 で新規起動を止めた (終了時 60)。**実行器を変えずに窓に収めた。**
- **段 3 lane sol の判定を採り、枠の失効実装は本 wave では行わない。** 持続化観測に失効を
  入れる案は発行規範 `remaining - 30 >= 直近観測 cost` (旧改訂 §4.1) を緩める。同節は
  「窓が明ける瞬間は観測していない」と明記しており、`observed_at + reset_seconds` を期限とする式は
  仮説であって凍結済みの規範ではない。U12 の裁定なしに親が既成事実にしない ({{D:openalex-quota-expiry-needs-ruling}})。
- **段 3 の 2 レンズがいずれも実測付きの欠陥を出した。** lane sol は Python 3.10 の
  `datetime.fromisoformat` が末尾 `Z` を読めないこと (実測) と、`_merge_quota` が古い
  `reset_seconds` を新しい観測時刻へ付け替えることを指摘。lane luna は独立に同じ merge の欠陥に
  到達し、加えて (a) page evidence schema が catalog path を相対文字列の const で要求すること、
  (b) `pass_complete` の rc が 3 なので rc ではなく JSON の `state` で判定すべきこと、
  (c) 一括実行器が repo に存在しないこと、を現物で示した。**(a)(b) はいずれも取得の argv を
  誤らせる実害があり、実際に本走行で採用した。**
- 段 2 プランは親の実測を 4 点訂正した — `permits_next` の呼出しは 3 箇所 (1646 は load であって
  gate ではない)、M6 は正規 CLI 経路に限定すべき、M7 は「新しい登録 commit の clean bytes に
  固定される」が正確、M9 の `git grep` は 8 file を返し live-code consumer はそのうち 3 file。
- 登録 commit は取得時点の local main HEAD `4ec3eba04` を使った。本 wave が作った commit では
  ないので、再開に必要な `HEAD == registration_commit` は main の祖先を detach するだけで満たせる。
- 生 bundle は repo 外の恒久 path に置いた
  (`/work/1/SFC/tanab/axis1-bundles/2026-09-03-t2090-openalex/bundle`、102 MB)。
  `verify_bundle` は checkpoint の `bundle_root` と検証先 path の一致を要求するため、
  worktree 内に置くと撤去後に再構成が要る (2026-09-02 の [T-2090] wave が踏んだ罠)。
  repo には URL・取得時点・digest・再開点を含む部分 mirror (約 2.3 MB) だけを入れ、
  raw と ledgers を除いた。**取得完了時に bundle 全体を commit する。**
- エージェント工数: codex 子 3 本 (plan 1、consult 2、いずれも read-only、reasoning=xhigh)。
  rc はすべて 0、`check_codex_output.py` も 3 本とも rc=0。実装子は起動していない
  (段 4 で「実装しない」と裁定したため)。
- 実装面の差分は 0 なので変異 matrix は免除 (DW-S04)。受入全走は免除せず親が実走した。
- 逐語と部分 mirror は `output/insights/2026-09-03_t2090-axis1-openalex-window1/`、
  凍結した実行記録は `docs/related-work/claim-survey/2026-09-03-axis1-search-execution.md`。

## 次の一手差分

### 更新

- [T-2090] **P2・1 窓目を取得済み・継続可**: 軸 1 の OpenAlex 78 leaf を無償枠の窓ごとに
  継いで取り切る。**2026-09-03 に 1 窓目を実行した** — 完走 1 (`Q2`)、pass 1 完了で独立 2 走目
  待ち 8 (`checkpoints/000001`〜`000008`、`resume_action=start_independent_pass`)、
  条件 5 で未完走 3 (`Q1`/`Q4`/`Q5`、checkpoint なし)、未走 66。
  生 bundle は `/work/1/SFC/tanab/axis1-bundles/2026-09-03-t2090-openalex/bundle`、
  登録 commit は `4ec3eba04`。次窓の再開は、その commit を detach した木を cwd にして
  同じ bundle 絶対 path へ `--checkpoint` (2 走目) と `--query-id` (未走) を投げる。
  1 窓は 97 request、shard は 1 leaf あたり 1〜5 request、非 shard は 4〜31 request。
  残り 66 leaf + 2 走目 8 本には最低 2 窓を要する。**条件 5 の裁定 ({{T:openalex-condition5-ruling}})
  が決まるまで、`Q1`/`Q4`/`Q5` を再取得しても完走にはならない。**
  base: f9d98b7a7c00e8fc66ed1b9d41825d9890e161a5f430b357265427468379fbed

### 新規

- {{T:openalex-condition5-ruling}} **P1・ユーザー裁定待ち・T-2090 の一部を塞いでいる**:
  OpenAlex の条件 5 (`distinct_work_id_total_mismatch`) をどう扱うか。改訂契約 §8 の未決 U11
  そのもので、2026-09-03 に実データで発火した。**索引が頁境界で同じ work ID を 2 回返しつつ
  総件数では 1 回しか数えるため、distinct が申告総数を下回る。** さらに同じ登録 request を
  同日に 2 回投げて判定が両方向に反転しており、現行の形では安定した判定にならない。
  選択肢は (a) 条件 5 を distinct と申告総数の差に許容幅を持たせる形へ改める、
  (b) 頁境界の重複を明示的に除いたうえで厳密一致を保つ、(c) 現状のまま `未完走` を受け入れて
  OpenAlex の非 shard 枝を諦める。(a)(b) は完走述語の変更なので意味的 amendment に当たり、
  新 epoch・新 query ID・全枝の再実行を要する。**着手前に裁定が要る。**
- {{T:openalex-quota-window-design}} **P2・ユーザー裁定待ち**: 窓をまたぐ継続取得の設計
  (改訂契約 §8 の U12)。持続化した無償枠の観測に失効を入れる案は、発行規範
  `remaining - 30 >= 直近観測 cost` を緩めるため凍結契約 §4.1 の改訂に当たる
  ({{D:openalex-quota-expiry-needs-ruling}})。**2026-09-03 時点では急がない** —
  窓を使い切る手前で親が止めれば施錠は起きないと実測した。窓を最後まで使い切りたくなった
  時点で必要になる。
- {{T:openalex-evidence-time-binding}} **P2・ユーザー裁定待ち**: 証拠が「登録 commit の後に
  取得された」ことを何へ束縛するか (改訂契約 §8 の U13、受領証・nonce・追記専用の登録)。
  現行契約にこの束縛は無く、検査器は旧生応答の再包装を拒否しない。2026-09-03 の走行は
  実際に登録 commit の後に新規取得したが、**検査器はその事実を検証していない。**
