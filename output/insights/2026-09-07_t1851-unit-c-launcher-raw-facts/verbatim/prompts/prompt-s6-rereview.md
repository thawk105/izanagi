単独段 dispatch: stage=review; sandbox=read-only; parent=/work/1/SFC/tanab/dev-wave-jobs/2026-09-05_t1851-unit-c/s4-adjudication.md

## 必読事項の射影

次を上から順に読む。いずれも絶対パスである。**読めなければ即停止**し、読めなかった path を報告して終われ。

1. `/work/1/SFC/tanab/dev-wave-jobs/2026-09-05_t1851-unit-c/s4-adjudication.md` — 親の段 4 裁定。**4 節 (plan v2 — C1a) と変異事前登録 M1〜M12 が受入基準の正本**。3 節の契約 v2 は次 wave の対象で、本 wave で実装されていないのが正しい
2. `/work/1/SFC/tanab/dev-wave-jobs/2026-09-05_t1851-unit-c/artifacts/t1851-unit-c/s6-review-a.md` と `s6-review-b.md` — 段 6 レビュー 1 巡目 (どちらも NO-GO)。親は全所見を real と裁定した
3. `/work/1/SFC/tanab/dev-wave-jobs/2026-09-05_t1851-unit-c/prompt-s6-fix2.md` — fix2 へ渡した契約 (9 件の修正指示、所有 path、`test_official_perf_closure.py` の 2 guard 条件の式を変えない制約)
4. `/work/1/SFC/tanab/dev-wave-jobs/2026-09-05_t1851-unit-c/artifacts/t1851-unit-c/s6-fix2.md` — fix2 の完了報告 (9 件すべて closed と自己申告)。**自己申告であり検証対象**
5. `/work/1/SFC/tanab/dev-wave-jobs/2026-09-05_t1851-unit-c/s6-fix2.patch` — fix2 の差分 (launcher + launcher test)
6. `/work/1/SFC/tanab/dev-wave-jobs/2026-09-05_t1851-unit-c/s5-s6-fix2-integrated-snapshot.patch` — 統合差分の全文 (実装子 + fix1 + fix2、base `04f06d032` に対する差分)
7. `/work/1/SFC/tanab/dev-wave-jobs/2026-09-05_t1851-unit-c/refs/decisions-verbatim.md` — 確定裁定の逐語 (特に D1113 / D1522)

**統合後のコードは `/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1851-unit-a` にある (未 commit の作業 tree)。所見はここの現物で裏を取れ。**

## 依頼

あなたは統合後の焦点再レビュー (1 本) である。1 巡目の所見 9 件 (A-1、A-2、A-3、A-4 = B-5、B-1、B-2、B-3、B-4、M4 再照準) が現物で閉じたかを検査し、fix2 が新たに持ち込んだ破れが無いかを見る。fix2 の報告を信じず、現物とつき合わせろ。

## 検査の軸

1. **所見ごとの closed / partial / regressed 表。** 9 件それぞれに、(a) 修正の現物 file:line、(b) 検査 node の実在と「他の入力は valid で対象 gate だけを踏む」形か、(c) 判定。partial / regressed には理由と残る修正案を書く。
2. **A-1 の閉じ方。** `_ReservationPolicy` が保持する copy が `dict` の浅い copy で十分か (値が可変 object の場合の別名は問題か、問題なら成果物への影響を 1 行で)。`_capture` が `measurement.keyword_arguments` を一切再読していないか grep で確かめる。
3. **A-2 の閉じ方。** 拒否の位置が `output.seal` より前で、registry の `record_attempt_terminal` が呼ばれないか。`terminal-failure` 申告 + failure None の組合せ (逆向きの矛盾) を通すか拒否するか、どちらであれ裁定 4 節との整合を書く。
4. **B-2 / B-3 の実体同形性。** fake sink の rep record key 集合が `calibrator/runner.py` の `open_measurement_point` が sink へ書く実体の key 集合と一致するか、実 adapter integration node が実際に `reserve_attempt_slot` → `classify_attempt` → `begin_*_observation` → `record_attempt_terminal` を実体で通っているか (monkeypatch / fake で adapter を差し替えていないか)。
5. **B-4 / M4。** public `launch_floor_attempt` の `classification_authority=_CLASSIFICATION_AUTHORITY,` を `ClassificationAuthority(authority_id="caller-selected", authority_policy_sha256="0" * 64)` へ差し替えた変異を、`test_certified_api_owns_classification_authority` が殺すか静的に追え。monkeypatch が launcher module 自身の属性に限られているか。
6. **受理集合と所有外。** `_CERTIFIED_MEASUREMENT_KEYWORDS` 不変、`_owned_post_probe` の argv / timeout / 関数名不変 (spawn-site pin `test_ccbench_spawn_sites.py:212`)、`_checked_reservation_policy` 内の 2 つの `if` 条件式が fix1 の guard 逐語 (`test_official_perf_closure.py` の `_REVIEWED_GUARDS`) と一致したままか、adapter / core / profile / campaign / calibrator 無変更。
7. **fix2 の新規持ち込み。** fix2 差分の中で、1 巡目の所見に対応しない変更 (削除された検査、緩められた assertion、新しい fail-open 経路、期待値の書き換え) を全件列挙せよ。A-3 の指示による `_contains_callable` 検査行の削除は指示どおりだが、削除後に marker が callable を含む入力が本当に非 None gate で拒否されるかを現物で確かめろ。
8. **変異 M1〜M12 の観測 node 表 (再掲)。** 1 巡目で挙がった冗長 gate 遮蔽が解消したか、node 名の変更 (改名・分割) があれば新旧対応を書け。親はこの表で変異 spec を再登録する。

## 出力形式

先頭に所見 9 件の closed / partial / regressed 表を置く。新規所見は `所見 R-N` の見出しを付け、(a) 何が問題か、(b) 現物の file:line、(c) real なら放置時に成果物 (certified 選択・レポート・台帳) の値・受理集合・参照がどう変わるか 1 行、(d) 修正案 (所有 file を明記)、を書け。各主張に [実測] / [推測] を付けろ。**blocker / must-fix / nit** を分けろ。成果物影響を書けない所見は must-fix にしない (DW-G05)。

## 制約

- 読取専用である。pytest の実走は要求しない。静的検査でよい。実測は親が行う。
- 予算が尽きそうなら途中結論を出力形式どおり書いて終われ。無出力が最悪である。
- 出力へ結合文字 U+0300〜U+036F を使わない。
- 出力の最後に `## 総括` 節を置き、closed / partial / regressed の件数、新規 blocker / must-fix / nit の件数、GO / NO-GO の判定を 10 行以内で書け。
