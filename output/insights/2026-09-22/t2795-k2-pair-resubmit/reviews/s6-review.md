## must-fix

- **M1 — real：見積りの説明が D2211 項 1 と食い違う。**
  [README.md:158](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2795-k2-pair-resubmit/output/insights/2026-09-22/t2795-k2-pair-resubmit/README.md:158)、[s1-brief.md:17](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2795-k2-pair-resubmit/output/insights/2026-09-22/t2795-k2-pair-resubmit/reviews/s1-brief.md:17)。候補のみの実測 69〜432 秒から pair を 3〜15 分と置き、brief は「D2211 の注意どおり」と説明している。しかし [decisions.md:70718](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2795-k2-pair-resubmit/docs/decisions.md:70718) は明示的に「pair の完走時間へ外挿しない」と定める。「仮定であり実測扱いしない」という限定だけでは一致しない。第31回項1にもこの禁止を解除する記述はない。
  当時の brief は保存し、記録本文にこの解釈差を開示する必要がある。後から得た Elapse 100 秒による取り直しと、初投入前の見積りは分けて記す。
  **成果物影響（DW-G05）：投入前の裁定遵守を過大に記録する。両 job の測定値・certified 判定には影響しない。**

## should

- **S1 — real：候補間差の不確かさを定量的に言い過ぎている。**
  [README.md:126](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2795-k2-pair-resubmit/output/insights/2026-09-22/t2795-k2-pair-resubmit/README.md:126) の「上の揺れと同じ桁の不確かさを含む」は、stock の別 job 1 対の差 +1.74% からは導けない。確認できるのは stock にも差が観測され、候補の +7.20% を設定効果へ帰属できないことまで。「job・node 差と分離できず、不確かさの大きさは未推定」とするのが適切。
  **成果物影響（DW-G05）：観測された stock 差を、候補間比較の不確かさの推定値と誤読させる。**

## nit

なし。

## 照合した数値 (一致)

原本 WAL から独立に再抽出し、比・率を検算した。

| 項目 | pair 再投入 | 4 巡目 |
|---|---:|---:|
| job / host | 16269.nqsv / bnode001 | 16312.nqsv / bnode052 |
| Elapse / driver_rc | 100秒 / 0 | 107秒 / 0 |
| 候補 / stock median tps | 825,490 / 348,883 | 884,922.5 / 354,948 |
| 候補反復値 | 830619, 820361 | 892103, 877742 |
| stock反復値 | 348858, 348908 | 358000, 351896 |
| CV：候補 / stock | 0.879% / 0.010% | 1.148% / 1.216% |
| 候補 / stock 比 | 2.366094… | 2.493104… |
| trace abort率：候補 / stock | 18.880% / 3.108% | 22.136% / 3.007% |
| perf abort率：候補 / stock | 9.01% / 1.815% | 10.105% / 1.835% |

差の検算も **+1.74% / +7.20% / +1.17% / +1.67%** と一致。Created・Started・Ended、commits・aborts、admission の class・policy・receipt・src_token、全4点の settled=true も一致した。

- **refuted：停止条件未達・rc依存の認定。**
  README.md:69、117。両 WAL は各10 record、候補・stock とも serializable / certified / anomaly 0、終端 commit。stock の BUILD_START は `src_token="stock"`。production の genome 式と `variant_id` を再計算して **602b4ce9c788** と一致した。
  **成果物影響：成立判定を撤回する根拠なし。**

- **refuted：入力への pair 結果混入・逐語からの組立て不一致。**
  README.md:75、93、148。current_perf / baseline、whiteboard、knowledge_input、leakproof_context、診断6 field、planner_direction は指定元と一致。両 prompt の JSON は対応する入力 JSON と一致し、pair 結果の混入なし。proposal-5 は planner・coder の逐語と一致した。再構成 SHA は **917ba3d3… / 66d3e737…**、255 / 32,979 B。
  **成果物影響：択Aの入力記録は支持される。実送付 bytes の一致までは認定しない。**

- **refuted：SHA・epoch差・正規化の記録不一致。**
  README.md:67、115、130、188。WAL・lock・loop_state・digest・受領証・claim の記録 SHA は `sha256sum` 再計算と一致。WAL は14,897 / 14,885 B、lock は両方12,003 B。closure は63→96 path、差37 / 42、初投入比の変更4 fileも一致。旧lockの厳密decode拒否を再確認した。MANIFESTは14/14一致。
  stdoutは **13,524→13,520 B / 13,505→13,501 B**、記載された全SHAと一致。変更は各29・72行の末尾空白だけで、`diff -w -B` は両方rc=0。他8 fileは原本とbytes一致。
  **成果物影響：証拠の転記・保存に修正を要する不一致なし。**

- **refuted：投入超過・過去本文改変・防護成果物のrepo複製・fragment形式違反。**
  README.md:45、101、195、round3 README.md:214、phase3.md:536、worklog fragment:24。qsub stdoutとattemptディレクトリは各1件。新treeのSHA・PIN・経路Hは記録と一致。round3は末尾追記のみ、実装差分なし。禁止されたcampaign成果物の複製なし。fragmentのH2・remaining・base・placeholder・新規T形式は適合し、base digest 2件も一致した。
  **成果物影響：記録範囲・台帳形式による阻害なし。**

主張限定は README.md:32、148 に存在する。別job・別node、stockの揺れ、配線限定、適応backoff、派生dataの同一性まで、送付bytes未照合、critic-4 / AO / 層3未実施を明記している。S1を除き、禁止された改善・一般化・因果・巡の完結を肯定する記述は認めなかった。

## 総括

**NO-GO（記録修正待ち）。** M1の裁定との解釈差を明示する必要がある。
両jobの成立、主要数値、入力の由来、SHA・正規化は一致。測定結果の撤回や再投入は不要。