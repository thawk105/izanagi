---
schema: izanagi-spool-v1
ledger: failures
authored: 2026-09-11
wave: dev-wave-cc-next-precheck
seq: 1
---

## 再発

### F945

- **再発: 2026-09-10** — CC次実験precheckのdocs-only tip4d5b403b8で、T1259の実repo Git走査30秒timeoutが受入23setup errorと単独再走48setup errorになった。9月11日にmainのmodule snapshot化・実repo直列化を取り込み、tip76928e91eの2file焦点走991663.nqsvは262passed/20.57秒。判定本文・timeout・除外は変更しない。記録はoutput/insights/2026-09-11/cc-next-precheck-resume/README.md。

### F273

- **再発: 2026-09-10** — 同precheckの受入でtest_manifest_is_appended_while_correlated_session_is_runningの3秒内manifest不在とtest_sigterm_ignoring_child_is_killedの10秒TimeoutExpiredが発生。docsによるlauncher制御変更はなく、9月11日の同fileを含む焦点走991663.nqsvは262passed。恒久的な再発解消とは主張せず、既存DW-O18と今回のユーザーによる該当case限定hold認可に従って残る赤を扱う。
