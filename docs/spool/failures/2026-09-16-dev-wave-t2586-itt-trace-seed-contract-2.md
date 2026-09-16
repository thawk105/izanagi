---
schema: izanagi-spool-v1
ledger: failures
authored: 2026-09-16
wave: dev-wave-t2586-itt-trace-seed-contract
seq: 2
---

## 新規

### {{F:repo-walk-races-with-in-repo-tempdir-fixture}}. repo 全体を走ってから除外する走査が、同じ suite の一時 dir と競走して land を止めた [テスト代表性] [手順漏れ]

- 事象: `orchestrator/tests/test_campaign.py` の
  `test_certified_writer_authorization_caller_inventory_is_closed` が、受入全走 9 回のうち
  **7 回**落ちた。逐語は毎回
  `FileNotFoundError: [Errno 2] No such file or directory: '<repo>/.t316-live-<乱数>'`。
  [T-2586] の成果はこれで 9 回 land できなかった。同 wave 自身の変更に帰属する赤は
  別に 1 件あり、そちらは先に閉じている。残ったのはこの競走だけだった。
- 根本原因: 当該 test は `sorted(repo_root.rglob("*.py"))` で repo 全体を走り、
  **走り終えてから** `.git` / `.claude` / `.codex` / `external` / `__pycache__` / `output` /
  `.venv` を除外していた。除外対象も一度は辿る。同じ受入走の
  `orchestrator/tests/test_t316_sandbox_probe.py` の fixture `s6_bindable_root` が
  `tempfile.TemporaryDirectory(prefix=".t316-live-", dir=_REPO)` で repo 直下に一時 dir を作り、
  test 終了時に消す。走査がその dir を辿っている最中に消えると `rglob` が落ちる。
  **除外を「辿った後の filter」で書くと、辿ること自体の副作用は消せない。**
- 恒久対応: 走査を `os.walk` へ替え、repo 直下の dot-dir を**降下前に**刈る
  (`orchestrator/tests/test_campaign.py`)。消えた entry はその entry だけ飛ばす。
  既存の除外条件と末尾の `assert source_paths` はすべて残した。
  t316 側は直していない — 同 fixture のコメントが repo 内に置く理由 (SandboxProfile が /tmp を
  隠すため mount 可能な祖先が要る) を明記しており、外へ出すと別の前提が壊れる。
- 再発検知: 被覆が恒等であることを実測で固定した。top-level dot-dir 配下に走査対象の `.py` は
  0 件、走査対象は変更前後とも 420 件で追加・削除とも空集合。`.t316-live-*` を列挙後・降下前に
  消す再現を 20 回行い、20 回とも落ちず 420 件を返す。被覆が動けばこの件数が動く。

## 再発

### F386

- **再発: 2026-09-16** — 閉包の上限を「依頼文の編集面ヒント」ではなく
  **「子が返した所見の列挙」**に置いた形で再発した。[T-2586] の親は、投入経路の検査を締めたとき
  赤になる既存 test の集合を、段 2 プランと段 3 の 2 レンズが挙げた 2 件に自分の実測 1 件を
  足して 3 件と裁定した。3 件は正しかったが**全数ではなかった**。4 件目
  (`test_backoff_trace_contract_accepts_only_four_exact_cell_literals`) は、実装子が
  「期待値のほうが誤りだと判断したときは実装を変えず報告して止まれ」という指示に従って
  停止報告を返したことで初めて出た。子 2 体が metadata だけを締める前提で列挙していたため、
  親が裁定で投入経路も締める方向へ変えた時点で、その列挙は閉包として無効になっていた。
  親はそこで閉包を取り直さず、無効になった列挙へ足し算した。
  是正は裁定の正誤表で、`_validate_backoff_trace_contract` と `_artifact_contract_metadata` の
  test file 内**全 20 呼び出し点**を表にして全数を出し、そこから影響 4 件を導いたこと。
  段 6 の敵対レビュー 2 本と焦点再レビューが独立に 5 件目の不在を確認した。
  **裁定で層を変えたら、前段の列挙は閉包でなくなる。** 権威 (呼び出し点の全列挙) から取り直す。

### F376

- **再発: 2026-09-16** — 今度は**検索結果の側**で再発した。F376 の根本原因は
  「切り取られた出力を不在・網羅の根拠にしない」規律を検索結果には適用していたが
  テストの失敗出力には適用していなかった、というものだった。[T-2586] の親はその逆をやった。
  段 1 の pin 閉包検査で `git grep -n "t2187_adaptive_const_probe" | grep -v <自 test> | head -40`
  を実行し、**自分で `head -40` を付けて切った出力**を閉包の全件として扱った。表示された 40 行は
  `acceptance_duration_ledger.json` の node 行が大半を占め、行番号 pin を持つ
  `orchestrator/tests/test_ccbench_spawn_sites.py` は切った側にあった。
  結果、`_DEFERRED_GATE_MEMBERS` が pin する build sink 2 件の行番号が実装の +31 行で
  ずれ、受入全走が決定的な赤 4 件 (cross-product 28 triple 分) を 2 回とも出した。
  是正は `git grep -l` で全件 (185 path) を列挙し直し、行番号を pin しているのが
  この 1 file だけであることを確かめたうえで anchor を再固定したこと。
  **出力を切る `head` は自分で付けても truncation である。** 閉包を数えるときは
  件数を先に出すか `-l` で path だけを全件出す。
