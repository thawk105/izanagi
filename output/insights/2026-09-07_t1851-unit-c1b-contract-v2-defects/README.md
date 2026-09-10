# [T-1851] 単位 C1b — 契約 v2 は実体化できない (実装 0 行の裁定 wave)

base `9c1951179` (継承 tip `17e85e413` + local main `086694d8c` の merge)。
branch `worktree-dev-wave-t1851-unit-a`。**land しない (D1341)。**

## 1. この wave が出した結論

C1a の段 4 が固定した **terminal 証拠の契約 v2 は、literal に実体化すると v2 台帳の
terminal 行を 1 行も書けない。** 段 2 の plan、段 3 の敵対レンズ 2 本、親の独立検算が
いずれも同じ結論に達したため、**実装せず契約の訂正だけを成果物とする** (DW-S04 の `4 → 7 → 8 → 9`)。

段 2 plan の判定も段 3 の 2 レンズの判定も **no** である。

## 2. 実測で確定した欠陥 7 件 + 偽造 2 件

正本は `s4-adjudication.md` の 1 節。要点だけ:

| # | 契約 v2 | 現物 |
|---|---|---|
| X-1 | 「exact field 24」 | 表の distinct field は **23** |
| X-2 | `campaign_record` は 27 key | exact **30 key**。`_JOURNAL_KEYS["session"]` と集合等値 |
| X-3 | issuer は 3 引数 | `attempt_binding` の 3 digest が launcher 側に存在しない |
| X-4 | 証拠へ probe / campaign_record を exact に載せる | 三軸 literal の運び手が **5 field 以上**。guarded writer が必ず拒否 |
| X-5 | E1 は campaign と同順 | **一致しない**。partial exec の枝が実測で分岐する |
| X-6 | `exec_failures` は私有 sink 由来 | campaign は `notes` の regex 由来。実測値が食い違う |
| X-7 | 非有限は null 化し `len + nonfinite + exec == reps` | **自己矛盾**。null を残すと左辺が 1 多い |
| X-8 | issuer table + private API で封印 | table 直接 insert・private issuer 直呼び・`__reduce_ex__` が全部 accepted |
| X-9 | (未検討) | `_launch_floor_attempt_for_test()` が fake fact から production の封印を発行できる |

## 3. 最も重い 1 件 — core の等値検査と E2 語彙の衝突

`attempt_registry_core.py:1388-1394` の等値と `:1402-1406` の null matrix を同時に満たす
`failure_reason` が存在しない。launcher の分類語彙 (`competing_process` / `launch_failure`) と
E2 の 4 語が互いに素だからである。封印証拠の検査 hook `:1407-1408` は**両方より後**なので、
C1b が作ろうとしていた機構をどれだけ強くしても解けない。
レンズ A が E2 の 4 語を直接投入した結果、**全件が等値で落ち validator 呼出しは 0 回**だった。

親が最初に出した修正案 (v2 では分類語彙を E2 の 4 語にする) は**否定された**。
E2 の 4 語のうち `measurement_sample_incomplete` と `measurement_dispersion_exceeded` は
`open()` の後にしか判明せず、分類は `open()` の前に起きるためである。

## 4. 親が確定させた訂正 (契約 v3)

`s4-adjudication.md` の 2 節が正本。要点は
(a) 30 key の確定、(b) issuer を draft → adapter 発行の 2 段にして test seam を塞ぐ、
(c) 証拠を再導出面 (平文) と束縛面 (digest) に分ける、(d) E1 を campaign の実 semantics に合わせる、
(e) 非有限の不変条件を `count(non-null) + nonfinite + exec == reps` に直す、
(f) capability の権威を canonical bytes にし table membership を権威にしない、
(g) claim v4 / `_AttemptState.mode` / core 8 surface 伝播は自発的拡張として不採用。

## 5. 未裁定だった 4 件 (**2026-09-07 に codex 2 本へ諮って決着済み**)

`s4-adjudication.md` の 3 節が正本。
(1) core の等値検査と E2 語彙の衝突をどう解くか (最重)、
(2) `exec_failures` の出所 — campaign 側を変えるか契約側を合わせるか (計測の意味論に触る)、
(3) 封印の信頼境界をどこに引くか (同一 process 内の module 改変を脅威に含めるか)、
(4) C1b の単位 — 縦 1 単位で実装するか、契約 v3 だけを積んで次 wave へ送るか。

**この 4 件はユーザー指示により codex 2 本 (lane sol / luna) へ諮り、親が決めた。
裁定の正本は `rulings-resolved.md`、逐語は `verbatim/rulings-lens{A,B}.md`。着手を塞ぐものは無い。**

## 6. 親が撤回した主張

**親の V3 は誤りだった。** 「証拠文書を塞ぐのは `workload` ではなく `run_cmd` だ」と書いたが、
親の probe が `workload` に文字列 `"rr80"` を渡していた。実型は freeze の `ycsb` mapping
そのもの (`s8b_floor_contract.py:680-692`) で、実型で測ると hit する。
**plan の元の帰属が正しく、親の訂正が誤りだった。** レンズ A の A-10 が正しい。
V6 で足した運び手 (`run_cmd` / `notes` / probe stdout) は有効で、運び手の集合はむしろ広がる。

## 7. 次 wave の出発点

- **契約 v3 を確定させるには 3 節の (1) と (2) のユーザー裁定が要る。** これが決まるまで
  実装子を起動しない
- 決まったら、レンズ B の判定どおり **production 効果のある分割は存在しない**ので、
  leaf + launcher + profile + core + adapter を縦 1 単位で実装する
- 変異候補は `s4-adjudication.md` の 4 節に可否を記録した。M4 / M5 / M6 / M7 / M9 / M12 は
  軽い具体化で成立、M1 / M2 / M3 / M8 / M10 / M11 は再照準、M13〜M18 は分割上この単位に入らない
- 段 2 / 段 3 の成果物は骨格が変わらない限り次 wave で流用できる (読み込み契約の規定)

## 9. 受入全走

- attempt 1 (19:32 JST): `stage=merge-message-provenance` rc=70。テストは 1 件も走っていない。
  受入自身が行う main 取り込みで、両親が共に `attempt_registry_core.py` と
  `test_attempt_registry_core_s8b_profile.py` を変更しているため、既定の self-report message では
  Codex `role=author` が足りない。親はこの走行に待ち手を付けておらず約 27 分を空転させた。
- 合成監査 (20:03-20:13 JST): Codex `role=author` の read-only 子が両側の差分と main 側の現物を
  読み、3 file の意味の合成を **干渉なし**と判定した。逐語は `verbatim/merge-audit.md`、
  prompt は `prompts/prompt-merge-audit.md`。
- attempt 2 (20:14-20:29 JST): **rc=0、`verdict: child-green`、21,414 passed / 68 skipped**。
  `tested_main=f2cca136a`、`tested_tip=6e1845adf`、red / flake は空、pre/post fingerprint 一致。
  receipt は `acceptance-receipt.json`。

## 8. 収録物

- `s1-brief.md` — 段 1 brief
- `s4-adjudication.md` — 段 4 裁定 (正本)
- `parent-verification.md` — 親の独立検算 V1〜V6 と V3 の撤回
- `verbatim/` — 段 2 plan、段 3 レンズ A / B の逐語出力と各 receipt
- `rulings-resolved.md` — 未裁定 4 件の裁定 (codex 2 本に諮り親が決定)
- `prompts/` — 全 6 子へ渡した prompt の逐語
