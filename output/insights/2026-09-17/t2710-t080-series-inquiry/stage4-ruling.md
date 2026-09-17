# 段 4 裁定 — [T-2710] (2026-09-17、親)

段 2 plan (`stage2-plan.md`)、段 3 レンズ A (`stage3-lensA.md`、検出力・受理集合) / B (`stage3-lensB.md`、実効性・費用) の所見を
real / refuted / 判定保留 に裁定し、本 wave の確定と裁定パッケージを決める。裁定 inbox の再走査: local main は wave 開始時の
`38353207f` から動いていない。

## 1. 本 wave の確定

- **実装しない (調査のみ)。段 4 → 7 → 8 → 9。** 実装面の差分ゼロなので変異 matrix は免除 (DW-S04)。受入全走は免除しない。
- 受理集合は変えない (D2068 / D2104 項 28 維持)。`growth_test_holds.py` の保留は復帰させない。probe は job dir に置き repo へ入れない。
- **別系列化は本 wave では採らない。** 3 材料は揃ったが、「受理集合が同値に保たれる」ことを示す条件が未成立 (§3)。採否は
  裁定パッケージ (§4) でユーザーへ返す。

## 2. 所見の裁定

### plan (段 2) の親 brief 訂正 — すべて real、採用

| 訂正 | 採用 |
|---|---|
| shared-base 群は 13 node (12 でない)、実 builder を通すのは 1 node | 採用。M′ = M + `test_t080_shared_base_builds_real_builder_once_across_processes` の 12 node |
| `dev_wave_wait.py acceptance --check-only` は存在しない (`--check-only` は producer 専用) | 採用。P2 の該当箇所を撤回 |
| M 除外後の次点 node の台帳値は 170 秒 (161.1 は T-2559 の実測) | 採用 |
| lock union は session `895f300a` で 231.9 秒 (186.5 は T-2559) | 採用 |
| β′: lock union 231.9 秒を維持すると 292〜327 秒 | **refuted** (親の `probe_lock_modes` とレンズ B: read は `LOCK_SH`、最大 22 本同時保持、union は直列化下限でない)。感度表示としてだけ残す |

### レンズ A

| # | 所見 | 裁定 | 扱い |
|---|---|---|---|
| A1 | 単体との「重複」は述語単位に限る。M の全経路 (stub-free 発行 + verifier 全体の単一原因 + public gate call-edge) の代替は無い | real | 被覆表の「分離すべき検出力」列をこの意味で確定 |
| A2 | g7 は実 repo (`ROOT` の git 履歴と `external/ccbench` HEAD) を読む — 被覆表の独立項目にする | real | 表に「実 ccbench checkout との比較」行を追加。束縛先は tree OID だけでは表せない |
| A3 | 実 git 履歴を作ること自体は e2e 専有でない | refuted (brief の表現を訂正) | 専有部分を「正常発行済み receipt に対する履歴変異 + stub-free 単一原因」に限定 |
| A4 | plan が M 全体を単体で代替可能と断言している | refuted | — |
| B1 | closure 束縛は受理集合を「同 tip で M 緑」から「≤24h 前の関連内容で M 緑」へ変える。HEAD 束縛でも毎走観測→過去観測の変更は残る | real | 裁定パッケージの中心条件 |
| B2 | closure A は `output/` を含まず、現行 e2e が base 構築時に複製する git 可視 output の conjunction file を旧証跡では検査しない | real | closure A は不適格。closure B も完全閉包未証明 |
| B3 | 11/11 probe は HEAD 完全一致で、closure 束縛の成立証拠に転用不可 | real | README に明記 |
| C1/C2 | hold 解除の追随を次回定期走に任せると F485 再演。解除版の有効化前に M の完走を必須にする条件が要る | real | 裁定パッケージの条件 |
| D1 | 「別系列化する」の成立条件に受理集合の同値性が不足 | real | §3 |
| D2 | plan が実装済みを装っている | refuted | — |
| brief 「M は実 repo に依存しない」への一般化 | real (誤り) | 訂正: M は timed lock を持たないだけで、g7 と output 複製は実 repo に依存する |

### レンズ B

| # | 所見 | 裁定 | 扱い |
|---|---|---|---|
| 1 | 利用時拒否は複数境界 (verifier / adapter / driver `gate_check` と `run_block` / holdout CLI legacy / floor の verifier 注入とは独立の境界 / report の検証済み利用 / 受入受領証 / land 再判定) を要し、診断→検証済み利用の昇格境界は未設計。実効性は部分的 | real | README §2 に「部分的」と明記 |
| 2 | closure A/B は完全閉包でない (`docs/phase3-8b-descriptor-design.md` が builder 入力、非 ignored untracked、submodule checkout は tree OID に載らない)。同期なら利得が消え、非同期なら有効化順序が要る。費用は A 35〜44 分/日、B 57〜72 分/日 (仮定つき) | real | 裁定パッケージに数値で載せる |
| 3 | plan の β′ は refuted。親の β (251〜255) も変更後の実測ではなく判定保留。α は shard-1 247.2 が最遅。±4% は感度表示であって信頼区間でない | real (β′ refuted / β 判定保留) | README §3 を「見積もり幅 228〜265 秒、300 秒を切るとは断定しない」に |
| 4 | 親の T-2750 仮想 probe は nodeid 書換えで台帳参照を壊し全 node 1 秒になった → 5,165×3 は撤回。修正値: 分割 (M 維持) 6,052.7×3、M は 0/6/5、240 秒 node が残る | real | probe を修正し再計算 (`probe_shard_wall.895f300a.v2.txt`): 6,052.7×3、M 0/6/5 で一致。撤回して差し替え |
| 4′ | T-2750 だけでは最長 node 240〜252 秒が残り 305〜318 秒級。別系列化の独自利得は長時間 node を毎走経路から外すこと | real | 裁定パッケージの比較表 |
| 5 | 別系列化は選択集合の変更だけでは成立せず、新設物 7 種が要る | real | 裁定パッケージ |
| 6 | 「上位 10 worker が M を 1 本ずつ」は node→worker の結合証拠が無い | 部分的に refuted: 占有データだけで示せる — M の重い 10 node (JUnit ≥228.5 秒) は 1 worker に 2 本入ると最大占有 272.3 秒を超えるので別 worker に 1 本ずつ入り、占有 ≥228.5 秒の worker はちょうど 10 本。よって残りの最忙 chain は 11〜14 番目 (177.8〜188.7 秒) のいずれか。ただし「変更後の割付も同じ」は言えない (この点は real) | README §3 に証明の形で書き、変更後の再割付は未実測と明記 |
| 6′ | 12 番目 (187.4) だけを床にする根拠は無い | real | 185.8〜188.7 秒の幅で書く |

## 3. 別系列化を採らない理由 (規律 2)

1. **受理集合の同値性が示せていない。** 現行 gate 4 は C 全体の exact partition を要求し、M の緑は**同じ tip・同じ走**で観測される。
   別系列にすると M の緑は「≤24h 前・関連内容が同じ」記録になる。関連内容の閉包 (git 可視 output、`docs/phase3-8b-descriptor-design.md`、
   非 ignored untracked、`external/ccbench` の実 checkout、hold の版) を tree OID で完全に表す設計が無く、closure A は output の穴を持つ (B2)。
2. **利用時拒否の実効性は部分的。** 判定器単体は負例 11/11 を拒否するが、迂回路 (migration CLI 直叩き、driver Python API、adapter への注入、
   floor の `receipt_verify_fn`、report の `inspect_receipt_history`、旧受領証の land 再利用) が残り、診断→検証済み利用の昇格境界が未設計。
3. **起動契約が無い。** CI / cron / timer は不在 (D700 の却下理由 (i) は現在も真)。D2002 は外部 scheduler を認めるが、起動主体・
   失敗回収・独立期限検知が決まらないと F485 の「未実行が露見しない」に戻る。
4. **hold 追随 (F485 型)。** `_freeze_hold.HELD=True` の下で M の single-defect 3 型は held/released 両挙動を検査している。hold 解除の裁定に
   test 全体が追随したかは、その変更の受入で M が走らなければ確認できない。

## 4. 裁定パッケージ (ユーザーへ返す)

| 選択肢 | 必要な条件・実装 | 費用 (仮定つき) | 毎走から失うもの | 見積もり wall (最遅 shard) |
|---|---|---|---|---|
| **(a) 毎走維持 (親の推奨)** | 無し | 現行 337.9〜351 秒を継続 | 無し | 現行のまま |
| (b) T-2750 (成分粒度 file → node) を先に実測 | allocator の成分単位変更 (peer wave [72bbfd] 稼働中)、D358 維持 | 別 wave | 無し (受理集合不変) | 負荷 6,052.7×3 に均等化するが 240 秒 node が残る → 305〜318 秒級 (モデル値) |
| (c) 別系列化 (条件付き) | (1) 完走記録 schema と真正な発行 (runner 由来、node 別 terminal)、(2) 独立期限検知 (24h、利用の無い期間も)、(3) 利用時拒否を全境界 + 昇格境界の設計、(4) 関連入力の閉包定義 (output git 可視 file・docs 入力・untracked・ccbench checkout・hold 版を含む) と関連変更時の焦点走、(5) gate 4 を `U = C − M` へ (C の gate 2/3 は維持)、(6) D701 維持 + M 本体完走の terminal 証跡、(7) hold 解除版の有効化前に M 完走、(8) 起動契約 (計算ノード投入経路) | closure A で 8.4 走/日 ≈ 35〜44 分/日、closure B で 13.7 走/日 ≈ 57〜72 分/日 (250 秒 + 前処理 0〜65 秒/走)。同期なら利得が消え、非同期なら有効化順序が要る | M 固有の結合検出 (被覆表) を各受入走で観測する機会 | α 247.2 (shard-1) / β 251〜255 (shard-0)、感度 228〜265 秒。300 秒を切るとは断定しない |
| (d) (b)+(c) | 両方 | 両方 | (c) と同じ | 負荷 5,285.4×3、最長 node 150 秒 (M′ なら 170 秒) |

**親の推奨: (a) を維持し、(b) の実測結果を待ってから (c) を再度諮る。** (c) の条件 (1)〜(8) は、いずれも本 wave の scope 外 (追加
gate・検査・台帳) であり、実装するなら別 wave で D2002/D2003 に従う。

## 5. worklog 次の一手への反映

- [T-2710] を「P1・裁定パッケージ提示済み → ユーザー裁定待ち」へ。一次資料は本 insight。
- [T-2750] (peer) へ本 wave の修正済み仮想計算 (6,052.7×3、M 0/6/5、240 秒 node 残存) を材料として渡す (worklog の同項に追記)。
