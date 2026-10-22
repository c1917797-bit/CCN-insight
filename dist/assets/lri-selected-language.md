# LRI selected display language

Canonical entry: `assets/lri-selected-language.js`. This is a read-only adapter over the existing `lri-site-shell` owner and `lri:locale-change` event, not another selector or translation engine.

## API and precedence

- `readSelectedLanguage(document?)` returns `zh` or `en`.
- `subscribeSelectedLanguage(listener, {document?, immediate?, signal?})` delivers the initial selection unless `immediate:false`, then only changed selections. It returns an idempotent unsubscribe function. AbortSignal disposes the subscription.
- `normalizeSelectedLanguage(value)` accepts supported tags such as `en-US` and `zh-CN`; unsupported or malformed values return null.

Resolution order: live `lri-site-shell.locale`; a valid Shell event observed for this document while its owner is absent; the existing `lri_locale` stored preference; source language only when no selected-language authority is available; finally `zh`.

The weakly referenced per-document event cache is not a new persistent preference. A live Shell supersedes it. The adapter never writes localStorage, `documentElement.lang` or the URL, emits no new locale event and controls no player.

The document/source language may remain Chinese while the user's selection is English. Source metadata changes cause a reread, never an instruction to switch the display. Valid events are emitted after the Shell updates its own locale; invalid or duplicate events do not force redraws.

Refresh and new pages read the Shell/preference; `pageshow` reconciles a retained document. Storage events only reread the live owner. Cross-tab ownership is not introduced.

## Responsibility and integration

The motion owner integrates architecture, brochure and flywheel players. A locale callback rerenders through the player's existing state-preserving API; it must not reset time, pause, scene/chapter, scenario, selected product, V1/V2 or current region. Async artwork replacement retains its request fence. These properties belong to motion and are not implemented or proven by this adapter.

The reader owner integrates the shared topic reader. This task owns utility/contract and its assigned self-topic consumer scope only. Same-file edits by another owner require coordination. Original source prose, facts, dates and evidence are unchanged.

## Validation and current boundary

`node research_domains/lrigit/validate-selected-language.mjs` checks precedence, source-language noninterference, invalid/duplicate events, absent Shell, disabled storage, reload initialization, pageshow and disposal.

Browser checks must independently compare the real Shell and adapter after normal controls, reload, navigation and reflow. Player-state acceptance is separate.

Handoff: `research_domains/lrigit/sources/selected-language-handoff-20261007.md`. This stage delivers the utility only: consumer integration was refused by the tool and remains undeployed. Do not enact the refused patch through this document, another tool or another owner as a workaround.

