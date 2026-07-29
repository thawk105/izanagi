指定ファイルはすべて読了できました。`decisions.md` は D96/D97 の節全体を確認済みです。ファイル編集・pytest・runner 実行はしていません。以下は静的読解と Git 2.34.1 への read-only probe に基づく段2プランです。

## 確定した既存挙動

- [check_ai_provenance.py:59](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-t153e-t15423/tools/check_ai_provenance.py:59) は `git interpret-trailers --parse` が最終 trailer block と認識した `AI-Agent` だけを抽出する。このため `AI-Agent`、空行、CAB の順の分断は既に `AI-Agent trailer がない` で拒否される。
- 純増 vector は brief どおり、CAB、空行、最終 `AI-Agent` の順である。現状は AI-Agent が有効なので通過する。
- [check_ai_provenance.py:80](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-t153e-t15423/tools/check_ai_provenance.py:80) の `AI-Agent: none` は早期 return するため、CAB 検査をその前で計算・保持しないと分断を見逃す。
- Git probe では、大文字小文字差と colon 前の空白・tab は CAB として認識された。行頭空白・tab は CAB key ではなく継続行または本文になった。したがって行頭空白も raw 候補として数え、parsed 件数との差で拒否する P1 は妥当。
- 現在の既定履歴範囲495 commitを同じ件数比較で読み取ったところ不一致は0件だった。ただし「既存履歴へ遡及しない」契約を省いてよい根拠にはならない。
- brief の P2 は一部、既存挙動を読み違えている。[check_docs.py:159](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-t153e-t15423/tools/check_docs.py:159) の `SELF_LIMITS` は予算だけでなく、[check_docs.py:228](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-t153e-t15423/tools/check_docs.py:228) で normative dispatch allowlist にも混入する。ここへ provenance 規約を直接追加すると dispatch の受理集合まで意図せず広がる。

## 推奨 file:line プラン

### 1. CAB 配置検査本体

[check_ai_provenance.py:17](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-t153e-t15423/tools/check_ai_provenance.py:17)〜41:

- 新規 policy epoch 用の一意な `CO_AUTHORED_BY_POLICY_NEEDLE` を定義する。更新後の provenance 規約に同じ文言を置く。
- raw CAB 候補を `re.compile(r"^[ \t]*co-authored-by[ \t]*:", re.IGNORECASE | re.MULTILINE)` で定義する。
- Markdown bullet・引用符付きの行は CAB field ではなく本文扱いとして対象外にする。装飾形として拒否する対象は、上記 regex が拾う行頭空白・colon 前空白付き候補である。

[check_ai_provenance.py:59](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-t153e-t15423/tools/check_ai_provenance.py:59)〜67:

- `interpret-trailers --parse` を一度だけ呼び、case-fold した key ごとの値列を返す共通 parser にする。
- `AI-Agent` と `Co-Authored-By` は同じ parsed 結果から抽出する。
- CAB の値、メール形式、集合一致は検査しない。raw 候補の出現件数と parsed CAB key の出現件数だけを比較する。これにより重複を含む複数 CAB も欠落なく扱える。

[check_ai_provenance.py:70](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-t153e-t15423/tools/check_ai_provenance.py:70)〜122:

- 戻り値を `(base_findings, scope_findings, cab_findings)` に拡張する。
- `raw_count != parsed_count` のとき、両件数を含むCAB配置 findingを1件返す。
- CAB finding は `AI-Agent` 欠落・形式検査および `AI-Agent: none` の排他判定より先に算出し、各早期 return に載せる。
- 既存の AI-Agent 形式、重複、scope、reserved product、Codex author 判定は変更しない。

[check_ai_provenance.py:125](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-t153e-t15423/tools/check_ai_provenance.py:125)〜140:

- `_co_authored_by_policy_commit()` を内容検出で追加する。scope/Codex-author epoch と同様、`git log --reverse -S <needle> -- docs/ai-provenance.md` の最初の commit を採る。
- SHA の固定や元の provenance 導入 commit への遡及は行わない。

[check_ai_provenance.py:246](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-t153e-t15423/tools/check_ai_provenance.py:246)〜277:

- `--message-file`: 現行規約を検査する経路なので CAB finding を無条件に `findings` へ加える。staged path の Codex author 検査はそのまま併用する。
- 既定履歴と `--range`: commit ごとに CAB epoch の descendant/equal か判定し、該当 commit だけ CAB finding を有効化する。
- pre-epoch commit は CAB finding だけを除外し、既存の AI-Agent 検査は従来どおり行う。

### 2. provenance 境界テスト

[test_check_ai_provenance.py:16](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-t153e-t15423/orchestrator/tests/test_check_ai_provenance.py:16) 付近へ CAB fixture と helper を置き、次の外延を固定する。

| message の境界 | raw CAB | parsed CAB | 期待 |
|---|---:|---:|---|
| CAB なし | 0 | 0 | 受理 |
| `CAB` → `AI-Agent`、空行なし | 1 | 1 | 受理 |
| `AI-Agent` → `CAB`、空行なし | 1 | 1 | 受理 |
| mixed-case CAB、colon 前空白/tab | 1 | 1 | 受理 |
| 行頭空白付き CAB を本文側に置き、最終 AI-Agent | 1 | 0 | CAB 配置違反 |
| CAB → 空行 → AI-Agent | 1 | 0 | 新規 CAB 配置違反 |
| AI-Agent → 空行 → CAB | 1 | 1 | 既存の AI-Agent 欠落違反 |
| CAB 2行を同一 block に配置 | 2 | 2 | 受理 |
| 本文側 CAB 1行＋最終 block CAB 1行 | 2 | 1 | CAB 配置違反 |
| CAB＋`AI-Agent: none`、同一 block | 1 | 1 | 受理 |
| 分断 CAB＋最終 `AI-Agent: none` | 1 | 0 | CAB 配置違反。none で免除しない |

[test_check_ai_provenance.py:98](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-t153e-t15423/orchestrator/tests/test_check_ai_provenance.py:98) 付近:

- synthetic repo に pre-epoch 分断 commit、needle 導入 commit、post-epoch 分断 commit を順に作る。
- pre-epoch の履歴範囲は受理し、既定履歴監査または post-epoch range は後者だけを拒否する。
- commit 後の `%B` を読み返し、fixture の分断が実 commit message に残っていることを先に確認する。

[test_check_ai_provenance.py:136](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-t153e-t15423/orchestrator/tests/test_check_ai_provenance.py:136) 付近:

- staged path テストとは独立して、分断 CAB＋`AI-Agent: none` の message file を作り、`--message-file` が rc=1 と CAB finding を返すテストを追加する。
- contiguous CAB の message file が受理される正例も置き、単なるCAB存在拒否への変異を防ぐ。

### 3. 9,000-byte TextLimit

推奨は P2 を修正し、[check_docs.py:159](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-t153e-t15423/tools/check_docs.py:159) 付近へ次の独立 registry を追加すること。

- `PROVENANCE_LIMITS = {"docs/ai-provenance.md": TextLimit(9_000)}`
- [check_docs.py:1463](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-t153e-t15423/tools/check_docs.py:1463) の `all_limits` にマージする。
- `NORMATIVE_DISPATCH_ALLOWLIST` にはマージしない。
- `docs/ai-provenance.md` は既に [check_docs.py:38](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-t153e-t15423/tools/check_docs.py:38) の `LIVING_DOCS` にあるため重複登録しない。

親が brief の「SELF_LIMITS に置く」を維持する場合は、先に allowlist を `REFERENCE_LIMITS + docs/skill-self-improvement.md` へ明示的に切り離し、その非拡張テストを追加する必要がある。段4でどちらかを明示裁定すべきで、無裁定の直接追加は推奨しない。

[test_check_docs.py:1566](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-t153e-t15423/orchestrator/tests/test_check_docs.py:1566) 付近:

- registry が `TextLimit(9_000)` であることと、provenance path が dispatch allowlist 外であることを literal pin する。
- 9,000 bytes exactly の正例を置く。
- 既存 `self_byte_over` とは独立したテスト関数で、9,001 bytes に pad した `docs/ai-provenance.md` が、path・9001・上限9000を含む finding で拒否されることを固定する。
- [test_check_docs.py:2085](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-t153e-t15423/orchestrator/tests/test_check_docs.py:2085) 付近の budget-governed 集合へ新 registry を加え、列挙対象不在テストの finding 件数を偶然増やさない。

### 4. 規約・decision・記録

[ai-provenance.md:14](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-t153e-t15423/docs/ai-provenance.md:14)〜19:

- 「連続性は機械検査されない」という現行文を置換する。
- 全 CAB 候補を最終 trailer block に置くこと、raw 件数と Git 認識件数を照合すること、適用は導入 commit 以後であることを簡潔に記す。
- 現物は8,817 bytesで余裕が183 bytesしかない。追記中心ではなく既存文の置換・縮約とし、UTF-8実 byte が9,000以下であることを親が実測する。

[decisions.md:4298](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-t153e-t15423/docs/decisions.md:4298) の D97 後へ D98 を新設する。D96/D97の既存本文は歴史記録として編集しない。D98には次を固定する。

- raw/parsed の件数一致による受理集合。
- case、空白、複数 CAB、両分断順序、`AI-Agent: none` の境界。
- content-detected epoch と非遡及。
- 履歴監査と message-file の両経路。
- 値集合比較、CAB構文の自前再実装、boolean比較、全履歴への無条件遡及を却下した理由。
- 9,000-byte予算と、dispatch allowlistを広げない registry 配置。
- D97ではscope外だったT-153(e)を本Dで別変更として閉じる関係。

[worklog.md:523](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-t153e-t15423/docs/worklog.md:523) 以後は親が段7で新規エントリを追加する。本文のトップレベル項目で `[T-153]` と `[T-154]` を消費し、次の一手から両IDだけを外して他IDを保存する。`docs/phase3.md` には両IDの該当箇所が見つからなかったため、存在しない完了 checkbox は作らない。

## 親が実測する検査

実装後、親が少なくとも焦点 pytest、両 bare runner、`tools/check_docs.py`、`tools/check_codex_agents.py`、commit前の `--message-file`、commit後の履歴 provenance 監査を実測する。今回の read-only planner はいずれも実行しておらず、緑は主張しない。

## 総括

推奨プランは、CAB raw候補数と同一messageをGitがparseしたCAB key数を比較し、message-fileでは即時、履歴では新policy epoch以後だけ適用する構成である。変更対象は `tools/check_ai_provenance.py`、両関連テスト、`tools/check_docs.py`、`docs/ai-provenance.md`、新規D98、worklogおよびwaveの逐語成果物。

主要リスクは、`AI-Agent: none` の早期returnによるCAB finding消失、件数でなくboolean/setを使う複数CAB見逃し、epochなしの遡及、そして `SELF_LIMITS` への直接追加によるdispatch allowlistの意図しない拡大である。特にP2は段4で修正裁定し、独立したprovenance予算registryを採るのが安全である。