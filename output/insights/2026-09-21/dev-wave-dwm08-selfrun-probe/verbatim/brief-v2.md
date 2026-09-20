# 段 1 brief v2 (段 6 レビュー A の所見を反映、2026-09-21 07:58 JST。v1 は brief.md に残す)

1. **新事実 (承認前提を覆す):** 依頼の中核は着地済み。entry 1774 (`docs/archive/worklog-phase3-0921-1774.md`)・D2195 (2026-09-21)、commit 993d2fc5f / 6d600f0a6 / 618fb8501 (docs のみ)・記録 33de1a3ea、fold 済み (FOLDED.md 5133–5134、tested_tip 4566c64b4)。
   **実測値の出所は食い違う (v1 の「同一」を撤回):** 依頼文 = 「20 変異 1 分」、D2195 理由 = 「20 変異で 2 分」。fig13 job dir の mtime では `login_probe.py` 20:19:35 → `login-probe-2.log` / `mutation-spec-v3-final.observed.json` 20:21:05 (≤ 90 秒、2026-09-20)、初回 `login-probe.log` 20:19:03。両者はこの mtime の粗い読みで、どちらかへ統一しない。「着地前の写し」は依頼文の実測値・要素が先行 wave の依頼 (`dev-wave-wall-decomp/verbatim/origin.md`) と同型であることからの判断で、起票時点は証明していない。
2. **研究前進:** 土台 (dev-wave 所要)。所要分解 (entry 1774) で変異 probe+final は impl wave wall の 19〜24%。本 wave の最小差分 = 依頼の手順のうち D2195 / DW-O19 で未被覆の 3 要素 (注入先・起動方法・復元後の clean) と skip の名指しを DW-M08 に収容し、self-run の観測を dispatch final の対象 commit へ束縛する。
3. **被覆表 (v2、レビュー A 所見 1 を反映):** 被覆 = 変異ごとの注入・FAIL / ERROR の観測・正規化 (DW-M08)、sha256 照合 + 復元 (DW-M08 + DW-O19)、`--collect-only` 同形式照合 (DW-M08)、node 抽出の一般契約 (F71)、dispatch final (DW-M08 / D2195)、parametrize・fixture・環境変数・import 副作用・対応不明の fallback (DW-M08)、完全一致 / KILLED (不変)。
   **未被覆 → 収容 (commit 956cce1c9):** (a) 注入先 = 「対象 commit の木」(DW-M07 の source-repo と同じ commit へ束縛)、(b) 起動 = 「`PYTHONPATH=. python3` の自走 harness」、(c) 復元後の「`--porcelain` 空」照合 (DW-O19 の porcelain 空確認は変異前、bytes 照合は対象 file だけ)。
   **意図的に固定しない:** 抽出 regex (harness ごとに FAIL 行の形が違う: fig13 は `FAIL <basename>::<fn>`、test_check_docs は `FAIL <fn>[label]` で `::` なし)。実測値 (D2195 理由が持つ、docs leaf に日付付き逸話を置かない)。
4. **skip (commit 002f926f4):** 規範上は「対応不明」に含意される具体例の明示であり、新しい防壁ではない (レビュー A 所見 4・10)。効果は「skip 持ち file を self-run へ投入して final で MISMATCH になる経路の見落とし防止」で、空振りの回数は未実測 (所見 9)。機序: `skiputil.skip()` は素の runner で `Skip(Exception)`、`except Skip` を持たない harness (test_check_docs.py::_run) では ERROR に数えられ pytest の SKIPPED と食い違う。`skipif` は mark を無視して実行、`pytest.skip()` 直呼びは自走が中断。`--collect-only` 一致では検出できない。帰結は MISMATCH (fail-closed) で偽 KILLED ではない。
5. **予算:** 収容 +約 61 bytes は D782 手順 1 段目 (既存記述の削減) として DW-M08 内の CJK 隣接空白 (58) と段落内改行 (9) を同 file M05〜M07 と同じ詰め書きに揃えて捻出。空白・改行を除いた差分は追加語 3 か所 + 助詞 1 字 (`verbatim/semantic_diff_002f926f4_to_956cce1c9.txt`)。L1.5 9681 → 9688 (002f926f4) → 9689 (956cce1c9) / 9696、L1 10623 / 10625 不変、上限不変、check_docs 違反なし (3 回)。
6. **pin 追随:** 不要 (レビュー A 所見 8 で追認)。`check_docs.py` / `test_check_docs.py` は mutation.md を節 ID 在庫・dispatch 配置・層予算で束縛し、DW-M08 本文の literal pin なし。3_750 / 25_200 は `_build_min_repo()` の合成 fixture への assert。→ 実装面差分ゼロ、Codex author なし (D95 docs-only 例外)、変異 matrix 免除 (DW-S04)、受入全走は免除しない。
7. **D2195 本文との差 (所見 12):** D2195 は fix 1 前の条件「FAIL + ERROR 集合 = `--collect-only` 集合」を保持し、着地した DW-M08 は「全 node の照合可能性」と「変異ごとの失敗観測」を分ける。canonical は追記のみなので D2195 は直さず、worklog で相違を明記する。
8. **不変条件:** 完全一致要件 (DW-M08 / F33)・KILLED 判定・DW-O19 の義務・規律 2 を変えない。gate・台帳・一般化を足さない。予算上限を動かさない。
9. **成果物:** docs commit 2 (002f926f4、956cce1c9)、insight (依頼逐語・brief v1/v2・レビュー逐語・被覆表)、worklog fragment。新 D は起票しない。
10. **分割方針:** 軽量版。段 2・3 省略。段 6 = 独立 read-only レビュー 1 本 (済、NO-GO) → fix (親、docs-only) → 焦点再レビュー 1 本 (DW-O16 対応表付き)。
11. **条件表:** O08 / O09 / O10 / O11 / O13 / O19 不成立。O12 は不成立 (裁定 P1/P2 と実行は一致、v2 は段 6 の fix として追加)。O16 成立 (焦点再レビュー直前に読了)。

## 訂正 (焦点再レビュー A 後、2026-09-21 08:05 JST)

- 項 1 の mtime: `login_probe.py` 20:19:35、`login-probe-2.log` / `mutation-spec-v3-final.observed.json` 20:21:05 で差は 90 秒 (2026-09-20)。初回 `login-probe.log` は 20:19:03。これは file 更新時刻の差であり、20 変異全体の実行時間の上限や「1 分」「2 分」の算出由来は確認できない。両記述は統一しない (「≤ 90 秒」の表現を撤回)。
- 項 5 の削減内訳: 収容 65 bytes は DW-M08 内の CJK 隣接空白 58 bytes と段落内改行 6 bytes の削減で捻出し、commit 956cce1c9 の純増は 1 byte (DW-M08 1177 → 1178)。累計は 1170 → 1178 (+8)。「改行 9」は圧縮余地の見積り (compress_estimate.py) で、実際に落とした改行は 6。
