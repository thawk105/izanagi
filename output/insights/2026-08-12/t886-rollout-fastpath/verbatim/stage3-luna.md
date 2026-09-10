## 総括

段 2 plan はそのまま実装へ進めない。主な理由は、(1) `21.8s` が受入全走の wall ではなく fixture 1 インスタンス分、(2) `rglob` による archive 線形成分が残る、(3) brief が認可していない例外迂回による受理集合拡大、(4) 既存テスト 1 本が keyword 引数で壊れるためである。

### 1. fixture の 21.8 秒を全走の改善とみなせない

深刻度: BLOCKER

反例構成:

- [`benchmark_snapshots`](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t886-rollout-fastpath/orchestrator/tests/test_codex_reasoning_ab.py:260>) は `scope="module"` だが、xdist の worker 間では共有されない。
- POS の `build_snapshot` は [`derive_independent_golden`](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t886-rollout-fastpath/tools/codex_reasoning_ab.py:1286>) 内で 3 回、POS/NEG の `render_prompt` で 2 回、合計 5 回 `_find_rollout` を呼ぶ。
- test module は `real-repo` group に固定されておらず、worker 数は compute node の affinity 依存である。実績は `-n 48` も存在する。

したがって `5 × 4.4s` は「worker 1 個の fixture 1 回」の値であり、全走では worker ごとに最大 `5k` 回の走査になる。wall は単純に `21.8k` 秒にはならないが、worker 間の同時 I/O 競合も含め、全走の critical path は別物である。

成果物影響（1行）: certified 値自体は直ちに変わらないが、受入 report / ledger の「全走が約 21.8 秒改善」という主張が成立しない。

提案する対処: 同一 worker 数・同一 full-suite shape で、fixture 構築回数を worker 別に記録し、focused run の値と全走 wall を分離して報告する。fast path 後の clone、snapshot 検証、`git` subprocess、選択 rollout 全文 parse が新しい律速候補になる。

### 2. before/after の測定プロトコルが未定義

深刻度: MUST-FIX

反例構成:

[`brief.md`](</work/1/SFC/tanab/dev-wave-jobs/dev-wave-t886-rollout-fastpath/brief.md:60>) は before/after 実測を成果物に挙げるだけで、workload、`-n`、worker 配置、cache 状態、測定順序を固定していない。

例えば baseline を先に走らせると、2.59GB archive の page cache と metadata cache が温まり、after 側の fast path が有利になる。逆順なら baseline 側の全 archive read が cold のままになる。focused fixture 走を full acceptance と比較する構成も成立する。

成果物影響（1行）: timing report と「受入全走の改善」台帳が cache 温度差または並列度差を測ってしまう。

提案する対処: 同一 archive snapshot・同一 checkout・同一 worker 数・同一コマンドを preregister し、cold/warm を別系列として測る。before/after の順序を counterbalance し、fixture 回数と全走 wall の両方を記録する。

### 3. `rglob` は archive 全体を歩き続ける

深刻度: BLOCKER

反例構成:

plan の `f"rollout-*-{glob.escape(session_id)}.jsonl"` を [`Path.rglob`](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t886-rollout-fastpath/tools/codex_reasoning_ab.py:282>) に渡しても、`rglob` は session id に一致する file だけを直接 index lookup しない。通常の directory を再帰し、各 directory entry の名前を検査する。

親の warm 値 5.5µs/file を単純外挿すると、29,460 file では約 0.162 秒になる。実測 glob 値 0.018〜0.021 秒をそのまま比例外挿すれば約 0.18〜0.21 秒である。ゼロにはならず、5 呼出なら fixture ごとに約 0.8〜1.0 秒が残る。

inode 数、directory 数、directory fan-out、Lustre metadata cache により file 数だけでは決まらない。cold cache の倍率は提示資料から算出不能である。

成果物影響（1行）: archive 成長に対する比例項は残り、「比例コストの除去」という成果物主張は誤りになる。

提案する対処: 真に比例項を消すなら、session-id index または直接解決可能な path 契約が必要であり、別裁定に戻す。現案を採るなら主張を「warm metadata walk の係数削減」に限定し、10倍規模・cold/warm・inode 構成を測定する。

### 4. 実測母集団が自己矛盾している

深刻度: MUST-FIX

反例構成:

- [`premise.json`](</work/1/SFC/tanab/dev-wave-jobs/dev-wave-t886-rollout-fastpath/artifacts/premise.json:1>) は 2,941 file。
- [`divergence.json`](</work/1/SFC/tanab/dev-wave-jobs/dev-wave-t886-rollout-fastpath/artifacts/divergence.json:1>) は 2,945 file。
- divergence には content id の重複も存在するが、premise の「名前由来 id の重複 0」と同じ母集団指標ではない。

4 file の差分が archive 成長によるものなら、両測定は同一 snapshot ではない。日時、manifest、archive bytes の pin も成果物にない。

成果物影響（1行）: 215〜242倍および係数約270倍の比較対象が揃っておらず、再現可能な性能証拠にならない。

提案する対処: 測定時点の file manifest、file count、総 bytes、directory/inode count、node、filesystem、worker 数を保存する。warm 値だけで cold 倍率を推定しない。

### 5. 未認可の `ValueError` 迂回で受理集合が広がる

深刻度: BLOCKER

反例構成:

1. pin 対象候補 `c = rollout-<timestamp>-<sid>.jsonl` に正しい `session_meta` と pin 一致 bytes を置く。
2. `rollout-0-poison.jsonl` を候補より先に置き、`"session_meta"` を含む 10,000 桁整数の JSON を入れる。
3. 現行全走査は [`_session_meta_rows`](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t886-rollout-fastpath/tools/codex_reasoning_ab.py:231>) の `json.loads` で `ValueError` を伝播する。
4. fast path は名前 glob で `c` だけを開き、pin 検証を通して `c` を返す。

これは段 2 plan 自身も認めている「無関係 rollout の未捕捉例外を迂回する」反例である。

成果物影響（1行）: baseline なら拒否される入力から certified 選択、report、ledger が生成され、受理集合が重複以外の理由で拡大する。

提案する対処: 段 4 で明示的に認可しない限り実装停止。現行例外挙動を完全保存するなら全 file の走査が必要で、現案の高速化と両立しない。

### 6. 既存テストが 1 本、keyword 配線で壊れる

深刻度: MUST-FIX

反例構成:

- plan は [`render_prompt`](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t886-rollout-fastpath/tools/codex_reasoning_ab.py:1556>) から `pinned_label=case` を渡す。
- [`test_prompt_replacement_count_zero_expected_and_excess`](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t886-rollout-fastpath/orchestrator/tests/test_codex_reasoning_ab.py:1511>) は [`lambda *_: rollout`](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t886-rollout-fastpath/orchestrator/tests/test_codex_reasoning_ab.py:1529>) で `_find_rollout` を差し替えている。
- この lambda は `**kwargs` を受けないため、`render_prompt` 呼出時に `TypeError` になる。

plan の「既存テストはすべて 2 引数呼出なので変更不要」という説明は誤りである。

成果物影響（1行）: 受入テストが赤になり、修正時にテスト削除・skip・期待値変更を選ぶと prompt 検査の検出力も失う。

提案する対処: monkeypatch seam を `lambda *args, **kwargs: rollout` 相当にし、既存期待値は変更しない。別テストで `pinned_label` の値を検査する。

### 7. 既存 `_find_rollout` テストの多くは fast path を通らない

深刻度: MUST-FIX

次のテストは 2 引数で呼ぶため、`pinned_label=None` の全走査だけを検査する。

- [`test_find_rollout_session_meta_encoding_and_payload_field_equivalence`](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t886-rollout-fastpath/orchestrator/tests/test_codex_reasoning_ab.py:1286>)
- [`test_find_rollout_preserves_zero_and_duplicate_failure`](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t886-rollout-fastpath/orchestrator/tests/test_codex_reasoning_ab.py:1338>)
- [`test_find_rollout_session_meta_scanner_parses_only_candidates`](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t886-rollout-fastpath/orchestrator/tests/test_codex_reasoning_ab.py:1373>)
- [`test_find_rollout_session_meta_scanner_propagates_value_error`](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t886-rollout-fastpath/orchestrator/tests/test_codex_reasoning_ab.py:1402>)
- single-escape、BOMless UTF、bad candidate、unreadable、blank の各テスト（[`1418`](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t886-rollout-fastpath/orchestrator/tests/test_codex_reasoning_ab.py:1418>) 以降）
- 実 SHA anchor（[`1544`](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t886-rollout-fastpath/orchestrator/tests/test_codex_reasoning_ab.py:1544>)）

例えば fast path 側だけで `ValueError` を広く catch しても、既存の ValueError テストは緑のままである。fast path 内の content predicate を `payload.id` のみにしても、既存テストは pinless 経路なので直接は検査しない。

成果物影響（1行）: 現行出力が同じでも、fast path の誤った受理・例外境界・再帰性が受入集合に入り込む。

提案する対処: pinned 版にも nested directory、UTF、bad candidate、ValueError、parse count の負例を置く。M07/M12 を「既存 gate が先取り」と扱うなら、fast path に実際に到達することを証明する。

### 8. F90 型の恒真ゲートになり得る

深刻度: MUST-FIX

反例構成:

- `test_find_rollout_real_pinned_pos_uses_single_content_probe` は POS だけで、archive が無ければ skip。
- caller wiring test は `_find_rollout` 自体を spy/sentinel 化するため、`pinned_label` を渡していることは確認できても、実際に fast path が選択されたことは確認できない。
- `ROLLOUT_SHA256` から `fix1` の key を削除しても、caller は `pinned_label="fix1"` を渡し続け、helper は eligibility 不成立から全走査へ fallback できる。出力は同じで、wire test は緑になり得る。
- synthetic candidate を root 直下に置くと、`rglob` を `glob` に変えて再帰性を失わせても通る。real POS test は skip 可能である。

これは F90 の「構成変化で被覆が落ち、gate が緑を返す」型である。F90 の根本原因は [`docs/failures.md`](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t886-rollout-fastpath/docs/failures.md:2669>) に記録されている。

成果物影響（1行）: certified bytes は同じでも、5 label の性能改善を実際には検査していないまま受入 report が緑になる。

提案する対処: skip 不可の hermetic nested-tree positive control を追加し、POS/NEG/author/fix1/fix2 全 label で実 helper の候補限定と content probe 回数を検査する。premise JSON を before 等価性 gate の代用にしない。

### 9. F141 型の「現在 1 件」前提は部分的に残る

深刻度: MUST-FIX

反例構成:

- 同じ id を持つ名前候補を 2 件作ると `len(candidates) != 1` から fallback するため、この部分の攻撃は構成できない。
- しかし [`divergence.json`](</work/1/SFC/tanab/dev-wave-jobs/dev-wave-t886-rollout-fastpath/artifacts/divergence.json:1>) は、filename に id が無い content duplicate を既に示している。`c` は名前 glob に一致し、別名 `d` は一致しない構成なら、全走査は RC_SESSION=21、fast path は pin 済み `c` を受理する。
- plan はこれを明示認可された一方向拡大として扱っているため、隠れたバグと断定はしない。ただし `names_with_duplicate_id={}` は将来の一意性の根拠にならない。

成果物影響（1行）: 同 id の別名・別 bytes が増えた時、baseline の拒否が fast path では certified 選択・report・ledger の生成へ変わる。

提案する対処: 「同 id の任意 duplicate を pin が上書きしてよい」のかを裁定文に明記し、divergence と同型の複数 content-id fixture を固定する。認可が filename duplicate のみなら現案は scope 外である。

### 10. SHA の二重読みと fallback の追加コスト

深刻度: NIT

反例構成:

plan は fast path 内で `_verify_rollout_sha` を無条件に呼びつつ、既存の外側照合も残す方針である。既定値では [`derive_independent_golden`](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t886-rollout-fastpath/tools/codex_reasoning_ab.py:589>) と [`render_prompt`](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t886-rollout-fastpath/tools/codex_reasoning_ab.py:1566>) が同じ候補を二度 hash する。候補不一致時は content probe 後に全走査へ落ちるため、従来より一部入力で余計に読む。

成果物影響（1行）: certified bytes は変わらないが、21.8 秒の削減量は SHA 読み増しを含まない上限値になる。

提案する対処: before/after fixture 実測に SHA、clone、snapshot verify、fallback ケースを含める。外側照合削除は裁定違反なので行わない。

## 構成できなかった攻撃

- 安定した filesystem で、名前 glob が唯一、content predicate が一致、SHA が一致し、全走査も正常終了する場合に、返却 path だけが異なる反例は構成できなかった。plan の等価性論証はこの限定条件では成立する。
- `pinned_label=None` の既定経路と [`thread_id` 経路](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t886-rollout-fastpath/tools/codex_reasoning_ab.py:2879>)は、提案どおりなら従来の全走査を維持する。pinless 挙動そのものの静的反例は構成できなかった。
- 並行 wave の実差分を base commit と比較したところ、`_filesystem_file_set` の production hunk（acceptance 側 [`1035`](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-acceptance-bottleneck/tools/codex_reasoning_ab.py:1035>)）と T-886 の production hunk（[`282`](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t886-rollout-fastpath/tools/codex_reasoning_ab.py:282>)）は重ならない。test 追加も base 上は acceptance 側 1052〜1243 相当、T-886 側 1286〜1508 相当で、同一 hunk の衝突は構成できなかった。ただし line number は挿入でずれるため、先に main を再取り込みしてから patch を適用する必要がある。
- cold cache の倍率は構成できなかった。提示資料は warm cache の 5.5µs/file だけで、node、filesystem、metadata cache、cold 条件がないため、倍率を数値で報告する根拠がない。

read-only 制約に従い、ファイル変更・pytest 実走・緑の実証は行っていない。