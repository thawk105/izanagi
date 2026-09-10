単独段 dispatch: stage=consult; sandbox=read-only; parent=/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2503-pbs-binding

必読事項の射影:

- `/home/SFC/tanab/.claude/jobs/2b56bf14/tmp/dw/t2503-pbs-binding/brief.md` — 親の段 1 brief。**これ自身も検査対象**。読めなければ即停止。
- `/home/SFC/tanab/.claude/jobs/2b56bf14/tmp/dw/t2503-pbs-binding/s2-plan-out.md` — 段 2 の plan。読めなければ即停止。
- `/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2503-pbs-binding/tools/pegasus/probes/t316_sandbox_backend_probe.py` — 修正対象。読めなければ即停止。
- `/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2503-pbs-binding/tools/pegasus/probes/t316_sandbox_backend_probe.pbs` — job body。読めなければ即停止。
- `/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2503-pbs-binding/orchestrator/tests/test_t316_sandbox_probe.py` — 負例を置く単位。読めなければ即停止。
- `/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2503-pbs-binding/orchestrator/tests/conftest.py` — 特に `_declare_default_test_site` (240 行付近) の site 中立化。読めなければ即停止。

## 依頼

あなたはレンズ A = **正しさ境界**の敵対検証子である。plan を守るのではなく攻撃せよ。
親 brief の前提・file:line・実測値・一般化も同じ強さで攻撃せよ。plan に賛成する所見は書かなくてよい。
コードを編集してはならず、commit してはならない。

## 攻撃面 (各項目に「real / refuted」と根拠の file:line を付けて答える)

1. **束縛が意味するもの。** 修正後の比較は「runtime に走った job body が、commit された job body と
   同一である」を本当に主張できるか。`.pbs` 側 (`t316_sandbox_backend_probe.pbs`) が既に同じ照合を
   しているなら、Python 側の照合は何を追加で守っているか。**追加で守るものが無いなら、それを言え** —
   その場合でも「削除せよ」ではなく「何を守るべきか」を書け。
2. **恒真ゲート。** 修正後の比較が、現実に起こりうるどの入力でも必ず真になる (= 何も検出しない) 経路が
   あるか。特に `.pbs` 側 line 65-80 を通った spool が Python 側の比較を必ず通るなら、Python 側は
   恒真である。恒真ならそれを real 所見として明示せよ。
3. **負例の検出力。** plan の負例は「比較対象を `.py` に戻す変異」を**確実に**殺すか。
   殺せない条件を具体的に構成せよ。特に (a) fixture の `.py` と `.pbs` の bytes がたまたま一致する、
   (b) 例外が別の理由 (HEAD 不一致・dirty・nodefile) で先に上がり、変異の有無に関わらず赤になる、
   (c) 主張が「性質」だけで実体を名指ししておらず、比較行を通らずに緑になる、を検査せよ。
4. **正例の実体性。** plan の正例は本当に `_execution_binding` の当該比較行を通るか。
   monkeypatch や stub で当該行を迂回していないか。通ることを示す証拠 (どの assert がどの行の
   副作用を観測するか) を file:line で書け。
5. **テスト代表性。** login node で走るこの test が、計算ノードの実挙動を代表するか。
   代表しない差 (hostname、PBS 環境、spool の実体、realpath の解決) を列挙せよ。
   `conftest.py` の `_declare_default_test_site` は `site_policy` module の `socket` だけを
   中立化する。probe module の `socket` は中立化されない。plan がこの差を取り違えていないか検査せよ。
   module scope の fixture は function scope の autouse より先に走る点も検査せよ。
6. **規律 2 / 3。** plan が正しさゲートを緩める方向 (例外を握り潰す、検査対象を減らす、
   `runtime_sha256` の key を減らす、例外文言を変える) を含まないか。含むなら real 所見にせよ。
7. **親 brief の攻撃。** brief の「(P1) 名前付き定数」「(P2) 実走負例」「凍結 pin 不在」
   「受入台帳は未知 node を unknown 扱い」「job body 側が既に照合済み」の各主張を、
   一次資料で裏取りし直せ。誤りがあれば real 所見として書け。

`docs/failures.md` の型タグ [捏造/幻覚] [恒真ゲート] [テスト代表性] [ドリフト] を攻撃面に含めよ。

## 制約

- あなたは書込可能な tmp を持たない read-only sandbox で走る。**pytest を実走しなくてよい**。
  静的検査で足りる。実走していないものを「緑」「赤」と書いてはならない。
- 仮想リスク向けの gate・検査・台帳・一般化の追加を推奨しない。scope 外の real 所見は
  「scope 外」と明記して裁定候補として返せ。

## 出力形式

見出しは H2 (`##`) で統一し、最後に `## 総括` を置く。各所見は「所見 / real か refuted か /
根拠 file:line / 提案」の 4 点で書く。結合文字 U+0300〜U+036F を使わない。
予算が尽きそうなら、途中でもこの出力形式どおりに結論を書いて終われ。無出力が最悪である。
