---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-09-16
wave: dev-wave-t2616-prewarm-configure-node
seq: 1
title: [T-2616] receipt memo の prewarm を受入全走でだけ collection 前へ起こし、待ちは既存 flock の上の最小差分にした (コード + テスト、branch worktree-dev-wave-t2616-prewarm-configure-node、変異 matrix = baseline PASSED・6/6 KILLED・SURVIVED 0・MISMATCH 0・期待 node 完全一致)
---

## 本文

- **裁定の授権。** 第 19 回 /rulings 項 4 (対象 T-2616) が「受領証の準備を collection 前へ移し
  待ち合わせを外す変更は**赤 0 件で成立する形が示せた場合に限り採用**。示せない間は D518 の
  待ち合わせ契約を維持」と定めている。この裁定は本 wave の開始後に着地し、段 5 dispatch 直前の
  `--mode midflight` gate が main の 2 commit 進行を実測したことで気づいた。`DW-S04` の
  「段 4 直前に裁定 inbox を再走査」がこの形で効いた。

- **設計が大きく縮んだ。** `_ReceiptMemo.prewarm` の `write_once()` は `_locked(...)` の**内側**で
  `_resolve_now()` を呼ぶので、**cache の flock は解決の全所要 (実測 28.328 秒) のあいだ保持される**。
  reader の `read_existing()` も同じ blocking flock の中にある。つまり**プロセス跨ぎの待ちは
  元から実装されていた**。欠落は 1 点だけで、reader が writer より先に lock を取ると本体不在で
  即 `cache-missing` になる。足したのは「早期 job が `workerinput` で明示されたときだけ、
  本体不在で即赤にせず期限まで retry する」であり、待ち機構の作り直しではない。
  依頼文の「worker 側は cache を最大 120 秒待ち `.pending` / `.failed` marker で失敗を共有する」は
  この 1 点のための記述だったと読み直した。

- **段 6 のレビューが「裁定 R1 が未充足」を実証した。** 除外する narrowing の destination 名が
  pytest の実 parser と食い違っていた — `--ff` は `ff` でなく `failedfirst`、`--sw` / `--sw-skip`
  (`stepwise` / `stepwise_skip`) と `-o` (`override_ini`) は列挙自体が無かった。
  **さらに悪いことに、同じ wave が追加した test も同じ誤名を使っており、test が実装の誤りと
  自己整合して検出できていなかった。** 実 `Parser` へ plugin の addoption を登録して destination を
  照合し、さらに独立した CLI 入力でも検査する対照を足して閉じた。放置すると `--ff` や
  `-o python_files=...` 付きの焦点走で早期 prewarm が発火し、D518 が却下した無条件 prewarm が
  焦点走へ漏れていた。

- **「宣言した上限が縛らない」も閉じた。** 120 秒の期限確認が lock 取得の前にしかなく、
  取得後の読取り・unlock・close を終えてからの再確認が無いため、期限を越えて成功した読取りを
  そのまま通していた。成功返却の直前でも共有 deadline を確認する形へ直した。

- **到達不能な防壁はそう書いた。** `publication-regressed` の分岐は production の待機経路から
  到達しない (待機は使い捨ての reader を 1 回使うだけ)。削除せず、到達しないことと production 側の
  fail-closed の所在をコメントへ明記した。**gate として数えない。**

- **前 wave の (b) の機序を変異で実測再現した。** `pytest_configure_node` の冒頭で早期 return させると
  `pytest.UsageError: xdist workerinput に acceptance ledger snapshot が無い` で worker が node down する。
  session ごと落ちて FAILED 行が出ないため `DW-M08` の期待 node 完全集合を作れず、matrix からは
  外して session 単位の fail-closed 実証として別枠に記録した。前 wave が「probe の入れ子 xdist 走行で
  worker が crash」と書いた現象と**同型の機序**である (locus は外側 session なので同定ではない)。

- **親自身の読解が 1 件誤っていた。** 「`DSession.pytest_sessionstart` は `-p` で載る plugin より先に
  走るので FakeMemo の差し替えが間に合わない」と書いたが、`xdist/dsession.py` の当該 hook には
  `trylast=True` が付いており、pluggy は trylast を最後に呼ぶ。段 3 の相談が反証し、親が現物で
  追認して撤回し、子へ渡した射影 file も訂正した。

- **F945 を踏み、単独非再現で非帰属を確定した。** 受入 attempt 2 で shard-0 の 28 件が
  `git -C <worktree> ls-files --others --exclude-standard -z` の 30 秒 TimeoutExpired で setup error に
  なった。直近の再発 (2026-09-14) と件数まで同じである。F945 の恒久対応どおり timeout 拡大・
  stub 化・除外・gate 新設は行わず、単独走で **51 passed / 15.92 秒 / rc=0** を確認して非帰属と
  判定した。shard-2 の 2 件 (`test_floor_checkpoint_filesystem_hang_has_a_wall_clock_bound[write]` と
  pytest internal error) も単独走 **143 passed / 4.83 秒 / rc=0** で非再現だった。

- **同じ受入で [T-2622] の dispatch job exit hang も踏んだ。** 3 shard とも junit.xml を書き終えた後、
  job `888.nqsv` が Elapse 3528 秒 / CPU 0.25 秒で終了せず、wrapper が `do_wait` で止まった。
  さらにその job が **orphan hold** を残し、後続 6 回の受入投入がすべて
  `preclaim-history-provenance rc=70 source_rc=16` で弾かれた。job が walltime で消えて hold が
  解けるまで待ってから投げ直した。

- **受入の実測 (attempt 11、緑)。** `verdict=child-green` / `red_nodeids=[]` / `flake_nodeids=[]` /
  `tested_main=119895f5f` / `tested_tip=365981846`。shard 別の pytest session wall (junit) は
  **shard-0 = 289.103 秒 / shard-1 = 227.654 秒 / shard-2 = 273.059 秒**、
  job Elapse は 305 / 245 / 288 秒。**最遅 shard は 289.1 秒で 300 秒を切った。**
  **ただしこの 1 走で効果の因果は主張しない。** 前 wave 自身が「単一走どうしの比較で効果を
  主張してはならない」と撤回を記録しており、同時刻の対照が無い n=1 の比較は無効である。
  記録するのは「この走行の最遅 shard wall は 289.1 秒で、新規赤は 0 件だった」という事実に留める。

- **親の契約逸脱を 2 件記録する。** (1) 段 2 / 段 3 の子を `reasoning=high` で起動したが、
  `DW-S02` / `DW-S03` の契約は `medium` である。親の読み落としで、予算を契約より多く使った方向の
  逸脱。再走は overrun を倍にするだけなので行わなかった。(2) 段 5 の実装子 prompt に `## 総括` 節の
  要求を書き落とし、成果物が `f43_fragment` で未受理になった。codex 自体は exit 0 で実装は
  完全に残っていたため、`DW-O01` の「未受理は未完了と記し次の子に監査させる」に従い、
  段 6 のレビュー 2 本に差分を監査させた。

- **エージェント工数。** codex 子 6 本 (plan 1 = reasoning high、consult 2 = high、author 1 /
  review 2 / fix 1 = docs 権威の medium、すべて gpt-6-astra)。受入投入 11 回 (緑 1、
  main churn による postcheck 競走 1、orphan hold による不発 6、job hang 1、他 2)、
  焦点走 6 回、変異 matrix 2 回 (probe + 本登録)。

## 次の一手差分

### 完了

- [T-2616] 受入全走 attempt 11 が `child-green` / `red_nodeids=[]` で通り、最遅 shard の
  pytest session wall は 289.1 秒で 300 秒を切った。変異 matrix は 6/6 KILLED。
  効果の因果は同時刻の対照が無い n=1 では主張しない。
  remaining: none
  base: 8b342557eb5b7023eff08e0c0fac37658ee5dc7522180e4f960d8df8e26e6048

### 新規

- {{T:acceptance-wall-contemporaneous-control}} **P2・新規**: 本 wave の 289.1 秒は n=1 であり、
  同時刻の対照が無い。prewarm の起動点が最遅 shard wall に効くという因果を主張するには、
  同じ窓で早期起動あり / なしを交互に投入する対照走が要る。何走必要かを先に見積もる。
- {{T:acceptance-receipt-shard-wall-field}} **P2・新規**: 受領証 schema v5 に shard 別 wall の
  field が無く、D1620 が定める測定面を受領証だけでは読めない。本 wave は shard 成果物の
  junit と dispatcher log から測った。schema へ足すか、測定面の定義を現物へ合わせるかを決める。
