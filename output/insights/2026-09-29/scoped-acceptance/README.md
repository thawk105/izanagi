# 縮小受入 — 知識面だけの wave を「その面を読む test」で受入して land する

- 着手: 2026-09-29 夜 (JST)、wave branch `worktree-dev-wave-scoped-acceptance`、全 9 段。
- 依頼: `raw/md_1.txt` (ユーザー発言の逐語を含む)。段 1 brief は `raw/brief.md`、段 4〜6 の裁定の逐語は `raw/stage4-ruling.md`。
- 決定: 本 wave の decisions fragment `docs/spool/decisions/2026-09-29-dev-wave-scoped-acceptance-1.md` (land の fold で `docs/decisions.md` に採番される)。
- 手順書: `docs/dev-wave/core.md` の `DW-S04`、`docs/pegasus-runbook.md` §7.3「縮小受入 (`--scoped`)」。

## 1. 何を作ったか

| 部品 | 所在 | 役割 |
|---|---|---|
| 分類・選択器 | `tools/scoped_acceptance.py` | tested_main..tested_tip の raw tree 差分を閉じた許可 path と参照規則で分類し、回す test 集合と直接実行の検査 2 本を決める。stdlib だけ、repo 内 module を import しない |
| 縮小 launcher | `tools/scoped_acceptance_launcher.py` | tested main の blob の分類選択器と既存 launcher を使い、直接実行 2 本 → 選んだ test の pytest を走らせ、緑なら `dev-wave-scoped-acceptance-receipt/v1` を出す |
| 待ち手 | `tools/dev_wave_wait.py acceptance --scoped` | 既存の claim・post-claim merge・fingerprint をそのまま使い、launcher だけ縮小版にする |
| land | `tools/dev_wave_land.py` | schema で分岐し、縮小受領証は lock 内で分類と選択を再導出して完全一致を要求。`tools/` の差分があれば分類器と独立に拒否。v5 受領証の field・検査は変えていない |
| runner | `tools/run_tests.py` | 選択された node / file の列を受入と同じ意味 (恒久除外・loadgroup) で走らせる閉じた形を足した |

変えていないもの: v5 受領証の field と検査、`tools/acceptance_launcher.py`、既存の受入全走の経路。テストは 1 件も削っておらず、hold も足していない (D747)。

## 2. 許可差分 (分類) — 閉じた列挙

通常 file (mode 100644、blob) の追加 (A) と内容変更 (M) だけを見る。削除・rename (両側)・mode 変更・type 変更・symlink・gitlink・非 UTF-8 や
`..` などの危険な path・2 MiB 超は、1 件でもあれば全受入。

| 許可 | 条件 |
|---|---|
| `docs/spool/{worklog,decisions,failures}/*.md` | 新規追加 (A) だけ。README.md は除外 |
| `output/insights/**` | 拡張子 md / txt / csv / tsv / json / jsonl |
| `docs/**/*.md` | 下の除外に当たらないもの |

除外 (許可 path の中でも全受入): `docs/dev-wave/**`、`docs/spool/` の上記以外、`docs/{worklog,decisions,failures}.md` (台帳正本)、`docs/archive/**`、
`docs/handoff/**`、`docs/skill-self-improvement.md`、`docs/ai-provenance.md`、basename に preregistration・erratum・freeze を含む文書。

**正しさの門の入力は全受入に倒す (参照規則):** 変更 path ごとの鍵のいずれかを、production code (docs/・output/・external/・Markdown・test・直接実行する
検査 2 本を除く tracked file) の本文が部分文字列として持てば全受入。鍵は次のとおり (最終版、fix2 後)。

- full path。
- basename (汎用名 README.md・index.md と日付を除く)。
- `docs/spool/` 配下の fragment は上の 2 つだけ (入れ物 dir は鍵にしない)。
- `output/insights/` 配下は深さ 3 以上の祖先 path と dir 名 (最後の要素が純粋な日付 YYYY-MM-DD の祖先と汎用名は除く)。
- `docs/<x>/` 配下は深さ 2 以上の祖先 path と dir 名 (汎用名は除く)。

**入れ物 reader の点検済み一覧:** 入れ物そのものの文字列 (`"output/insights"`・`"insights"`・`"docs/spool"`・`"spool"` を引用符 2 種で) を持つ production file は
7 本 (tools/check_docs.py、tools/spool_fold.py、tools/dev_wave_land.py、tools/scoped_acceptance.py、tools/audit_dangling_commits.py、
orchestrator/campaign/layout.py、orchestrator/campaign/p3_b4_wiring_probe.py) を点検済みとして閉じた定数に置いた。一覧外の production file が
入れ物文字列を持ち、変更がその入れ物 (insight / spool) を含むときは全受入。新しい入れ物 reader が足されると、点検されるまで全受入に倒れる。

## 3. 縮小集合 (選択)

- S1 実 repo を読む test 一覧 `_REAL_REPO_NODE_INVENTORY` の全 node (149)。
- S2 固定 file: test_check_docs.py、test_spool_fold.py、test_check_ai_provenance.py、test_real_repo_serialization.py、test_acceptance_schedule_order.py、
  test_official_perf_closure.py、test_p3_exploration_namespace.py、test_p3_b4_wiring_probe.py と、test_campaign.py の certified-writer caller inventory node。
- S3 分類と同じ鍵を部分文字列として持つ test file 全体。
- S4 insight を変えるとき、`"insights"` (引用符 2 種) を持つ test file 全体。
- S5 spool fragment を変えるとき、`docs/spool` を持つ test file 全体。
- 直接実行: `python3 tools/check_docs.py`、`python3 tools/spool_fold.py --dry-run`。どちらかが非 0 なら受領証を出さない。

growth hold (現行の全受入でも skip される 50 件、うち docs_bytes 軸 3 件は test_check_docs.py の実 repo 正例) は縮小受入でも同じく skip される。
直接実行の check_docs は、その 3 件が見る実 repo の finding を毎回検査する。ただし held test 固有の assertion (checker が過剰拒否しない契約など) と同値ではない。

## 4. 受領証と land

- 受領証 `dev-wave-scoped-acceptance-receipt/v1` は v5 と共通の field (wave・holder・tested_main/tip・fingerprint・env・child_rc=0・child-green・scheduler・
  log digest・待ち手/launcher/runner の blob と実行 bytes) に、分類結果・選択結果・直接実行 2 本の argv/rc/log digest・分類選択器の blob と実行 bytes を足す。
- land は schema で分岐し、登録前検査・lock 内再検査・fold 後再検査・forward-main 比較・release authority の全入口で縮小受領証を扱う。
  lock 内で tested_main..tested_tip の分類と選択を land 自身の module で再導出し、受領証と完全一致を要求する。land の module と tested main の
  分類選択器の blob も一致を要求する。
- 取り込んだ main で runner・分類選択器・縮小 launcher・直接実行の検査 2 本・`orchestrator/tests/conftest.py` のいずれかの blob が変わっていれば
  縮小受領証は再利用しない (D987 の拡張)。test file の追加・変更だけでは再受入しない (D662 と同じ割り切り)。

## 5. 実在の land への分類 (DW-O13 の値域の実測)

直近 80 区間 (main の first-parent 上の fold commit の間) のうち、区間の正味差分が docs/ と output/insights/ だけのもの 10 区間に分類器をかけた
(`raw/probe/classify-*.txt`)。

| 分類器の版 | 縮小可 | 主な全受入の理由 |
|---|---|---|
| 段 5 の実装 | 0 / 10 | 入れ物 dir (`docs/spool/worklog` 等) と basename `README.md` と汎用 dir 名が鍵になり、ほぼ全 path が「production 参照」になった |
| fix1 (鍵 v2.1) | 5 / 10 | 台帳正本・archive の直接編集 (spool 導入前の形)、phase3.md を読む role adapter 設定、許可外の `.log` |
| fix2 (最終) | 4 / 10 | 上に加え、当時の tree にあった一覧外の入れ物 reader `tools/insights_date_layout.py` で 1 区間が全受入に倒れた (設計どおりの fail-closed) |

最終版で縮小可の区間の選択は 142〜149 node と 14〜19 file だった。
参考: 区間ごとの非 merge commit の変更 file で数えると 80 区間中 31 区間が docs と insight だけだった (`raw/probe/wave-surface.txt`)。
区間の中に複数 wave が入ることがあり、どちらの数え方も wave 単位の正確な割合ではない。

## 6. 実物確認 (独立 clone、共有 repo の main には触れていない)

独立 clone (`git clone --local`、main = 本 wave の 1e97b58e0) の中で確かめた。

- **(a) docs だけの tip が縮小受入で land できる。** tip f4a8807e4 = decisions fragment 1 本 + 新しい insight README。分類は適格 (選択 149 node + 20 file)。
  `acceptance --scoped` は child-green で受領証を出し (3,889 passed / 45 skipped、直接実行 2 本とも rc=0)、`tools/dev_wave_land.py` が
  status=landed で main を f4a8807e4 へ進め fold した (fold commit 1e8bb1981)。受領証は `raw/real-check/accept-a2-scoped.receipt.json`。
- **(b) 実装面が混ざれば拒否される。** f4a8807e4 に `tools/sa_probe_impl.py` を 1 本足した tip 448e0f08e は分類で不適格 (`path:tools/sa_probe_impl.py`)。
  (a) の縮小受領証でこの tip を land しようとすると rc=23 `acceptance-receipt-rejected`、tested tip を f4a8807e4 に据えて着地 tip だけ 448e0f08e にすると
  rc=23 (既存規則「tested tip から着地 tip までは main の取り込み merge だけ」)。どちらも main は動かなかった。
- **(c) 許可 path でも検査を壊せば赤になる。** (a) の land 後の main 1e8bb1981 に、frontmatter に未知 key を持つ decisions fragment を 1 本足した tip 3b700955a は、
  path だけを見る分類では適格 (`raw/real-check/plan-c.json`、選択 15 file)。`acceptance --scoped` は直接実行の検査 0 (check_docs) が rc=1 で落ち
  (`docs/spool/decisions/2026-09-30-dev-wave-sa-probe-c-1.md:7: spool frontmatter-line: ... frontmatter は key: value 限定`)、
  pytest に進まず受領証を出さなかった (待ち手 rc=70、投入から 6 分 34 秒)。依頼文の例「pin された節の改変」は許可集合の外 (docs/dev-wave は全受入) なので、
  許可 path の中で実際に検査が拾う違反に置き換えた (段 2 plan と段 3 の指摘)。

## 7. 効果 (同時刻の対照)

同じ tip f4a8807e4 に、縮小受入 (作業木 wa) と受入全走 (作業木 wb、同じ tip の別 branch) を 2026-09-30 01:26:08 JST に同時投入した
(投入時の login 負荷 26.4 / 14.7 / 11.0)。

| | 縮小受入 | 受入全走 |
|---|---|---|
| 結果 | child-green、受領証あり | 3 failed / 28,254 passed / 74 skipped、受領証なし |
| 走った test | 3,889 passed / 45 skipped (1 job、shard 1) | 3 shard、計 28,254 passed / 3 failed / 74 skipped |
| pytest 所要 | 195.90 s (job Elapse 202 s) | shard 0: 281.76 s (Elapse 300 s)、shard 1: 319.52 s (347 s)、shard 2: 225.75 s (246 s) |
| 直接実行 2 本 | check_docs 66.1 s + spool_fold 24.9 s (login、別時刻に単独で測定) | なし |
| 投入から終了まで (wall) | 14 分 14 秒 | 11 分 22 秒 |

- **wall は縮小受入のほうが長かった。** 受入全走は計算ノード複数へ shard 分割して並列に走るが、縮小受入は 1 job で、しかも直接実行 2 本 (約 91 秒) を
  login で先に直列に走らせる。queue 待ちも残る。login の実効メモリ天井 (約 15.0 GB) を同じ user の他 session が使い切っている時間帯が多く
  (2026-09-29 23 時台の実測で使用 17.0 GB)、縮小集合も login では走らず計算ノードへ回る。
- **効いたのは「無関係な赤で止まらないこと」だった。** 受入全走は 2 回とも本 wave と無関係な赤 3 件で受領証を出さなかった
  (1 回目: test_codex_worker_launch の SIGTERM 系・test_dev_wave_cleanup・本 wave の新 test の allowlist 漏れ。2 回目: test_dev_wave_cleanup の 3 node)。
  縮小受入は同じ tip で緑になり、そのまま land できた。2026-09-29 の VHash の docs だけの land が約 5 時間かかった内訳 (依頼文) は、queue 待ちと
  非帰属の赤による再投入が大半だった。縮小受入が縮めるのはこの再投入の側で、queue 待ちは縮めない。
- 1 回の同時刻対照で、混雑は時刻で大きく変わる。wall の大小関係を一般化しない。

## 8. 変異 (事前登録どおり)

`raw/mutation/`。段 4 で MS1〜MS9、段 6 の fix 前に MF1〜MF6 を登録した (定義は `raw/stage4-ruling.md` と `raw/mutation/mutation-spec-final.json`)。
独立 clone (D1009) の固定 commit で、束ね経路の dispatch として走らせた。

- 初回 probe (88fa8f1f1、全件 SURVIVED 期待で観測 node を収集): baseline 64 passed。15 変異中 14 が赤、**MS8 (launcher の直接実行 rc 検査を外す) が生存**。
  既存 test は launcher 全体を合成環境で走らせ、MS8 下でも後段が別理由で失敗して「受領証なし」のまま緑になっていた (他層の mask)。
  `_gate` を直接呼ぶ単一理由の test を fix3 で足した (DW-M02 の再照準)。
- final (6ba3f5c72): baseline 緑 (6.8 s)、**15 / 15 が事前登録の期待 node と完全一致で KILLED**、MISMATCH 0。

## 9. 段 6 で見つかって直したもの

- 引用文字列の中だけで照合していたため、コメント中のアポストロフィ (`# don't`) で引用の対応がずれ、後続の path 文字列を見逃した → file 全体の部分文字列照合。
- 鍵が粗く、実在の知識面 land が 0 / 10 しか縮小可にならなかった → 鍵 v2.1。
- insight の「日付_slug」形の深さ 3 dir (`output/insights/2026-08-27_t1769-b4-wiring-probe`) を部品連結で読む実在の reader (p3_b4_wiring_probe.py) を
  見逃していた → 深さ 3 からの鍵と入れ物 reader の点検済み一覧。
- 既存関数 `_verify_forward_main_runner_blob` に引数を足し、それを差し替える既存 test 4 件を壊した → signature を戻し縮小用を別関数に。
- 新 test file 2 本が plain runner の偽緑 meta-test (自走 harness か pytest 専用 allowlist が必須) に掛かった → allowlist に追加。親の焦点走がこの meta-test を
  含めていなかった (DW-O26 の取りこぼし) ため、独立 clone の受入全走で初めて見つかった。

## 10. 限界

- **入れ物 dir を列挙する reader は鍵で拾えない。** 下位の入れ物 path (`"docs/spool/worklog"`)、分割した文字列 (`"docs" / "spool"`)、純粋な日付 dir を列挙する
  reader は、分類では全受入に倒れない。2026-09-30 時点の tree では、該当するのは `tools/dev_waves/git_state.py` (wave の未 fold fragment を列挙する開発道具)
  だけで、その test は S5 で選ばれる。日付 dir を列挙する production reader は無かった。
- 動的に組み立てる path、設定 file 経由、subprocess の中の reader は文字列照合で追えない。点検済み一覧と過大除外 (部分文字列) で補うが、完全ではない。
- 受領証の rc・log digest は、v5 と同じく launcher が書いた値を信じる (受領証 file を書き換えられる主体に対する実行証明ではない)。
  分類と選択は land が固定 SHA から再導出するので受領証を信じない。
- 取り込んだ main で test file が増えても縮小受領証は再利用される (D662 と同じ割り切り)。
- 縮小受入の wall は受入全走より短くなるとは限らない (§7)。shard 分割しないこと、直接実行 2 本を直列に走らせることは、短縮の余地として残る (本 wave では変えていない)。
