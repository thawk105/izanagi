---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-08-09
wave: dev-wave-provenance-model-switch-rule
seq: 1
title: provenance 規約へ /model 切替後の unknown 条項と文字集合外 slug の決定的変換を入れた — 予算を上げず意味保存縮約 3 箇所で捻出し総量は 17 bytes 減 (docs のみ、受入 7727 passed / 20 skipped、branch worktree-dev-wave-provenance-model-switch-rule)
---

## 本文

- **裁定の実装。** 2026-08-09 /rulings の発話「推奨通りで」で確定した 2 件 ((i) `/model` 切替後の
  `unknown` 条項追加、(ii') 文字集合外 slug の決定的変換 (a) の追認) を `docs/ai-provenance.md`
  へ入れた。逐語控え = repo 外 `rulings-inbox/2026-08-09-provenance-model-switch-rule.md`
  (「以後このファイルは済み」と追記済み)、台帳ポインタ = worklog (348) の未採番 2 問のうち (1)。
- **(ii') は共通則へ上げた。** 変換規則を `model` 固有ではなく
  `product`/`model`/`reasoning`/`scope`/`reason` 共通の文字集合則の直後に置いたため、
  `model` の「表示名だけなら小文字化し空白を `-` に置換する」と `reasoning` の
  「同じ規則で正規化する」を落とせた。規則本体は「外れる表示値は小文字化し、非適合文字を `-` へ
  替えて連続と前後を畳む」で、`claude-opus-5[1m]`→`claude-opus-5-1m` を例に置いた。
  この出力が main に land 済みの commit の実値と一致することは `git log --grep` で実測した。
- **予算が本 wave の主たる制約だった。** 着手時点で entry 6,287/6,300、family 8,994/9,000 =
  **空き 6 bytes**。予算引き上げは禁止 (D110 決定 2、自己改善契約) なので意味保存縮約で場所を
  作った。縮約 3 箇所 = (a) trailer 位置の二重記述 (「message 末尾に」と「最終段落に置き」)、
  (b) `model`/`reasoning` に分かれていた正規化規則、(c) セッション URL 条項の理由句。
  結果は entry 6,270、family 8,977 で、**条項を 2 つ足したうえで総量は 17 bytes 減った**。
- **(c) で落とした理由句をここへ移す。** 削ったのは「履歴に永続し公開時に session の存在と ID を
  露出するため」で、規約本文には裁定日 (2026-07-17 ユーザー裁定) と義務・機械抑止だけを残した。
  義務は 1 文字も弱めていない。理由が decisions にも archive worklog にも無いことを grep で
  確認したうえで本項へ移した (自己改善契約 routing 5「入口は命令と dispatch、decisions は採用理由」)。
- **非遡及規定には触れていない。** family の縮約余地として最大なのは非遡及の三重記述だが、
  [T-619] が 2026-08-07 の裁定で「非遡及規定の改訂と等価縮約 net −168 bytes」を受け取っており、
  その枠は未消化のまま carry である。D230 の `applies_R` 統一で意味自体が変わる予定でもあるため、
  本 wave の縮約対象から外した。
- **依存 gate の生死を実編集で測った。** 本 wave が寄りかかる 2 つの予算 gate を、実際に byte を
  足して発火させた — entry 6,308 で赤 (`> 予算 6300`)、family 9,015 で赤 (`> hard ceiling 9000`)。
  いずれも `git checkout --` で復元し、bytes 一致と `check_docs` rc=0 を再確認した。
  monkeypatch も模擬も使っていない。
- **新条項に機械 gate は付かない。** checker は `/model` 切替を観測できず、変換後の値が正しい変換の
  結果かも照合できない (`claude-fable-5` のように形式が妥当な誤りは素通りする)。したがって
  gate 新設は不成立、変異 matrix も実装面差分ゼロで対象なしとした。防壁は規律と人間の指摘だけ
  である、という既存の認識は変わらない。
- **子は使っていない。** docs-only であり、規約自身の実装面定義 (「docs-only、ログ・計測結果・
  凍結記録だけの変更は対象外」) により Codex `role=author` は不要。裁定文の「Codex author の
  軽量 wave」は実装面を伴う想定の表現と読み、実装面 path を 1 byte も触らないことで整合させた。
- **[T-657] 側の未 land fragment との関係。** 同件の未採番項 (slug `provenance-model-switch-rule`)
  は `worktree-dev-wave-t657-t660-g2-activation` の未 land fragment が持っており、それが land
  すると新しい T が起票される。条項化自体は本 wave で完了しているので、その T は起票と同時に
  完了扱いにしてよい。本 wave からは他 wave の placeholder を参照できないため、ここへ書き置く。
- **段 8 の改善候補 2 件は不採用。** (1) 予算逼迫下の docs wave で「縮約枠が別タスクへ裁定で
  割り当てられていないか」を機構名で検索する義務、(2) wave startup gate の submodule 未初期化を
  `DW-O08` の初期化で解消してから再走してよいと明示する。いずれも本 wave の 1 例だけで、
  `DW-G03` の「族一般化には独立 2 例」を満たさない。常時読量 gate の予算も圧迫するため、
  再発したら起票する。
- **検査。** `check_docs` rc=0、全史 provenance 監査 rc=0 (2,024 件・新規違反なし、既知 30 件)、
  **受入全走 7,727 passed / 20 skipped、rc=0** (1,616.54 秒、request `898073.nqsv`、
  計算ノード dispatch、対象 tip = local main `f8916b69` 取り込み後の merge commit)。

## 次の一手差分
