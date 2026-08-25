---
schema: izanagi-spool-v1
ledger: decisions
authored: 2026-08-25
wave: dev-wave-t1622-resume-acceptance-boundary
seq: 3
---

## {{D:resume-gate-boundary-diagnosis-not-exit-code}}. 起動 gate と受入 post-claim merge の境界は診断の二分で固定し、専用 exit code を作らない

**決定:** `tools/check_wave_startup.py` の `--mode resume` が local main の behind を検出したときの
診断を「session 開始時」と「session 開始 gate が成功した後の受入前」へ二分し、後者では
`tools/dev_wave_wait.py acceptance` の post-claim merge に委ねること、および束縛実行体
(待ち手・launcher・runner) の bytes を変える前進だけ先に取り込むこと (F524) を名指しする。
**exit code は 0 / 1 の二値を維持し、この状態を表す専用 rc を新設しない。**
同じ境界を `docs/dev-wave/operations.md` の `DW-O20` へ書き、両者が同じことを言うことを
`orchestrator/tests/test_check_wave_startup.py` の逐語検査で固定する。

**理由:**
- checker は呼び出された時点が session 開始か受入直前かを**観測できない**。入力は repository、
  mode、handoff の実在だけであり、その session の gate が既に成功したかという状態を持たない。
  専用 rc が分類できるのは `resume + behind のみ不合格` という**状態**であって、
  誤適用の**時系列**ではない。段 3 の 2 レンズが独立に同じ結論へ到達した。
- 専用 rc は受理集合を広げる affordance を作る。将来の呼び手が `rc == 1` だけを拒否したり、
  新 rc を「受入へ進んでよい」と解釈すれば、正当な session 開始 gate を迂回できる。
  checker 自身に正当な再開と誤適用を区別する信号が無い以上、区別を表す出口を作るべきでない。
  絶対規律 2 に照らし、拒否を増やす方向以外の変更は採らない。
- 診断の二分は受理・拒否集合を 1 bit も変えずに、誤適用した読み手を正しい経路へ送る。
  実測でも `rev-list --count` が返しうる全出力クラスで受理・拒否と rc は変更前後で同一だった。

**却下した選択肢:**
- **`RC_RESUME_BEHIND_ONLY` のような専用 rc を新設する** — 上記の affordance を作る。
  repo 内外の自動 caller は現時点で 0 件だが、「今は消費者がいない」は将来の誤読を防がない。
- **待ち手の生存や lease の実在を根拠に resume gate を拒否する** — 受入は `held` でも待たずに
  進む契約であり、待ち手は成功後も lease を保持しうる。lease の実在は異常の証明にならず、
  受入後の正当な fresh-context 再開を塞ぐ誤検出になる。
- **手順書だけを直す** — 機械が受理集合を持たないため、除外の範囲が読み手ごとにぶれる。
  診断文をテストで固定することで、文言の退行だけは機械検出できる。

## {{D:boundary-e2e-is-composition-not-line-gate}}. 2 つの CLI にまたがる境界は時系列結合の E2E で固定し、単独行の変異で測らない

**決定:** 起動 gate と受入 post-claim merge の境界を検査する
`orchestrator/tests/test_resume_gate_acceptance_boundary.py` は、**正常系の時系列結合テスト**として
位置づける。すなわち wave-ahead な worktree で resume gate が成功した後に main が独立前進し、
単一の待ち手が固定 message で merge commit を作り、behind=0 と clean tree を再確認して
canonical runner を 1 回だけ起動する、という順序を 1 回の決定的な subprocess 走行で固定する。
このテストを enforcement 各行の変異検査として扱わず、個々の防壁は既存の負例テストが担う。

**理由:**
- 実測で示された。待ち手側の 4 変異 (post-claim の behind 分岐・merge・commit・message) は
  この E2E も殺すが、**既存の単体テストが同時に 16〜36 node で殺す**。E2E の単独純増はゼロである。
  一方 containment 検査を無条件成功にする変異では E2E は緑のままで、checker の負例だけが殺した。
  この対照は変異事前登録の時点で期待値として登録し、実測で一致した。
- 理由は構造的である。**境界は単一の production 行に存在しない。** 一方は起動時の checker、
  他方は受入待ち手であり、両者を結ぶ制約はこれまで文書にしか無かった。
  単独行の変異はこの結合を分離できない。
- したがって「変異で殺せない」ことはこの E2E の欠陥ではなく、固定している対象の性質である。
  記録では純増検出力を「2 つの production CLI 間の時系列結合」と書き、
  個々の防壁の検出力を主張しない。

**却下した選択肢:**
- **変異で殺せる形になるまで E2E の scope を広げる** — 単独行で殺せる面は既存テストが既に
  被覆しており、重複を増やすだけで境界そのものは固定されない。
- **E2E を作らず既存テストで足りるとする** — 個々の性質は被覆されているが、
  gate 成功 → main 前進 → 単一待ち手の取り込み → runner 1 回、という順序は
  どのテストも検査していなかった (実測: 両 CLI を同時に参照する test file は 0 件)。
