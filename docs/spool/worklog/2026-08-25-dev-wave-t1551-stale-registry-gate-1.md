---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-08-25
wave: dev-wave-t1551-stale-registry-gate
seq: 1
title: [T-1551] stale registry 検査を実効 scheduler によらず発火させ、恒真な control を実物へ置き換えた (コード + テスト、branch worktree-dev-wave-t1551-stale-registry-gate、変異 matrix = baseline PASSED・10/10 KILLED・SURVIVED 0・MISMATCH 0)
---

## 本文

- 設計判断は {{D:flaky-stale-delegation-by-dsession}}。新しい失敗型は
  {{F:probe-mutation-seen-by-concurrent-reviewer}}、F174 は 3 例目の再発。

- **依頼が挙げた 2 つの穴のうち 1 つは、依頼の書きぶりのままでは既に成立していなかった。**
  「`_xdist_flaky_collection_is_complete` を常に `False` にする変異が生存する」は、
  親が base main で当て直すと **KILLED** になる。殺しているのは mut5 観測より後の
  commit `c6f5d756` が足した合成 config assertion である。
  一次資料 `mutation-ledger-mut5-survived.json` は repo の外
  (`/work/1/SFC/tanab/dev-wave-jobs/dev-wave-flaky-quarantine/`) に実在し、
  `repo_head 583543ca` / KILLED 4・SURVIVED 1 で、置換は当該関数の先頭へ
  `if True: return False` を入れる形だった。親の再実測はこれと同型である。
- **生きている形は配線側だった。** xdist hook の**呼び出し側**を殺す変異は base main で
  **SURVIVED** (93 passed)。述語の戻り値だけが pin され、hook から検査への配線は未証明だった。
  依頼の (b) はそのまま再現した (`-n 2 --collect-only` + stale 注入で rc=0、
  実効 scheduler は serial)。`-n` を外した同じ走行は rc=4 で正しく落ちるので、
  壊れていたのは経路選択だけである。

- **依頼にも前 wave の記録にも無い事実として、前 wave の control の注入は
  production の conftest 実体に届いていなかった。** `orchestrator/tests/__init__.py` が
  無いため、pytest が読む `conftest` と test が import する `orchestrator.tests.conftest` は
  別 module object である。親が pytest 実行中に plugin manager を走査して
  `registered=1` / `__name__=conftest` / `sys.modules` に `conftest` のみ、を観測し、
  別途 `same object: False` を id 比較で確認した。前 wave の control は
  `-p orchestrator.tests.conftest` 相当の二重登録を渡していたときだけ注入が効いていた。
  本 wave の control は `-p` に頼らず、登録済み plugin を実 path で 1 件だけ特定して patch し、
  対象が 1 件でなければ plugin 自身が落ちる形にした。

- **親の brief が 1 件間違っており、段 3 の 2 レンズが独立に指摘した。**
  親は「growth-hold 側は受入 regime で一度も stale 検査が発火していない」と書いたが、
  誤りである。worker は `workerinput` を持つので委譲条件を通らず、自分で検査する。
  xdist が worker へ controller の argv をそのまま渡すことが根拠であり、
  同じ理由で **flaky 側も受入では worker が検査している**。
  この訂正は本 wave の位置づけを変えた — 直したのは「受入の正しさゲートの破れ」ではなく、
  受入以外の invocation 形に残っていた衛生検査の欠落と、恒真な control である。
  報告でも commit 本文でもそう書いた。

- **段 2 の plan が提案した「`numnodes` が不正なら停止」は採らなかった。**
  段 3 の 2 レンズが独立に「分配器は登録済みだが scheduler が未準備の時点で呼ぶと
  受入を rc=4 にする」と指摘し、親が `pytest-xdist 3.8.0` の実装を読んで裏づけた
  (`sched` は実行ループに入るまで `None`、controller は collection を行わない)。
  委譲の可否と完了判定を分離する、より小さい形へ差し替えた。

- **段 6 のレビューが、新しい control の過適合を 1 件見つけた。** 注入する stale node が
  1 件だけだと、`if missing:` を `if len(missing) == 1:` にする変異を control 群が
  誰も殺せない。親が実測で確認し (fix 前は生存、fix 後は当該 control が落ちる)、
  注入を 2 件へ変えて閉じた。**production の防壁は 1 行も緩めていない。**

- **レビュー所見の 1 件は親の段取りが生んだ誤報だった。** 詳細は
  {{F:probe-mutation-seen-by-concurrent-reviewer}}。

- **変異 matrix は baseline PASSED / 10 KILLED / SURVIVED 0 / MISMATCH 0 (rc=0)。**
  期待 node は probe 走行の観測から確定させ、完全一致で KILLED と数えた。
  過剰拒否の正例 2 件 (絞り込み判定の無効化、shard guard の無効化) を含む。
  前者は 10 node を落とすので**単一理由ではない**と明記する。
  controller hook 側の 3 変異は diagnostic sensitivity pin として別枠にした。
  実 xdist では worker が同じ入力を拒否するので、これらの kill を
  「受理集合を守った」とは数えない。

- **`DW-M08` の新旧両走で、新テストだけが検出する差分を 2 件示した。**
  変更前 HEAD の使い捨て worktree (baseline PASSED) で、
  `len(missing) == 1` と controller hook の呼び出し無効化はどちらも **SURVIVED (0 node)**、
  `if missing:` の無効化は当時も KILLED (1 node) だった。変更後はそれぞれ
  1 node / 1 node / 3 node で KILLED になる。旧 suite が単に壊れていたのではないことの
  対照として `if missing:` を同じ走行に含めた。同じ走行を 2 回行い結果は一致した。

- **親の手順違反 2 件を記録する。** (1) 変異 probe の復元に `git checkout --` を使い
  実装子の変更ごと消した (F174 の 3 例目、退避 patch から byte 一致で復元、実害ゼロ)。
  (2) 旧側の変異走行で `--out` を home、`--scratch-root` を /work へ置いたため、
  走行完了後の証拠退避が cross-device rename で失敗した (`DW-M07` が明記する制約への違反)。
  走行自体は完走しており ledger は 3 件記録済みだったが、container を撤去し
  `git worktree prune` してから同一 device で再走した。
  背景 job の成果物を home へ置く慣習とこの制約は衝突する。

- 子は 8 本 (plan 1・consult 2・author 1・review 2・fix 1・focus 1)、
  すべて `gpt-5.6-sol` / xhigh / 受理・evidence complete。
  実装子と fix 子はどちらも Pegasus dispatch へ到達できず `rc=16` で 0 件実走だったため、
  テストの実走はすべて親が行った (既知の sandbox 制約)。

## 次の一手差分

### 完了

- [T-1551] stale registry 検査の配線を実効 scheduler によらず発火する形へ直し、
  恒真な control を実 subprocess の control へ置き換えた。変異で恒真でないことを確かめた。
  remaining: none
  base: d37c857fcdfc80d325101f2542c000588c0b461bf94a17bca6f715072be2b8b5

### 新規

- {{T:growth-hold-worker-sensitivity-pin}} **P2・新規**: growth-hold 側の worker 経路 stale 検査に
  感度 control が無い。現実装は静的には検査しているが、`_is_complete_growth_hold_collection` の
  最終行を `return not hasattr(config, "workerinput") and ...` にする変異で
  worker 側の検査だけを殺せ、既存 test は誰も落ちない (段 6 のレビューが具体的な変異まで特定した)。
  effective-serial の同型の穴も残る。flaky 側と同じ形の control を足す。
- {{T:stale-gate-superset-target}} **P3・新規**: suite root に別 target を足した上位集合は
  完全 collection と見なされず、stale 検査が発火しない。collection は狭まらないので
  検査は安全に実行できるが、「引数がちょうど 1 個」を緩めると重複 root の迂回防止契約と
  衝突する。両立する判定 (包含関係で決める形) を設計してから直す。
