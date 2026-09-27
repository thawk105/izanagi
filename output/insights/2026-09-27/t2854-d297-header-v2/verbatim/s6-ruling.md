# 段 6 裁定 (fix 1 巡) — 対象 commit 9ceb5519

入力: レビュー A (`out/s6-review-A.md`、正しさ境界、NO-GO)、レビュー B (`out/s6-review-B.md`、過剰・削除と実効性、NO-GO)、親の事前所見 (`parent-findings-s6.md`)。

| # | 所見 | 判定 | 採否 | 放置時の成果物影響 (DW-G05) |
|---|---|---|---|---|
| F1 | P-1 予定集合と実行済み集合の照合が恒真 (A・B must-fix) | real | 採用 | 比較を落とした実装でも pass し、C2' 判定の「予定と実行の厳密一致」が名目だけになる |
| F2 | P-4 `-U/-D __DATE__` probe が `-Werror` で失敗 (親実測、A・B must-fix) | real | 採用 | 実 CCBench の C → C2' 判定が常に拒否になり完了条件に届かない |
| F3 | P-2 discovery が全 entry を列挙・選定確定後も調査を続ける (A・B should) | real | 採用 | 判定 job が 1 起動あたり十数分以上重くなり、2 node 時間の線を超える見込み |
| F4 | P-3 既存の `_assert_proven_repo_absent_macros` の呼び出し位置の変更 (A・B should) | real | 採用 | 既存 caller が複数の不正を持つ入力で受け取る拒否理由が変わる |
| F5 | P-5 V2 は構造的に偽緑へ届かない (A・B) | real | 採用: V2 を登録から外す (再登録しない) | なし (V3 が生成物を覆う) |
| F6 | 判定 job が裁定済み C・C2' を固定値で照合しない (A should) | real | 採用 | 別 OID で走った結果を C2' 判定と取り違えうる |
| F7 | 代表 fixture の不足: `-Werror`・TRACE token の無い target (A must-fix の一部) | real | 採用 | F2 型の実構成差を test が見逃す |
| F8 | 未使用の `discovered`、target 形式の三重検査、正規化 root の重複 (B should / nit) | real | 採用 (局所の削除のみ) | 保守時の判定ずれ |
| F9 | root 正規化が path 境界を見ない (A must-fix) | refuted | 不採用 | 置換される root はすべて検査器自身が新しい `mkdtemp` 下に作る固定幅の一意名 (`src-old`/`src-new`、`b%04d-*`、`g%04d-*`、hydrate の staging) で、互いに接頭辞にならず、commit 済み source や configure が事前にその乱数 path を含むことはできない。A の例 (`<root>-extra`) を作る主体が存在しない |
| F10 | `supply is None` で本体の生成物経路が分岐し、test が production 経路を通らない (B should) | real (性質) | 不採用 (構造変更はしない) | production 経路 (hydrate・masstree 複製・config.h 確認) は実 CCBench 判定 job で実走し、F2 型の差は F7 の代表 fixture で test 側にも写す。本体の再構成は裁定 S3 の範囲を超える |

## fix の仕様 (Codex fix 子へ)

- F1: 比較の結果 (集約した各比較の成功 evidence と、その集約鍵に属する configure の列) から実行済み集合 `{(configure, entry)}` を作り、予定集合と厳密一致を照合する。予定集合は比較の実行前に固定する。test は V9 (予定の最後の 1 件を実行しない単独変異) で赤になる形にする (件数の自己照合 `planned_count == executed_count` だけに頼らない)。
- F2: volatile builtin の probe argv にだけ `-Wno-builtin-macro-redefined` を足す (比較する完全展開・include 活性の argv は変えない)。
- F3: discovery (未選定 protocol の genome 調査) は、その protocol の production target の entry だけを旧新 × TRACE 0/1 で依存列挙する。1 genome で consumer が見つかった時点で調査をやめて選定する。選定 configure の依存列挙は従来どおり全 entry。
- F4: header 用の 4 引数が 1 つも無い起動 (既存 caller) では、`check()` の検査順序を段 5 前と同一にする (`_resolve_commit` → `_assert_proven_repo_absent_macros` 2 回 → ancestor → diff → `_validate_diff`)。header 分岐が有効な起動でだけ現在の順序と条件を使ってよい。
- F5: コード変更なし (V2 の test は生成 header 経由の consumer の正例・負例として残してよい)。
- F6: `run_judge.sh` に C `68106660686232781bca3be792a750d3e19d7a8a` と C2' `40a7f4acb174ca43cb590f40d13847216a1564bc` を定数で持ち、引数の OID と一致しなければ exit 2。
- F7: 正例 fixture に `-Werror` を compile option として持たせ (正例は pass のまま)、`-DTRACE` を持たない target (変更 header を読まない) を 1 つ加えて pass すること。`-Werror` があると F2 修正前の実装が拒否することを自走で確かめる。
- F8: `discovered` を削る。production target の形式検査は provider の返り値を受ける 1 箇所にまとめる。正規化 root は同一 path を 1 度だけ登録する。
- 既存 test の期待値は変えない。段 5 で追加した test は編集してよい (同 wave の未 land test)。test 全体の所要を再測する。

## 追補 (21:0x JST、判定 job 1 回目 31898.nqsv の拒否を受けて)

- 事実: 判定 job 1 回目 (commit de51469e、Elapse 10 秒) は GCC 11.4 / 12.3 とも `source tree に regular file 以外: b'third_party/shirakami'` で rc=1。C・C2' の tree は gitlink `third_party/shirakami` (160000、fb14e659) を 1 件持つ (symlink 0)。
- 訂正: 段 4 裁定 S8 の「symlink・gitlink は拒否 (CCBench では生死確認で問題なし)」は親の事実誤認 (生死確認 driver は tree 照合をせず、単位 11 の probe は gitlink を照合から除外して記録していた)。
- F11 (採用、親の実機 blocker): S8 を「gitlink (160000) は展開・file 照合の対象から除外し、旧新で同じ path 集合と commit OID であることを確かめて report に列挙する。symlink と他の非 regular は従来どおり拒否」に改める。gitlink の変更は既存の diff 検証 (mode 100 系以外を拒否) が拒否し、gitlink 配下の file を読む entry は `-MG` なしの依存列挙で失敗して拒否になるので、除外で比較対象が黙って欠けることはない。合成 fixture に gitlink を 1 つ持たせた正例を加える。

## 追補 2 (焦点再レビュー F1 の後)

- F1 焦点再レビュー: F1〜F8 と焦点走の consumer test 赤 (AST 固定) を closed、F10 は反証なし、F9 に反証ありとして NO-GO。
- F9 の再裁定 (親、refuted を維持): 反例 (`#define P "${CMAKE_SOURCE_DIR}-extra"`) の旧新の値は、それぞれの source root から同じ構成で作られた文字列で、同じ置き場で build すれば同じ bytes になる「置き場由来の差」である。正規化はこの差だけを同一視するためにあり、各側の出力はその側の root だけで置換する。root は検査器が新しい mkdtemp 下に作る固定幅の一意名で、root を含む bytes は root から構成されたもの以外に現れえない (commit 済み source も configure 前の入力もその乱数 path を知らない)。別々の実体が同じ token に潰れるには、一方が root_A 由来・他方が root_B 由来の異なる構成を持つ必要があり、その場合は token が異なって不一致になる。よって偽緑にならない。DW-O16 の 3 巡上限に従い fix は重ねない。
