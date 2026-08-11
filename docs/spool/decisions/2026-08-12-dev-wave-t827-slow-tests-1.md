---
schema: izanagi-spool-v1
ledger: decisions
authored: 2026-08-12
wave: dev-wave-t827-slow-tests
seq: 1
---

## {{D:no-history-proportional-test-cost}}. テスト経路に repo 履歴へ比例するコストを入れない

**決定 (ユーザー恒久ルール、2026-08-11):** 目的は
**「開発を進めれば進めるほどテスト時間が増えていって開発できなくなる状況を避ける」**こと。
次の 3 つを規律とする。

1. テスト時間が **1.1 倍 (+10%)** になり、**CPU を 100% 使い倒し続けていない**なら **land しない**。
   並列にできるものは並列にし、仕事量を減らして戻す。遊んでいる CPU がある状態での遅延は受け入れない。
2. **CPU 飽和状態で 1.1 倍**なら、必ず裁定でユーザーへ知らせ改善案を検討する。黙って受け入れない。
3. **repo の履歴 (commit 数・ファイル数・オブジェクト数) に比例して伸びるコストを、テスト経路に
   入れてはならない。** これは「開発するほど遅くなる」を構造的に保証するため、単発の +10% より悪い。
   新しい検査を足す wave は、そのコストが **O(1) / O(変更量) / O(履歴)** のどれかを段 1 brief で宣言する。
   O(履歴) なら設計をやり直す。

**理由:**
- 本 wave の実測。T-080 移行 receipt の履歴検査は発行後の descendant 数に比例し、descendant は
  2026-07-23 の発行から 2026-08-12 までに **2255 commit**、日に約 120 増えていた。
  受入全走はこの間に 207 秒 (D104 実測、2026-07-31) → 558.18 秒 (2026-08-11 記録) → 約 568 秒
  (2026-08-12 実測) と伸び続けており、放置すれば約 2 週間で `dispatch_compute` の walltime 上限に
  到達して 1 走が全損する見込みだった。
- 受入全走は lease 直列窓を占有するため、伸びると全 wave の待ち行列が伸びる。
- 「遅い」の大半は計算資源不足ではない。本 wave の基線では **48 コア中 平均 4.4 コア (9%)** しか
  使われておらず、subprocess と待ちが律速だった。

**判定手順:** wave の段 6 / 段 7 で受入全走を測るとき、wall だけでなく **CPU 飽和度** を併記する。
1.1 倍を超えたら (a) 非飽和なら差し戻して並列化・削減、(b) 飽和なら裁定パッケージで改善案を出す。
性能の一次証拠に duration を使わない (D104 決定 4) は不変で、判定は wall と飽和度で行う。

**却下した選択肢:**
- 上限を上げて凌ぐ — 増加の傾きを変えないため、期限が延びるだけである (D104 決定 2 と同型)。
- 遅いテストを既定から外すことによる一律解決 — 検出力を失う。外すのは他に手が無い場合に限り、
  外した範囲を worklog へ列挙する。

## {{D:keep-gains-below-target}}. 数値目標に届かないことを理由に実測された改善を捨てない

**決定 (ユーザー恒久ルール、2026-08-11):** 受入全走 5 分などの数値目標は**達成目標であって
合否判定ではない**。わずかに届かないことを理由に、実測で確認された改善を破棄・差し戻ししない。

- 報告を「達成 / 未達」の二値にしない。**「何から何になったか / 残っている律速は何か /
  次に何を削れば届くか」**の形で書く。
- 目標未達でも、改善が本物 (実測済み・検出力の喪失なし) なら land する。
- 設計択一を閾値の跨ぎで決めない。**実際の交換レート** (失う検出力 対 得る時間) で判断し、
  割れるならユーザーへ諮る。
- **逆に「閾値を満たすために検査を弱める」も禁止** (規律 2)。閾値は緩和の口実にもしない。

**理由:** 本 wave で、静的見積りが「300 秒到達は結論できない (322〜355 秒の経路が残る)」と出た時点で、
親が成果の扱いを未達 = 失敗の枠で語りかけていた。実際には receipt 解決の git 起動 4500 本 → 2 本という
確定した改善があり、閾値未達を理由に捨てるのは本末転倒である。

**却下した選択肢:**
- 閾値を下げて「達成」と書く — 数字の意味が失われる。
- 未達なら land しない — 改善が永久に入らず、次の wave が同じ律速を再発見する。

## {{D:t080-history-scan-batched}}. T-080 receipt の履歴検査は per-commit 起動をやめ batch 呼び出しで行う

**決定:** `inspect_receipt_history` の descendant 走査を、commit ごとの git subprocess から
**範囲を 1 回で舐める batch 呼び出し**へ置換する。**受理集合は 1 件も変えない。**

- 親 tree entry の取得: descendant ごとの `ls-tree` → `cat-file --batch` **1 本**
- 別 path への exact copy 検出 (S3): descendant ごとの `diff-tree` → `diff-tree --stdin` **1 本**
- 保持する意味論: mode/kind/OID の三つ組比較、M/D/R/C/T の検出、
  `--find-copies-harder` を使わない destination OID 照合
- fail-closed: batch 出力の件数不一致・形式異常・git 異常終了は `receipt.git_error` で拒否する

**理由:**
- 発行後の descendant は 2255 commit で、1 解決あたり git subprocess 約 4500 本・182 秒を要し、
  受入 1 走で 2 回発生していた。同じコードが T-080 E2E fixture 構築 (1 回 213.40 秒) の
  約 9 割も占めていた。
- 同型の先例が repo 内にある。`s8b_ratified_freeze._blob_oid_by_commit` は
  「∀C: entry(C,path) ∈ {absent, expected_oid}」という**同じ形の不変条件**を
  `cat-file --batch-check` **1 本**で判定し、docstring に「per-commit 起動なし」と明記している。
  したがって per-commit 起動はこの検査に必然のコストではなく、実装が劣っていただけである。

**実装上の落とし穴 (git 実測で確定):**
- `diff-tree --stdin` は**空 diff の commit に marker を出さず**、merge では**差分のある親ごとに
  同一 marker を複数回出す**。入力 commit と 1 対 1 ではない。`--always` と commit グループ解析で扱う。
- `-z` は pathname の **quoting を無効化して raw bytes を出す**。path を UTF-8 strict decode すると、
  receipt と無関係な非 UTF-8 filename が repo に 1 つあるだけで正当な receipt を過剰拒否する。
  固定 target のみ bytes 化し、出力 path は decode せず bytes 比較する。

**却下した選択肢:**
- 履歴走査そのものの削除 / 保留 (runtime switch) — 検討の末に不採用。保留は成果物へ「保留中」の印を
  通す配管が 6 層 (GateDecision / campaign-start WAL / holdout adapter / report parser /
  certificate・journal / artifact loader) に及び、現行はいずれも「有効でなければ null」のため
  保留を null で表すと撤去と区別できない。安くすれば同じ高速化が検出力の喪失ゼロで得られる。
- 走査対象を凍結 bytes (F_p) へ固定 — **恒真ゲートになる。** この走査の目的は
  「凍結後に D291 を覆す決定が出ていないか」の検出であり、対象を凍結時点へ固定すると
  以後追加された decision を構造的に一切見られず常に `none_found` を返す。
  payload の trust root (過去へ固定) と supersession の見張り (現在を見る) は目的が逆向きである。

## {{D:optin-needs-dispatch-env-allowlist}}. 重いテストの opt-in は env allowlist への登録まで含めて 1 つの機構とする

**決定:** テストを環境変数で opt-in にする場合、**`tools/pegasus/dispatch_compute.py` の
task 別 env allowlist へ当該変数を追加するところまでを 1 つの変更単位**とする。
allowlist は exact 集合で pin するテストを併せて置き、誤削除・誤追加の双方が落ちるようにする。

**理由:** 本 wave の実測。opt-in の既定側 (skip) は正しく動いたが、環境変数を立てても計算ノードでは
skip されたままだった。`dispatch_compute` の `request_env` が allowlist 射影であり、
未登録の変数は落とされるためである。これを直さないと、外したテストは
**「既定で走らず、解除しても走らない」= 永久に未検証で腐る**状態になる。
テストを既定 suite から外す設計は、**外した先に到達できることを実測で示して初めて成立する**。

**却下した選択肢:**
- CLI flag による opt-in — `run_tests.py` に flag を足すと `_is_acceptance_run` が False になり、
  受入形の事前検査が黙って発火しなくなる。
- allowlist を「全通し」に変える — 親だけが所有する台帳状態が計算ノードへ漏れる。
