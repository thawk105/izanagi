# [T-2826] 依頼の逐語

## 1. ユーザーの起動引数 (2026-09-21 14:03 JST、`/dev-wave` の引数、逐語)

```
[T-2826] 受入 pre の worker 側 45 秒 (shard plugin を載せた段の modify 複合区間、sys +2027 秒、Lustre intent_lock 11.7 倍)
    を関数別に計時する診断。probe は job dir に置き、Codex author。対象は tools/acceptance_shards.py の records_from_items / _canonical_item
  の
    Path.resolve() (全 item に 2 回) / allocate / 選択と、conftest の _validate_real_repo_shard_state。T-2817 の S2 / S3
    形の段階載せで内訳を閉じる。pre ≈ max(worker 側, 早期 memo prewarm 44〜54 秒) という構造を事前登録し、worker 側の短縮量と pre
    の変化を別々に測る。短縮の実装は含めない (D1936 項 35「効果を先に測り、未確認のまま実装しない」)。一次資料は
    output/insights/2026-09-21/t2817-acceptance-bottleneck-3/README.md §5 (b)。稼働中の T-2825 (受入所要台帳の隣接対)
    とは編集面が別だが、比較測定の区間は重ねない。標本の時点は固定する。着手直前の local main から fresh
    worktree。本題の計測だけ。仮想リスク向けの gate・検査・台帳・一般化の追加は scope 外。
    不一致 1 件: codex は P1 規則でこの項を 1 位に置いた。私は 5 位にした。分けた根拠は、選定規則の「第一キー = P
    ラベル」と常設の前提「土台を上げるのは研究を止めているときだけ」が食い違い、実測では受入が研究を止めていないこと。
```

## 2. 起票時の本文 (`docs/archive/worklog-phase3-0921-1777.md` 623 行、entry 1777 の次の一手、逐語)

```
- [T-2826] **P1・新規**: 受入 `pre` の worker 側 45 秒 (shard plugin を載せた段で現れる modify 複合区間、process 群の sys +2027 秒、Lustre `intent_lock` 11.7 倍) の内訳を関数別に計時する (probe は job dir、Codex author; 対象 = `tools/acceptance_shards.py` の `records_from_items` / `_canonical_item` の `Path.resolve()` (全 item に 2 回) / `allocate` / 選択、conftest の `_validate_real_repo_shard_state`)。同 job の段階載せ (T-2817 の S2/S3 形) で内訳が閉じてから、`records_digest` / `selected_digest` と受理集合を byte 不変に保つ縮約 (例: path 解決の回数を減らす) を設計し、効果は同 job 段階載せ + 実受入 隣接対で測ってから実装する。早期 memo prewarm (44〜54 秒) が並走しているので、`pre` は 2 本の長い方で決まる (T-2817 README §5 (b): 他方を固定した場合、worker 側の短縮は memo の長さに達したところで頭打ちになる) — 判定の読み方にこの構造 (`pre` ≈ max の 2 本) を事前登録し、worker 側の短縮量と `pre` の変化を別々に測る。
```

## 3. 起動引数と起票本文の差 (親の読み)

- 起票本文は「内訳が閉じてから縮約を設計し、効果を同 job 段階載せ + 実受入隣接対で測ってから実装する」までを含む。起動引数は「短縮の実装は含めない」「本題の計測だけ」で、縮約の設計・実装と実受入隣接対は本 wave の外。
- 「worker 側の短縮量と pre の変化を別々に測る」は起動引数にも残る。本 wave はこれを repo の code を変えない probe 内の反実仮想条件で測る (brief (P2) / (P3))。
