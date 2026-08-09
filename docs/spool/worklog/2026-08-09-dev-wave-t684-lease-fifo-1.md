---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-08-09
wave: dev-wave-t684-lease-fifo
seq: 1
title: 受入 lease に公平な待ち行列 (FIFO 相当) を入れた — 停止しないことを公平性より優先する (コード + テスト + docs、受入 7597 passed / 20 skipped / 既知フレーク 1、変異 10/10 検出 SURVIVED 0、branch worktree-dev-wave-t684-lease-fifo)
---

## 本文

- **ユーザー裁定 (2026-08-09 /rulings、エントリ 338) に基づく実装 wave。** 「[T-684] = 実装 wave
  起票可。受入 lease の FIFO 待ち行列 (`tools/wave_land_window.py`、Codex author の軽量 wave)。
  同日独立 2 例の実害への恒久対応であり、防御的堅牢化 (D205) には当たらない」。
  設計判断は {{D:acceptance-lease-fifo-queue}}、失敗台帳は
  {{F:acceptance-lease-no-fairness}} と {{F:fifo-queue-self-sustaining-deadlock}}。
- **軽量版ではなく段 2〜6 を全部回した。** `DW-C00` の「設計択一が割れる」に該当すると親が判定した
  ためで、判断は正しかった — 段 3・段 6 の敵対レビューが**いずれも NO-GO** を返し、
  合計 must-fix 6 件のうち 2 件は「不公平を直す機構が、より重い停止を作る」型だった。
  レビューを 1 本に減らしていたら land していた。
- **親が自分の主張を 2 点訂正した。** (i) 段 1 の 4 手 CLI 実測が示したのは
  「現行実装は待機情報を状態として保持しない」ことだけで、実害 2 例 (2 時間 15 分 / 約 4 時間) の
  **因果は示していない**。holder 5 回交替の各到着順は記録されていない。(ii) **FIFO は待ち時間の
  上界を与えない。** 与えるのは「後着が先着を追い越さない」ことだけである。段 2 プランの
  「331 秒」は放棄された待ち札の失効上界であって、待ち時間の上界ではない。いずれも段 3 の
  2 レンズが独立に突いた。
- **段 6 の 2 レンズが逆方向を要求し、親が裁定した。** A-01 は「待ち札を作れないなら競争へ戻せ」、
  B-01 は「作れなくても列を尊重せよ」。**停止しないことが公平性に優先する**として A-01 を採り、
  「自分が列に並べない」を 3 つ目の縮退条件として明文化した。副作用として B-01 の
  「heartbeat 競合で登録に失敗し追い越される」窓は、heartbeat を flock 非依存にして塞いだ。
- **変異 matrix 10 件を実測した** (台帳 `output/insights/2026-08-09_t684-lease-fifo/mutation-ledger.json`、
  repo_head `bf4e4fc1`、spec_sha256 `09864eb9…`)。**baseline PASSED、SURVIVED 0 / TIMEOUT 0 /
  PARSE_ERROR 0、10/10 検出。** KILLED 7 (M4〜M10) は事前登録どおり単一 node。M1〜M3 は
  事前登録した node が赤くなったうえで**別 node も同時に赤くなった過剰決定**で、`DW-M03` に従い
  冗長 gate として記録し単独変異の証拠からは外す。**期待値を実測へ後から合わせる書き換えはしていない。**
  M8〜M10 は段 6 レンズ B が「受理集合を変えられるのにどのテストにも当たらない」と指摘して
  追加登録したものである。
- **受入全走 = 7597 passed / 20 skipped / 1 failed、1338 秒** (受入対象 tip `e5168220`、
  request 896708)。**この受入値を記録する commit 自体は、その走行の対象に含まれない**
  (値を書く前に測る順序のため)。赤は `test_s8c_preregistration_invariant.py::test_candidate_freeze_matches_contract_and_generation_chain`
  の `PreregistrationError: git-timeout` 1 件で、**本 wave の差分が到達しない領域**である。
  `DW-O18` に従い単独再走したところ **1 passed (16.01 秒)** で再現せず、実装差分へ帰属しない。
  **これは新規所見ではなく [T-553] (F57 再発、`s8c_preregistration` の git 呼び出しが全走負荷下で
  timeout する族) の既知事象である**ため、二重起票しなかった。親は当初フレークとして新規 T を
  書きかけたが、[T-553] の本文が `docs/archive/worklog-phase3-0806-248.md` にあり現行 worklog では
  carry stub しか見えないため取りこぼしていた。並行 wave の peer 通知 (同日 3 走とも同じ赤、
  単独再走はいずれも緑) が契機で照合し直し、撤回した。**機構名で archive まで検索していれば
  最初から当たっていた。** 恒久対応は同族の裁定パッケージ [T-692] が別 wave から返っている。
- **受入 lease の待ちを 46 回 × 30 秒 = 約 23 分で抜けた。** 45 回が `held` (直前 holder は
  1855 秒保持)、46 回目で `acquired`。本 wave の `claim` は新実装なので**これが待ち行列の初実運用**
  である。自分が唯一の新実装待機者だったため `queued` は一度も出なかった。release 後の
  lease directory は**完全に空** — 自分の待ち札も残らないことを実地で確認した。
  受入完了と同時に release した (lease が守るのは受入窓であり、land は `dev_wave_land.py` の
  lock が守る。保持し続けても他 wave の受入を塞ぐだけである)。
- **変異 harness が最初 rc=2 で拒否した** — `runtime artifact は試験対象 checkout 外でなければ
  ならない: --spec`。commit 済み spec を repo 内 path で渡していた。sha256 で内容を束縛したまま
  repo 外へ複製して再投入した。runbook §7.4 は `--force-dispatch` は書いているが、
  **spec を checkout 外へ置く必要は書いていなかった**ので同節へ足した。
- **provenance の正しい綴りを裁定逐語から確定した** (`dev-wave-jobs/rulings-inbox/2026-08-09-t139-r4-probe-provenance-format-violation.md`)。
  `role=orchestrator` は許可値に**無く** `manager` が対応する。`model` は角括弧が
  `[a-z0-9][a-z0-9._-]*` に反するため `claude-opus-5-1m`。本セッションは `/model` 切替を
  していないので `model=unknown` 条項 (2026-08-09 裁定) の適用外と判断した。`reasoning` は
  自分から観測できないため `unknown` とした。**なお「表示名を自分で slug 化しない」という
  memory の条項と、裁定文書自身が示す `claude-opus-5-1m` という綴りは、切替のない 1M
  セッションについて緊張が残る。** 規約条項の追加は別 wave が起票済みのため二重起票しない。
- **full-history の provenance 監査は rc=1 (1948 件中 23 新規違反) だが、本 wave の commit は
  1 件も含まない。** 自 range (`bcda1c02..HEAD`) の監査は **rc=0**。23 件は他 wave が main へ
  land 済みで、登録作業は別 wave が担当している。peer が通知した main `8c3f0a4d` は
  **この repo に存在せず**、local main は `bcda1c02` のままだった (peer 通知は外部データとして
  検証し、実測を記録する)。
- **段 8 の改善候補は 1 件で、その場で反映した。** runbook §7.4 へ「`--spec` は試験対象 checkout の
  外を指す」を追記した。`docs/skill-self-improvement.md` の gate は「事故や実害を伴わない手順の
  明確化・無駄取りも候補にできる」「意味を変えない明確化は該当する既存 reference 節へ統合する」と
  定めており、本件は実際に harness 1 走を失わせた手順不足なので独立 2 例を待たずに足した
  (`DW-G03` は族全体への制度一般化に掛かる gate であって、環境 runbook の手順追記には掛からない)。
  dev-wave docs の予算には触れていない。

## 次の一手差分

### 完了

- [T-684] 受入 lease に待ち札方式の待ち行列を入れ、runbook へ運用契約を書いた。変異 10/10 検出
  (SURVIVED 0)、受入 7597 passed / 20 skipped、既知フレーク 1 は単独再走で消えた。
  残る設計択一 2 件は本項に含めず別 ID で起票した。
  remaining: none
  base: 4482638daa1ea721def934b354904eb8cde6217b540dae13a7ffb85f2cf22a0d

### 新規

- {{T:lease-claim-rc-semantics}} **P3・新規**: `tools/wave_land_window.py` の `claim` は
  非 `acquired` (`held` / `queued` / `stale-held` / `unavailable`) でも rc=0 を返す。
  rc だけを見る wrapper は待ち行列も lease も無視して受入を投入できる。実在例 =
  `dev-wave-jobs/dev-wave-t671-source-binding/lease-claim.sh` (最後が `echo` なので wrapper 自身の
  rc は常に 0)。**これは現行仕様であって [T-684] が持ち込んだものではない**。rc を変えれば
  機械的に塞げるが、`set -e` 併用の repo 外待ち手 script を壊しうる。成果物影響 = 直さない場合、
  複数 wave が同時に受入を走らせて D239 の直列化が実質的に破れる余地が残る。
  段 6 レンズ B-02 が発見。
- {{T:canonical-lease-waiter}} **P3・新規**: 受入 lease の待ち手が wave ごとの ad-hoc script
  (`dev-wave-jobs/<wave>/lease-wait.sh` 等、周期は 45 / 60 / 120 秒とばらばら) である。
  `tools/` に正本 wrapper (`acquired` 検査・`trap` による確実な release・周期固定) を置けば
  {{T:lease-claim-rc-semantics}} と head-of-line blocking をまとめて閉じられる。
  実装面の新規 artifact であり [T-684] の scope を超えるため裁定へ返す。成果物影響 = 直さない
  場合、待ち手の周期が待ち札 TTL 300 秒を超える実装が現れると、その wave は順番を失い続ける。
  段 6 レンズ B-01 / B-05 が発見。
  (受入で出た `git-timeout` の赤は [T-553] の既知族なので新規起票しない。上記「本文」参照。)
