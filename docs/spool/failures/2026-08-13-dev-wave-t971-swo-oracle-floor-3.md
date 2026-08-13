---
schema: izanagi-spool-v1
ledger: failures
authored: 2026-08-13
wave: dev-wave-t971-swo-oracle-floor
seq: 3
---

## 新規

### {{F:new-preflight-reintroduces-opaque-failure}}. 不透明な失敗を塞ぐ wave が、自分の新設した前段で同じ不透明さを作り直した [恒真ゲート] [防壁の射程誤認]

- 事象: 「床値 job が oracle 不可用の理由を成果物に残さない」を塞ぐ実装で、同じ wave が新設した
  依存 preflight (共有 cache の可視性・`masstree` の実在・HEAD 照合・`config.h` の regular file 性) が
  素の `FloorCampaignError` で倒れる形になっていた。汎用 JSON へ落ちるため、構造化診断も
  private 射影も通らない。**計算ノードで最も起きやすい失敗要因がまさにこの新経路を通る**ため、
  修正後も症状 (理由が残らない) がそのまま再現しうる状態だった。
- 根本原因: 検査の中身は fail-closed で正しく、欠けていたのは「失敗理由が残るか」だけだった。
  正しさレビューの視線は受理集合と fail-open だけを見るため、
  「この検査が落ちたとき何が記録されるか」は素通りする。親の裁定も、
  診断の対象を**既存の**不可用経路に限定しており、wave が新設する前段を射程に入れていなかった。
- 恒久対応: {{D:new-gate-must-not-reintroduce-opaque-failure}} —
  不透明な失敗を塞ぐ wave では、その wave が新設した前段の検査についても
  失敗が構造化されて残ることを実装レビューの必須項目にする。
- 再発検知: 依存 4 要因・toolchain 3 要因それぞれについて、private artifact と exact detail code を
  固定する回帰テスト (`test_production_floor_dependency_preflight_failure_persists_private_attempt`、
  `test_production_floor_toolchain_preflight_failure_persists_private_attempt`)。
  加えて未知 detail code を拒否する検査を置き、閉集合から外れた失敗が黙って通らないようにした。

### {{F:optional-marker-root-degrades-guarantee}}. 記録機構の置き場所が未設定でも例外にならず、保証が条件付き機能へ退化した [恒真ゲート]

- 事象: 強制終了時に停止位置を残すための phase marker を新設したが、置き場所の解決関数が
  未設定時に例外ではなく `None` を返す形だった。marker 書込みが全て条件付きになり、
  **置き場所未設定なら marker ゼロのまま oracle と build が走る**。さらに marker は
  最初の関連 subprocess (compiler の版取得、依存の HEAD 取得) より**後**に書かれており、
  その手前で殺されると何も残らなかった。実装報告は「marker を備えている」と書いていた。
- 根本原因: 新設した保証の発火条件を、実装が既定で満たさない側に倒していた。
  `DW-G04` は条件付き機能について「発火条件を満たす既存 artifact path か計測 ID を
  brief に書ける場合だけ実装する」と定めるが、本 wave は marker を無条件の保証として
  裁定しながら、実装は条件付きのまま通した。
- 恒久対応: 規律 {{D:diagnostic-emission-never-masks-original-failure}} の (c)
  「いずれの経路でも非ゼロ終了する」と同じ考え方を置き場所解決へ適用し、
  production 経路では未設定を fail-closed 例外にした。marker は最初の関連 subprocess より
  前に書く。
- 再発検知: 置き場所未設定で toolchain / oracle / build が呼ばれない負例
  (`test_production_floor_requires_staging_before_toolchain_or_oracle_or_build`) と、
  preflight marker が両 probe より先に存在する ordering 検査
  (`test_production_floor_preflight_marker_precedes_toolchain_and_dependency_probes`)。
