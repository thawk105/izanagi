---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-08-06
wave: dev-wave-t522-admission-registry
seq: 1
title: [T-522] Pegasus admission registry を data 正本へ移し hook と checker を投影にした — 規範・手順・防壁の食い違い 2 件が現に存在したと実測した (コード + docs、受入 6606 passed、branch worktree-dev-wave-t522-admission-registry)
---

## 本文

- **ユーザー裁定 (2026-08-05 /rulings、択 (b) + grandfather 追認) の実装。** admission registry を
  `tools/pegasus/admission_registry.json` へ移し、hook と `check_docs.py` を共有 validator 経由の投影に
  した。設計は {{D:pegasus-admission-registry-canonical}}。
- **段 1 の実測で、規範・手順・防壁の食い違いが現に 2 件存在した** (F122 が「検査が無い」と書いた状態の
  実害)。(a) runbook §7.0 の `unknown` 表は `submit_silo_ladder_rung1.sh` を「login で外部 3 repo を
  clone」と列挙する一方、registry は `local-ok` で hook が許可していた。(b) F122 の当該事例である
  `tools/pegasus/README.md` §3 が、hook が拒否する login 直実行の collector 手順を書いたままだった。
  受理集合は変えず、(a) は grandfather の明示、(b) は手順の訂正で閉じた。§7.0 の表から切り離された
  孤立行も表へ戻した。
- **敵対レビューが親の設計を 1 つ差し替えた。** README の command 行を解析して実行 site を推定する案は、
  同じ手順を inline code や平文へ移すだけで逃げられると指摘され、宣言表 + site タグ付き block へ
  置き換えた。親 brief の「registry 異常時は全 Pegasus path を拒否する」も射程過大と指摘され、
  「正しく LOGIN/SUSPECT と判定され parser が実行 target と認識した綴り」に限定した。
- **fail-open の窓を実測で 1 つ潰した。** hook が module 初期化で例外を漏らすと process は rc=1 で死に、
  Claude Code の hook 契約では rc=2 以外を遮断しないため command が通る。実 hook を subprocess 起動した
  親の probe で、正常 rc=0 / JSON 不在 rc=2 / JSON 破損 rc=2 / 復元 rc=0 を確認した。
- **親が独立に等価性を検査した。** `git show <base>:hooks/guard_bash.py` を ast で評価して JSON と比較し、
  24 entry × 4 field の完全一致を確認した (実装子のコードも新 loader も使わない経路)。
  class 内訳は local-ok 5 / dispatch-required 10 / unknown 9。
- **変異 matrix 11 本: KILLED 9 / MISMATCH 2 / SURVIVED 0 / TIMEOUT 0、baseline PASSED。**
  MISMATCH 2 本 (M10 = JSON の class 1 件書き換え、M11 = canonical bytes 検査 + class 検査の二層同時変異) は
  **事前登録した赤がすべて実際に赤になった上で、予測しなかった層も赤くなった**もので、検出漏れ方向の
  ずれではない。M10 は hook 側の綴り検査 7 本が、M11 は checker 側の loader 検査 1 本が追加で落ちた。
  事前登録どおり冗長 gate として記録し、期待値を結果に合わせて書き換えることはしなかった。
  なお「部分成功を返す」単独変異は canonical bytes 検査に mask されるため、二層同時変異 (M11) で裏を取った。
- **受入全走 6,606 passed / 1 failed。** 赤は本 wave の差分が到達しない
  `test_s8c_preregistration_invariant.py` 1 件で、`git cat-file --batch-check` の 15 秒 timeout。
  同 file 単独では 8 passed / 29 秒で再現せず、F57 の再発として記録した ({{T:s8c-git-timeout-under-load}})。
- **scope 外の real 所見 4 件を裁定パッケージとして返す** (下記 新規)。加えて**報告 1 件**: 正本 JSON が
  壊れる・消える・権限が落ちると、現在 login で通っている 5 本 (`dispatch_compute.py` /
  `fetch_third_party.py` / `submit_certify.sh` / `submit_floor.sh` / `submit_silo_ladder_rung1.sh`) も
  拒否される。安全側だが可用性は下がるため、許容しない場合は別設計が要る。
- 逐語 (プラン、敵対レビュー 2 本、実装・fix 報告、焦点再レビュー) と変異台帳は
  `output/insights/2026-08-06_t522-admission-registry/` に凍結した。

## 次の一手差分

### 完了

- [T-522] admission registry を `tools/pegasus/admission_registry.json` へ移し、hook と
  `check_docs.py` を共有 validator 経由の投影にした。未実測 4 本は `legacy-admitted (未実測)` の
  まま grandfather 追認を維持し、docs へ明示した。設計は {{D:pegasus-admission-registry-canonical}}。
  remaining: none
  base: 4337db397d68ba9627108303c04bf1087036d5a8957811f8a6bd136c86796e05

### 新規

- {{T:s8c-git-timeout-under-load}} **P2・新規**: 全走 48 worker 下で
  `s8c_preregistration._batch_oids` の `git cat-file --batch-check` が 15 秒 timeout で落ちる
  (F57 再発)。[T-327] が `git add -A` 側を session fixture 化 + 180 秒へ延ばした直後の別呼び出しでの
  再発であり、timeout 値の個別延長ではなく「全走負荷下の git 呼び出し」を族として扱う必要がある
- {{T:hook-wiring-skip-gate}} **P2・新規 (ユーザー裁定待ち)**: `test_settings_json_wires_all_hooks` は
  `.claude/settings.json` に `hooks` key が無いと skip する。設定から `hooks` を丸ごと消すと全 hook が
  発火しないのにテストは緑になる。D30 の再設計期の遺物で、現在は配線済みのため skip を廃止できる。
  廃止するか、別の理由で残すかを裁定されたい
- {{T:admission-reason-gate-sync}} **P3・新規 (ユーザー裁定待ち)**: admission registry の
  `reason` / `primary_gate` は docs へ投影しておらず、registry が「入力 cap 未完」とする path の説明を
  docs 側で「実測済みで安全」に書き換えても検出されない。安定 ID (`reason_id` / `primary_gate_id`) を
  投影する設計を採るかを裁定されたい。現に `submit_silo_ladder_rung1.sh` の `primary_gate` は
  「compute work stays in job body」だが実体は login で clone する
- {{T:admission-living-doc-closure}} **P3・新規 (ユーザー裁定待ち)**: 分類 claim を書ける living doc の
  集合が閉じていない。本 wave は `tools/README.md` の誤記を手で直したが、同じ事実を書ける文書を
  閉集合化しない限り再発しうる。閉集合化するか、検査対象を runbook と Pegasus README に限る現状を
  追認するかを裁定されたい
- {{T:barrier-policy-on-old-commits}} **P3・新規 (ユーザー裁定待ち)**: 本 wave 以前の commit へ
  checkout すると新 checker 自体が消え、hook も commit 相対の旧版になる。「commit 相対の旧防壁へ戻る」
  ことを是とするか、「外部の最新 hook を維持する」設計にするかが未裁定である
- {{T:dev-wave-docs-budget-headroom}} **P3・新規 (ユーザー裁定待ち)**: 段 8 の改善候補 1 件
  (`DW-M08` へ「kill 判定は失敗 node 集合の完全一致であり、冗長 gate を落とした部分列挙は
  MISMATCH になる」を明記する) が**予算で入らなかった**。`docs/dev-wave/**` は合計 25,192 /
  hard ceiling 25,200 bytes で headroom が 8 bytes しかなく、`mutation.md` 単体も 3,674 / 3,750 で
  30 bytes 不足した。予算値の変更は独立審査と定められているため実装せず返す。
  (a) 予算の独立審査、(b) 既存節の意味等価な縮約で空ける、(c) 見送り、の択一
