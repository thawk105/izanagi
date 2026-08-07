# repo の「赤」の全数実測と、provenance 監査 6 違反の裁定パッケージ (2026-08-07)

依頼: 「現在、テストが赤なものはある？それを適切に直してほしい。」

計測 checkout = `.claude/worktrees/dev-wave-red-tests` (branch `worktree-dev-wave-red-tests`、
起点 `0d64599e`、権威ある受入結果は local main `23337171` を取り込んだ後のもの)。
submodule `external/ccbench` は `d706650c` で pinned-clean。
実行環境は Pegasus。全走は `run_tests.py` が計算ノードへ同期 dispatch した結果である。
検査は特記のない限り起点 `0d64599e` 時点で実測した。

## 結論

**テスト本体に赤は 1 件も無い。** 赤いのは `tools/check_ai_provenance.py` の全履歴監査だけで、
その 6 違反は既に共有済みの履歴にあり、**現行規約の内側に緑へ戻す経路が存在しない**。
したがって本 wave は実装差分を持たず、択一をユーザーへ返す。

## 実測一覧

| 検査 | rc | 結果 |
|---|---|---|
| `python3 tools/run_tests.py -rf` (**受入形ではない**、起点 `0d64599e`) | 0 | 6837 passed / 20 skipped / 0 failed |
| `python3 tools/run_tests.py` (受入形、起点 `0d64599e`) | 1 | 1 failed / 6836 passed / 20 skipped — **走行中に親が docs を書いたことによる偽の赤** (F106 の 4 度目)。落ちたのは `test_ruleops.py::test_real_checkout_independent_maximum_package_and_runner_preflight@real_repo` で、ツール実行前後の `git status` 一致を見る検査 |
| `python3 tools/run_tests.py` (受入形、local main `23337171` 取り込み後) | 0 | **7057 passed / 20 skipped / 0 failed** ← 本 wave の権威ある受入結果 |
| `python3 tools/check_docs.py` | 0 | 違反なし |
| `python3 tools/check_codex_agents.py` | 0 | 0 native active / 13 static dormant |
| `python3 tools/check_wave_startup.py` | 0 | submodule 初期化後に緑 |
| `python3 tools/ruleops.py check` | 0 | `candidate_count=0, structurally_valid=true` |
| `python3 tools/spool_fold.py --dry-run` | 0 | `status=noop` (fragment 0 件) |
| `python3 tools/audit_dangling_commits.py` | 1 | 取り残しあり (テストの赤ではない。下記) |
| `python3 tools/check_ai_provenance.py` | 1 | **1587 件中 6 違反** |

`audit_dangling_commits.py` の rc=1 は docstring どおり「取り残しあり」であって検査の赤ではない
(0 = 取り残しなし / 1 = 取り残しあり / 2 = 実行不能)。到達不能 commit が触れた path が main にも
他 local branch tip にも無いという人間確認向けの報告であり、
`rulings-inbox/2026-08-05-cleanup-branches-dangling-commit-gap.md` として既に卓上にある。
本 wave では新規起票しない。

20 skipped の内訳: 発生源を持つ 23 ファイルだけを別走行した結果 1389 passed / 20 skipped となり、
**20 件すべてがその 23 ファイルに閉じている**ことを確認した。個別の skip 理由 (逐語ラベル) は
取得できていない — 走行に `-rs -rf` を並べたため後勝ちで `-rf` が効き、失敗ゼロでは要約が出ない。
既知の発生条件は busybox / bwrap / bundled Codex runtime の有無、v1 freeze 不在、
sandbox の AF_UNIX 制約、submodule 未取得の 6 種で、**submodule 未取得だけは本 wave で
初期化済みのため発火していない** (`DW-O08`)。件数 20 は worklog (271) の前 wave と同一である。

## 赤の内訳 (一次資料 = Git object の `%B` を実読)

- **(a) merge commit 5 件** — `88f0f9f0` `85dacc27` `6e69ca5c` `16affe16` `905c867a`。
  いずれも `Merge branch 'main' into worktree-rulings-20260806-a` の subject だけで**本文が空**、
  `AI-Agent` trailer が無い。`DW-O17` が禁じる自動 message で作られている。
- **(b) `b0a07672`** — trailer は `role=manager` 1 行のみ。
  `output/insights/2026-08-06_token-hygiene/` へ `analyze_codex.py` / `analyze_v2.py` を置いており、
  実装面に Codex `role=author` を欠く。**F75 の型の 3 例目**だが、前 2 件は履歴確定前に修正された
  ため、**履歴に残存した F75 型違反としてはこれが最初**である。

## なぜ「直せない」のか (敵対検証済み)

段 3 の独立 codex に「緑へ戻す経路がある」方向から攻めさせたが、反証できなかった。

- forward correction は汎用機構ではない。target は `check_ai_provenance.py:111` でコードに固定され、
  枠は `6d7141dc` で消費済み、`docs/provenance/correction.md:5` が新しい担い手の追加と
  一般 allowlist への拡張を明示的に禁じている。candidate は exact 1 件に制限される (:855)。
- waiver は当該 commit 自身の message と paths に対してだけ評価される (:811)。
  後続 commit から過去 commit を指す構文は無く、`ratified=` (ユーザー批准) も要る。
- 後続 commit で revert / 削除 / rename しても、checker は各元 commit の `%B` とその commit の
  paths を読み直すため相殺されない (:786)。
- 誤検出説も否定された。merge commit も「すべての commit」に含まれ AI 非関与なら
  `AI-Agent: none` が要る。`.py` は所在不問で実装面であり、凍結場所であることは免除理由にならない。

したがって緑化には (i) 6 commit の message 書き換え = 履歴書き換え (規約が禁止)、
(ii) correction の一般化 = gate 設計の変更、(iii) 既知違反 allowlist = gate 弱体化、
(iv) waiver の遡及適用 = 契約変更 + 批准、のいずれかが要る。**すべてユーザー裁定の領分である。**

## 深刻度 — land は止まらないが、gate は実質無効化されている

`tools/dev_wave_land.py:1388` が呼ぶのは `--message-file` の per-commit preflight だけなので、
この赤は取り込みを止めない。しかし `DW-O17` は通常 commit を
「message file → `--dry-run -F` → `commit -F` → **既定 full-history 監査**」と定め、赤なら止める。
つまり **6 違反が入った時点から、全 wave の commit gate は恒久的に赤**であり、
各 wave が「これは既存分だ」と手で帰属して赤を跨ぐ運用になっている (worklog (272) がその実例)。
新しい違反が既存 6 件に紛れる状態であり、**放置の費用は監査品質そのもの**である。

### 予測ではなく実測になった (2026-08-07、本 wave の land 再試行時)

上の段落を書いた数時間後、land をやり直すために local main (`5f2dfaf4`) を取り込んだところ、
**違反が 6 件から 7 件へ増えていた**。7 件目は `3f2c43d7`
(`docs(t503): 変異本走の停止原因の誤診断を訂正し、F148/F149 の再発として記録する`) で、
`AI-Agent` trailer が丸ごと無い。本日 main へ入った別 wave の docs commit であり、本 wave の
commit は 1 件も違反に含まれない。

**「赤が常態化すると新しい違反が既存分に紛れて見逃される」は、もはや予測ではない。**
既存 6 件を跨ぐ運用が続く限り、7 件目・8 件目は同じ経路で増える。
案 1 (現状維持) の費用見積りは、この実測ぶんだけ上方修正される。

## ユーザーへ返す択一

親の推奨は **案 2**。

1. **現状維持** — 費用ゼロ。ただし上記のとおり gate は実質無効のまま固定される。
2. **forward correction の一般化 (推奨)** — `PR-C01` の「固定 target 1 件・一回限り」を、
   連言条件 (strict descendant / candidate exact 1 / target の実欠落 / 担い手自身が通常 green /
   waiver 保持者は担い手不可) を**保ったまま** target 複数へ拡張する。判定強度は落ちず、
   担い手が「誰が何をしたか」を明示的に書くので帰属の捏造もできない。decisions への記録が要る。
3. **既知違反台帳** — 6 SHA を固定台帳に置き、監査は既知と新規を分けて集計し rc は新規だけで決める。
   実装は軽いが**帰属の訂正が残らない**点で案 2 に劣る。
4. **履歴書き換え** — 規約が明示的に禁じている。**非推奨**。

いずれも `check_ai_provenance.py` (実装面) の変更を伴うため、実装は Codex `role=author` が書く。

### 併せて諮る小さな改善 (任意)

`tools/run_tests.py` は、受入形でない走行 (`-rf` を足した等) でも何も警告しない。
本 wave で親自身が踏み、同時刻に別 wave も `run_tests.py -rf` を受入として走らせていた
(独立 2 例)。**受入形でないときに 1 行警告を出す**改修を提案する。受理集合は変わらず、
「受入全走のつもりで事前検査 2 件が発火していなかった」という誤記録だけを塞ぐ。

## 逐語

- 段 3 敵対検証子の出力: `s3-adversarial.md` (`check_codex_output.py` rc=0)
