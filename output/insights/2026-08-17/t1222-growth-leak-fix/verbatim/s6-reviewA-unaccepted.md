## 所見

### R1. cache の効果そのものを恒久 test が監視していない

- **主張:** 現実装は重複物理読取を除去しているが、cache を無効化しても既存 test は意味論上すべて通り得る。「速くなった」性質に mutation kill がない。
- **根拠:** cache の実効点は `tools/check_docs.py:899-960`、生存篮囲は `tools/check_docs.py:5282-5289`。しかし commit `1122d724` は `tools/check_docs.py` だけを変更し、物理 open 回数を assert する test を追加していない。例えば `cache = _READ_TEXT_CACHE.get()` を `cache = None` にする変異は旧挙動へ戻すだけで、finding・rc の既存期待値を変えない。
- **帰結:** 今回の親実測は効果を証明するが、将来 cache が壊れても受入が検出しない。「壊れても誰も気づけない」に該当する。
- **深刻度:** must-fix

### R2. M1 と M3 に D452 を満たす期待赤 node がない

- **主張:** M2 は既存 node で検出できるが、M1 と M3 は既存 test 群へ静的に結び付かない。
- **根拠:** M1 に最も近い CRLF node は `orchestrator/tests/test_check_docs.py:6704-6716` だが、対象の `workers.md` は raw 読取でも各 parser が CRLF を処理する。archive の CRLF node `orchestrator/tests/test_check_docs.py:4595-4625` は `_placeholder_findings()` を直接呼び、`main()` cache を有効にしない (`orchestrator/tests/test_check_docs.py:4025-4029`)。M3 について、invalid UTF-8 test は最初の finding だけを assert している (`orchestrator/tests/test_check_docs.py:4692-4718`, `4747-4788`, `4827-4863`)。cache hit 時の二つ目の caller 固有 prefix は assert されない。
- **帰結:** M1/M3 は変異を注入できても SURVIVED が予想される。項目 3 の「newline を別物として扱う」「finding を再生する」という二つの制約に回帰検出力がない。
- **深刻度:** must-fix

### R3. 親の `1,133 → 673` は同一計測面の比較ではない

- **主張:** 効果の方向と 12.2% 短縮は支持されるが、「物理読取 1,133 → 673」という表現は厳密には過大である。
- **根拠:** 変更前の 1,133 は `_safe_read_text` 呼出し数、変更後の 673 は `Path.open` 数である。現コードには `_safe_read_text` の `Path.open` (`tools/check_docs.py:931`) に加えて admission loader の binary open (`tools/check_docs.py:3029`) がある。また spool guard は import loader を実行し (`tools/check_docs.py:976-982`)、その consumer は間接的に Git subprocess を1回起動する (`tools/check_docs.py:999-1006`, `tools/spool_fold.py:1098-1105`)。import loader や Git 内部読取は `Path.open` 計測外である。
- **帰結:** 673 distinct が旧 666 distinct より7多いこととも整合する。旧版の全 `Path.open` を同じ wrapper で再計測しない限り、総物理読取の exact 差とは呼べない。ただし460前後の重複 open が消えた主結論は覆らない。
- **深刻度:** nit

### R4. `4.147` 秒との差は残存重複処理と計測揺れで説明できる

- **主張:** 実装後 4.233 秒は予測上限より0.086秒、約2.1%遅い。物理 open は一意になったが、論理読取と安全検査、本文走査は重複したままである。
- **根拠:** cache hit 前にも親 component の symlink 走査と `lstat()` を行う (`tools/check_docs.py:868-901`)。`_safe_read_text` 呼出しは1,135回のままで、open は673回なので約462回の安全検査が残る。archive 本文は placeholder 検査で走査され (`tools/check_docs.py:1801-1851`)、同じ worklog を backlog/archive 検査でも解析する (`tools/check_docs.py:2071-2118`)。後者の物理読取だけが raw cache 導出 (`tools/check_docs.py:902-915`) で消える。親の3走も変更後0.197秒幅、変更前0.250秒幅があり、0.086秒全体を実装差とは断定できない。
- **帰結:** 「予測とほぼ一致」は妥当。ただし「重複処理がすべて消えた」は誤りで、消えたのは重複 open/decode の主要部分である。
- **深刻度:** nit

### R5. 成長次数は引き続き線形で、全体係数は半減していない

- **主張:** `docs/archive` は cache に載っている。物理読取係数は概ね2回/fileから1回/fileへ下がったが、node 全体は依然 `Θ(corpus bytes)` である。
- **根拠:** archive worklog の第1読取は `tools/check_docs.py:1801-1809`、第2読取は `tools/check_docs.py:2071-2096`。第2読取は `tools/check_docs.py:902-915` で第1読取の raw entryから導出されるため、親の913回/13.9M文字の主要群も cache 対象である。一方、両方の本文走査は残る。実測差0.589秒を削除された7.1M文字へ比例配分すると、残る12.8M文字の物理読取は約1.06秒、現4.233秒の約25%。残り約75%は安全検査、regex/parse、import、固定処理である。直接 Git subprocess はないが、spool validation 経由で1回ある。
- **帰結:** corpus 10倍時、corpus依存部分は約10倍になる。固定処理をすべて非成長とみなす下限でも約3.3倍、すべての残存走査が成長すると10倍弱である。静的構造上は二重 regex/parse も成長するため、実際は下限より上限寄りと見るべきである。「全コストの係数が約半分」ではなく、「物理読取係数が約半分、現時点の wall 係数は12.2%低下」が正確である。
- **深刻度:** nit

### R6. cache は corpus 全文を `main()` 終了まで保持する

- **主張:** 時間短縮と引き換えに、peak memory の corpus 比例項が増えている。
- **根拠:** cache は `main()` 冒頭で生成され (`tools/check_docs.py:5285`)、終了まで破棄されない (`tools/check_docs.py:5287-5289`)。成功本文は `tools/check_docs.py:956-960` で保持される。CRを含む本文では raw と正規化後文字列の双方を持つ。
- **帰結:** 現在の unique 約12.8M文字が10倍なら、少なくとも約128M文字相当と dict/Path/文字列 overhead を保持する。現規模では blocker ではないが、growth 軸の副作用として記録すべきである。
- **深刻度:** nit

## 変異 anchor の実在確認

### M1 — cache key から `newline` を落とす

- **適用可能か:** 条件付きで可能。ただし key 表現が `cache_key` だけでなく raw alias に分散しており、事前登録どおりの単一 anchor ではない。
- **anchor:** `tools/check_docs.py:852-854`, `900`, `905`, `915`, `937-960`
- **期待赤 node id:** **なし**
- **D452:** 不成立。既存 CRLF test は cache 非経由または raw/normalized の差を観測しない。
- **再照準案:** `tools/check_docs.py:908-911` の CRLF/CR→LF変換を省く単一変異にし、同一 archive file を `newline=""` と `None` で `main()` 内読取させる未保留・非 `xdist_group` test を追加する。想定名は `orchestrator/tests/test_check_docs.py::test_read_cache_preserves_distinct_newline_results`。

### M2 — path を key から落とす

- **適用可能か:** 可能。`tools/check_docs.py:900` の path 成分を定数へ置換すれば、同じ newline の別 file が衝突する。
- **anchor:** `tools/check_docs.py:900`
- **期待赤 node id:** `orchestrator/tests/test_check_docs.py::test_dev_wave_model_pins_accept_min_repo_contract`
- **D452:** 成立。`_HOLD_ROWS` に無く、`xdist_group` も無い。誤本文により child checker が rc=1となり、`orchestrator/tests/test_check_docs.py:7277-7279` の assert が failure になる。

### M3 — cache hit 時の finding 再生を省く

- **適用可能か:** 可能。
- **anchor:** `tools/check_docs.py:916-925`
- **期待赤 node id:** **なし**
- **D452:** 不成立。既存 failure test は初回 caller の finding だけを固定し、二回目の caller 固有 prefix を要求しない。
- **再照準案:** 同じ invalid UTF-8 file を二つの prefix で読む `main()` testを追加し、双方が1回ずつ出ることを assertする。想定名は `orchestrator/tests/test_check_docs.py::test_read_cache_replays_failure_for_each_caller`。

追加で、cache 効果自体には `tools/check_docs.py:899` で cache を無効化する変異を置き、物理 open が distinct file 数を超えないことを固定する未保留・非 `xdist_group` node が必要である。

## refuted

- `main()` から到達する `_safe_read_text` 15 call site はすべて `main()` の cache scope内にある (`tools/check_docs.py:5282-5292`)。cache 外の `main()` 経路は見つからない。
- `docs/archive` は対象外ではない。worklog群の二つの読取経路はいずれも cache を共有する。
- `read_text` / `read_bytes` / built-in `open()` /直接 `subprocess` は `tools/check_docs.py` にない。直接の別読取は `Path.open` 2箇所と import loaderで、同じ対象 file の反復読取は見つからない。
- Python consumer 全件では、直接 import は `test_check_docs.py:41`、`test_s8c_preregistration_invariant.py:22`、`test_s8b_selector_output.py:20`、`test_check_ai_provenance.py:22`。動的 import は `tools/spool_fold.py:2125-2149`。変更された既存名・signature・定数はなく、consumer break は見つからない。
- `_safe_read_text` の monkeypatch は `orchestrator/tests/test_s8c_preregistration_invariant.py:345-358` の1件だけ。call site は引き続き module-global 名解決である。
- CLI consumer、land、hooks、checker/daemon は `main()` の既存 CLI契約だけに依存し、その契約変更はない。
- commit `1122d724` の変更は `tools/check_docs.py` だけ。test、docs、保留台帳の変更はない。
- `_HOLD_ROWS` は静的に59行のままである。
- pytest は実行していない。親の453 passed / 3 skippedを再実走したとは扱っていない。

## 総括

**NO-GO**

実装効果と consumer 互換性は支持され、`docs/archive` の重複物理 open も実際に除去されている。しかし、M1とM3にD452準拠の期待赤 nodeがなく、さらに cacheを丸ごと無効化する性能回帰も既存 testが検出しない。少なくとも newline 分離、finding 再生、物理読取一意性の3性質を未保留・非 `xdist_group` の failure nodeへ結び付けるまで着地不可と判定する。