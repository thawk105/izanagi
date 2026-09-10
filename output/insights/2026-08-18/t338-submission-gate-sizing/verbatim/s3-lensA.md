- **[blocker] (P3) は CMakeCache の再読脚を落とし、3 者一致を 2 者一致へ弱める**
  - 反する逐語: 「validator は次の 3 者を再読して一致を要求する」および「(12) 申告値と実体の 3 者一致 (§6.3 の argv macro / compile_commands / CMakeCache)」 (`materials/record-items-v2-s4-s10.md:473-477,642`)
  - 実装面のアンカー: `s1-parent-p3-measurement.md:25-33,43-49`; `s2-plan.md:30-33`; `output/insights/2026-08-11_t139-manifest-land1/receipt-schema-v1.json:54-71,130-131,824-825`。CMake helper は macro が compile command に現れることだけを裏付ける (`external/ccbench/cmake/ProtocolHelpers.cmake:29-43`)。raw `CMakeCache.txt` は schema に無く、申告値はその代用にならない。実 cache が 1、configure・compile command・申告値が 0 の receipt を親案は受理するが、承認済み述語は拒否する。
  - **成果物影響**: trace / analysis の実 cache が食い違う build を適格 receipt として受理し、certified 選択と材料レポートの正しさ根拠を拡大する。

- **[blocker] §8 の予定テストは第 3 脚の欠落を検出しない**
  - 反する逐語: 「消費側が次のいずれかを受理条件の入力に使ったら落ちるテストを置く」「arms.*.compile.trace_enabled / analysis_enabled / cmake_cache」 (`materials/record-items-v2-s4-s10.md:653-668`)
  - 実装面のアンカー: `s2-plan.md:36-45`。予定 3 本は fallback、`R OR C`、申告不一致を検出するが、raw CMakeCache を一度も入力しないため、configure と `compile_commands` だけで判定する 2 脚実装も全て通る。さらに不一致検査は consumer でなく semantic helper 直呼びである。
  - **成果物影響**: conformance / mutation 検査が成功したように見えても、承認済み 3 者一致より広い receipt 集合が certified 経路へ入る。

- **[blocker] (P2) の現 tip 検査は alpha 予約の再利用履歴を受理する**
  - 反する逐語: 「各世代の blob が直前世代の blob の byte-prefix である」「`(family_root, ordinal)` の全履歴一意性」「当該行が初めて出現した `reservation_commit` を再導出する」 (`materials/record-items-v2-s4-s10.md:525-536`)
  - 実装面のアンカー: `s1-brief.md:63-66`; `s1-parent-classification.md:52-56`。予約行を使用後に削除し、同じ `(F,1)` を再導入すれば、現 tip の `k=1` と初出 commit の祖先性は両方成立する。`s2-plan.md:103-113` も同じ反例を確認している。
  - **成果物影響**: 同じ alpha 予約を別 parent series で再利用して累積有意水準をリセットでき、台帳上は一意のまま候補を certified に押し上げられる。

- **[blocker] 未定義の intent / series authority のまま「gate 完成」と正例受理を主張できない**
  - 反する逐語: 「`attempts[]` は durable submission intent の全 attempt を exact に被覆する」 (`materials/record-items-v2-s4-s10.md:444-454`) および「§6 の cross-field 制約と §7.1 の全項目は固定 semantic validator が再計算する」 (`同:607-613`)
  - 実装面のアンカー: `s2-plan.md:177,202,298-312` は canonical registry root、`series_id` / `parent_series_id` 導出、intent discovery、manifest grammar が未裁定と認めている。一方 `s1-brief.md:72-75,97` は「採用した制約」だけの負例で完成を名乗る。
  - **成果物影響**: fail-closed 実装なら正例を含む受理集合が空になり、receipt 自身を discovery authority にすれば失敗 attempt を receipt と intent の双方から落とした台帳を受理する。

- **[must-fix] `load_json_strict` は duplicate-key 拒否の無料再利用にならない**
  - 反する逐語: 「duplicate JSON key は schema 検査の前段の parser で拒否する」および「engine の差で受理集合が変わってはならない」 (`materials/record-items-v2-s4-s10.md:607-613`)
  - 実装面のアンカー: `orchestrator/qualification/artifacts.py:541-555` は duplicate key に加えて canonical serialization と末尾 LF を要求する。`orchestrator/tests/test_pegasus_floor_tools.py:1470-1484` は pretty JSON を明示的に拒否するが、承認済み T-139 receipt 契約には top-level canonical bytes 要件がない。
  - **成果物影響**: schema と全 semantic 制約を満たす非 canonical JSON receipt が余分に拒否され、validator の受理集合と材料レポート生成対象が承認なしに縮む。

- **[must-fix] `read_regular_file_with_identity` は §6.10 の全 component hardening を満たさない**
  - 反する逐語: 「path の各 component を `O_NOFOLLOW` で辿り、`fstat` / hash / parse を同一 fd に対して行う」 (`materials/record-items-v2-s0-s3.md:81-83`) および「各 path component を `O_NOFOLLOW` で辿り、symlink を拒否する」 (`materials/record-items-v2-s4-s10.md:588-595`)
  - 実装面のアンカー: `orchestrator/qualification/artifacts.py:82-112` は最終 component を `os.open(path, O_NOFOLLOW)` で単一 fd 読取するだけで、中間 component を `openat` 型に辿らない。親の「無料」判定は `s1-parent-classification.md:32-34`。
  - **成果物影響**: symlink 化された親 directory 経由の外部・差替え可能な証拠 pointerを受理し、receipt と材料レポートが参照する bytes を承認済み閉包外へ動かせる。

- **[must-fix] pilot 禁止は維持されているが、予定 `submit_pilot` の成功契約が未定義**
  - 反する逐語: 「`pilot_submission = forbidden` を解除できるのは、canonical 台帳へ fold された decision だけ」 (`materials/D292.md:3-8`) および「gate API の空実装や恒真 deny stub を先に置く」を却下 (`materials/D264.md:17-20`)
  - 実装面のアンカー: 現行 `orchestrator/preregistration/__init__.py:3-5` は `submit_pilot` 未実装、`orchestrator/publication/report.py:229-231` は forbidden のままなので 1 bit も動いていない。一方 `s2-plan.md:163,181-184` は戻り型を `str` としつつ、現状態では常に `SubmissionForbiddenError` とするが、canonical state resolver と「gate 合格後に policy deny へ到達した」ことを証明する統合検査を定めていない。
  - **成果物影響**: 実装択一を誤ると、submission ID を返して未承認 pilot を生成するか、恒真 deny のまま 4 名前を export して gate 完成を偽装する。

## 総括

NO-GO — (P3) が承認済み 3 者一致を弱め、(P2) が alpha 再利用履歴を通し、intent / series authority 未定義のまま gate 完成を名乗れない。静的検査のみで、pytest・build は実走していない。