単独段 dispatch: stage=review; sandbox=read-only; parent=/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2761-handshake-check

必読事項の射影:
- /home/SFC/tanab/.claude/jobs/1031d339/tmp/wave/s4-adjudication.md (親の段 4 裁定 = 実装の正本と変異事前登録。読めなければ即停止)
- /home/SFC/tanab/.claude/jobs/1031d339/tmp/wave/s1-brief-v2.md (親の brief v2。読めなければ即停止)
- /home/SFC/tanab/.claude/jobs/1031d339/tmp/wave/s5-author-snapshot.patch (実装差分の snapshot。読めなければ即停止)
- /home/SFC/tanab/.claude/jobs/1031d339/tmp/wave/s5-author.md (実装子の最終報告。読めなければ即停止)
- /home/SFC/tanab/.claude/jobs/1031d339/tmp/wave/focus-run-1-request4017.o.txt (親の焦点走 log: 計算ノードで対象 2 node が 2 passed。読めなければ即停止)
- /home/SFC/tanab/.claude/jobs/1031d339/tmp/wave/login-probe-b4-b5.txt (親の login probe B4/B5 の結果。読めなければ即停止)
- /home/SFC/tanab/.claude/jobs/1031d339/tmp/wave/make_mutation_spec.py (親の変異 spec 生成器 (job dir、repo 外)。anchor 逐語と期待 node を持つ。読めなければ即停止)
- /home/SFC/tanab/.claude/jobs/1031d339/tmp/wave/login_probe_b4_b5.py (親の login probe script。読めなければ即停止)
- /work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2761-handshake-check/orchestrator/tests/test_pegasus_dispatch_compute.py (実装後の対象 test。2580〜2637 行と `_job_script` を呼ぶ他 test。読めなければ即停止)
- /work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2761-handshake-check/tools/pegasus/dispatch_compute.py (production。828〜916 行。読めなければ即停止)
- /work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2761-handshake-check/docs/dev-wave/mutation.md (変異契約。読めなければ即停止)

## 依頼

あなたは dev-wave [T-2761] の段 6 敵対レビュー役 (レンズ B、read-only)。実装 (snapshot patch = 作業ツリーの現物) と親の変異登録を、
**整合・実効性・変異の帰属と anchor・波及・probe の妥当性** のレンズで攻撃せよ。実装子の報告を鵜呑みにせず現物で確認する。

ユーザー依頼 (逐語): 「`"release" not in script.lower()` を、repo path を除いた本文に対する handshake 構文 (marker を操作する
release 行) の不在検査へ変える。規律 2 を緩めない。本題の検査置換だけ。追加 gate は scope 外。」

親が実測済み: 焦点走 (計算ノード、request 4017) で C/R 2 node が 2 passed。login probe B4/B5 は期待どおり赤、対照は緑。
変異 matrix は未走 (レビュー後に container worktree で probe → 本走、旧 HEAD arm も別 container)。

## 攻撃点

1. **変異 spec の anchor と実装の一致:** `make_mutation_spec.py` の `test_anchor()` が実装後の file から切り出すブロック
   (`    normalizations = (` 〜 `    assert "while" not in script\n`) が file 内で一意か。production anchor (`PROD_ANCHOR`、`PROD_ANCHOR_B3`) が
   現物と byte 一致し一意か。f-string の `{{`/`}}` escape が `new` にも正しいか。`OLD_CHECK` の復元 bytes が旧 HEAD の 2 行と一致するか。
2. **各変異の単一理由性と期待 node:** m0 (SURVIVED)、a-old-check [R]、b-handshake / ab / b2 / b3 [C,R] について、対象 test 内で最初に赤になる
   assert が release 候補行の assert (a では旧 assert) か。B3 は MARKER needle を消費した後 `; until …` が残る形になるか
   (`script[end]` が `;` なので P5 は通る) を現物で追え。file 全体を runner にしたとき、他 test が production 変異 (`_job_script` の
   comment / until 行) で赤になる可能性 (script 全文比較・行数比較・`until` の不在検査等) を grep で否定せよ。
3. **runner 経路の安全:** 変異後の `_job_script` が計算ノードで即抜けするか (`-n "$MARKER"` / `-n "$gate"`、`set -u`、定義順)。bash 構文として
   正しいか (`[[ ... || ... ]]`、`; do sleep 1; done`)。B3 の同一行 `MARKER=...; until` は f-string 展開後に妥当な bash か。
4. **login probe の妥当性:** `login_probe_b4_b5.py` が対象 test 関数を parametrize 抜きで直接呼ぶ形が、pytest 経由と同じ検査経路を通るか
   (`tmp_path` の代わりに合成 dir を渡すだけ、fixture 依存なし)。B5 の wrapper が REPO needle の直後に `ase` を足す形が、
   裁定 A-1 の反例と同値か。probe が repo に入っていないこと。
5. **波及:** `_job_script` の他 caller (実装子の報告の行番号) と共有 helper に挙動変化が無いこと。node 数 1→2 で影響を受ける機構
   (duration ledger、shard 配分、allowlist、pin) の有無を grep で確認。
6. **記録に書く事実の検算:** 「暫定防壁 (wave 名に release を含めない) が着地後に不要になる」の根拠 = 他 test に script/path への release
   語不在検査が無いこと (grep で確認)。`while` の同型偽赤が残る事実も書き添えるべきか。
7. **scope:** 差分に本題以外の変更が無いか。

## 制約

- pytest は走らせられない。静的検査だけでよく、緑を主張するな。
- 所見は real / refuted、must-fix / nit、scope 内 / 外を各 1 語で明示し、must-fix には放置時の成果物影響 (受理集合・偽赤・偽緑・変異の誤判定) を
  1 行で書く (書けないものは nit)。scope 外の real 所見は「裁定パッケージ候補」として書く。
- 出力は file に書かず、最終メッセージの本文に全文を書け (親の launcher が保存する)。
- 予算が尽きそうなら途中結論を出力形式どおり書いて終われ (無出力が最悪)。

## 出力形式 (見出しは全部 `##`)

## 所見一覧 (番号・real/refuted・must-fix/nit・scope 内/外・成果物影響・根拠 file:line)
## 変異 spec の検算表 (変異 × anchor 一意性 × 単一理由 × 期待 node)
## 波及と記録事項の検算
## 総括

最後の節は必ず `## 総括` (`#` を 2 個) とする。`### 総括` と書いてはならない。
