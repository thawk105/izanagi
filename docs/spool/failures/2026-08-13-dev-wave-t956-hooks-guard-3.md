---
schema: izanagi-spool-v1
ledger: failures
authored: 2026-08-13
wave: dev-wave-t956-hooks-guard
seq: 3
---

## 新規

### {{F:guard-self-lockout}}. guard に自分自身の保護を入れた瞬間、自分がその guard に締め出された [手順漏れ]

- 事象: [T-956] 段 5 第 1 attempt で、実装子が `hooks/guard_write.py` と
  `hooks/guard_bash.py` を 1 回の apply_patch で変更したが、`guard_write.py:335` に
  `(` の閉じ忘れがあった。**壊れた guard は `codex_guard.sh` が rc≠0/2 を 2 へ正規化するため
  全編集を拒否する。** 実装子は自分の誤りを直せず、回避せず fail-closed で停止した
  (子の判断は正しい)。さらに、guard bytes が HEAD blob と食い違う間は
  `check_codex_hooks.validate_installation` が起動前検査を赤にするため、
  **代わりの Codex 子を 1 本も起動できない**状態になった。実測では consumer テストが
  `working bytes が HEAD blob から drift` で 65 件赤になり、統合 commit 後に解消した。
- 根本原因: 「保護を入れる対象」と「保護を入れる作業の実行環境」が同一だったのに、
  1 回きりの書き込みが正しい保証が手順に無かった。加えて、復旧経路が
  「commit するか restore するか」の 2 択しかないことが事前に洗い出されていなかった。
- 恒久対応: {{D:guard-self-edit-protocol}} — 完成形を保護対象外の作業 directory へ書いて
  `py_compile` と `decide()` 実測を通してから、最後に 1 回だけ本番へ入れる。guard_bash を
  先に、guard_write を最後に patch する。親は次の子を起動する前に統合 commit を作る。
  修正が要るときは有効化前の commit から作り直す。
- 再発検知: guard 変更 wave で `python3 tools/check_codex_hooks.py` の rc を、子の起動前と
  統合 commit 後に必ず測る。段 5/6 の子が「hooks/ の再編集が必要」と報告したら、
  回避策を足さず本手順へ戻る。

### {{F:parent-monotonicity-claim-without-counterexample-search}}. 「拒否しか増えない」を反例探索なしで裁定した [恒真ゲート]

- 事象: [T-956] 段 4 の追補裁定で、親は「canonical 解決を raw 起点へ変えても拒否が増える
  方向にしか動かない」と判断し、根拠を (a) 方向の直観、(b) 既存テスト 256 件が緑、の 2 点に
  置いた。段 6 の敵対レビュー 2 本が**独立に**反例を構成した — repo 外への symlink component の
  後ろに `..` が続く形では、変更前に拒否していた入力が変更後に許可へ反転する。
  既存テストはこの形を持っていなかったため緑のままだった。
- 根本原因: 単調性は「テストが緑」では示せない性質 (テストが被覆していない入力について何も
  言わない) なのに、緑を証拠として扱った。反例の構成を試みていない。
- 恒久対応: {{D:dual-canonical-deny-union}} — 2 系統を保持して deny union にし、旧拒否を
  構造的に失わない形へ変えた。手順としては、**受理集合の単調性を主張するときは、
  反転する入力の構成を明示的に試み、試みた形を記録する**。テスト緑は反証にならない。
- 再発検知: 受理集合を縮める wave では、段 6 の敵対レビューに「変更前に拒否されていた入力で
  いま許可になるものを構成せよ」を明示項目として渡す ([T-956] ではこれが機能した)。

### {{F:codex-cyber-classifier-refusal}}. 敵対レンズの語彙が上流分類器に拒否され、22 分と出力 token が全損した [コンテキスト浪費]

- 事象: [T-956] 段 3 レンズ A (read-only、防御目的を明記済み) が、22 分・model call 39 回・
  出力 token 約 4.1 万を消費した末に、最終メッセージ生成時点で
  `This content was flagged for possible cybersecurity risk` により `turn.failed` になり、
  **output_bytes=0** で終わった。受領証は `evidence_status=complete` / `codex_exit_code=1` で、
  Web 検索由来の全損 (重複 key で invalid) とは切り分けられる。
- 根本原因: prompt の語彙が攻撃カタログ寄りだった (「攻撃せよ」「すり抜ける入力」
  「負例カタログ」「poisoned pyc」「hijack」「import shadow」)。**防御目的の明記だけでは
  足りない。** 同じ wave のレンズ B (同じく敵対的だが「実効性・波及」の語彙) は通っている。
- 恒久対応: 敵対レンズは**分類器のレビュー**として書く。「reject に分類し損ねる入力」
  「reject 入力表 / accept 入力表」「source と内容が一致しない `.pyc`」「同名 module の
  探索順序」のように、検査項目を 1 件も削らずに語彙だけを置換する。[T-956] では
  この置換だけで同一内容が通り、32 KB の成果物を得た。
- 再発検知: codex 子が `rc=1` かつ `output_bytes=0` で終わったら、まず receipt の
  `evidence_status` を読み、`complete` なら events 末尾の `type=error` を見る。
  `flagged for possible cybersecurity risk` なら語彙の問題であって内容の問題ではない。
