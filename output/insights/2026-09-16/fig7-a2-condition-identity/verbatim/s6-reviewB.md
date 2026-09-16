## 総括

既存 CLI テストの prefix 変更は被覆を下げており、追加テストは「既定 legacy 経路の repo 相対 argv・完全 provenance・publish」の同時検査を補っていない。  
凍結 fig5 の caption は現物 JSON と UTF-8 **1788 bytes 完全一致**し、空白の差もない。  
改訂稿が無い非凍結 legacy 生成は fail-closed。current-full の描画・caption 分岐には変更が波及しない。  
layout 検査は renderer の文字 bbox を比較しており、恒真ではない。変異事前登録は M1・M2・M5 の期待赤理由に訂正が必要。  
以下、P＝[生成器](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-fig5-a2-identity-reissue/tools/plotting/plot_a2_certification.py)、T＝[テスト](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-fig5-a2-identity-reissue/orchestrator/tests/test_plot_a2_certification.py)。pytest は未実走。caption は AST から純粋関数だけを取り出して照合した。

## must-fix

- **主張:** 凍結 prefix への差替えで失った既定 legacy の CLI 被覆を、同じテスト枠内で復元すべき。
  **根拠:** T:1447 が `_fixture` の `fig5_fixture` を凍結名へ変更し、T:1448 の仮 repo に改訂稿が存在しない問題を回避している。T:1578 の新 provenance テストは実 repo と既存 fig5 の画像を使った `build_provenance` 直接呼出しであり、`main`・publish・repo 相対 argv を通さない。T:1400 は非凍結 legacy の CLI を通すが、検査するのは caption の図番号だけ。さらに T:1564 は凍結フラグを直接渡すため、P:910 の配線を検査しない。具体的に `main` が常に `frozen_legacy_caption=True` を渡す欠陥は、これらの assertion では捕まらない。
  **成果物影響 1 行:** 訂正 caption・3 行 provenance を持ちながら画像だけが旧 `fixed … us` 目盛の図を、新規生成しても検査が通り得る。
  **判定:** **real**。既定 prefix と必要な改訂稿を備えた仮 repo で既存の完全性検査を維持し、CLI から描画へ渡る分岐も同じ枠内で確認する。

## nit

- **既定反転による既存経路への影響 — real、fail-open の疑いは refuted。**  
  `_fixture` は引き続き `fig5_fixture`（T:185）。T:1341 の provenance 直接生成と T:1400 の CLI 生成は新たに実 repo の改訂稿へ依存する。改訂稿が無ければ P:808 → P:85 で `FigureDataError`。CLI は P:914 で捕捉して rc=2、P:843 は最終配置 P:849 より前なので、一時画像を finally で削除して終了する。既存の出力があればそれは残るが、新しい不完全 bundle は publish しない。凍結 fig5 と current-full はこの追加 hash を通らない。caption だけ・描画だけの caller、入力検証で先に拒否される負例にはこの依存は及ばない。唯一の `REPO_ROOT=tmp_path` テストは今回凍結経路へ移された。改訂稿を必須入力とする裁定自体には沿っているため、この依存追加は must-fix としない。

- **追加テスト 1 — `test_frozen_fig5_caption_requires_frozen_prefix_entry`（T:1526）。**  
  凍結列挙の無視、旧 caption の変更、closure の caption 比較削除を殺せる。最初に正常 closure を確認し、その後で列挙を空にして特定例外を要求するので恒真ではない。一方、描画目盛や `main` のフラグ配線は見ない。fig5 不在時の skip もないが、現物は存在する。

- **追加テスト 2 — `test_corrected_legacy_caption_describes_effective_conditions`（T:1536）。**  
  fig7・fig8 で訂正文言の欠落、旧文言への復帰、限定文の変更を全文比較で殺す。effects を別値に変更する T:1554 により、現物の効果値をハードコードする欠陥も殺す。測定日時・request ID を期待文字列に焼き込んでいない。期待値の土台は保存 caption なので、保存物と実装の協調変更には追随するが、今回要求された凍結 bytes 保持の下では有効。`name[3]` は一桁番号しか表現できず、複数桁の図番号はこのテストの射程外。

- **追加テスト 3 — `test_legacy_backoff_axis_condition_labels`（T:1561）。**  
  新旧双方の tick、下段 xlabel、内部 artist identity の変化を検出する。実 renderer に layout 検査も行う。`figure._a2_artist_series` は `_artist_series(data)` の記録なので、これだけでは実際の scatter 座標の誤りを殺せない。最大の穴は、フラグを直接指定しており prefix → フラグの配線を検査しない点。

- **追加テスト 4 — `test_corrected_legacy_provenance_tracks_condition_source`（T:1578）。**  
  追加行の欠落・重複、kind 順序、固定 path、scope、誤った hash、旧 2 行の改変を殺す。`_sha(REPO / source)` は実ファイルから独立計算するため恒真ではなく、揮発 hash の焼込みでもない。ただし `set(new)==set(old)` は両方から同じ top-level key を消す変更を見逃す。共通欠落は既存 T:1453 のリテラル全集合が補うが、訂正経路だけの余分な key 等を除き、CLI 経路の保証にはならない。画像は `hash_paths=sources` で旧 fig5 を借りており、訂正図の描画検査ではない。

- **追加テスト 5 — `test_landed_fig7_repo_closure_and_caption_when_present`（T:1601）。**  
  bundle の部分欠落、記録 hash と現物の不一致、caption/artist の再投影不一致、README 未収録を殺す。現物 fig7 があるため今回は skip 条件に入らない。closure は記載された入力だけを検証するため、保存 provenance から `caption_source` 行を取り除く欠陥はこのテスト単独では見逃す。また画像内容と caption の意味的一致や、生成時の CLI 分岐も検査しない。

- **fig6 波及 — 描画・条件分岐の変更という疑いは refuted。**  
  現物 fig6 は `artifact_profile="current-full"`。P:740 の真理値は、current-full なら frozen=False/True とも False、legacy なら frozen=False のみ True。したがって current-full は常に旧 tick/xlabel、caption は P:623 で早期 return、provenance は P:803 で追加行なし。保存 caption も **1995 bytes 完全一致**した。ただし「再生成 provenance まで 1 bit 不変」は保証できない。生成器変更による `generator.sha256` と生成日時は変わる。凍結済み成果物を変更しない要件とは区別すべき。

- **layout の恒真性 — refuted。**  
  P:765 で描画して実 renderer を取得し、全可視 Text の bbox について図外逸脱・隣 panel 侵入・文字同士の交差面積 >1 を検査する（P:771、P:786）。tick と xlabel も対象。T:1377 は同位置の文字を注入し、`overlap` 例外と出力ゼロを要求する。文字と点・線の衝突までは検査しないが、今回の目盛・軸 label の文字重なり検査は実体がある。

## 変異事前登録への指摘

- **M1 — 再照準が必要。** 列挙を空にすると旧 fig5 closure は予定どおり落ちるが、T:1530 の正常確認、T:1585 の旧 2 行 assertion も落ち、仮 repo の CLI は改訂稿欠落で先に rc=2 になる。caption 単一理由を狙うなら、共有列挙ではなく `_caption` 内だけで凍結名を訂正側へ送る変異に限定する。
- **M2 — KILLED は成立、期待 node 数が不正確。** `_caption` 条件反転で旧 fig5、訂正 caption の両パラメータ、凍結負例の正常確認、着地済み fig7 closure が落ちる。先行 hash 層ではなく同じ caption 投影理由なので変異は維持できるが、「2 node」は訂正が必要。
- **M3 — 妥当。** 追加処理だけを除去すれば T:1590 の kind 列 assertion が落ちる。保存済み fig7 は変わらず、closure も必須 3 行を要求しないため、他の既存 node がこの欠落を先に落とす構造ではない。
- **M4 — 妥当。** tick 選択だけを旧側へ固定すれば T:1568 の frozen=False が落ちる。旧 tick はもともと layout を通る文字列であり、caption/closure は tick を見ない。xlabel まで一緒に変更せず、tick のみに注入すれば理由を限定できる。
- **M5 — README を赤理由とする登録は誤り。** 文削除は訂正 caption テストと着地 fig7 closure を落とすが、helper は closure で先に停止する。保存 caption と README は変異で変わらず、逐語収録 assertion 自体は真のまま。caption 文削除を維持し、期待理由を「caption 全文比較＋着地 caption 再投影不一致」へ訂正する。

## 親裁定の誤り

- [s4-ruling.md:78](/work/1/SFC/tanab/dev-wave-artifacts/fig5-a2-identity-reissue/s4-ruling.md:78) の「既定は現行挙動」は不正確。引数省略の互換性は保つが、legacy の既定目盛と xlabel は変わる。
- 同文書 §5 の M1 は共有列挙が provenance にも効くことを考慮しておらず、単一理由性を満たさない。M2 の node 数、M5 の README 検出理由も上記のとおり誤り。
- §4 の「既存テストの期待値を甘くしない」は、assertion の文面だけでは満たせない。今回の prefix 差替えは検査対象を例外経路へ狭めており、既定経路の被覆復元が必要。