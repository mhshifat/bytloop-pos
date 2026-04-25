"""Bookstore — no tables.

This module is intentionally entity-less. Books are ordinary catalog
``Product`` rows whose ``barcode`` holds the ISBN; the bookstore's only
vertical-specific behaviour is ISBN-10 ↔ ISBN-13 normalization on lookup,
which is pure computation. Adding a table here would just duplicate
``products.barcode`` and invite drift.

The file exists so the module still has the standard six-file shape
(``__init__``, ``entity``, ``schemas``, ``service``, ``router``, ``api``)
and so future structured-metadata work has an obvious landing pad.
"""

from __future__ import annotations

__all__: list[str] = []
