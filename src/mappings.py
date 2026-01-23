# Hardcoded mappings from Alteryx Tool Types to KNIME Node Specs
# This serves as the "Law Book" to prevent hallucinations.

NODE_SPECS = {
    # --- Input/Output ---
    "DbFileInput": {
        "name": "CSV Reader",
        "factory": "org.knime.base.node.io.filehandling.csv.reader.CSVReaderNodeFactory",
        "bundle": "KNIME Base Nodes",
        "symbolic": "org.knime.base"
    },
    "DbFileInput_DB": {
        "name": "DB Query Reader",
        "factory": "org.knime.database.node.io.reader.query.DBQueryReaderNodeFactory",
        "bundle": "KNIME database nodes",
        "symbolic": "org.knime.database.nodes"
    },
    "DbFileOutput": {
        "name": "CSV Writer",
        "factory": "org.knime.base.node.io.filehandling.csv.writer.CSVWriterNodeFactory",
        "bundle": "KNIME Base Nodes",
        "symbolic": "org.knime.base"
    },
    "TextInput": {
        "name": "Table Creator",
        "factory": "org.knime.base.node.io.tablecreator.TableCreator2NodeFactory",
        "bundle": "KNIME Base Nodes",
        "symbolic": "org.knime.base"
    },
    
    # --- Preparation ---
    "Select": {
        "name": "Table Manipulator",
        "factory": "org.knime.base.node.preproc.manipulator.TableManipulatorNodeFactory",
        "bundle": "KNIME Base Nodes",
        "symbolic": "org.knime.base"
    },
    "AlteryxSelect": {
        "name": "Table Manipulator",
        "factory": "org.knime.base.node.preproc.manipulator.TableManipulatorNodeFactory",
        "bundle": "KNIME Base Nodes",
        "symbolic": "org.knime.base"
    },
    "Sort": {
        "name": "Sorter",
        "factory": "org.knime.base.node.preproc.sorter.SorterNodeFactory",
        "bundle": "KNIME Base Nodes",
        "symbolic": "org.knime.base"
    },
    "Filter": {
        "name": "Row Filter",
        "factory": "org.knime.base.node.preproc.filter.row.RowFilterNodeFactory",
        "bundle": "KNIME Base Nodes",
        "symbolic": "org.knime.base"
    },
    "Sample": {
        "name": "Row Sampling",
        "factory": "org.knime.base.node.preproc.sample.SamplingNodeFactory",
        "bundle": "KNIME Base Nodes",
        "symbolic": "org.knime.base"
    },
    "Unique": {
        "name": "Duplicate Row Filter",
        "factory": "org.knime.base.node.preproc.duplicates.DuplicateRowFilterNodeFactory",
        "bundle": "KNIME Base Nodes",
        "symbolic": "org.knime.base"
    },

    # --- Transformation ---
    "Formula": {
        "name": "Column Expressions (legacy)",
        "factory": "org.knime.expressions.base.node.formulas.FormulasNodeFactory",
        "bundle": "KNIME Expression Nodes",
        "symbolic": "org.knime.expressions.base"
    },
    "MultiRowFormula": {
        "name": "Column Expressions (legacy)",
        "factory": "org.knime.expressions.base.node.formulas.FormulasNodeFactory",
        "bundle": "KNIME Expression Nodes",
        "symbolic": "org.knime.expressions.base"
    },
    "Summarize": {
        "name": "GroupBy",
        "factory": "org.knime.base.node.preproc.groupby.GroupByNodeFactory",
        "bundle": "KNIME Base Nodes",
        "symbolic": "org.knime.base"
    },
    "Join": {
        "name": "Joiner",
        "factory": "org.knime.base.node.preproc.joiner3.Joiner3NodeFactory",
        "bundle": "KNIME Base Nodes",
        "symbolic": "org.knime.base"
    },
    "Union": {
        "name": "Concatenate",
        "factory": "org.knime.base.node.preproc.append.row.AppendedRowsNodeFactory",
        "bundle": "KNIME Base Nodes",
        "symbolic": "org.knime.base"
    },

    # --- Utility ---
    "BrowseV2": {
        "name": "Interactive Table",
        "factory": "org.knime.js.base.node.viz.table.TableNodeFactory",
        "bundle": "KNIME JavaScript Views",
        "symbolic": "org.knime.js.base"
    },
    
    # --- Default Fallback ---
    "Unknown": {
        "name": "Node",
        "factory": "org.knime.base.node.dummy.DummyNodeFactory",
        "bundle": "KNIME Base Nodes",
        "symbolic": "org.knime.base"
    }
}

def get_spec(alteryx_type, extra_config={}):
    """Retrieves KNIME specs for an Alteryx tool type."""
    
    # SPECIAL HANDLING: Check if DbFileInput is a Database
    if alteryx_type == "DbFileInput" and extra_config.get('input_type') == 'DB':
        return NODE_SPECS["DbFileInput_DB"]

    # Direct match
    if alteryx_type in NODE_SPECS:
        return NODE_SPECS[alteryx_type]
    
    return NODE_SPECS["Unknown"]