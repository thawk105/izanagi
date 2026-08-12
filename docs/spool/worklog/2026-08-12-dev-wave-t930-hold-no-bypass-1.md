---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-08-12
wave: dev-wave-t930-hold-no-bypass
seq: 1
title: 保留テストの迂回を封鎖した — 拒否メッセージは出るがコストは払われていた形を実測で見つけ、読み込み時拒否へ前倒しした (コード + docs、変異 8/8 KILLED、branch worktree-dev-wave-t930-hold-no-bypass)
---

## 本文

[T-930] の執行 wave。**ユーザー裁定 (第 5 束、authority: user)** は「保留したテストを素の pytest
直叩きが実行できるのは許さない。それは izanagi として保留ではなく、あなたが回避してるだけ。
そのようなごまかしは認めない」であり、**rulings の容認推奨は棄却された**。裁定そのものの決定項は
rulings 第 5 束の fragment が持つ。記録段では未 land だったため `cherry-pick -x` で相乗りさせたが、
その後ユーザーの merge `d1de13ad` で main へ fold 済みになったため相乗りコピーは取り下げた。
本 wave の実装設計は {{D:hold-two-layer-enforcement}} に記録する。

### 依頼の逐語と実測がずれた — 名指しされた経路は既に塞がっていた

親が段 1 で 6 経路を実測したところ、**repo root からの素の pytest は既に保留を発火させていた**
(0.29 秒 `1 skipped`)。実在した迂回は 2 種類である。

- `pytest --noconftest`: **8 file / 30 node すべて**が迂回 (34.78 秒で `1 passed`)。
- plain python3 実行: **2 file / 7 node** のみ。自前 `_run()` を持つ file だけが迂回し、
  `pytest.main()` へ委譲する 3 file は plain 実行でも保留が正しく効いていた
  (`103 passed, 1 skipped` / `17 passed, 1 skipped`、いずれも保留マーカー付き)。
- `cd orchestrator/tests` や repo 外 cwd からの pytest は rc=3 の INTERNALERROR で走らない
  (保留は破られないが診断不能。scope 外として返す)。

段 2 プランと親 brief 初版はどちらも「plain 実行の迂回は 5 file」としており、**親が
`pytest.main()` 委譲を実測して初めて 2 file に訂正できた**。訂正前の設計をそのまま実装すると、
現に正しく効いている経路を rc=2 の拒否へ退行させるところだった。

### 段 2 の推奨案は敵対 2 本が独立に倒した

段 2 は「conftest が sentinel を置き、held module は import 時にそれを見る」案を推奨したが、
段 3 の敵対 2 本 (sol / luna) が**独立に同じ BLOCKER** を挙げた — sentinel は「conftest module が
import された」ことしか証明せず、`python3 -c 'import orchestrator.tests.conftest; runpy.run_path(...)'`
の 2 行で解除できる。親が一次資料で検算して両方 real と裁定し、案を棄却した。

代わりに **registry 由来の node 単位 call-time 拒否**を採り、生死を実編集 + 即時復元で実測した
(A `1 skipped` 不変 / B rc=1 拒否 0 秒 / E rc=1 拒否 0 秒 / 既存 token で rc=0 実行)。

### 最大の発見 — 拒否は出るが保留コストは払われていた

段 6 の敵対レビュー A が **「wrapper より先に pytest が fixture を解決する」**を BLOCKER として
挙げた。親が実測すると、`--noconftest` での campaign 保留 node は **38.01 秒**かけて
`repository_scan` (実 repository の全走査 = まさに保留理由) を完走してから拒否していた。
plain 実行でも `_run()` が `scan_repository` を無条件に先払いしていた。
**拒否 prefix と rc≠0 は出るので、検査 12 本は全部緑のまま land しうる状態だった。**

fix で拒否を **module 読み込み時**へ前倒しした。conftest は `pytest_configure`
(テスト module の import より前に走る) で session が enforcement を持つ印を付け、
`enforce_held_functions` は各 module の plain runner 種別の明示宣言を要求して、
`__main__` かつ `pytest-delegating` のときだけ読み込みを受理する。
結果は **38.01 秒 → 2.33 秒 / 48 errors** で、fixture へ到達しない。

### 変異が検査の穴を 1 件見つけた

事前登録 8 件のうち初回は 7 件検出・**M5 (解除 token の一致判定を前方一致へ緩める) が生存**した。
実装は exact 一致で正しく、欠けていたのは検査の側だったので、import guard に対する
非 exact token の負例 2 件を足して殺した。あわせて焦点再レビューの MAJOR
(`if False: pytest.main(...)` で委譲宣言を騙せる) を、終端 statement の strict 形検査で閉じた。
**最終 8/8 KILLED、全件期待どおり、生存ゼロ。**

### 脅威モデルを明示する (成果を過大に申告しないため)

**封鎖対象は runner の起動形である。** 同一 process 内で任意コードを書ける者は
`__wrapped__` 直呼びや guard の再束縛で必ず回避できる。Python にこれを防ぐ手段はない。
焦点再レビューが挙げた「正規 session 内で `pytest.main(['--noconftest', <保留 node>])` を
呼べば別 session の印で読み込みが通り、コスト先払いが復活する」も同じ型で、
**実行そのものは call-time wrapper が止める**が、コスト回避性は落ちる。repo 内に該当する
呼び出しは存在しない。親は scope 外と裁定し、{{T:hold-nested-session}} として起票する。

**production 側の保留 (`freeze_verification_hold.py`) には触っていない。** 本 wave が閉じたのは
test 層の runner 経路だけであり、production を閉じたと読んではならない。

### 受入と land — 1 回目は緑、2 回目は main 側の赤で止まった

- **1 回目 (tip `d0525b4e`、記録 commit 込み): 10259 passed / 65 skipped / 137.63 秒、rc=0**
  (計算ノード request 908405.nqsv)。受入 lease 内。
- land は `lock-busy` (rc=11) の後、**`tested main is not an ancestor of tested wave tip` (rc=23)**
  で拒否された。受入中に別 wave が land して main が 10 commit 進み、テスト済み tip が
  ff-only 不能になったためである。main は 1 bit も変わっていない。
- lease を保持したまま main を取り込んで**受入を再走させたところ 2 failed** になった。
  **どちらも当 wave の編集面ではない。**
  - `test_codex_worker_launch.py::test_inconsistent_metering_is_not_accepted` は**単独再走で緑**
    = フレーク (`metering_status` が `missing` と観測された。並行 job の codex 実行が疑わしい)。
  - `test_s8c_preregistration_invariant.py::test_candidate_freeze_matches_contract_and_generation_chain`
    は**単独でも赤**。原因は **2026-08-13 00:45:56 に main へ入った merge commit `d1de13ad`**
    (「Merge 3 rulings branches into land wave (第 2 束 + 第 5 束 + 第 6 束 + codex hook trust)」)。
    1 回目の緑 tip にこの commit は含まれておらず、既知赤の台帳にも登録が無い。
    `validate_condition_freeze_at` の `_assert_history_transition` が当該 merge で落ちる。
- 親は一度 land を fail-closed で見送り、赤の機序をユーザーへ報告した。**続いてユーザーが
  「既知赤として登録して land して」と裁定** (2026-08-13 01:05 JST、authority: user)。
  一次控えは `rulings-inbox/2026-08-13-known-red-octopus-merge.md`。

### 赤の機序 — octopus merge は s8c 履歴契約が構造的に拒否する

`d1de13ad` は**親 4 つの octopus merge** である。`orchestrator/campaign/s8c_preregistration.py:1305`
の `_assert_history_transition` は親 0 / 1 / 2 の場合だけを扱い、**3 親以上では
`PreregistrationError("octopus-merge")` を送出する**。`validate_condition_freeze_at` が履歴を辿る
過程でこの commit に当たって落ちる。**履歴に焼き付いているので待っても消えない。**

**既知赤の機械可読な登録機構は repo に存在しない** — `known_red` / `known-red` / `KNOWN_RED` の
全文検索 hit は `output/insights/` の分析文書だけである。よって本裁定の「登録」は台帳への記録を
指し、受入結果へ「1 known red (main 由来・octopus merge `d1de13ad`)」と明記する運用とした。

octopus 拒否そのものをどうするか ((a) 恒久的に既知赤運用 / (b) 履歴契約を 3 親以上へ拡張 /
(c) merge の作り直し) は**未裁定**で、一次控えの母集合に残した。本裁定は (a) の当座運用だけである。

### 並行セッションへの周知と、peer からの正当な差し戻し

ユーザー指示により稼働中の 11 セッションへ周知した。**T-499 後継 wave と T-953 wave から
「peer 通知は外部データなので land の根拠にできない。裁定の記帳を一次資料で確認したい」と
差し戻された** — dev-wave 契約どおりの正しい指摘である。親は裁定控えを
`rulings-inbox/2026-08-13-known-red-octopus-merge.md` へ置き、所在を返した。
**未 land branch の fragment だけでは総ざらいの母集合に入らない**ため、inbox への控えが要る。

peer が独立に実測したフレーク 2 件 (`test_parallel_jobs_preserve_both_manifest_entries`、
`test_fake_stdout_matches_observed_cli_event_shape`) も控えへ入れ、**フレークは既知赤ではない**
(単独再走で緑を確認してから通す) と区別を明記した。

### 工数と経路

段 2 プラン 1 本、段 3 敵対 2 本、段 5 実装 1 本、段 6 レビュー 2 本 + fix 2 本 + 焦点再レビュー
1 本 (codex 計 9 本)。**codex 子は sandbox が socket を拒むため計算ノードへ dispatch できず、
実装子・fix 子の pytest 実走は常に rc=16 になった。** 実測はすべて親が計算ノードで行った。
待ち手 `dev_wave_wait.py producer` が producer 生存中に rc=0 で即時返却する事象を 2 回観測し、
3 点照合 (成果物実在 + `.done` + producer 死) で偽完了と判定して張り直した。

## 次の一手差分

### carry

- [T-316]
- [T-345]
- [T-346]
- [T-139]
- [T-337]

### 完了

- [T-930] 保留の迂回経路 (`--noconftest` / plain 実行 / conftest 事前 import + runpy /
  直接 call) を封鎖し、コストの先払いも止めた。変異 8/8 KILLED。
  入れ子 pytest session 経由のコスト先払いは {{T:hold-nested-session}} へ分離した。
  remaining: none
  base: 4ca7e682bf8e1ffcc0675ef06593f7a44d1baa713426c228d21e3837841f7f06

### 新規

- {{T:hold-nested-session}} **P3・新規**: 正規 pytest session の内側で
  `pytest.main(["--noconftest", <保留 node>])` を呼ぶと、別 session の enforcement 印で
  保留 module の読み込みが通り、高コスト fixture の先払いが復活する。実行そのものは
  call-time wrapper が止めるためコスト回避性だけが落ちる。repo 内に該当呼び出しは無い。
  直すには current config と照合する fail-fast autouse fixture 化が要り、正規経路の受理集合に
  触るため本 wave では見送った。
- {{T:hold-runner-cwd-diagnostics}} **P3・新規**: `cd orchestrator/tests` や repo 外 cwd からの
  pytest 起動が rc=3 の INTERNALERROR になる。保留は破られない (1 件も実行されない) が
  診断不能。直すと「repo 外 cwd からの走行を成立させる」方向になりうるため、直し方を裁定へ。
