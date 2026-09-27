# [T-1072] 材料の逐語経路 (diff_region) の文字集合制限 — wave 記録

authority: none
default_effect: no-state-change

可変状態の正本ではない。worklog エントリ (本 wave の fragment) と commit が正本。

## 1. 依頼と裁定

- 依頼 (2026-09-27): 2026-08-25 /rulings 全件の択 (a) のとおり、材料の逐語経路に文字集合の制限を掛け、外側の理由文字列も
  同じ変更単位で閉じる。正例と負例を同じ単位で置く。規律 2 を緩めない。本題だけ、他の gate・検査・台帳・一般化は scope 外。
- 裁定: 2026-08-15 (diff_region 経路を閉じる、範囲は表示直前の無害化に限る、WAL 改変耐性は別問題) と 2026-08-25 択 (a)。
  起票は `docs/archive/worklog-phase3-0813-542-543.md` の [T-1072]、裁定は同 `-0816-568.md` と `-0825-944.md`。

## 2. 実装 (commit c88034e38 実装、c415e1da0 テスト fix)

- `orchestrator/critic/digest.py`: 既存の文字集合検査 `_validated_diff_quarantine_text` に許可集合の引数 (既定 = 従来集合) を足し、
  region 用 wrapper `_validated_diff_quarantine_region` を置いた。region の許可集合 = 従来集合 ∪ {`@`}
  (正当な `<path> @@ -N +M` 形のため)。renderer の `marker=... / region=...` 行だけで検査し、許可外は
  `diff-quarantine-region-invalid` に置き換える。空・欠落は従来どおり `region=?`。
- loader の値、reject record の件数・subtype・variant・判定は変えない (表示直前限定、規律 2 不変)。
  reason / evidence の許可集合は不変 (既存の `at@sign` 拒否テストが固定)。
- 外側の理由文字列 (検疫 record の `reason`) は T-1047 で loader・renderer とも既に閉じており、コード変更なし
  (T-1047 は 2026-09-27 に「実装済み」で取り下げ、D2257)。外側の `STAGE_ABORT.payload.reason` は固定値 `diff-quarantine` との
  一致で選別される。同じ record に不正な region と reason が同居する負例を同じ変更単位に置いた。
- テスト (`orchestrator/tests/test_critic.py`、6 関数 29 ケース):
  - 正例: 実 producer (`DiffQuarantine`) の `_mk_digest` 13 箇所の region 形を 15 ケースで WAL→loader→renderer に通す
    (各呼び出し箇所を通すが、同じ region 文字列を返す群内の分岐までは識別しない)、`@` を含む path、段 4 の定数 4 種の直構築描画、
    空文字と WAL の field 欠落で `region=?`。
  - 負例: 実 producer を通した `cc/[outside].cc` (loader 前に `[` の到達を assert、同 record の reason も不正化)、
    直構築の改行・tab・ESC・双方向制御・`[`・非文字列。

## 3. 到達条件 (段 3・段 6 で限定した主張)

- 攻撃者制御の値が region に入るのは、`DiffQuarantine` へ外部 diff を直接渡した場合の `+++ ` 行の file path だけ。
  通常の段 4 driver は固定 `source_rel` から diff を自前で組む (`orchestrator/campaign/p3_s4_loop.py` の `make_working_diff` 呼び出し周辺)。
- parser は LF で行を分け、行末 CR と tab 以降を落とすので、改行・tab は file path に届かない。負例は届く文字 (`[`) で作った。
- subtype / template_diff_id / genome に外部 diff の文字列が届かないのは、確認した実行経路と WAL 非改変の範囲に限る
  (`Genome` 型自体は任意文字列を受ける)。
- 実 WAL 154 本 (主 checkout の `output/campaigns/*/runs/` と過去 wave の submit-tree、実体重複除き) に diff 検疫 payload は
  0 件 (2026-09-27 走査)。これは実運用での正当値の網羅証拠には使わず、正例は producer 列挙と実 producer 経由のテストで取った。

## 4. 検証の実測

- 焦点走 (15 file、計算ノード dispatch): 実装 commit 後 2,473 passed / 3 skipped / rc=0、fix 後も同数で rc=0。
- 変異 (独立 clone、`tools/mutation_worktree.py` dispatch): §5。
- 受入全走: 本記録の commit の後に行い、結果は land の受領証に残る。

## 5. 変異 matrix

- 本走 (独立 clone、固定 commit c415e1da0、spec sha256 `ba92dad4…`、`mutation-spec-final.json`): 6 / 6 KILLED
  (MISMATCH・SURVIVED・TIMEOUT 0、baseline 緑)。要約と results 本体の sha256 は `mutation-summary.json`。

| ID | 変異 | 分類 | 本走の赤 | M0 を引いた固有 node | drift なしの side run |
|---|---|---|---|---|---|
| M0 | digest.py の comment 1 語 (対照) | 対照 | 64 (= drift 核) | 0 | (走らせていない) |
| M1 | renderer の region 検査を外し生値表示 | 負例 | 70 | 6 (直構築の負例) | 7 (WAL 経由の負例を含む) |
| M2 | region 集合から `@` を外す | 負例 | 64 | 0 | 2 |
| M3 | 共通集合に `@` を足す (reason の受理拡大) | 負例 | 65 | 1 | 1 |
| M4 | 空・欠落 region も検査に通す | 負例 | 65 | 1 | 2 |
| M5 | region 検査が常に sentinel (過剰拒否) | 正例側 | 68 | 4 | 20 |

- drift 層: digest.py は contract-loader 閉包に入っており、bytes が HEAD と違うだけで test_critic.py の 64 node が赤になる
  (comment だけを変える対照変異 M0 で直接測定。5 変異の赤の共通部分とも一致)。WAL を admission 経由で読む今回の新テスト
  (P-a・P-b・N-a・WAL 欠落ケース) もこの層に入るため、harness 上の固有証拠は直構築テストだけが担う。
- probe (全件 SURVIVED 期待): 各変異の赤 = M0 の核 64 件 ∪ 事前登録の期待集合、に完全一致 (期待外 0 件)。
- M2 (region 集合から `@` を外す) は狙いの 2 node が両方 drift 層に入り、harness 上は M0 と同じ集合になる。
  固有証拠は下の side run が担う。
- side run (harness 外の証拠): 変異を commit した使い捨て detached worktree で test_critic.py だけを dispatch 実行
  (commit 済みなので drift は起きない)。baseline 169 passed。M1 7・M2 2・M3 1・M4 2・M5 20 node が赤で、
  5 変異とも事前登録の期待集合と完全一致。

## 6. scope 外の残余 (実装していない、起票もしない)

依頼が「本題だけ・一般化は scope 外」と定めたため、次は実装せず記録だけにする。どちらも実害 (攻撃者制御の値の到達) は測っていない。

- trace 由来の key と integrity notes が critic digest に逐語で表示される (`orchestrator/critic/digest.py` の rejections 節の
  cycle / integrity 行)。2026-09-26 の持ち越し整理 (D2257) が T-1072 を残した根拠はこれだったが、起票の定義する材料 field
  (diff_region / subtype / template_diff_id / genome) の外にある。
- 検疫以外の `STAGE_ABORT` の外側 reason (コロン前) が digest に表示され、文字集合検査は無い。T-1047 の「外側 reason」は
  検疫 reason を指していた。
- 両者を閉じるなら、到達性 (攻撃者制御の値が届くか) の実測から始める別の変更単位になる。

## 7. 成果物

job dir `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t1072-material-path-charset/` (repo 外): brief・段 2 plan・段 3 相談 2 本・
段 4 裁定・実装/fix 報告・段 6 レビュー 2 本と焦点再レビュー・変異 spec と結果・side run 結果。
