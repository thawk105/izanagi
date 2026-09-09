単独段 dispatch: stage=focus; sandbox=read-only; parent=/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2500-backoff-tail-prereg

必読事項の射影: 以下はすべて絶対パスである。**読めなければ即停止**し、読めなかったパスを出力に書け。

- **検査対象 (fix 後の本体)**: `/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2500-backoff-tail-prereg/docs/b10-backoff-static-tail-preregistration.md`
- **検査対象 (地図)**: `/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2500-backoff-tail-prereg/docs/README.md`
- 前回の焦点レビューの所見: `/home/SFC/tanab/.claude/jobs/8a4f2a40/tmp/t2500/focus.md`
- 段 6 レビュー A / B: `/home/SFC/tanab/.claude/jobs/8a4f2a40/tmp/t2500/review-a2.md` と
  `/home/SFC/tanab/.claude/jobs/8a4f2a40/tmp/t2500/review-b2.md`
- 実装の現物: `/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2500-backoff-tail-prereg/orchestrator/campaign/backoff_extended_sweep.py`

探索走の成果物は `/work/1/SFC/tanab/b10-backoff-grid-t2418-explore/` 以下にある
(`jq` / `cat` / `grep` で読め。`python3 -c` は guard に拒否されることがある)。
WAL は各 campaign の `runs/wal.jsonl`。

## 依頼 — 一意性と全域性の最終監査 (3 巡目、最後)

親は前回の焦点レビューが出した 6 件の real must-fix を直した。直したのは次である。

1. ゼロ abort の規則を分類表の**外**から**中**へ移し、単一の表の先頭 2 規則にした
   (両端全ゼロ → `saturated`、正値から全ゼロ → `declining`、どちらも対数を取らない)。
   分散なしの規則はその後に置き、「1・2 に当たらず」を条件に加えた。
2. 分散なしの区間では `qL` / `qU` / `U` / `L` / `U_flat` をすべて `null` にすると定めた。
3. workload 状態の 2 番目と 3 番目に「`indeterminate` が 0 件」を明示的に入れ、
   評価順に依存しない排他にした。
4. `j = 1` の飽和位置を「1250 以下・左側打切り・下端なし」に一本化し、
   `1250` という点として報告することを禁じた。両側から挟める最左は 1768 と書き分けた。
5. `analysis_input_contract` の各 field へ `wal_stage` と `payload_key` を付けた。
6. 投入前条件を 3 件から 5 件へ増やした (正しさ記録 5 本の発行確認と、mode 座標の記録を追加)。

**あなたの仕事は、この文書が「どんな観測入力に対しても唯一の結論を返すか」を破ることである。**

### 探すもの

- **全域性。** 分類・workload 状態・集約 verdict・失敗条件のどれかが**当てはまらない**入力を作れるか。
  作れたら、その入力を具体的な数値で書け。
- **一意性。** 2 つ以上の分類・状態・verdict が同時に成立する入力を作れるか。
  「上から順に評価する」で救っている箇所と、条件自体が排他な箇所を区別して指摘せよ。
- **散文と spec の食い違い。** §0〜§4・§6〜§9 の散文と §5 の JSON が、規則・値・順序のどこかで
  食い違っていないか。1 件ずつ、どちらが正しいかの判断つきで挙げよ。
- **到達不能。** ある結末 (とくに `saturated` と `not-observed-in-any-workload`) が、
  失敗条件や前提条件と組み合わさって事実上到達不能になっていないか。
- **正常な走行を殺す条項。** 探索走の実測値をそのまま本走に当てはめたとき、
  失敗条件 18 項のどれかが発火しないか。発火するなら、それは正しい発火か過剰か。
- **field の出所。** `wal_stage` と `payload_key` に書かれた値が、探索走の WAL の現物と一致するか。
  一致しないものがあれば、現物の値を示せ。
- **新しく持ち込んだ矛盾。** 上の 1〜6 の修正自体が別の箇所と衝突していないか。

### 制約

- 所見は **real / refuted を自分で判定**し、根拠を path と節番号で示せ。
- 成果物影響を 1 行で書けない所見は must-fix にせず nit と明記せよ。
- 本 wave は docs-only である。コード・test・gate の新設を要求しない。
- **所見が無ければ「無し」と書け。** その場合は、上の 7 つの観点それぞれについて
  「何を試して破れなかったか」を具体的に書け。**破ろうとした痕跡のない「問題なし」は受け取らない。**
- sandbox は read-only である。**pytest 緑を要求しない。静的検査でよい。**
- 予算が尽きそうなら途中結論を下記の形式で書いて終われ。無出力が最悪である。
- 出力に結合文字 U+0300〜U+036F を使うな。

## 出力形式

## 前回 6 件の対応
(1〜6 それぞれ closed / partial / regressed → 根拠の節と逐語)

## 破壊の試み
(全域性・一意性・散文と spec・到達不能・過剰な失敗・field 出所・新しい矛盾の 7 観点それぞれについて、
何を試したか。破れたものは具体的な数値入力つきで)

## 新しい所見
(1 件ずつ。無ければ「無し」)

## 総括
(3〜8 行)
