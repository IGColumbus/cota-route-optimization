"""Release tooling for the COTA study: reproduction commands and the `cota-opt`
console entry point.

Kept outside ``src/cota_opt`` on purpose: the frozen experiment contracts pin a
content digest of ``src/cota_opt``, and release tooling must not change it.
"""
