# 段 1 brief — [T-153(e)] + [T-154(2)(3)]

- scope: `docs/ai-provenance.md` を 9,000 bytes 上限として `SELF_LIMITS` に登録する。
- scope: commit message 内の全 `Co-Authored-By` 行が Git の最終 trailer block で認識されることを
  `check_ai_provenance` で検査し、T-153(e) / T-154(3) を同一変更として閉じる。
- 確定済み裁定: T-154(2) は 8,000〜9,000 bytes、現物 8,817 bytes のため 9,000 を選ぶ。
- 確定済み裁定: T-154(3) は採用済み。受理集合変更なので D96 に従い新規 D と境界テストを
  同じ commit に含める。
- 不変条件: `AI-Agent` の既存形式・scope・Codex author 検査を弱めず、既存履歴へ遡及しない。
- 不変条件: Git の trailer 解釈を再実装せず、raw CAB 行数と `interpret-trailers --parse` が
  認識した CAB 件数の一致で配置だけを検査する。
- 既存被覆: AI-Agent が Git trailer として消える分断は既存検査が検出する。
- 純増 vector: 本文側の CAB と、最終段落の有効な AI-Agent が分断される現行見逃しを赤にする。
- 純増 vector: contiguous な CAB、CAB 無し、複数 CAB の正常形は緑のまま固定する。
- (P1) raw CAB は case-insensitive、行頭空白と colon 前空白を許して数え、Git が trailer と
  認識しない装飾形も拒否する。親の provisional 裁定であり攻撃対象。
- (P2) byte 上限は `SELF_LIMITS` に置き、既存の全 budget 検査・登録集合へ自動合流させる。
  親の provisional 裁定であり攻撃対象。
- 成果物影響: 未実装なら F25 型の CAB 分断 message と 9,000 bytes 超の provenance 規約を
  開発 gate が受理し、commit provenance の機械受理集合と予算台帳が裁定より広いまま残る。
- 成果物: checker、境界テスト、limit 回帰、policy 文言、新規 decision、worklog、逐語レビュー。
- 分割: read-only plan 1、敵対相談 2、Codex author 実装 1、敵対レビュー 2、必要時 fix author 1。
- 受入: 本 worktree / 共有ログインノードで焦点 pytest、関連 runner、全受入、check_docs、
  check_codex_agents、commit 前後 provenance を実行し、wall time は性能値に使わない。
- freeze/proof chain: 実験 freeze と producer bytes は変更しないため DW-O09/O10 は不成立。
- dev-wave 改善候補: 現時点でなし。
