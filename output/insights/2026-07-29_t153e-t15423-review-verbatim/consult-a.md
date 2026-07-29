指定資料はすべて読了しました。編集、pytest、runner は実行しておらず、緑も主張しません。以下の実測は Git 2.34.1 に対する read-only probe です。

## Findings

### 1. HIGH / real / must-fix — `---` により「最終 trailer block」が成立しない

- file: [check_ai_provenance.py:61](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-t153e-t15423/tools/check_ai_provenance.py:61)、[plan.md:24](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-t153e-t15423/output/insights/2026-07-29_t153e-t15423-review-verbatim/plan.md:24)、[ai-provenance.md:14](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-t153e-t15423/docs/ai-provenance.md:14)
- `interpret-trailers --parse` は既定で `---` より後を divider 後領域として無視する。実測では、CAB と `AI-Agent: none` の後に `---` と後続本文があっても両 trailer を返し、現行 `validate_message()` も違反なしだった。
- 逆に、本文中の `---` より後に物理的な最終 CAB/AI-Agent block がある message は trailer なしと判定された。
- 放置時の受理集合:
  - 不正拡大: provenance block の後ろに `---` と任意本文が残る非末尾 message を受理する。
  - 不正縮小: 本文に Markdown 水平線 `---` を含み、その後の真の最終 trailer を持つ message を拒否する。
- 最小修正: commit message の parser は `git interpret-trailers --parse --no-divider` とする。両方向を境界テストに追加し、D98 に「format-patch stream ではなく commit message を検査する」と固定する。

### 2. HIGH / real / must-fix — ambient Git config で別の物理行同士を件数相殺できる

- file: [check_ai_provenance.py:44](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-t153e-t15423/tools/check_ai_provenance.py:44)、[check_ai_provenance.py:61](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-t153e-t15423/tools/check_ai_provenance.py:61)、[plan.md:24](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-t153e-t15423/output/insights/2026-07-29_t153e-t15423-review-verbatim/plan.md:24)
- 現在の repo には有効な `trailer.*` 設定はなかったが、checker は system/global/local/env config を継承する。
- 実測反例: `trailer.foo.key=Co-Authored-By:` の下では、本文側の raw `Co-Authored-By:` 1本と、最終 block の `Foo:` 1本が `raw=1, parsed CAB=1` になり、本文 CAB が trailer でなくても一致する。
- `trailer.separators=%:` や `trailer.co-authored-by.key=X-CAB:` では、正しい colon 形式が parsed CAB/AI-Agent として数えられず偽拒否になる。
- 放置時の受理集合:
  - 不正拡大: alias が生成した parsed CAB と、別位置の raw CAB が相殺される。
  - 不正縮小: separator/key canonicalization により通常形まで拒否される。
- 最小修正: parser を repo・global・system・env config から隔離し、canonical separator `:` と `--no-divider` を使う。単に `-c trailer.separators=:` を足すだけでは alias は残る。代替は関連 config が一つでも有効なら rc=2 で fail-closed。separator、alias、`core.commentChar` の境界テストが必要。

### 3. HIGH / real / must-fix — policy epoch 案が不在・非線形履歴で fail-open

- file: [plan.md:35](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-t153e-t15423/output/insights/2026-07-29_t153e-t15423-review-verbatim/plan.md:35)、[plan.md:43](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-t153e-t15423/output/insights/2026-07-29_t153e-t15423-review-verbatim/plan.md:43)、[check_ai_provenance.py:125](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-t153e-t15423/tools/check_ai_provenance.py:125)、[check_ai_provenance.py:142](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-t153e-t15423/tools/check_ai_provenance.py:142)、[check_ai_provenance.py:259](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-t153e-t15423/tools/check_ai_provenance.py:259)
- planner は既存 epoch helper と同様に、HEAD の `git log --reverse -S` の先頭1件を選ぶ案である。既存 main は epoch が `None` なら対応 finding を黙って捨てる。
- `--range` が HEAD に未統合の別 branch を含む場合、その branch 上の独立した policy 導入を HEAD 検索では発見できない。cherry-pick 等で独立導入が複数ある場合も先頭1件に潰れる。
- `_is_descendant()` は「非祖先」の rc=1 と Git 実行エラーをどちらも `False` にしており、後者も pre-epoch 扱いになる。
- 放置時の受理集合: needle 不在、別 lineage、Git graph エラー時に post-policy の分断 CAB commit が履歴監査で受理される。
- 最小修正: history mode で epoch 不在は rc=2。監査対象 graph に対して epoch を解決し、独立導入を集合として扱うか、非一意なら停止する。`merge-base` は rc=0/1以外を例外にする。linear pre/post に加え、needle 不在、別 branch、複数導入、Git error をテストする。

### 4. MEDIUM / real / must-fix — 「全 CAB 行」と raw candidate grammar が一致していない

- file: [brief.md:4](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-t153e-t15423/output/insights/2026-07-29_t153e-t15423-review-verbatim/brief.md:4)、[brief.md:15](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-t153e-t15423/output/insights/2026-07-29_t153e-t15423-review-verbatim/brief.md:15)、[plan.md:19](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-t153e-t15423/output/insights/2026-07-29_t153e-t15423-review-verbatim/plan.md:19)、[plan.md:20](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-t153e-t15423/output/insights/2026-07-29_t153e-t15423-review-verbatim/plan.md:20)
- planner の regex では、fence 内でも列頭の `Co-Authored-By:` や4空白 indent は raw CAB として拒否される。一方、`- Co-Authored-By:` と `> Co-Authored-By:` は raw 0件となり受理される。
- これは「全 CAB 行」ではなく「行頭に SP/HTAB を任意個置いた ASCII token」という別の集合である。Markdown 例示か実 attribution かは意味ではなく装飾文字だけで決まる。
- 放置時の受理集合: brief を字義どおり取れば bullet/quote 形を過剰受理し、実 trailer 候補だけを対象と解すれば fence 内の例示を過剰拒否する。
- 最小修正: D98 と policy に raw candidate の字句文法を明記する。完全な Markdown parser は不要だが、bullet、quote、列頭 fence、indent code の期待をテストで固定し、例示方法も示す。

### 5. MEDIUM / real / must-fix — D96 が要求する境界テスト集合が未閉鎖

- file: [plan.md:48](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-t153e-t15423/output/insights/2026-07-29_t153e-t15423-review-verbatim/plan.md:48)、[D96:4277](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-t153e-t15423/docs/decisions.md:4277)
- planner 表には continuation、CRLF、同一値の重複 CAB、body/code 装飾、divider、ambient config がない。
- Git 2.34.1 の canonical probe では次だった:
  - CAB の通常 continuation: raw 1 / parsed 1、受理。
  - CAB-looking な indented continuation: raw 1 / parsed 0、拒否。
  - CRLF: raw 1 / parsed 1、受理。
  - 同一 CAB 2本: raw 2 / parsed 2、受理。
- 「CAB 2行」だけでは exact duplicate を固定せず、set 化する変異を殺せない。行頭空白テストも、前 trailer への continuation と、block 全体を無効にする配置を区別していない。
- 放置時の受理集合: dedup、newline normalization、continuation handling の実装差で、合法 duplicate/CRLF を拒否するか、CAB-looking continuation を受理し得る。
- 最小修正: 上記を独立 fixture として追加する。duplicate は値検査を scope 外とするなら明示的に受理へ固定する。

### 6. MEDIUM / real（親 brief）・planner の修正案は妥当 / must-fix

- file: [brief.md:17](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-t153e-t15423/output/insights/2026-07-29_t153e-t15423-review-verbatim/brief.md:17)、[check_docs.py:159](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-t153e-t15423/tools/check_docs.py:159)、[check_docs.py:228](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-t153e-t15423/tools/check_docs.py:228)、[check_docs.py:1301](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-t153e-t15423/tools/check_docs.py:1301)、[plan.md:77](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-t153e-t15423/output/insights/2026-07-29_t153e-t15423-review-verbatim/plan.md:77)
- `SELF_LIMITS` へ追加すると `NORMATIVE_DISPATCH_ALLOWLIST` に provenance path が入る。特に bare path は `dispatch.paths` には入るが、後続 section token がなければ契約 pair を増やさないため、exact pair 検査を変えず allowlist 検査だけ通せる。
- 放置時の受理集合: CAB message 集合そのものは変わらないが、dev-wave の規範 dispatch が provenance 文書を leaf として参照する不正形を受理し、変更手続の受理集合が scope 外に広がる。
- 最小修正: planner 提案どおり独立 `PROVENANCE_LIMITS` を `all_limits` のみに合流し、dispatch allowlist 外であることを literal pin する。親 P2 は段4で覆すべき。

### 7. LOW / real だが planner で対処可能 — 8,817 bytes は将来適合性の証明ではない

- file: [brief.md:6](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-t153e-t15423/output/insights/2026-07-29_t153e-t15423-review-verbatim/brief.md:6)、[plan.md:99](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-t153e-t15423/output/insights/2026-07-29_t153e-t15423-review-verbatim/plan.md:99)
- working tree と HEAD blob はともに正確に 8,817 bytes だった。9,000 までの余白は183 bytesしかなく、この一標本から必須 policy 改訂が収まるとは言えない。
- 放置時の受理集合: 追記なら文書自身が拒否される。予算へ収めるため安全義務を削れば、byte gate は緑でも message の意味受理集合が広がる。
- 最小修正: planner の「置換・縮約、UTF-8実測、9000/9001境界」を採用し、安全義務を削らないことを停止条件にする。収まらなければ予算を黙って増減せず再裁定する。

### 8. NIT/BACKLOG / 数値は real、一般化は refuted

- file: [plan.md:9](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-t153e-t15423/output/insights/2026-07-29_t153e-t15423-review-verbatim/plan.md:9)
- 495 commit・不一致0件は再現した。ただし内訳は CAB なし238件、CABあり257件で、257件すべてが1本だけの厳密な `Co-Authored-By:` 形だった。mixed case、colon前空白、leading、CRLF、複数・重複、divider の既存例は0件。
- planner はこれを epoch 省略根拠にはしていないため、数値自体は問題ではない。成果物の受理集合を直接変えないので nit/backlog。
- 最小修正: 互換性観測を残すなら上記内訳を併記し、境界一般化の証拠として扱わない。

## 反証できなかった点

- case-insensitive と colon 前の SP/HTAB は Git 2.34.1 で raw 1 / parsed 1。
- 行頭 SP/HTAB 付き CAB は独立 trailer にならず、件数差または AI-Agent 形式違反で拒否できる。
- `CAB → 空行 → AI-Agent` は CAB mismatch、逆順は既存の AI-Agent 欠落で拒否される。
- contiguous な CAB と `AI-Agent: none` は受理できる。planner が CAB finding を全 early return に載せる方針も正しい。
- 複数・重複 CAB は件数比較なら multiplicity を保持する。
- したがって、canonical config、`--no-divider`、明示した raw grammar という前提を満たせば、件数一致と既存 AI-Agent 検査の積は「全 raw CAB が同じ最終 parsed block にある」を表せる。現プランはその前提をまだ満たしていない。

## 総括

判定は **NO-GO**。must-fix は、(1) `--no-divider` による commit-message 専用 parsing、(2) system/global/local/env の trailer alias・separator・comment 設定から独立した canonical parser、(3) epoch 不在・Git error・非線形/複数導入を fail-closed にする履歴モデル、(4) body/code/continuation/CRLF/完全重複を含む raw candidate grammar と境界テストの確定、(5) `SELF_LIMITS` ではない独立 budget registry、の5点です。特に divider と config alias は、raw 件数と parsed 件数が等しくても別の物理行が相殺される実反例であり、現状の「同じ最終 trailer block」という主張を直接破ります。D98 はこれらを受理集合として記録し、D97 が scope 外とした T-153(e) を別変更として閉じる必要があります。8,817 bytes と既存履歴0不一致はどちらも観測値としては正しいものの、安全性や一般形の根拠にはなりません。編集・pytest・runner 実行は行っておらず、検査緑は主張しません。