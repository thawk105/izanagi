# [T-1871] 段 4 裁定と plan v2 (2026-09-20 19:35 JST)

裁定 inbox 再走査: wave 開始後の main (42096593 → 800178b3) は T-2700 の land のみ。対象 doc・phase3.md・README に差分なし、
T-1871 / D1441 に関する新裁定なし。

## 所見の裁定 (real / refuted、採否)

| 所見 | 判定 | 採否 | 対応 |
|---|---|---|---|
| A-1 / B-4: 「1 byte でも追記すると 8b oracle が refuse し受入全走が赤」は過大。T-080 adapter (active-valid receipt) 発火時は `s8b_oracle_driver.py:239–325,466–506` の static adapter 経路で直接 verifier を呼ばず、source closure は H_mig blob と照合する | real | 採用 (must-fix) | 一般化を「現 root を読む直接 verifier `s1_known_axes_freeze.verify()` と、それを実行する `test_historical_current_use_matches_real_reconstruction` (1055 行) が source 不一致になる」に限定。追補・worklog・phase3 pointer から「全 8b 経路」「唯一の形」を削る |
| A-4: 語義改訂の発効と D1012 の休眠解除の発火を分ける。承認記録を 3 つに分けて書く | real | 採用 (must-fix) | 追補に「本追補は語義改訂を発効させるが、旧 headline・対照 3/4・段 6 (a)〜(e) の休眠を解除しない」と書き、承認記録 = 語義変更の承認日 2026-09-02 (D1441) / 追補作成の根拠 = 本依頼 / 反映 = 本追補の日付付き commit |
| A-5 / B-2 / B-5: phase3.md の pointer に将来規則 (`addendum-N`)・「2026-09-20 以降 pin される」・「唯一の形」を書かない。不在 path は check_docs で赤 (B-4 `tools/check_docs.py:1156,6769`) | real | 採用 (must-fix) | pointer は実在 file への具体リンク 1 文だけ。追補 §4 の「以後の改訂は追補 2 として別 file」を削る |
| B-2: 五節構成の圧縮 (冒頭 + §0 統合、§3/§4 を末尾へ統合) | real | 採用 (nit) | 追補を §0〜§3 に圧縮。壁の再説明は出所リンク程度に |
| B-3: 命名を `erratum-1` に寄せる | real | 一部採用 (nit) | 依頼が「追補」と呼ぶので file 名は `addendum-1` を維持。README entry と追補冒頭に「D1789 の erratum 系列と同じ別 file 訂正形」と書き、`erratum` 検索でも当たるようにする |
| A-2: D1441 逐語で足りるが適用対象・未確定事項を明記 | refuted (P2 採用条件の確認) | 採用済み | 「2026-07-12 追記『旧 headline 主張の扱い』の『非列挙』を D1441 の意味で読む」と接続し、「予算・生成器・判定手続きを確定せず、特定軸の条件充足を判定しない」を明記 |
| A-3: 休眠・(c')・B-5 と矛盾なし。論文ストーリー 2026-09-14 1549〜1550 行の「未裁定」は陳腐化 | refuted | 記録のみ | 論文ストーリー次版は scope 外。worklog の次の一手に「次版で D1441 反映」を 1 行残す (起票せず) |
| B-1: 「D1441 の記録で足りる」 | refuted | — | 追補は実施。研究前進は「D1441 を対象事前登録の改訂として参照可能にする」に限定し、「食い違いを解消した」とは報告しない |

## plan v2 (成果物)

1. `docs/phase3-main-experiment-addendum-1.md` (新規、40〜60 行): 冒頭 (対象 path + sha256 + 発行日 + 承認記録 3 分割 + bytes 不変の理由 (直接 verifier の実測に限定)) → §1 対象箇所の逐語と適用範囲 → §2 追補本文 (D1441 4 点逐語 + 非拘束の意図) → §3 発効するもの / 動かさないもの → 末尾 2 行 (対で読む、限界)。
2. `docs/README.md` 19 行の直後に 1 entry (実在 path、erratum 系列との対応を明記)。
3. `docs/phase3.md` 分離節末尾 (294 行の直後) に 1 文: 実在 file への具体リンクのみ。
4. `python3 tools/check_docs.py` 緑、`docs/phase3-main-experiment.md` の sha256 不変を実測。
5. 段 6: 独立 read-only レビュー 1 本 (luna) → fix は親 (docs-only) → 受入全走。変異 matrix は実装面 0 で免除 (DW-S04)。
   実 repo を読む test (`test_s1_known_axes_freeze.py::test_historical_current_use_matches_real_reconstruction`) は段 7 前に実走し worklog へ書く。

## 事前登録 (変異): 実装面 0 → 免除。代わりに段 6 で「対象 doc の sha256 = e544de19… 不変」と上記 test の緑を実測する。
