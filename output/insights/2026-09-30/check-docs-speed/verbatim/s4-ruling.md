# 段 4 裁定 — dev-wave-check-docs-speed (2026-09-30 JST、親)

入力: brief.md、s3/out-a.md (レンズ A)、s3/out-b.md (レンズ B)、login 変更前 1 走 (login-base-run.{out,time}: rc=0、wall 85.2 s、user 30.9 s、CPU 38%、自発切替 34,529、maxRSS 302 MiB、load 42/96)。
裁定 inbox 再走査: 2026-09-30-rulings-full40-verdicts.md まで。本 wave に効く新裁定なし。

## 所見の裁定

| # | 所見 | 判定 | 処置 |
|---|---|---|---|
| A1 | O2 の sink は entry 本文の ID (section の ID と別文字列)。境界は sort 後の right.entries[0]、最終境界は worklog entries[0]。位置で対応 | real | 採用。entry 本文 ID を entry の位置ごとに 1 回計算し entry_has_id と sink に共用。archive 境界用に各 archive の先頭 entry の本文 ID を archive と共に保持 |
| A2 | O1 は str.count の end 規則 (負・範囲外) を再現 | real | 採用。end を slice 規則で正規化し bisect_left |
| A3 | O3 は \r 単独・CRLF・assert 経路を保つ | real | 採用 (B3 と合わせ条件付き)。旧実装の逐語コピーとの網羅対照 test を必須 |
| A4 | O4 の memo は例外非 cache・寿命限定 | real | global memo は採らず、O4' = 順序検査ループ内で各 archive の先頭/末尾 entry point を局所に 1 回だけ計算して比較 (関数 `_archive_entry_point`・`_entry_point_is_before`・`_archive_is_before` は残す) |
| A5 | O5 は等価、bypass は 1513 行だけ | real | 採用 |
| A6 | 所見順序・早期 return・generator の逐次性・Path.open 回数を保つ | real | 不変条件として prompt に明記 |
| A7/B1/B8 | 30 s 見積りは実測でない。累積時間は重複 | real | 効果主張は同時刻 ABAB の未計測 wall と peak RSS だけで行う。各 O の寄与は変更前後 profile の関数別比較で帰属 (wall では主張しない) |
| A8 | `_validate_next_action_items` 13.4 s・section の 3 重解析 | real | 今回は O1 で line 番号分を取り、section 再解析は次の一手 (再計測後) |
| A9 | E1/E2 は境界入力を網羅しない | real | 合成入力の網羅対照 test (T1〜T3) で補う。全体比較は stdout 全文と rc |
| B3 | O3 は初回から外す | refuted (部分) | 取り分 6.8 s は profile 上の tottime 5.0 s が主で純関数。網羅対照 test で等価を示せるので採用。digest の遅延計算は次の一手 |
| B4 | O4 は外す | refuted (部分) | O4' は局所計算で cache 寿命問題がなく、所見と順序を保つ。採用 |
| B5 | P2 の 200〜400 MB は根拠なし | real | 見積り文を撤回。実測: 変更前 maxRSS 302 MiB (login)。E3 で新旧の peak RSS を併記 |
| B6 | E2 全 node 二重実行は過剰になりうる | refuted | test_check_docs の直列所要は台帳で 583 node / 223 s。2 回でも計算ノード 8 分程度で、「全 fixture」を漏れなく覆う最も単純な方法 |
| B7 | node 時間の内訳 | real | E1: 7 木 × 新旧 × ~60 s ≈ 14 分、E2: 2 × ~4 分 (xdist なし) ≈ 8 分、E3: 5 × (旧 ~50 + 新 ~30) s ≈ 7 分 + 変更後 profile 1 走 ≈ 2 分。合計 < 35 分 = 0.6 node 時間 (2 node 時間未満、確認不要) |

## plan v2 (実装子 A = tools/check_docs.py + orchestrator/tests/test_check_docs.py)

- O1 tools/check_docs.py:1381 `_line_number`: `\n` の位置の索引 (小さい上限付き LRU、値キー) + `bisect_left`。end は `str.count(sub, 0, offset)` と同じ slice 規則で正規化。
- O2 tools/check_docs.py:2960〜3210: entry 本文の ID (`_top_level_ids(entry[1])`) を entry の位置ごとに 1 回だけ計算し、entry_has_id / worklog 側 `if _top_level_ids(entry[1])` と check_transition の sink に共用。check_transition は sink の本文 ID を引数で受ける形に変えてよい (内部関数)。archive 境界・最終境界の sink は、その sink entry について既に計算した本文 ID を使う (`_ArchiveWorklog` にフィールド追加可)。所見の文言・順序・実行順・早期 return を変えない。
- O3 tools/check_docs.py:1953 `_top_level_item_raw_slice`: 1 文字ループを str.find / 正規表現で等価実装。先頭 assert を維持。
- O4' tools/check_docs.py:3188〜3199: 全ペアループ内の `_archive_is_before(left, right)` を、事前に各 archive につき 1 回だけ求めた (先頭 entry point, 末尾 entry point) の比較で置換。比較規則は `_entry_point_is_before` と同一。所見文言・順序は同一。
- O5 tools/check_docs.py:1513: `not in_comment and "<!--" not in line` なら `_mask_html_comments` を呼ばず `visible = line`。
- 付随可: `_is_carry_candidate` の正規表現を module 定数として事前 compile (パターン文字列は逐語同一)。
- 追加 test (末尾追加のみ、既存期待値・exact pin 不変、実 corpus 不到達、tmp_path と合成文字列だけ):
  T1 `_line_number` を小アルファベット (`a`,`\n`,`\r`) 長さ 0〜7 の全文字列 × offset ∈ [-len-2, len+2] で `text.count("\n",0,offset)+1` と照合。
  T2 `_top_level_item_raw_slice` を test 内に逐語複製した旧実装と、小アルファベット (`-`,`x`,` `,`\t`,`\r`,`\n`) 長さ 1〜6 の全文字列 × 全 item_offset で照合 (assert 経路も一致)。
  T3 `_visible_markdown_lines` を test 内に逐語複製した旧実装 (launch_authority の `_mask_html_comments` を使う) と、comment の開始・継続・終了、fence 内の `<!--`、CR/CRLF を含む合成入力群で照合。
  T4 O2 の正例・負例: (a) sink entry の本文にあるが sink の「次の一手」節外にだけある ID は遷移所見を出さない (旧挙動)、(b) 本文にも見送り台帳にもない ID は所見を出す、(c) archive 境界 (archive → 次 archive 先頭、最終 archive → worklog 先頭) で同じ 2 例。
  所要は T1〜T3 合計 数秒以内、T4 は既存の _build_min_repo subprocess と同程度。

## 実装子 B (probe、repo 外へ退避): worktree 内 `wave-probe/` だけに書く
- `equiv_real.py`: 旧 check_docs (git show で取り出した blob) と新 check_docs を、(i) main 現物の git archive 木、(ii) 故障注入 6 種 (宙吊り carry 参照先、entry 番号重複、archive 順序曖昧、CRLF/CR 混在の archive、次の一手節内の fence と HTML comment 継続、carry 文法崩れ) に対して同じ木で走らせ、rc と stdout 全文を比較し JSON を出す。
- `equiv_fixtures.py` + pytest plugin: test_check_docs.py の全 node を新旧 check_docs で直列実行し、checker subprocess 呼出しごとに (nodeid, 呼出し順, argv の root 正規化, rc, root 正規化 stdout/stderr) と node の outcome を記録、差分を出す。
- `bench_abab.py`: 1 job 内で旧/新を交互に 5 回ずつ未計測実行、wall と子の peak RSS を記録。

## 変異の事前登録 (実装後に単一理由性を確認し、期待 node は probe で完全集合を確定)
- M1 O1: bisect_left → bisect_right。期待: T1 が赤。
- M2 O1: 負 offset の正規化を外す。期待: T1 が赤。
- M3 O2: sink に sink entry の「次の一手」節の ID を使う (本文 ID でなく)。期待: T4(a) が赤。
- M4 O2: archive 境界の sink に left の先頭 entry の本文 ID を使う。期待: T4(c) か既存境界 test が赤。
- M5 O3: 行終端判定から `\r` を外す。期待: T2 が赤。
- M6 O5: 条件から `not in_comment` を外す。期待: T3 か既存 comment test が赤。
- M7 O4': 事前計算で left の末尾でなく先頭 entry point を使う。期待: 既存の archive 順序曖昧 test が赤 (無ければ実装子 A が正例・負例を追加)。
