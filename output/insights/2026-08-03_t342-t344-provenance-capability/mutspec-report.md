## 総括

変異 spec を作成しました。M01〜M11 と正例 P01 の全 12 件を登録し、登録を見送った変異はありません。

- ファイル: [mutation-spec.json](/work/1/SFC/tanab/izanagi/.claude/worktrees/t342-mut/output/insights/2026-08-03_t342-t344-provenance-capability/mutation-spec.json)
- SHA-256: `1f998c83309f143188d0a72dc3b7126a704a615bcb8354b500eb04878fa93146`
- 見積り: 1 全走 300 秒、baseline + 12 変異で約 3,900 秒
- timeout: 900 秒
- 変更はこの JSON 1 ファイルのみ。commit・add・branch 操作なし
- harness・pytest は指示どおり未実行

一意性は、登録ファイル自身を除く `git ls-files -co --exclude-standard` の全 UTF-8 ファイルについて、各 `old` の `str.count()` が repo 全体・対象ファイル内とも exactly one であることを確認しました。全置換後 source はメモリ上で `compile()` 済みです。

- M01 — [build_admission.py:433](/work/1/SFC/tanab/izanagi/.claude/worktrees/t342-mut/orchestrator/campaign/build_admission.py:433)
  - 2 行の stock 条件全体で exact-one。
  - 手前は context/source の型・canonical body と receipt 曖昧性検査だけで、clean 検査は 441 行目が最初。
  - dirty stock が `STOCK_BASELINE` になる同一理由で、unit node と coder namespace node の2件が赤になります。

- M02 — [build_admission.py:441](/work/1/SFC/tanab/izanagi/.claude/worktrees/t342-mut/orchestrator/campaign/build_admission.py:441)
  - M01 と同じ一意な条件全体を anchor 化。
  - repo pin の照合はこの条件より前にありません。
  - clean だが宣言 commit が `CURRENT_PIN` と異なる source が stock になる理由だけで対象 node が赤になります。

- M03 — [build_admission.py:299](/work/1/SFC/tanab/izanagi/.claude/worktrees/t342-mut/orchestrator/campaign/build_admission.py:299)
  - `authority_nonce` 初期化から exact-type guard までを anchor 化して exact-one。
  - 手前は registered `GeneratorId` の検査だけ。authority の最初の検査は 302〜305 行目です。
  - `True` を実際の sealed・issued token に変換してから既存 nonce 検査へ流すため、`True._nonce` の別例外は生じず、「plain True が受理された」理由だけで赤になります。

- M04 — [buildcache.py:141](/work/1/SFC/tanab/izanagi/.claude/worktrees/t342-mut/orchestrator/campaign/buildcache.py:141)
  - admission を含む `raw` 構築2行を anchor 化して exact-one。
  - 手前は admission の exact type 検査だけで、class を key に束縛する別処理はありません。
  - 4 class の legacy key が同一化する理由で class 集合 node と T-343 golden node が赤になります。

- M05 — [buildcache.py:838](/work/1/SFC/tanab/izanagi/.claude/worktrees/t342-mut/orchestrator/campaign/buildcache.py:838)
  - sidecar validator 呼出し全体を anchor 化して exact-one。
  - 800〜815 行目の検査は request/source 自体の検査で、sidecar 欠落の最初の拒否点は 839 行目です。
  - テストは旧 binary を新 key 配下へ置くため cache miss ではなく、この validator の skip だけで誤 hit になります。

- M06 — [buildcache.py:253](/work/1/SFC/tanab/izanagi/.claude/worktrees/t342-mut/orchestrator/campaign/buildcache.py:253)
  - `admission` field と digest return を合わせて anchor 化し、過去 ledger 内の類似文字列とも区別して exact-one。
  - `_v2_identity` 内でこれ以前に digest を作る処理はありません。
  - 戻り値の preimage は維持し、digest 用 preimage だけから admission を除くため、後段 manifest 検査による別理由を避け、4 class digest の同一化だけを検出します。

- M07 — [buildcache.py:373](/work/1/SFC/tanab/izanagi/.claude/worktrees/t342-mut/orchestrator/campaign/buildcache.py:373)
  - key 集合、admission equality、canonical receipt 呼出しの3 anchor がそれぞれ exact-one。
  - 手前は cache directory と JSON manifest の一般構造検査だけで、admission 欠落の最初の拒否点は 381 行目です。
  - field を optional 化し、欠落時は current admission を coherent fallback として equality・canonicality 検査へ渡すため、直接参照の `KeyError` に mask されません。

- M08 — [ident.py:132](/work/1/SFC/tanab/izanagi/.claude/worktrees/t342-mut/orchestrator/campaign/ident.py:132)
  - `search_config` projection の1行を anchor 化して exact-one。
  - 132〜135 行目の presence 検査は残るため、同じ入力を手前で拒否しません。policy が identity bytes に入る最初の箇所は 140 行目です。
  - representative、screening、backoff/S6、S8a、trigger の5 nodeはいずれも、現行 ID が pre-T343 IDへ戻る同一理由で赤になります。

- M09 — [wal.py:660](/work/1/SFC/tanab/izanagi/.claude/worktrees/t342-mut/orchestrator/campaign/wal.py:660)
  - receiptless terminal 分岐と直後の SHA 検査を一体で anchor 化して exact-one。
  - matching START・variant・active attempt 検査は 660〜670 行目に残ります。
  - receipt がある attempt の SHA 流用検査も維持し、receiptless terminal の場合だけ terminal stage を許すため、splice・duplicate START・receipt reuse は無効化されません。

- M10 — [artifact_admission.py:440](/work/1/SFC/tanab/izanagi/.claude/worktrees/t342-mut/orchestrator/campaign/artifact_admission.py:440)
  - `_inspect_campaign()` の overlay decision return 全体で exact-one。
  - exact identity/hash、WAL parse、build-start count は 440〜480 行目で先に通り、exact overlay member を拒否する最初の decision は 482 行目です。
  - 共通 decision を admitted historical view に変えるため、`classify_campaign()` と全 sink が同じ受理集合になります。登録した6 nodeはいずれも「旧3 campaign が再び材料・certified viewへ入る」という単一理由です。

- M11 — [layer3_report.py:365](/work/1/SFC/tanab/izanagi/.claude/worktrees/t342-mut/orchestrator/campaign/layer3_report.py:365)
  - import block 2件と validator assignment＋後続 `except` をそれぞれ exact-one に拡張。
  - 手前は campaign directory の存在検査だけで、artifact admission の最初の gate は 373 行目です。
  - overlay decision の場合だけ coherent historical raw view に差し替え、通常 admitted decision は変更しません。後段の raw WAL・byte hash 検査（420〜427行目）も残るため、旧 S8a report が描画される理由だけで対象 node が赤になります。

- P01 — [s6_sort_sweep.py:203](/work/1/SFC/tanab/izanagi/.claude/worktrees/t342-mut/orchestrator/campaign/s6_sort_sweep.py:203)
  - S6 resolver の関数宣言全体まで広げ、同形の S8a resolver と区別して exact-one。
  - stock 分岐は 205〜206 行目に残り、machine capability の最初の発行点は 207〜210 行目です。
  - machine resolver だけを `None` 化するため clean stock と opt-in coder は不変。S6 独立統合 node と、3経路を固定する正例 nodeが「registered machine capability の過剰拒否」という同一理由で赤になります。