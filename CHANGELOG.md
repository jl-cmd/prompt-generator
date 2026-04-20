# Changelog

## [1.7.0](https://github.com/jl-cmd/prompt-generator/compare/v1.6.0...v1.7.0) (2026-04-20)


### Features

* **pmax:** add incremental prompt-builder skill ([#37](https://github.com/jl-cmd/prompt-generator/issues/37)) ([43d6408](https://github.com/jl-cmd/prompt-generator/commit/43d6408b859dd6da57e41c7f0a68681a67ce3224))

## [1.6.0](https://github.com/jl-cmd/prompt-generator/compare/v1.5.1...v1.6.0) (2026-04-16)


### Features

* **pmin:** add eval 8 for compound investigate+implement scope boundary ([#31](https://github.com/jl-cmd/prompt-generator/issues/31)) ([c9593e0](https://github.com/jl-cmd/prompt-generator/commit/c9593e028ed424e0af8705215b3f9d393a4cab9f))
* **pmin:** add nested-backtick fence safety rule and eval ([#25](https://github.com/jl-cmd/prompt-generator/issues/25)) ([8ef66f1](https://github.com/jl-cmd/prompt-generator/commit/8ef66f167f7c033b7bd07982584913d61cdf385d))

## [1.5.1](https://github.com/jl-cmd/prompt-generator/compare/v1.5.0...v1.5.1) (2026-04-16)


### Bug Fixes

* add actions/checkout@v4 before claude-code-action ([4b16bce](https://github.com/jl-cmd/prompt-generator/commit/4b16bce3efc1109af153219deebe44d2d6bd49d9))
* switch to claude_code_oauth_token for Claude Max ([e3285d9](https://github.com/jl-cmd/prompt-generator/commit/e3285d9f76c06ba3a8db1ab7e2f02b39b978df2d))

## [1.5.0](https://github.com/jl-cmd/prompt-generator/compare/v1.4.0...v1.5.0) (2026-04-15)


### Features

* add automated eval runner for pmid and pmin (10/10 pass) ([#23](https://github.com/jl-cmd/prompt-generator/issues/23)) ([8fcbfe3](https://github.com/jl-cmd/prompt-generator/commit/8fcbfe3ced815c9606e93f8fe97c4edbf027a0d6))

## [1.4.0](https://github.com/jl-cmd/prompt-generator/compare/v1.3.0...v1.4.0) (2026-04-15)


### Features

* add outcome digest and scope-boundary evals for prompt-generator, pmid, and pmin ([#20](https://github.com/jl-cmd/prompt-generator/issues/20)) ([4e714d3](https://github.com/jl-cmd/prompt-generator/commit/4e714d34a1d441bad217fc8050b1ce42a4b3dcb9))

## [1.3.0](https://github.com/jl-cmd/prompt-generator/compare/v1.2.1...v1.3.0) (2026-04-15)


### Features

* include pmid and pmin skills in published package ([#18](https://github.com/jl-cmd/prompt-generator/issues/18)) ([3f4eced](https://github.com/jl-cmd/prompt-generator/commit/3f4eceddb86c1c99ad22c917c631ccf93c19f222))

## [1.2.1](https://github.com/jl-cmd/prompt-generator/compare/v1.2.0...v1.2.1) (2026-04-15)


### Bug Fixes

* address naming and magic-value feedback in prompt_workflow_gate_core ([bb9c08f](https://github.com/jl-cmd/prompt-generator/commit/bb9c08f98b8fcffb4778b6274b5365bae3b06157))
* collapse double blank lines between test functions to single ([c7000be](https://github.com/jl-cmd/prompt-generator/commit/c7000be505bc86aecbb8eae57fcdaff051e47f0c))
* match headers at column 0 only, skip fenced code blocks ([dada1e9](https://github.com/jl-cmd/prompt-generator/commit/dada1e90b091e60be29e50b640cf1b40417f6caa))
* match plan headers at column 0 only, skip fenced code blocks ([c4000c0](https://github.com/jl-cmd/prompt-generator/commit/c4000c0a6db88104a760efd3deee7e116c86dff6))
* port digit-leading tag name guard from llm-settings PR[#11](https://github.com/jl-cmd/prompt-generator/issues/11) ([e63e2d0](https://github.com/jl-cmd/prompt-generator/commit/e63e2d0e81efb0ff4d604ea9d3248c2cf6bbcf79))

## [1.2.0](https://github.com/jl-cmd/prompt-generator/compare/v1.1.0...v1.2.0) (2026-04-15)


### Features

* add /pmid mid-tier skill and finalize /pmin ([0ee2395](https://github.com/jl-cmd/prompt-generator/commit/0ee23957e770295e41a6ad84da4ec997af2c1453))
* add /pmin and /pmid XML formatter skills ([80dd5cb](https://github.com/jl-cmd/prompt-generator/commit/80dd5cb1250f006e191d93e2f42742e4fb8c1656))
* add /pmin single-pass XML formatter skill ([3d00181](https://github.com/jl-cmd/prompt-generator/commit/3d00181d3929e71482f994c04ef8bd8e46b9232f))


### Bug Fixes

* address Copilot review comments on pmin skill ([bb060b5](https://github.com/jl-cmd/prompt-generator/commit/bb060b56a563f082689065c2c344b74010d3be92))
* address Copilot review round 2 and clean up negative-keyword violations ([4b6aef4](https://github.com/jl-cmd/prompt-generator/commit/4b6aef442bc4bffbc372464b66de7f5f61a9afee))
* address Copilot review round 3 — output contract consistency and anti-pattern fix ([8c4eb9c](https://github.com/jl-cmd/prompt-generator/commit/8c4eb9c92cc080566cffadc5742a71f33e4761cf))
* address Copilot round 5 — outcome digest heading, validator stderr wording, test rename ([1b8edf9](https://github.com/jl-cmd/prompt-generator/commit/1b8edf99feb71265696d76f6a21a3556c54163d2))
* address Copilot/Cursor round 4 comments on pmid skill ([f710fab](https://github.com/jl-cmd/prompt-generator/commit/f710fab0b78b8f5d731d673ec1948fb9b5321edf))

## [1.1.0](https://github.com/jl-cmd/prompt-generator/compare/v1.0.1...v1.1.0) (2026-04-14)


### Features

* replace discovery phase with plan-mode deep-dive in prompt-generator ([741f6d1](https://github.com/jl-cmd/prompt-generator/commit/741f6d19eba1b029e387babe11d224f136a20e2c))
* replace discovery phase with plan-mode deep-dive in prompt-generator ([fd06c31](https://github.com/jl-cmd/prompt-generator/commit/fd06c31718344fae99dbd8843aa2bc810e744e15))

## [1.0.1](https://github.com/jl-cmd/prompt-generator/compare/v1.0.0...v1.0.1) (2026-04-13)


### Bug Fixes

* add CHANGELOG.md referenced by package files ([3c29e14](https://github.com/jl-cmd/prompt-generator/commit/3c29e1466d6e34407e03b1fa51ee2a1635d46606))
* add CHANGELOG.md referenced by package files ([82e01f0](https://github.com/jl-cmd/prompt-generator/commit/82e01f042bfb8e4cd103ddf82d56c0614ff018cf))

## [1.0.0](https://github.com/jl-cmd/prompt-generator/releases/tag/v1.0.0) (2026-04-12)

Initial published release of the prompt-generator and agent-prompt skills package.
