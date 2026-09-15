---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-09-15
wave: dev-wave-t2592-calibration-miss-floor
seq: 2
title: [T-2592] 較正のレコード数の選択規則へ品質検査の取りこぼし率下限を足し、rr5 の観測系列で採用点が 100 万から 200 万へ動くことを実測した (コード + docs、branch worktree-dev-wave-t2592-calibration-miss-floor、変異 matrix = baseline PASSED・7/7 KILLED・期待 node 完全一致、うち単一理由性ありが 4 件)
---

## 本文

裁定 = D1986 項 1。実装した規則の正本は {{D:calibration-records-miss-floor}}、
実測と射程の限界は `output/insights/2026-09-15_t2592-calibration-miss-floor/README.md`。
実装 commit = `632754bbc`。

- **裁定の条件 3 つの充足の仕方。** (a) workload 非依存 = read/write 比率にも workload tag にも
  触れない形で書いた。(b) 走らせ直す前に登録 = 本エントリと同じ着地で
  {{D:calibration-records-miss-floor}} が main へ入る。較正の再走はその後の別作業であり、
  本 wave では走らせていない。(c) rr5 の却下記録は却下のまま残した
  (`output/insights/2026-09-13/t2515-t2534-backoff-withdraw/README.md` と `docs/phase3.md` は無編集)。
- **段 3 の敵対相談が、変異で裏の取れた穴を 1 つ出した (refuted ではなく real)。** 起草プランの
  テスト群では、警告閾値を `floor * 0.8` へ緩める変異が生き延びる。miss 率 0.45% の負例を
  1 本足させたところ、本走で M3 はその 1 本だけに殺された。段 3 を省いていれば、
  正しさ防壁の閾値を下方へ緩める変異が素通りする状態で着地していた。
- **棄却 finding (real だが不採用)。** 「飽和候補が全て下限未満で、系列の最終点だけが両条件を
  満たす系列では新規則でも却下が残る」という所見は挙動の記述として正しいが、実装しない。
  裁定の逐語が「**も**満たす最小の値」で既存候補条件への追加を指すこと、最終点を飽和候補に
  入れると飽和を確認できていない点に `saturated=True` を付けて下流の読む選択根拠を偽装すること
  (絶対規律 2)、現行コードでも同じ挙動で退行ではないこと、の 3 点による。観測として記録する。
- **親 brief 自身の誤りを 2 レンズが独立に否定した。** 「片側の経路だけに掛けると workload
  非依存にならない」という親の理由づけは成立しない。結論 (両経路へ掛ける) は維持し、理由を
  「裁定が名指すのは選択規則全体であって片方の経路ではない」へ差し替えた。
  段 6 レビューも裁定文の説明の誤りを 2 件挙げ (must-fix は 0 件)、insight で訂正した。
- **登録簿は wave 中に増える。** 着手時点の登録済み較正は 4 件で、その全件について採用点が
  動かないことを確認した。しかし wave 中に local main が `6cf35ee7a` で 3 件足したため、
  取り込み後に 7 件で取り直した。7 件とも採用点は動かない。
  **着手時の 4 件だけで「全件動かない」と書いていたら誤りだった。**
- **受入全走 1 回目は `stage=postcheck rc=70` で終端した (非帰属)。** 子 rc は null で、
  テストは 1 本も走っていない。`claimed_main` は `0864b5dfa` だったが、post-claim merge の後に
  local main がさらに進んで `behind != 0` になった競走である。取り込み merge `8e974931e` 自体は
  成立しており、差分にも成果物にも影響しない。
- **セッション異常 2 件。** (1) `EnterWorktree` tool が
  `Could not read the repository git config to neutralize filter drivers` で失敗した
  (`.git/config` は読取可能で `git config --get` も成功する)。手動 `git worktree add` で回復した。
  (2) `tools/dev_wave_submodule_init.py` が 2 つの worktree の**両方で 1 回目に**
  `runtime-io-failure: update-no-fetch` で失敗し、同じ引数の再実行 (DW-O08) で成功した (2/2)。
- **工数。** codex 子 6 本 (plan 1・consult 2・author 1・review 2)。段 6 の fix 子は
  must-fix 0 件のため起動していない。変異は probe 1 走 + 本走 1 走。

## 次の一手差分

### 完了

- [T-2592] 較正のレコード数の選択規則へ「品質検査の取りこぼし率下限も満たす最小の値を選ぶ」を
  足した。規則の登録は {{D:calibration-records-miss-floor}}。rr5 の観測系列では採用点が
  N=1,000,000 (miss 0.364%) から N=2,000,000 (miss 1.392%) へ動き `cache_floor_warning=False`
  になる。下限値 0.50% と `l3_multiple` は動かしていない。rr5 の却下記録は却下のまま。
  remaining: none
  base: 44ac0794da658dba2069e6695d1c2d55d2232365efb5511400113809beb689c8
