# [T-2146] 発行主体 subtree を hooks の書込み防護対象へ足す

着地受領証の署名鍵と issuer 運用複製を置く repo 外の固定 subtree を、hooks の 2 つの書込み防壁
(`guard_write` = Write/Edit/MultiEdit/NotebookEdit/apply_patch、`guard_bash` = 書込み・削除・移動)
の拒否対象へ加えた。読取りは従来どおり通す。

- wave branch: `worktree-dev-wave-t2146-authority-guard`
- 実装 branch (D427 の第 2 worktree): `worktree-dev-wave-t2146-guard-author`、
  fix branch: `worktree-dev-wave-t2146-guard-fix1`
- base: `f486ff13c` (着手時の local main)

## 着手前の実測 — 何が開いていたか

`verbatim/s1-brief.md` の前提確認と、親の probe で次を実測した。

- 発行主体 root への Write、redirect 書込み、`rm -rf` は**すべて許可**されていた。
- 同 root の**読取り**も許可 (これは意図どおりで、変更後も許可のまま)。
- 現行 HEAD では `hooks/` 配下が Write / Edit / apply_patch / Bash のどれからも編集できない。

## 手順 — D374 ではなく D427

段 2 と段 3 の両レンズが独立に「依頼が引く D374 の手順は現行 main では実行不能」と指摘し、
親も実測で確かめた。正本は **D427** (有効化前 commit を base にした第 2 worktree で実装し、
親が統合 commit を作り、wave branch へ merge)。**D428** の反転検査も同時に発火する。

本 wave で実測した D427 運用の要点 3 つ (`hooks/README.md` の「guard 自身の保守境界」へ記録済み)。

1. 第 2 worktree の作業ツリー版は古いので、実装子には現行 main の全文を射影して渡し、
   親が同期後の bytes を sha256 で検算する。
2. `guard_write` は**最後の 1 回**で入れる。入った瞬間に第 2 worktree でも `hooks/` が施錠される。
   実際、段 6 の fix1 子はこの施錠に当たって適用できず、正しく「未適用」と報告して止まった。
   親は `guard_write` に判定が入る前の commit から fix 用 branch を作って作業場を復活させた。
3. merge は競合する。実装 branch 側を採ったうえで、結果が実装 branch の blob と byte 一致し、
   かつ他の file が 1 本も動いていないことを親が検算する。

## 段 3 / 段 6 が見つけたもの

段 6 のレビュー 2 本は**どちらも NO-GO** を出した。最も重いのは次である。

- **`perf` の出力先処理が既存防護を弱めていた** (レビュー A)。単位 A1 が発行主体判定を足した際に
  出力値を後段の既存判定から除外したため、末端でない既存の防護対象 (official / exploration の
  campaign tree、namespace marker、`hooks/` 配下、ccbench) が `perf` の出力先として通るようになった。
  実測での退化は 6 形。**親が最初に回した 61 件の反転検査 corpus はこの形を含んでおらず、
  取り逃していた。** 規律 2 に直接触れるため最優先で直した。
- **祖先判定が filesystem root だけを捕捉しない** (レビュー B)。採用済み項目の取りこぼしとして閉じた。
- **既存テストの赤の帰属**。索引が 2 本になったことで走査回数が 1→2 になった期待値ずれで、
  実装の欠陥ではないと両レビューが一致。ただし「単に 2 へ書き換える案」はレビュー A が不採用とし、
  root ごとの走査回数を個別に見る形へ改めた (元テストが守っていた「候補ごとの再走査を禁じる」
  性質を保つため)。
- **変異 M2 は独立した位置になっていない** (レビュー A)。apply_patch も共通の判定を使うため
  等価変異になる。DW-M01 / F28 に従い登録から外し、`perf` 退化を狙う変異へ再照準した。

## 実測 (すべて親が実行)

| 検査 | 結果 |
|---|---|
| 焦点走 (test_hooks / test_codex_hooks / test_codex_worker_launch / test_campaign / test_plain_runner_coverage) | fix 前 1158 passed / 1 failed → **fix 後 1163 passed / 0 failed / 4 skipped** |
| D428 反転検査 (子が書いた 61 件 corpus) | `deny → allow` **0 件**、`allow → deny` 9 件 (すべて発行主体関連) |
| D428 反転検査 (親が独自に書いた 32 件 corpus。レビューが見つけた `perf` の 6 形入り) | `deny → allow` **0 件**、`allow → deny` 7 件 (すべて発行主体関連) |
| 変異本走 (`mutation-final-result.summary.json`) | baseline PASSED、**8/8 KILLED**、MISMATCH 0、TIMEOUT 0、等価変異 1 件のみ SURVIVED |
| provenance 全史監査 | 3112 件、新規違反なし |
| `check_docs.py` | 違反なし |

変異は probe 走 (`mutation-probe-result.summary.json`) で観測した赤 node を期待値に固定してから
本走を回した。期待 node の完全一致だけを KILLED と数える契約なので、8/8 は「登録した歯がすべて
実際に立っている」ことを意味する。等価変異が SURVIVED したことは、harness が生存を報告する能力
自体の正例になっている。

## 主張の上限 — 何が閉じていないか

**書込みを閉じただけでは、受領証の偽造不能性は主張できない。** 秘密鍵の**読取り**は通り、
読める主体は署名を作れる。0700 という権限は、同じ利用者として動く AI を隔離しない。

言える上限は「**信頼済み PreToolUse が観測する直接書込み面から、発行主体 subtree を追加で
除外した**」まで。「完全ロック」「AI は署名を偽造できない」「D906 を満たした」とは書かない。
残余の全列挙は `hooks/README.md` の「発行主体 subtree について閉じない面」が正本である。

## ユーザー裁定へ返すもの

1. **D906 の実効層。** 真正性を機械的に主張するには、鍵と署名実行権限を AI から分離した
   別 OS principal / 別 host / hardware signer が要る。本 wave の着地は「直接書込み面の縮小」
   までで、D906 の完了根拠に数えない。
2. **shell 状態模型。** `pushd` / `env --chdir` / subshell / 条件実行の cwd 追跡は、現在どの
   防護対象でも成立していない。閉じるなら全防護対象へ同時に入れる独立 wave が要る。
3. **既存欠陥 2 件。** `perf` の密着短 option (`-oFILE`) が専用分岐に認識されないこと、
   読むだけの `cp` が拒否されるのに `cat` は通る非対称。どちらも発行主体に限らない族の問題。

## 収録物

- `verbatim/` — 段 1 brief、段 2 プラン、段 3 敵対相談 2 本、段 4 裁定、段 5 実装子 3 本、
  段 6 敵対レビュー 2 本と fix 3 本の逐語。
- `mutation-probe.json` / `mutation-final.json` — 変異 spec (probe 用と本走用)。
- `mutation-probe-result.summary.json` / `mutation-final-result.summary.json` — 変異台帳の要約。
- `d428-inversion-final.json` — 最終形での D428 反転検査の生結果。
