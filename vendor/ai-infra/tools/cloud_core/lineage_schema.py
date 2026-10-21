"""Normalized technical lineage and bounded source-screening tables.

Persistent TableGit authority. URL/title authority remains cloud_core_sources.
No arrays, opaque page payloads or paper bodies are stored in these tables.
"""

def table(key, values, indexes, description):
    fields = {key: {'type': 'string', 'required': True, 'role': 'key'}}
    fields.update({name: {'type': kind, 'required': True, 'role': 'value'} for name, kind in values.items()})
    return {'key_field': key, 'description': description,
            'fields': fields, 'required_fields': list(fields),
            'indexes': [{'name': 'idx_' + name, 'field': name} for name in indexes]}

COMMON = {'business_id': 'string', 'topic_id': 'string'}
DEFINITIONS = {
    'ic_lineages': table('lineage_id', {
        **COMMON, 'name_zh': 'string', 'name_en': 'string',
        'question_zh': 'text', 'question_en': 'text',
        'summary_zh': 'text', 'summary_en': 'text',
        'ascend_zh': 'text', 'ascend_en': 'text',
        'boundary_zh': 'text', 'boundary_en': 'text',
        'position': 'integer', 'status': 'string', 'checked_at': 'string',
    }, ['topic_id', 'business_id', 'status'],
       'Curated compression research routes; chronology is not algorithm inheritance or maturity ranking.'),
    'ic_lineage_nodes': table('node_id', {
        **COMMON, 'lineage_id': 'string', 'technique_id': 'string', 'source_id': 'string',
        'first_submitted_on': 'string', 'observed_version': 'string', 'checked_at': 'string',
        'change_zh': 'text', 'change_en': 'text', 'boundary_zh': 'text', 'boundary_en': 'text',
        'position': 'integer',
    }, ['topic_id', 'business_id', 'lineage_id', 'technique_id', 'source_id'],
       'One representative primary-paper event in a route; source identity is external, date is original UTC first submission.'),
    'ic_lineage_relations': table('relation_id', {
        **COMMON, 'lineage_id': 'string', 'from_node_id': 'string', 'to_node_id': 'string',
        'relation_kind': 'string', 'relation_note_zh': 'text', 'relation_note_en': 'text',
        'source_id': 'string',
    }, ['topic_id', 'business_id', 'lineage_id', 'from_node_id', 'to_node_id', 'source_id'],
       'Evidence-backed explicit extension/generalization or labeled analyst comparison, never inferred ancestry.'),
    'ic_lineage_cells': table('link_id', {
        **COMMON, 'lineage_id': 'string', 'cell_id': 'string',
    }, ['topic_id', 'business_id', 'lineage_id', 'cell_id'],
       'Normalized many-to-many links from technical routes to the unchanged canonical 42-cell taxonomy.'),
    'ic_source_scans': table('scan_id', {
        **COMMON, 'channel_source_id': 'string', 'label_zh': 'string', 'label_en': 'string',
        'title_rule_zh': 'text', 'title_rule_en': 'text', 'boundary_zh': 'text', 'boundary_en': 'text',
        'retrieved_at': 'string', 'listing_date': 'string', 'origin_kind': 'string',
        'requested_limit': 'integer', 'received_count': 'integer', 'title_candidate_count': 'integer',
        'selected_count': 'integer', 'adjacent_count': 'integer', 'excluded_count': 'integer',
        'pending_count': 'integer', 'title_not_matched_count': 'integer',
        'scan_status': 'string', 'position': 'integer',
    }, ['topic_id', 'business_id', 'channel_source_id', 'retrieved_at', 'scan_status'],
       'Actual bounded source retrieval and title-screen counts, not advertised total feed size or a global census.'),
    'ic_source_screenings': table('screening_id', {
        **COMMON, 'scan_id': 'string', 'source_id': 'string', 'screening_status': 'string',
        'reason_zh': 'text', 'reason_en': 'text', 'checked_at': 'string', 'position': 'integer',
    }, ['topic_id', 'business_id', 'scan_id', 'source_id', 'screening_status'],
       'One primary-reviewed title hit and its relevance verdict; unmatched titles are not full-content exclusions.'),
}
