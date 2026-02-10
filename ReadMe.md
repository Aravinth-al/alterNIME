# Alteryx to KNIME Migration Status

**Date:** February 10, 2026
**Version:** 2.0

This document outlines the current conversion capabilities of the migration tool, including new tools identified from your workflow diagrams.

### Fully Supported Tools
The following tools are extracted, analyzed, and converted into valid, pre-configured KNIME nodes.

- [x] **Input Data (Oracle)**: Converts to *Oracle Connector* and *DB Query Reader*. Supports "Gold Image" templates.
- [x] **Select**: Converts to *Table Manipulator*. Handles renaming, type changes, and column selection.
- [x] **Sort**: Converts to *Sorter*. Maps ascending and descending sort orders.
- [x] **Formula**: Converts to *Column Expressions*. Translates Alteryx syntax to JavaScript.
- [x] **Multi-Row Formula**: Converts to *Column Expressions*.
- [x] **Summarize**: Converts to *GroupBy*. Maps grouping fields and aggregation methods.
- [x] **Join**: Converts to *Joiner*. Configures left/right join keys and column collisions.
- [x] **Union**: Converts to *Concatenate*. Configures union by name.
- [x] **Browse**: Explicitly handled (removed to keep workflows clean).

### Pending Support (Shell Nodes)
The following tools are recognized and placed on the canvas as the correct KNIME node type, but currently require manual configuration after migration.

- [ ] **Input Data (CSV/Excel)**: Maps to *CSV Reader* / *Excel Reader*.
- [ ] **Output Data**: Maps to *CSV Writer* / *Excel Writer*.
- [ ] **Text Input**: Maps to *Table Creator*.
- [ ] **Filter**: Maps to *Row Filter*.
- [ ] **Unique**: Maps to *Duplicate Row Filter*.
- [ ] **Sample**: Maps to *Row Sampling*.
- [ ] **Message**: Maps to *Breakpoint* (Validation logic).
- [ ] **Interface Tools**: Maps to *Configuration Nodes* (Text Box, Action, etc. for Analytic Apps).