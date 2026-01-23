import os
import zipfile
import json
from src import config, mappings, formula_converter

# --- XML TEMPLATES ---

WORKFLOW_TEMPLATE = """<?xml version="1.0" encoding="UTF-8"?>
<config xmlns="http://www.knime.org/2008/09/XMLConfig" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xsi:schemaLocation="http://www.knime.org/2008/09/XMLConfig http://www.knime.org/XMLConfig_2008_09.xsd" key="workflow.knime">
    <entry key="created_by" type="xstring" value="5.1.0"/>
    <entry key="version" type="xstring" value="5.1.0"/>
    <entry key="name" type="xstring" isnull="true" value=""/>
    <config key="authorInformation">
        <entry key="authored-by" type="xstring" value="alterNIME"/>
        <entry key="authored-when" type="xstring" value="2026-01-01 00:00:00 +0000"/>
    </config>
    <config key="workflow_credentials"/>
    <config key="nodes">
{nodes_block}
    </config>
    <config key="connections">
{connections_block}
    </config>
</config>
"""

NODE_ENTRY_TEMPLATE = """        <config key="node_{index}">
            <entry key="id" type="xint" value="{knime_id}"/>
            <entry key="node_settings_file" type="xstring" value="{folder_name}/settings.xml"/>
            <entry key="node_is_meta" type="xboolean" value="false"/>
            <entry key="node_type" type="xstring" value="NativeNode"/>
            <entry key="ui_classname" type="xstring" value="org.knime.core.node.workflow.NodeUIInformation"/>
            <config key="ui_settings">
                <config key="extrainfo.node.bounds">
                    <entry key="array-size" type="xint" value="4"/>
                    <entry key="0" type="xint" value="{x}"/>
                    <entry key="1" type="xint" value="{y}"/>
                    <entry key="2" type="xint" value="-1"/>
                    <entry key="3" type="xint" value="-1"/>
                </config>
            </config>
        </config>"""

CONNECTION_TEMPLATE = """        <config key="connection_{index}">
            <entry key="sourceID" type="xint" value="{source_id}"/>
            <entry key="destID" type="xint" value="{dest_id}"/>
            <entry key="sourcePort" type="xint" value="{source_port}"/>
            <entry key="destPort" type="xint" value="{dest_port}"/>
        </config>"""

# --- NODE SPECIFIC SETTINGS TEMPLATES ---

# 1. Base Generic Shell
SETTINGS_TEMPLATE = """<?xml version="1.0" encoding="UTF-8"?>
<config xmlns="http://www.knime.org/2008/09/XMLConfig" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xsi:schemaLocation="http://www.knime.org/2008/09/XMLConfig http://www.knime.org/XMLConfig_2008_09.xsd" key="settings.xml">
    <entry key="node_file" type="xstring" value="settings.xml"/>
    <config key="flow_stack"/>
    <config key="internal_node_subsettings">
        <entry key="memory_policy" type="xstring" value="CacheSmallInMemory"/>
    </config>
    <config key="model">
        {model_content}
    </config>
    <entry key="customDescription" type="xstring" isnull="true" value=""/>
    <entry key="state" type="xstring" value="IDLE"/>
    <entry key="factory" type="xstring" value="{factory}"/>
    <entry key="node-name" type="xstring" value="{name}"/>
    <entry key="node-bundle-name" type="xstring" value="{bundle}"/>
    <entry key="node-bundle-symbolic-name" type="xstring" value="{symbolic}"/>
    <entry key="node-bundle-vendor" type="xstring" value="KNIME AG, Zurich, Switzerland"/>
    <entry key="node-bundle-version" type="xstring" value="5.1.0"/>
    <config key="factory_settings"/>
    <entry key="name" type="xstring" value="{name}"/>
    <entry key="hasContent" type="xboolean" value="false"/>
    <entry key="isInactive" type="xboolean" value="false"/>
    <config key="ports">
        <config key="port_1">
            <entry key="index" type="xint" value="1"/>
            <entry key="port_dir_location" type="xstring" isnull="true" value=""/>
        </config>
        <config key="port_2">
            <entry key="index" type="xint" value="2"/>
            <entry key="port_dir_location" type="xstring" isnull="true" value=""/>
        </config>
        <config key="port_3">
            <entry key="index" type="xint" value="3"/>
            <entry key="port_dir_location" type="xstring" isnull="true" value=""/>
        </config>
    </config>
</config>
"""

# 2. DB Query Reader Content
DB_QUERY_CONTENT = """
<entry key="sql_statement" type="xstring" value="{sql_query}"/>
<config key="external_to_knime_mapping_Internals">
    <entry key="SettingsModelID" type="xstring" value="SMID_dataTypeMapping"/>
    <entry key="EnabledStatus" type="xboolean" value="true"/>
</config>
"""

# 3. Oracle Connector Content
ORACLE_CONNECTOR_CONTENT = """
<config key="oracle-connection">
    <entry key="host" type="xstring" value="{host}"/>
    <entry key="port" type="xint" value="{port}"/>
    <entry key="database_name" type="xstring" value="{database_name}"/>
</config>
<config key="authentication">
    <entry key="username" type="xstring" value="{username}"/>
    <entry key="selectedType" type="xstring" value="USER_PWD"/>
</config>
"""

def get_groupby_model(config_data):
    """Generates GroupBy settings with correctly mapped aggregations."""
    summarize_fields = config_data.get('summarize_fields', [])
    group_cols = [f['field'] for f in summarize_fields if f.get('action') == 'GroupBy']
    agg_fields = [f for f in summarize_fields if f.get('action') != 'GroupBy']

    # Group Columns
    groupby_xml = f"""<config key="grouByColumns">
        <config key="InclList"><entry key="array-size" type="xint" value="{len(group_cols)}"/>"""
    for i, col in enumerate(group_cols):
        groupby_xml += f'\n            <entry key="{i}" type="xstring" value="{col}"/>'
    groupby_xml += """
        </config>
        <config key="ExclList"><entry key="array-size" type="xint" value="0"/></config>
        <entry key="keep_all_columns_selected" type="xboolean" value="false"/>
    </config>"""

    # Aggregation Columns
    agg_map = {"Sum": "Sum_V2.5.2", "Count": "Count", "Min": "Min", "Max": "Max", "Avg": "Mean", "Concat": "List"}
    count = len(agg_fields)
    
    agg_cols_xml = f"""<config key="aggregationColumn">
        <config key="columnNames"><entry key="array-size" type="xint" value="{count}"/>"""
    for i, field in enumerate(agg_fields):
        agg_cols_xml += f'\n            <entry key="{i}" type="xstring" value="{field["field"]}"/>'
    agg_cols_xml += f"""
        </config>
        <config key="columnTypes"><entry key="array-size" type="xint" value="{count}"/>"""
    for i in range(count):
         agg_cols_xml += f'\n            <entry key="{i}" type="xstring" value="String"/>'
    agg_cols_xml += f"""
        </config>
        <config key="aggregationMethod"><entry key="array-size" type="xint" value="{count}"/>"""
    for i, field in enumerate(agg_fields):
        method = agg_map.get(field.get('action'), "Count")
        agg_cols_xml += f'\n            <entry key="{i}" type="xstring" value="{method}"/>'
    agg_cols_xml += f"""
        </config>
        <config key="inclMissingVals"><entry key="array-size" type="xint" value="{count}"/>"""
    for i in range(count):
         agg_cols_xml += f'\n            <entry key="{i}" type="xboolean" value="false"/>'
    agg_cols_xml += "\n        </config>\n    </config>"

    return f"""
    {groupby_xml}
    <config key="maxNoneNumericalVals_Internals">
        <entry key="SettingsModelID" type="xstring" value="SMID_integer"/>
        <entry key="EnabledStatus" type="xboolean" value="true"/>
    </config>
    <entry key="maxNoneNumericalVals" type="xint" value="10000"/>
    <entry key="enableHilite" type="xboolean" value="false"/>
    <entry key="valueDelimiter" type="xstring" value=", "/>
    <entry key="sortInMemory" type="xboolean" value="false"/>
    <entry key="columnNamePolicy" type="xstring" value="Keep original name(s)"/>
    {agg_cols_xml}
    <config key="aggregationOperatorSettings"/>
    <config key="patternAggregators"/>
    <config key="dataTypeAggregators"/>
    <entry key="retainOrder" type="xboolean" value="false"/>
    <entry key="inMemory" type="xboolean" value="false"/>
    <entry key="nodeVersion" type="xint" value="1"/>
    <entry key="typeMatch" type="xbyte" value="0"/>
    """

def get_joiner_model(config_data):
    """Generates Joiner settings with correct output ports and column filters."""
    join_keys = config_data.get('join_keys', [])
    select_fields = config_data.get('select_fields', [])
    
    # Process extracted join keys
    left_cols = []
    right_cols = []
    for item in join_keys:
        if item['side'] == 'Left': left_cols = item['cols']
        if item['side'] == 'Right': right_cols = item['cols']
    
    # Matching Criteria
    min_len = min(len(left_cols), len(right_cols))
    left_cols = left_cols[:min_len]
    right_cols = right_cols[:min_len]

    criteria_block = ""
    for idx, (l_col, r_col) in enumerate(zip(left_cols, right_cols)):
         criteria_block += f"""<config key="{idx}">
            <config key="leftTableColumnV2">
                <entry key="regularChoice" type="xstring" value="{l_col}"/>
                <entry key="specialChoice_Internals" type="xstring" isnull="true" value=""/>
            </config>
            <config key="rightTableColumnV2">
                <entry key="regularChoice" type="xstring" value="{r_col}"/>
                <entry key="specialChoice_Internals" type="xstring" isnull="true" value=""/>
            </config>
        </config>"""

    # Manual Filter Configuration
    # We filter out columns that were explicitly deselected in Alteryx
    deselected_cols = [f['field'] for f in select_fields if f.get('selected') == 'False']
    
    def get_manual_filter(deselected):
        xml = f"""<config key="manualFilter">
            <config key="manuallySelected">
                <entry key="array-size" type="xint" value="0"/>
            </config>
            <config key="manuallyDeselected">
                <entry key="array-size" type="xint" value="{len(deselected)}"/>"""
        for i, col in enumerate(deselected):
            xml += f'\n                <entry key="{i}" type="xstring" value="{col}"/>'
        xml += """
            </config>
            <entry key="includeUnknownColumns" type="xboolean" value="true"/>
        </config>"""
        return xml

    manual_filter_block = get_manual_filter(deselected_cols)

    return f"""
    <entry key="compositionMode" type="xstring" value="MATCH_ALL"/>
    <config key="matchingCriteria">
        {criteria_block}
    </config>
    <entry key="dataCellComparisonMode" type="xstring" value="STRICT"/>
    <entry key="includeMatchesInOutput" type="xboolean" value="true"/>
    <entry key="includeLeftUnmatchedInOutput" type="xboolean" value="true"/>
    <entry key="includeRightUnmatchedInOutput" type="xboolean" value="true"/>
    <entry key="outputUnmatchedRowsToSeparatePorts" type="xboolean" value="true"/>
    
    <config key="leftColumnSelectionConfigV2">
        <entry key="mode" type="xstring" value="MANUAL"/>
        <config key="patternFilter">
            <entry key="pattern" type="xstring" value=""/>
            <entry key="isCaseSensitive" type="xboolean" value="false"/>
            <entry key="isInverted" type="xboolean" value="false"/>
        </config>
        {manual_filter_block}
        <config key="typeFilter">
            <config key="selectedTypes">
                <entry key="array-size" type="xint" value="0"/>
            </config>
        </config>
    </config>
    
    <config key="rightColumnSelectionConfigV2">
        <entry key="mode" type="xstring" value="MANUAL"/>
        <config key="patternFilter">
            <entry key="pattern" type="xstring" value=""/>
            <entry key="isCaseSensitive" type="xboolean" value="false"/>
            <entry key="isInverted" type="xboolean" value="false"/>
        </config>
        {manual_filter_block}
        <config key="typeFilter">
            <config key="selectedTypes">
                <entry key="array-size" type="xint" value="0"/>
            </config>
        </config>
    </config>
    
    <entry key="mergeJoinColumns" type="xboolean" value="false"/>
    <entry key="duplicateHandling" type="xstring" value="APPEND_SUFFIX"/>
    <entry key="suffix" type="xstring" value=" (Right)"/>
    <entry key="rowKeyFactory" type="xstring" value="CONCATENATE"/>
    <entry key="rowKeySeparator" type="xstring" value="_"/>
    <entry key="outputRowOrder" type="xstring" value="ARBITRARY"/>
    <entry key="maxOpenFiles" type="xint" value="200"/>
    <entry key="enableHiliting" type="xboolean" value="false"/>
    """

def get_expression_model(config_data):
    """
    Generates Column Expressions settings using AI transpiler.
    """
    formulas = config_data.get('formulas', [])
    
    elements_xml = ""
    for i, item in enumerate(formulas):
        raw_expr = item.get('expression', '')
        
        # USE NEW AI CONVERTER
        print(f"      [AI] Converting formula for field: {item.get('field', 'Unknown')}")
        js_code = formula_converter.convert_alteryx_formula(raw_expr)
        
        # Escape for XML
        js_code_safe = js_code.replace('\n', '%%00010').replace('"', '&quot;').replace('<', '&lt;').replace('>', '&gt;')
        
        out_col = item.get('field', f'Column{i}')
        
        elements_xml += f"""
        <config key="element {i}">
            <entry key="expression" type="xstring" value="{js_code_safe}"/>
            <entry key="outputName" type="xstring" value="{out_col}"/>
            <config key="outputType">
                <entry key="cell_class" type="xstring" value="org.knime.core.data.def.StringCell"/>
                <entry key="is_null" type="xboolean" value="false"/>
            </config>
            <entry key="replaceColumn" type="xboolean" value="false"/>
            <entry key="isCollection" type="xboolean" value="false"/>
        </config>"""

    return f"""
    <config key="expressions">
        {elements_xml}
    </config>
    <entry key="count" type="xint" value="{len(formulas)}"/>
    <entry key="failOnInvalidAccess" type="xboolean" value="true"/>
    <entry key="failOnScriptError" type="xboolean" value="false"/>
    <entry key="multiRowAccessWindowSize" type="xint" value="0"/>
    <entry key="multiRowAccessReturnFirstLastWhenOutOfBounds" type="xboolean" value="true"/>
    """

def get_concatenate_model(config_data):
    """Generates Concatenate (Union) settings."""
    return """
    <entry key="create_new_rowids" type="xboolean" value="true"/>
    <entry key="fail_on_duplicates" type="xboolean" value="false"/>
    <entry key="append_suffix" type="xboolean" value="false"/>
    <entry key="intersection_of_columns" type="xboolean" value="false"/>
    <entry key="suffix" type="xstring" value="_dup"/>
    <entry key="enable_hiliting" type="xboolean" value="false"/>
    """

def get_table_manipulator_model(config_data):
    """
    Generates Table Manipulator settings based on Alteryx Select tool.
    Constructs the table_spec_config_Internals block.
    """
    select_fields = config_data.get('select_fields', [])
    
    # --- DEBUG START ---
    print(f"\n[TableManipulator] Processing Node...")
    print(f"   Input Fields Count: {len(select_fields)}")
    if len(select_fields) > 0:
        print(f"   Sample Fields: {[f['field'] for f in select_fields[:3]]}...")
    else:
        print("   WARNING: No fields found in config. KNIME will default to keeping all columns (Unknown=True).")
    # --- DEBUG END ---
    
    # Filter only selected fields or fields that are renamed
    # Alteryx *Unknown field usually handles dynamic columns. 
    # KNIME's Table Manipulator has a specific "unknown_columns_transformation" block for this.
    
    # We need to build the 'columns' config block.
    # Since we don't have true input indices, we'll assign arbitrary indices 0..N
    
    columns_config = ""
    valid_fields = [f for f in select_fields if f['field'] != '*Unknown']
    
    for i, field in enumerate(valid_fields):
        original_name = field['field']
        new_name = field.get('rename', original_name) # Default to original if no rename
        
        # Alteryx Logic: selected="True" (String). Default is True if missing? Usually explicit.
        is_selected = field.get('selected') == 'True'
        
        # DEBUG: Print selection status for first few or dropped cols
        if not is_selected:
             print(f"   -> Dropping Column: {original_name}")

        # We assume String type for all to avoid crashes, as we don't know upstream types
        columns_config += f"""
        <config key="{i}">
            <config key="external_spec">
                <entry key="name" type="xstring" value="{original_name}"/>
                <entry key="has_type" type="xboolean" value="true"/>
                <config key="type">
                    <config key="type">
                        <entry key="cell_class" type="xstring" value="org.knime.core.data.def.StringCell"/>
                        <entry key="is_null" type="xboolean" value="false"/>
                    </config>
                </config>
            </config>
            <entry key="name" type="xstring" value="{new_name}"/>
            <entry key="keep" type="xboolean" value="{str(is_selected).lower()}"/>
            <entry key="position" type="xint" value="{i}"/>
            <config key="production_path">
                <entry key="_converter" type="xstring" value="CELL_CONVERTER_IDENTITY_FACTORY"/>
                <entry key="_converter_src" type="xstring" value="org.knime.core.data.DataCell"/>
                <entry key="_converter_dst" type="xstring" value="String"/>
                <entry key="_converter_name" type="xstring" value=""/>
                <config key="_converter_config">
                    <entry key="cell_class" type="xstring" value="org.knime.core.data.def.StringCell"/>
                </config>
                <entry key="_producer" type="xstring" value="CELL_VALUE_PRODUCER_IDENTITY_FACTORY"/>
                <entry key="_producer_src" type="xstring" value="String"/>
                <entry key="_producer_dst" type="xstring" value="org.knime.core.data.DataCell"/>
                <entry key="_producer_name" type="xstring" value="org.knime.core.data.DataCell"/>
                <config key="_producer_config">
                    <entry key="cell_class" type="xstring" value="org.knime.core.data.def.StringCell"/>
                </config>
            </config>
        </config>"""

    # Handle *Unknown (Dynamic Columns)
    # Alteryx: <SelectField field="*Unknown" selected="True" />
    unknown_field = next((f for f in select_fields if f['field'] == '*Unknown'), None)
    
    keep_unknown = "true" # Default if no config found (Pass-through safe mode)
    
    if unknown_field:
        if unknown_field.get('selected') == 'False':
            keep_unknown = "false"
        print(f"   -> *Unknown Field Found. Selected={unknown_field.get('selected')} -> KNIME keep={keep_unknown}")
    else:
        print(f"   -> *Unknown Field NOT Found. Defaulting to KNIME keep={keep_unknown}")

    return f"""
    <config key="table_spec_config_Internals">
        <entry key="version" type="xstring" value="V4_4"/>
        <config key="individual_specs">
            <config key="org.knime.base.node.preproc.manipulator.table.DataTableBackedBoundedTable@6bd64fab">
                <entry key="num_columns" type="xint" value="{len(valid_fields)}"/>
                {columns_config}
            </config>
        </config>
        <config key="table_transformation">
            <config key="columns">
                {columns_config}
            </config>
            <entry key="skip_empty_columns" type="xboolean" value="false"/>
            <entry key="enforce_types" type="xboolean" value="true"/>
            <entry key="column_filter_mode" type="xstring" value="UNION"/>
            <config key="unknown_columns_transformation">
                <entry key="position" type="xint" value="{len(valid_fields)}"/>
                <entry key="keep" type="xboolean" value="{keep_unknown}"/>
                <entry key="force_type" type="xboolean" value="false"/>
            </config>
        </config>
        <entry key="source_group_id" type="xstring" value="org.knime.base.node.preproc.manipulator.table.EmptyTable@5339229c"/>
        <config key="config_id">
            <config key="table_manipulator"/>
        </config>
    </config>
    <config key="settings">
        <entry key="has_row_id" type="xboolean" value="false"/>
        <entry key="prepend_table_index_to_row_id" type="xboolean" value="false"/>
    </config>
    """

def build_skeleton(graph_data):
    output_path = os.path.join(config.OUTPUT_DIR, "skeleton.knwf")
    print(f"🏗️  Building Skeleton to {output_path}...")

    nodes_xml_parts = []
    conns_xml_parts = []
    zip_contents = {} 
    
    id_map = {}
    current_knime_id = 1
    node_entries_count = 0
    
    # --- 1. PROCESS NODES ---
    for node in graph_data['nodes']:
        alteryx_id = node['id']
        tool_type = node['type']
        
        # SKIP BROWSE NODES (As requested)
        if tool_type == "BrowseV2":
            print(f"      [SKIP] Ignoring Browser Tool {alteryx_id}")
            continue

        nodes_to_create = []
        
        if tool_type == "DbFileInput" and node['config'].get('input_type') == 'DB':
            nodes_to_create.append({
                "spec": {
                    "name": "Oracle Connector",
                    "factory": "org.knime.database.extension.oracle.node.connector.OracleDBConnectorNodeFactory",
                    "bundle": "KNIME Oracle database extension",
                    "symbolic": "org.knime.database.extensions.oracle"
                },
                "config": node['config'],
                "offset_x": 0, "offset_y": -80
            })
            nodes_to_create.append({
                "spec": mappings.get_spec("DbFileInput_DB", node['config']),
                "config": node['config'],
                "offset_x": 0, "offset_y": 0
            })
        else:
            nodes_to_create.append({
                "spec": mappings.get_spec(tool_type, node['config']),
                "config": node['config'],
                "offset_x": 0, "offset_y": 0
            })

        created_knime_ids = []
        
        for n_def in nodes_to_create:
            knime_id = current_knime_id
            current_knime_id += 1
            created_knime_ids.append(knime_id)
            
            spec = n_def['spec']
            folder_name = f"{spec['name']} (#{knime_id})"
            
            model_block = ""
            if spec['name'] == "DB Query Reader":
                raw_sql = n_def['config'].get('sql_query', 'SELECT * FROM TABLE')
                safe_sql = raw_sql.replace('"', '&quot;').replace('<', '&lt;')
                model_block = DB_QUERY_CONTENT.format(sql_query=safe_sql)
            elif spec['name'] == "Oracle Connector":
                model_block = ORACLE_CONNECTOR_CONTENT.format(
                    host=n_def['config'].get('host', 'localhost'),
                    port=n_def['config'].get('port', 1521),
                    database_name=n_def['config'].get('db_name', 'XE'),
                    username=n_def['config'].get('username', 'user')
                )
            elif spec['name'] == "GroupBy":
                model_block = get_groupby_model(n_def['config'])
            elif spec['name'] == "Joiner":
                model_block = get_joiner_model(n_def['config'])
            elif spec['name'] == "Column Expressions (legacy)":
                model_block = get_expression_model(n_def['config'])
            elif spec['name'] == "Concatenate":
                model_block = get_concatenate_model(n_def['config'])
            elif spec['name'] == "Table Manipulator": # Handle Select/AlteryxSelect mapped to Table Manipulator
                model_block = get_table_manipulator_model(n_def['config'])
            
            settings_content = SETTINGS_TEMPLATE.format(
                name=spec['name'], factory=spec['factory'], bundle=spec['bundle'],
                symbolic=spec['symbolic'], model_content=model_block
            )
            zip_contents[f"{folder_name}/settings.xml"] = settings_content

            x = int(node['x']) + n_def['offset_x']
            y = int(node['y']) + n_def['offset_y']
            
            nodes_xml_parts.append(NODE_ENTRY_TEMPLATE.format(
                index=node_entries_count, knime_id=knime_id, folder_name=folder_name, x=x, y=y
            ))
            node_entries_count += 1

        if len(created_knime_ids) > 1:
            conns_xml_parts.append(CONNECTION_TEMPLATE.format(
                index=len(conns_xml_parts), source_id=created_knime_ids[0], dest_id=created_knime_ids[1],
                source_port=1, dest_port=1
            ))
            id_map[alteryx_id] = created_knime_ids[-1]
        else:
            id_map[alteryx_id] = created_knime_ids[0]

    # --- 2. PROCESS EXTERNAL CONNECTIONS ---
    conn_base_index = len(conns_xml_parts)
    for i, edge in enumerate(graph_data['edges']):
        src = id_map.get(edge['source'])
        dest = id_map.get(edge['target'])
        
        # Verify both src and dest exist (Handles cases where Browse nodes were skipped)
        if src and dest:
            src_port = 1
            dest_port = 1
            
            origin_conn = edge.get('origin_connection', 'Output')
            dest_conn = edge.get('destination_connection', 'Input')
            
            if origin_conn == "Join": src_port = 1
            elif origin_conn == "Left": src_port = 2
            elif origin_conn == "Right": src_port = 3
            elif origin_conn == "True": src_port = 1
            elif origin_conn == "False": src_port = 2
            
            if dest_conn == "Left": dest_port = 1
            elif dest_conn == "Right": dest_port = 2
            elif dest_conn == "Source": dest_port = 2
            elif dest_conn == "Targets": dest_port = 1

            conns_xml_parts.append(CONNECTION_TEMPLATE.format(
                index=conn_base_index + i,
                source_id=src, dest_id=dest,
                source_port=src_port, dest_port=dest_port
            ))

    # --- 3. ASSEMBLE & ZIP ---
    workflow_content = WORKFLOW_TEMPLATE.format(
        nodes_block="\n".join(nodes_xml_parts),
        connections_block="\n".join(conns_xml_parts)
    )

    with zipfile.ZipFile(output_path, 'w', zipfile.ZIP_DEFLATED) as z:
        root_dir = "Workflow"
        z.writestr(f"{root_dir}/workflow.knime", workflow_content)
        for path, content in zip_contents.items():
            z.writestr(f"{root_dir}/{path}", content)

    print("✅ Skeleton Build Complete.")