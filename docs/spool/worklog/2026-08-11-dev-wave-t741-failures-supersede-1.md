---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-08-11
wave: dev-wave-t741-failures-supersede
seq: 1
title: failures fragment へ supersede 追記の文法を足した ([T-741]) — 敵対レビューが偽 F 見出しの生成経路を暴き、fold 側で構造を握る形に変えた (コード + docs、受入 8275 passed / 20 skipped / 526.68 秒 / rc=0、変異 7/7 KILLED、branch worktree-dev-wave-t741-failures-supersede)
---

## 本文

- **裁定どおり (a) を実装した。** 既存 F エントリの記述が後続の事実で古くなったことを、再発として
  誤記録せずに書けるようにした。fragment の H2 に `supersede 追記` を足し、
  `- F<n> **supersede: YYYY-MM-DD** — <本文>` の 1 物理行を対象 F エントリの
  最後の非空行の直後へ挿入する。
- **段 3 の敵対レンズが、素直な実装の致命的な穴を暴いた。** 当初案は挿入行の本文をそのまま
  canonical へ書く形で、本文に `### F203. ...` と書けば**偽の F 見出しを作れた**。
  F-ID 集合・次回採番・`F<n>` 参照が同時に壊れる。裁定で 2 段構えにした —
  (i) 行頭の `- ` は fold が付ける (書き手の本文が見出しになりえない)、
  (ii) 描画後の F 見出し列を postcondition で検査する (`failure-topology`)。
  後者は `再発` payload 経由の既存の同型経路も塞ぐ。
- **迂回できる gate は恒真に近い、という理由で `再発` 側にも排他を入れた。**
  新節を足しても書き手が `再発` 節に supersede 文を書けば shape・重複検査を丸ごと迂回できる。
  本文を `**supersede: 日付** — ...` の署名に固定し、`再発` 節でその形を拒否した。
  迂回の閉じ方は 2 巡かかった — 1 巡目は HTML comment 分割 (`- **super<!--x-->sede:`)、
  2 巡目は先頭空白 1〜3 個・marker 直後の tab・ゼロ幅文字 5 種。負制御 (fence 内 decoy、
  空白 4 個以上のインデント、全角 `ｓｕｐｅｒｓｅｄｅ`、通常 prose 中の言及) も同時に固定した。
- **焦点再レビュー 2 回目が返した最後の NO-GO は、親裁定で nit へ降格して裁定パッケージへ回した。**
  HTML 文字参照 (`- **super&#x73;ede:`) は表示上 supersede になるが現行投影では拒否されない。
  降格の根拠は 3 つ — (i) この検査は台帳の構造を守る正しさ防壁ではなく分類の運用ガードであり、
  迂回しても (R1)(R3)・shape 検査・F-ID topology は不変、(ii) 同レビュー自身が全角
  `ｓｕｐｅｒｓｅｄｅ` は裁定 E 節 (受理集合の縮小は `再発` 排他だけ) を超えるとして
  拒否対象から外しており、文字参照だけを閉じるのは原理的な境界にならない、
  (iii) 表示等価の偽装一般を閉じるには正規化形の契約という別設計が要る。
- **親 brief の誤りを 3 件、レンズの指摘で訂正した。** (i)「failures fragment は supersede を
  表現できない」は誤りで、正しくは「`再発` payload が任意文字列なので書けるが再発として
  誤記録される」。(ii) 凍結 pin の grep 説明を「hit 2 ファイル」と書いたが実際は 6 ファイル
  (結論の「SHA-256 pin なし」は不変。`FROZEN_MANIFEST` は `output/**` 23 件のみ)。
  一次資料の出力を貼らずに要約した F1 型の near-miss。(iii) stale な逐語の行番号を
  F196 の見出し行と取り違えていた。
- **`tools/codex_reasoning_ab.py` の `TRACKED_HASHES` は生きた pin ではない。**
  `orchestrator/tests/test_check_docs.py` を編集対象に加える際に確認した。記録された hash は
  現行ファイルと既に不一致で、過去実験の履歴記録である。よって凍結 bytes 条件 (`DW-O09`) は
  不成立と判定し、巻き戻しをしなかった。
- **P8 (実 canonical への dogfood) は byte で裏取りした。** `--dry-run` は after hash しか出さないため、
  `spool_fold` を使わない独立計算で挿入後の全文を組み立てて sha256 を照合し、一致を確認した
  (`726563271d9e...`)。本 wave の failures fragment は F196 へ supersede 1 行、F138 へ再発 1 行を入れる。
- **変異は 7/7 KILLED (2 走)。** 1 走目は 5 KILLED / 2 MISMATCH。MISMATCH の 2 件は変異が
  殺されていたが期待 node が 1 件ずつ不足していた (F138 の 3 例目)。
  観測集合で再登録した 2 走目で 2/2 KILLED。初回台帳は erratum として保持している。
  なお挿入位置そのものへの変異は**登録しなかった** — 合成 fixture の `docs/failures.md` は F1 が
  最初かつ最後のエントリなので、位置を動かすとほぼ全 byte-exact テストが赤くなり、
  harness が要求する期待 node の完全一致を事前に確定できない。位置は実 canonical 3 境界
  (空行なし / 空行 1 行 / EOF) と合成 1 件の byte-exact テスト計 4 本で固定した。
- **段 8 の自己改善候補は 1 件で、3 度目の見送りになった。** 「期待 node は完全集合で登録する」を
  `DW-M08` へ 1 行入れる案。実際に編集して測ったところ
  `docs/dev-wave/**: L1.5 unique footprint 9773 bytes > 予算 9566 bytes` で 207 bytes 足りず、
  上限は引き上げない方針のため戻した。陳腐化ルールの削除かテスト化で空ける作業が要る。
- **[T-731] が 3 例目として再現したが、署名が新しい。** 焦点 3 file の subset 走行で
  `test_exploration_external_root_keeps_wave_clean` が赤 (556 passed / 1 failed)。単独 nodeid でも
  再現し、当該 test は campaign pipeline 専用で `spool_fold` を import しないため実装差分へ
  帰属しない。同じ tree の受入全走は 0 failed。**署名は従来の
  `TypeError: campaign env_tag は exact str` ではなく
  `CertifiedWriterAuthorizationError: Pegasus compute では receipt state 内で一意な
  required authorization_contract だけを受理する` (`execution_guard.py:156`)** で、
  走行範囲依存が単一原因でないことを示す。
- **受入 lease の merge commit を作り直した (provenance)。** 待ち手 script が自動で作る merge の
  message file に Codex `role=author` 行を入れ忘れており、`orchestrator/tests/test_check_docs.py`
  を両親がともに変更していたため統合結果がどちらの親とも異なり、
  `check_ai_provenance.py` が `実装面に Codex role=author がない` で 1 新規違反を出した
  (`DW-O17` の「実装面 path が両親と異なれば Codex `role=author` へ」に該当)。
  branch は未 push で共有されていないため、merge の第 1 親へ戻して同じ merge を正しい message で
  作り直し、記録 commit を cherry-pick し直した。**受入を走らせた tree と bit 一致することを
  `git diff a59b6bdb HEAD` が空であることで確認済み**。受入を走らせた tip は `a59b6bdb`、
  作り直し後の同一 tree の merge は `dbae4a66`。PR-C01 の forward correction 枠は消費済みで
  使えず、`KNOWN_PROVENANCE_VIOLATIONS` への自己登録は機械防壁の自己緩和になるため採らなかった。
- **受入 lease は 1 度取り損ねた。** 10 秒周期 400 回 (約 67 分) すべて `held` で、
  一度も `queued` を観測しないまま上限に達した。上限を 1700 回へ広げて張り直し、69 回目で取得。
  取得時点で main が 43 commit 先行しており、待ち手内 merge で取り込んでから投入した。
- エージェント工数: codex 子 10 本 (plan 1 / 段 3 敵対 2 / 実装 1 / 段 6 レビュー 2 / fix 2 /
  焦点再レビュー 2)。親は 段 4 裁定・統合・docs・変異 2 走・受入 1 走・記録。

## 次の一手差分

### 完了

- [T-741] failures fragment へ `supersede 追記` 節を実装した。fold は対象 F エントリの最後の
  非空行の直後へ `- ` 付きで 1 行挿入し、描画後の F 見出し列を postcondition で検査する。
  `再発` 節への誤用は正規化投影で拒否する。本 wave 自身が F196 へ 1 行使い、byte で裏取りした。
  remaining: none
  base: 27bee8ee4d7a99b27032da31ac970d7dbe70cb8daac431843a1438f511b71000

### 更新

- [T-731] **P3・3 例目を実測 (2026-08-11)**: `test_dev_wave_land.py::test_exploration_external_root_keeps_wave_clean`
  が走行範囲に依存して落ちる件。本 wave の 3 file subset (556 passed / 1 failed) と単独 nodeid 走で
  再現し、同じ tree の受入全走は 0 failed。**署名が過去 2 例と異なる** —
  `CertifiedWriterAuthorizationError: Pegasus compute では receipt state 内で一意な
  required authorization_contract だけを受理する` (`orchestrator/campaign/execution_guard.py:156`)。
  過去 2 例は `TypeError: campaign env_tag は exact str`。単一の exact 型検査ではなく、
  **site 依存分岐が参照する activation 登録状態そのもの**が走行範囲で変わる疑いへ広がった。
  base: 232f1d8389017be824502fc1c2d6b19dcebe357a5cf5f5f43b834b627c6a502a

### 新規

- {{T:land-rollback-state-retention}} **P3・新規・ユーザー裁定待ち**: `tools/dev_wave_land.py` は
  lock 内 fold の rollback が失敗しても fold の resume state を無条件で削除する。
  ref・index・path 復元のいずれかが失敗すると、canonical・`FOLDED.md`・fragment が混在した状態で
  resume journal だけが消える。選択肢 = (a) 全復元点の成功時だけ state を削除し fault injection
  テストを足す / (b) 現状維持。成果物影響 = (b) のままなら land 中断時に台帳が第三の状態へ落ち、
  同じコマンドでの resume ができない。本 wave の段 3 レンズ A の所見 4 (scope 外裁定)。
- {{T:reserved-label-display-equivalence}} **P3・新規・ユーザー裁定待ち**: `再発` 節の
  supersede 誤用検査は、表示上は同じで文字列が違う予約ラベル (HTML 文字参照 `&#x73;`、
  全角 `ｓｕｐｅｒｓｅｄｅ`、confusable) を拒否しない。併せて `再発` payload 一般が
  任意文字列である点も残る (本 wave は `failure-topology` で最悪ケースのみ封じた)。
  選択肢 = (a) 可視文字列の正規化形を定義して予約ラベル判定に使う / (b) `再発` payload へ
  shape 契約を入れる / (c) 現状維持 (運用ガードとして割り切る)。成果物影響 = (c) のままなら
  表示上 supersede の行を再発として台帳へ入れられ、型別の件数と監査対象集合が歪む。
  推奨 = (c) 現状維持 + 再訪条件 (誤用が実際に 1 件でも観測されたら (a))。
- {{T:dry-run-after-bytes}} **P3・新規・ユーザー裁定待ち**: `tools/spool_fold.py --dry-run` は
  target の before/after hash だけを出し、after bytes も diff も出さないため、実 canonical への
  挿入結果を land 前に byte で目視できない。本 wave は独立計算で hash 照合して代替したが、
  毎回書き捨ての probe を要する。選択肢 = (a) `--dry-run --show-diff` を足す / (b) 現状維持。
  成果物影響 = (b) のままなら台帳への挿入結果の事前確認が書き手の自作 probe 頼みになる。
- {{T:dev-wave-l15-budget-headroom}} **P3・新規・ユーザー裁定待ち**: `DW-M08` へ
  「期待 node は完全集合」を 1 行入れる案が **3 度目の見送り** ([T-714]、[T-726]、本 wave)。
  実測は `docs/dev-wave/**: L1.5 unique footprint 9773 bytes > 予算 9566 bytes` で 207 bytes 不足。
  上限引き上げはしない方針なので、L1.5 集合から陳腐化ルールを外すかテスト化して空ける作業が要る。
  選択肢 = (a) L1.5 の棚卸し wave を起票 / (b) F138 の恒久対応が台帳側にある以上、
  reference への明文化は諦める。成果物影響 = (b) のままなら同じ MISMATCH を 4 例目以降も踏む。
